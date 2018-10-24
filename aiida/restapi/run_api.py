#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
It defines the method with all required parameters to run restapi locally.
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import argparse
import imp
import os

from flask_cors import CORS

from aiida.backends.utils import load_dbenv


# pylint: disable=inconsistent-return-statements,too-many-locals
def run_api(flask_app, flask_api, *args, **kwargs):
    """
    Takes a flask.Flask instance and runs it. Parses
    command-line flags to configure the app.

    flask_app: Class inheriting from Flask app class
    flask_api = flask_restful API class to be used to wrap the app

    args: required by argparse

    kwargs:
    List of valid parameters:
    prog_name: name of the command before arguments are parsed. Useful when
    api is embedded in a command, such as verdi restapi
    default_host: self-explainatory
    default_port: self-explainatory
    default_config_dir = directory containing the config.py file used to
    configure the RESTapi
    parse_aiida_profile= if True, parses an option to specify the AiiDA
    profile
    All other passed parameters are ignored.
    """

    import aiida  # Mainly needed to locate the correct aiida path

    # Unpack parameters and assign defaults if needed
    prog_name = kwargs['prog_name'] if 'prog_name' in kwargs else ""

    default_host = kwargs['default_host'] if 'default_host' in kwargs else \
        "127.0.0.1"

    default_port = kwargs['default_port'] if 'default_port' in kwargs else \
        "5000"

    default_config_dir = kwargs['default_config_dir'] if \
        'default_config_dir' in kwargs \
        else os.path.join(os.path.split(os.path.abspath(
        aiida.restapi.__file__))[0], 'common')

    parse_aiida_profile = kwargs['parse_aiida_profile'] if \
        'parse_aiida_profile' in kwargs else False

    catch_internal_server = kwargs['catch_internal_server'] if\
        'catch_internal_server' in kwargs else False

    hookup = kwargs['hookup'] if 'hookup' in kwargs else False

    # Set up the command-line options
    parser = argparse.ArgumentParser(prog=prog_name, description='Hook up the AiiDA ' 'RESTful API')

    parser.add_argument("-H", "--host",
                        help="Hostname of the Flask app " + \
                             "[default %s]" % default_host,
                        dest='host',
                        default=default_host)
    parser.add_argument("-P", "--port",
                        help="Port for the Flask app " + \
                             "[default %s]" % default_port,
                        dest='port',
                        default=default_port)
    parser.add_argument("-c", "--config-dir",
                        help="Directory with config.py for Flask app " + \
                             "[default {}]".format(default_config_dir),
                        dest='config_dir',
                        default=default_config_dir)

    # This one is included only if necessary
    if parse_aiida_profile:
        parser.add_argument(
            "-p",
            "--aiida-profile",
            help="AiiDA profile to expose through the RESTful "
            "API [default: the default AiiDA profile]",
            dest="aiida_profile",
            default=None)

    # Two options useful for debugging purposes, but
    # a bit dangerous so not exposed in the help message.
    parser.add_argument("-d", "--debug", action="store_true", dest="debug", help=argparse.SUPPRESS)
    parser.add_argument("-w", "--wsgi-profile", action="store_true", dest="wsgi_profile", help=argparse.SUPPRESS)

    parsed_args = parser.parse_args(args)

    # Import the right configuration file
    confs = imp.load_source(
        os.path.join(parsed_args.config_dir, 'config'), os.path.join(parsed_args.config_dir, 'config.py'))

    import aiida.backends.settings as settings

    # Set aiida profile
    #
    # General logic:
    #
    # if aiida_profile is parsed the following cases exist:
    #
    # aiida_profile:
    #    "default"    --> default profile set in .aiida/config.json
    #    <profile>    --> corresponding profile in .aiida/config.json
    #    None         --> default restapi profile set in <config_dir>/config,py
    #
    # if aiida_profile is not parsed we assume
    #
    # default restapi profile set in <config_dir>/config.py

    if parse_aiida_profile and parsed_args.aiida_profile is not None:
        aiida_profile = parsed_args.aiida_profile

    elif confs.DEFAULT_AIIDA_PROFILE is not None:
        aiida_profile = confs.DEFAULT_AIIDA_PROFILE

    else:
        aiida_profile = "default"

    if aiida_profile != "default":
        settings.AIIDADB_PROFILE = aiida_profile
    else:
        pass  # This way the default of .aiida/config.json will be used

    # Set the AiiDA environment. If already loaded, load_dbenv will raise an
    # exception
    # if not is_dbenv_loaded():
    load_dbenv()

    # Instantiate an app
    app_kwargs = dict(catch_internal_server=catch_internal_server)
    app = flask_app(__name__, **app_kwargs)

    # Config the app
    app.config.update(**confs.APP_CONFIG)

    # cors
    cors_prefix = os.path.join(confs.PREFIX, "*")
    CORS(app, resources={r"" + cors_prefix: {"origins": "*"}})

    # Config the serializer used by the app
    if confs.SERIALIZER_CONFIG:
        from aiida.restapi.common.utils import CustomJSONEncoder
        app.json_encoder = CustomJSONEncoder

    # If the user selects the profiling option, then we need
    # to do a little extra setup
    if parsed_args.wsgi_profile:
        from werkzeug.contrib.profiler import ProfilerMiddleware

        app.config['PROFILE'] = True
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])

    # Instantiate an Api by associating its app
    api_kwargs = dict(PREFIX=confs.PREFIX, PERPAGE_DEFAULT=confs.PERPAGE_DEFAULT, LIMIT_DEFAULT=confs.LIMIT_DEFAULT)
    api = flask_api(app, **api_kwargs)

    # Check if the app has to be hooked-up or just returned
    if hookup:
        api.app.run(debug=parsed_args.debug, host=parsed_args.host, port=int(parsed_args.port), threaded=True)

    else:
        # here we return the app, and the api with no specifications on debug
        #  mode, port and host. This can be handled by an external server,
        # e.g. apache2, which will set the host and port. This implies that
        # the user-defined configuration of the app is ineffective (it only
        # affects the internal werkzeug server used by Flask).
        return (app, api)


# Standard boilerplate to run the api
if __name__ == '__main__':

    # I run the app via a wrapper that accepts arguments such as host and port
    # e.g. python api.py --host=127.0.0.2 --port=6000 --config-dir=~/.restapi
    # Default address is 127.0.0.1:5000, default config directory is
    # <aiida_path>/aiida/restapi/common
    #
    # Start the app by sliding the argvs to flaskrun, choose to take as an
    # argument also whether to parse the aiida profile or not (in verdi
    # restapi this would not be the case)

    import sys
    from aiida.restapi.api import AiidaApi, App

    #Or, equivalently, (useful starting point for derived apps)
    #import the app object and the Api class that you want to combine.

    run_api(App, AiidaApi, *sys.argv[1:], parse_aiida_profile=True, hookup=True, catch_internal_server=True)
