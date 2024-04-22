import requests
import requests.adapters
import datetime as dt
import os
import boto3
import botocore.session
import botocore.handlers
from urllib.parse import urljoin, urlparse, parse_qs
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry
import shapely.wkt as wkt
import humanfriendly
import enum
from typing import (
    Iterator,
    List,
    Optional,
    Union,
    Dict,
    Iterable,
    Tuple,
    Callable,
    TypeVar,
)
import logging

from terracatalogueclient import auth, __title__, __version__
from terracatalogueclient.config import CatalogueConfig
from terracatalogueclient.exceptions import (
    TooManyResultsException,
    ProductDownloadException,
    ParameterParserException,
    SearchException,
)

T = TypeVar("T")

_DEFAULT_REQUEST_HEADERS = {"User-Agent": f"{__title__}/{__version__}"}
_SEARCH_TIMEOUT = 60
_DOWNLOAD_TIMEOUT = 300

logger = logging.getLogger(__name__)


class Collection:
    """
    Collection returned from a catalogue search.

    :ivar id: collection identifier
    :vartype id: str
    :ivar geojson: GeoJSON representation of the collection
    :vartype geojson: dict
    :ivar geometry: collection geometry as a Shapely geometry
    :vartype geometry: BaseGeometry
    :ivar bbox: bounding box
    :vartype bbox: List[float]
    :ivar properties: collection properties
    :vartype properties: dict
    """

    def __init__(
        self,
        id: str,
        geojson: dict,
        geometry: BaseGeometry,
        bbox: List[float],
        properties: dict,
    ):
        self.id = id
        self.geojson = geojson
        self.geometry = geometry
        self.bbox = bbox
        self.properties = properties

    def __str__(self):
        return self.id


class ProductFileType(enum.Flag):
    """
    Enum flag to indicate the type of a product file.
    """

    DATA = enum.auto()  #: Data files
    RELATED = enum.auto()  #: Related files (eg. cloud mask)
    PREVIEWS = enum.auto()  #: Previews
    ALTERNATES = enum.auto()  #: Metadata description in an alternative format
    ALL = DATA | RELATED | PREVIEWS | ALTERNATES  #: Matches all types of files


class ProductFile:
    """
    File that belongs to a product.

    :ivar href: URI locator of the product file
    :vartype href: str
    :ivar length: content length in bytes
    :vartype length: Optional[int]
    :ivar title: title of the product file
    :vartype title: Optional[str]
    :ivar type: content type
    :vartype type: Optional[str]
    :ivar category: category, only applicable for previews or related files
    :vartype category: Optional[str]
    """

    def __init__(
        self,
        href: str,
        length: Optional[int],
        title: Optional[str] = None,
        type: Optional[str] = None,
        category: Optional[str] = None,
    ):
        self.href = href
        self.length = length
        self.title = title
        self.type = type
        self.category = category

    def __str__(self):
        return self.href

    def get_protocol(self):
        return self.href[: self.href.find("://")].lower()


class Product:
    """
    Product entry returned from a catalogue search.

    :ivar id: product identifier
    :vartype id: str
    :ivar title: product title
    :vartype title: str
    :ivar geojson: GeoJSON representation of the product
    :vartype geojson: dict
    :ivar geometry: product geometry as a Shapely geometry
    :vartype geometry: BaseGeometry
    :ivar bbox: bounding box
    :vartype bbox: List[float]
    :ivar beginningDateTime: acquisition start date time
    :vartype beginningDateTime: dt.datetime
    :ivar endingDateTime: acquisition end date time
    :vartype endingDateTime: dt.datetime
    :ivar properties: product properties
    :vartype properties: dict
    :ivar data: product data files
    :vartype data: List[ProductFile]
    :ivar related: related resources (eg. cloud mask)
    :vartype related: List[ProductFile]
    :ivar previews: previews or quicklooks of the product
    :vartype previews: List[ProductFile]
    :ivar alternates: metadata description in an alternative format
    :vartype alternates: List[ProductFile]
    """

    def __init__(
        self,
        id: str,
        title: str,
        geojson: dict,
        geometry: BaseGeometry,
        bbox: List[float],
        beginningDateTime: Optional[dt.datetime],
        endingDateTime: Optional[dt.datetime],
        properties: dict,
        data: List[ProductFile],
        related: List[ProductFile],
        previews: List[ProductFile],
        alternates: List[ProductFile],
    ):
        self.id = id
        self.title = title
        self.geojson = geojson
        self.geometry = geometry
        self.bbox = bbox

        self.beginningDateTime = beginningDateTime
        self.endingDateTime = endingDateTime
        self.properties = properties

        # product file references
        self.data = data
        self.related = related
        self.previews = previews
        self.alternates = alternates

    def __str__(self):
        return self.id


class Catalogue:
    """Connection to a catalogue endpoint, which allows for searching and downloading EO products."""

    def __init__(self, config: CatalogueConfig = None):
        """
        :param config: catalogue configuration. If none is supplied, the default Terrascope config is used.
        """
        self.config = config if config else CatalogueConfig.get_default_config()
        self._auth = None
        self.s3 = None

        adapter = requests.adapters.HTTPAdapter(
            max_retries=requests.adapters.Retry(
                total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504]
            )
        )

        self._session_search = requests.Session()
        self._session_search.headers.update(_DEFAULT_REQUEST_HEADERS)
        self._session_search.headers.update(
            {"Accept": "application/json, application/geo+json"}
        )
        self._session_search.mount("http://", adapter)
        self._session_search.mount("https://", adapter)

        self._session_download = requests.Session()
        self._session_download.headers.update(_DEFAULT_REQUEST_HEADERS)
        self._session_download.headers.update({"Accept": "application/json"})
        self._session_download.mount("http://", adapter)
        self._session_download.mount("https://", adapter)

    def authenticate(self) -> "Catalogue":
        """
        Authenticate to the catalogue in an interactive way. A browser window will open to handle the sign-in procedure.

        :return: the catalogue object
        """

        if not self.config.oidc_interactive_supported:
            raise ProductDownloadException(
                "Interactive authentication is not supported for this catalogue endpoint"
            )

        self._auth = auth.authorization_code_grant(
            authorization_url=self.config.oidc_authorization_endpoint,
            token_url=self.config.oidc_token_endpoint,
            client_id=self.config.oidc_client_id,
        )
        self._session_search.auth = self._auth
        self._session_download.auth = self._auth
        return self

    def authenticate_non_interactive(self, username: str, password: str) -> "Catalogue":
        """
        Authenticate to the catalogue in a non-interactive way. This requires you to pass your user credentials directly in the code.

        :param username: username
        :param password: password
        :return: the catalogue object
        """

        if not self.config.oidc_non_interactive_supported:
            raise ProductDownloadException(
                "Non interactive authentication is not supported for this catalogue endpoint"
            )

        self._auth = auth.resource_owner_password_credentials_grant(
            username=username,
            password=password,
            client_id=self.config.oidc_client_id,
            client_secret=self.config.oidc_client_secret,
            token_url=self.config.oidc_token_endpoint,
        )
        self._session_search.auth = self._auth
        self._session_download.auth = self._auth
        return self

    def get_collections(
        self,
        start: Optional[Union[str, dt.date, dt.datetime]] = None,
        end: Optional[Union[str, dt.date, dt.datetime]] = None,
        bbox: Optional[
            Union[str, List[Union[int, float]], Dict[str, Union[int, float]]]
        ] = None,
        geometry: Optional[Union[str, BaseGeometry]] = None,
        platform: Optional[str] = None,
        **kwargs,
    ) -> Iterator[Collection]:
        """
        Get the collections in the catalogue.

        :param start: start of the temporal interval to search
        :param end: end of the temporal interval to search
        :param bbox: geographic bounding box as list or dict (west, south, east, north)
        :param geometry: geometry as WKT string or Shapely geometry
        :param platform: acquisition platform
        :param \**kwargs: additional query parameters can be provided as keyword arguments
        """
        url = urljoin(self.config.catalogue_url, "collections")
        if start:
            kwargs["start"] = start
        if end:
            kwargs["end"] = end
        if bbox:
            kwargs["bbox"] = bbox
        if geometry:
            kwargs["geometry"] = geometry
        if platform:
            kwargs["platform"] = platform
        self._convert_parameters(kwargs)
        return self._get_paginated_feature_generator(
            url, kwargs, self._build_collection
        )

    def get_products(
        self,
        collection: str,
        start: Optional[Union[str, dt.date, dt.datetime]] = None,
        end: Optional[Union[str, dt.date, dt.datetime]] = None,
        bbox: Optional[
            Union[str, List[Union[int, float]], Dict[str, Union[int, float]]]
        ] = None,
        geometry: Optional[Union[str, BaseGeometry]] = None,
        title: Optional[str] = None,
        productType: Optional[str] = None,
        relativeOrbitNumber: Optional[Union[int, str]] = None,
        orbitDirection: Optional[str] = None,
        cloudCover: Optional[
            Union[
                Tuple[Union[float, int, None], Union[float, int, None]], float, int, str
            ]
        ] = None,
        tileId: Optional[str] = None,
        productGroupId: Optional[str] = None,
        publicationDate: Optional[
            Union[
                Tuple[
                    Union[dt.date, dt.datetime, str, None],
                    Union[dt.date, dt.datetime, str, None],
                ],
                str,
            ]
        ] = None,
        modificationDate: Optional[
            Union[
                Tuple[
                    Union[dt.date, dt.datetime, str, None],
                    Union[dt.date, dt.datetime, str, None],
                ],
                str,
            ]
        ] = None,
        accessedFrom: Optional[str] = None,
        limit: Optional[int] = None,
        **kwargs,
    ) -> Iterator[Product]:
        """Get the products matching the query.

        :param collection: collection to query
        :param start: start of the temporal interval to search
        :param end: end of the temporal interval to search
        :param bbox: geographic bounding box as list or dict (west, south, east, north)
        :param geometry: geometry as WKT string or Shapely geometry
        :param title: title of the product
        :param productType: product type
        :param relativeOrbitNumber: relative acquisition orbit number
        :param orbitDirection: acquisition orbit direction
        :param cloudCover: maximum cloud cover percentage as int/float; cloud cover percentage interval as tuple; or number, set or interval of cloud cover percentages as a str
        :param tileId: tile identifier
        :param productGroupId: string identifying the particular group to which a product belongs
        :param publicationDate: date of publication, as a date range in a date/datetime tuple (you can use None to have an unbounded interval) or as a str
        :param modificationDate: date of publication, as a date range in a date/datetime tuple (you can use None to have an unbounded interval) or as a str
        :param accessedFrom: information on the origin of the request
        :param limit: limit the number of requested products
        :param \**kwargs: additional query parameters can be provided as keyword arguments
        """
        url = urljoin(self.config.catalogue_url, "products")
        kwargs["collection"] = collection
        if start:
            kwargs["start"] = start
        if end:
            kwargs["end"] = end
        if bbox:
            kwargs["bbox"] = bbox
        if geometry:
            kwargs["geometry"] = geometry
        if title:
            kwargs["title"] = title
        if productType:
            kwargs["productType"] = productType
        if relativeOrbitNumber:
            kwargs["relativeOrbitNumber"] = relativeOrbitNumber
        if orbitDirection:
            kwargs["orbitDirection"] = orbitDirection
        if cloudCover:
            kwargs["cloudCover"] = cloudCover
        if tileId:
            kwargs["tileId"] = tileId
        if productGroupId:
            kwargs["productGroupId"] = productGroupId
        if publicationDate:
            kwargs["publicationDate"] = publicationDate
        if modificationDate:
            kwargs["modificationDate"] = modificationDate
        if accessedFrom:
            kwargs["accessedFrom"] = accessedFrom
        if limit:
            kwargs["limit"] = limit
        self._convert_parameters(kwargs)
        return self._get_paginated_feature_generator(url, kwargs, self._build_product)

    def get_product_count(self, collection: str, **kwargs):
        """Get the count of products matching the query.

        This is significantly more efficient than loading all results and then counting.

        :param collection: collection to query
        :param \**kwargs: query parameters, check :meth:`~terracatalogueclient.client.Catalogue.get_products` for more information on query parameters
        """
        url = urljoin(self.config.catalogue_url, "products")
        kwargs["collection"] = collection
        kwargs["count"] = 0
        self._convert_parameters(kwargs)
        response = self._session_search.get(url, params=kwargs, timeout=_SEARCH_TIMEOUT)
        logger.debug(f"{response.request.url} - {response.status_code}")
        if response.status_code == requests.codes.ok:
            response_json = response.json()
            return response_json["totalResults"]
        else:
            raise SearchException(response)

    def _get_total_file_size(
        self, products: Iterable[Product], file_types: ProductFileType
    ) -> int:
        """Get the total file size of the given products.

        :param products: iterable of products
        :param file_types: product file types
        :return: total file size in bytes
        """
        return sum(
            [
                product_file.length
                for product in products
                for product_file in self._get_product_files_matching_file_types(
                    product, file_types
                )
                if product_file.length is not None
            ]
        )

    def _get_product_files_matching_file_types(
        self, product: Product, file_types: ProductFileType
    ) -> List[ProductFile]:
        """
        Get the product files matching the given file types.

        :param product: product
        :param file_types: product file types
        :return: product files matching the given file types
        """
        files = []
        if ProductFileType.DATA in file_types:
            files += product.data
        if ProductFileType.RELATED in file_types:
            files += product.related
        if ProductFileType.PREVIEWS in file_types:
            files += product.previews
        if ProductFileType.ALTERNATES in file_types:
            files += product.alternates

        return files

    def download_products(
        self,
        products: Iterable[Product],
        path: str,
        file_types: ProductFileType = ProductFileType.ALL,
        force: bool = False,
        raise_on_failure: bool = True,
    ):
        """
        Download the given products. This will download the files belonging to the given products matching the provided file types.

        :param products: iterable of products to download
        :param path: output directory to write files to
        :param file_types: type of product files to download
        :param force: skip download confirmation
        :param raise_on_failure: raise an exception on a failure or silently continue
        """
        products = list(products)
        if not force:
            confirmed = False
            while not confirmed:
                in_confirmation = input(
                    f"You are about to download {humanfriendly.format_size(self._get_total_file_size(products, file_types))}, do you want to continue? [Y/n] "
                )
                if any(in_confirmation.lower() == s for s in ["y", ""]):
                    confirmed = True
                elif in_confirmation.lower() == "n":
                    return
        for product in products:
            self.download_product(product, path, file_types, raise_on_failure)

    def download_product(
        self,
        product: Product,
        path: str,
        file_types: ProductFileType = ProductFileType.ALL,
        raise_on_failure: bool = True,
    ):
        """Download a single product. This will download all files belonging to the given product.

        :param product: product to download
        :param path: output directory to write files to
        :param file_types: type of product files to download
        :param raise_on_failure: raise an exception on a failure or silently continue
        """
        for product_file in self._get_product_files_matching_file_types(
            product, file_types
        ):
            try:
                self.download_file(product_file, self._get_product_dir(path, product))
            except ConnectionError as e:
                logger.error(e)
                if raise_on_failure:
                    raise e

    def download_file(self, product_file: ProductFile, path: str):
        """Download a single product file.

        :param product_file: product file to download
        :param path: output directory to write the file to
        """
        protocol = product_file.get_protocol()
        if protocol.startswith("http"):
            self._download_file_http(product_file, path)
        elif protocol == "s3":
            self._download_file_s3(product_file, path)
        else:
            raise ProductDownloadException(
                f"Could not download product file, {product_file.href} is not a downloadable path."
            )

    def _download_file_http(self, product_file: ProductFile, path: str):
        """Download a single product file over HTTP.
        Assumes that the href in the product file contains a valid HTTP address.

        :param product_file: product file to download
        :param path: output directory to write the file to
        """
        if not self._is_authorized_to_download_http(product_file):
            raise ProductDownloadException(
                "You are not authorized to download this product. Make sure you are authenticated to the catalogue."
            )
        # create output directory if it doesn't exist
        if not os.path.exists(path):
            logger.debug(f"Creating output directory {path}")
            os.makedirs(path)
        filename = os.path.basename(product_file.href)
        out_path = os.path.join(path, filename)
        logger.info(f"Downloading {product_file.href} to {out_path}")
        with self._session_download.get(
            product_file.href,
            stream=True,
            allow_redirects=False,
            timeout=_DOWNLOAD_TIMEOUT,
        ) as r:
            r.raise_for_status()
            with open(out_path, "wb") as f:
                for chunk in r.iter_content(
                    chunk_size=self.config.http_download_chunk_size
                ):
                    if chunk:
                        f.write(chunk)

    def _download_file_s3(self, product_file: ProductFile, path: str):
        """Download a single product over S3.
        Assumes that the href in the product file contains a valid S3 link.

        :param product_file: product file to download
        :param path: output directory to write the file to
        """
        if not os.path.exists(path):
            logger.debug(f"Creating output directory {path}")
            os.makedirs(path)
        filename = os.path.basename(product_file.href)
        out_path = os.path.join(path, filename)

        if not self.s3:
            self._init_s3_client()

        logger.info(f"Downloading {product_file.href} to {out_path}")
        _, tmp = product_file.href.split("://", 1)
        bucket_name, key = tmp.split("/", 1)
        bucket = self.s3.Bucket(bucket_name)
        bucket.download_file(key, out_path)

    def _init_s3_client(self):
        """Set up the S3 resource service client using the configuration values."""
        # disable bucket name validation: https://creodias.eu/-/bucket-sharing-using-s3-bucket-policy
        logger.info("Initializing S3 client")
        botocore_session = botocore.session.Session()
        botocore_session.unregister(
            "before-parameter-build.s3", botocore.handlers.validate_bucket_name
        )
        boto3.setup_default_session(botocore_session=botocore_session)

        if not (
            self.config.s3_endpoint_url
            and self.config.s3_access_key
            and self.config.s3_secret_key
        ):
            raise ProductDownloadException(
                "Please provide S3 endpoint and credentials in the configuration file "
                "or using environment variables in order to use S3 as a download method."
            )

        self.s3 = boto3.resource(
            "s3",
            endpoint_url=self.config.s3_endpoint_url,
            aws_access_key_id=self.config.s3_access_key,
            aws_secret_access_key=self.config.s3_secret_key,
        )

    def _is_authorized_to_download_http(self, product_file: ProductFile) -> bool:
        """Check if the authenticated user has authorization to download the product file.
        If the user is not authenticated, a redirect will take place.

        :param product_file: product file
        """
        r = self._session_download.head(product_file.href, timeout=_DOWNLOAD_TIMEOUT)
        return r.ok

    @staticmethod
    def _convert_parameters(params):
        parameter_time = ["start", "end"]
        parameter_time_interval = ["publicationDate", "modificationDate"]

        for p in parameter_time:
            if p in params:
                params[p] = _date_to_str(params[p])

        for p in parameter_time_interval:
            if p in params:
                if type(params[p]) == tuple:
                    params[p] = _tuple_to_interval_str(params[p], p, _date_to_str)

        if "geometry" in params:
            p = "geometry"
            if isinstance(params[p], str):
                pass
            elif isinstance(params[p], BaseGeometry):
                params[p] = wkt.dumps(params[p], trim=True)

        if "bbox" in params:
            p = "bbox"
            if isinstance(params[p], str):
                pass
            elif isinstance(params[p], list):
                params[p] = ",".join(str(i) for i in params[p])
            elif isinstance(params[p], dict):
                params[
                    p
                ] = f"{params[p]['west']},{params[p]['south']},{params[p]['east']},{params[p]['north']}"

        if "cloudCover" in params:
            p = "cloudCover"
            if type(params[p]) == tuple:
                params[p] = _tuple_to_interval_str(params[p], p, str)
            elif isinstance(params[p], int) or isinstance(params[p], float):
                params[p] = f"{params[p]}]"

        return params

    @staticmethod
    def _can_get_all_features(response: dict, limit: Optional[int] = None) -> bool:
        """
        Check if all features can be retrieved using pagination.
        If too many results are found for the query, it may not be possible due to a limitation on the pagination depth.
        :param response: FeatureCollection as a dict
        :param limit: limit the number of requested features
        :return: boolean indicating whether all features can be retrieved
        """
        page_size = response["itemsPerPage"]
        total_results = response["totalResults"]
        requested_results = (
            total_results if limit is None else min(limit, total_results)
        )

        if (
            "last" in response["properties"]["links"]
            and len(response["properties"]["links"]["last"]) == 1
        ):
            last_href = response["properties"]["links"]["last"][0]["href"]
            last_start_index = int(parse_qs(urlparse(last_href).query)["startIndex"][0])

            return requested_results <= last_start_index + page_size - 1
        else:
            return requested_results <= page_size

    def _is_authenticated(self):
        """
        Checks if the user is authenticated.
        :return: true if the user is authenticated.
        """
        return self._auth is not None

    def _get_paginated_feature_generator(
        self, url: str, url_params: dict, builder
    ) -> Iterator:
        limit = url_params.pop("limit", None)
        feature_count = 0

        response = self._session_search.get(
            url, params=url_params, timeout=_SEARCH_TIMEOUT
        )
        logger.debug(f"{response.request.url} - {response.status_code}")

        if response.status_code == requests.codes.ok:
            response_json = response.json()
            if not Catalogue._can_get_all_features(response_json, limit):
                raise TooManyResultsException(
                    f"Too many results: {response_json['totalResults']} found. "
                    f"Please narrow down your search."
                )

            for f in response_json["features"]:
                feature_count += 1
                yield builder(f)
                if limit is not None and feature_count >= limit:
                    return

            while "next" in response_json["properties"]["links"]:
                url = response_json["properties"]["links"]["next"][0]["href"]
                response = self._session_search.get(url, timeout=_SEARCH_TIMEOUT)
                logger.debug(f"{response.request.url} - {response.status_code}")

                if response.status_code == requests.codes.ok:
                    response_json = response.json()
                    for f in response_json["features"]:
                        feature_count += 1
                        yield builder(f)
                        if limit is not None and feature_count >= limit:
                            return
                else:
                    response.raise_for_status()
        else:
            raise SearchException(response)

    @staticmethod
    def _build_collection(feature: dict) -> Collection:
        """Build collection object from the JSON response.
        :param feature: feature as a JSON dict
        """
        return Collection(
            feature["id"],
            feature,
            shape(feature["geometry"]),
            feature["bbox"],
            feature["properties"],
        )

    @staticmethod
    def _build_product(feature: dict) -> Product:
        """Build product object from the JSON response.
        :param feature: feature as a JSON dict
        """
        id = feature["id"]
        title = feature["properties"]["title"]
        geometry = shape(feature["geometry"])
        bbox = feature["bbox"]

        # get first acquisitionParameters block, if available
        acquisitionParameters = next(
            iter(
                [
                    i["acquisitionParameters"]
                    for i in feature["properties"]["acquisitionInformation"]
                    if "acquisitionParameters" in i
                ]
            ),
            None,
        )
        beginningDateTime = (
            _parse_date(acquisitionParameters["beginningDateTime"])
            if acquisitionParameters and "beginningDateTime" in acquisitionParameters
            else None
        )
        endingDateTime = (
            _parse_date(acquisitionParameters["endingDateTime"])
            if acquisitionParameters and "endingDateTime" in acquisitionParameters
            else None
        )

        # build product files
        links = feature["properties"]["links"]
        data = Catalogue._build_files(links["data"]) if "data" in links else []
        related = Catalogue._build_files(links["related"]) if "related" in links else []
        previews = (
            Catalogue._build_files(links["previews"]) if "previews" in links else []
        )
        alternates = (
            Catalogue._build_files(links["alternates"]) if "alternates" in links else []
        )

        return Product(
            id,
            title,
            feature,
            geometry,
            bbox,
            beginningDateTime,
            endingDateTime,
            feature["properties"],
            data,
            related,
            previews,
            alternates,
        )

    @staticmethod
    def _build_files(links: list) -> List[ProductFile]:
        return [Catalogue._build_file(link) for link in links]

    @staticmethod
    def _build_file(link: dict) -> ProductFile:
        href = link.get("href")
        length = link.get("length", None)
        title = link.get("title", None)
        type = link.get("type", None)
        category = link.get("category", None)
        return ProductFile(href, length, title, type, category)

    @staticmethod
    def _get_product_dir(path: str, product: Product):
        try:
            return os.path.join(path, product.id[product.id.rindex(":") + 1 :])
        except ValueError:
            return os.path.join(path, product.id)


def _parse_date(datestr: str) -> dt.datetime:
    # remove the milliseconds
    # eg. 2021-04-16T16:15:14.243Z --> 2021-04-16T16:15:14
    datestr = datestr[: datestr.find(".")][: datestr.find("Z")]
    return dt.datetime.strptime(datestr, "%Y-%m-%dT%H:%M:%S")


def _date_to_str(date: Union[str, dt.datetime, dt.date]) -> str:
    if isinstance(date, str):
        return date
    elif isinstance(date, dt.datetime):
        return dt.datetime.strftime(date, "%Y-%m-%dT%H:%M:%SZ")
    elif isinstance(date, dt.date):
        return dt.date.strftime(date, "%Y-%m-%d")


def _tuple_to_interval_str(
    tuple: Tuple[T, T], param_name: str, formatter: Callable[[T], str]
) -> str:
    if len(tuple) != 2:
        raise ParameterParserException(
            f"Failed to parse the value of the '{param_name}' parameter. "
            f"A tuple of length {len(tuple)} is not supported. "
            f"To use an interval, the tuple should be of length 2."
        )

    t1, t2 = tuple
    if t1 is None and t2 is None:
        # filtering doesn't have any effect, remove it
        return ""
    elif t1 is None:
        # left unbounded
        return f"{formatter(t2)}]"
    elif t2 is None:
        # right unbounded
        return f"[{formatter(t1)}"
    else:
        # both sides bounded
        return f"[{formatter(t1)},{formatter(t2)}]"
