from __future__ import division

from functools import wraps

import six
from redis import ResponseError

from brainzutils import cache

NAMESPACE_METRICS = "metrics"
REDIS_MAX_INTEGER = 2**63-1
RESERVED_TAG_NAMES = {"tag", "date"}

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
    ret = {six.ensure_text(k): int(v) for k, v in counters.items()}
    ret["tag"] = _metrics_project_name
    return ret
