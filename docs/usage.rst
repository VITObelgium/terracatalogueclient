Usage
=====

On this page, some code examples are listed to get you started.


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

For querying products, the :meth:`~terracatalogueclient.client.Catalogue.get_products` method can ne used.
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

