# TerraCatalogueClient

TerraCatalogueClient is a Python client for the [Terrascope](https://terrascope.be/) EO catalogue. 
This client uses the OpenSearch REST service of the catalogue and makes it easier to query and download EO data products in Python.

More information about the OpenSearch interface can be found in the [Terrascope Documentation](https://docs.terrascope.be/#/Developers/WebServices/TerraCatalogue/TerraCatalogue).

> [!IMPORTANT]
> The Terrascope OpenSearch API is deprecated and its service has been discontinued. Please migrate to the STAC API and its Python ecosystem.
> The [Terrascope documentation](https://docs.terrascope.be/Developers/WebServices/TerraCatalogue/STACAPI.html) explains how to get started with these tools.

## Documentation
Information on the usage of the Python client and a full API overview can be found in [the package documentation](https://vitobelgium.github.io/terracatalogueclient/).

## Installation

This package is published to PyPI and can be installed using `pip`:
```shell
pip install terracatalogueclient
```


## Development
### Building the docs
Install the documentation dependencies:
```shell
pip install -e .[docs]
```

Build the documentation:
```shell
cd docs/
make html
```