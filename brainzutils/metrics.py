import datetime
from functools import wraps

from redis import ResponseError

from brainzutils import cache

NAMESPACE_METRICS = "metrics"
REDIS_MAX_INTEGER = 2**63-1
RESERVED_TAG_NAMES = {"tag", "date"}
STATS_COUNT_DATE_KEY = "date"

_metrics_project_name = None


def init(project):
    global _metrics_project_name
    _metrics_project_name = project


def metrics_init_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not _metrics_project_name:
            raise RuntimeError("Metrics module needs to be initialized before use")
        return f(*args, **kwargs)
    return decorated


@cache.init_required
@metrics_init_required
def increment(metric_name, amount=1):
    """Increment the counter for a metric by a set amount. A metric is a counter that can increment over time
    and can be used for monitoring any statistic.

    If incrementing the counter causes it to go over redis' internal counter limit of 2**63-1, the counter
    is reset to 0. The metric name ``tag`` is reserved and cannot be used.

    Arguments:
        metric_name: the name of a metric
        amount: the amount to increase the counter by, must be 1 or greater (default: 1)

    Raises:
        ValueError if amount is less than 1 or greater than 2**63-1
        ValueError if the reserved metric name ``tag`` is used
    """

    if amount < 1:
        raise ValueError("amount must be 1 or greater")
    if amount > REDIS_MAX_INTEGER:
        raise ValueError("amount is too large")
    if metric_name in RESERVED_TAG_NAMES:
        raise ValueError("the name '{}' is reserved".format(metric_name))

    try:
        ret = cache.hincrby(_metrics_project_name, metric_name, amount, namespace=NAMESPACE_METRICS)
    except ResponseError as e:
        # If the current value is too large, redis will return this error message.
        # Reset to 0 and re-increment
        if e.args and "increment or decrement would overflow" in e.args[0]:
            cache.hset(_metrics_project_name, metric_name, 0, namespace=NAMESPACE_METRICS)
            ret = cache.hincrby(_metrics_project_name, metric_name, amount, namespace=NAMESPACE_METRICS)
        else:
            raise

    return ret


@cache.init_required
@metrics_init_required
def remove(metric_name):
    """Remove a metric from the local counter. When a metric is removed it will no longer
    appear in the data returned by :meth:`stats`

    Arguments:
        metric_name: The metric to remove
    """

    return cache.hdel(_metrics_project_name, [metric_name], namespace=NAMESPACE_METRICS)


@cache.init_required
@metrics_init_required
def stats():
    """Get the current value for metrics in the currently configured project.

    This can be used in a flask view to return the current metrics::

        @bp.route('/metric_statistics')
        def increment_metric():
            return jsonify(metrics.stats())

    The view can be read by telegraf or any other logging system.

    Returns:
        A dictionary containing metric names and counts for the current project, as well
        as a field ``tag`` containing the current project name. For example::

            {"new_users": 100,
             "computed_stats": 20,
             "tag": "listenbrainz.org"}
    """

    counters = cache.hgetall(_metrics_project_name, namespace=NAMESPACE_METRICS)
    ret = {str(k): int(v) for k, v in counters.items()}
    ret["tag"] = _metrics_project_name
    return ret


@cache.init_required
@metrics_init_required
def set_count(metric_name, **data):
    """Set fixed counter for a given metric name. This allows you
    to log the result of a given computation that happens periodically.

    For example, if you have an import process that happens periodically,
    you could call something like::

        metrics.set_count('import', artists=10, releases=27, recordings=100)

    to set some fixed counts for the ``import`` metric. These metrics are
    stored with the time that the method is called.
    Unlike incrementing statistics, a specific number cannot be incremented.
    To set new values for a subsequent iteration of the process, call it again.

    The statistics for a given metric can be retrieved with :meth:`stats_count`.

    Calling ``set_count`` with the same metric name but different data will cause all
    previous data values to be cleared. An entire metric can be removed with
    :meth:`remove_count`.
    """
    for k, v in data.items():
        if k in RESERVED_TAG_NAMES:
            raise ValueError("the name '{}' is reserved".format(k))
        try:
            int(v)
        except ValueError:
            raise ValueError("Argument values must be integers")
    metric_key = _metrics_project_name + ":" + metric_name
    # Override all values for this key by deleting it if it already exists
    cache.delete(metric_key, namespace=NAMESPACE_METRICS)
    for k, v in data.items():
        cache.hset(metric_key, k, v, namespace=NAMESPACE_METRICS)
    now = datetime.datetime.now()
    now = now.replace(microsecond=0)
    cache.hset(metric_key, "date", now.isoformat(), namespace=NAMESPACE_METRICS)


@cache.init_required
@metrics_init_required
def remove_count(metric_name):
    """Remove fixed counters for a specific metric.
    This will remove all counters for the given metric name from local storage.

    Arguments:
        metric_name: The metric to delete
    """
    metric_key = _metrics_project_name + ":" + metric_name
    return cache.delete(metric_key, namespace=NAMESPACE_METRICS)


@cache.init_required
@metrics_init_required
def stats_count(metric_name):
    """Get the fixed counters for a given metric in the currently configured project.

    This can be used in a flask view to return the current metrics::

        @bp.route('/metric_counts/<metric_name>')
        def increment_metric(metric_name):
            return jsonify(metrics.stats_count(metric_name))

    The view can be read by telegraf or any other logging system.

    Returns:
        A dictionary containing fixed counters for the given metric, as well
        as a field ``tag`` containing the current project name, a field ``metric`` containing
        the requested metric, and ``date`` containing the date that the metric was last written.
        For example::

            {"artists": 10,
             "releases": 29,
             "recordings": 100,
             "date": "2021-02-17T13:02:18",
             "metric": "import",
             "tag": "listenbrainz.org"}
    """

    metric_key = _metrics_project_name + ":" + metric_name
    counters = cache.hgetall(metric_key, namespace=NAMESPACE_METRICS)
    ret = {}
    for k, v in counters.items():
        k = str(k)
        if k == STATS_COUNT_DATE_KEY:
            ret[k] = v.decode('utf-8')
        else:
            ret[k] = int(v)
    ret["metric"] = metric_name
    ret["tag"] = _metrics_project_name
    return ret
