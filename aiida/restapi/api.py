"""
Implementation of RESTful API for materialscloud.org based on flask +
flask_restful module
For the time being the API returns the parsed valid endpoints upon GET request
Author: Snehal P. Waychal and Fernando Gargiulo @ Theos, EPFL
"""

from flask import Flask, jsonify
from flask_restful import Api


# TODo Transform the app into aa class to be instantiated by the runner

class App(Flask):
    """
    Basic Flask App customized for this REST Api purposes
    """

    def __init__(self, *args, **kwargs):

        from aiida.restapi.common.exceptions import RestInputValidationError, \
            RestValidationError

        # Basic initialization
        super(App, self).__init__(*args, **kwargs)

        # Decide whether or not to catch the internal server exceptions (
        # default is True)
        catch_internal_server = True

        if 'catch_internal_server' in kwargs and kwargs[
            'catch_internal_server'] == False:
            catch_internal_server = False

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

        from aiida.restapi.resources import Calculation, Computer, Code, Data, \
            Group, Node, User, StructureData, KpointsData, BandsData

        super(AiidaApi, self).__init__(app=app, prefix=kwargs['PREFIX'])

        ## Add resources to the api
        self.add_resource(Computer,
                          # supported urls
                          '/computers/',
                          '/computers/page/',
                          '/computers/page/<int:page>/',
                          '/computers/<int:pk>/',
                          '/computers/schema/',
                          strict_slashes=False,
                          resource_class_kwargs=kwargs)

        self.add_resource(Node,
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
                          strict_slashes=False,
                          resource_class_kwargs=kwargs)

        self.add_resource(Calculation,
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
                          strict_slashes=False,
                          resource_class_kwargs=kwargs)

        self.add_resource(Data,
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
                          '/data/<int:pk>/content/visualization/',
                          strict_slashes=False,
                          resource_class_kwargs=kwargs)

        self.add_resource(Code,
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
                          '/codes/<int:pk>/content/visualization/',
                          strict_slashes=False,
                          resource_class_kwargs=kwargs)

        self.add_resource(StructureData,
                          '/structures/',
                          '/structures/schema/',
                          '/structures/statistics/',
                          '/structures/page/',
                          '/structures/page/<int:page>',
                          '/structures/<int:pk>/',
                          '/structures/<int:pk>/io/inputs/',
                          '/structures/<int:pk>/io/inputs/page/',
                          '/structures/<int:pk>/io/inputs/page/<int:page>/',
                          '/structures/<int:pk>/io/outputs/',
                          '/structures/<int:pk>/io/outputs/page/',
                          '/structures/<int:pk>/io/outputs/page/<int:page>/',
                          '/structures/<int:pk>/io/tree/',
                          '/structures/<int:pk>/content/attributes/',
                          '/structures/<int:pk>/content/extras/',
                          '/structures/<int:pk>/content/visualization/',
                          strict_slashes=False,
                          resource_class_kwargs=kwargs
                          )

        self.add_resource(KpointsData,
                          '/kpoints/',
                          '/kpoints/schema/',
                          '/kpoints/statistics/',
                          '/kpoints/page/',
                          '/kpoints/page/<int:page>',
                          '/kpoints/<int:pk>/',
                          '/kpoints/<int:pk>/io/inputs/',
                          '/kpoints/<int:pk>/io/inputs/page/',
                          '/kpoints/<int:pk>/io/inputs/page/<int:page>/',
                          '/kpoints/<int:pk>/io/outputs/',
                          '/kpoints/<int:pk>/io/outputs/page/',
                          '/kpoints/<int:pk>/io/outputs/page/<int:page>/',
                          '/kpoints/<int:pk>/io/tree/',
                          '/kpoints/<int:pk>/content/attributes/',
                          '/kpoints/<int:pk>/content/extras/',
                          '/kpoints/<int:pk>/content/visualization/',
                          strict_slashes=False,
                          resource_class_kwargs=kwargs
                          )

        self.add_resource(BandsData,
                          '/bands/',
                          '/bands/schema/',
                          '/bands/statistics/',
                          '/bands/page/',
                          '/bands/page/<int:page>',
                          '/bands/<int:pk>/',
                          '/bands/<int:pk>/io/inputs/',
                          '/bands/<int:pk>/io/inputs/page/',
                          '/bands/<int:pk>/io/inputs/page/<int:page>/',
                          '/bands/<int:pk>/io/outputs/',
                          '/bands/<int:pk>/io/outputs/page/',
                          '/bands/<int:pk>/io/outputs/page/<int:page>/',
                          '/bands/<int:pk>/io/tree/',
                          '/bands/<int:pk>/content/attributes/',
                          '/bands/<int:pk>/content/extras/',
                          '/bands/<int:pk>/content/visualization/',
                          strict_slashes=False,
                          resource_class_kwargs=kwargs
                          )

        self.add_resource(User,
                          '/users/',
                          '/users/schema/',
                          '/users/statistics/',
                          '/users/page/',
                          '/users/page/<int:page>/',
                          '/users/<int:pk>/',
                          strict_slashes=False,
                          resource_class_kwargs=kwargs)

        self.add_resource(Group,
                          '/groups/',
                          '/groups/schema/',
                          '/groups/statistics/',
                          '/groups/page/',
                          '/groups/page/<int:page>/',
                          '/groups/<int:pk>/',
                          strict_slashes=False,
                          resource_class_kwargs=kwargs)
