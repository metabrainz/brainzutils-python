from __future__ import division

import datetime

import six

from brainzutils import cache

NAMESPACE_STATS = "timeseries_stats"

# Keep this many hours of old cache items in each key
HOURS_TO_KEEP = 12

STATS_RANGE_MINUTE = 1
STATS_RANGE_10MIN = 10
STATS_RANGE_HOUR = 60


class TimeseriesStats:
    """TimeseriesStats keeps basic counts of the number of events that occur over time.
    This can be used to count events in a system, grouping events in a time range together
    (e.g. all events that happened in 10 minutes, or in an hour).

    Items are stored in a separate cache namespace.

    Example usage:

        counter = TimeseriesStats("user-signups", STATS_RANGE_10MIN)
        counter.increment()

        ...
        return jsonify(counter.stats())

    Dates are stored in UTC.

    TODO: Ranges must be multiples of 60 minutes. If not, the last bucket of the hour may be shorter than the
      duration of `range`
    """

    @cache.init_required
    def __init__(self, name, range):
        """Create a stats object. The BU cache must be initalised first.

        Arguments:
            name: the name of the stats to record.
            range: the duration in minutes of each bucket"""
        self.name = name
        self.range = range

    def increment(self, amount=1):
        """Increment the counter of the current bucket by a set amount.

        Arguments:
            amount: the amount to increase the counter by (default: 1)"""

        now = datetime.datetime.utcnow()
        minute = now.minute // self.range * self.range
        now = now.replace(minute=minute, second=0, microsecond=0)
        field = now.isoformat()

        ret = cache.hincrby(self.name, field, amount, namespace=NAMESPACE_STATS)
        tokeep = int(60 // self.range * HOURS_TO_KEEP)
        self._expire_old_items(tokeep)
        return ret

    def _expire_old_items(self, tokeep):
        """Remove old items from the redis hash
        TODO: This kind of keeps HOURS_TO_KEEP items, but only if all buckets exist.
          if there is a gap (bucket with 0 items) then it will keep more than
          HOURS_TO_KEEP hours worth of items
        """
        items = cache.hkeys(self.name, namespace=NAMESPACE_STATS)
        toremove = items[tokeep:]
        if toremove:
            cache.hdel(self.name, toremove)

    def stats(self):
        """Get all current stats for this counter.
         Returns a dictionary of {bucket: count} items where bucket
         is the UTC timestamp that the bucket starts at, in iso8601 format"""
        counters = cache.hgetall(self.name, namespace=NAMESPACE_STATS)
        ret = {}
        for key in sorted(counters.keys()):
            ret[six.ensure_text(key)] = int(counters[key])
        return ret
