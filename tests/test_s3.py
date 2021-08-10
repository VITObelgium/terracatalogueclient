import unittest
from unittest.mock import patch, Mock
from terracatalogueclient import Catalogue, ProductFile


class TestS3(unittest.TestCase):

    def test_s3_download_mock(self):
        with patch.object(Catalogue, "_init_s3_client") as mock_init_s3_client:
            catalogue = Catalogue()
            catalogue.s3 = Mock()
            href = "s3://b7bef1640a4a4ecca1e8ca04a70cd472:hr-vpp-products-vi-101-201610/01/VI_20161001T092022_S2A_T34SDG-010m_V101_QFLAG2.tif"
            length = 495702
            file = ProductFile(href, length)
            catalogue.download_file(file, "/tmp")
            catalogue.s3.Bucket.assert_called_with("b7bef1640a4a4ecca1e8ca04a70cd472:hr-vpp-products-vi-101-201610")
            catalogue.s3.Bucket.return_value.download_file.assert_called_with(
                "01/VI_20161001T092022_S2A_T34SDG-010m_V101_QFLAG2.tif",
                "/tmp/VI_20161001T092022_S2A_T34SDG-010m_V101_QFLAG2.tif"
            )