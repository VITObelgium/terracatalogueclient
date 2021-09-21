import os
import unittest
import tempfile
from terracatalogueclient import Catalogue
from terracatalogueclient.config import CatalogueConfig

test_resource_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources")


class TestHRVPP(unittest.TestCase):

    config_hrvpp = CatalogueConfig.from_file(os.path.join(test_resource_dir, "hrvpp.ini"))

    def test_get_collections(self):

        catalogue = Catalogue(self.config_hrvpp)
        collections = list(catalogue.get_collections())
        collection_ids = [collection.id for collection in collections]
        self.assertIn("copernicus_r_utm-wgs84_10_m_hrvpp-vi_p_2017-ongoing_v01_r01", collection_ids)

    def test_get_products(self):
        catalogue = Catalogue(self.config_hrvpp)
        tileId = "31UGS"
        products = list(
            catalogue.get_products(
                "copernicus_r_utm-wgs84_10_m_hrvpp-vi_p_2017-ongoing_v01_r01",
                tileId=tileId,
                start="2021-01-01",
                end="2021-01-31")
        )
        self.assertTrue(products)  # check if list is not empty

    @unittest.skipIf(int(os.getenv('MANUAL_TESTS', 0)) == 0, "Run manually to test download with authentication.")
    def test_download_http(self):
        catalogue = Catalogue(self.config_hrvpp).authenticate()
        tileId = "31UGS"
        products = catalogue.get_products(
            "copernicus_r_utm-wgs84_10_m_hrvpp-vi_p_2017-ongoing_v01_r01",
            tileId=tileId,
            start="2021-01-01",
            end="2021-01-31",
            accessedFrom="HTTP"
        )
        with tempfile.TemporaryDirectory() as tempdir:
            catalogue.download_product(next(products), tempdir)

    @unittest.skipIf(int(os.getenv('MANUAL_TESTS', 0)) == 0 or 'AWS_ACCESS_KEY_ID' not in os.environ or 'AWS_SECRET_ACCESS_KEY' not in os.environ,
                     "Run manually to test download with authentication. Provide S3 credentials as environment variables AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.")
    def test_download_s3(self):
        catalogue = Catalogue(self.config_hrvpp)
        catalogue.config.s3_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        catalogue.config.s3_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

        products = catalogue.get_products(
            collection="copernicus_r_utm-wgs84_10_m_hrvpp-vi_p_2017-ongoing_v01_r01",
            uid="VI_20161001T092022_S2A_T34SDG-010m_V101_QFLAG2",
            accessedFrom="S3"
        )
        product = next(products)
        with tempfile.TemporaryDirectory() as tempdir:
            catalogue.download_product(product, tempdir)
            prod_dir = os.path.join(tempdir, product.title)
            self.assertTrue(os.path.isdir(prod_dir))
            for pf in product.data:
                self.assertTrue(os.path.isfile(os.path.join(prod_dir, os.path.basename(pf.href))))
