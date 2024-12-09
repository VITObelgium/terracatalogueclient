from setuptools import setup, find_packages
import re

with open("terracatalogueclient/__init__.py", "r") as fd:
    __version__ = re.search(
        r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', fd.read(), re.MULTILINE
    ).group(1)

version = __version__

with open("README.md", "r") as mdf:
    readme_content = mdf.read()

setup(
    name="terracatalogueclient",
    version=version,
    author="Stijn Caerts",
    author_email="stijn.caerts@vito.be",
    description="Client for the Terrascope EO catalogue",
    long_description=readme_content,
    long_description_content_type="text/markdown",
    url="https://github.com/VITObelgium/terracatalogueclient",
    packages=find_packages(),
    package_data={"": ["resources/*"]},
    install_requires=[
        "requests",
        "requests-auth~=6.0",
        "shapely",
        "humanfriendly",
        "boto3",
    ],
    test_suite="tests",
    tests_require=["pytest"],
    setup_requires=["pytest-runner"],
    extras_require={
        "docs": ["sphinx", "sphinx-autodoc-typehints"],
        "dev": ["pre-commit", "ruff"],
    },
)
