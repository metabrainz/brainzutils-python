import unittest
import smtplib
from unittest import mock

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from brainzutils import flask
from brainzutils import mail

class MailTestCase(unittest.TestCase):

    @mock.patch('smtplib.SMTP')
    def test_send_email(self, mock_smtp):
        app = flask.CustomFlask(__name__)
        app.config['SMTP_SERVER'] = 'localhost'
        app.config['SMTP_PORT'] = 8080

        with app.app_context():
            from_address = 'noreply@metabrainz.org'
            recipients = 'sarthak2907@gmail.com'
            text = 'It is a test mail'
            from_name = 'ListenBrainz'
            subject = 'ListenBrainz Spotify Importer Error'
            boundary = '===============2220963697271485568=='
            message = MIMEMultipart(boundary=boundary)
            message['To'] = '<%s>' % (recipients)
            message['Subject'] = subject
            message['From'] = '%s <%s>' % (from_name, from_address)
            message.attach(MIMEText(text, _charset='utf-8'))

            mail.send_mail(
                subject='ListenBrainz Spotify Importer Error',
                text='It is a test mail',
                recipients='sarthak2907@gmail.com',
                attachments=None,
                from_name='ListenBrainz',
                from_addr='noreply@metabrainz.org',
                boundary=boundary
            )

            mock_smtp.return_value.sendmail.assert_called_once_with(from_address, recipients, message.as_string())
