import unittest
import smtplib

from mock import patch, call
from brainzutils import flask
from brainzutils import mail


class SendEmailTests(unittest.TestCase):

    @patch('brainzutils.mail.send_mail')
    def test_send_email(self, mock_send_mail):
        app=flask.CustomFlask(__name__) 
        with app.app_context():
            from_address = "noreply@metabrainz.org"
            recipients='sarthak2907@gmail.com'
            attachments=None
            text="It is a test mail"
            from_name='ListenBrainz'
            subject='ListenBrainz Spotify Importer Error'
            mail.send_mail(
            subject='ListenBrainz Spotify Importer Error',
            text="It is a test mail",
            recipients='sarthak2907@gmail.com',
            from_name='ListenBrainz',
            from_addr="noreply@metabrainz.org",
                          )
            self.expected=[subject, text, recipients, from_name, from_address]
            self.result=[mock_send_mail.call_args[1]['subject'], mock_send_mail.call_args[1]['text'], mock_send_mail.call_args[1]['recipients'], mock_send_mail.call_args[1]['from_name'], mock_send_mail.call_args[1]['from_addr']]
            mock_send_mail.assert_called_once()
            self.assertListEqual(self.expected, self.result)
        
