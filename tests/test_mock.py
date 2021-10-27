from unittest import TestCase
from unittest.mock import patch
from terracatalogueclient import Catalogue, ProductFile, Product, ProductFileType
from terracatalogueclient.client import _parse_date
import os


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

    def test_download_file_type_filter(self):
        product = Product(
            "urn:eop:VITO:TERRASCOPE_S2_NDVI_V2:S2A_20150704T101006_32TML_NDVI_10M_V200",
            "S2A_20150704T101006_32TML_NDVI_10M_V200",
            None,
            [8.2009294, 40.5584724, 9.1170316, 41.5517851],
            _parse_date("2015-07-04T10:10:06.027Z"),
            _parse_date("2015-07-04T10:10:06.027Z"),
            None,
            data=[ProductFile(
                "https://services.terrascope.be/download/Sentinel2/NDVI_V2/2015/07/04/S2A_20150704T101006_32TML_NDVI_V200/S2A_20150704T101006_32TML_NDVI_10M_V200.tif",
                39500389, "NDVI_10M", "image/tiff"
            )],
            related=[ProductFile(
                "https://services.terrascope.be/download/Sentinel2/NDVI_V2/2015/07/04/S2A_20150704T101006_32TML_NDVI_V200/S2A_20150704T101006_32TML_SCENECLASSIFICATION_20M_V200.tif",
                1521972, "SCENECLASSIFICATION_20M", "image/tiff", "QUALITY"
            )],
            previews=[ProductFile(
                "https://services.terrascope.be/download/Sentinel2/NDVI_V2/2015/07/04/S2A_20150704T101006_32TML_NDVI_V200/S2A_20150704T101006_32TML_NDVI_QUICKLOOK_V200.tif",
                182760, None, "image/tiff", "QUICKLOOK"
            )],
            alternates=[ProductFile(
                "https://services.terrascope.be/download/Sentinel2/NDVI_V2/2015/07/04/S2A_20150704T101006_32TML_NDVI_V200/S2A_20150704T101006_32TML_NDVI_10M_V200.xml",
                32523, "Inspire metadata", "application/vnd.iso.19139+xml"
            )]
        )

        with patch.object(Catalogue, "download_file") as mock_download_file:
            catalogue = Catalogue()
            tmp_dir = "/tmp"
            download_dir = os.path.join(tmp_dir, product.id.split(":")[-1])

            # only download data files
            catalogue.download_product(product, tmp_dir, ProductFileType.DATA)
            mock_download_file.assert_called_once_with(product.data[0], download_dir)
            mock_download_file.reset_mock()

            # download all files
            catalogue.download_products([product], tmp_dir, force=True)
            self.assertEqual(4, mock_download_file.call_count)
            call_args = [call_args.args for call_args in mock_download_file.call_args_list]
            for pf in product.data + product.related + product.previews + product.alternates:
                self.assertIn((pf, download_dir), call_args)
            mock_download_file.reset_mock()

            # combine file types
            catalogue.download_product(product, tmp_dir, ProductFileType.DATA | ProductFileType.RELATED)
            self.assertEqual(2, mock_download_file.call_count)
            call_args = [call_args.args for call_args in mock_download_file.call_args_list]
            for pf in product.data + product.related:
                self.assertIn((pf, download_dir), call_args)
