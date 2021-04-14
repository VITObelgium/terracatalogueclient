import requests
import datetime as dt
from urllib.parse import urljoin
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry
from typing import Iterator, List, Optional, Union

from terracatalogueclient.exceptions import TooManyResultsException

DEFAULT_CATALOGUE_URL = "https://services.terrascope.be/catalogue/"


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


class Product:
    """ Product entry returned from a catalogue search. """

    def __init__(self,
                 id: str,
                 geometry: BaseGeometry,
                 bbox: List[float],
                 data: List[ProductFile],
                 related: List[ProductFile],
                 previews: List[ProductFile],
                 alternates: List[ProductFile]):
        self.id = id
        self.geometry = geometry
        self.bbox = bbox

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

    def get_collections(self, **kwargs) -> Iterator[Collection]:
        """ Get the collections in the catalogue. """
        url = urljoin(self.base_url, "collections")
        return self._get_paginated_feature_generator(url, kwargs, self._build_collection)

    def get_products(self,
                     collection: str,
                     start: Optional[str] = None,
                     end: Optional[str] = None,
                     bbox: Optional = None,
                     geometry: Optional[str] = None,
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
        :param bbox: geographic bounding box
        :param geometry: geometry as WKT Polygon
        :param title: title of the product
        :param productType: product type
        :param relativeOrbitNumber: relative acquisition orbit number
        :param orbitDirection: acquisition orbit direction
        :param cloudCover: cloud cover percentage
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
        geometry = shape(feature['geometry'])
        bbox = feature['bbox']


        # build product files
        links = feature['properties']['links']
        data = Catalogue._build_files(links['data']) if 'data' in links else []
        related = Catalogue._build_files(links['related']) if 'related' in links else []
        previews = Catalogue._build_files(links['previews']) if 'previews' in links else []
        alternates = Catalogue._build_files(links['alternates']) if 'alternates' in links else []

        return Product(id, geometry, bbox, data, related, previews, alternates)

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