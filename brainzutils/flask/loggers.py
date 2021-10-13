# pylint: disable=invalid-name
import logging
import os
from logging.handlers import RotatingFileHandler, SMTPHandler

import sentry_sdk
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.flask import FlaskIntegration


def add_file_handler(app, filename, max_bytes=512 * 1024, backup_count=100):
    """Adds file logging."""
    file_handler = RotatingFileHandler(filename, maxBytes=max_bytes,
                                       backupCount=backup_count)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
    ))
    app.logger.addHandler(file_handler)


def add_sentry(dsn, level=logging.WARNING, **options):
    """Adds Sentry event logging.

    Sentry is a realtime event logging and aggregation platform.
    By default we add integration to the python logger, flask, redis, and sqlalchemy.

    Arguments:
        dsn: The sentry DSN to connect to
        level: the logging level at which logging messages are sent as events to sentry
        options: Any other arguments to be passed to sentry_sdk.init.
          See https://docs.sentry.io/platforms/python/configuration/options/
    """
    sentry_sdk.init(dsn, integrations=[LoggingIntegration(level=level), FlaskIntegration(), RedisIntegration(),
                                       SqlalchemyIntegration()],
                    **options)
    container_name = os.getenv("CONTAINER_NAME")
    if container_name:
        sentry_sdk.set_tag("container_name", container_name)
