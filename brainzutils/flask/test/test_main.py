import unittest

from brainzutils import flask

class FlaskTestCase(unittest.TestCase):

    def test_create_app(self):
        app = flask.CustomFlask(__name__)
        self.assertIsNotNone(app)

    def test_debug_toolbar(self):
        """ Tests that debug toolbar loads if initialized correctly
        """

        # create an app
        app = flask.CustomFlask(__name__)
        self.assertIsNotNone(app)
        app.debug = True
        app.config['SECRET_KEY'] = 'this is a totally secret key btw'
        app.init_debug_toolbar()

        # add a dummy route
        @app.route('/')
        def index():
            return '<html><body>test</body></html>'

        client = app.test_client()
        response = client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('flDebug', str(response.data))
