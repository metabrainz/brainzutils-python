#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name="brainzutils",
    description="Python tools for MetaBrainz projects",
    author="MetaBrainz Foundation",
    author_email="support@metabrainz.org",
    py_modules=["brainzutils"],
    python_requires='>=3.7',
    packages=find_packages(),
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    install_requires=open("requirements.txt").read().splitlines(),
)
