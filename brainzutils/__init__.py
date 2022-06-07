import sys

if sys.version_info >= (3, 10):
    from importlib.metadata import version, PackageNotFoundError
else:
    # importlib.metadata's API changed in 3.10, so use a backport for versions less than this.
    from importlib_metadata import version, PackageNotFoundError

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    # package is not installed
    __version__ = "unknown"
