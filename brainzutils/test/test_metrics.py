import os
from unittest import mock, TestCase

from brainzutils import cache
from brainzutils import metrics


class MetricsTestCase(TestCase):

    def setUp(self):
        cache.init('redis')

    def tearDown(self):
        metrics._metrics_project_name = None

    @mock.patch('brainzutils.metrics.cache._r.rpush')
    def test_set(self, rpush):
        metrics.init('listenbrainz.org')
        os.environ["PRIVATE_IP"] = "127.0.0.1"
        metrics.set("my_metric", timestamp=1619629462352960742, test_i=2, test_fl=.3, test_t=True, test_f=False, test_s="gobble")
        rpush.assert_called_with(metrics.REDIS_METRICS_KEY,
            'my_metric,dc=hetzner,server=127.0.0.1,project=listenbrainz.org test_i=2i,test_fl=0.300000,test_t=t,test_f=f,test_s="gobble" 1619629462352960742')
