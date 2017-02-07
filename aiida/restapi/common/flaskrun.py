## This snippet has been originally writtten by Armin Ronacher, who explicitely
# defined it to be of public domain and freely usable as the user likes.

import argparse
import imp
import os
import aiida  # Mainly needed to locate the correct aiida path
from aiida.backends.utils import load_dbenv, is_dbenv_loaded

def flaskrun(app, *args, **kwargs):

    """
    Takes a flask.Flask instance and runs it. Parses
    command-line flags to configure the app.

    app: app to be run
    *args: required by argparse

    List of valid parameters
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

    # Unpack parameters and assign defaults if needed
    prog_name = kwargs['prog_name'] if 'prog_name' in kwargs else ""

    default_host = kwargs['default_host'] if 'default_host' in kwargs else \
        "127.0.0.1"

    default_port = kwargs['default_port'] if 'default_port' in kwargs else \
        "5000"

    default_config_dir = kwargs['default_config_dir'] if\
        'default_config_dir' in kwargs\
        else  os.path.join(os.path.split(os.path.abspath(
        aiida.restapi.__file__))[0], 'common')

    parse_aiida_profile = kwargs['parse_aiida_profile'] if \
        'parse_aiida_profile' in kwargs else False

    # Set up the command-line options
    parser = argparse.ArgumentParser(prog=prog_name,
                                     description='Hook up the AiiDA '
                                                 'RESTful API')

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
        parser.add_argument("-p", "--aiida-profile",
                        help="AiiDA profile to expose through the RESTful API [default: the default AiiDA profile]",
                        dest="aiida_profile",
                        default="default")

    # Two options useful for debugging purposes, but
    # a bit dangerous so not exposed in the help message.
    parser.add_argument("-d", "--debug",
                        action="store_true", dest="debug",
                        help=argparse.SUPPRESS)
    parser.add_argument("-w", "--wsgi-profile",
                        action="store_true", dest="wsgi_profile",
                        help=argparse.SUPPRESS)

    parsed_args = parser.parse_args(args)

    # If the user selects the profiling option, then we need
    # to do a little extra setup
    if parsed_args.wsgi_profile:
        from werkzeug.contrib.profiler import ProfilerMiddleware

        app.config['PROFILE'] = True
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app,
                                          restrictions=[30])

    # Import the right configuration file
    confs = imp.load_source(os.path.join(parsed_args.config_dir, 'config'),
                            os.path.join(parsed_args.config_dir,
                                         'config.py')
                            )

    import aiida.backends.settings as settings

    # set ptofile
    if parse_aiida_profile and parsed_args.aiida_profile is not "default":
        settings.AIIDADB_PROFILE = parsed_args.aiida_profile
    else:
        # Keep the default profile
        pass

    # Set the AiiDA environment, if not already done
    if not is_dbenv_loaded():
        load_dbenv()

    # Config the app
    app.config.update(**confs.APP_CONFIG)

    # Config the serializer used by the app
    if confs.SERIALIZER_CONFIG:
        from aiida.restapi.common.utils import CustomJSONEncoder
        app.json_encoder = CustomJSONEncoder

    # Hook up the app
    app.run(
        debug=parsed_args.debug,
        host=parsed_args.host,
        port=int(parsed_args.port)
    )
