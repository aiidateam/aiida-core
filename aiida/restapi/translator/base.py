from aiida.common.exceptions import InputValidationError, InvalidOperation
# from aiida.restapi import caching
from aiida.orm.querybuilder import QueryBuilder
from aiida.restapi.common.exceptions import RestValidationError, RestInputValidationError
from aiida.restapi.common.config import LIMIT_DEFAULT


class BaseTranslator(object):
    """
    Generic class for translator. It also contains all methods
    required to build QueryBuilder object
    """

    _aiida_type = None
    _qb_type = None
    _qb_label = None
    _result_type = _qb_label
    _default_projections = []
    _pk_dbsynonym = "id"
    _is_qb_initialized = False
    _is_pk_query = None
    _total_count = None

    def __init__(self):
        """
        Initialise the parameters.
        Create the basic query_help
        """
        # basic query_help object
        self._query_help = {
            "path": [{
                "type": self._qb_type,
                "label": self._qb_label
            }],
            "filters": {},
            "project": {},
            "order_by": {}
        }
        # query_builder object (No initialization)
        self.qb = QueryBuilder()

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
                                filter_key = self._pk_dbsynonym
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
        self.set_projections({self._qb_label: self._default_projections})


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
                order_dict[self._pk_dbsynonym] = order_dict.pop('pk')
            return order_dict

        ## Assign orderby field query_help
        for tag, columns in orders.iteritems():
            self._query_help['order_by'][tag] = def_order(columns)




        # if isinstance(orders, dict):
        #     if len(orders) > 0:
        #         for tag, tag_orders in orders.iteritems():
        #             print tag, tag_orders
        #             if len(tag_orders) > 0 and isinstance(tag_orders, dict):
        #                 self.query_help["order_by"][tag] = {}
        #                 for order_key, order_value in tag_orders.iteritems():
        #                     if order_key == "pk":
        #                         order_key = self._pk_dbsynonym
        #                     self.query_help["filters"][tag][order_key] \
        #                         = order_value
        # else:
        #     raise InputValidationError("Pass data in dictionary format where "
        #                                 "keys are the tag names given in the "
        #                                 "path in query_help and and their values"
        #                                 " are the dictionary of orders want "
        #                                 "to add for that tag name.")


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
            if self._result_type==self._qb_label and len(filters)>0:
                raise RestInputValidationError("selecting a specific pk does "
                                              "not "
                                           "allow to specify filters")
            elif not self._check_pk_validity(pk):
                raise RestValidationError("either the selected pk does not exist "
                                       "or the corresponding object is not of "
                                       "type {}".format(self._aiida_type))
            else:
                tagged_filters[self._qb_label] = {'id': {'==': pk}}
                if self._result_type is not self._qb_label:
                    tagged_filters[self._result_type] = filters
        else:
            tagged_filters[self._qb_label] = filters

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
            if limit > LIMIT_DEFAULT:
                raise RestValidationError("Limit and perpage cannot be bigger "
                                          "than {}".format(LIMIT_DEFAULT))
        else:
            limit = LIMIT_DEFAULT

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

        data = []

        if self._total_count>0:
            for tmp in self.qb.iterdict():
                data.append(tmp[label])

        return data


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
        Checks whether a pk corresponds to an object of the expected type
        :param pk: (integer) ok to check
        :return: True or False
        """
        # The logic could be to load the node or to use querybuilder. Let's
        # do with qb for consistency, although it would be easier to do it
        # with load_node

        query_help_base = {'path':[
                                {
                                'type': self._qb_type,
                                'label': self._qb_label,
                                },
                            ],
                      'filters': {self._qb_label:
                                      {'id': {'==': pk}
                                       }
                                  }
                      }

        qb_base = QueryBuilder(**query_help_base)
        return qb_base.count()==1
