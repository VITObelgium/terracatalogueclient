import requests
import datetime as dt
import os
from urllib.parse import urljoin
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry
import shapely.wkt as wkt
from typing import Iterator, List, Optional, Union, Dict, Iterable

from terracatalogueclient import auth
from terracatalogueclient.exceptions import TooManyResultsException, ProductDownloadException

DEFAULT_CATALOGUE_URL = "https://services.terrascope.be/catalogue/"
DEFAULT_OIDC_CLIENT_ID = "terracatalogueclient"
DEFAULT_OIDC_TOKEN_ENDPOINT = "https://sso.vgt.vito.be/auth/realms/terrascope/protocol/openid-connect/token"
DEFAULT_OIDC_AUTHORIZATION_ENDPOINT = "https://sso.vgt.vito.be/auth/realms/terrascope/protocol/openid-connect/auth"


class Collection:
    """ Collection returned from a catalogue search. """

    def __init__(self, id: str, geometry: BaseGeometry, bbox: List[float], properties: dict):
        self.id = id
        self.geometry = geometry
        self.bbox = bbox
        self.properties = properties

    def __str__(self):
        return self.id


class ProductFile:
    """ File that belongs to a product. """

    def __init__(self,
                 href: str,
                 length: int,
                 title: Optional[str] = None,
                 type: Optional[str] = None,
                 category: Optional[str] = None):
        self.href = href
        self.length = length
        self.title = title
        self.type = type
        self.category = category

    def __str__(self):
        return self.href

    def is_downloadable(self):
        href = self.href.lower()
        return href.startswith("http")


class Product:
    """ Product entry returned from a catalogue search. """

    def __init__(self,
                 id: str,
                 title: str,
                 geometry: BaseGeometry,
                 bbox: List[float],
                 beginningDateTime : Optional[dt.datetime],
                 endingDateTime: Optional[dt.datetime],
                 properties: dict,
                 data: List[ProductFile],
                 related: List[ProductFile],
                 previews: List[ProductFile],
                 alternates: List[ProductFile]):
        self.id = id
        self.title = title
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
    """ Connection to a catalogue endpoint, which allows for searching. """

    def __init__(self, url: str = DEFAULT_CATALOGUE_URL):
        """
        :param url: base URL of the catalogue endpoint
        """
        self.base_url = url.rstrip("/") + "/"
        self._auth = auth.NoAuth()

    def authenticate(
            self,
            authorization_url: str = DEFAULT_OIDC_AUTHORIZATION_ENDPOINT,
            token_url: str = DEFAULT_OIDC_TOKEN_ENDPOINT,
            client_id: str = DEFAULT_OIDC_CLIENT_ID
    ) -> 'Catalogue':
        """
        Authenticate to the catalogue in an interactive way. A browser window will open to handle the sign-in procedure.

        :return: the catalog object
        """
        self._auth = auth.authorization_code_grant(authorization_url=authorization_url, token_url=token_url, client_id=client_id)
        return self

    def authenticate_non_interactive(
            self,
            username: str,
            password: str,
            token_url: str = DEFAULT_OIDC_TOKEN_ENDPOINT,
            client_id: str = DEFAULT_OIDC_CLIENT_ID
    ) -> 'Catalogue':
        """
        Authenticate to the catalogue in a non-interactive way. This requires you to pass your user credentials directly in the code.

        :return: the catalog object
        """
        self._auth = auth.resource_owner_password_credentials_grant(username=username, password=password, client_id=client_id, token_url=token_url)
        return self

    def get_collections(self, **kwargs) -> Iterator[Collection]:
        """ Get the collections in the catalogue. """
        url = urljoin(self.base_url, "collections")
        return self._get_paginated_feature_generator(url, kwargs, self._build_collection)

    def get_products(self,
                     collection: str,
                     start: Optional[Union[str, dt.date, dt.datetime]] = None,
                     end: Optional[Union[str, dt.date, dt.datetime]] = None,
                     bbox: Optional[Union[str, List[Union[int, float]], Dict[str, Union[int, float]]]] = None,
                     geometry: Optional[Union[str, BaseGeometry]] = None,
                     title: Optional[str] = None,
                     productType: Optional[str] = None,
                     relativeOrbitNumber: Optional[Union[int, str]] = None,
                     orbitDirection: Optional[str] = None,
                     cloudCover: Optional[Union[float, int, str]] = None,
                     tileId: Optional[str] = None,
                     accessedFrom: Optional[str] = None,
                     **kwargs) -> Iterator[Product]:
        """ Get the products matching the query.

        :param collection: collection to query
        :param start: start of the temporal interval to search
        :param end: end of the temporal interval to search
        :param bbox: geographic bounding box as list or dict (west, south, east, north)
        :param geometry: geometry as WKT string or Shapely geometry
        :param title: title of the product
        :param productType: product type
        :param relativeOrbitNumber: relative acquisition orbit number
        :param orbitDirection: acquisition orbit direction
        :param cloudCover: maximum cloud cover percentage as int/float; or number, set or interval of cloud cover percentages as a str
        :param tileId: tile identifier
        :param accessedFrom: information on the origin of the request
        :param kwargs: additional query parameters
        """
        url = urljoin(self.base_url, "products")
        kwargs['collection'] = collection
        if start: kwargs['start'] = start
        if end: kwargs['end'] = end
        if bbox: kwargs['bbox'] = bbox
        if geometry: kwargs['geometry'] = geometry
        if title: kwargs['title'] = title
        if productType: kwargs['productType'] = productType
        if relativeOrbitNumber: kwargs['relativeOrbitNumber'] = relativeOrbitNumber
        if orbitDirection: kwargs['orbitDirection'] = orbitDirection
        if cloudCover: kwargs['cloudCover'] = cloudCover
        if tileId: kwargs['tileId'] = tileId
        if accessedFrom: kwargs['accessedFrom'] = accessedFrom
        self._convert_parameters(kwargs)
        return self._get_paginated_feature_generator(url, kwargs, self._build_product)

    def get_product_count(self, collection: str, **kwargs):
        """ Get the count of products matching the query.

        This is significantly more efficient than loading all results and then counting.

        :param collection: collection to query
        :param kwargs: query parameters, check get_products() for more information on query parameters
        """
        url = urljoin(self.base_url, "products")
        kwargs['collection'] = collection
        self._convert_parameters(kwargs)
        response = requests.get(url, params=kwargs)
        if response.status_code == requests.codes.ok:
            response_json = response.json()
            return response_json['totalResults']
        else:
            response.raise_for_status()

    def download_products(self, products: Iterable[Product], path: str):
        """ Download the given products. This will download all files belonging to the given products.

         :param products: iterable of products to download
         :param path: output directory to write files to
         """
        for product in products:
            self.download_product(product, path)

    def download_product(self, product: Product, path: str):
        """ Download a single product. This will download all files belonging to the given product.

        :param product: product to download
        :param path: output directory to write files to
        """
        product_dir = os.path.join(path, product.title)
        for product_file in product.data + product.related + product.alternates + product.previews:
            self.download_file(product_file, product_dir)

    def download_file(self, product_file: ProductFile, path: str):
        """ Download a single product file.

        :param product_file: product file to download
        :param path: output directory to write files to
        """
        if product_file.is_downloadable():
            if not self._is_authorized_to_download(product_file):
                raise ProductDownloadException(f"You are not authorized to download this product. Make sure you are authenticated to the catalogue.")
            # create output directory if it doesn't exists
            if not os.path.exists(path):
                os.makedirs(path)
            filename = os.path.basename(product_file.href)
            out_path = os.path.join(path, filename)
            with requests.get(product_file.href, stream=True, auth=self._auth, allow_redirects=False) as r:
                r.raise_for_status()
                with open(out_path, 'wb') as f:
                    for chunk in r.iter_content():
                        if chunk:
                            f.write(chunk)
        else:
            raise ProductDownloadException(f"Could not download product file, {product_file.href} is not a downloadable path.")

    def _is_authorized_to_download(self, product_file: ProductFile) -> bool:
        """ Check if the authenticated user has authorization to download the product file.
        If the user is not authenticated, a redirect will take place.

        :param product_file: product file
        """
        r = requests.head(product_file.href, auth=self._auth)
        return r.ok

    @staticmethod
    def _convert_parameters(params):
        parameter_time = ['start', 'end']
        for p in parameter_time:
            if p in params:
                if isinstance(params[p], str):
                    pass
                elif isinstance(params[p], dt.datetime):
                    params[p] = dt.datetime.strftime(params[p], "%Y-%m-%dT%H:%M:%SZ")
                elif isinstance(params[p], dt.date):
                    params[p] = dt.date.strftime(params[p], "%Y-%m-%d")

        if 'geometry' in params:
            p = 'geometry'
            if isinstance(params[p], str):
                pass
            elif isinstance(params[p], BaseGeometry):
                params[p] = wkt.dumps(params[p], trim=True)

        if 'bbox' in params:
            p = 'bbox'
            if isinstance(params[p], str):
                pass
            elif isinstance(params[p], list):
                params[p] = ','.join(str(i) for i in params[p])
            elif isinstance(params[p], dict):
                params[p] = f"{params[p]['west']},{params[p]['south']},{params[p]['east']},{params[p]['north']}"

        if 'cloudCover' in params:
            p = 'cloudCover'
            if isinstance(params[p], int) or isinstance(params[p], float):
                params[p] = f"{params[p]}]"

        return params

    @staticmethod
    def _get_paginated_feature_generator(url: str, url_params: dict, builder) -> Iterator:
        response = requests.get(url, params=url_params)

        if response.status_code == requests.codes.ok:
            response_json = response.json()
            if response_json['totalResults'] > 10000:
                raise TooManyResultsException(
                    f"Too many results: found {response_json['totalResults']} (max 10000 allowed). "
                    f"Please narrow down your search.")

            for f in response_json['features']:
                yield builder(f)

            while 'next' in response_json['properties']['links']:
                url = response_json['properties']['links']['next'][0]['href']
                response = requests.get(url)

                if response.status_code == requests.codes.ok:
                    response_json = response.json()
                    for f in response_json['features']:
                        yield builder(f)
                else:
                    response.raise_for_status()
        else:
            # TODO custom error handling, custom exceptions?
            response.raise_for_status()

    @staticmethod
    def _build_collection(feature: dict) -> Collection:
        """ Build collection object from the JSON response.
        :param feature: feature as a JSON dict
        """
        return Collection(feature['id'], shape(feature['geometry']), feature['bbox'], feature['properties'])

    @staticmethod
    def _build_product(feature: dict) -> Product:
        """ Build product object from the JSON response.
        :param feature: feature as a JSON dict
        """
        id = feature['id']
        title = feature['properties']['title']
        geometry = shape(feature['geometry'])
        bbox = feature['bbox']

        # get first acquisitionParameters block, if available
        acquisitionParameters = next(iter([i['acquisitionParameters'] for i in feature['properties']['acquisitionInformation'] if 'acquisitionParameters' in i]), None)
        beginningDateTime = _parse_date(acquisitionParameters['beginningDateTime']) if acquisitionParameters and 'beginningDateTime' in acquisitionParameters else None
        endingDateTime = _parse_date(acquisitionParameters['endingDateTime']) if acquisitionParameters and 'endingDateTime' in acquisitionParameters else None

        # build product files
        links = feature['properties']['links']
        data = Catalogue._build_files(links['data']) if 'data' in links else []
        related = Catalogue._build_files(links['related']) if 'related' in links else []
        previews = Catalogue._build_files(links['previews']) if 'previews' in links else []
        alternates = Catalogue._build_files(links['alternates']) if 'alternates' in links else []

        return Product(id, title, geometry, bbox, beginningDateTime, endingDateTime, feature['properties'], data, related, previews, alternates)

    @staticmethod
    def _build_files(links: list) -> List[ProductFile]:
        return [Catalogue._build_file(link) for link in links]

    @staticmethod
    def _build_file(link: dict) -> ProductFile:
        href = link.get('href')
        length = link.get('length')
        title = link.get('title', None)
        type = link.get('type', None)
        category = link.get('category', None)
        return ProductFile(href, length, title, type, category)


def _parse_date(datestr: str) -> dt.datetime:
    # remove the milliseconds
    # eg. 2021-04-16T16:15:14.243Z --> 2021-04-16T16:15:14
    datestr = datestr[:datestr.find('.')][:datestr.find('Z')]
    return dt.datetime.strptime(datestr, "%Y-%m-%dT%H:%M:%S")
