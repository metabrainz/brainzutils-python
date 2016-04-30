import logging
from logging.handlers import RotatingFileHandler, SMTPHandler
from raven.contrib.flask import Sentry


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


def add_sentry(app, dsn, level=logging.WARNING):
    """Adds Sentry logging.

    Sentry is a realtime event logging and aggregation platform. Additional
    information about it is available at https://sentry.readthedocs.org/.

    We use Raven as a client for Sentry. More info about Raven is available at
    https://raven.readthedocs.org/.
    """
    Sentry(app, dsn=dsn, level=level, logging=True)
