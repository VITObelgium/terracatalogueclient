import unittest
from terracatalogueclient import Catalogue
import terracatalogueclient.client
import datetime as dt
from shapely.geometry import box


class TestClient(unittest.TestCase):

    def test_url_join(self):
        from urllib.parse import urljoin
        actual = urljoin("https://services.terrascope.be/catalogue/", "collections")
        self.assertEqual("https://services.terrascope.be/catalogue/collections", actual)

    def test_convert_parameters_time(self):
        params = {
            "start": dt.date(2020, 1, 1),
            "end": dt.datetime(2021, 2, 20, 10, 11, 12)
        }
        Catalogue._convert_parameters(params)
        self.assertEqual("2020-01-01", params['start'])
        self.assertEqual("2021-02-20T10:11:12Z", params['end'])

    def test_convert_parameters_geometry(self):
        params = {
            'geometry': box(4, 50, 6, 51)
        }
        Catalogue._convert_parameters(params)
        print(params['geometry'])

    def test_convert_parameters_bbox(self):
        expected = "4.1,50,5.5,51"
        params = {
            'bbox': [4.1, 50, 5.5, 51]
        }
        Catalogue._convert_parameters(params)
        self.assertEqual(expected, params['bbox'])

        params = {
            'bbox': {
                'west': 4.1,
                'south': 50,
                "east": 5.5,
                "north": 51
            }
        }
        Catalogue._convert_parameters(params)
        self.assertEqual(expected, params['bbox'])

    def test_convert_parameters_cloudCover(self):
        expected = "60]"
        params = {
            'cloudCover': 60
        }
        Catalogue._convert_parameters(params)
        self.assertEqual(expected, params['cloudCover'])

        expected = "50.0]"
        params = {
            'cloudCover': 50.0
        }
        Catalogue._convert_parameters(params)
        self.assertEqual(expected, params['cloudCover'])

        params = Catalogue._convert_parameters({'cloudCover': (None, None)})
        self.assertEqual("", params['cloudCover'])

        params = Catalogue._convert_parameters({'cloudCover': (None, 60)})
        self.assertEqual("60]", params['cloudCover'])

        params = Catalogue._convert_parameters({'cloudCover': (1.0, 78)})
        self.assertEqual("[1.0,78]", params['cloudCover'])

    def test_convert_parameters_publicationDate(self):
        # both sides unbounded
        params = Catalogue._convert_parameters({'publicationDate': (None, None)})
        self.assertEqual("", params['publicationDate'])

        # left unbounded
        params = Catalogue._convert_parameters({'publicationDate': (None, dt.date(2020, 1, 1))})
        self.assertEqual("2020-01-01]", params['publicationDate'])

        # right unbounded
        params = Catalogue._convert_parameters({'publicationDate': (dt.date(2021, 1, 1), None)})
        self.assertEqual("[2021-01-01", params['publicationDate'])

        # both sides bounded
        params = Catalogue._convert_parameters({'publicationDate': (dt.datetime(2021, 2, 20, 12, 34, 56), dt.date(2021, 3, 1))})
        self.assertEqual("[2021-02-20T12:34:56Z,2021-03-01]", params['publicationDate'])

    def test_parse_date(self):
        self.assertEqual(dt.datetime(2021, 4, 16, 16, 15, 14), terracatalogueclient.client._parse_date("2021-04-16T16:15:14.243Z"))
        self.assertEqual(dt.datetime(2020, 2, 20, 18, 12, 38), terracatalogueclient.client._parse_date("2020-02-20T18:12:38Z"))

    def test_get_product_dir(self):

        product = terracatalogueclient.Product(
            id='urn:eop:VITO:TERRASCOPE_S2_NDVI_V2:S2A_20150704T101006_32TML_NDVI_10M_V200',
            title='S2A_20150704T101006_32TML_NDVI_10M_V200',
            geometry=None, bbox=None, beginningDateTime=None, endingDateTime=None, properties=None, data=None,
            related=None, previews=None, alternates=None)
        self.assertEqual('/tmp/S2A_20150704T101006_32TML_NDVI_10M_V200',
                         Catalogue._get_product_dir('/tmp/', product))

        product = terracatalogueclient.Product(
            id='VI_20161001T092022_S2A_T34SDG-010m_V100_FAPAR',
            title='Vegetation Indices 2017-ongoing (raster 010m) - version 1 : FAPAR T34SDG 20161001T092022',
            geometry=None, bbox=None, beginningDateTime=None, endingDateTime=None, properties=None, data=None,
            related=None, previews=None, alternates=None)
        self.assertEqual('/tmp/VI_20161001T092022_S2A_T34SDG-010m_V100_FAPAR',
                         Catalogue._get_product_dir('/tmp/', product))
