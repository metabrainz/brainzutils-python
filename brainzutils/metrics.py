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
def set(metric_name: str, tags: Dict[str,str]=None, timestamp: int=None, **fields):
    """
        Submit a metric to the MetaBrainz influx datastore for graphing/monitoring
        purposes. TBC.
    """

    hostid = os.environ['PRIVATE_IP']
    if not hostid:
        hostid = socket.gethostname()

    tags["dc"] = "hetzner"
    tags["server"] = hostid
    tag_string = ",".join([ "%s=%s" % (k, tags[k]) for k in tags ])

    fields = " ".join([ "%s=%s" % (k, fields[k]) for k in fields ])

    if timestamp is None:
        timestamp = time_ns()

    metric = "%s,%s %s %d" % (metric_name, tag_string, fields, timestamp)
    try:
        cache.rpush(REDIS_METRICS_KEY, metric)
    except Exception:
        # If we fail to push the metric to redis, so be it.
        pass
