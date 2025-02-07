Installation
============

.. note::
    When you are using a `Terrascope Virtual Machine (VM) or Notebooks <https://terrascope.be/en/services>`_,
    the package is already pre-installed for you.


This package is available both in PyPI and the public Terrascope repository and can be installed using ``pip``.

**From PyPI**

    $ pip install terracatalogueclient

**From the Terrascope repository**

    $ pip install --extra-index-url https://artifactory.vgt.vito.be/artifactory/api/pypi/python-packages-public/simple terracatalogueclient


Alternatively, you can configure ``pip`` to use the Terrascope repository as an additional package source:

- add the Terrascope PyPI repository in your `pip configuration file <https://pip.pypa.io/en/stable/user_guide/#configuration>`_::

    [global]
    extra-index-url = https://artifactory.vgt.vito.be/artifactory/api/pypi/python-packages-public/simple

- install the ``terracatalogueclient`` package::

    $ pip install terracatalogueclient

