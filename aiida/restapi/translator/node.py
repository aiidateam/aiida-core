from aiida.common.exceptions import InputValidationError, ValidationError, \
    InvalidOperation
from aiida.restapi.common.exceptions import RestValidationError
from aiida.restapi.translator.base import BaseTranslator


class NodeTranslator(BaseTranslator):
    """
    TODO add docstring

    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = "nodes"
    # The string name of the AiiDA class one-to-one associated to the present
    #  class
    _aiida_type = "node.Node"
    # The string associated to the AiiDA class in the query builder lexicon
    _qb_type = _aiida_type + '.'

    _result_type = __label__

    _content_type = None

    _alist = None
    _nalist = None
    _elist = None
    _nelist = None

    def __init__(self, Class=None, **kwargs):
        """
        Initialise the parameters.
        Create the basic query_help
        """

        # Assume default class is this class (cannot be done in the
        # definition as it requires self)
        if Class is None:
            Class = self.__class__

        # basic initialization
        super(NodeTranslator, self).__init__(Class=Class, **kwargs)

        # Extract the default projections from custom_schema if they are defined
        if self.custom_schema is not None and 'columns' in self.custom_schema:
            self._default_projections = self.custom_schema['columns'][
                self.__label__]
        else:
            self._default_projections = ['**']

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
        elif query_type == 'visualization':
            self._content_type = 'visualization'
        else:
            raise InputValidationError("invalid result/content value: {"
                                       "}".format(query_type))

        ## Add input/output relation to the query help
        if self._result_type is not self.__label__:
            self._query_help["path"].append(
                {
                    "type": "node.Node.",
                    "label": self._result_type,
                    self._result_type: self.__label__
                })

    def set_query(self, filters=None, orders=None, projections=None,
                  query_type=None, id=None, alist=None, nalist=None,
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
        :param id: (integer) id of a specific node
        """

        ## Check the compatibility of query_type and id
        if query_type is not "default" and id is None:
            raise ValidationError("non default result/content can only be "
                                  "applied to a specific node (specify an id)")

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
            pass  # i.e. use the input parameter projection

        # TODO this actually works, but the logic is a little bit obscure.
        # Make it clearer
        if self._result_type is not self.__label__:
            projections = self._default_projections

        super(NodeTranslator, self).set_query(filters=filters,
                                              orders=orders,
                                              projections=projections,
                                              id=id)

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

        # If count==0 return
        if self._total_count == 0:
            return data

        # otherwise ...
        n = self.qb.first()[0]

        # content/attributes
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
        # content/extras
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

        # Data needed for visualization appropriately serialized (this
        # actually works only for data derived classes)
        # TODO refactor the code so to have this option only in data and
        # derived classes
        elif self._content_type == 'visualization':
            data[self._content_type] = self.get_visualization_data(n)

        else:
            raise ValidationError("invalid content type")

        return data

    def get_visualization_data(self, node):
        """
        Generic function to get the data required to visualize the node with
        a specific plugin.
        Actual definition is in child classes as the content to be be
        returned and its format depends on the visualization plugin specific
        to the resource

        :param node: node object that has to be visualized
        :returns: data selected and serializaed for visualization
        """
        pass

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


    # TODO this works but has to be rewritten once group_by is available in
    # querybuilder
    def get_statistics(self, tclass, users=[]):
        from aiida.orm.querybuilder import QueryBuilder as QB
        from aiida.orm import User
        from collections import Counter

        def count_statistics(dataset):

            def get_statistics_dict(dataset):
                results = {}
                for count, typestring in sorted(
                        (v, k) for k, v in dataset.iteritems())[::-1]:
                    results[typestring] = count
                return results

            count_dict = {}

            types = Counter([r[3] for r in dataset])
            count_dict["types"] = get_statistics_dict(types)

            ctimelist = [r[1].strftime("%Y-%m") for r in dataset]
            ctime = Counter(ctimelist)
            count_dict["ctime_by_month"] = get_statistics_dict(ctime)

            ctimelist = [r[1].strftime("%Y-%m-%d") for r in dataset]
            ctime = Counter(ctimelist)
            count_dict["ctime_by_day"] = get_statistics_dict(ctime)

            mtimelist = [r[2].strftime("%Y-%m") for r in dataset]
            mtime = Counter(ctimelist)
            count_dict["mtime_by_month"] = get_statistics_dict(mtime)

            mtimelist = [r[1].strftime("%Y-%m-%d") for r in dataset]
            mtime = Counter(ctimelist)
            count_dict["mtime_by_day"] = get_statistics_dict(mtime)

            return count_dict

        statistics = {}

        q = QB()
        q.append(tclass, project=['id', 'ctime', 'mtime', 'type'], tag='node')
        q.append(User, creator_of='node', project='email')
        qb_res = q.all()

        # total count
        statistics["total"] = len(qb_res)

        node_users = Counter([r[4] for r in qb_res])
        statistics["users"] = {}

        if isinstance(users, basestring):
            users = [users]
        if len(users) == 0:
            users = node_users

        for user in users:
            user_data = [r for r in qb_res if r[4] == user]
            # statistics for user data
            statistics["users"][user] = count_statistics(user_data)
            statistics["users"][user]["total"] = node_users[user]

        # statistics for node data
        statistics.update(count_statistics(qb_res))

        return statistics

    def get_io_tree(self, nodeId):
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm.node import Node

        nodes = []
        edges = []
        nodeCount = 0

        qb = QueryBuilder()
        qb.append(Node, tag="main", project=["id", "type"],
                  filters={"id": {"==": nodeId}})
        if qb.count() > 0:
            mainNode = qb.first()
            nodes.append({
                             "id": nodeCount,
                             "nodeid": mainNode[0],
                             "nodetype": mainNode[1],
                             "group": "mainNode"
                             })
        nodeCount += 1

        # get all inputs
        qb = QueryBuilder()
        qb.append(Node, tag="main", project=["id", "type"],
                  filters={"id": {"==": nodeId}})
        qb.append(Node, tag="in", project=['id', 'type'], input_of='main')
        if qb.count() > 0:
            for input in qb.iterdict():
                print "in:", input
                nodes.append({
                                 "id": nodeCount,
                                 "nodeid": input["in"]["id"],
                                 "nodetype": input["in"]["type"],
                                 "group": "inputs"
                                 })
                edges.append({
                                 "from": nodeCount,
                                 "to": 0,
                                 "arrows": "to",
                                 "color": {"inherit": 'from'}
                                 })
                nodeCount += 1

        # get all outputs
        qb = QueryBuilder()
        qb.append(Node, tag="main", project=["id", "type"],
                  filters={"id": {"==": nodeId}})
        qb.append(Node, tag="out", project=['id', 'type'], output_of='main')
        if qb.count() > 0:
            for output in qb.iterdict():
                print "in:", output
                nodes.append({
                                 "id": nodeCount,
                                 "nodeid": output["out"]["id"],
                                 "nodetype": output["out"]["type"],
                                 "group": "outputs"
                                 })
                edges.append({
                                 "from": 0,
                                 "to": nodeCount,
                                 "arrows": "to",
                                 "color": {"inherit": 'from'}
                                 })
                nodeCount += 1

        return {"nodes": nodes, "edges": edges}
