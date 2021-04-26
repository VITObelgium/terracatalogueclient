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
    description="Client for the Terrascope OpenSearch catalogue",
    url="https://git.vito.be/projects/BIGGEO/repos/terracatalogueclient",
    packages=find_packages(),
    install_requires=["requests", "requests-auth", "shapely"],
    test_suite="tests",
    tests_require=["pytest"],
    setup_requires=["pytest-runner"]
)
