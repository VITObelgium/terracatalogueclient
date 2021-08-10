from unittest import TestCase
from unittest.mock import patch
from terracatalogueclient import Catalogue, ProductFile


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

    def test_download_method_http(self):
        with patch.object(Catalogue, "_download_file_http") as mock_download_file_http:
            catalogue = Catalogue()
            href = "https://phenology.vgt.vito.be/download/VI_V101/2016/10/01/VI_20161001T092022_S2A_T34SDG-010m_V101_QFLAG2.tif"
            length = 495702
            product_file = ProductFile(href, length)
            catalogue.download_file(product_file, "/tmp")
            mock_download_file_http.assert_called_once()

    def test_download_method_s3(self):
        with patch.object(Catalogue, "_download_file_s3") as mock_download_file_s3:
            catalogue = Catalogue()
            href = "s3://b7bef1640a4a4ecca1e8ca04a70cd472:hr-vpp-products-vi-101-201610/01/VI_20161001T092022_S2A_T34SDG-010m_V101_QFLAG2.tif"
            length = 495702
            product_file = ProductFile(href, length)
            catalogue.download_file(product_file, "/tmp")
            mock_download_file_s3.assert_called_once()