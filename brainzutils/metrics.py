import datetime
from functools import wraps
import os
import socket
from time import time_ns
from typing import Dict

from redis import ResponseError

from brainzutils import cache

REDIS_METRICS_KEY = "metrics:influx_data"
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
def set(metric_name: str, tags: Dict[str,str]={}, timestamp: int=None, **fields):
    """
        Submit a metric to the MetaBrainz influx datastore for graphing/monitoring
        purposes.

        Args:
          metric_name: The name of the metric to record.
          tags: Additional influx tags to write with the metric. (optional)
          timestamp: A nanosecond timestamp to use for this metric. If not provided
                     the current time is used.
          fields: The key, value pairs to store with this metric.
    """

    # Add types to influx data
    try:
        host = os.environ['PRIVATE_IP']
    except KeyError:
        host = socket.gethostname()

    tags["dc"] = "hetzner"
    tags["server"] = host
    tags["project"] = _metrics_project_name
    tag_string = ",".join([ "%s=%s" % (k, tags[k]) for k in tags ])

    fields_list = []
    for k in fields:
        if type(fields[k]) == int:
            fields_list.append("%s=%di" % (k, fields[k]))
        elif type(fields[k]) == bool and fields[k] == True:
            fields_list.append("%s=t" % (k))
        elif type(fields[k]) == bool and fields[k] == False:
            fields_list.append("%s=f" % (k))
        elif type(fields[k]) == str:
            fields_list.append('%s="%s"' % (k, fields[k]))
        else:
            fields_list.append("%s=%s" % (k, str(fields[k])))

    fields = " ".join(fields_list)

    if timestamp is None:
        timestamp = time_ns()

    metric = "%s,%s %s %d" % (metric_name, tag_string, fields, timestamp)
    try:
        cache._r.rpush(REDIS_METRICS_KEY, metric)
    except Exception:
        # If we fail to push the metric to redis, so be it.
        pass
