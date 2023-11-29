Installation
============

.. note::
    When you are using a `Terrascope Virtual Machine (VM) or Notebooks <https://terrascope.be/en/services>`_,
    the package is already pre-installed for you.


This package is available in the public Terrascope PyPi repository and can be installed using ``pip``::

    $ pip install --extra-index-url https://artifactory.vgt.vito.be/artifactory/api/pypi/python-packages/simple terracatalogueclient


Alternatively, you can configure ``pip`` to use the Terrascope repository by default:

- add the Terrascope PyPi repository in your `pip configuration file <https://pip.pypa.io/en/stable/user_guide/#configuration>`_::

    [global]
    extra-index-url = https://artifactory.vgt.vito.be/artifactory/api/pypi/python-packages/simple

- install the ``terracatalogueclient`` package::

    $ pip install terracatalogueclient

