import unittest
import mock

from freezegun import freeze_time

from brainzutils import cache
from brainzutils import metrics


class MetricsTestCase(unittest.TestCase):

    def setUp(self) -> None:
        cache.init('redis')

    @freeze_time('2020-10-14 14:20:21')
    @mock.patch('brainzutils.metrics.cache.hincrby')
    def test_increment_hourly(self, hincrby):
        m = metrics.Metrics('test_m', metrics.METRICS_RANGE_HOUR)
        m.increment(2)
        hincrby.assert_called_with('test_m', '2020-10-14T14:00:00+00:00', 2, namespace='metrics')

    @freeze_time('2020-10-14 14:25:21')
    @mock.patch('brainzutils.metrics.cache.hincrby')
    def test_increment_10_min(self, hincrby):
        m = metrics.Metrics('test_m', metrics.METRICS_RANGE_10MIN)
        m.increment()
        hincrby.assert_called_with('test_m', '2020-10-14T14:20:00+00:00', 1, namespace='metrics')

    @mock.patch('brainzutils.metrics.cache.hgetall')
    def test_stats(self, hgetall):
        hgetall.return_value = {b'2020-10-14T14:00:00+00:00': b'1',
                                b'2020-10-14T15:00:00+00:00': b'20',
                                b'2020-10-14T16:00:00+00:00': b'8'}

        stats = metrics.stats('test_m')
        hgetall.assert_called_with('test_m', namespace='metrics')

        expected = [
            {'time': '2020-10-14T14:00:00+00:00', 'amount': 1},
            {'time': '2020-10-14T15:00:00+00:00', 'amount': 20},
            {'time': '2020-10-14T16:00:00+00:00', 'amount': 8}
        ]
        self.assertEqual(stats, expected)

    @mock.patch('brainzutils.metrics.cache.hkeys')
    @mock.patch('brainzutils.metrics.cache.hdel')
    def test_expire(self, hdel, hkeys):
        hkeys.return_value = [b'2020-10-14T14:00:00+00:00',
                              b'2020-10-14T18:00:00+00:00',
                              b'2020-10-14T15:00:00+00:00',
                              b'2020-10-14T16:00:00+00:00',
                              b'2020-10-14T17:00:00+00:00']

        m = metrics.Metrics('test_m', metrics.METRICS_RANGE_10MIN)
        m._expire_old_items(2)
        hkeys.assert_called_with('test_m', namespace='metrics')

        hdel.assert_called_with('test_m',
                                [b'2020-10-14T16:00:00+00:00',
                                 b'2020-10-14T17:00:00+00:00',
                                 b'2020-10-14T18:00:00+00:00'],
                                namespace='metrics'),
