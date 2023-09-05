Usage
=====

On this page, some code examples are listed to get you started.

Catalogue configuration
-----------------------
When you create a catalogue object, you can provide a configuration file with the details of the catalogue you wish to connect to::

    from terracatalogueclient import Catalogue
    from terracatalogueclient.config import CatalogueConfig

    config = CatalogueConfig.from_file("/path/to/configuration.ini")
    catalogue = Catalogue(config)  # catalogue with custom configuration

Check the :obj:`~terracatalogueclient.config.CatalogueConfig` API for more information on how to load a configuration file.

Terrascope configuration
^^^^^^^^^^^^^^^^^^^^^^^^

If no configuration is supplied, the default `Terrascope <https://terrascope.be/>`_ configuration will be used::

    from terracatalogueclient import Catalogue
    catalogue = Catalogue()  # catalogue with default Terrascope configuration

A configuration file has the following structure. The default configuration is used as an example:

.. literalinclude:: ../terracatalogueclient/resources/terrascope.ini
    :language: ini

Pre-defined configurations
^^^^^^^^^^^^^^^^^^^^^^^^^^
The ``terracatalogueclient`` also supports other catalogues:

* `HR-VPP <https://land.copernicus.eu/pan-european/biophysical-parameters/high-resolution-vegetation-phenology-and-productivity>`_
* `Copernicus Global Land Service (CGLS) <https://land.copernicus.eu/global/>`_

We include pre-defined configurations for them. The following code snippet shows how to initialize the client for use with the HR-VPP catalogue::

    from terracatalogueclient import Catalogue
    from terracatalogueclient.config import CatalogueConfig, CatalogueEnvironment

    config = CatalogueConfig.from_environment(CatalogueEnvironment.HRVPP)
    catalogue = Catalogue(config)

For CGLS, the :attr:`~terracatalogueclient.config.CatalogueEnvironment.CGLS` :obj:`~terracatalogueclient.config.CatalogueEnvironment` can be used.

Authentication
--------------
Downloading products and accessing protected collections may require you to authenticate. This is done by first creating a catalogue object and subsequently calling the :meth:`~terracatalogueclient.client.Catalogue.authenticate` or :meth:`~terracatalogueclient.client.Catalogue.authenticate_non_interactive` method.
The :meth:`~terracatalogueclient.client.Catalogue.authenticate` method will open a browser window to provide you with a login form::

    from terracatalogueclient import Catalogue
    catalogue = Catalogue().authenticate()  # authenticated catalogue

The :meth:`~terracatalogueclient.client.Catalogue.authenticate_non_interactive` method uses the provided username and password directly to obtain an access token. However, it is a bad practice to store your credentials directly in a script!

.. note::
    The CGLS catalogue doesn't require authentication to download products.

Query collections
-----------------

Get all available collections and print the collection identifiers and their titles::

    from terracatalogueclient import Catalogue
    catalogue = Catalogue()
    collections = catalogue.get_collections()
    for c in collections:
        print(f"{c.id} - {c.properties['title']}")


Query collections based on the acquisition platform:

>>> collections = catalogue.get_collections(platform="SENTINEL-1")


Note that the :meth:`~terracatalogueclient.client.Catalogue.get_collections` method returns an ``Iterator`` of
:obj:`~terracatalogueclient.client.Collection` objects. If you want to iterate multiple times over the collections,
you can wrap the iterator in a list, but this will also load all results in memory:

>>> collections_list = list(catalogue.get_collections())


To get more information on the available query parameters, you can take a look at the
:meth:`~terracatalogueclient.client.Catalogue.get_collections` method in the :doc:`api`.
The `OpenSearch Description Document <https://docs.terrascope.be/#/Developers/WebServices/TerraCatalogue/TerraCatalogue?id=the-opensearch-description-document>`_ contains a complete list of all supported parameters.


Query products
--------------

For querying products, the :meth:`~terracatalogueclient.client.Catalogue.get_products` method can be used.
The collection identifier is the only mandatory parameter for this method.

Get Sentinel-2 NDVI products for May 2020 with tile identifier 31UGS::

    products = catalogue.get_products(
        "urn:eop:VITO:TERRASCOPE_S2_NDVI_V2",
        start=dt.date(2020, 5, 1),
        end=dt.date(2020, 6, 1),
        tileId="31UGS"
    )
    for product in products:
        print(product.title)

Note that the :meth:`~terracatalogueclient.client.Catalogue.get_products` method returns an ``Iterator`` of
:obj:`~terracatalogueclient.client.Product` objects. If you want to iterate multiple times over these products,
you can wrap the iterator in a list, but this will also load all results in memory:

>>> products_list = list(catalogue.get_products(...))


.. note::
    If your product query has more results than supported by the pagination of the catalogue, a :obj:`~terracatalogueclient.exceptions.TooManyResultsException` will be raised.

There is a separate method to get product counts: :meth:`~terracatalogueclient.client.Catalogue.get_product_count`. This method is much more efficient than first retrieving all products and then counting them.
Here is a query to get the number of products per collection for 2019::

    collections = catalogue.get_collections()
    for collection in collections:
        count = catalogue.get_product_count(
            collection.id,
            start=dt.date(2019, 1, 1),
            end=dt.date(2020, 1, 1)
        )
        print(f"{collection.id}: {count}")


To get more information on the available query parameters, you can take a look at the
:meth:`~terracatalogueclient.client.Catalogue.get_products` method in the :doc:`api`.
The collection specific `OpenSearch Description Document <https://docs.terrascope.be/#/Developers/WebServices/TerraCatalogue/TerraCatalogue?id=the-opensearch-description-document>`_ contains a complete list of all supported parameters for a product query.


Download products
-----------------
.. note::
    If you are working on the Terrascope Notebooks or VM, you don't have to download products. They are already locally available.
    To get the local path of the products, use the ``accessedFrom="MEP"`` parameter in the product search::

        products = catalogue.get_products(
            collection="urn:eop:VITO:TERRASCOPE_S2_FAPAR_V2",
            start="2021-02-01",
            end="2021-02-28",
            tileId="31UGS",
            resolution=20,
            accessedFrom="MEP"  # get local path
        )

        # href of the product file now contains the local path
        local_paths = [pf.href for p in products for pf in p.data]

Download methods
^^^^^^^^^^^^^^^^
A catalogue may support multiple data access methods. Based on the ``accessedFrom`` search parameter supplied when querying products, the product file links will be provided for your preferred access method.
The default value is HTTP, but other options are (amongst others) S3 and MEP (local paths). This data access method will be used later when downloading the products.

.. note::
    The Terrascope catalogue doesn't support the S3 data access method. Consult the OpenSearch Description Document
    (endpoint '/description') to get allowed values per deployment (Terrascope, HRVPP).

For downloading products over S3, make sure to use the ``accessedFrom="S3"`` parameter in the product search.
Also specify the S3 endpoint and S3 credentials, either in the configuration file or using environment variables::

    products = catalogue.get_products(
        collection=collection,
        start="2021-01-01",
        end="2021-02-01",
        tileId="31UES",
        accessedFrom="S3"
    )
    # download automatically selects the access method specified when querying the products
    catalogue.download_products(products, path)

Filter files
^^^^^^^^^^^^
It is possible to filter out the files that are of interest for you. By default, all product files will be downloaded.
The filtering is handled by the ``file_types`` parameter of the download method.
This parameter expects an enum flag of type :obj:`~terracatalogueclient.client.ProductFileType`.
You can combine multiple of these flags to download several types of product files. This is done with the ``|`` operator.

The following example will download the data files and related resources (eg. cloud mask):

>>> catalogue.download_product(product, path, ProductFileType.DATA | ProductFileType.RELATED)

Check the :doc:`api` for a full overview of the download methods (:meth:`~terracatalogueclient.client.Catalogue.download_product` or :meth:`~terracatalogueclient.client.Catalogue.download_products`) and the :obj:`~terracatalogueclient.client.ProductFileType` enum flag.