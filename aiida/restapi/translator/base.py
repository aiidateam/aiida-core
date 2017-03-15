# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.backends.profile import BACKEND_DJANGO, BACKEND_SQLA
from aiida.backends.settings import BACKEND
from aiida.common.exceptions import InputValidationError, InvalidOperation, \
    ConfigurationError
from aiida.common.utils import get_object_from_string, issingular
from aiida.orm.querybuilder import QueryBuilder
from aiida.restapi.common.exceptions import RestValidationError, \
    RestInputValidationError
from aiida.restapi.common.utils import pk_dbsynonym


class BaseTranslator(object):
    """
    Generic class for translator. It also contains all methods
    required to build QueryBuilder object
    """

    # A label associated to the present class
    __label__ = None
    # The string name of the AiiDA class one-to-one associated to the present
    #  class
    _aiida_type = None
    # The string associated to the AiiDA class in the query builder lexicon
    _qb_type = None

    _result_type = __label__

    _default = _default_projections = []
    _is_qb_initialized = False
    _is_pk_query = None
    _total_count = None

    def __init__(self, Class=None, **kwargs):
        """
        Initialise the parameters.
        Create the basic query_help

        keyword Class (default None but becomes this class): is the class
        from which one takes the initial values of the attributes. By default
        is this class so that class atributes are  translated into object
        attributes. In case of inheritance one cane use the
        same constructore but pass the inheriting class to pass its attributes.
        """

        # Assume default class is this class (cannot be done in the
        # definition as it requires self)
        if Class is None:
            Class = self.__class__

        # Assign class parameters to the object
        self.__label__ = Class.__label__
        self._aiida_type = Class._aiida_type
        self._qb_type = Class._qb_type
        self._result_type = Class.__label__

        self._default = Class._default
        self._default_projections = Class._default_projections
        self._is_qb_initialized = Class._is_qb_initialized
        self._is_pk_query = Class._is_pk_query
        self._total_count = Class._total_count

        # basic query_help object
        self._query_help = {
            "path": [{
                "type": self._qb_type,
                "label": self.__label__
            }],
            "filters": {},
            "project": {},
            "order_by": {}
        }
        # query_builder object (No initialization)
        self.qb = QueryBuilder()

        self.LIMIT_DEFAULT = kwargs['LIMIT_DEFAULT']

        if 'custom_schema' in kwargs:
            self.custom_schema = kwargs['custom_schema']
        else:
            self.custom_schema = None

    def __repr__(self):
        """
        This function is required for the caching system to be able to compare
        two NodeTranslator objects. Comparison is done on the value returned by
        __repr__
        :return: representation of NodeTranslator objects. Returns nothing
        because the inputs of self.get_nodes are sufficient to determine the
        identity of two queries.
        """
        return ""

    def get_schema(self):

        # Construct the full class string
        class_string = 'aiida.orm.' + self._aiida_type

        # Load correspondent orm class
        orm_class = get_object_from_string(class_string)

        # Construct the json object to be returned
        basic_schema = orm_class.get_db_columns()

        if self._default_projections == ['**']:
            schema = basic_schema  # No custom schema, take the basic one
        else:
            schema = dict([(k, basic_schema[k]) for k in
                           self._default_projections
                           if k in basic_schema.keys()])

        # Convert the related_tablevalues to the RESTAPI resources
        # (orm class/db table ==> RESTapi resource)
        def table2resource(table_name):
            # TODO Consider ways to make this function backend independent (one
            # idea would be to go from table name to aiida class name which is
            # univoque)
            if BACKEND == BACKEND_DJANGO:
                (spam, resource_name) = issingular(table_name[2:].lower())
            elif BACKEND == BACKEND_SQLA:
                (spam, resource_name) = issingular(table_name[5:])
            elif BACKEND is None:
                raise ConfigurationError("settings.BACKEND has not been set.\n"
                                         "Hint: Have you called "
                                         "aiida.load_dbenv?")
            else:
                raise ConfigurationError("Unknown settings.BACKEND: {}".format(
                    BACKEND))
            return resource_name

        for k, v in schema.iteritems():

            # Add custom fields to the column dictionaries
            if 'fields' in self.custom_schema:
                if k in self.custom_schema['fields'].keys():
                    schema[k].update(self.custom_schema['fields'][k])

            # Convert python types values into strings
            schema[k]['type'] = str(schema[k]['type'])[7:-2]

            # Construct the 'related resource' field from the 'related_table'
            # field
            if v['is_foreign_key'] == True:
                schema[k]['related_resource'] = table2resource(
                    schema[k].pop('related_table'))

        return dict(columns=schema)

    def init_qb(self):
        """
        Initialize query builder object by means of _query_help
        """
        self.qb.__init__(**self._query_help)
        self._is_qb_initialized = True

    def count(self):
        """
        Count the number of rows returned by the query and set total_count
        """
        if self._is_qb_initialized:
            self._total_count = self.qb.count()
        else:
            raise InvalidOperation("query builder object has not been "
                                   "initialized.")

            # def caching_method(self):
            #     """
            #     class method for caching. It is a wrapper of the
            # flask_cache memoize
            #     method. To be used as a decorator
            #     :return: the flask_cache memoize method with the timeout kwarg
            #     corrispondent to the class
            #     """
            #     return cache.memoize()
            #

            #    @cache.memoize(timeout=CACHING_TIMEOUTS[self.__label__])

    def get_total_count(self):
        """
        Returns the number of rows of the query
        :return: total_count
        """
        ## Count the results if needed
        if not self._total_count:
            self.count()

        return self._total_count

    def set_filters(self, filters={}):
        """
        Add filters in query_help.

        :param filters: it is a dictionary where keys are the tag names
         given in the path in query_help and their values are the dictionary
         of filters want to add for that tag name. Format for the Filters
         dictionary:
         filters = {
                    "tag1" : {k1:v1, k2:v2},
                    "tag2" : {k1:v1, k2:v2},
                  }
        :return: query_help dict including filters if any.
        """

        if isinstance(filters, dict):
            if len(filters) > 0:
                for tag, tag_filters in filters.iteritems():
                    if len(tag_filters) > 0 and isinstance(tag_filters, dict):
                        self._query_help["filters"][tag] = {}
                        for filter_key, filter_value in tag_filters.iteritems():
                            if filter_key == "pk":
                                filter_key = pk_dbsynonym
                            self._query_help["filters"][tag][filter_key] \
                                = filter_value
        else:
            raise InputValidationError("Pass data in dictionary format where "
                                       "keys are the tag names given in the "
                                       "path in query_help and and their values"
                                       " are the dictionary of filters want "
                                       "to add for that tag name.")

    def get_default_projections(self):
        """
        method to get default projections of the node
        :return: self._default_projections
        """
        return self._default_projections

    def set_default_projections(self):
        """
        It calls the set_projections() methods internally to add the
        default projections in query_help

        :return: None
        """
        self.set_projections({self.__label__: self._default_projections})

    def set_projections(self, projections):
        """
        add the projections in query_help

        :param projections: it is a dictionary where keys are the tag names
         given in the path in query_help and values are the list of the names
         you want to project in the final output
        :return: updated query_help with projections
        """
        if isinstance(projections, dict):
            if len(projections) > 0:
                for project_key, project_list in projections.iteritems():
                    self._query_help["project"][project_key] = project_list
        else:
            raise InputValidationError("Pass data in dictionary format where "
                                       "keys are the tag names given in the "
                                       "path in query_help and values are the "
                                       "list of the names you want to project "
                                       "in the final output")

    def set_order(self, orders):
        """
        Add order_by clause in query_help
        :param orders: dictionary of orders you want to apply on final
        results
        :return: None or exception if any.
        """
        ## Validate input
        if type(orders) is not dict:
            raise InputValidationError("orders has to be a dictionary"
                                       "compatible with the 'order_by' section"
                                       "of the query_help")

        ## Auxiliary_function to get the ordering cryterion
        def def_order(columns):
            """
            Takes a list of signed column names ex. ['id', '-ctime',
            '+mtime']
            and transforms it in a order_by compatible dictionary
            :param columns: (list of strings)
            :return: a dictionary
            """
            order_dict = {}
            for column in columns:
                if column[0] == '-':
                    order_dict[column[1:]] = 'desc'
                elif column[0] == '+':
                    order_dict[column[1:]] = 'asc'
                else:
                    order_dict[column] = 'asc'
            if order_dict.has_key('pk'):
                order_dict[pk_dbsynonym] = order_dict.pop('pk')
            return order_dict

        ## Assign orderby field query_help
        for tag, columns in orders.iteritems():
            self._query_help['order_by'][tag] = def_order(columns)

    def set_query(self, filters=None, orders=None, projections=None, pk=None):
        """
        Adds filters, default projections, order specs to the query_help,
        and initializes the qb object

        :param filters: dictionary with the filters
        :param orders: dictionary with the order for each tag
        :param pk (integer): pk of a specific node
        """

        tagged_filters = {}

        ## Check if filters are well defined and construct an ad-hoc filter
        # for pk_query
        if pk is not None:
            self._is_pk_query = True
            if self._result_type == self.__label__ and len(filters) > 0:
                raise RestInputValidationError("selecting a specific pk does "
                                               "not "
                                               "allow to specify filters")
            elif not self._check_pk_validity(pk):
                raise RestValidationError(
                    "either the selected pk does not exist "
                    "or the corresponding object is not of "
                    "type aiida.orm.{}".format(self._aiida_type))
            else:
                tagged_filters[self.__label__] = {'id': {'==': pk}}
                if self._result_type is not self.__label__:
                    tagged_filters[self._result_type] = filters
        else:
            tagged_filters[self.__label__] = filters

        ## Add filters
        self.set_filters(tagged_filters)

        ## Add projections
        if projections is None:
            self.set_default_projections()
        else:
            tagged_projections = {self._result_type: projections}
            self.set_projections(tagged_projections)

        ##Add order_by
        if orders is not None:
            tagged_orders = {self._result_type: orders}
            self.set_order(tagged_orders)

        ## Initialize the query_object
        self.init_qb()

    def get_query_help(self):
        """
        :return: return QB json dictionary
        """
        return self._query_help

    def set_limit_offset(self, limit=None, offset=None):
        """
        sets limits and offset directly to the query_builder object

        :param limit:
        :param offset:
        :return:
        """

        ## mandatory params
        # none

        ## non-mandatory params
        if limit is not None:
            try:
                limit = int(limit)
            except ValueError:
                raise InputValidationError("Limit value must be an integer")
            if limit > self.LIMIT_DEFAULT:
                raise RestValidationError("Limit and perpage cannot be bigger "
                                          "than {}".format(self.LIMIT_DEFAULT))
        else:
            limit = self.LIMIT_DEFAULT

        if offset is not None:
            try:
                offset = int(offset)
            except ValueError:
                raise InputValidationError("Offset value must be an "
                                           "integer")

        if self._is_qb_initialized:
            if limit is not None:
                self.qb.limit(limit)
            else:
                pass
            if offset is not None:
                self.qb.offset(offset)
            else:
                pass
        else:
            raise InvalidOperation("query builder object has not been "
                                   "initialized.")

    def get_formatted_result(self, label):
        """
        Runs the query and retrieves results tagged as "label"
        :param label (string): the tag of the results to be extracted out of
        the query rows.
        :return: a list of the query results
        """

        if not self._is_qb_initialized:
            raise InvalidOperation("query builder object has not been "
                                   "initialized.")

        results = []
        if self._total_count > 0:
            results = [res[label] for res in self.qb.dict()]

        # TODO think how to make it less hardcoded
        if self._result_type == 'input_of':
            return {'inputs': results}
        elif self._result_type == 'output_of':
            return {'outputs': results}
        else:
            return {self.__label__: results}

    def get_results(self):
        """
        Returns either list of nodes or details of single node from database

        :return: either list of nodes or details of single node
        from database
        """

        ## Check whether the querybuilder object has been initialized
        if not self._is_qb_initialized:
            raise InvalidOperation("query builder object has not been "
                                   "initialized.")

        ## Count the total number of rows returned by the query (if not
        # already done)
        if self._total_count is None:
            self.count()

        ## Retrieve data
        data = self.get_formatted_result(self._result_type)
        return data

    def _check_pk_validity(self, pk):
        """
        Checks whether a pk corresponds to an object of the expected type,
        whenever type is a valid column of the database (ex. for nodes,
        but not for users)_
        :param pk: (integer) ok to check
        :return: True or False
        """
        # The logic could be to load the node or to use querybuilder. Let's
        # do with qb for consistency, although it would be easier to do it
        # with load_node

        query_help_base = {
            'path': [
                {
                    'type': self._qb_type,
                    'label': self.__label__,
                },
            ],
            'filters': {
                self.__label__:
                    {
                        'id': {'==': pk}
                    }
            }
        }

        qb_base = QueryBuilder(**query_help_base)
        return qb_base.count() == 1
