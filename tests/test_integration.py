import unittest
from terracatalogueclient import Catalogue
from terracatalogueclient.exceptions import TooManyResultsException


class TestIntegration(unittest.TestCase):

    def test_get_collections(self):
        catalogue = Catalogue()
        collections = list(catalogue.get_collections())
        collection_ids = [collection.id for collection in collections]
        self.assertIn("urn:eop:VITO:CGS_S1_GRD_L1", collection_ids)
        self.assertIn("urn:eop:VITO:CGS_S1_GRD_SIGMA0_L1", collection_ids)
        self.assertIn("urn:eop:VITO:CGS_S1_SLC_L1", collection_ids)

    def test_get_too_many_products(self):
        catalogue = Catalogue()
        products = catalogue.get_products("urn:eop:VITO:CGS_S1_GRD_L1")
        # exception is raised only when elements of the generator are actually accessed
        # converting the generator to a list will do this
        self.assertRaises(TooManyResultsException, list, products)

    def test_get_products_single_page(self):
        catalogue = Catalogue()
        products = catalogue.get_products("urn:eop:VITO:TERRASCOPE_S2_FAPAR_V2", start="2021-01-01", end="2021-01-31", tileId="31UGS")
        count = catalogue.get_product_count("urn:eop:VITO:TERRASCOPE_S2_FAPAR_V2", start="2021-01-01", end="2021-01-31", tileId="31UGS")
        self.assertEqual(count, len(list(products)))

    def test_get_products_multi_page(self):
        catalogue = Catalogue()
        count = catalogue.get_product_count("urn:eop:VITO:TERRASCOPE_S2_FAPAR_V2", start="2020-01-01", end="2020-12-31", tileId="31UFS")
        products = catalogue.get_products("urn:eop:VITO:TERRASCOPE_S2_FAPAR_V2", start="2020-01-01", end="2020-12-31", tileId="31UFS")
        self.assertEqual(count, len(list(products)))
