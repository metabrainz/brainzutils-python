import unittest
import os
from time import sleep

from brainzutils import flask, cache
from brainzutils.ratelimit import (
    ratelimit,
    set_rate_limits,
    get_rate_limits,
    inject_x_rate_headers,
    set_user_validation_function,
    ratelimit_cache_namespace,
)


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

        set_rate_limits(self.max_token_requests, self.max_ip_requests, self.ratelimit_window)
        self.app = flask.CustomFlask(__name__)
        self.app.debug = True
        self.app.config["SECRET_KEY"] = "this is a totally secret key btw"

        @self.app.after_request
        def after_request_callbacks(response):
            return inject_x_rate_headers(response)

    def tearDown(self):
        self.app = None

    def print_headers(self, response):
        print("X-RateLimit-Remaining", response.headers["X-RateLimit-Remaining"])
        print("X-RateLimit-Limit", response.headers["X-RateLimit-Limit"])
        print("X-RateLimit-Reset", response.headers["X-RateLimit-Reset"])
        print("X-RateLimit-Reset-In", response.headers["X-RateLimit-Reset-In"])
        print()

    def make_requests(self, client, nominal_num_requests, token = None):
        print("===== make %d requests" % nominal_num_requests)
        # make one more than the allowed number of requests to catch the 429
        num_requests = nominal_num_requests + 1

        # make a specified number of requests
        while True:
            reset_time = 0
            restart = False
            for i in range(num_requests):
                if token:
                    response = client.get("/", headers={"Authorization": token})
                else:
                    response = client.get("/")
                if reset_time == 0:
                    reset_time = response.headers["X-RateLimit-Reset"]

                if reset_time != response.headers["X-RateLimit-Reset"]:
                    # Whoops, we didn"t get our tests done before the window expired. start over.
                    restart = True

                    # when restarting we need to do one request less, since the current requests counts to the new window
                    num_requests = nominal_num_requests
                    break

                if i == num_requests - 1:
                    self.assertEqual(response.status_code, 429)
                else:
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(int(response.headers["X-RateLimit-Remaining"]), num_requests - i - 2)
                self.print_headers(response)

                sleep(1.1)

            if not restart:
                break

    def test_ratelimit(self):
        """ Tests that the ratelimit decorator works """
        @self.app.route("/")
        @ratelimit()
        def index():
            return "<html><body>test</body></html>"

        client = self.app.test_client()

        # Make a pile of requests based on IP address
        self.make_requests(client, self.max_ip_requests)

        # Set a user token and make requests based on the token
        cache.flush_all()
        set_user_validation_function(validate_user)
        set_rate_limits(self.max_token_requests, self.max_ip_requests, self.ratelimit_window)
        self.make_requests(client, self.max_token_requests, token="Token %s" % valid_user)

    def test_custom_ip_limit(self):
        """Test that per_ip_limit parameter overrides global limit."""
        custom_limit = 2

        @self.app.route("/custom")
        @ratelimit(per_ip_limit=custom_limit, window=60)
        def custom_endpoint():
            return "OK"

        client = self.app.test_client()

        # First request should succeed
        response = client.get("/custom")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-RateLimit-Limit"], str(custom_limit))
        self.assertEqual(response.headers["X-RateLimit-Remaining"], "1")

        response = client.get("/custom")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-RateLimit-Remaining"], "0")

        response = client.get("/custom")
        self.assertEqual(response.status_code, 429)

    def test_custom_window(self):
        """Test that window parameter works correctly."""
        @self.app.route("/short-window")
        @ratelimit(per_ip_limit=1, window=2)
        def short_window_endpoint():
            return "OK"

        client = self.app.test_client()

        response = client.get("/short-window")
        self.assertEqual(response.status_code, 200)
        response = client.get("/short-window")
        self.assertEqual(response.status_code, 429)

        sleep(2.5)
        response = client.get("/short-window")
        self.assertEqual(response.status_code, 200)

    def test_headers_contain_correct_values(self):
        """Test that rate limit headers contain expected values."""
        limit = 5
        window = 30

        @self.app.route("/headers")
        @ratelimit(per_ip_limit=limit, window=window)
        def headers_endpoint():
            return "OK"

        client = self.app.test_client()
        response = client.get("/headers")

        self.assertEqual(response.status_code, 200)
        self.assertIn("X-RateLimit-Limit", response.headers)
        self.assertIn("X-RateLimit-Remaining", response.headers)
        self.assertIn("X-RateLimit-Reset-In", response.headers)

        self.assertEqual(response.headers["X-RateLimit-Limit"], str(limit))
        self.assertEqual(response.headers["X-RateLimit-Remaining"], str(limit - 1))
        self.assertLessEqual(int(response.headers["X-RateLimit-Reset-In"]), window)
        self.assertIn("X-RateLimit-Reset", response.headers)

    def test_scope_isolation(self):
        """Test that different scopes have independent rate limit buckets."""
        @self.app.route("/scope-a")
        @ratelimit(scope="scope_a", per_ip_limit=2, window=60)
        def scope_a_endpoint():
            return "A"

        @self.app.route("/scope-b")
        @ratelimit(scope="scope_b", per_ip_limit=2, window=60)
        def scope_b_endpoint():
            return "B"

        client = self.app.test_client()

        # Exhaust scope_a limit
        response = client.get("/scope-a")
        self.assertEqual(response.status_code, 200)
        response = client.get("/scope-a")
        self.assertEqual(response.status_code, 200)
        response = client.get("/scope-a")
        self.assertEqual(response.status_code, 429)

        # scope_b should still work independently
        response = client.get("/scope-b")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-RateLimit-Remaining"], "1")

        response = client.get("/scope-b")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-RateLimit-Remaining"], "0")
        response = client.get("/scope-b")
        self.assertEqual(response.status_code, 429)

    def test_same_scope_shared_limit(self):
        """Test that endpoints with the same scope share rate limit bucket."""
        scope = "shared"
        set_rate_limits(per_token=100, per_ip=2, window=60, scope=scope)

        @self.app.route("/shared-1")
        @ratelimit(scope=scope)
        def shared_1_endpoint():
            return "Shared 1"

        @self.app.route("/shared-2")
        @ratelimit(scope=scope)
        def shared_2_endpoint():
            return "Shared 2"

        client = self.app.test_client()

        # Make request to shared-1
        response = client.get("/shared-1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-RateLimit-Remaining"], "1")

        # Make request to shared-2 (should share the count)
        response = client.get("/shared-2")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-RateLimit-Remaining"], "0")

        # Both should now be rate limited
        response = client.get("/shared-1")
        self.assertEqual(response.status_code, 429)
        response = client.get("/shared-2")
        self.assertEqual(response.status_code, 429)

    def test_no_scope_vs_scoped(self):
        """Test that unscoped and scoped endpoints have separate buckets."""
        @self.app.route("/unscoped")
        @ratelimit(per_ip_limit=1, window=60)
        def unscoped_endpoint():
            return "Unscoped"

        @self.app.route("/scoped")
        @ratelimit(scope="my_scope", per_ip_limit=1, window=60)
        def scoped_endpoint():
            return "Scoped"

        client = self.app.test_client()

        # Exhaust unscoped limit
        response = client.get("/unscoped")
        self.assertEqual(response.status_code, 200)
        response = client.get("/unscoped")
        self.assertEqual(response.status_code, 429)

        # Scoped endpoint should still work
        response = client.get("/scoped")
        self.assertEqual(response.status_code, 200)

        # Now exhaust scoped
        response = client.get("/scoped")
        self.assertEqual(response.status_code, 429)

    def test_set_and_get_scope_limits(self):
        """Test that set_rate_limits_for_scope and get_rate_limits work."""
        scope = "test_scope"
        per_token = 100
        per_ip = 50
        window = 120

        set_rate_limits(per_token, per_ip, window, scope=scope)

        result = get_rate_limits(scope)
        self.assertIsNotNone(result)
        self.assertEqual(result["per_token"], per_token)
        self.assertEqual(result["per_ip"], per_ip)
        self.assertEqual(result["window"], window)

        result = get_rate_limits("nonexistent_scope")
        self.assertIsNotNone(result)
        self.assertEqual(result["per_token"], None)
        self.assertEqual(result["per_ip"], None)
        self.assertEqual(result["window"], None
                         )

    def test_decorator_overrides_cache_scope_limits(self):
        """Test that decorator parameters override scope limits from cache."""
        scope = "override_scope"
        set_rate_limits(per_token=100, per_ip=10, window=60, scope=scope)

        @self.app.route("/override")
        @ratelimit(scope=scope, per_ip_limit=2)
        def override_endpoint():
            return "OK"

        client = self.app.test_client()

        response = client.get("/override")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-RateLimit-Limit"], "2")

        response = client.get("/override")
        self.assertEqual(response.status_code, 200)

        # 3rd request should fail (limit is 2, not 10)
        response = client.get("/override")
        self.assertEqual(response.status_code, 429)

    def test_scope_cache_values_stored_correctly(self):
        """Test that scope limits are stored in cache with correct keys."""
        scope = "verify_cache"
        per_token = 50
        per_ip = 25
        window = 30

        set_rate_limits(per_token, per_ip, window, scope=scope)

        # Verify the values are in cache with correct keys
        stored_per_token = cache.get(
            f"{scope}:rate_limit_per_token_limit",
            namespace=ratelimit_cache_namespace
        )
        stored_per_ip = cache.get(
            f"{scope}:rate_limit_per_ip_limit",
            namespace=ratelimit_cache_namespace
        )
        stored_window = cache.get(
            f"{scope}:rate_limit_window",
            namespace=ratelimit_cache_namespace
        )

        self.assertEqual(int(stored_per_token), per_token)
        self.assertEqual(int(stored_per_ip), per_ip)
        self.assertEqual(int(stored_window), window)

    def test_scope_limits_override_global(self):
        """Test that scope limits override global limits."""
        set_rate_limits(per_token=100, per_ip=10, window=60)
        scope = "priority_scope"
        set_rate_limits(per_token=100, per_ip=3, window=60, scope=scope)

        @self.app.route("/global")
        @ratelimit()
        def global_endpoint():
            return "OK"

        @self.app.route("/scope-priority")
        @ratelimit(scope=scope)
        def scope_priority_endpoint():
            return "OK"

        @self.app.route("/decorator-priority")
        @ratelimit(scope=scope, per_ip_limit=2)
        def decorator_priority_endpoint():
            return "OK"

        client = self.app.test_client()

        response = client.get("/global")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-RateLimit-Limit"], "10")

        response = client.get("/scope-priority")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-RateLimit-Limit"], "3")

        response = client.get("/decorator-priority")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-RateLimit-Limit"], "2")
