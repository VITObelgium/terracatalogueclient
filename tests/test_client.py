import unittest
from terracatalogueclient import Catalogue
import datetime as dt


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