.. terracatalogueclient documentation master file, created by
   sphinx-quickstart on Mon May 10 14:57:30 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

TerraCatalogueClient: a Python client for the Terrascope catalogue
==================================================================

TerraCatalogueClient is a Python client for the `Terrascope <https://terrascope.be/>`_ and `HRVPP <https://land.copernicus.eu/pan-european/biophysical-parameters/high-resolution-vegetation-phenology-and-productivity>`_ EO catalogues.
This client uses the OpenSearch REST service of the catalogue and makes it easier to query and download EO data products in Python.

.. warning::
    The Terrascope OpenSearch API is deprecated and its service has been discontinued. Please migrate to the STAC API and its Python ecosystem. The `Terrascope documentation <https://docs.terrascope.be/Developers/WebServices/TerraCatalogue/STACAPI.html>`_ explains how to get started with these tools.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   usage
   api

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
