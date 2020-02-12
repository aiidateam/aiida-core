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


def run_api(flask_app, flask_api, **kwargs):
    """
    Takes a flask.Flask instance and runs it.

    flask_app: Class inheriting from Flask app class
    flask_api = flask_restful API class to be used to wrap the app

    kwargs:
    List of valid parameters:
    prog_name: name of the command before arguments are parsed. Useful when
    api is embedded in a command, such as verdi restapi
    hostname: self-explainatory
    port: self-explainatory
    config: directory containing the config.py file used to
    configure the RESTapi
    catch_internal_server: If true, catch and print all inter server errors
    debug: self-explainatory
    wsgi_profile:to use WSGI profiler middleware for finding bottlenecks in web application
    hookup: to hookup app
    All other passed parameters are ignored.
    """
    # pylint: disable=too-many-locals

    # Unpack parameters
    hostname = kwargs['hostname']
    port = kwargs['port']
    config = kwargs['config']

    catch_internal_server = kwargs.pop('catch_internal_server', False)
    debug = kwargs['debug']
    wsgi_profile = kwargs['wsgi_profile']
    hookup = kwargs['hookup']

    # Import the right configuration file
    spec = importlib.util.spec_from_file_location(os.path.join(config, 'config'), os.path.join(config, 'config.py'))
    confs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(confs)

    # Instantiate an app
    app_kwargs = dict(catch_internal_server=catch_internal_server)
    app = flask_app(__name__, **app_kwargs)

    # Config the app
    app.config.update(**confs.APP_CONFIG)

    # cors
    cors_prefix = os.path.join(confs.PREFIX, '*')
    CORS(app, resources={r'' + cors_prefix: {'origins': '*'}})

    # Config the serializer used by the app
    if confs.SERIALIZER_CONFIG:
        from aiida.restapi.common.utils import CustomJSONEncoder
        app.json_encoder = CustomJSONEncoder

    # If the user selects the profiling option, then we need
    # to do a little extra setup
    if wsgi_profile:
        from werkzeug.middleware.profiler import ProfilerMiddleware

        app.config['PROFILE'] = True
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])

    # Instantiate an Api by associating its app
    api_kwargs = dict(PREFIX=confs.PREFIX, PERPAGE_DEFAULT=confs.PERPAGE_DEFAULT, LIMIT_DEFAULT=confs.LIMIT_DEFAULT)
    api = flask_api(app, **api_kwargs)

    # Check if the app has to be hooked-up or just returned
    if hookup:
        print(' * REST API running on http://{}:{}{}'.format(hostname, port, confs.PREFIX))
        api.app.run(debug=debug, host=hostname, port=int(port), threaded=True)

    else:
        # here we return the app, and the api with no specifications on debug
        #  mode, port and host. This can be handled by an external server,
        # e.g. apache2, which will set the host and port. This implies that
        # the user-defined configuration of the app is ineffective (it only
        # affects the internal werkzeug server used by Flask).
        return (app, api)
