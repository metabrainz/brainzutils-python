# TODO: We are the backport of importlib to support python 3.7.
#  When we raise the minimum to python 3.8, we can remove this and use the builtin importlib module.
from importlib_metadata import version, PackageNotFoundError

try:
    __version__ = version(__name__)
except PackageNotFoundError:
    # package is not installed
    pass
