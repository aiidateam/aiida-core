#!/usr/bin/env python

"""
Implementation of RESTful API for materialscloud.org based on flask + flask_restful module
For the time being the API returns the parsed valid endpoints upon GET request
Author: Snehal P. Waychal and Fernando Gargiulo @ Theos, EPFL
"""

from flask import Flask, jsonify
from flask_restful import Api
from flask_cors import CORS
from aiida.restapi.common.exceptions import RestInputValidationError,\
    RestValidationError
from aiida.restapi.resources import Calculation, Computer, Code, Data, Group, \
    Node, User
import aiida.restapi.common.config as conf
from aiida.restapi.common.flaskrun import flaskrun

## Initiate an app with its api
app = Flask(__name__)
api = Api(app, prefix=conf.PREFIX)
cors = CORS(app, resources={r"/api/v2/*": {"origins": "*"}})

## Error handling for error raised for invalid urls (not for non existing
# resources!)
@app.errorhandler(Exception)
def error_handler(error):
    if isinstance(error, RestValidationError):
        response = jsonify({'message': error.message})
        response.status_code = 400
    elif isinstance(error, RestInputValidationError):
        response = jsonify({'message': error.message})
        response.status_code = 400
    # Generic server-side error (not to make the api crash if an unhandled
    # exception is raised. Caution is never enough!!)
    else:
        response = jsonify({'message': 'Internal server error. The original '
                                       'message was: \"{}\"'.format(
            error.message)})
        response.status_code = 500

    return response


## Add resources to the api
api.add_resource(Computer,
                 # supported urls
                 '/computers/',
                 '/computers/schema/',
                 '/computers/statistics/',
                 '/computers/page/',
                 '/computers/page/<int:page>/',
                 '/computers/<int:pk>/',
                 '/computers/schema/',
                 strict_slashes=False)

api.add_resource(Node,
                 '/nodes/',
                 '/nodes/schema/',
                 '/nodes/statistics/',
                 '/nodes/page/',
                 '/nodes/page/<int:page>/',
                 '/nodes/<int:pk>/',
                 '/nodes/<int:pk>/io/inputs/',
                 '/nodes/<int:pk>/io/inputs/page/',
                 '/nodes/<int:pk>/io/inputs/page/<int:page>/',
                 '/nodes/<int:pk>/io/outputs/',
                 '/nodes/<int:pk>/io/outputs/page/',
                 '/nodes/<int:pk>/io/outputs/page/<int:page>/',
                 '/nodes/<int:pk>/io/tree/',
                 '/nodes/<int:pk>/content/attributes/',
                 '/nodes/<int:pk>/content/extras/',
                 '/nodes/statistics/',
                 strict_slashes=False)

api.add_resource(Calculation,
                 '/calculations/',
                 '/calculations/schema/',
                 '/calculations/statistics/',
                 '/calculations/page/',
                 '/calculations/page/<int:page>/',
                 '/calculations/<int:pk>/',
                 '/calculations/<int:pk>/io/inputs/',
                 '/calculations/<int:pk>/io/inputs/page/',
                 '/calculations/<int:pk>/io/inputs/page/<int:page>/',
                 '/calculations/<int:pk>/io/outputs/',
                 '/calculations/<int:pk>/io/outputs/page/',
                 '/calculations/<int:pk>/io/outputs/page/<int:page>/',
                 '/calculations/<int:pk>/io/tree/',
                 '/calculations/<int:pk>/content/attributes/',
                 '/calculations/<int:pk>/content/extras/',
                 '/calculations/schema/',
                 '/calculations/statistics/',
                 strict_slashes=False)

api.add_resource(Data,
                 '/data/',
                 '/data/schema/',
                 '/data/statistics/',
                 '/data/page/',
                 '/data/page/<int:page>',
                 '/data/<int:pk>/',
                 '/data/<int:pk>/io/inputs/',
                 '/data/<int:pk>/io/inputs/page/',
                 '/data/<int:pk>/io/inputs/page/<int:page>/',
                 '/data/<int:pk>/io/outputs/',
                 '/data/<int:pk>/io/outputs/page/',
                 '/data/<int:pk>/io/outputs/page/<int:page>/',
                 '/data/<int:pk>/io/tree/',
                 '/data/<int:pk>/content/attributes/',
                 '/data/<int:pk>/content/extras/',
                 '/data/schema/',
                 '/data/statistics/',
                 strict_slashes=False)

api.add_resource(Code,
                 '/codes/',
                 '/codes/schema/',
                 '/codes/statistics/',
                 '/codes/page/',
                 '/codes/page/<int:page>/',
                 '/codes/<int:pk>/',
                 '/codes/<int:pk>/io/inputs/',
                 '/codes/<int:pk>/io/inputs/page/',
                 '/codes/<int:pk>/io/inputs/page/<int:page>/',
                 '/codes/<int:pk>/io/outputs/',
                 '/codes/<int:pk>/io/outputs/page/',
                 '/codes/<int:pk>/io/outputs/page/<int:page>/',
                 '/codes/<int:pk>/io/tree/',
                 '/codes/<int:pk>/content/attributes/',
                 '/codes/<int:pk>/content/extras/',
                 '/codes/schema/',
                 '/codes/statistics/',
                 strict_slashes=False)

api.add_resource(User,
                 '/users/',
                 '/users/schema/',
                 '/users/statistics/',
                 '/users/page/',
                 '/users/page/<int:page>/',
                 '/users/<int:pk>/',
                 strict_slashes=False)

api.add_resource(Group,
                 '/groups/',
                 '/groups/schema/',
                 '/groups/statistics/',
                 '/groups/page/',
                 '/groups/page/<int:page>/',
                 '/groups/<int:pk>/',
                 strict_slashes=False)


# Standard boilerplate to run the app
if __name__ == '__main__':

    #I run the app via a wrapper that accepts arguments such as host and port
    #e.g. python api.py --host=127.0.0.2 --port=6000 --config-dir=~/.restapi
    # Default address is 127.0.01:5000, default config directory is
    # <aiida_path>/aiida/restapi/common

    #Start the app by sliding the argvs to flaskrun, choose to take as an
    # argument also whether to parse the aiida profile or not (in verdi
    # restapi this would not be the case)
    import sys
    flaskrun(app, *sys.argv[1:], parse_aiida_profile=True)

