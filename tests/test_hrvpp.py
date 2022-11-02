import os
import unittest
import tempfile
from terracatalogueclient import Catalogue
from terracatalogueclient.config import CatalogueConfig
from terracatalogueclient.config import CatalogueEnvironment
from terracatalogueclient.exceptions import ProductDownloadException


class TestHRVPP(unittest.TestCase):

    config_hrvpp = CatalogueConfig.from_environment(CatalogueEnvironment.HRVPP)

    def test_get_collections(self):

        catalogue = Catalogue(self.config_hrvpp)
        collections = list(catalogue.get_collections())
        collection_ids = [collection.id for collection in collections]
        self.assertIn("copernicus_r_utm-wgs84_10_m_hrvpp-vi_p_2017-now_v01", collection_ids)

    def test_get_products(self):
        catalogue = Catalogue(self.config_hrvpp)
        tileId = "31UGS"
        products = list(
            catalogue.get_products(
                "copernicus_r_utm-wgs84_10_m_hrvpp-vi_p_2017-now_v01",
                tileId=tileId,
                start="2021-01-01",
                end="2021-01-31")
        )
        self.assertTrue(products)  # check if list is not empty

    def test_download_interactive(self):
        with self.assertRaises(ProductDownloadException):
            Catalogue(self.config_hrvpp).authenticate()

    @unittest.skipIf(int(os.getenv('MANUAL_TESTS', 0)) == 0 or 'WEKEO_USERNAME' not in os.environ or 'WEKEO_PASSWORD' not in os.environ,
                     "Run manually to test download with authentication. Provide WekEO credentials as WEKEO_USERNAME and WEKEO_PASSWORD.")
    def test_download_non_interactive(self):
        # note that this will only work when production download service uses WekEO IdP for authentication
        catalogue = Catalogue(self.config_hrvpp).authenticate_non_interactive(os.getenv("WEKEO_USERNAME"),
                                                                              os.getenv("WEKEO_PASSWORD"))
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

        products = catalogue.get_products(
            collection="copernicus_r_utm-wgs84_10_m_hrvpp-vi_p_2017-now_v01",
            uid="VI_20161001T092022_S2A_T34SDG-010m_V101_QFLAG2",
            accessedFrom="S3-private"
        )
        product = next(products)
        with tempfile.TemporaryDirectory() as tempdir:
            catalogue.download_product(product, tempdir)
            prod_dir = os.path.join(tempdir, product.id)
            self.assertTrue(os.path.isdir(prod_dir))
            for pf in product.data:
                self.assertTrue(os.path.isfile(os.path.join(prod_dir, os.path.basename(pf.href))))
