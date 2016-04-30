#!/usr/bin/env python

from setuptools import setup

setup(
    name="pytools",
    version="1.0.0",
    description="Python tools for MetaBrainz projects",
    author="MetaBrainz Foundation",
    author_email="support@metabrainz.org",
    py_modules=["pytools"],
    install_requires=open("requirements.txt").read().split(),
)
