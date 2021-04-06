import unittest
import mock
from freezegun import freeze_time
from redis import ResponseError

from brainzutils import cache
from brainzutils import metrics


class MetricsTestCase(unittest.TestCase):

    def setUp(self):
        cache.init('redis')

    def tearDown(self):
        metrics._metrics_project_name = None

    @mock.patch('brainzutils.metrics.cache.hincrby')
    def test_increment(self, hincrby):
        metrics.init('listenbrainz.org')
        metrics.increment('test_m', 2)
        hincrby.assert_called_with('listenbrainz.org', 'test_m', 2, namespace='metrics')

    @mock.patch('brainzutils.metrics.cache.hincrby')
    def test_increment_default(self, hincrby):
        metrics.init('listenbrainz.org')
        metrics.increment('test_m')
        hincrby.assert_called_with('listenbrainz.org', 'test_m', 1, namespace='metrics')

    def test_increment_negative(self):
        metrics.init('listenbrainz.org')
        with self.assertRaises(ValueError):
            metrics.increment('test_m', -2)

    def test_increment_badname(self):
        metrics.init('listenbrainz.org')
        with self.assertRaises(ValueError):
            metrics.increment('tag')

    def test_increment_noinit(self):
        with self.assertRaises(RuntimeError):
            metrics.increment('test_m')

    @mock.patch('brainzutils.metrics.cache.hincrby')
    @mock.patch('brainzutils.metrics.cache.hset')
    def test_increment_overflow(self, hset, hincrby):
        hincrby.side_effect = [ResponseError("increment or decrement would overflow"), 10]
        metrics.init('listenbrainz.org')
        metrics.increment('test_m', 10)

        hincrby.assert_has_calls([mock.call('listenbrainz.org', 'test_m', 10, namespace='metrics'),
                                  mock.call('listenbrainz.org', 'test_m', 10, namespace='metrics')])
        hset.assert_called_with('listenbrainz.org', 'test_m', 0, namespace='metrics')

    @mock.patch('brainzutils.metrics.cache.hdel')
    def test_remove(self, hdel):
        metrics.init('listenbrainz.org')
        metrics.remove('test_m')
        hdel.assert_called_with('listenbrainz.org', ['test_m'], namespace='metrics')

    @mock.patch('brainzutils.metrics.cache.hgetall')
    def test_stats(self, hgetall):
        metrics.init('listenbrainz.org')
        hgetall.return_value = {b'valueone': b'1',
                                b'valuetwo': b'20',
                                b'somethingelse': b'8'}

        stats = metrics.stats()
        hgetall.assert_called_with('listenbrainz.org', namespace='metrics')

        expected = {'valueone': 1,
                    'valuetwo': 20,
                    'somethingelse': 8,
                    'tag': 'listenbrainz.org'}

        self.assertEqual(stats, expected)

    @freeze_time('2021-02-15T10:22:00')
    @mock.patch('brainzutils.metrics.cache.hset')
    @mock.patch('brainzutils.metrics.cache.delete')
    def test_set_count(self, mock_del, hset):
        metrics.init('listenbrainz.org')
        metrics.set_count('dataimport', artists=10, recordings=2)

        mock_del.assert_called_with('listenbrainz.org:dataimport', namespace='metrics')
        hset.assert_has_calls([mock.call('listenbrainz.org:dataimport', 'artists', 10, namespace='metrics'),
                               mock.call('listenbrainz.org:dataimport', 'recordings', 2, namespace='metrics'),
                               mock.call('listenbrainz.org:dataimport', 'date', '2021-02-15T10:22:00', namespace='metrics')],
                              any_order=True)

    def test_set_count_invalid_values(self):
        metrics.init('listenbrainz.org')
        with self.assertRaises(ValueError):
            metrics.set_count('dataimport', date=1)

        with self.assertRaises(ValueError):
            metrics.set_count('dataimport', artists='not-an-int')

    @mock.patch('brainzutils.metrics.cache.delete')
    def test_remove_count(self, mock_del):
        metrics.init('listenbrainz.org')
        metrics.remove_count('dataimport')
        mock_del.assert_called_with('listenbrainz.org:dataimport', namespace='metrics')

    @mock.patch('brainzutils.metrics.cache.hgetall')
    def test_stats_count(self, hgetall):
        metrics.init('listenbrainz.org')
        hgetall.return_value = {b'valueone': b'1',
                                b'valuetwo': b'20',
                                b'date': b'2021-02-12T13:02:18'}

        stats = metrics.stats_count('dataimport')
        hgetall.assert_called_with('listenbrainz.org:dataimport', namespace='metrics')

        expected = {'valueone': 1,
                    'valuetwo': 20,
                    'date': '2021-02-12T13:02:18',
                    'metric': 'dataimport',
                    'tag': 'listenbrainz.org'}

        self.assertEqual(stats, expected)
