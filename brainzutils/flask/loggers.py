# pylint: disable=invalid-name
import logging
from logging.handlers import RotatingFileHandler, SMTPHandler
import raven
import raven.base
import raven.contrib.flask
import raven.transport.threaded_requests


class MissingRavenClient(raven.Client):
    """Raven client class that is used as a placeholder.
    This is done to make sure that calls to functions in the client don't fail
    even if the client is not initialized. Sentry server might be missing, but
    we don't want to check if it actually exists in every place exception is
    captured.
    """
    captureException = lambda self, *args, **kwargs: None
    captureMessage = lambda self, *args, **kwargs: None


_sentry_client = MissingRavenClient()  # type: raven.Client


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

    We use Raven as a client for Sentry. More info about Raven is available at
    https://raven.readthedocs.org/.
    """
    app.config["SENTRY_TRANSPORT"] = raven.transport.threaded_requests.ThreadedRequestsHTTPTransport
    app.config["SENTRY_CONFIG"] = options
    global _sentry_client
    _sentry_client = raven.contrib.flask.Sentry(
        app=app,
        dsn=dsn,
        level=level,
        logging=True,
    )


def get_sentry_client():
    return _sentry_client
