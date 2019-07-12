# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Implementation of RESTful API for materialscloud.org based on flask +
flask_restful module
For the time being the API returns the parsed valid endpoints upon GET request
Author: Snehal P. Waychal and Fernando Gargiulo @ Theos, EPFL
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from flask import Flask, jsonify
from flask_restful import Api
from werkzeug.exceptions import HTTPException


class App(Flask):
    """
    Basic Flask App customized for this REST Api purposes
    """

    def __init__(self, *args, **kwargs):

        # Decide whether or not to catch the internal server exceptions (
        # default is True)
        catch_internal_server = True
        try:
            catch_internal_server = kwargs.pop('catch_internal_server')
        except KeyError:
            pass

        # Basic initialization
        super(App, self).__init__(*args, **kwargs)

        # Error handler
        from aiida.restapi.common.exceptions import RestInputValidationError, \
            RestValidationError, RestFeatureNotAvailable

        if catch_internal_server:

            @self.errorhandler(Exception)
            def error_handler(error):
                # pylint: disable=unused-variable
                """Error handler to return customized error messages from rest api"""

                if isinstance(error, RestValidationError):
                    response = jsonify({'message': str(error)})
                    response.status_code = 400

                elif isinstance(error, RestInputValidationError):
                    response = jsonify({'message': str(error)})
                    response.status_code = 400

                elif isinstance(error, RestFeatureNotAvailable):
                    response = jsonify({'message': str(error)})
                    response.status_code = 501

                # Generic server-side error (not to make the api crash if an
                # unhandled exception is raised. Caution is never enough!!)
                else:
                    response = jsonify(
                        {'message': 'Internal server error. The original '
                         'message was: \"{}\"'.format(error)})
                    response.status_code = 500

                return response

        else:
            pass


class AiidaApi(Api):
    """
    AiiDA customized version of the flask_restful Api class
    """

    def __init__(self, app=None, **kwargs):
        """
        The need to have a special constructor is to include directly the
        addition of resources with the parameters required to initialize the
        resource classes.

        :param kwargs: parameters to be passed to the resources for
          configuration and PREFIX
        """

        from aiida.restapi.resources import ProcessNode, Computer, User, Group, Node, ServerInfo

        self.app = app

        super(AiidaApi, self).__init__(app=app, prefix=kwargs['PREFIX'], catch_all_404s=True)

        self.add_resource(
            ServerInfo,
            "/server/",
            "/server/endpoints/",
            endpoint='server',
            strict_slashes=False,
            resource_class_kwargs=kwargs)

        ## Add resources and endpoints to the api
        self.add_resource(
            Computer,
            # supported urls
            '/computers/',
            '/computers/page/',
            '/computers/page/<int:page>/',
            '/computers/<id>/',
            '/computers/schema/',
            endpoint='computers',
            strict_slashes=False,
            resource_class_kwargs=kwargs)

        self.add_resource(
            Node,
            '/nodes/',
            '/nodes/schema/',
            '/nodes/statistics/',
            '/nodes/page/',
            '/nodes/page/<int:page>/',
            '/nodes/<id>/',
            '/nodes/<id>/io/inputs/',
            '/nodes/<id>/io/inputs/page/',
            '/nodes/<id>/io/inputs/page/<int:page>/',
            '/nodes/<id>/io/outputs/',
            '/nodes/<id>/io/outputs/page/',
            '/nodes/<id>/io/outputs/page/<int:page>/',
            '/nodes/<id>/io/tree/',
            '/nodes/<id>/content/attributes/',
            '/nodes/<id>/content/extras/',
            '/nodes/<id>/content/visualization/',
            '/nodes/<id>/content/download/',
            #'/nodes/<id>/content/comments/',
            endpoint='nodes',
            strict_slashes=False,
            resource_class_kwargs=kwargs)

        self.add_resource(
            ProcessNode,
            '/processnodes/schema/',
            '/processnodes/<id>/io/retrieved_inputs/',
            '/processnodes/<id>/io/retrieved_outputs/',
            #'/processnodes/<id>/reports/',
            endpoint='processnodes',
            strict_slashes=False,
            resource_class_kwargs=kwargs)

        self.add_resource(
            User,
            '/users/',
            '/users/schema/',
            '/users/page/',
            '/users/page/<int:page>/',
            '/users/<id>/',
            endpoint='users',
            strict_slashes=False,
            resource_class_kwargs=kwargs)

        self.add_resource(
            Group,
            '/groups/',
            '/groups/schema/',
            '/groups/page/',
            '/groups/page/<int:page>/',
            '/groups/<id>/',
            endpoint='groups',
            strict_slashes=False,
            resource_class_kwargs=kwargs)

    def handle_error(self, e):
        """
        this method handles the 404 "URL not found" exception and return custom message
        :param e: raised exception
        :return: list of available endpoints
        """

        if isinstance(e, HTTPException):
            if e.code == 404:

                from aiida.restapi.common.utils import list_routes

                response = {}

                response["status"] = "404 Not Found"
                response["message"] = "The requested URL is not found on the server."

                response["available_endpoints"] = list_routes()

                return jsonify(response)

        raise e
