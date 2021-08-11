# The original version of this code was written by Armin Ronacher:
#
# This snippet by Armin Ronacher can be used freely for anything you like. Consider it public domain.
#
# http://flask.pocoo.org/snippets/70/
#
import time
from functools import update_wrapper

from flask import request, g
from werkzeug.exceptions import TooManyRequests

from brainzutils import cache

# g key for the timeout when limits must be refreshed from cache
ratelimit_refresh = 60 # in seconds
ratelimit_timeout = "rate_limits_timeout"

# Defaults
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

    3. The default rate limits are defined above (see comment Defaults). If you want to set different
       rate limits, which can be also done dynamically without restarting the application, call
       the set_rate_limits function::

          from brainzutils.ratelimit import set_rate_limits

          set_rate_limits(per_token_limit, per_ip_limit, rate_limit_window)

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
    '''
        The function passed to this method should accept on argument, the Authorization header contents
        and return a True/False value if this user is a valid user.
    '''

    global ratelimit_user_validation
    ratelimit_user_validation = func


def set_rate_limits(per_token, per_ip, window):
    '''
        Update the current rate limits. This will affect all new rate limiting windows and existing windows will not be changed.
    '''
    cache.set(ratelimit_per_token_key, per_token, expirein=0, namespace=ratelimit_cache_namespace)
    cache.set(ratelimit_per_ip_key, per_ip, expirein=0, namespace=ratelimit_cache_namespace)
    cache.set(ratelimit_window_key, window, expirein=0, namespace=ratelimit_cache_namespace)


def inject_x_rate_headers(response):
    '''
        Add rate limit headers to responses
    '''
    limit = get_view_rate_limit()
    if limit:
        h = response.headers
        h.add('Access-Control-Expose-Headers', 'X-RateLimit-Remaining,X-RateLimit-Limit,X-RateLimit-Reset,X-RateLimit-Reset-In')
        h.add('X-RateLimit-Remaining', str(limit.remaining))
        h.add('X-RateLimit-Limit', str(limit.limit))
        h.add('X-RateLimit-Reset', str(limit.reset))
        h.add('X-RateLimit-Reset-In', str(limit.seconds_before_reset))
    return response


def get_view_rate_limit():
    '''
        Helper function to fetch the ratelimit limits from the flask context
    '''
    return getattr(g, '_view_rate_limit', None)


def on_over_limit(limit):
    ''' 
        Set a nice and readable error message for over the limit requests.
    '''
    raise TooManyRequests(
        'You have exceeded your rate limit. See the X-RateLimit-* response headers for more ' \
        'information on your current rate limit.')


def check_limit_freshness():
    '''
        This function checks to see if the values we have cached in the current request context
        are still fresh enough. If they've existed longer than the timeout value, refresh from
        the cache. This allows us to not check the limits for each request, saving cache traffic.
    '''

    limits_timeout = getattr(g, '_' + ratelimit_timeout, 0)
    if time.time() <= limits_timeout:
        return

    value = int(cache.get(ratelimit_per_token_key, namespace=ratelimit_cache_namespace) or '0')
    if not value:
        cache.set(ratelimit_per_token_key, ratelimit_per_token_default, expirein=0, namespace=ratelimit_cache_namespace)
        value = ratelimit_per_token_default
    setattr(g, '_' + ratelimit_per_token_key, value)

    value = int(cache.get(ratelimit_per_ip_key, namespace=ratelimit_cache_namespace) or '0')
    if not value:
        cache.set(ratelimit_per_ip_key, ratelimit_per_ip_default, expirein=0, namespace=ratelimit_cache_namespace)
        value = ratelimit_per_ip_default
    setattr(g, '_' + ratelimit_per_ip_key, value)

    value = int(cache.get(ratelimit_window_key, namespace=ratelimit_cache_namespace) or '0')
    if not value:
        cache.set(ratelimit_window_key, ratelimit_window_default, expirein=0, namespace=ratelimit_cache_namespace)
        value = ratelimit_window_default
    setattr(g, '_' + ratelimit_window_key, value)

    setattr(g, '_' + ratelimit_timeout, int(time.time()) + ratelimit_refresh)


def get_per_ip_limits():
    '''
        Fetch the per IP limits from context/cache
    '''
    check_limit_freshness()
    return {
            'limit':   getattr(g, '_' + ratelimit_per_ip_key),
            'window' : getattr(g, '_' + ratelimit_window_key),
           }


def get_per_token_limits():
    '''
        Fetch the per token limits from context/cache
    '''
    check_limit_freshness()
    return {
            'limit':   getattr(g, '_' + ratelimit_per_token_key),
            'window' : getattr(g, '_' + ratelimit_window_key),
           }


def get_rate_limit_data(request):
    '''Fetch key for the given request. If an Authorization header is provided,
       the caller will get a better and personalized rate limit. If no header is provided,
       the caller will be rate limited by IP, which gets an overall lower rate limit.
       This should encourage callers to always provide the Authorization token
    '''

    # If a user verification function is provided, parse the Authorization header and try to look up that user
    if ratelimit_user_validation:
        auth_header = request.headers.get('Authorization')
        if auth_header:
            auth_token = auth_header[6:]
            is_valid = ratelimit_user_validation(auth_token)
            if is_valid:
                values = get_per_token_limits()
                values['key'] = auth_token
                return values


    # no valid auth token provided. Look for a remote addr header provided a the proxy
    # or if that isn't available use the IP address from the header
    ip = request.environ.get('REMOTE_ADDR', None)
    if not ip:
        ip = request.remote_addr

    values = get_per_ip_limits()
    values['key'] = ip
    return values


def ratelimit():
    '''
        This is the decorator that should be applied to all view functions that should be 
        rate limited.
    '''
    def decorator(f):
        def rate_limited(*args, **kwargs):
            data = get_rate_limit_data(request)
            rlimit = RateLimit(data['key'], data['limit'], data['window'])
            g._view_rate_limit = rlimit
            if rlimit.over_limit:
                return on_over_limit(rlimit)
            return f(*args, **kwargs)
        return update_wrapper(rate_limited, f)
    return decorator
