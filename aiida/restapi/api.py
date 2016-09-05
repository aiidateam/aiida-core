#!/usr/bin/env python

"""
Implementation of RESTful API for materialscloud.org based on flask + flask_restful module
For the time being the API returns the parsed valid endpoints upon GET request
Author: Snehal P. Waychal and Fernando Gargiulo @ Theos, EPFL
"""

from flask import Flask, jsonify
from flask_restful import Api
from flask_cors import CORS, cross_origin
from aiida.restapi.common.exceptions import RestInputValidationError,\
    RestValidationError
from aiida.restapi.resources import Calculation, Computer, Code, Data, Group, \
    Node, User
from aiida.restapi.common.config import PREFIX, APP_CONFIG
from aiida.restapi.common.flaskrun import flaskrun
from flask.ext.sqlalchemy import SQLAlchemy


## Initiate an app with its api
app = Flask(__name__)
api = Api(app, prefix=PREFIX)

cors = CORS(app, resources={r"/api/v2/*": {"origins": "*"}})

# database
from aiida.restapi.database.initdb import mcloud_db_session
from aiida.restapi.database.resources import (McloudUserResource,
    McloudUsersResource, McloudTokenResource )


## Error handling for error raised for invalid urls (not for non existing
# resources!)
@app.errorhandler(Exception)
def error_handler(error):
    if isinstance(error, RestValidationError):
        response = jsonify({'message': error.message})
        response.status_code = 400
        return response
    elif isinstance(error, RestInputValidationError):
        response = jsonify({'message': error.message})
        response.status_code = 400
        return response
    # Generic server-side error (not to make the api crash if an unhandled
    # exception is raised. Caution is never enough!!)
    else:
        response = jsonify({'message': 'Internal server error'})
        response.status_code = 500
        return response


## Add resources to the api
api.add_resource(Computer,
                 # supported urls
                 '/computers/',
                 '/computers/page/',
                 '/computers/page/<int:page>/',
                 '/computers/<int:pk>/',
                 '/computers/schema/',
                 strict_slashes=False)

api.add_resource(Node,
                 '/nodes/',
                 '/nodes/page/',
                 '/nodes/page/<int:page>/',
                 '/nodes/<int:pk>/',
                 '/nodes/<int:pk>/io/inputs/',
                 '/nodes/<int:pk>/io/inputs/page/',
                 '/nodes/<int:pk>/io/inputs/page/<int:page>/',
                 '/nodes/<int:pk>/io/outputs/',
                 '/nodes/<int:pk>/io/outputs/page/',
                 '/nodes/<int:pk>/io/outputs/page/<int:page>/',
                 '/nodes/<int:pk>/content/attributes/',
                 '/nodes/<int:pk>/content/extras/',
                 strict_slashes=False)

api.add_resource(Calculation,
                 '/calculations/',
                 '/calculations/page/',
                 '/calculations/page/<int:page>/',
                 '/calculations/<int:pk>/',
                 '/calculations/<int:pk>/io/inputs/',
                 '/calculations/<int:pk>/io/inputs/page/',
                 '/calculations/<int:pk>/io/inputs/page/<int:page>/',
                 '/calculations/<int:pk>/io/outputs/',
                 '/calculations/<int:pk>/io/outputs/page/',
                 '/calculations/<int:pk>/io/outputs/page/<int:page>/',
                 '/calculations/<int:pk>/content/attributes/',
                 '/calculations/<int:pk>/content/extras/',
                 '/calculations/schema/',
                 strict_slashes=False)

api.add_resource(Data,
                 '/data/',
                 '/data/page/',
                 '/data/page/<int:page>',
                 '/data/<int:pk>/',
                 '/data/<int:pk>/io/inputs/',
                 '/data/<int:pk>/io/inputs/page/',
                 '/data/<int:pk>/io/inputs/page/<int:page>/',
                 '/data/<int:pk>/io/outputs/',
                 '/data/<int:pk>/io/outputs/page/',
                 '/data/<int:pk>/io/outputs/page/<int:page>/',
                 '/data/<int:pk>/content/attributes/',
                 '/data/<int:pk>/content/extras/',
                 '/data/schema/',
                 strict_slashes=False)

api.add_resource(Code,
                 '/codes/',
                 '/codes/page/',
                 '/codes/page/<int:page>/',
                 '/codes/<int:pk>/',
                 '/codes/<int:pk>/io/inputs/',
                 '/codes/<int:pk>/io/inputs/page/',
                 '/codes/<int:pk>/io/inputs/page/<int:page>/',
                 '/codes/<int:pk>/io/outputs/',
                 '/codes/<int:pk>/io/outputs/page/',
                 '/codes/<int:pk>/io/outputs/page/<int:page>/',
                 '/codes/<int:pk>/content/attributes/',
                 '/codes/<int:pk>/content/extras/',
                 '/codes/schema/',
                 strict_slashes=False)

api.add_resource(User,
                 '/users/',
                 '/users/page/',
                 '/users/page/<int:page>/',
                 '/users/<int:pk>/',
                 strict_slashes=False)

api.add_resource(Group,
                 '/groups/',
                 '/groups/page/',
                 '/groups/page/<int:page>/',
                 '/groups/<int:pk>/',
                 strict_slashes=False)

#mcloud user resource mapping
api.add_resource(McloudUsersResource,
                 '/mcloud/users/',
                 strict_slashes=False)

api.add_resource(McloudUserResource,
                 '/mcloud/user/',
                 '/mcloud/user/<int:pk>/',
                 strict_slashes=False)

api.add_resource(McloudTokenResource,
                 '/mcloud/token/',
                 strict_slashes=False)

@app.teardown_appcontext
def shutdown_session(exception=None):
    mcloud_db_session.remove()

from aiida.restapi.database.initdb import setup_database
setup_database()

# Standard boilerplate to run the app
if __name__ == '__main__':
    #Config the app
    app.config.update(**APP_CONFIG)


    #I run the app via a wrapper that accepts arguments such as host and port
    #e.g. python api.py --host=127.0.0.2 --port=6000
    # Default address is 127.0.01:5000
    #Warm up the engine - brum brum - and staaarrrt!!
    flaskrun(app)
