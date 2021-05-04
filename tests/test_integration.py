import unittest
from terracatalogueclient import Catalogue
from terracatalogueclient.exceptions import TooManyResultsException
import datetime as dt
from shapely.geometry import box
from shapely.geometry.base import BaseGeometry
import tempfile
import os


class TestIntegration(unittest.TestCase):

    def test_get_collections(self):
        catalogue = Catalogue()
        collections = list(catalogue.get_collections())
        collection_ids = [collection.id for collection in collections]
        self.assertIn("urn:eop:VITO:CGS_S1_GRD_L1", collection_ids)
        self.assertIn("urn:eop:VITO:CGS_S1_GRD_SIGMA0_L1", collection_ids)
        self.assertIn("urn:eop:VITO:CGS_S1_SLC_L1", collection_ids)

    def test_get_collections_by_platform(self):
        catalogue = Catalogue()
        collections = list(catalogue.get_collections(platform="SENTINEL-1"))
        self.assertTrue(len(collections) > 0)
        for c in collections:
            self.assertTrue(any(a['platform']['platformShortName'] == "SENTINEL-1" for a in c.properties['acquisitionInformation']))

    def test_get_collection_by_date(self):
        catalogue = Catalogue()
        collections = list(catalogue.get_collections(start=dt.date(2020, 1, 1), end=dt.date(2020, 12, 31)))
        self.assertTrue(len(collections) > 0)

    def test_get_collections_by_bbox(self):
        catalogue = Catalogue()
        collections = list(catalogue.get_collections(bbox={'west': 4.1, 'south': 50, "east": 5.5, "north": 51}))
        self.assertTrue(len(collections) > 0)

    def test_get_collections_by_geometry(self):
        catalogue = Catalogue()
        geom = box(4, 50, 6, 51)
        collections = list(catalogue.get_collections(geometry=geom))
        self.assertTrue(len(collections) > 0)

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

    def test_get_products_date(self):
        catalogue = Catalogue()
        start = dt.date(2020, 1, 1)
        end = dt.date(2020, 1, 31)
        products = catalogue.get_products("urn:eop:VITO:TERRASCOPE_S2_FAPAR_V2", start=start, end=end, tileId="31UFS")
        for p in products:
            self.assertTrue(dt.datetime(2019, 12, 31) <= p.beginningDateTime <= dt.datetime(2020, 2, 1))

    def test_get_products_bbox(self):
        catalogue = Catalogue()
        bbox = {
            'west': 4.1,
            'south': 50,
            "east": 5.5,
            "north": 51
        }
        products = catalogue.get_products("urn:eop:VITO:CGS_S1_GRD_SIGMA0_L1", bbox=bbox, start="2020-01-01", end="2020-05-01")
        self.assertTrue(len(list(products)))  # check if list is not empty

    def test_get_products_geometry(self):
        catalogue = Catalogue()
        geom = box(4, 50, 6, 51)
        products = catalogue.get_products("urn:eop:VITO:CGS_S1_GRD_SIGMA0_L1", geometry=geom, start="2020-01-01", end="2020-05-01")
        self.assertTrue(len(list(products)))  # check if list is not empty

    def test_get_products_title(self):
        catalogue = Catalogue()
        title = "S2A_20200101T142731_19HBV_FAPAR_20M_V200"
        products = list(catalogue.get_products("urn:eop:VITO:TERRASCOPE_S2_FAPAR_V2", title=title))
        # expect only one product with the same title
        self.assertEqual(1, len(products))
        self.assertEqual(title, products[0].title)

    def test_get_products_relativeOrbitNumber(self):
        catalogue = Catalogue()
        relativeOrbitNumber = 37
        products = list(catalogue.get_products("urn:eop:VITO:CGS_S1_SLC_L1", relativeOrbitNumber=relativeOrbitNumber, start="2020-01-01", end="2020-05-01"))
        self.assertTrue(products)  # check if list is not empty
        for p in products:
            acquisitionParameters = next(iter([i['acquisitionParameters'] for i in p.properties['acquisitionInformation'] if 'acquisitionParameters' in i]))
            self.assertEqual(relativeOrbitNumber, acquisitionParameters['relativeOrbitNumber'])

    def test_get_products_orbitDirection(self):
        catalogue = Catalogue()
        orbitDirection = "DESCENDING"
        products = list(catalogue.get_products("urn:eop:VITO:CGS_S1_SLC_L1", orbitDirection=orbitDirection, start="2020-01-01", end="2020-05-01"))
        self.assertTrue(products)  # check if list is not empty
        for p in products:
            acquisitionParameters = next(iter([i['acquisitionParameters'] for i in p.properties['acquisitionInformation'] if 'acquisitionParameters' in i]))
            self.assertEqual(orbitDirection, acquisitionParameters['orbitDirection'])

    def test_get_products_cloudCover(self):
        catalogue = Catalogue()
        cloudCoverMax = 60
        products = list(catalogue.get_products("urn:eop:VITO:TERRASCOPE_S2_FAPAR_V2", cloudCover=cloudCoverMax, start="2021-02-01", end="2021-02-28", tileId="31UFS"))
        self.assertTrue(products)  # check if list is not empty
        for p in products:
            self.assertGreaterEqual(cloudCoverMax, p.properties['productInformation']['cloudCover'])

    def test_get_products_tileId(self):
        catalogue = Catalogue()
        tileId = "31UGS"
        products = list(catalogue.get_products("urn:eop:VITO:TERRASCOPE_S2_FAPAR_V2", tileId=tileId, start="2021-01-01", end="2021-01-31"))
        self.assertTrue(products)  # check if list is not empty
        for p in products:
            acquisitionParameters = next(iter(
                [i['acquisitionParameters'] for i in p.properties['acquisitionInformation'] if
                 'acquisitionParameters' in i]))
            self.assertEqual(tileId, acquisitionParameters['tileId'])

    def test_get_products_unsupported_parameter(self):
        catalogue = Catalogue()
        products = catalogue.get_products("urn:eop:VITO:CGS_S1_SLC_L1", test="test")
        self.assertRaises(Exception, list, products)  # getting items from the generator and putting them in a list raises the error

    def test_product_building(self):
        catalogue = Catalogue()
        products = list(catalogue.get_products("urn:eop:VITO:TERRASCOPE_S2_FAPAR_V2", tileId="31UFS", start="2021-01-01", end="2021-03-31"))
        self.assertTrue(products)
        for p in products:
            self.assertIsInstance(p.id, str)
            self.assertIsInstance(p.title, str)
            self.assertIsInstance(p.geometry, BaseGeometry)
            self.assertIsInstance(p.bbox, list)
            self.assertIsInstance(p.beginningDateTime, dt.datetime)
            self.assertIsInstance(p.endingDateTime, dt.datetime)
            self.assertIsInstance(p.properties, dict)
            self.assertIsInstance(p.data, list)
            self.assertIsInstance(p.related, list)
            self.assertIsInstance(p.previews, list)
            self.assertIsInstance(p.alternates, list)

            for d in p.data:
                self.assertIsNotNone(d.href)
                self.assertIsNotNone(d.length)

    def test_download_xml(self):
        catalogue = Catalogue()
        title = "S2A_20200101T142731_19HBV_FAPAR_20M_V200"
        products = list(catalogue.get_products("urn:eop:VITO:TERRASCOPE_S2_FAPAR_V2", title=title))
        product = products[0]
        with tempfile.TemporaryDirectory() as dir:
            catalogue.download_file(product.alternates[0], dir)
            self.assertTrue(os.path.isfile(os.path.join(dir, f"{title}.xml")))

    # Manual tests: set the MANUAL_TESTS environment variable to 1 to run these tests.

    @unittest.skipIf(int(os.getenv('MANUAL_TESTS', 0)) == 0, "Run manually to test download with authentication.")
    def test_download(self):
        catalogue = Catalogue().authenticate()
        products = list(catalogue.get_products(
            collection="urn:eop:VITO:TERRASCOPE_S2_FAPAR_V2",
            start="2021-02-01",
            end="2021-02-28",
            tileId="31UGS",
            resolution=20
        ))
        print(len(products))
        with tempfile.TemporaryDirectory() as tempdir:
            catalogue.download_products(products, tempdir)
            for product in products:
                prod_dir = os.path.join(tempdir, product.title)
                self.assertTrue(os.path.isdir(prod_dir))
                for pf in product.data:
                    self.assertTrue(os.path.isfile(os.path.join(prod_dir, os.path.basename(pf.href))))

    @unittest.skipIf(int(os.getenv('MANUAL_TESTS', 0)) == 0, "Run manually to test donwload authorization.")
    def test_authorization_download(self):
        catalogue = Catalogue()  # unauthenticated catalogue instance
        catalogue_auth = Catalogue().authenticate()

        title = "S2A_20200101T142731_19HBV_FAPAR_20M_V200"
        products = list(catalogue.get_products("urn:eop:VITO:TERRASCOPE_S2_FAPAR_V2", title=title))
        product = products[0]
        self.assertFalse(catalogue._is_authorized_to_download(product.data[0]))  # unauthenticated download not possible
        self.assertTrue(catalogue_auth._is_authorized_to_download(product.data[0]))  # authenticated download possible