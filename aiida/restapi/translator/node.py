from aiida.restapi.translator.base import BaseTranslator
# from aiida.restapi import caching
from aiida.common.exceptions import InputValidationError, ValidationError, \
    InvalidOperation
from aiida.restapi.common.exceptions import RestValidationError


class NodeTranslator(BaseTranslator):
    """
    It prepares the query_help from user inputs which later will be
    passed to QueryBuilder to get either the list of Nodes or the
    details of one node

    Supported REST requests:
    - http://base_url/node?filters
    - http://base_url/node/pk
    - http://base_url/node/pk/io/inputs
    - http://base_url/node/pk/io/outputs
    - http://base_url/node/pk/content/attributes
    - http://base_url/node/pk/content/extras

    **Please NOTE that filters are allowed ONLY in first resuest to
    get nodes list

    Pk         : pk of the node
    Filters    : filters dictionary to apply on
                 nodes list. Not applicable to single node.
    order_by   : used to sort nodes list. Not applicable to
                 single node
    end_points : io/inputs, io/outputs, content/attributes, content/extras
    query_help : (TODO)
    kwargs: extra parameters if any.

    **Return: list of nodes or details of single node

    EXAMPLES:
    ex1:: get single node details
    ct = NodeTranslator()
    ct.set_filters(pk)
    _query_help = ct.get__query_help()
    qb = QueryBuilder(**_query_help)
    data = ct.formatted_result(qb)

    ex2:: get list of nodes (use filters)
    ct = NodeTranslator()
    ct.set_filters(filters_dict)
    _query_help = ct.get__query_help()
    qb = QueryBuilder(**_query_help)
    data = ct.get_formatted_result(qb)

    ex3:: get node inputs
    ct = NodeTranslator()
    ct.get_inputs(pk)
    results_type = "inputs"
    ct.set_filters(filters_dict)
    _query_help = ct.get__query_help()
    qb = QueryBuilder(**_query_help)
    data = ct.get_formatted_result(qb, results_type)

    ex4:: get node outputs
    ct = NodeTranslator()
    ct.get_outputs(pk)
    results_type = "outputs"
    ct.set_filters(filters_dict)
    _query_help = ct.get__query_help()
    qb = QueryBuilder(**_query_help)
    data = ct.get_formatted_result(qb, results_type)

    """
    _aiida_type = "Node"
    _qb_type = "node.Node."
    _qb_label = "nodes  "
    _result_type = _qb_label
    _content_type = None
    _default_projections = ['id',
                   'label',
                   'type',
                   'state',
                   'ctime',
                   'mtime',
                   'uuid'
                   ]
    _alist = None
    _nalist = None
    _elist = None
    _nelist = None

    def __init__(self):
        """
        Initialise the parameters.
        Create the basic query_help
        """
        # basic query_help object
        super(NodeTranslator, self).__init__()


    def set_query_type(self, query_type, alist=None, nalist=None, elist=None,
                       nelist=None):
        """
        sets one of the mutually exclusive values for self._result_type and
        self._content_type.
        :param query_type:(string) the value assigned to either variable.
        """

        if query_type == "default":
            pass
        elif query_type == "inputs":
            self._result_type = 'input_of'
        elif query_type == "outputs":
            self._result_type = "output_of"
        elif query_type == "attributes":
            self._content_type = "attributes"
            self._alist = alist
            self._nalist = nalist
        elif query_type == "extras":
            self._content_type = "extras"
            self._elist = elist
            self._nelist = nelist
        else:
            raise InputValidationError("invalid result/content value: {"
                                       "}".format(query_type))

        ## Add input/output relation to the query help
        if self._result_type is not self._qb_label:
            self._query_help["path"].append(
                {
                "type": "node.Node.",
                "label": self._result_type,
                self._result_type: self._qb_label
                })


    def set_query(self, filters=None, orders=None, projections=None,
                  query_type=None, pk=None, alist=None, nalist=None,
                  elist=None, nelist=None):
        """
        Adds filters, default projections, order specs to the query_help,
        and initializes the qb object

        :param filters: dictionary with the filters
        :param orders: dictionary with the order for each tag
        :param projections: dictionary with the projection. It is discarded
        if query_type=='attributes'/'extras'
        :param query_type: (string) specify the result or the content (
        "attr")
        :param pk: (integer) pk of a specific node
        """

        ## Check the compatibility of query_type and pk
        if query_type is not "default" and pk is None:
            raise ValidationError("non default result/content can only be "
                                  "applied to a specific pk")

        ## Set the type of query
        self.set_query_type(query_type, alist=alist, nalist=nalist,
                            elist=elist, nelist=nelist)

        ## Define projections
        if self._content_type is not None:
            # Use '*' so that the object itself will be returned.
            # In get_results() we access attributes/extras by
            # calling the get_attrs()/get_extras().
            projections = ['*']
        else:
            pass #i.e. use the input parameter projection

        ## TODO this actually works, but the logic is a little bit obscure.
        # Make it clearer
        if self._result_type is not self._qb_label:
            projections = self._default_projections

        super(NodeTranslator, self).set_query(filters=filters,
                                              orders=orders,
                                              projections=projections,
                                              pk=pk)


    def _get_content(self):
        """
        Used by get_results() in case of endpoint include "content" option
        :return: data: a dictionary containing the results obtained by
        running the query
        """
        if not self._is_qb_initialized:
            raise InvalidOperation("query builder object has not been "
                                    "initialized.")

        ## Initialization
        data = {}

        ## Count the total number of rows returned by the query (if not
        # already done)
        if self._total_count is None:
            self.count()

        if self._total_count > 0:
            n = self.qb.first()[0]
            if self._content_type == "attributes":
                # Get all attrs if nalist and alist are both None
                if self._alist is None and self._nalist is None:
                    data[self._content_type] = n.get_attrs()
                # Get all attrs except those contained in nalist
                elif self._alist is None and self._nalist is not None:
                    attrs = {}
                    for key in n.get_attrs().keys():
                        if key not in self._nalist:
                            attrs[key] = n.get_attr(key)
                    data[self._content_type] = attrs
                # Get all attrs contained in alist
                elif self._alist is not None and self._nalist is None:
                    attrs = {}
                    for key in n.get_attrs().keys():
                        if key in self._alist:
                            attrs[key] = n.get_attr(key)
                    data[self._content_type] = attrs
                else:
                    raise RestValidationError("you cannot specify both alist "
                                              "and nalist")
            elif self._content_type == "extras":
                # Get all extras if nelist and elist are both None
                if self._elist is None and self._nelist is None:
                    data[self._content_type] = n.get_extras()
                # Get all extras except those contained in nelist
                elif self._elist is None and self._nelist is not None:
                    extras = {}
                    for key in n.get_extras().keys():
                        if key not in self._nelist:
                            extras[key] = n.get_extra(key)
                    data[self._content_type] = extras
                # Get all extras contained in elist
                elif self._elist is not None and self._nelist is None:
                    extras = {}
                    for key in n.get_extras().keys():
                        if key in self._elist:
                            extras[key] = n.get_extra(key)
                    data[self._content_type] = extras
                else:
                    raise RestValidationError("you cannot specify both elist "
                                              "and nelist")
            else:
                raise ValidationError("invalid content type")
                # Default case
        else:
            pass

        return data

    def get_results(self):
        """
        Returns either a list of nodes or details of single node from database

        :return: either a list of nodes or the details of single node
        from the database
        """
        if self._content_type is not None:
            return self._get_content()
        else:
            return super(NodeTranslator, self).get_results()

    def get_statistics(self, tclass, user=""):
       from aiida.orm.querybuilder import QueryBuilder as QB
       from aiida.orm import User
       from collections import Counter
       from datetime import datetime

       statistics = {}

       q = QB()
       q.append(tclass, project=['id', 'ctime', 'mtime', 'type'], tag='node')
       q.append(User, creator_of='node', project='email')
       res = q.all()

       # total count
       statistics["total"] = len(res)

       users = Counter([r[4] for r in res])
       statistics["users"]={}

       if user is not "":
           statistics["users"][user] = users[user]
       else:
           for count, email in sorted((v, k) for k, v in users.iteritems())[::-1]:
               statistics["users"][email] = count

       types = Counter([r[3] for r in res])
       statistics["types"] = {}
       for count, typestring in sorted((v, k) for k, v in types.iteritems())[::-1]:
           statistics["types"][typestring] = count

       ctimelist = [r[1].strftime("%Y-%m") for r in res]
       ctime = Counter(ctimelist)
       statistics["ctime_by_month"] = {}
       for count, period in sorted((v, k) for k, v in ctime.iteritems())[::-1]:
           statistics["ctime_by_month"][period] = count

       ctimelist = [r[1].strftime("%Y-%m-%d") for r in res]
       ctime = Counter(ctimelist)
       statistics["ctime_by_day"] = {}
       for count, period in sorted((v, k) for k, v in ctime.iteritems())[::-1]:
           statistics["ctime_by_day"][period] = count

       mtimelist = [r[1].strftime("%Y-%m") for r in res]
       mtime = Counter(mtimelist)
       statistics["mtime_by_month"] = {}
       for count, period in sorted((v, k) for k, v in mtime.iteritems())[::-1]:
           statistics["mtime_by_month"][period] = count

       mtimelist = [r[1].strftime("%Y-%m-%d") for r in res]
       mtime = Counter(mtimelist)
       statistics["mtime_by_day"] = {}
       for count, period in sorted((v, k) for k, v in mtime.iteritems())[::-1]:
           statistics["mtime_by_day"][period] = count

       return statistics
