import tempfile
import unittest
from datetime import date
from terracatalogueclient import Catalogue
from terracatalogueclient.config import CatalogueConfig, CatalogueEnvironment
from terracatalogueclient.exceptions import ProductDownloadException


class TestCGLS(unittest.TestCase):

    config_cgls = CatalogueConfig.from_environment(CatalogueEnvironment.CGLS)

    def test_get_collections(self):
        catalogue = Catalogue(self.config_cgls)
        collections = list(catalogue.get_collections())
        collection_ids = {collection.id for collection in collections}
        self.assertIn("clms_global_ba_300m_v3_daily_netcdf", collection_ids)

    def test_get_products(self):
        catalogue = Catalogue(self.config_cgls)
        collection_id = "clms_global_ba_300m_v3_daily_netcdf"
        products = list(
            catalogue.get_products(
                collection_id,
                start=date(2023, 6, 1),
                end=date(2023, 6, 30)
            )
        )
        self.assertIn("c_gls_BA300-NRT_202306260000_GLOBE_S3_V3.1.1", {p.id for p in products})

    def test_auth_not_supported(self):
        with self.assertRaises(ProductDownloadException):
            Catalogue(self.config_cgls).authenticate()
        with self.assertRaises(ProductDownloadException):
            Catalogue(self.config_cgls).authenticate_non_interactive(None, None)

    def test_download(self):
        catalogue = Catalogue(self.config_cgls)
        params = {
            'collection': "clms_global_ba_300m_v3_daily_netcdf",
            'start': date(2023, 6, 1),
            'end': date(2023, 6, 30)
        }
        nb_products = catalogue.get_product_count(**params)
        self.assertGreater(nb_products, 1)
        self.assertLess(nb_products, 10)
        products = catalogue.get_products(**params)
        with tempfile.TemporaryDirectory() as tmpdir:
            catalogue.download_product(next(products), tmpdir)

