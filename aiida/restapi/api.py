"""
Implementation of RESTful API for materialscloud.org based on flask + flask_restful module
For the time being the API returns the parsed valid endpoints upon GET request
Author: Snehal P. Waychal and Fernando Gargiulo @ Theos, EPFL
"""
from flask import Flask, jsonify
from flask_restful import Api
from aiida.restapi.common.exceptions import RestInputValidationError,\
    RestValidationError
from aiida.restapi.resources import Calculation, Computer, Code, Data, Group, \
    Node, User
from aiida.restapi.common.config import PREFIX, APP_CONFIG

## Initiate an app with its api
app = Flask(__name__)
api = Api(app, prefix=PREFIX)


## Errors handling for  error raised by invalid uri
@app.errorhandler(RestValidationError)
def validation_error_handler(error):
    response = jsonify({'message': error.message})
    response.status_code = 400
    return response

@app.errorhandler(RestInputValidationError)
def validation_error_handler(error):
    response = jsonify({'message': error.message})
    response.status_code = 400
    return response

## Todo: add api configutations, such as prefix '/api/v1 ...'
## Add resources to the api
api.add_resource(Computer,
                 # supported urls
                 '/computers/',
                 '/computers/page/',
                 '/computers/page/<int:page>/',
                 '/computers/<int:pk>/',
                 strict_slashes=False)

api.add_resource(Node,
                 # supported urls
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
                 # supported urls
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
                 strict_slashes=False)

api.add_resource(Data,
                 # supported urls
                 '/datas/',
                 '/datas/page/',
                 '/datas/page/<int:page>',
                 '/datas/<int:pk>/',
                 '/datas/<int:pk>/io/inputs/',
                 '/datas/<int:pk>/io/inputs/page/',
                 '/datas/<int:pk>/io/inputs/page/<int:page>/',
                 '/datas/<int:pk>/io/outputs/',
                 '/datas/<int:pk>/io/outputs/page/',
                 '/datas/<int:pk>/io/outputs/page/<int:page>/',
                 '/datas/<int:pk>/content/attributes/',
                 '/datas/<int:pk>/content/extras/',
                 strict_slashes=False)

api.add_resource(Code,
                 # supported urls
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
                 strict_slashes=False)

api.add_resource(User,
                 # supported urls
                 '/users/',
                 '/users/page/',
                 '/users/page/<int:page>/',
                 '/users/<int:pk>/',
                 strict_slashes=False)

api.add_resource(Group,
                 # supported urls
                 '/groups/',
                 '/groups/page/',
                 '/groups/page/<int:page>/',
                 '/groups/<int:pk>/',
                 strict_slashes=False)


# Standard boilerplate to run the app
if __name__ == '__main__':
    #Config the app
    app.config.update(**APP_CONFIG)
    #Warm up the engine - brum brum - and run it!!
    app.run()