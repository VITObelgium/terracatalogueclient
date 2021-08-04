from unittest import TestCase
from unittest.mock import Mock, patch
from terracatalogueclient import Catalogue


class TestMock(TestCase):

    def test_download_force(self):
        with patch.object(Catalogue, "download_product") as mock_download_product:
            catalogue = Catalogue()
            products = list(catalogue.get_products(
                collection="urn:eop:VITO:TERRASCOPE_S2_FAPAR_V2",
                start="2021-02-01",
                end="2021-02-28",
                tileId="31UGS",
                resolution=20
            ))
            catalogue.download_products(products, '/tmp', force=True)

            mock_download_product.assert_called()

    def test_download_confirm(self):
        with patch.object(Catalogue, "download_product") as mock_download_product, \
                patch("builtins.input") as mock_input:
            mock_input.return_value = "y"

            catalogue = Catalogue()
            products = list(catalogue.get_products(
                collection="urn:eop:VITO:TERRASCOPE_S2_FAPAR_V2",
                start="2021-02-01",
                end="2021-02-28",
                tileId="31UGS",
                resolution=20
            ))
            catalogue.download_products(products, '/tmp')

            mock_download_product.assert_called()

    def test_download_abort(self):
        with patch.object(Catalogue, "download_product") as mock_download_product, \
                patch("builtins.input") as mock_input:
            mock_input.return_value = "n"

            catalogue = Catalogue()
            products = list(catalogue.get_products(
                collection="urn:eop:VITO:TERRASCOPE_S2_FAPAR_V2",
                start="2021-02-01",
                end="2021-02-28",
                tileId="31UGS",
                resolution=20
            ))
            catalogue.download_products(products, '/tmp')

            mock_download_product.assert_not_called()