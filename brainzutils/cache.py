# pylint: disable=invalid-name
"""
This module serves as an interface for Redis.

Module needs to be initialized before use! See init() function.

It basically is a wrapper for redis package with additional
functionality and tweaks specific to serve our needs.

There's also support for namespacing, which simplifies management of different
versions of data saved in the cache. You can invalidate whole namespace using
invalidate_namespace() function. See its description for more info.

More information about Redis can be found at http://redis.io/.
"""
from functools import wraps
import shutil
import hashlib
import tempfile
import datetime
import os.path
import re
import redis
import msgpack
from brainzutils import locks


_r = None  # type: redis.StrictRedis
_glob_namespace = None  # type: bytes
_ns_versions_loc = None  # type: str


SHA1_LENGTH = 40
MAX_KEY_LENGTH = 250
NS_VERSIONS_LOC_DIR = "namespace_versions"
NS_REGEX = re.compile('[a-zA-Z0-9_-]+$')
CONTENT_ENCODING = "utf-8"
ENCODING_ASCII = "ascii"


def init(host="localhost", port=6379, db_number=0, namespace="", ns_versions_loc=None):
    """Initializes Redis client. Needs to be called before use.

    Namespace versions are stored in a local directory.

    Args:
        host (str): Redis server hostname.
        port (int): Redis port.
        db_number (int): Redis database number.
        namespace (str): Global namespace that will be prepended to all keys.
        ns_versions_loc (str): Path to directory where namespace versions will
            be stored. If not specified, creates a temporary directory that uses
            global namespace as a reference to make sure availability to multiple
            processes. See NS_VERSIONS_LOC_DIR value in this module and implementation.
    """
    global _r, _glob_namespace, _ns_versions_loc
    _r = redis.StrictRedis(
        host=host,
        port=port,
        db=db_number,
    )

    _glob_namespace = namespace + ":"
    _glob_namespace = _glob_namespace.encode(ENCODING_ASCII)
    if len(_glob_namespace) + SHA1_LENGTH > MAX_KEY_LENGTH:
        raise ValueError("Namespace is too long.")

    if ns_versions_loc:
        if not os.path.isdir(ns_versions_loc):
            raise ValueError("Can't find directory for storing namespace versions! "
                             "Please check `version_location` argument.")
    else:
        ns_versions_loc = os.path.join(tempfile.gettempdir(), NS_VERSIONS_LOC_DIR)
    _ns_versions_loc = os.path.join(ns_versions_loc, namespace)
    if not os.path.exists(_ns_versions_loc):
        os.makedirs(_ns_versions_loc)


def delete_ns_versions_dir():
    if os.path.isdir(_ns_versions_loc):
        shutil.rmtree(_ns_versions_loc)


def init_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not _r:
            raise RuntimeError("Cache module needs to be initialized before "
                               "use! See documentation for more info.")
        return f(*args, **kwargs)
    return decorated


# pylint: disable=redefined-builtin
@init_required
def set(key, val, time=0, namespace=None):
    """Set a key to a given value.

    Args:
        key: Key of the item.
        val: Item's value.
        time: The time after which this value should expire, either as a delta
            number of seconds, or an absolute unix time-since-the-epoch value.
            If set to 0, value will be stored "forever".
        namespace: Optional namespace in which key needs to be defined.

    Returns:
        True if stored successfully.
    """
    # Note that both key and value are encoded before insertion.
    return set_many({key: val}, time, namespace)


@init_required
def get(key, namespace=None):
    """Retrieve an item.

    Args:
        key: Key of the item that needs to be retrieved.
        namespace: Optional namespace in which key was defined.

    Returns:
        Stored value or None if it's not found.
    """
    # Note that key is encoded before retrieval request.
    return get_many([key], namespace).get(key)


@init_required
def delete(key, namespace=None):
    """Delete an item.

    Args:
        key: Key of the item that needs to be deleted.
        namespace: Optional namespace in which key was defined.

    Returns:
          Number of keys that were deleted.
    """
    # Note that key is encoded before deletion request.
    return delete_many([key], namespace)


@init_required
def set_many(mapping, time=None, namespace=None):
    """Set multiple keys doing just one query.

    Args:
        mapping (dict): A dict of key/value pairs to set.
        time (int): Time to store the keys (in milliseconds).
        namespace (str): Namespace for the keys.

    Returns:
        True on success.
    """
    # TODO: Fix return value
    result = _r.mset(_prep_dict(mapping, namespace))
    if time:
        for key in _prep_keys_list(list(mapping.keys()), namespace):
            _r.pexpire(_prep_key(key, namespace), time)

    return result


@init_required
def get_many(keys, namespace=None):
    """Retrieve multiple keys doing just one query.

    Args:
        keys (list): List of keys that need to be retrieved.
        namespace (str): Namespace for the keys.

    Returns:
        A dictionary of key/value pairs that were available.
    """
    result = {}
    for i, value in enumerate(_r.mget(_prep_keys_list(keys, namespace))):
        result[keys[i]] = _decode_val(value)
    return result


@init_required
def delete_many(keys, namespace=None):
    """Delete multiple keys.

    Returns:
        Number of keys that were deleted.
    """
    return _r.delete(*_prep_keys_list(keys, namespace))


@init_required
def flush_all():
    _r.flushdb()


def gen_key(key, *attributes):
    """Helper function that generates a key with attached attributes.

    Args:
        key: Original key.
        attributes: Attributes that will be appended a key.

    Returns:
        Key that can be used with cache.
    """
    if not isinstance(key, str):
        key = str(key)
    key = key.encode(ENCODING_ASCII, errors='xmlcharrefreplace')

    for attr in attributes:
        if not isinstance(attr, str):
            attr = str(attr)
        key += b'_' + attr.encode(ENCODING_ASCII, errors='xmlcharrefreplace')

    key = key.replace(b' ', b'_')  # spaces are not allowed

    return key


def _prep_dict(dictionary, namespace=None):
    """Wrapper for _prep_key and _encode_val functions that works with dictionaries."""
    if namespace:
        namespace_and_version = _append_namespace_version(namespace)
    else:
        namespace_and_version = None
    return {_prep_key(key, namespace_and_version): _encode_val(value)
            for key, value in dictionary.items()}


def _prep_key(key, namespace_and_version=None):
    """Prepares a key for use with Redis."""
    # TODO(roman): Check if this is actually required for Redis.
    if namespace_and_version:
        key = "%s:%s" % (namespace_and_version, key)
    if not isinstance(key, bytes):
        key = key.encode(ENCODING_ASCII, errors='xmlcharrefreplace')
    key = hashlib.sha1(key).hexdigest().encode(ENCODING_ASCII)
    return _glob_namespace + key


def _prep_keys_list(l, namespace=None):
    """Wrapper for _prep_key function that works with lists.

    Returns:
        Prepared keys in the same order.
    """
    if namespace:
        namespace_and_version = _append_namespace_version(namespace)
    else:
        namespace_and_version = None
    return [_prep_key(k, namespace_and_version) for k in l]


@init_required
def _append_namespace_version(namespace):
    version = get_namespace_version(namespace)
    if version is None:  # namespace isn't initialized
        version = invalidate_namespace(namespace)
    return "%s:%s" % (namespace, version)


def _encode_val(value):
    if value is None:
        return value
    return msgpack.packb(value, use_bin_type=True, default=_msgpack_default)


def _decode_val(value):
    if value is None:
        return value
    return msgpack.unpackb(value, encoding=CONTENT_ENCODING, ext_hook=_msgpack_ext_hook)


############
# NAMESPACES
############


@init_required
def invalidate_namespace(namespace):
    """Invalidates specified namespace.

    Invalidation is done by incrementing version of the namespace

    Args:
        namespace: Namespace that needs to be invalidated.

    Returns:
        New version number.
    """
    validate_namespace(namespace)
    current_version = get_namespace_version(namespace)
    if current_version is None:  # namespace isn't initialized
        new_version = 1
    else:
        new_version = current_version + 1
    with locks.locked_open(_get_ns_version_file_path(namespace), mode=locks.M_WRITE) as f:
        f.write(str(new_version).encode(ENCODING_ASCII))
    return new_version


@init_required
def get_namespace_version(namespace):
    """Get version of a namespace.

    Args:
        namespace (str): Namespace itself.

    Returns:
        Namespace version as an integer if it exists, otherwise None.
    """
    validate_namespace(namespace)
    path = _get_ns_version_file_path(namespace)
    if not os.path.isfile(path):
        return None
    with locks.locked_open(path) as f:
        try:
            cont = f.read()
            return int(cont.decode(ENCODING_ASCII))
        except ValueError as e:
            raise RuntimeError("Failed to get version of namespace. Error: %s" % e)


def validate_namespace(namespace):
    """Checks that namespace value is supported."""
    if not NS_REGEX.match(namespace):
        raise ValueError("Invalid namespace. Must match regex /[a-zA-Z0-9_-]+$/.")


def _get_ns_version_file_path(namespace):
    return os.path.join(_ns_versions_loc, namespace)


######################
# CUSTOM SERIALIZATION
######################

TYPE_DATETIME_CODE = 1
DATETIME_FORMAT = "%Y%m%dT%H:%M:%S.%f"


def _msgpack_default(obj):
    if isinstance(obj, datetime.datetime):
        return msgpack.ExtType(TYPE_DATETIME_CODE, obj.strftime(DATETIME_FORMAT).encode(CONTENT_ENCODING))
    raise TypeError("Unknown type: %r" % (obj,))


def _msgpack_ext_hook(code, data):
    if code == TYPE_DATETIME_CODE:
        return datetime.datetime.strptime(data.decode(CONTENT_ENCODING), DATETIME_FORMAT)
    return msgpack.ExtType(code, data)
