from setuptools import setup
import re

with open('terracatalogueclient/__init__.py', 'r') as fd:
    __version__ = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                            fd.read(), re.MULTILINE).group(1)

version = __version__

setup()
