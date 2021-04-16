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


    def test_parse_date(self):
        self.assertEqual(dt.datetime(2021, 4, 16, 16, 15, 14), terracatalogueclient.client._parse_date("2021-04-16T16:15:14.243Z"))
        self.assertEqual(dt.datetime(2020, 2, 20, 18, 12, 38), terracatalogueclient.client._parse_date("2020-02-20T18:12:38Z"))