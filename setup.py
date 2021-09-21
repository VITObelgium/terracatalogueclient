from setuptools import setup, find_packages
import re

with open('terracatalogueclient/__init__.py', 'r') as fd:
    __version__ = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                            fd.read(), re.MULTILINE).group(1)

version = __version__

setup(
    name="terracatalogueclient",
    version=version,
    author="Stijn Caerts",
    author_email="stijn.caerts@vito.be",
    description="Client for the Terrascope EO catalogue",
    url="https://github.com/VITObelgium/terracatalogueclient",
    packages=find_packages(),
    package_data={"": ["resources/*"]},
    install_requires=["requests", "requests-auth>=5.3.0", "shapely", "humanfriendly", "boto3"],
    test_suite="tests",
    tests_require=["pytest"],
    setup_requires=["pytest-runner"],
    extras_require={
        "docs": ["sphinx", "sphinx-autodoc-typehints"]
    }
)
