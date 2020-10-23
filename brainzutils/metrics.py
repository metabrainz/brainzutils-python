from __future__ import division

import datetime

import six

from brainzutils import cache

NAMESPACE_METRICS = "metrics"

# Keep this many hours of old cache items in each key
HOURS_TO_KEEP = 12

METRICS_RANGE_MINUTE = 1
METRICS_RANGE_10MIN = 10
METRICS_RANGE_HOUR = 60


def increment(metric_name, amount=1):
    """Increment a metric with the name ``metric_name`` with a default range of one hour
    Arguments:
        metric_name: the name of a metric
        amount (int): the amount to increment the metrric by (default 1)
    """
    metric = Metrics(metric_name, METRICS_RANGE_HOUR)
    metric.increment(amount)


def stats(metric_name):
    """Get an overview of the metrics for a given metric name"""
    metric = Metrics(metric_name, METRICS_RANGE_HOUR)
    return metric.stats()


class Metrics:
    """Metrics keeps basic counts of the number of events that occur over time.
    This can be used to count events in a system, grouping events in a time range together
    (e.g. all events that happened in 10 minutes, or in an hour).

    Items are stored in a separate cache namespace.

    Example usage:

        counter = Metrics("user-signups", METRICS_RANGE_10MIN)
        counter.increment()

        ...
        return jsonify(counter.stats())

    Dates are stored in UTC.

    TODO: Ranges must be multiples of 60 minutes. If not, the last bucket of the hour may be shorter than the
      duration of `range`
    """

    @cache.init_required
    def __init__(self, name, range):
        """Create a metrics object. The BU cache must be initalised first.

        Arguments:
            name: the name of the metrics to record.
            range: the duration in minutes of each bucket"""
        self.name = name
        self.range = range

    def increment(self, amount=1):
        """Increment the counter of the current bucket by a set amount.

        Arguments:
            amount: the amount to increase the counter by (default: 1)"""

        now = datetime.datetime.now(tz=datetime.timezone.utc)
        minute = now.minute // self.range * self.range
        now = now.replace(minute=minute, second=0, microsecond=0)
        field = now.isoformat()

        ret = cache.hincrby(self.name, field, amount, namespace=NAMESPACE_METRICS)
        tokeep = int(60 // self.range * HOURS_TO_KEEP)
        self._expire_old_items(tokeep)
        return ret

    def _expire_old_items(self, tokeep):
        """Remove old items from the redis hash
        TODO: This kind of keeps HOURS_TO_KEEP items, but only if all buckets exist.
          if there is a gap (bucket with 0 items) then it will keep more than
          HOURS_TO_KEEP hours worth of items
        """
        items = cache.hkeys(self.name, namespace=NAMESPACE_METRICS)
        toremove = sorted(items)[tokeep:]
        if toremove:
            cache.hdel(self.name, toremove, namespace=NAMESPACE_METRICS)

    def stats(self):
        """Get all current stats for this counter.
         Returns a dictionary of {bucket: count} items where bucket
         is the UTC timestamp that the bucket starts at, in iso8601 format"""
        counters = cache.hgetall(self.name, namespace=NAMESPACE_METRICS)
        ret = []
        for key in sorted(counters.keys()):
            ret.append({
                'time': six.ensure_text(key),
                self.name: int(counters[key])
            })

        return ret
