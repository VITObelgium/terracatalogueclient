import configparser
import pkgutil
import os
from enum import Enum


class CatalogueEnvironment(Enum):
    """Catalogue environment object."""

    TERRASCOPE = "terrascope.ini"
    HRVPP = "hrvpp.ini"
    CGLS = "cgls.ini"


class CatalogueConfig:
    """Catalogue configuration object."""

    def __init__(self, config: configparser.ConfigParser):
        """
        :param config: configuration
        """
        self.config = config

        # Catalogue
        self.catalogue_url = config.get("Catalogue", "URL").rstrip("/") + "/"

        # Auth
        self.oidc_client_id = config.get("Auth", "ClientId")
        self.oidc_client_secret = config.get("Auth", "ClientSecret")
        self.oidc_token_endpoint = config.get("Auth", "TokenEndpoint")
        self.oidc_authorization_endpoint = config.get("Auth", "AuthorizationEndpoint")
        self.oidc_interactive_supported = config.getboolean(
            "Auth", "InteractiveSupported"
        )
        self.oidc_non_interactive_supported = config.getboolean(
            "Auth", "NonInteractiveSupported"
        )

        # HTTP
        self.http_download_chunk_size = config.getint("HTTP", "ChunkSize")

        # S3
        self.s3_endpoint_url = config.get("S3", "EndpointUrl")
        # allow override of S3 credentials using environment variables
        if "AWS_ACCESS_KEY_ID" in os.environ and os.environ["AWS_ACCESS_KEY_ID"]:
            self.s3_access_key = os.environ["AWS_ACCESS_KEY_ID"]
        else:
            self.s3_access_key = config.get("S3", "AccessKey")

        if (
            "AWS_SECRET_ACCESS_KEY" in os.environ
            and os.environ["AWS_SECRET_ACCESS_KEY"]
        ):
            self.s3_secret_key = os.environ["AWS_SECRET_ACCESS_KEY"]
        else:
            self.s3_secret_key = config.get("S3", "SecretKey")

    @staticmethod
    def get_default_config() -> "CatalogueConfig":
        return CatalogueConfig.from_environment(CatalogueEnvironment.TERRASCOPE)

    @staticmethod
    def from_file(path: str) -> "CatalogueConfig":
        """
        Get a catalogue configuration object from a configuration file.

        :param path: path of the catalogue .ini configuration file
        :return: CatalogueConfig object
        """
        return CatalogueConfig.from_environment(CatalogueEnvironment.TERRASCOPE, path)

    @staticmethod
    def from_environment(
        environment: CatalogueEnvironment, path: str = None
    ) -> "CatalogueConfig":
        """
        Get a catalogue configuration object from a pre-defined environment.

        :param environment: the pre-defined environment
        :param path: optional path of the catalogue .ini configuration file containing values to override the
            pre-defined environment config
        :return: CatalogueConfig object
        """
        config = configparser.ConfigParser()
        # read the default config first to populate default values
        config.read_string(
            pkgutil.get_data(__name__, "resources/" + environment.value).decode()
        )
        if path is not None:
            # apply values from custom config
            config.read(path)

        return CatalogueConfig(config)
