# pylint: disable=invalid-name
import logging
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


def add_email_handler(app, mail_server, mail_port, mail_from_host,
                      log_email_recipients, log_email_topic,
                      level=logging.ERROR):
    """Adds email notifications about captured logs."""
    mail_handler = SMTPHandler(
        (mail_server, mail_port),
        "logs@" + mail_from_host,
        log_email_recipients,
        log_email_topic
    )
    mail_handler.setLevel(level)
    mail_handler.setFormatter(logging.Formatter('''
    Message type: %(levelname)s
    Location: %(pathname)s:%(lineno)d
    Module: %(module)s
    Function: %(funcName)s
    Time: %(asctime)s

    Message:

    %(message)s
    '''))
    app.logger.addHandler(mail_handler)


def add_sentry(app, dsn, level=logging.WARNING, **options):
    """Adds Sentry logging.

    Sentry is a realtime event logging and aggregation platform. Additional
    information about it is available at https://sentry.readthedocs.org/.
    """
    app.config["SENTRY_CONFIG"] = options
    sentry_sdk.init(dsn, integrations=[LoggingIntegration(level=level), FlaskIntegration(), RedisIntegration(),
                                       SqlalchemyIntegration()])
