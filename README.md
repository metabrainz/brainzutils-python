# BrainzUtils for Python

This is a package with common utilities that are used throughout MetaBrainz
projects that use Python programming language.

Please report issues at https://tickets.musicbrainz.org/browse/BU.

## Usage

You can include this line into a `requirements.txt` file:

    git+https://github.com/metabrainz/brainzutils-python.git@<VERSION>

Replace `<VERSION>` with the tag that you want to reference.
See https://github.com/metabrainz/brainzutils-python/releases.

## Release process

For this project we are using [semantic versioning](http://semver.org/). If
you want to make a new release:

1. Create a new tag in git using the following format: `v<MAJOR>.<MINOR>.<PATCH>`.
2. Create a release on GitHub based on that tag. Specify changes that were made.

When updating underlying dependencies keep in mind breaking changes that they
might have. Update version of `brainzutils-python` accordingly.
