# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Base translator class"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six

from aiida.common.exceptions import InputValidationError, InvalidOperation, \
    ConfigurationError
from aiida.common.utils import get_object_from_string
from aiida.orm.querybuilder import QueryBuilder
from aiida.restapi.common.exceptions import RestValidationError, \
    RestInputValidationError
from aiida.restapi.common.utils import PK_DBSYNONYM


class BaseTranslator(object):
    """
    Generic class for translator. It contains the methods
    required to build a related QueryBuilder object
    """
    # pylint: disable=useless-object-inheritance,too-many-instance-attributes,fixme

    # A label associated to the present class
    __label__ = None
    # The AiiDA class one-to-one associated to the present class
    _aiida_class = None
    # The string name of the AiiDA class
    _aiida_type = None

    # The string associated to the AiiDA class in the query builder lexicon
    _qb_type = None

    # If True (False) the corresponding AiiDA class has (no) uuid property
    _has_uuid = None

    _result_type = __label__

    _default = _default_projections = ["**"]

    _schema_projections = {"column_order": [], "additional_info": {}}

    _is_qb_initialized = False
    _is_id_query = None
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
        self._aiida_class = Class._aiida_class  # pylint: disable=protected-access
        self._aiida_type = Class._aiida_type  # pylint: disable=protected-access
        self._qb_type = Class._qb_type  # pylint: disable=protected-access
        self._result_type = Class.__label__

        self._default = Class._default  # pylint: disable=protected-access
        self._default_projections = Class._default_projections  # pylint: disable=protected-access
        self._schema_projections = Class._schema_projections  # pylint: disable=protected-access
        self._is_qb_initialized = Class._is_qb_initialized  # pylint: disable=protected-access
        self._is_id_query = Class._is_id_query  # pylint: disable=protected-access
        self._total_count = Class._total_count  # pylint: disable=protected-access

        # Basic filter (dict) to set the identity of the uuid. None if
        #  no specific node is requested
        self._id_filter = None

        # basic query_help object
        self._query_help = {
            "path": [{
                "entity_type": self._qb_type,
                "tag": self.__label__
            }],
            "filters": {},
            "project": {},
            "order_by": {}
        }
        # query_builder object (No initialization)
        self.qbobj = QueryBuilder()

        self.limit_default = kwargs['LIMIT_DEFAULT']
        self.schema = None

    def __repr__(self):
        """
        This function is required for the caching system to be able to compare
        two NodeTranslator objects. Comparison is done on the value returned by __repr__

        :return: representation of NodeTranslator objects. Returns nothing
            because the inputs of self.get_nodes are sufficient to determine the
            identity of two queries.
        """
        return ""

    def get_schema(self):
        # pylint: disable=fixme,too-many-branches
        """
        Get node schema
        :return: node schema
        """

        # Construct the full class string
        if any([self._aiida_type.startswith(prefix) for prefix in ['node.', 'data.', 'process.']]):
            class_string = 'aiida.orm.nodes.' + self._aiida_type
        else:
            class_string = 'aiida.orm.' + self._aiida_type

        # Load correspondent orm class
        orm_class = get_object_from_string(class_string)

        # Construct the json object to be returned
        basic_schema = orm_class.get_schema()

        schema = {}
        ordering = []

        # get addional info and column order from translator class
        # and combine it with basic schema
        if self._schema_projections["column_order"]:
            for field in self._schema_projections["column_order"]:

                # basic schema
                if field in basic_schema.keys():
                    schema[field] = basic_schema[field]
                else:
                    ## Note: if column name starts with user_* get the schema information from
                    # user class. It is added mainly to handle user_email case.
                    # TODO need to improve
                    field_parts = field.split("_")
                    if field_parts[0] == "user" and field != "user_id" and len(field_parts) > 1:
                        from aiida.orm.users import User
                        user_schema = User.get_schema()
                        if field_parts[1] in user_schema.keys():
                            schema[field] = user_schema[field_parts[1]]
                        else:
                            raise KeyError("{} is not present in user schema".format(field))
                    else:
                        raise KeyError("{} is not present in ORM basic schema".format(field))

                # additional info defined in translator class
                if field in self._schema_projections["additional_info"]:
                    schema[field].update(self._schema_projections["additional_info"][field])
                else:
                    raise KeyError("{} is not present in default projection additional info".format(field))

            # order
            ordering = self._schema_projections["column_order"]

        else:
            raise ConfigurationError("Define column order to get schema for {}".format(self._aiida_type))

        return dict(fields=schema, ordering=ordering)

    def init_qb(self):
        """
        Initialize query builder object by means of _query_help
        """
        self.qbobj.__init__(**self._query_help)
        self._is_qb_initialized = True

    def count(self):
        """
        Count the number of rows returned by the query and set total_count
        """
        if self._is_qb_initialized:
            self._total_count = self.qbobj.count()
        else:
            raise InvalidOperation("query builder object has not been initialized.")

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
        Returns the number of rows of the query.

        :return: total_count
        """
        ## Count the results if needed
        if not self._total_count:
            self.count()

        return self._total_count

    def set_filters(self, filters=None):
        """
        Add filters in query_help.

        :param filters: it is a dictionary where keys are the tag names
            given in the path in query_help and their values are the dictionary
            of filters want to add for that tag name. Format for the Filters
            dictionary::

                filters = {
                    "tag1" : {k1:v1, k2:v2},
                    "tag2" : {k1:v1, k2:v2},
                }

        :return: query_help dict including filters if any.
        """
        if filters is None:
            filters = {}

        if isinstance(filters, dict):  # pylint: disable=too-many-nested-blocks
            if filters:
                for tag, tag_filters in filters.items():
                    if tag_filters and isinstance(tag_filters, dict):
                        self._query_help["filters"][tag] = {}
                        for filter_key, filter_value in tag_filters.items():
                            if filter_key == "pk":
                                filter_key = PK_DBSYNONYM
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
            if projections:
                for project_key, project_list in projections.items():
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
        if not isinstance(orders, dict):
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
            if 'pk' in order_dict:
                order_dict[PK_DBSYNONYM] = order_dict.pop('pk')
            return order_dict

        ## Assign orderby field query_help
        for tag, columns in orders.items():
            self._query_help['order_by'][tag] = def_order(columns)

    def set_query(self,
                  filters=None,
                  orders=None,
                  projections=None,
                  query_type=None,
                  node_id=None,
                  alist=None,
                  nalist=None,
                  elist=None,
                  nelist=None,
                  downloadformat=None,
                  visformat=None,
                  filename=None,
                  rtype=None):
        # pylint: disable=too-many-arguments,unused-argument
        """
        Adds filters, default projections, order specs to the query_help,
        and initializes the qb object

        :param filters: dictionary with the filters
        :param orders: dictionary with the order for each tag
        :param projections: dictionary with the projection. It is discarded
            if query_type=='attributes'/'extras'
        :param query_type: (string) specify the result or the content ("attr")
        :param id: (integer) id of a specific node
        :param alist: list of attributes queried for node
        :param nalist: list of attributes, returns all attributes except this for node
        :param elist: list of extras queries for node
        :param nelist: list of extras, returns all extras except this for node
        :param downloadformat: file format to download e.g. cif, xyz
        :param visformat: data format to visualise the node. Mainly used for structure,
            cif, kpoints. E.g. jsmol, chemdoodle
        :param filename: name of the file to return its content
        :param rtype: return type of the file
        """

        tagged_filters = {}

        ## Check if filters are well defined and construct an ad-hoc filter
        # for id_query
        if node_id is not None:
            self._is_id_query = True
            if self._result_type == self.__label__ and filters:
                raise RestInputValidationError("selecting a specific id does not allow to specify filters")

            try:
                self._check_id_validity(node_id)
            except RestValidationError as exc:
                raise RestValidationError(str(exc))
            else:
                tagged_filters[self.__label__] = self._id_filter
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
            if limit > self.limit_default:
                raise RestValidationError("Limit and perpage cannot be bigger than {}".format(self.limit_default))
        else:
            limit = self.limit_default

        if offset is not None:
            try:
                offset = int(offset)
            except ValueError:
                raise InputValidationError("Offset value must be an integer")

        if self._is_qb_initialized:
            if limit is not None:
                self.qbobj.limit(limit)
            else:
                pass
            if offset is not None:
                self.qbobj.offset(offset)
            else:
                pass
        else:
            raise InvalidOperation("query builder object has not been initialized.")

    def get_formatted_result(self, label):
        """
        Runs the query and retrieves results tagged as "label".

        :param label: the tag of the results to be extracted out of
          the query rows.
        :type label: str
        :return: a list of the query results
        """

        if not self._is_qb_initialized:
            raise InvalidOperation("query builder object has not been initialized.")

        results = []
        if self._total_count > 0:
            results = [res[label] for res in self.qbobj.dict()]

        # TODO think how to make it less hardcoded
        if self._result_type == 'with_outgoing':
            result = {'inputs': results}
        elif self._result_type == 'with_incoming':
            result = {'outputs': results}
        else:
            result = {self.__label__: results}

        return result

    def get_results(self):
        """
        Returns either list of nodes or details of single node from database.

        :return: either list of nodes or details of single node from database
        """

        ## Check whether the querybuilder object has been initialized
        if not self._is_qb_initialized:
            raise InvalidOperation("query builder object has not been initialized.")

        ## Count the total number of rows returned by the query (if not
        # already done)
        if self._total_count is None:
            self.count()

        ## Retrieve data
        data = self.get_formatted_result(self._result_type)
        return data

    def _check_id_validity(self, node_id):
        """
        Checks whether id corresponds to an object of the expected type,
        whenever type is a valid column of the database (ex. for nodes,
        but not for users)

        :param node_id: id (or id starting pattern)

        :return: True if node_id valid, False if invalid. If True, sets the id
          filter attribute correctly

        :raise RestValidationError: if no node is found or id pattern does
          not identify a unique node
        """
        from aiida.common.exceptions import MultipleObjectsError, NotExistent
        from aiida.orm.utils.loaders import IdentifierType, get_loader

        loader = get_loader(self._aiida_class)

        if self._has_uuid:

            # For consistency check that tid is a string
            if not isinstance(node_id, six.string_types):
                raise RestValidationError('parameter id has to be an string')

            identifier_type = IdentifierType.UUID
            qbobj, _ = loader.get_query_builder(node_id, identifier_type, sub_classes=(self._aiida_class,))
        else:

            # Similarly, check that id is an integer
            if not isinstance(node_id, int):
                raise RestValidationError('parameter id has to be an integer')

            identifier_type = IdentifierType.ID
            qbobj, _ = loader.get_query_builder(node_id, identifier_type, sub_classes=(self._aiida_class,))

        # For efficiency I don't go further than two results
        qbobj.limit(2)

        try:
            pk = qbobj.one()[0].pk
        except MultipleObjectsError:
            raise RestValidationError("More than one node found." " Provide longer starting pattern" " for id.")
        except NotExistent:
            raise RestValidationError("either no object's id starts"
                                      " with '{}' or the corresponding object"
                                      " is not of type aiida.orm.{}".format(node_id, self._aiida_type))
        else:
            # create a permanent filter
            self._id_filter = {'id': {'==': pk}}
            return True
