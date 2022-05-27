# pylint: disable=invalid-name
"""
This module serves as an interface for Redis.

The module needs to be initialized before use! See :meth:`init()`.

It basically is a wrapper for redis package with additional
functionality and tweaks specific to serve our needs.

There's also support for namespacing, which simplifies management of different
versions of data saved in the cache.

More information about Redis can be found at http://redis.io/.
"""
import builtins
import os
import socket
from functools import wraps
import datetime
import re
from typing import Optional

import redis
import msgpack


_r: redis.StrictRedis = None
_glob_namespace: str = None

NS_REGEX = re.compile('[a-zA-Z0-9_-]+$')
CONTENT_ENCODING = "utf-8"
ENCODING_ASCII = "ascii"


def init(host: str = "localhost", port: int = 6379, db_number: int = 0,
         namespace: str = "", client_name: str = None):
    """Initializes Redis client. Needs to be called before use.

    Namespace versions are stored in a local directory.

    Args:
        host: Redis server hostname.
        port: Redis port.
        db_number: Redis database number.
        namespace: Global namespace that will be prepended to all keys.
        client_name: The client name to assign to the redis connection. This value is used to identify which clients
          are connected to a server, and is only used for debugging purposes.
    """

    # The first priority in setting the client name is to set the user specified
    # client_name as this can come in handy during testing and development. Otherwise,
    # we use CONTAINER_NAME environment variable, this is always set in production.
    # Finally, we fall back to the host name, not as informative as the container name
    # but something is better than nothing.
    if client_name is None:
        client_name = os.getenv("CONTAINER_NAME", None)
    if client_name is None:
        client_name = socket.gethostname()

    global _r, _glob_namespace
    _r = redis.StrictRedis(
        host=host,
        port=port,
        db=db_number,
        client_name=client_name
    )

    _glob_namespace = namespace + ":"


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
def set(key, val, expirein, namespace=None, encode=True):
    """Set a key to a given value.

    Args:
        key (str): Key of the item.
        val: Item's value.
        expirein (int): The time after which this value should expire, in seconds.
        namespace (str): Optional namespace in which key needs to be defined.
        encode: True if the value should be encoded with msgpack, False otherwise

    Returns:
        True if stored successfully.
    """
    # Note that both key and value are encoded before insertion.
    return set_many(
        mapping={key: val},
        expirein=expirein,
        namespace=namespace,
        encode=encode
    )


@init_required
def get(key, namespace=None, decode=True):
    """Retrieve an item.

    Args:
        key: Key of the item that needs to be retrieved.
        namespace: Optional namespace in which key was defined.
        decode (bool): True if value should be decoded with msgpack, False otherwise

    Returns:
        Stored value or None if it's not found.
    """
    # Note that key is encoded before retrieval request.
    return get_many([key], namespace, decode).get(key)


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
def expire(key, expirein, namespace=None):
    """Set the expiration time for an item

    Args:
        key: Key of the item that needs to be deleted.
        expirein: the number of seconds after which the item should expire
        namespace: Optional namespace in which key was defined.

    Returns:
          True if the timeout was set, False otherwise
    """
    # Note that key is encoded before deletion request.
    return _r.pexpire(_prep_key(key, namespace), expirein * 1000)


@init_required
def expireat(key, timeat, namespace=None):
    """Set the absolute expiration time for an item

    Args:
        key: Key of the item that needs to be deleted.
        timeat: the number of seconds since the epoch when the item should expire
        namespace: Optional namespace in which key was defined.

    Returns:
          True if the timeout was set, False otherwise
    """
    # Note that key is encoded before deletion request.
    return _r.pexpireat(_prep_key(key, namespace), timeat * 1000)


@init_required
def set_many(mapping, expirein, namespace=None, encode=True):
    """Set multiple keys doing just one query.

    Args:
        mapping (dict): A dict of key/value pairs to set.
        expirein (int): The time after which this value should expire, in seconds.
        namespace (str): Namespace for the keys.
        encode: True if the values should be encoded with msgpack, False otherwise

    Returns:
        True on success.
    """
    # TODO: Fix return value
    result = _r.mset(_prep_dict(mapping, namespace, encode))
    if expirein:
        for key in list(mapping.keys()):
            expire(key, expirein, namespace)

    return result


@init_required
def get_many(keys, namespace=None, decode=True):
    """Retrieve multiple keys doing just one query.

    Args:
        keys (list): List of keys that need to be retrieved.
        namespace (str): Namespace for the keys.
        decode (bool): True if values should be decoded with msgpack, False otherwise

    Returns:
        A dictionary of key/value pairs that were available.
    """
    result = {}
    for i, value in enumerate(_r.mget(_prep_keys_list(keys, namespace))):
        result[keys[i]] = _decode_val(value) if decode else value
    return result


@init_required
def delete_many(keys, namespace=None):
    """Delete multiple keys.

    Returns:
        Number of keys that were deleted.
    """
    return _r.delete(*_prep_keys_list(keys, namespace))


@init_required
def increment(key, amount=1, namespace=None):
    """ Increment the value for given key using the INCR command.

    Args:
        key: Key of the item that needs to be incremented
        amount: the amount to increment the value by
        namespace: Namespace for the key

    Returns:
        An integer equal to the value after increment
    """
    return _r.incr(_prep_keys_list([key], namespace)[0], amount=amount)


@init_required
def hincrby(name, key, amount, namespace=None):
    """Increment a hashes key by a given amount using HINCRBY

    Args:
        name: Name of the hash
        key: Key of the item in the hash to increment
        amount: the number to increment the key by
        namespace: Namespace for the name

    Returns:
        An integer equal to the value after increment
    """
    return _r.hincrby(_prep_keys_list([name], namespace)[0], key, amount)


@init_required
def hgetall(name, namespace=None):
    """Get all keys and values for a hash using HGETALL

    Args:
        name: Name of the hash
        namespace: Namespace for the name

    Returns:
        A dictionary of {key: value} items for all keys in the hash
    """
    return _r.hgetall(_prep_keys_list([name], namespace)[0])


@init_required
def hkeys(name, namespace=None):
    """Get all keys for a hash using HKEYS

    Args:
        name: Name of the hash
        namespace: Namespace for the name

    Returns:
        A list of [key] values for all keys in the hash
    """
    return _r.hkeys(_prep_keys_list([name], namespace)[0])


@init_required
def hset(name, key, value, namespace=None):
    """Delete the specified keys from a hash using HDEL.
    Note that the ``keys`` argument must be a list. This differs from the underlying redis
    library's version of this command, which takes varargs.

    Args:
        name: Name of the hash
        key: Key of the item in the hash to set
        value: value to set the item to
        namespace: Namespace for the name

    Returns:
        the number of keys deleted from the hash
    """
    return _r.hset(_prep_keys_list([name], namespace)[0], key, value)


@init_required
def hdel(name, keys, namespace=None):
    """Delete the specified keys from a hash using HDEL.
    Note that the ``keys`` argument must be a list. This differs from the underlying redis
    library's version of this command, which takes varargs.

    Args:
        name: Name of the hash
        keys: a list of the keys to delete from the has
        namespace: Namespace for the name

    Returns:
        the number of keys deleted from the hash
    """
    if not isinstance(keys, list):
        keys = [keys]
    return _r.hdel(_prep_keys_list([name], namespace)[0], *keys)


@init_required
def sadd(name, keys, expirein, encode=True, namespace=None):
    """Add the specified keys to the set stored at name using SADD
    Note that it is not possible to expire a single value stored in a set.  The ``expirein``
    argument will set the expiration period of the entire set stored at ``name``. Therefore,
    any additions to a set will reset its expiry to the value of ``expirein`` passed in
    last call.
    Args:
        name: Name of the set
        keys: keys to add to the set
        expirein: the number of seconds after which the item should expire
        namespace: namespace for the name
        encode: True if the value should be encoded with msgpack, False otherwise

    Returns:
        the number of elements that were added to the set, not including all the elements already present into the set.
    """
    prepared_name = _prep_key(name, namespace)
    if not isinstance(keys, list) and not isinstance(keys, builtins.set):
        keys = {keys}

    if encode:
        keys = {_encode_val(key) for key in keys}

    result = _r.sadd(prepared_name, *keys)
    expire(name, expirein, namespace)
    return result


@init_required
def smembers(name, decode=True, namespace=None):
    """Returns all the members of the set value stored at name.
    Args:
        name: Name of the set
        decode: True if value should be decoded with msgpack, False otherwise
        namespace: namespace for the name

    Returns:
        all members of the set
    """
    keys = _r.smembers(_prep_key(name, namespace))
    if decode:
        keys = {_decode_val(key) for key in keys}
    return keys


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
    key = key.encode(ENCODING_ASCII, errors='xmlcharrefreplace').decode(ENCODING_ASCII)

    for attr in attributes:
        if not isinstance(attr, str):
            attr = str(attr)
        key += '_' + attr.encode(ENCODING_ASCII, errors='xmlcharrefreplace').decode(ENCODING_ASCII)

    key = key.replace(' ', '_')  # spaces are not allowed

    return key


def _prep_dict(dictionary, namespace=None, encode=True):
    """Wrapper for _prep_key and _encode_val functions that works with dictionaries."""
    return {_prep_key(key, namespace): _encode_val(value) if encode else value
            for key, value in dictionary.items()}


def _prep_key(key, namespace=None):
    """Prepares a key for use with Redis."""
    if namespace:
        key = "%s:%s" % (namespace, key)
    if not isinstance(key, bytes):
        key = key.encode(ENCODING_ASCII, errors='xmlcharrefreplace').decode(ENCODING_ASCII)
    return _glob_namespace + key


def _prep_keys_list(l, namespace=None):
    """Wrapper for _prep_key function that works with lists.

    Returns:
        Prepared keys in the same order.
    """
    return [_prep_key(k, namespace) for k in l]


def _encode_val(value):
    if value is None:
        return value
    return msgpack.packb(value, use_bin_type=True, default=_msgpack_default)


def _decode_val(value):
    if value is None:
        return value
    return msgpack.unpackb(value, raw=False, ext_hook=_msgpack_ext_hook)


############
# NAMESPACES
############

def validate_namespace(namespace):
    """Checks that namespace value is supported."""
    if not NS_REGEX.match(namespace):
        raise ValueError("Invalid namespace. Must match regex /[a-zA-Z0-9_-]+$/.")


######################
# CUSTOM SERIALIZATION
######################

TYPE_DATETIME_CODE = 1


def _msgpack_default(obj):
    if isinstance(obj, datetime.datetime):
        return msgpack.ExtType(TYPE_DATETIME_CODE, obj.isoformat().encode(CONTENT_ENCODING))
    raise TypeError("Unknown type: %r" % (obj,))


def _msgpack_ext_hook(code, data):
    if code == TYPE_DATETIME_CODE:
        return datetime.datetime.fromisoformat(data.decode(CONTENT_ENCODING))
    return msgpack.ExtType(code, data)
