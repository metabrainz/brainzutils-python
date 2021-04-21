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

    def test_create_app(self):
        app = flask.CustomFlask(__name__)
        self.assertIsNotNone(app)

    def test_ratelimit(self):
        """ Tests that the ratelimit decorator works
        """

        # Set the limits as per defines in this class
        set_rate_limits(self.max_token_requests, self.max_ip_requests, self.ratelimit_window)

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


        def make_requests(client, nominal_num_requests, token = None):

            print("===== make %d requests" % nominal_num_requests)
            # make one more than the allowed number of requests to catch the 429
            num_requests = nominal_num_requests + 1

            # make a specified number of requests
            while True:
                reset_time = 0
                restart = False
                for i in range(num_requests):
                    if token:
                        response = client.get('/', headers={'Authorization': token})
                    else:
                        response = client.get('/')
                    if reset_time == 0:
                        reset_time = response.headers['X-RateLimit-Reset']

                    if reset_time != response.headers['X-RateLimit-Reset']:
                        # Whoops, we didn't get our tests done before the window expired. start over.
                        restart = True

                        # when restarting we need to do one request less, since the current requests counts to the new window
                        num_requests = nominal_num_requests
                        break

                    if i == num_requests - 1:
                        self.assertEqual(response.status_code, 429)
                    else:
                        self.assertEqual(response.status_code, 200)
                        self.assertEqual(int(response.headers['X-RateLimit-Remaining']), num_requests - i - 2)
                    print_headers(response)

                    sleep(1.1)

                if not restart:
                    break

        client = app.test_client()

        # Make a pile of requests based on IP address
        make_requests(client, self.max_ip_requests)

        # Set a user token and make requests based on the token
        cache.flush_all()
        set_user_validation_function(validate_user)
        set_rate_limits(self.max_token_requests, self.max_ip_requests, self.ratelimit_window)
        make_requests(client, self.max_token_requests, token="Token %s" % valid_user)
