import os
from brainzutils import cache


def setup_cache():
    host = os.environ.get("REDIS_HOST", "localhost")
    port = 6379
    namespace = "NS_TEST"

    cache.init(
        host=host,
        port=port,
        namespace=namespace,
    )
