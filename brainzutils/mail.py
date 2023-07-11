"""This module provides a way to send emails."""
from email.message import EmailMessage
import mimetypes
import smtplib
from typing import List

from flask import current_app


def send_mail(subject: str,
              text: str,
              recipients: List[str],
              attachments=None,
              from_name="MetaBrainz Notifications",
              from_addr=None,
              boundary=None):
    """This function can be used as a foundation for sending email.

    Args:
        subject: Subject of the message.
        text: The message itself.
        recipients: List of recipients.
        attachments: List of (file object, subtype, name) tuples. For example:
            (<file_obj>, 'pdf', 'receipt.pdf').
        from_name: Name of the sender.
        from_addr: Email address of the sender.
    """
    if not isinstance(recipients, list):
        raise ValueError("recipients must be a list of email addresses")

    if 'SMTP_SERVER' not in current_app.config or 'SMTP_PORT' not in current_app.config:
        raise ValueError("Flask current_app requires config items SMTP_SERVER and SMTP_PORT to be set")

    if attachments is None:
        attachments = []
    if from_addr is None:
        from_addr = 'noreply@' + current_app.config['MAIL_FROM_DOMAIN']

    if current_app.config['TESTING']:  # Not sending any emails during the testing process
        return

    if not recipients:
        return

    message = EmailMessage()
    message['To'] = ", ".join(recipients)
    message['Subject'] = subject
    message['From'] = "%s <%s>" % (from_name, from_addr)
    message.set_content(text)
    if boundary is not None:
        message.set_boundary(boundary)

    for attachment in attachments:
        file_obj, subtype, name = attachment
        maintype, _, subtype = (mimetypes.guess_type(name)[0] or 'application/octet-stream').partition("/")
        message.add_attachment(file_obj.read(), maintype=maintype, subtype=subtype)
        file_obj.close()

    try:
        smtp_server = smtplib.SMTP(current_app.config['SMTP_SERVER'], current_app.config['SMTP_PORT'])
    except (socket.error, smtplib.SMTPException) as e:
        current_app.logger.error('Error while sending email: %s', e, exc_info=True)
        raise MailException(e)
    smtp_server.send_message(message)
    smtp_server.quit()


class MailException(Exception):
    pass
