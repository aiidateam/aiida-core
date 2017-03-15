# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from urllib import unquote

from flask import request
from flask_restful import Resource

from aiida.restapi.common.utils import Utils


## TODO add the caching support. I cache total count, results, and possibly
# set_query
class BaseResource(Resource):
    ## Each derived class will instantiate a different type of translator.
    # This is the only difference in the classes.
    def __init__(self, **kwargs):

        self.trans = None

        # Configure utils
        utils_conf_keys = ('PREFIX', 'PERPAGE_DEFAULT', 'LIMIT_DEFAULT')
        self.utils_confs = {k: kwargs[k] for k in utils_conf_keys if k in
                            kwargs}
        self.utils = Utils(**self.utils_confs)

    def get(self, pk=None, page=None):
        """
        Get method for the Computer resource
        :return:
        """

        ## Decode url parts
        path = unquote(request.path)
        query_string = unquote(request.query_string)
        url = unquote(request.url)
        url_root = unquote(request.url_root)

        ## Parse request
        (resource_type, page, pk, query_type) = self.utils.parse_path(path)
        (limit, offset, perpage, orderby, filters, alist, nalist, elist,
         nelist) = self.utils.parse_query_string(query_string)

        ## Validate request
        self.utils.validate_request(limit=limit, offset=offset, perpage=perpage,
                                    page=page, query_type=query_type,
                                    is_querystring_defined=(bool(query_string)))

        ## Treat the schema case which does not imply access to the DataBase
        if query_type == 'schema':

            ## Retrieve the schema
            results = self.trans.get_schema()
            ## Build response and return it
            headers = self.utils.build_headers(url=request.url, total_count=1)

        else:
            ## Set the query, and initialize qb object
            self.trans.set_query(filters=filters, orders=orderby, pk=pk)

            ## Count results
            total_count = self.trans.get_total_count()

            ## Pagination (if required)
            if page is not None:
                (limit, offset, rel_pages) = self.utils.paginate(page, perpage,
                                                                 total_count)
                self.trans.set_limit_offset(limit=limit, offset=offset)
                headers = self.utils.build_headers(rel_pages=rel_pages,
                                                   url=request.url,
                                                   total_count=total_count)
            else:
                self.trans.set_limit_offset(limit=limit, offset=offset)
                headers = self.utils.build_headers(url=request.url,
                                                   total_count=total_count)

            ## Retrieve results
            results = self.trans.get_results()

        ## Build response and return it
        data = dict(method=request.method,
                    url=url,
                    url_root=url_root,
                    path=request.path,
                    pk=pk,
                    query_string=request.query_string,
                    resource_type=resource_type,
                    data=results)
        return self.utils.build_response(status=200, headers=headers, data=data)


class Node(Resource):
    ##Differs from BaseResource in trans.set_query() mostly because it takes
    # query_type as an input
    def __init__(self, **kwargs):

        # Set translator
        from aiida.restapi.translator.node import NodeTranslator
        self.trans = NodeTranslator(**kwargs)

        from aiida.orm import Node
        self.tclass = Node

        # Configure utils
        utils_conf_keys = ('PREFIX', 'PERPAGE_DEFAULT', 'LIMIT_DEFAULT')
        self.utils_confs = {k: kwargs[k] for k in utils_conf_keys if k in
                            kwargs}
        self.utils = Utils(**self.utils_confs)

    def get(self, pk=None, page=None):
        """
        Get method for the Node resource.
        :return:
        """

        ## Decode url parts
        path = unquote(request.path)
        query_string = unquote(request.query_string)
        url = unquote(request.url)
        url_root = unquote(request.url_root)

        ## Parse request
        (resource_type, page, pk, query_type) = self.utils.parse_path(path)

        (limit, offset, perpage, orderby, filters, alist, nalist, elist,
         nelist) = self.utils.parse_query_string(query_string)

        ## Validate request
        self.utils.validate_request(limit=limit, offset=offset, perpage=perpage,
                                    page=page, query_type=query_type,
                                    is_querystring_defined=(bool(query_string)))

        ## Treat the schema case which does not imply access to the DataBase
        if query_type == 'schema':

            ## Retrieve the schema
            results = self.trans.get_schema()

            ## Build response and return it
            headers = self.utils.build_headers(url=request.url, total_count=1)

        elif query_type == "statistics":
            (limit, offset, perpage, orderby, filters, alist, nalist, elist,
             nelist) = self.utils.parse_query_string(query_string)
            headers = self.utils.build_headers(url=request.url, total_count=0)
            if len(filters) > 0:
                usr = filters["user"]["=="]
            else:
                usr = []
            results = self.trans.get_statistics(self.tclass, usr)

        elif query_type == "tree":
            if len(filters) > 0:
                depth = filters["depth"]["=="]
            else:
                depth = None
            results = self.trans.get_io_tree(pk, depth)
            headers = self.utils.build_headers(url=request.url, total_count=0)

        else:
            ## Instantiate a translator and initialize it
            self.trans.set_query(filters=filters, orders=orderby,
                                 query_type=query_type, pk=pk, alist=alist,
                                 nalist=nalist, elist=elist, nelist=nelist)

            ## Count results
            total_count = self.trans.get_total_count()

            ## Pagination (if required)
            if page is not None:
                (limit, offset, rel_pages) = self.utils.paginate(page, perpage,
                                                                 total_count)
                self.trans.set_limit_offset(limit=limit, offset=offset)
                headers = self.utils.build_headers(rel_pages=rel_pages,
                                                   url=request.url,
                                                   total_count=total_count)
            else:
                self.trans.set_limit_offset(limit=limit, offset=offset)
                headers = self.utils.build_headers(url=request.url,
                                                   total_count=total_count)

            ## Retrieve results
            results = self.trans.get_results()

        ## Build response
        data = dict(method=request.method,
                    url=url,
                    url_root=url_root,
                    path=path,
                    pk=pk,
                    query_string=query_string,
                    resource_type=resource_type,
                    data=results)
        return self.utils.build_response(status=200, headers=headers, data=data)


class Computer(BaseResource):
    def __init__(self, **kwargs):
        super(Computer, self).__init__(**kwargs)

        ## Instantiate the correspondent translator
        from aiida.restapi.translator.computer import ComputerTranslator
        self.trans = ComputerTranslator(**kwargs)


class Group(BaseResource):
    def __init__(self, **kwargs):
        super(Group, self).__init__(**kwargs)

        from aiida.restapi.translator.group import GroupTranslator
        self.trans = GroupTranslator(**kwargs)


class User(BaseResource):
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

        from aiida.restapi.translator.user import UserTranslator
        self.trans = UserTranslator(**kwargs)


class Calculation(Node):
    def __init__(self, **kwargs):
        super(Calculation, self).__init__(**kwargs)

        from aiida.restapi.translator.calculation import CalculationTranslator
        self.trans = CalculationTranslator(**kwargs)
        from aiida.orm import Calculation as CalculationTclass
        self.tclass = CalculationTclass


class Code(Node):
    def __init__(self, **kwargs):
        super(Code, self).__init__(**kwargs)

        from aiida.restapi.translator.code import CodeTranslator
        self.trans = CodeTranslator(**kwargs)
        from aiida.orm import Code as CodeTclass
        self.tclass = CodeTclass


class Data(Node):
    def __init__(self, **kwargs):
        super(Data, self).__init__(**kwargs)

        from aiida.restapi.translator.data import DataTranslator
        self.trans = DataTranslator(**kwargs)
        from aiida.orm import Data as DataTclass
        self.tclass = DataTclass
