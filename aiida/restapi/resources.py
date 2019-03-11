# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
""" Resources for REST API """

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from six.moves.urllib.parse import unquote  # pylint: disable=import-error
from flask import request, make_response
from flask_restful import Resource

from aiida.restapi.common.utils import Utils


class ServerInfo(Resource):
    # pylint: disable=fixme
    """Endpointd to return general server info"""

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

        ## Decode url parts
        path = unquote(request.path)
        url = unquote(request.url)
        url_root = unquote(request.url_root)

        pathlist = self.utils.split_path(self.utils.strip_api_prefix(path))

        if len(pathlist) > 1:
            resource_type = pathlist.pop(1)
        else:
            resource_type = "info"

        response = {}

        import aiida.restapi.common.config as conf
        from aiida import __version__

        if resource_type == "info":
            response = []

            # Add Rest API version
            response.append("REST API version: " + conf.PREFIX.split("/")[-1])

            # Add Rest API prefix
            response.append("REST API Prefix: " + conf.PREFIX)

            # Add AiiDA version
            response.append("AiiDA==" + __version__)

        elif resource_type == "endpoints":

            from aiida.restapi.common.utils import list_routes
            response["available_endpoints"] = list_routes()

        headers = self.utils.build_headers(url=request.url, total_count=1)

        ## Build response and return it
        data = dict(
            method=request.method,
            url=url,
            url_root=url_root,
            path=path,
            query_string=request.query_string.decode('utf-8'),
            resource_type="Info",
            data=response)
        return self.utils.build_response(status=200, headers=headers, data=data)


class BaseResource(Resource):
    # pylint: disable=fixme
    """
    Each derived class will instantiate a different type of translator.
    This is the only difference in the classes.
    """

    ## TODO add the caching support. I cache total count, results, and possibly

    def __init__(self, **kwargs):

        self.trans = None

        # Flag to tell the path parser whether to expect a pk or a uuid pattern
        self.parse_pk_uuid = None

        # Configure utils
        utils_conf_keys = ('PREFIX', 'PERPAGE_DEFAULT', 'LIMIT_DEFAULT')
        self.utils_confs = {k: kwargs[k] for k in utils_conf_keys if k in kwargs}
        self.utils = Utils(**self.utils_confs)
        self.method_decorators = {'get': kwargs.get('get_decorators', [])}

    def get(self, id=None, page=None):  # pylint: disable=redefined-builtin,invalid-name,unused-argument
        # pylint: disable=too-many-locals
        """
        Get method for the resource
        :param id: node identifier
        :param page: page no, used for pagination
        :return: http response
        """

        ## Decode url parts
        path = unquote(request.path)
        query_string = unquote(request.query_string.decode('utf-8'))
        url = unquote(request.url)
        url_root = unquote(request.url_root)

        ## Parse request
        (resource_type, page, node_id, query_type) = self.utils.parse_path(path, parse_pk_uuid=self.parse_pk_uuid)

        # pylint: disable=unused-variable
        (limit, offset, perpage, orderby, filters, _alist, _nalist, _elist, _nelist, _downloadformat, _visformat,
         _filename, _rtype, tree_in_limit, tree_out_limit) = self.utils.parse_query_string(query_string)

        ## Validate request
        self.utils.validate_request(
            limit=limit,
            offset=offset,
            perpage=perpage,
            page=page,
            query_type=query_type,
            is_querystring_defined=(bool(query_string)))

        ## Treat the schema case which does not imply access to the DataBase
        if query_type == 'schema':

            ## Retrieve the schema
            results = self.trans.get_schema()
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
            query_string=request.query_string.decode('utf-8'),
            resource_type=resource_type,
            data=results)

        return self.utils.build_response(status=200, headers=headers, data=data)


class Node(Resource):
    """
    Differs from BaseResource in trans.set_query() mostly because it takes
    query_type as an input and the presence of additional result types like "tree"
    """

    def __init__(self, **kwargs):

        # Set translator
        from aiida.restapi.translator.node import NodeTranslator
        self.trans = NodeTranslator(**kwargs)

        from aiida.orm import Node as tNode
        self.tclass = tNode

        # Parse a uuid pattern in the URL path (not a pk)
        self.parse_pk_uuid = 'uuid'

        # Configure utils
        utils_conf_keys = ('PREFIX', 'PERPAGE_DEFAULT', 'LIMIT_DEFAULT')
        self.utils_confs = {k: kwargs[k] for k in utils_conf_keys if k in kwargs}
        self.utils = Utils(**self.utils_confs)
        self.method_decorators = {'get': kwargs.get('get_decorators', [])}

    def get(self, id=None, page=None):  # pylint: disable=redefined-builtin,invalid-name,unused-argument
        # pylint: disable=too-many-locals,too-many-statements,too-many-branches,fixme
        """
        Get method for the Node resource.

        :param id: node identifier
        :param page: page no, used for pagination
        :return: http response
        """

        ## Decode url parts
        path = unquote(request.path)
        query_string = unquote(request.query_string.decode('utf-8'))
        url = unquote(request.url)
        url_root = unquote(request.url_root)

        ## Parse request
        (resource_type, page, node_id, query_type) = self.utils.parse_path(path, parse_pk_uuid=self.parse_pk_uuid)

        (limit, offset, perpage, orderby, filters, alist, nalist, elist, nelist, downloadformat, visformat, filename,
         rtype, tree_in_limit, tree_out_limit) = self.utils.parse_query_string(query_string)

        ## Validate request
        self.utils.validate_request(
            limit=limit,
            offset=offset,
            perpage=perpage,
            page=page,
            query_type=query_type,
            is_querystring_defined=(bool(query_string)))

        ## Treat the schema case which does not imply access to the DataBase
        if query_type == 'schema':

            ## Retrieve the schema
            results = self.trans.get_schema()

            ## Build response and return it
            headers = self.utils.build_headers(url=request.url, total_count=1)

        ## Treat the statistics
        elif query_type == "statistics":
            (limit, offset, perpage, orderby, filters, alist, nalist, elist, nelist, downloadformat, visformat,
             filename, rtype, tree_in_limit, tree_out_limit) = self.utils.parse_query_string(query_string)
            headers = self.utils.build_headers(url=request.url, total_count=0)
            if filters:
                usr = filters["user"]["=="]
            else:
                usr = None
            results = self.trans.get_statistics(usr)

        # TODO improve the performance of tree endpoint by getting the data from database faster
        # TODO add pagination for this endpoint (add default max limit)
        elif query_type == "tree":
            headers = self.utils.build_headers(url=request.url, total_count=0)
            results = self.trans.get_io_tree(node_id, tree_in_limit, tree_out_limit)
        else:
            ## Initialize the translator
            self.trans.set_query(
                filters=filters,
                orders=orderby,
                query_type=query_type,
                node_id=node_id,
                alist=alist,
                nalist=nalist,
                elist=elist,
                nelist=nelist,
                downloadformat=downloadformat,
                visformat=visformat,
                filename=filename,
                rtype=rtype)

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

                if query_type == "download" and results:
                    if results["download"]["status"] == 200:
                        data = results["download"]["data"]
                        response = make_response(data)
                        response.headers['content-type'] = 'application/octet-stream'
                        response.headers['Content-Disposition'] = 'attachment; filename="{}"'.format(
                            results["download"]["filename"])
                        return response

                    results = results["download"]["data"]

                if query_type in ["retrieved_inputs", "retrieved_outputs"] and results:
                    try:
                        status = results[query_type]["status"]
                    except KeyError:
                        status = ""
                    except TypeError:
                        status = ""

                    if status == 200:
                        data = results[query_type]["data"]
                        response = make_response(data)
                        response.headers['content-type'] = 'application/octet-stream'
                        response.headers['Content-Disposition'] = 'attachment; filename="{}"'.format(
                            results[query_type]["filename"])
                        return response

                    results = results[query_type]["data"]

                headers = self.utils.build_headers(url=request.url, total_count=total_count)

        ## Build response
        data = dict(
            method=request.method,
            url=url,
            url_root=url_root,
            path=path,
            id=node_id,
            query_string=request.query_string.decode('utf-8'),
            resource_type=resource_type,
            data=results)

        return self.utils.build_response(status=200, headers=headers, data=data)


class Computer(BaseResource):
    """ Resource for Computer """

    def __init__(self, **kwargs):
        super(Computer, self).__init__(**kwargs)

        ## Instantiate the correspondent translator
        from aiida.restapi.translator.computer import ComputerTranslator
        self.trans = ComputerTranslator(**kwargs)

        # Set wheteher to expect a pk (integer) or a uuid pattern (string) in
        # the URL path
        self.parse_pk_uuid = "uuid"


class Group(BaseResource):
    """ Resource for Group """

    def __init__(self, **kwargs):
        super(Group, self).__init__(**kwargs)

        from aiida.restapi.translator.group import GroupTranslator
        self.trans = GroupTranslator(**kwargs)

        self.parse_pk_uuid = 'uuid'


class User(BaseResource):
    """ Resource for User """

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

        from aiida.restapi.translator.user import UserTranslator
        self.trans = UserTranslator(**kwargs)

        self.parse_pk_uuid = 'pk'


class Calculation(Node):
    """ Resource for Calculation """

    def __init__(self, **kwargs):
        super(Calculation, self).__init__(**kwargs)

        from aiida.restapi.translator.calculation import CalculationTranslator
        self.trans = CalculationTranslator(**kwargs)
        from aiida.orm import CalcJobNode as CalculationTclass
        self.tclass = CalculationTclass

        self.parse_pk_uuid = 'uuid'


class Code(Node):
    """ Resource for Code """

    def __init__(self, **kwargs):
        super(Code, self).__init__(**kwargs)

        from aiida.restapi.translator.code import CodeTranslator
        self.trans = CodeTranslator(**kwargs)
        from aiida.orm import Code as CodeTclass
        self.tclass = CodeTclass

        self.parse_pk_uuid = 'uuid'


class Data(Node):
    """ Resource for Data node """

    def __init__(self, **kwargs):
        super(Data, self).__init__(**kwargs)

        from aiida.restapi.translator.data import DataTranslator
        self.trans = DataTranslator(**kwargs)
        from aiida.orm import Data as DataTclass
        self.tclass = DataTclass

        self.parse_pk_uuid = 'uuid'


class StructureData(Data):
    """ Resource for structure data """

    def __init__(self, **kwargs):

        super(StructureData, self).__init__(**kwargs)

        from aiida.restapi.translator.data.structure import \
            StructureDataTranslator
        self.trans = StructureDataTranslator(**kwargs)
        from aiida.orm import StructureData as StructureDataTclass
        self.tclass = StructureDataTclass

        self.parse_pk_uuid = 'uuid'


class KpointsData(Data):
    """ Resource for kpoints data """

    def __init__(self, **kwargs):
        super(KpointsData, self).__init__(**kwargs)

        from aiida.restapi.translator.data.kpoints import KpointsDataTranslator
        self.trans = KpointsDataTranslator(**kwargs)
        from aiida.orm import KpointsData as KpointsDataTclass
        self.tclass = KpointsDataTclass

        self.parse_pk_uuid = 'uuid'


class BandsData(Data):
    """ Resource for Bands data """

    def __init__(self, **kwargs):
        super(BandsData, self).__init__(**kwargs)

        from aiida.restapi.translator.data.bands import \
            BandsDataTranslator
        self.trans = BandsDataTranslator(**kwargs)
        from aiida.orm import BandsData as BandsDataTclass
        self.tclass = BandsDataTclass

        self.parse_pk_uuid = 'uuid'


class CifData(Data):
    """ Resource for cif data """

    def __init__(self, **kwargs):

        super(CifData, self).__init__(**kwargs)

        from aiida.restapi.translator.data.cif import \
            CifDataTranslator
        self.trans = CifDataTranslator(**kwargs)
        from aiida.orm import CifData as CifDataTclass
        self.tclass = CifDataTclass

        self.parse_pk_uuid = 'uuid'


class UpfData(Data):
    """ Resource for upf data """

    def __init__(self, **kwargs):

        super(UpfData, self).__init__(**kwargs)

        from aiida.restapi.translator.data.upf import \
            UpfDataTranslator
        self.trans = UpfDataTranslator(**kwargs)
        from aiida.orm import UpfData as UpfDataTclass
        self.tclass = UpfDataTclass

        self.parse_pk_uuid = 'uuid'
