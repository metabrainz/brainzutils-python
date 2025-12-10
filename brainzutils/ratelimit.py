# The original version of this code was written by Armin Ronacher:
#
# This snippet by Armin Ronacher can be used freely for anything you like. Consider it public domain.
#
# http://flask.pocoo.org/snippets/70/
#
import time
from functools import update_wrapper
from typing import Literal

from flask import request, g
from werkzeug.exceptions import TooManyRequests

from brainzutils import cache

# g key for the timeout when limits must be refreshed from cache
ratelimit_refresh = 60 # in seconds
ratelimit_timeout = "rate_limits_timeout"

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

       You can also pass custom rate limit parameters directly to the decorator to override
       the global/cached values::

         @app.route('/expensive')
         @ratelimit(per_token_limit=10, per_ip_limit=5, window=60)
         def expensive_endpoint():
             return 'This endpoint has stricter rate limits'

       Use the scope parameter to isolate rate limits for different endpoints::

         @app.route('/api/v1/search')
         @ratelimit(scope='search')
         def search():
             return 'Search results'

         @app.route('/api/v1/upload')
         @ratelimit(scope='upload', per_ip_limit=5, window=60)
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
           1. Decorator parameters (per_token_limit, per_ip_limit, window)
           2. Scope-specific limits from cache (if scope is provided)
           3. Global limits from cache

    4. To enable token based rate limiting, callers need to pass the Authorization header (see above)
       and the application needs to provide a user validation function::

          from brainzutils.ratelimit import set_user_validation_function

          def validate_user(user):
              if user == valid_user:
                  return True
              return False

         set_user_validation_function(validate_user)

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
        self.current = cache.increment(self.key, namespace=ratelimit_cache_namespace)
        cache.expireat(self.key, self.reset + self.expiration_window, namespace=ratelimit_cache_namespace)

    remaining = property(lambda x: max(x.limit - x.current, 0))
    over_limit = property(lambda x: x.current > x.limit)


def set_user_validation_function(func):
    """
        The function passed to this method should accept on argument, the Authorization header contents
        and return a True/False value if this user is a valid user.
    """
    global ratelimit_user_validation
    ratelimit_user_validation = func


def set_rate_limits(per_token, per_ip, window, scope=None):
    """
        Update the current global rate limits. This will affect all new rate limiting windows
        and existing windows will not be changed. If a scope is provided, the limits will be
        changed only for that scope.
    """
    prefix = f"{scope}:" if scope else ""
    cache.set_many({
        f"{prefix}{ratelimit_per_token_key}": per_token,
        f"{prefix}{ratelimit_per_ip_key}": per_ip,
        f"{prefix}{ratelimit_window_key}": window,
    }, expirein=0, namespace=ratelimit_cache_namespace)


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
    _global: dict, _scope: dict = None, _local: dict = None
) -> dict:
    values = {}
    if _local is not None and (local_limit := _local.get(limit_type)) is not None:
        values["limit"] = local_limit
    elif _scope is not None and (scope_limit := _scope.get(limit_type)) is not None:
        values["limit"] = scope_limit
    else:
        values["limit"] = _global[limit_type]

    if _local is not None and (local_window := _local.get("window")) is not None:
        values["window"] = local_window
    elif _scope is not None and (scope_window := _scope.get("window")) is not None:
        values["window"] = scope_window
    else:
        values["window"] = _global["window"]

    return values


def get_rate_limit_data(request, per_token_limit=None, per_ip_limit=None, window=None, scope=None):
    """Fetch key for the given request. If an Authorization header is provided,
       the caller will get a better and personalized rate limit. If no header is provided,
       the caller will be rate limited by IP, which gets an overall lower rate limit.
       This should encourage callers to always provide the Authorization token

       Args:
           request: The Flask request object
           per_token_limit: Optional override for per-token limit (uses cache value if None)
           per_ip_limit: Optional override for per-IP limit (uses cache value if None)
           window: Optional override for rate limit window in seconds (uses cache value if None)
           scope: Optional scope name to check for scope-specific limits in cache

       Limit resolution order (first non-None value wins):
           1. Decorator parameters (per_token_limit, per_ip_limit, window)
           2. Scope-specific limits from cache (if scope is provided)
           3. Global limits from cache
    """
    _global = get_rate_limits()
    _scope = get_rate_limits(scope) if scope else None
    _local = {
        "per_token": per_token_limit,
        "per_ip": per_ip_limit,
        "window": window
    }

    # If a user verification function is provided, parse the Authorization header and try to look up that user
    if ratelimit_user_validation:
        auth_header = request.headers.get("Authorization")
        if auth_header:
            auth_token = auth_header[6:]
            is_valid = ratelimit_user_validation(auth_token)
            if is_valid:
                values = _get_rate_limit_helper(
                    "per_token", _global=_global, _scope=_scope, _local=_local
                )
                values["key"] = auth_token
                return values

    # no valid auth token provided. Look for a remote addr header provided a the proxy
    # or if that isn't available use the IP address from the header
    ip = request.environ.get("REMOTE_ADDR", None)
    if not ip:
        ip = request.remote_addr

    values = _get_rate_limit_helper(
        "per_ip", _global=_global, _scope=_scope, _local=_local
    )
    values["key"] = ip
    return values


def ratelimit(per_token_limit=None, per_ip_limit=None, window=None, scope=None):
    """
        This is the decorator that should be applied to all view functions that should be
        rate limited.

        Args:
            per_token_limit: Optional override for per-token limit (uses cache value if None)
            per_ip_limit: Optional override for per-IP limit (uses cache value if None)
            window: Optional override for rate limit window in seconds (uses cache value if None)
            scope: Optional scope to isolate rate limits for different endpoints.
                   If provided, the rate limit key will be scoped with this value,
                   allowing different endpoints to have separate rate limit buckets..
    """
    def decorator(f):
        def rate_limited(*args, **kwargs):
            data = get_rate_limit_data(
                request,
                per_token_limit=per_token_limit,
                per_ip_limit=per_ip_limit,
                window=window,
                scope=scope
            )
            key = f"{scope}:{data['key']}" if scope else data["key"]
            rlimit = RateLimit(key, data["limit"], data["window"])
            g._view_rate_limit = rlimit
            if rlimit.over_limit:
                return on_over_limit(rlimit)
            return f(*args, **kwargs)
        return update_wrapper(rate_limited, f)
    return decorator
