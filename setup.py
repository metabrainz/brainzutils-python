#!/usr/bin/env python

from setuptools import setup, find_packages
from pytools import __version__

setup(
    name="pytools",
    version=__version__,
    description="Python tools for MetaBrainz projects",
    author="MetaBrainz Foundation",
    author_email="support@metabrainz.org",
    py_modules=["pytools"],
    packages=find_packages(),
    install_requires=open("requirements.txt").read().split(),
)
