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
Implementation of RESTful API for materialscloud.org based on flask +
flask_restful module
For the time being the API returns the parsed valid endpoints upon GET request
Author: Snehal P. Waychal and Fernando Gargiulo @ Theos, EPFL
"""

from flask import Flask, jsonify
from flask_restful import Api

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
            RestValidationError

        if catch_internal_server:

            @self.errorhandler(Exception)
            def error_handler(error):

                if isinstance(error, RestValidationError):
                    response = jsonify({'message': error.message})
                    response.status_code = 400

                elif isinstance(error, RestInputValidationError):
                    response = jsonify({'message': error.message})
                    response.status_code = 400

                # Generic server-side error (not to make the api crash if an
                # unhandled exception is raised. Caution is never enough!!)
                else:
                    response = jsonify(
                        {
                            'message': 'Internal server error. The original '
                                       'message was: \"{}\"'.format(
                                error.message)
                        }
                    )
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

        Args:
            **kwargs: parameters to be passed to the resources for
            configuration and PREFIX
        """

        from aiida.restapi.resources import Calculation, Computer, User, Code, Data, \
            Group, Node, StructureData, KpointsData, BandsData

        super(AiidaApi, self).__init__(app=app, prefix=kwargs['PREFIX'])

        ## Add resources and endpoints to the api
        self.add_resource(Computer,
                          # supported urls
                          '/computers/',
                          '/computers/page/',
                          '/computers/page/<int:page>/',
                          '/computers/<id>/',
                          '/computers/schema/',
                          strict_slashes=False,
                          resource_class_kwargs=kwargs)

        self.add_resource(Node,
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
                          strict_slashes=False,
                          resource_class_kwargs=kwargs)

        self.add_resource(Calculation,
                          '/calculations/',
                          '/calculations/schema/',
                          '/calculations/page/',
                          '/calculations/page/<int:page>/',
                          '/calculations/<id>/',
                          '/calculations/<id>/io/inputs/',
                          '/calculations/<id>/io/inputs/page/',
                          '/calculations/<id>/io/inputs/page/<int:page>/',
                          '/calculations/<id>/io/outputs/',
                          '/calculations/<id>/io/outputs/page/',
                          '/calculations/<id>/io/outputs/page/<int:page>/',
                          '/calculations/<id>/io/tree/',
                          '/calculations/<id>/content/attributes/',
                          '/calculations/<id>/content/extras/',
                          strict_slashes=False,
                          resource_class_kwargs=kwargs)

        self.add_resource(Data,
                          '/data/',
                          '/data/schema/',
                          '/data/page/',
                          '/data/page/<int:page>',
                          '/data/<id>/',
                          '/data/<id>/io/inputs/',
                          '/data/<id>/io/inputs/page/',
                          '/data/<id>/io/inputs/page/<int:page>/',
                          '/data/<id>/io/outputs/',
                          '/data/<id>/io/outputs/page/',
                          '/data/<id>/io/outputs/page/<int:page>/',
                          '/data/<id>/io/tree/',
                          '/data/<id>/content/attributes/',
                          '/data/<id>/content/extras/',
                          '/data/<id>/content/visualization/',
                          strict_slashes=False,
                          resource_class_kwargs=kwargs)

        self.add_resource(Code,
                          '/codes/',
                          '/codes/schema/',
                          '/codes/page/',
                          '/codes/page/<int:page>/',
                          '/codes/<id>/',
                          '/codes/<id>/io/inputs/',
                          '/codes/<id>/io/inputs/page/',
                          '/codes/<id>/io/inputs/page/<int:page>/',
                          '/codes/<id>/io/outputs/',
                          '/codes/<id>/io/outputs/page/',
                          '/codes/<id>/io/outputs/page/<int:page>/',
                          '/codes/<id>/io/tree/',
                          '/codes/<id>/content/attributes/',
                          '/codes/<id>/content/extras/',
                          '/codes/<id>/content/visualization/',
                          strict_slashes=False,
                          resource_class_kwargs=kwargs)

        self.add_resource(StructureData,
                          '/structures/',
                          '/structures/schema/',
                          '/structures/page/',
                          '/structures/page/<int:page>',
                          '/structures/<id>/',
                          '/structures/<id>/io/inputs/',
                          '/structures/<id>/io/inputs/page/',
                          '/structures/<id>/io/inputs/page/<int:page>/',
                          '/structures/<id>/io/outputs/',
                          '/structures/<id>/io/outputs/page/',
                          '/structures/<id>/io/outputs/page/<int:page>/',
                          '/structures/<id>/io/tree/',
                          '/structures/<id>/content/attributes/',
                          '/structures/<id>/content/extras/',
                          '/structures/<id>/content/visualization/',
                          strict_slashes=False,
                          resource_class_kwargs=kwargs
                          )

        self.add_resource(KpointsData,
                          '/kpoints/',
                          '/kpoints/schema/',
                          '/kpoints/page/',
                          '/kpoints/page/<int:page>',
                          '/kpoints/<id>/',
                          '/kpoints/<id>/io/inputs/',
                          '/kpoints/<id>/io/inputs/page/',
                          '/kpoints/<id>/io/inputs/page/<int:page>/',
                          '/kpoints/<id>/io/outputs/',
                          '/kpoints/<id>/io/outputs/page/',
                          '/kpoints/<id>/io/outputs/page/<int:page>/',
                          '/kpoints/<id>/io/tree/',
                          '/kpoints/<id>/content/attributes/',
                          '/kpoints/<id>/content/extras/',
                          '/kpoints/<id>/content/visualization/',
                          strict_slashes=False,
                          resource_class_kwargs=kwargs
                          )

        self.add_resource(BandsData,
                          '/bands/',
                          '/bands/schema/',
                          '/bands/page/',
                          '/bands/page/<int:page>',
                          '/bands/<id>/',
                          '/bands/<id>/io/inputs/',
                          '/bands/<id>/io/inputs/page/',
                          '/bands/<id>/io/inputs/page/<int:page>/',
                          '/bands/<id>/io/outputs/',
                          '/bands/<id>/io/outputs/page/',
                          '/bands/<id>/io/outputs/page/<int:page>/',
                          '/bands/<id>/io/tree/',
                          '/bands/<id>/content/attributes/',
                          '/bands/<id>/content/extras/',
                          '/bands/<id>/content/visualization/',
                          strict_slashes=False,
                          resource_class_kwargs=kwargs
                          )

        self.add_resource(User,
                          '/users/',
                          '/users/schema/',
                          '/users/page/',
                          '/users/page/<int:page>/',
                          '/users/<id>/',
                          strict_slashes=False,
                          resource_class_kwargs=kwargs)

        self.add_resource(Group,
                          '/groups/',
                          '/groups/schema/',
                          '/groups/page/',
                          '/groups/page/<int:page>/',
                          '/groups/<id>/',
                          strict_slashes=False,
                          resource_class_kwargs=kwargs)
