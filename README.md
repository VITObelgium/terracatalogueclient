# TerraCatalogueClient

TerraCatalogueClient is a Python client for the [Terrascope](https://terrascope.be/) EO catalogue. 
This client uses the OpenSearch REST service of the catalogue and makes it easier to query and download EO data products in Python.

More information about the OpenSearch interface can be found in the [Terrascope Documentation](https://docs.terrascope.be/#/Developers/WebServices/TerraCatalogue/TerraCatalogue).

## Documentation
Information on the usage of the Python client and a full API overview can be found in [the package documentation](https://vitobelgium.github.io/terracatalogueclient/).

## Installation

This package is available in the public Terrascope PyPi repository and can be installed using `pip`:
- add the Terrascope PyPi repository in your [`pip` configuration file](https://pip.pypa.io/en/stable/user_guide/#configuration)
    ```
    [global]
    index-url = https://artifactory.vgt.vito.be/artifactory/api/pypi/python-packages/simple
    ```
- install the `terracatalogueclient` package
    ```
    $ pip install terracatalogueclient
    ```

When you are using a [Terrascope Virtual Machine (VM) or Notebooks](https://terrascope.be/en/services), 
the package is already pre-installed for you.

## Development
### Building the docs
Install the documentation dependencies:
```
$ pip install -e .[docs]
```

Build the documentation:
```
$ cd docs/
$ make html
```