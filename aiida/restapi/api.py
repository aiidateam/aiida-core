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
Implementation of RESTful API for AiiDA based on flask and flask_restful.

Author: Snehal P. Waychal and Fernando Gargiulo @ Theos, EPFL
"""

from flask import Flask, jsonify
from flask_restful import Api
from werkzeug.exceptions import HTTPException


class App(Flask):
    """
    Basic Flask App customized for this REST Api purposes
    """

    def __init__(self, *args, **kwargs):

        # Decide whether or not to catch the internal server exceptions (default is True)
        catch_internal_server = kwargs.pop('catch_internal_server', True)

        # Basic initialization
        super().__init__(*args, **kwargs)

        # Error handler
        from aiida.restapi.common.exceptions import (
            RestFeatureNotAvailable,
            RestInputValidationError,
            RestValidationError,
        )

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
                    response.status_code = 404

                elif isinstance(error, RestFeatureNotAvailable):
                    response = jsonify({'message': str(error)})
                    response.status_code = 501

                elif isinstance(error, HTTPException) and error.code == 404:
                    from aiida.restapi.common.utils import list_routes

                    response = jsonify({
                        'message': 'The requested URL is not found on the server.',
                        'available_endpoints': list_routes()
                    })
                    response.status_code = 404

                # Generic server-side error (not to make the api crash if an
                # unhandled exception is raised. Caution is never enough!!)
                else:
                    response = jsonify({'message': str(error)})
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

        from aiida.restapi.common.config import CLI_DEFAULTS
        from aiida.restapi.resources import (
            CalcJobNode,
            Computer,
            Group,
            Node,
            ProcessNode,
            QueryBuilder,
            ServerInfo,
            User,
        )

        self.app = app

        super().__init__(app=app, prefix=kwargs['PREFIX'], catch_all_404s=True)

        posting = kwargs.pop('posting', CLI_DEFAULTS['POSTING'])

        self.add_resource(
            ServerInfo,
            '/',
            '/server/',
            '/server/endpoints/',
            endpoint='server',
            strict_slashes=False,
            resource_class_kwargs=kwargs
        )

        if posting:
            self.add_resource(
                QueryBuilder,
                '/querybuilder/',
                endpoint='querybuilder',
                strict_slashes=False,
                resource_class_kwargs=kwargs,
            )

        ## Add resources and endpoints to the api
        self.add_resource(
            Computer,
            # supported urls
            '/computers/',
            '/computers/page/',
            '/computers/page/<int:page>/',
            '/computers/<id>/',
            '/computers/projectable_properties/',
            endpoint='computers',
            strict_slashes=False,
            resource_class_kwargs=kwargs
        )

        self.add_resource(
            Node,
            '/nodes/',
            '/nodes/projectable_properties/',
            '/nodes/statistics/',
            '/nodes/full_types/',
            '/nodes/full_types_count/',
            '/nodes/download_formats/',
            '/nodes/page/',
            '/nodes/page/<int:page>/',
            '/nodes/<id>/',
            '/nodes/<id>/links/incoming/',
            '/nodes/<id>/links/incoming/page/',
            '/nodes/<id>/links/incoming/page/<int:page>/',
            '/nodes/<id>/links/outgoing/',
            '/nodes/<id>/links/outgoing/page/',
            '/nodes/<id>/links/outgoing/page/<int:page>/',
            '/nodes/<id>/links/tree/',
            '/nodes/<id>/contents/attributes/',
            '/nodes/<id>/contents/extras/',
            '/nodes/<id>/contents/derived_properties/',
            '/nodes/<id>/contents/comments/',
            '/nodes/<id>/repo/list/',
            '/nodes/<id>/repo/contents/',
            '/nodes/<id>/download/',
            endpoint='nodes',
            strict_slashes=False,
            resource_class_kwargs=kwargs
        )

        self.add_resource(
            ProcessNode,
            '/processes/projectable_properties/',
            '/processes/<id>/report/',
            endpoint='processes',
            strict_slashes=False,
            resource_class_kwargs=kwargs
        )

        self.add_resource(
            CalcJobNode,
            '/calcjobs/<id>/input_files/',
            '/calcjobs/<id>/output_files/',
            endpoint='calcjobs',
            strict_slashes=False,
            resource_class_kwargs=kwargs
        )

        self.add_resource(
            User,
            '/users/',
            '/users/projectable_properties/',
            '/users/page/',
            '/users/page/<int:page>/',
            '/users/<id>/',
            endpoint='users',
            strict_slashes=False,
            resource_class_kwargs=kwargs
        )

        self.add_resource(
            Group,
            '/groups/',
            '/groups/projectable_properties/',
            '/groups/page/',
            '/groups/page/<int:page>/',
            '/groups/<id>/',
            endpoint='groups',
            strict_slashes=False,
            resource_class_kwargs=kwargs
        )

    def handle_error(self, e):
        """
        this method handles the 404 "URL not found" exception and return custom message
        :param e: raised exception
        :return: list of available endpoints
        """
        raise e
