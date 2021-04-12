# BrainzUtils for Python

This is a package with common utilities that are used throughout MetaBrainz
projects that use Python programming language.

Note that v1.18.* will be the last line of releases compatible with Python 2.

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

       git tag v1.x.0
       git push --tags

2. Create a release on GitHub based on that tag. Specify changes that were made.
  https://github.com/metabrainz/brainzutils-python/releases/new

When updating underlying dependencies keep in mind breaking changes that they
might have. Update version of `brainzutils-python` accordingly.

## License

```
brainzutils - Python utilities for MetaBrainz projects
Copyright (C) 2018  MetaBrainz Foundation Inc.

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
```
