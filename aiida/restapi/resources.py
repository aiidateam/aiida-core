# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
""" Resources for REST API """
from urllib.parse import unquote

from flask import make_response, request
from flask_restful import Resource

from aiida.common.lang import classproperty
from aiida.manage import get_config_option, load_profile
from aiida.restapi.common.exceptions import RestInputValidationError
from aiida.restapi.common.utils import Utils, close_thread_connection
from aiida.restapi.translator.nodes.node import NodeTranslator


class ServerInfo(Resource):
    """Endpoint to return general server info"""

    def __init__(self, **kwargs):
        # Configure utils
        utils_conf_keys = ('PREFIX', 'PERPAGE_DEFAULT', 'LIMIT_DEFAULT')
        self.utils_confs = {k: kwargs[k] for k in utils_conf_keys if k in kwargs}
        self.utils = Utils(**self.utils_confs)

    def get(self):
        """
        It returns the general info about the REST API
        :return: returns current AiiDA version defined in aiida/__init__.py
        """
        path = unquote(request.path)
        url = unquote(request.url)
        url_root = unquote(request.url_root)
        query_string = unquote(request.query_string.decode('utf-8'))
        subpath = self.utils.strip_api_prefix(path).strip('/')
        pathlist = self.utils.split_path(subpath)

        if subpath == '':
            resource_type = 'endpoints'
        elif len(pathlist) > 1:
            resource_type = pathlist.pop(1)
        else:
            resource_type = 'info'

        response = {}

        from aiida import __version__
        from aiida.restapi.common.config import API_CONFIG

        if resource_type == 'info':
            response = {}

            # Add Rest API version
            api_version = API_CONFIG['VERSION'].split('.')
            response['API_major_version'] = api_version[0]
            response['API_minor_version'] = api_version[1]
            response['API_revision_version'] = api_version[2]

            # Add Rest API prefix
            response['API_prefix'] = API_CONFIG['PREFIX']

            # Add AiiDA version
            response['AiiDA_version'] = __version__

        elif resource_type == 'endpoints':

            from aiida.restapi.common.utils import list_routes
            response['available_endpoints'] = list_routes()

        headers = self.utils.build_headers(url=request.url, total_count=1)

        ## Build response and return it
        data = dict(
            method=request.method,
            url=url,
            url_root=url_root,
            path=path,
            query_string=query_string,
            resource_type='Info',
            data=response
        )
        return self.utils.build_response(status=200, headers=headers, data=data)


class BaseResource(Resource):
    # pylint: disable=fixme
    """
    Each derived class will instantiate a different type of translator.
    This is the only difference in the classes.
    """
    from aiida.restapi.translator.base import BaseTranslator

    _translator_class = BaseTranslator
    _parse_pk_uuid = None  # Flag to tell the path parser whether to expect a pk or a uuid pattern

    method_decorators = [close_thread_connection]  # Close the thread's storage connection after any method call

    ## TODO add the caching support. I cache total count, results, and possibly

    def __init__(self, profile, **kwargs):
        """Construct the resource."""
        self.trans = self._translator_class(**kwargs)
        self.profile = profile

        # Configure utils
        utils_conf_keys = ('PREFIX', 'PERPAGE_DEFAULT', 'LIMIT_DEFAULT')
        self.utils_confs = {k: kwargs[k] for k in utils_conf_keys if k in kwargs}
        self.utils = Utils(**self.utils_confs)

        # HTTP Request method decorators
        if 'get_decorators' in kwargs and isinstance(kwargs['get_decorators'], (tuple, list, set)):
            self.method_decorators = {'get': list(kwargs['get_decorators'])}

    @staticmethod
    def unquote_request():
        """Unquote and return various parts of the request.

        :returns: Tuple of the request path, url, url root and query string.
        """
        path = unquote(request.path)
        url = unquote(request.url)
        url_root = unquote(request.url_root)
        query_string = unquote(request.query_string.decode('utf-8'))
        return path, url, url_root, query_string

    def parse_path(self, path):
        """Parse the request path."""
        return self.utils.parse_path(path, parse_pk_uuid=self.parse_pk_uuid)

    def parse_query_string(self, query_string):
        """Parse the request query string."""
        return self.utils.parse_query_string(query_string)

    @classproperty
    def parse_pk_uuid(cls):  # pylint: disable=no-self-argument
        return cls._parse_pk_uuid

    def _load_and_verify(self, node_id=None):
        """Load node and verify it is of the required type"""
        from aiida.orm import load_node
        node = load_node(node_id)

        if not isinstance(node, self.trans._aiida_class):  # pylint: disable=protected-access,isinstance-second-argument-not-valid-type
            raise RestInputValidationError(
                f'node {node_id} is not of the required type {self.trans._aiida_class}'  # pylint: disable=protected-access
            )

        return node

    def load_profile(self, profile=None):
        """Load the required profile.

        This will load the profile specified by the ``profile`` keyword in the query parameters, and if not specified it
        will default to the profile defined in the constructor.
        """
        profile_switching_enabled = get_config_option('rest_api.profile_switching')

        if profile is not None and not profile_switching_enabled:
            raise RestInputValidationError('specifying an explicit profile is not enabled for this REST API.')

        load_profile(profile or self.profile, allow_switch=True)

    def get(self, id=None, page=None):  # pylint: disable=redefined-builtin,invalid-name,unused-argument
        # pylint: disable=too-many-locals
        """
        Get method for the resource
        :param id: node identifier
        :param page: page no, used for pagination
        :return: http response
        """
        path, url, url_root, query_string = self.unquote_request()
        resource_type, page, node_id, query_type = self.parse_path(path)
        parameters = self.parse_query_string(query_string)
        limit = parameters[0]
        offset = parameters[1]
        perpage = parameters[2]
        orderby = parameters[3]
        filters = parameters[4]
        profile = parameters[-1]

        try:
            self.load_profile(profile)
        except RestInputValidationError as exception:
            return self.utils.build_response(
                status=400,
                headers=self.utils.build_headers(url=request.url, total_count=0),
                data={
                    'method': request.method,
                    'url': url,
                    'url_root': url_root,
                    'path': path,
                    'query_string': query_string,
                    'resource_type': self.__class__.__name__,
                    'data': {
                        'message': str(exception)
                    },
                }
            )

        ## Validate request
        self.utils.validate_request(
            limit=limit,
            offset=offset,
            perpage=perpage,
            page=page,
            query_type=query_type,
            is_querystring_defined=(bool(query_string))
        )

        ## Treat the projectable_properties case which does not imply access to the DataBase
        if query_type == 'projectable_properties':

            ## Retrieve the projectable properties
            projectable_properties, ordering = self.trans.get_projectable_properties()
            results = dict(fields=projectable_properties, ordering=ordering)
            ## Build response and return it
            headers = self.utils.build_headers(url=request.url, total_count=1)

        else:

            ## Set the query, and initialize qb object
            self.trans.set_query(filters=filters, orders=orderby, node_id=node_id)

            ## Count results
            total_count = self.trans.get_total_count()

            ## Pagination (if required)
            if page is not None:
                (limit, offset, rel_pages) = self.utils.paginate(page, perpage, total_count)
                self.trans.set_limit_offset(limit=limit, offset=offset)
                headers = self.utils.build_headers(rel_pages=rel_pages, url=request.url, total_count=total_count)
            else:
                self.trans.set_limit_offset(limit=limit, offset=offset)
                headers = self.utils.build_headers(url=request.url, total_count=total_count)

            ## Retrieve results
            results = self.trans.get_results()

        ## Build response and return it
        data = dict(
            method=request.method,
            url=url,
            url_root=url_root,
            path=request.path,
            id=node_id,
            query_string=query_string,
            resource_type=resource_type,
            data=results
        )

        return self.utils.build_response(status=200, headers=headers, data=data)


class QueryBuilder(BaseResource):
    """
    Representation of a QueryBuilder REST API resource (instantiated with a serialised QueryBuilder instance).

    It supports POST requests taking in JSON :py:func:`~aiida.orm.querybuilder.QueryBuilder.as_dict`
    objects and returning the :py:class:`~aiida.orm.querybuilder.QueryBuilder` result accordingly.
    """
    _translator_class = NodeTranslator

    GET_MESSAGE = (
        'Method Not Allowed. Use HTTP POST requests to use the AiiDA QueryBuilder. '
        'POST JSON data, which MUST be a valid QueryBuilder.as_dict() dictionary as a JSON object. '
        'See the documentation at '
        'https://aiida.readthedocs.io/projects/aiida-core/en/latest/topics/database.html'
        '#converting-the-querybuilder-to-from-a-dictionary for more information.'
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # HTTP Request method decorators
        if 'get_decorators' in kwargs and isinstance(kwargs['get_decorators'], (tuple, list, set)):
            self.method_decorators.update({'post': list(kwargs['get_decorators'])})

    def get(self):  # pylint: disable=arguments-differ
        """Static return to state information about this endpoint."""
        path, url, url_root, query_string = self.unquote_request()
        headers = self.utils.build_headers(url=request.url, total_count=1)
        return self.utils.build_response(
            status=405,  # Method Not Allowed
            headers=headers,
            data={
                'method': request.method,
                'url': url,
                'url_root': url_root,
                'path': path,
                'query_string': query_string,
                'resource_type': self.__class__.__name__,
                'data': {'message': self.GET_MESSAGE},
            },
        )

    def post(self):  # pylint: disable=too-many-branches
        """
        POST method to pass query help JSON.

        If the posted JSON is not a valid QueryBuilder serialisation,
        the request will fail with an internal server error.

        This uses the NodeTranslator in order to best return Nodes according to the general AiiDA
        REST API data format, while still allowing the return of other AiiDA entities.

        :return: QueryBuilder result of AiiDA entities in "standard" REST API format.
        """
        # pylint: disable=protected-access
        path, url, url_root, query_string = self.unquote_request()
        profile = self.parse_query_string(query_string)[-1]

        try:
            self.load_profile(profile)
        except RestInputValidationError as exception:
            return self.utils.build_response(
                status=400,
                headers=self.utils.build_headers(url=request.url, total_count=0),
                data={
                    'method': request.method,
                    'url': url,
                    'url_root': url_root,
                    'path': path,
                    'query_string': query_string,
                    'resource_type': self.__class__.__name__,
                    'data': {
                        'message': str(exception)
                    },
                }
            )

        self.trans._query_help = request.get_json(force=True)
        # While the data may be correct JSON, it MUST be a single JSON Object,
        # equivalent of a QueryBuilder.as_dict() dictionary.
        assert isinstance(self.trans._query_help, dict), (
            'POSTed data MUST be a valid QueryBuilder.as_dict() dictionary. '
            f'Got instead (type: {type(self.trans._query_help)}): {self.trans._query_help}'
        )
        self.trans.__label__ = self.trans._result_type = self.trans._query_help['path'][-1]['tag']

        # Handle empty list projections
        number_projections = len(self.trans._query_help['project'])
        empty_projections_counter = 0
        skip_tags = []
        for tag, projections in tuple(self.trans._query_help['project'].items()):
            if projections == [{'*': {}}]:
                self.trans._query_help['project'][tag] = self.trans._default
            elif not projections:
                empty_projections_counter += 1
                skip_tags.append(tag)
            else:
                # Use projections as given, no need to "correct" them.
                pass

        if empty_projections_counter == number_projections:
            # No projections have been specified in the dictionary.
            # To be true to the QueryBuilder response, the last entry in path
            # is the only entry to be returned, all without edges/links.
            self.trans._query_help['project'][self.trans.__label__] = self.trans._default

        self.trans.init_qb()

        data = {}
        if self.trans.get_total_count():
            if empty_projections_counter == number_projections:
                # "Normal" REST API retrieval can be used.
                data = self.trans.get_results()
            else:
                # Since the "normal" REST API retrieval relies on single-tag retrieval,
                # we must instead be more creative with how we retrieve the results here.
                # So we opt for a dictionary, with the tags being the keys.
                for tag in self.trans._query_help['project']:
                    if tag in skip_tags:
                        continue
                    self.trans.__label__ = tag
                    data.update(self.trans.get_formatted_result(tag))

        # Remove 'full_type's when they're `None`
        for tag, entities in list(data.items()):
            updated_entities = []
            for entity in entities:
                if entity.get('full_type') is None:
                    entity.pop('full_type', None)
                updated_entities.append(entity)
            data[tag] = updated_entities

        headers = self.utils.build_headers(url=request.url, total_count=self.trans.get_total_count())
        return self.utils.build_response(
            status=200,
            headers=headers,
            data={
                'method': request.method,
                'url': unquote(request.url),
                'url_root': unquote(request.url_root),
                'path': unquote(request.path),
                'query_string': request.query_string.decode('utf-8'),
                'resource_type': self.__class__.__name__,
                'data': data,
            },
        )


class Node(BaseResource):
    """
    Differs from BaseResource in trans.set_query() mostly because it takes
    query_type as an input and the presence of additional result types like "tree"
    """
    _translator_class = NodeTranslator
    _parse_pk_uuid = 'uuid'  # Parse a uuid pattern in the URL path (not a pk)

    def get(self, id=None, page=None):  # pylint: disable=redefined-builtin,invalid-name,unused-argument
        # pylint: disable=too-many-locals,too-many-statements,too-many-branches,fixme,unused-variable
        """
        Get method for the Node resource.

        :param id: node identifier
        :param page: page no, used for pagination
        :return: http response
        """
        path, url, url_root, query_string = self.unquote_request()
        (resource_type, page, node_id, query_type) = self.parse_path(path)
        (
            limit, offset, perpage, orderby, filters, download_format, download, filename, tree_in_limit,
            tree_out_limit, attributes, attributes_filter, extras, extras_filter, full_type, profile
        ) = self.parse_query_string(query_string)

        try:
            self.load_profile(profile)
        except RestInputValidationError as exception:
            return self.utils.build_response(
                status=400,
                headers=self.utils.build_headers(url=request.url, total_count=0),
                data={
                    'method': request.method,
                    'url': url,
                    'url_root': url_root,
                    'path': path,
                    'query_string': query_string,
                    'resource_type': self.__class__.__name__,
                    'data': {
                        'message': str(exception)
                    },
                }
            )

        ## Validate request
        self.utils.validate_request(
            limit=limit,
            offset=offset,
            perpage=perpage,
            page=page,
            query_type=query_type,
            is_querystring_defined=(bool(query_string))
        )

        ## Treat the projectable properties case which does not imply access to the DataBase
        if query_type == 'projectable_properties':

            ## Retrieve the projectable properties
            projectable_properties, ordering = self.trans.get_projectable_properties()
            results = dict(fields=projectable_properties, ordering=ordering)
            ## Build response and return it
            headers = self.utils.build_headers(url=request.url, total_count=1)

        ## Treat the statistics
        elif query_type == 'statistics':
            headers = self.utils.build_headers(url=request.url, total_count=0)
            if filters:
                user_pk = filters['user']['==']
            else:
                user_pk = None
            results = self.trans.get_statistics(user_pk)

        elif query_type == 'full_types':
            headers = self.utils.build_headers(url=request.url, total_count=0)
            results = self.trans.get_namespace()

        elif query_type == 'full_types_count':
            headers = self.utils.build_headers(url=request.url, total_count=0)
            if filters:
                user_pk = filters['user']['==']
            else:
                user_pk = None
            results = self.trans.get_namespace(user_pk=user_pk, count_nodes=True)

        # TODO improve the performance of tree endpoint by getting the data from database faster
        # TODO add pagination for this endpoint (add default max limit)
        elif query_type == 'tree':
            headers = self.utils.build_headers(url=request.url, total_count=0)
            results = self.trans.get_io_tree(node_id, tree_in_limit, tree_out_limit)

        elif node_id is None and query_type == 'download_formats':
            headers = self.utils.build_headers(url=request.url, total_count=0)
            results = self.trans.get_all_download_formats(full_type)

        else:
            ## Initialize the translator
            self.trans.set_query(
                filters=filters,
                orders=orderby,
                query_type=query_type,
                node_id=node_id,
                download_format=download_format,
                download=download,
                filename=filename,
                attributes=attributes,
                attributes_filter=attributes_filter,
                extras=extras,
                extras_filter=extras_filter,
                full_type=full_type
            )

            ## Count results
            total_count = self.trans.get_total_count()

            ## Pagination (if required)
            if page is not None:
                (limit, offset, rel_pages) = self.utils.paginate(page, perpage, total_count)
                self.trans.set_limit_offset(limit=limit, offset=offset)

                ## Retrieve results
                results = self.trans.get_results()

                headers = self.utils.build_headers(rel_pages=rel_pages, url=request.url, total_count=total_count)
            else:

                self.trans.set_limit_offset(limit=limit, offset=offset)
                ## Retrieve results
                results = self.trans.get_results()

                if query_type == 'repo_contents' and results:
                    response = make_response(results)
                    response.headers['content-type'] = 'application/octet-stream'
                    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
                    return response

                if query_type == 'download' and download not in ['false', 'False', False] and results:
                    if results['download']['status'] == 200:
                        data = results['download']['data']
                        response = make_response(data)
                        response.headers['content-type'] = 'application/octet-stream'
                        response.headers['Content-Disposition'] = 'attachment; filename="{}"'.format(
                            results['download']['filename']
                        )
                        return response

                    results = results['download']['data']

                headers = self.utils.build_headers(url=request.url, total_count=total_count)

            if attributes_filter is not None and attributes:
                for node in results['nodes']:
                    node['attributes'] = {}
                    if not isinstance(attributes_filter, list):
                        attributes_filter = [attributes_filter]
                    for attr in attributes_filter:
                        node['attributes'][str(attr)] = node[f'attributes.{str(attr)}']
                        del node[f'attributes.{str(attr)}']

            if extras_filter is not None and extras:
                for node in results['nodes']:
                    node['extras'] = {}
                    if not isinstance(extras_filter, list):
                        extras_filter = [extras_filter]
                    for extra in extras_filter:
                        node['extras'][str(extra)] = node[f'extras.{str(extra)}']
                        del node[f'extras.{str(extra)}']

        ## Build response
        data = dict(
            method=request.method,
            url=url,
            url_root=url_root,
            path=path,
            id=node_id,
            query_string=query_string,
            resource_type=resource_type,
            data=results
        )

        return self.utils.build_response(status=200, headers=headers, data=data)


class Computer(BaseResource):
    """ Resource for Computer """
    from aiida.restapi.translator.computer import ComputerTranslator

    _translator_class = ComputerTranslator
    _parse_pk_uuid = 'uuid'


class Group(BaseResource):
    """ Resource for Group """
    from aiida.restapi.translator.group import GroupTranslator

    _translator_class = GroupTranslator
    _parse_pk_uuid = 'uuid'


class User(BaseResource):
    """ Resource for User """
    from aiida.restapi.translator.user import UserTranslator

    _translator_class = UserTranslator
    _parse_pk_uuid = 'pk'


class ProcessNode(Node):
    """ Resource for ProcessNode """
    from aiida.restapi.translator.nodes.process.process import ProcessTranslator

    _translator_class = ProcessTranslator

    def get(self, id=None, page=None):  # pylint: disable=redefined-builtin
        """
        Get method for the Process resource.

        :param id: node identifier
        :return: http response
        """
        path, url, url_root, query_string = self.unquote_request()
        resource_type, page, node_id, query_type = self.parse_path(path)
        profile = self.parse_query_string(query_string)[-1]

        try:
            self.load_profile(profile)
        except RestInputValidationError as exception:
            return self.utils.build_response(
                status=400,
                headers=self.utils.build_headers(url=request.url, total_count=0),
                data={
                    'method': request.method,
                    'url': url,
                    'url_root': url_root,
                    'path': path,
                    'query_string': query_string,
                    'resource_type': self.__class__.__name__,
                    'data': {
                        'message': str(exception)
                    },
                }
            )

        headers = self.utils.build_headers(url=request.url, total_count=1)

        results = None
        if query_type == 'report':
            node = self._load_and_verify(node_id)
            report = self.trans.get_report(node)
            results = report

        elif query_type == 'projectable_properties':
            ## Retrieve the projectable properties
            projectable_properties, ordering = self.trans.get_projectable_properties()
            results = dict(fields=projectable_properties, ordering=ordering)

        ## Build response
        data = dict(
            method=request.method,
            url=url,
            url_root=url_root,
            path=path,
            id=node_id,
            query_string=query_string,
            resource_type=resource_type,
            data=results
        )

        return self.utils.build_response(status=200, headers=headers, data=data)


class CalcJobNode(ProcessNode):
    """ Resource for CalcJobNode """
    from aiida.restapi.translator.nodes.process.calculation.calcjob import CalcJobTranslator

    _translator_class = CalcJobTranslator

    def get(self, id=None, page=None):  # pylint: disable=redefined-builtin
        """
        Get method for the Process resource.

        :param id: node identifier
        :return: http response
        """
        path, url, url_root, query_string = self.unquote_request()
        resource_type, page, node_id, query_type = self.parse_path(path)
        profile = self.parse_query_string(query_string)[-1]

        try:
            self.load_profile(profile)
        except RestInputValidationError as exception:
            return self.utils.build_response(
                status=400,
                headers=self.utils.build_headers(url=request.url, total_count=0),
                data={
                    'method': request.method,
                    'url': url,
                    'url_root': url_root,
                    'path': path,
                    'query_string': query_string,
                    'resource_type': self.__class__.__name__,
                    'data': {
                        'message': str(exception)
                    },
                }
            )

        node = self._load_and_verify(node_id)
        results = None

        params = request.args
        filename = params.get('filename', '')

        if query_type == 'input_files':
            results = self.trans.get_input_files(node, filename)
        elif query_type == 'output_files':
            results = self.trans.get_output_files(node, filename)

        ## Build response and return it
        headers = self.utils.build_headers(url=request.url, total_count=1)

        ## Build response
        data = dict(
            method=request.method,
            url=url,
            url_root=url_root,
            path=path,
            id=node_id,
            query_string=query_string,
            resource_type=resource_type,
            data=results
        )

        return self.utils.build_response(status=200, headers=headers, data=data)
