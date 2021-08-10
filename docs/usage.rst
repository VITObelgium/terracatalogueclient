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

Check the :obj:`~terracatalogueclient.config.CatalogueConfig` API for more information on how to load a configuration file. If no configuration is supplied, the default Terrascope configuration will be used::

    from terracatalogueclient import Catalogue
    catatalogue = Catalogue()  # catalogue with default Terrascope configuration

A configuration file has the following structure. The default configuration is used as an example:

.. literalinclude:: ../terracatalogueclient/resources/terrascope.ini
    :language: ini

Query collections
-----------------

Get all available collections and print the collection identifiers and their titles::

    from terracatalogueclient import Catalogue
    catatalogue = Catalogue()
    collections = catatalogue.get_collections()
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
    If your product query has more than 10,000 results, a :obj:`~terracatalogueclient.exceptions.TooManyResultsException` will be raised.

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
A catalogue may support multiple data access methods. Based on the ``accessedFrom`` search parameter supplied when querying products, the product file links will be provided for your prefered access method.
The default value is HTTP, but other options are S3 and MEP (local paths). This data access method will be used later when downloading the products.

.. note::
    The Terrascope catalogue doesn't support the S3 data access method.

For downloading products over S3, make sure to use the ``accessedFrom="S3"`` parameter in the product search::

    products = catalogue.get_products(
        collection=collection,
        start="2021-01-01",
        end="2021-02-01",
        tileId="31UES",
        accessedFrom="S3"
    )
    # download automatically selects the access method specified when querying the products
    catalogue.download_products(products, path)
