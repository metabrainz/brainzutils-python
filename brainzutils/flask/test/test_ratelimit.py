import unittest
import os
from time import sleep

from brainzutils import flask, cache
from brainzutils.ratelimit import ratelimit, set_rate_limits, inject_x_rate_headers, set_user_validation_function

valid_user = "41FB6EEB-636B-4F7C-B376-3A8613F1E69A"
def validate_user(user):
    if user == valid_user:
        return True
    return False

class RatelimitTestCase(unittest.TestCase):

    host = os.environ.get("REDIS_HOST", "localhost")
    port = 6379
    namespace = "NS_TEST"
    max_ip_requests = 3
    max_token_requests = 5
    ratelimit_window = 10

    def setUp(self):
        cache.init(
            host=self.host,
            port=self.port,
            namespace=self.namespace,
        )
        # Making sure there are no items in cache before we run each test
        cache.flush_all()

    def tearDown(self):
        cache.delete_ns_versions_dir()

    def test_create_app(self):
        app = flask.CustomFlask(__name__)
        self.assertIsNotNone(app)

    def test_ratelimit(self):
        """ Tests that the ratelimit decorator works
        """

        # Three per token requests, three per IP requests in max 10 seconds
        set_rate_limits(self.max_ip_requests, self.max_token_requests, self.ratelimit_window)

        # create an app
        app = flask.CustomFlask(__name__)
        self.assertIsNotNone(app)
        app.debug = True
        app.config['SECRET_KEY'] = 'this is a totally secret key btw'
        app.init_debug_toolbar()

        @app.after_request
        def after_request_callbacks(response):
            return inject_x_rate_headers(response)

        # add a dummy route
        @app.route('/')
        @ratelimit()
        def index():
            return '<html><body>test</body></html>'

        def print_headers(response):
            print("X-RateLimit-Remaining", response.headers['X-RateLimit-Remaining'])
            print("X-RateLimit-Limit", response.headers['X-RateLimit-Limit'])
            print("X-RateLimit-Reset", response.headers['X-RateLimit-Reset'])
            print("X-RateLimit-Reset-In", response.headers['X-RateLimit-Reset-In'])
            print()

        client = app.test_client()

        response = client.get('/')
        print_headers(response)
        self.assertEqual(int(response.headers['X-RateLimit-Remaining']), self.max_ip_requests - 1)
        self.assertEqual(int(response.headers['X-RateLimit-Reset-In']), self.ratelimit_window)
        self.assertEqual(response.status_code, 200)
        sleep(.1)

        for i in range(self.max_ip_requests - 1):
            response = client.get('/')
            print_headers(response)
            self.assertEqual(int(response.headers['X-RateLimit-Remaining']), self.max_ip_requests - 1 - i)
            self.assertEqual(response.status_code, 200)
            sleep(.1)

        response = client.get('/')
        print_headers(response)
        self.assertEqual(response.status_code, 429)

        cache.flush_all()
        set_user_validation_function(validate_user)
        set_rate_limits(self.max_ip_requests, self.max_token_requests, self.ratelimit_window)

        for i in range(self.max_token_requests):
            response = client.get('/', headers={'Authorization': valid_user})
            print_headers(response)
            self.assertEqual(int(response.headers['X-RateLimit-Remaining']), self.max_token_requests - 1 - i)
            self.assertEqual(response.status_code, 200)
            sleep(.1)

        response = client.get('/')
        print_headers(response)
        self.assertEqual(response.status_code, 429)
