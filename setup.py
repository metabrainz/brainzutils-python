#!/usr/bin/env python

from setuptools import setup, find_packages
from brainzutils import __version__

setup(
    name="brainzutils",
    version=__version__,
    description="Python tools for MetaBrainz projects",
    author="MetaBrainz Foundation",
    author_email="support@metabrainz.org",
    py_modules=["brainzutils"],
    packages=find_packages(),
    install_requires=open("requirements.txt").read().split(),
)
