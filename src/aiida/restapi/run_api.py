#!/usr/bin/env python
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""It defines the method with all required parameters to run restapi locally."""

import importlib
import os

from flask_cors import CORS

from . import api as api_classes
from .common.config import API_CONFIG, APP_CONFIG, CLI_DEFAULTS

__all__ = ('configure_api', 'run_api')


def run_api(flask_app=api_classes.App, flask_api=api_classes.AiidaApi, **kwargs):
    """Takes a flask.Flask instance and runs it.

    :param flask_app: Class inheriting from flask app class
    :type flask_app: :py:class:`flask.Flask`
    :param flask_api: flask_restful API class to be used to wrap the app
    :type flask_api: :py:class:`flask_restful.Api`
    :param hostname: hostname to run app on (only when using built-in server)
    :param port: port to run app on (only when using built-in server)
    :param config: directory containing the config.py file used to configure the RESTapi
    :param catch_internal_server:  If true, catch and print all inter server errors
    :param debug: enable debugging
    :param wsgi_profile: use WSGI profiler middleware for finding bottlenecks in web application
    :param posting: Whether or not to include POST-enabled endpoints (currently only `/querybuilder`).

    :returns: tuple (app, api) if hookup==False or runs app if hookup==True
    """
    hostname = kwargs.pop('hostname', CLI_DEFAULTS['HOST_NAME'])
    port = kwargs.pop('port', CLI_DEFAULTS['PORT'])
    debug = kwargs.pop('debug', APP_CONFIG['DEBUG'])

    api = configure_api(flask_app, flask_api, **kwargs)

    # Run app through built-in werkzeug server
    print(f" * REST API running on http://{hostname}:{port}{API_CONFIG['PREFIX']}")
    api.app.run(debug=debug, host=hostname, port=int(port), threaded=True)


def configure_api(flask_app=api_classes.App, flask_api=api_classes.AiidaApi, **kwargs):
    """Configures a flask.Flask instance and returns it.

    :param flask_app: Class inheriting from flask app class
    :type flask_app: :py:class:`flask.Flask`
    :param flask_api: flask_restful API class to be used to wrap the app
    :type flask_api: :py:class:`flask_restful.Api`
    :param config: directory containing the config.py configuration file
    :param catch_internal_server:  If true, catch and print internal server errors with full python traceback.
        Useful during app development.
    :param wsgi_profile: use WSGI profiler middleware for finding bottlenecks in the web application
    :param posting: Whether or not to include POST-enabled endpoints (currently only `/querybuilder`).

    :returns: Flask RESTful API
    :rtype: :py:class:`flask_restful.Api`
    """
    # Unpack parameters
    profile = kwargs.pop('profile', None)
    config = kwargs.pop('config', CLI_DEFAULTS['CONFIG_DIR'])
    catch_internal_server = kwargs.pop('catch_internal_server', CLI_DEFAULTS['CATCH_INTERNAL_SERVER'])
    wsgi_profile = kwargs.pop('wsgi_profile', CLI_DEFAULTS['WSGI_PROFILE'])
    posting = kwargs.pop('posting', CLI_DEFAULTS['POSTING'])

    if kwargs:
        raise ValueError(f'Unknown keyword arguments: {kwargs}')

    # Import the configuration file
    spec = importlib.util.spec_from_file_location(os.path.join(config, 'config'), os.path.join(config, 'config.py'))
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)

    # Instantiate an app
    app = flask_app(__name__, catch_internal_server=catch_internal_server)

    # Apply default configuration
    app.config.update(**config_module.APP_CONFIG)

    # Allow cross-origin resource sharing
    cors_prefix = r'{}/*'.format(config_module.API_CONFIG['PREFIX'])
    CORS(app, resources={cors_prefix: {'origins': '*'}})

    # Configure the serializer
    if config_module.SERIALIZER_CONFIG:
        from aiida.restapi.common.utils import CustomJSONProvider

        app.json = CustomJSONProvider(app)

    # Set up WSGI profiler if requested
    if wsgi_profile:
        from werkzeug.middleware.profiler import ProfilerMiddleware

        app.config['PROFILE'] = True
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])

    # Instantiate and return a Flask RESTful API by associating its app
    return flask_api(app, posting=posting, **config_module.API_CONFIG, profile=profile)
