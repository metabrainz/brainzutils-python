"""
This module serves as an interface for memcached.

Module needs to be initialized before use! See init() function.

It basically is a wrapper for pymemcache package with additional
functionality and tweaks specific to serve our needs.

There's also support for namespacing, which simplifies management of different
versions of data saved in the cache. You can invalidate whole namespace using
invalidate_namespace() function. See its description for more info.

More information about memcached can be found at https://memcached.org/.
"""
from pymemcache.client.hash import HashClient
from functools import wraps
from pytools import locks
import tempfile
import datetime
import os.path
import hashlib
import msgpack
import shutil

_mc = None  # type: HashClient
_glob_namespace = None  # type: bytes
_ns_versions_loc = None  # type: str

SHA1_LENGTH = 40
MAX_KEY_LENGTH = 250
NS_VERSIONS_LOC_DIR = "namespace_versions"
CONTENT_ENCODING = "utf-8"
ENCODING_ASCII = "ascii"


def init(servers, namespace, ns_versions_loc=None, ignore_exc=False):
    """Initializes memcached client. Needs to be called before use.

    Args:
        servers (list): List of tuples with memcached servers (host (str), port (int)).
        namespace (str): Global namespace that will be prepended to all keys.
        ns_versions_loc (str): Path to directory where namespace versions will
            be stored. If not specified, creates a temporary directory that uses
            global namespace as a reference to make sure availability to multiple
            processes. See NS_VERSIONS_LOC_DIR value in this module and implementation.
        ignore_exc (bool): Treat exceptions that occur in the underlying
            library as cache misses.
    """
    global _mc, _glob_namespace, _ns_versions_loc
    _mc = HashClient(
        servers=servers,
        serializer=_serializer,
        deserializer=_deserializer,
        ignore_exc=ignore_exc
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
        if not _mc:
            raise RuntimeError("Cache module needs to be initialized before "
                               "use! See documentation for more info.")
        return f(*args, **kwargs)
    return decorated


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
    result = get_many([key], namespace)
    return result.get(key)


@init_required
def delete(key, namespace=None):
    """Delete an item.

    Args:
        key: Key of the item that needs to be deleted.
        namespace: Optional namespace in which key was defined.

    Returns:
          True if deleted successfully.
    """
    return delete_many([key], namespace)


@init_required
def set_many(mapping, time=0, namespace=None):
    """Set multiple keys doing just one query.

    Args:
        mapping: A dict of key/value pairs to set.
        time: Time to store the keys (in milliseconds).
        namespace: Namespace for the keys.

    Returns:
        True on success.
    """
    return _mc.set_many(_prep_dict(mapping, namespace), time)


@init_required
def get_many(keys, namespace=None):
    """Retrieve multiple keys doing just one query.

    Args:
        keys: Array of keys that need to be retrieved.
        namespace: Namespace for the keys.

    Returns:
        A dictionary of key/value pairs that were available.
    """
    keys_prepd = _prep_list(keys, namespace)
    result = _mc.get_many(keys_prepd)
    for key_orig, key_mod in zip(keys, keys_prepd):
        if key_mod in result:
            result[key_orig] = _decode_value(result.pop(key_mod))
    return result


@init_required
def delete_many(keys, namespace=None):
    return _mc.delete_many(_prep_list(keys, namespace))


@init_required
def flush_all():
    _mc.flush_all()


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


def _prep_key(key, namespace_and_version=None):
    """Prepares a key for use with memcached."""
    if namespace_and_version:
        key = "%s:%s" % (namespace_and_version, key)
    if not isinstance(key, bytes):
        key = key.encode(ENCODING_ASCII, errors='xmlcharrefreplace')
    key = hashlib.sha1(key).hexdigest().encode(ENCODING_ASCII)
    return _glob_namespace + key


def _prep_list(l, namespace=None):
    """Wrapper for _prep_key function that works with lists."""
    if namespace:
        namespace_and_version = _append_namespace_version(namespace)
    else:
        namespace_and_version = None
    return [_prep_key(k, namespace_and_version) for k in l]


def _prep_dict(dictionary, namespace=None):
    """Wrapper for _prep_key function that works with dictionaries."""
    if namespace:
        namespace_and_version = _append_namespace_version(namespace)
    else:
        namespace_and_version = None
    return {_prep_key(key, namespace_and_version): value
            for key, value in dictionary.items()}


@init_required
def _append_namespace_version(namespace):
    version_key = _glob_namespace + namespace.encode(ENCODING_ASCII)
    version = _mc.get(version_key)
    if version is None:  # namespace isn't initialized
        version = 1
        _mc.set(version_key, version)  # initializing the namespace
    return "%s:%s" % (namespace, version)


def _encode_value(value):
    if isinstance(value, str):
        value = value.encode(CONTENT_ENCODING)
    return value


def _decode_value(value):
    if isinstance(value, bytes):
        value = value.decode(CONTENT_ENCODING)
    return value


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
    path = _get_ns_version_file_path(namespace)
    if not os.path.isfile(path):
        return None
    with locks.locked_open(path) as f:
        try:
            cont = f.read()
            return int(cont.decode(ENCODING_ASCII))
        except ValueError as e:
            raise RuntimeError("Failed to get version of namespace. Error: %s" % e)


def _get_ns_version_file_path(namespace):
    return os.path.join(_ns_versions_loc, namespace)


######################
# CUSTOM SERIALIZATION
######################

TYPE_DATETIME_CODE = 1
DATETIME_FORMAT = "%Y%m%dT%H:%M:%S.%f"


def _serializer(key, value):
    if type(value) == str:
        return _encode_value(value), 1
    return msgpack.packb(value, use_bin_type=True, default=_msgpack_default), 2


def _deserializer(key, value, flags):
    if flags == 1:
        return _decode_value(value)
    if flags == 2:
        return msgpack.unpackb(value, encoding=CONTENT_ENCODING, ext_hook=_msgpack_ext_hook)
    raise ValueError("Unknown serialization format.")


def _msgpack_default(obj):
    if isinstance(obj, datetime.datetime):
        return msgpack.ExtType(TYPE_DATETIME_CODE, obj.strftime(DATETIME_FORMAT).encode(CONTENT_ENCODING))
    raise TypeError("Unknown type: %r" % (obj,))


def _msgpack_ext_hook(code, data):
    if code == TYPE_DATETIME_CODE:
        return datetime.datetime.strptime(_decode_value(data), DATETIME_FORMAT)
    return msgpack.ExtType(code, data)
