from flask import Flask
from flask_debugtoolbar import DebugToolbarExtension


class CustomFlask(Flask):
    """Custom version of Flask with our bells and whistles."""

    def __init__(self, import_name, config_file=None, debug=None,
                 *args, **kwargs):
        """Create an instance of Flask app.

            See original documentation for Flask.

            Arguments:
                import_name (str): Name of the application package.
                config_file (str): Path to a config file that needs to be loaded.
                    Should be in a form of Python module.
                debug (bool): Override debug value.
        """
        super(CustomFlask, self).__init__(import_name, *args, **kwargs)
        if config_file:
            self.config.from_pyfile(config_file)
        if debug is not None:
            self.debug = debug

    def init_debug_toolbar(self):
        """This method initializes the Flask-Debug extension toolbar for the
        Flask app.

        Note that the Flask-Debug extension requires app.debug be true
        and the SECRET_KEY be defined in app.config.
        """
        if self.debug:
            DebugToolbarExtension(self)
