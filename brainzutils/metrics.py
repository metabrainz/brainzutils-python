from functools import wraps
import os
import socket
import logging
from time import time_ns
from typing import Dict

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
def set(metric_name: str, tags: Dict[str, str] = None, timestamp: int = None, **fields):
    """
        Submit a metric to be read by the MetaBrainz influx datastore for graphing/monitoring
        purposes. These metrics are stored in redis in the influxdb line protocol format:
        https://docs.influxdata.com/influxdb/v2.0/reference/syntax/line-protocol/

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

    if tags is None:
        tags = {}

    tags["dc"] = "hetzner"
    tags["server"] = host
    tags["project"] = _metrics_project_name
    tag_string = ",".join([ "%s=%s" % (k, v) for k, v in tags.items() ])

    fields_list = []
    for k, v in fields.items():
        if type(v) == int:
            fields_list.append("%s=%di" % (k, v))
        elif type(v) == float:
            fields_list.append('%s=%f' % (k, v))
        elif type(v) == bool:
            val = "t" if v else "f"
            fields_list.append("%s=%s" % (k, val))
        elif type(fields[k]) == str:
            fields_list.append('%s="%s"' % (k, v))
        else:
            fields_list.append("%s=%s" % (k, str(v)))

    fields = ",".join(fields_list)

    if timestamp is None:
        timestamp = time_ns()

    metric = "%s,%s %s %d" % (metric_name, tag_string, fields, timestamp)
    try:
        cache._r.rpush(REDIS_METRICS_KEY, metric)
    except Exception:
        logging.error("Cannot set redis metric:", exc_info=True)
