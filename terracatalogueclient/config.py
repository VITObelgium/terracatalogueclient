import configparser
import pkgutil


class CatalogueConfig:

    def __init__(self, config: configparser.ConfigParser):
        self.config = config

        # Catalogue
        self.catalogue_url = config.get("Catalogue", "URL").rstrip("/") + "/"

        # Auth
        self.oidc_client_id = config.get("Auth", "ClientId")
        self.oidc_token_endpoint = config.get("Auth", "TokenEndpoint")
        self.oidc_authorization_endpoint = config.get("Auth", "AuthorizationEndpoint")

        # S3
        self.s3_access_key = config.get("S3", "AccessKey")
        self.s3_secret_key = config.get("S3", "SecretKey")
        self.s3_endpoint_url = config.get("S3", "EndpointUrl")

    @staticmethod
    def get_default_config() -> 'CatalogueConfig':
        config = configparser.ConfigParser()
        config.read_string(pkgutil.get_data(__name__, "resources/terrascope.ini").decode())
        return CatalogueConfig(config)

    @staticmethod
    def from_file(path: str) -> 'CatalogueConfig':
        """
        Load a catalogue configuration file.

        :param path: path of the catalogue .ini configuration file
        :return: CatalogueConfig object
        """
        config = configparser.ConfigParser()
        config.read(path)
        return CatalogueConfig(config)