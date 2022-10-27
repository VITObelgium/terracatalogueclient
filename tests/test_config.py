import unittest

import os

from terracatalogueclient.config import CatalogueConfig
from terracatalogueclient.config import CatalogueEnvironment

test_resource_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources")


class TestConfig(unittest.TestCase):

    def test_environment_terrascope(self):
        config = CatalogueConfig.from_environment(CatalogueEnvironment.TERRASCOPE)
        self.assertEqual('https://services.terrascope.be/catalogue/', config.catalogue_url)

    def test_environment_hrvpp(self):
        config = CatalogueConfig.from_environment(CatalogueEnvironment.HRVPP)
        self.assertEqual('https://phenology.vgt.vito.be/', config.catalogue_url)

    def test_override_from_file(self):
        config = CatalogueConfig.from_file(os.path.join(test_resource_dir, "override.ini"))
        self.assertEqual(4096, config.http_download_chunk_size)

    def test_override_from_environment(self):
        config = CatalogueConfig.from_environment(CatalogueEnvironment.TERRASCOPE,
                                                  os.path.join(test_resource_dir, "override.ini"))
        self.assertEqual(4096, config.http_download_chunk_size)
