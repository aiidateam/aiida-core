#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=inconsistent-return-statements
"""
It defines the method with all required parameters to run restapi locally.
"""
import importlib
import os

from flask_cors import CORS
from .common.config import CLI_DEFAULTS, APP_CONFIG, API_CONFIG
from . import api as api_classes


def run_api(flask_app=api_classes.App, flask_api=api_classes.AiidaApi, **kwargs):
    """
    Takes a flask.Flask instance and runs it.

    :param flask_app: Class inheriting from flask app class
    :type flask_app: :py:class:`flask.Flask`
    :param flask_api: flask_restful API class to be used to wrap the app
    :type flask_api: :py:class:`flask_restful.Api`

    List of valid keyword arguments:
    :param hostname: hostname to run app on (only when using built-in server)
    :param port: port to run app on (only when using built-in server)
    :param config: directory containing the config.py file used to configure the RESTapi
    :param catch_internal_server:  If true, catch and print all inter server errors
    :param debug: enable debugging
    :param wsgi_profile: use WSGI profiler middleware for finding bottlenecks in web application
    :param hookup: If true, hook up application to built-in server - else just return it
    """
    # pylint: disable=too-many-locals

    # Unpack parameters
    hostname = kwargs.pop('hostname', CLI_DEFAULTS['HOST_NAME'])
    port = kwargs.pop('port', CLI_DEFAULTS['PORT'])
    config = kwargs.pop('config', CLI_DEFAULTS['CONFIG_DIR'])

    catch_internal_server = kwargs.pop('catch_internal_server', CLI_DEFAULTS['CATCH_INTERNAL_SERVER'])
    debug = kwargs.pop('debug', APP_CONFIG['DEBUG'])
    wsgi_profile = kwargs.pop('wsgi_profile', CLI_DEFAULTS['WSGI_PROFILE'])
    hookup = kwargs.pop('hookup', CLI_DEFAULTS['HOOKUP_APP'])

    if kwargs:
        raise ValueError('Unknown keyword arguments: {}'.format(kwargs))

    # Import the configuration file
    spec = importlib.util.spec_from_file_location(os.path.join(config, 'config'), os.path.join(config, 'config.py'))
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)

    # Instantiate an app
    app = flask_app(__name__, catch_internal_server=catch_internal_server)

    # Apply default configuration
    app.config.update(**config_module.APP_CONFIG)

    # Allow cross-origin resource sharing
    cors_prefix = r'{}/*'.format(config_module)
    CORS(app, resources={cors_prefix: {'origins': '*'}})

    # Configure the serializer
    if config_module.SERIALIZER_CONFIG:
        from aiida.restapi.common.utils import CustomJSONEncoder
        app.json_encoder = CustomJSONEncoder

    # Set up WSGI profile if requested
    if wsgi_profile:
        from werkzeug.middleware.profiler import ProfilerMiddleware

        app.config['PROFILE'] = True
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])

    # Instantiate an Api by associating its app
    api = flask_api(app, **API_CONFIG)

    if hookup:
        # Run app through built-in werkzeug server
        print(' * REST API running on http://{}:{}{}'.format(hostname, port, API_CONFIG['PREFIX']))
        api.app.run(debug=debug, host=hostname, port=int(port), threaded=True)

    else:
        # Return the app & api without specifying port/host to be handled by an external server (e.g. apache).
        # Some of the user-defined configuration of the app is ineffective (only affects built-in server).
        return (app, api)
