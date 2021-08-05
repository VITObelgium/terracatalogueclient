import os
import unittest
from terracatalogueclient import Catalogue
from terracatalogueclient.config import CatalogueConfig

test_resource_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources")


class TestHRVPP(unittest.TestCase):

    config_hrvpp = CatalogueConfig.from_file(os.path.join(test_resource_dir, "hrvpp.ini"))

    def test_get_collections(self):

        catalogue = Catalogue(self.config_hrvpp)
        collections = list(catalogue.get_collections())
        collection_ids = [collection.id for collection in collections]
        self.assertIn("copernicus_r_utm-wgs84_10_m_hrvpp-vi_p_2017-ongoing_v01_r00", collection_ids)

    def test_get_products(self):
        catalogue = Catalogue(self.config_hrvpp)
        tileId = "31UGS"
        products = list(
            catalogue.get_products(
                "copernicus_r_utm-wgs84_10_m_hrvpp-vi_p_2017-ongoing_v01_r00",
                tileId=tileId,
                start="2021-01-01",
                end="2021-01-31")
        )
        self.assertTrue(products)  # check if list is not empty
