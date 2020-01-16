# -*- coding: utf-8 -*-
"""This module provides a way to send emails."""
from __future__ import absolute_import
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import current_app

import smtplib
import socket

def send_mail(subject, text, recipients, attachments=None,
              from_name="MetaBrainz Notifications",
              from_addr=None, boundary=None):
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

    if from_addr is None:
        from_addr = 'noreply@' + current_app.config['MAIL_FROM_DOMAIN']
              
    if current_app.config['TESTING']:  # Not sending any emails during the testing process
        return

    if not recipients:
        return

    message =MIMEMultipart()

    if boundary is not None:
        originalboundary = "===============2220963697271485568=="
        message = MIMEMultipart(boundary=originalboundary)
     
    message['To']="<%s>" %(recipients)
    message['Subject'] = subject
    message['From'] = "%s <%s>" % (from_name, from_addr)
    message.attach(MIMEText(text, _charset='utf-8'))

    if attachments is not None:

        for attachment in attachments:
            file_obj, subtype, name = attachment
            attachment = MIMEApplication(file_obj.read(), _subtype=subtype)
            file_obj.close()  # FIXME(roman): This feels kind of hacky. Maybe there's a better way?
            attachment.add_header('content-disposition', 'attachment', filename=name)
            message.attach(attachment)
    try:
        smtp_server = smtplib.SMTP(current_app.config['SMTP_SERVER'], current_app.config['SMTP_PORT'])
    except (socket.error, smtplib.SMTPException) as e:
        current_app.logger.error('Error while sending email: %s', e, exc_info=True)
        raise MailException(e)
    smtp_server.sendmail(from_addr, recipients, message.as_string())
    smtp_server.quit()


class MailException(Exception):
    pass
