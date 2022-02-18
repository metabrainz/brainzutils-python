import logging
import os

import sentry_sdk
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.flask import FlaskIntegration


def init_sentry(dsn, level=logging.WARNING, **options):
    """Adds Sentry event logging.

    Sentry is a realtime event logging and aggregation platform.
    By default, we add integration to the python logger, flask, redis, and sqlalchemy.

    Arguments:
        dsn: The sentry DSN to connect to
        level: the logging level at which logging messages are sent as events to sentry
        options: Any other arguments to be passed to sentry_sdk.init.
          See https://docs.sentry.io/platforms/python/configuration/options/
    """
    sentry_sdk.init(dsn, integrations=[LoggingIntegration(level=level), FlaskIntegration(), RedisIntegration(),
                                       SqlalchemyIntegration()],
                    **options)
    # This env variable is set in the MetaBrainz production infrastructure and is unique per container
    container_name = os.getenv("CONTAINER_NAME")
    if container_name:
        sentry_sdk.set_tag("container_name", container_name)
