# The original version of this code was written by Armin Ronacher:
#
# This snippet by Armin Ronacher can be used freely for anything you like. Consider it public domain.
#
# http://flask.pocoo.org/snippets/70/
#
import logging
import time
from functools import update_wrapper
from typing import Literal

from flask import request, g
from redis.exceptions import RedisError
from werkzeug.exceptions import TooManyRequests

from brainzutils import cache

logger = logging.getLogger(__name__)

# how long the limits read from cache are kept in process memory before being read again
ratelimit_refresh = 60 # in seconds

# Defaults
ratelimit_defaults = {
    "per_token": 50,
    "per_ip": 30,
    "window": 10
}
ratelimit_per_token_default = 50
ratelimit_per_ip_default = 30
ratelimit_window_default = 10

# keys
ratelimit_per_token_key = "rate_limit_per_token_limit"
ratelimit_per_ip_key = "rate_limit_per_ip_limit"
ratelimit_window_key = "rate_limit_window"
ratelimit_cache_namespace = "rate_limit"

# external functions
ratelimit_user_validation = None

# if True, requests are let through without a rate limit when Redis is unavailable
ratelimit_fail_open = True

# scope -> (time after which to read the limits from cache again, limits); None is the global scope
_limits_in_memory = {}


class RateLimit(object):
    """
        This Ratelimit object is created when a request is started (via the ratelimit decorator)
        and is stored in the flask's request context so that the results can be injected into
        the response headers before the request is over.

    HOW TO USE THIS MODULE:

    This module defines a set of function that allows your to add ratelimiting to your
    flask app. There are three values to know and set:

       per_token_limit - The number of requests that are allowed for a caller who is
            setting an::

               Authorization: Token <auth token>

            header. This limit can be different than the limit for rate limiting on an IP basis.

       per_ip_limit - The number of requests that are allowed for a caller who is not
            providing an Authorization header and is rate limited on their IP address.

       ratelimit_window - The window, in number of seconds, how long long the limits
            above are applied for.

    To add ratelimit capabilities to your flask app, follow these steps:

    1. During app creation add these lines::

          from brainzutils.ratelimit import ratelimit, inject_x_rate_headers

          @app.after_request
          def after_request_callbacks(response):
              return inject_x_rate_headers(response)

    2. Then apply the ratelimit() decorator to any function that should be rate limited::

         @app.route('/')
         @ratelimit()
         def index():
             return '<html><body>test</body></html>'

       Use the scope parameter to isolate and apply custom rate limits for different endpoints::

         @app.route('/api/v1/search')
         @ratelimit(scope='search')
         def search():
             return 'Search results'

         @app.route('/api/v1/upload')
         @ratelimit(scope='upload')
         def upload():
             return 'Upload complete'

    3. The default rate limits are defined above (see comment Defaults). If you want to set different
       rate limits, which can be also done dynamically without restarting the application, call
       the set_rate_limits function::

          from brainzutils.ratelimit import set_rate_limits

          set_rate_limits(per_token_limit, per_ip_limit, rate_limit_window)

       You can also set scope-specific limits in cache::

          from brainzutils.ratelimit import set_rate_limits

          set_rate_limits(per_token=100, per_ip=50, window=60, scope='search')
          set_rate_limits(per_token=10, per_ip=5, window=120, scope='upload')

       Limit resolution order (first non-None value wins):
           1. Scope-specific limits from cache (if scope is provided)
           2. Global limits from cache

       Each process keeps the limits in memory and reads them from cache again after ratelimit_refresh
       seconds, so other processes pick up new limits within that time.

    4. To enable token based rate limiting, callers need to pass the Authorization header (see above)
       and the application needs to provide a user validation function::

          from brainzutils.ratelimit import set_user_validation_function

          def validate_user(user):
              if user == valid_user:
                  return True
              return False

         set_user_validation_function(validate_user)

    5. If Redis is unavailable, requests are let through without a rate limit, so that an outage of Redis does
       not take the application down with it. To make such requests fail instead, call::

          from brainzutils.ratelimit import set_fail_open

          set_fail_open(False)

    """

    # From the docs:
    # We also give the key extra expiration_window seconds time to expire in cache so that badly
    # synchronized clocks between the workers and the cache server do not cause problems.
    expiration_window = 10

    def __init__(self, key_prefix, limit, per):
        current_time = int(time.time())
        self.reset = (current_time // per) * per + per
        self.seconds_before_reset = self.reset - current_time
        self.key = key_prefix + str(self.reset)
        self.limit = limit
        self.per = per
        self.current = cache.increment(self.key, namespace=ratelimit_cache_namespace,
                                       expireat=self.reset + self.expiration_window)

    remaining = property(lambda x: max(x.limit - x.current, 0))
    over_limit = property(lambda x: x.current > x.limit)


def set_user_validation_function(func):
    """
        The function passed to this method should accept on argument, the Authorization header contents
        and return a True/False value if this user is a valid user.
    """
    global ratelimit_user_validation
    ratelimit_user_validation = func


def set_fail_open(fail_open):
    """
        Set whether requests are let through without a rate limit when Redis is unavailable (the default),
        or fail with the Redis error.
    """
    global ratelimit_fail_open
    ratelimit_fail_open = fail_open


def clear_rate_limits_cache():
    """
        Forget the limits kept in memory, so the next request reads them from cache.
    """
    _limits_in_memory.clear()


def set_rate_limits(per_token, per_ip, window, scope=None):
    """
        Update the current global rate limits. This will affect all new rate limiting windows
        and existing windows will not be changed. If a scope is provided, the limits will be
        changed only for that scope. The new limits apply at once in this process, and in
        other processes within ratelimit_refresh seconds.
    """
    prefix = f"{scope}:" if scope else ""
    cache.set_many({
        f"{prefix}{ratelimit_per_token_key}": per_token,
        f"{prefix}{ratelimit_per_ip_key}": per_ip,
        f"{prefix}{ratelimit_window_key}": window,
    }, expirein=0, namespace=ratelimit_cache_namespace)
    _limits_in_memory[scope] = (time.time() + ratelimit_refresh,
                                {"per_token": per_token, "per_ip": per_ip, "window": window})


def _get_rate_limits_in_memory(scope=None):
    """
        The limits for the global or a specific scope, read from cache at most once every ratelimit_refresh
        seconds.
    """
    refresh_at, limits = _limits_in_memory.get(scope, (0, None))
    if time.time() >= refresh_at:
        limits = get_rate_limits(scope)
        _limits_in_memory[scope] = (time.time() + ratelimit_refresh, limits)
    return limits


def get_rate_limits(scope=None):
    """
        Get rate limits for global or specific scope from cache.

        Args:
            scope: The scope name to get limits for

        Returns:
            A dict with 'per_token', 'per_ip', 'window' keys if scope limits exist,
            or None if no scope-specific limits are set.
    """
    prefix = f"{scope}:" if scope else ""
    keys = {
        "per_token": f"{prefix}{ratelimit_per_token_key}",
        "per_ip": f"{prefix}{ratelimit_per_ip_key}",
        "window": f"{prefix}{ratelimit_window_key}"
    }
    cache_values = cache.get_many(list(keys.values()), namespace=ratelimit_cache_namespace)

    result = {}
    for key in keys:
        if (value := cache_values.get(keys[key])) is not None:
            result[key] = value
        # if returning global rate limits and value is not in cache,
        # return global defaults
        elif scope is None:
            result[key] = ratelimit_defaults[key]
        else:
            result[key] = None

    return result


def inject_x_rate_headers(response):
    """
        Add rate limit headers to responses
    """
    limit = get_view_rate_limit()
    if limit:
        h = response.headers
        h.add("Access-Control-Expose-Headers", "X-RateLimit-Remaining,X-RateLimit-Limit,X-RateLimit-Reset,X-RateLimit-Reset-In")
        h.add("X-RateLimit-Remaining", str(limit.remaining))
        h.add("X-RateLimit-Limit", str(limit.limit))
        h.add("X-RateLimit-Reset", str(limit.reset))
        h.add("X-RateLimit-Reset-In", str(limit.seconds_before_reset))
    return response


def get_view_rate_limit():
    """
        Helper function to fetch the ratelimit limits from the flask context
    """
    return getattr(g, "_view_rate_limit", None)


def on_over_limit(limit):
    """
        Set a nice and readable error message for over the limit requests.
    """
    raise TooManyRequests(
        "You have exceeded your rate limit. See the X-RateLimit-* response headers for more "
        "information on your current rate limit."
    )

def _get_rate_limit_helper(
    limit_type: Literal["per_ip", "per_token"],
    _global: dict,
    _scope: dict = None
) -> dict:
    values = {}
    if _scope is not None and (scope_limit := _scope.get(limit_type)) is not None:
        values["limit"] = scope_limit
    else:
        values["limit"] = _global[limit_type]

    if _scope is not None and (scope_window := _scope.get("window")) is not None:
        values["window"] = scope_window
    else:
        values["window"] = _global["window"]

    return values


def get_rate_limit_data(request, scope=None):
    """Fetch key for the given request. If an Authorization header is provided,
       the caller will get a better and personalized rate limit. If no header is provided,
       the caller will be rate limited by IP, which gets an overall lower rate limit.
       This should encourage callers to always provide the Authorization token

       Args:
           request: The Flask request object
           scope: Optional scope name to check for scope-specific limits in cache

       Limit resolution order (first non-None value wins):
           1. Scope-specific limits from cache (if scope is provided)
           3. Global limits from cache
    """
    _global = _get_rate_limits_in_memory()
    _scope = _get_rate_limits_in_memory(scope) if scope else None

    # If a user verification function is provided, parse the Authorization header and try to look up that user
    if ratelimit_user_validation:
        auth_header = request.headers.get("Authorization")
        if auth_header:
            auth_token = auth_header[6:]
            is_valid = ratelimit_user_validation(auth_token)
            if is_valid:
                values = _get_rate_limit_helper(
                    "per_token", _global=_global, _scope=_scope
                )
                values["key"] = auth_token
                return values

    # no valid auth token provided. Look for a remote addr header provided a the proxy
    # or if that isn't available use the IP address from the header
    ip = request.environ.get("REMOTE_ADDR", None)
    if not ip:
        ip = request.remote_addr

    values = _get_rate_limit_helper(
        "per_ip", _global=_global, _scope=_scope
    )
    values["key"] = ip
    return values


def ratelimit(scope=None):
    """
        This is the decorator that should be applied to all view functions that should be
        rate limited.

        Args:
            scope: Optional scope to isolate rate limits for different endpoints.
                   If provided, the rate limit key will be scoped with this value,
                   allowing different endpoints to have separate rate limit buckets..
    """
    def decorator(f):
        def rate_limited(*args, **kwargs):
            try:
                data = get_rate_limit_data(
                    request,
                    scope=scope
                )
                key = f"{scope}:{data['key']}" if scope else data["key"]
                rlimit = RateLimit(key, data["limit"], data["window"])
            except RedisError:
                if not ratelimit_fail_open:
                    raise
                logger.warning("Rate limiting skipped, Redis is unavailable", exc_info=True)
                return f(*args, **kwargs)
            g._view_rate_limit = rlimit
            if rlimit.over_limit:
                return on_over_limit(rlimit)
            return f(*args, **kwargs)
        return update_wrapper(rate_limited, f)
    return decorator
