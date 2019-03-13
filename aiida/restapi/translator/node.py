# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Translator for node"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from aiida.common.exceptions import InputValidationError, ValidationError, \
    InvalidOperation
from aiida.restapi.common.exceptions import RestValidationError
from aiida.restapi.translator.base import BaseTranslator
from aiida.manage.manager import get_manager
from aiida import orm


class NodeTranslator(BaseTranslator):
    # pylint: disable=too-many-instance-attributes,anomalous-backslash-in-string,too-many-arguments,too-many-branches,fixme
    """
    Translator relative to resource 'nodes' and aiida class Node
    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = "nodes"
    # The AiiDA class one-to-one associated to the present class
    _aiida_class = orm.Node
    # The string name of the AiiDA class
    _aiida_type = "node.Node"
    # The string associated to the AiiDA class in the query builder lexicon
    _qb_type = _aiida_type + '.'

    # If True (False) the corresponding AiiDA class has (no) uuid property
    _has_uuid = True

    _result_type = __label__

    _content_type = None

    _alist = None
    _nalist = None
    _elist = None
    _nelist = None
    _downloadformat = None
    _visformat = None
    _filename = None
    _rtype = None

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

        self._default_projections = [
            "id", "label", "node_type", "ctime", "mtime", "uuid", "user_id", "user_email", "attributes", "extras"
        ]

        ## node schema
        # All the values from column_order must present in additional info dict
        # Note: final schema will contain details for only the fields present in column order
        self._schema_projections = {
            "column_order":
            ["id", "label", "node_type", "ctime", "mtime", "uuid", "user_id", "user_email", "attributes", "extras"],
            "additional_info": {
                "id": {
                    "is_display": True
                },
                "label": {
                    "is_display": False
                },
                "node_type": {
                    "is_display": True
                },
                "ctime": {
                    "is_display": True
                },
                "mtime": {
                    "is_display": True
                },
                "uuid": {
                    "is_display": False
                },
                "user_id": {
                    "is_display": False
                },
                "user_email": {
                    "is_display": True
                },
                "attributes": {
                    "is_display": False
                },
                "extras": {
                    "is_display": False
                }
            }
        }

        # Inspect the subclasses of NodeTranslator, to avoid hard-coding
        # (should resemble the following tree)
        """
                                          /- KpointsTranslator
                                         /
                         /- DataTranslator  -- SructureTranslator
                        /                \
                                          \- BandsTranslator
        NodeTranslator  -- CodeTranslator
                        \
                         \- CalculationTranslator
        """

        self._subclasses = self._get_subclasses()
        self._backend = get_manager().get_backend()

    def set_query_type(self,
                       query_type,
                       alist=None,
                       nalist=None,
                       elist=None,
                       nelist=None,
                       downloadformat=None,
                       visformat=None,
                       filename=None,
                       rtype=None):
        """
        sets one of the mutually exclusive values for self._result_type and
        self._content_type.

        :param query_type:(string) the value assigned to either variable.
        """

        if query_type == "default":
            pass
        elif query_type == "inputs":
            self._result_type = 'with_outgoing'
        elif query_type == "outputs":
            self._result_type = "with_incoming"
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
            self._visformat = visformat
        elif query_type == 'download':
            self._content_type = 'download'
            self._downloadformat = downloadformat
        elif query_type == "retrieved_inputs":
            self._content_type = 'retrieved_inputs'
            self._filename = filename
            self._rtype = rtype
        elif query_type == "retrieved_outputs":
            self._content_type = 'retrieved_outputs'
            self._filename = filename
            self._rtype = rtype
        else:
            raise InputValidationError("invalid result/content value: {}".format(query_type))

        # Add input/output relation to the query help
        if self._result_type != self.__label__:
            self._query_help["path"].append({
                "entity_type": ("node.Node.", "data.Data."),
                "tag": self._result_type,
                self._result_type: self.__label__
            })

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

        ## Check the compatibility of query_type and id
        if query_type != "default" and id is None:
            raise ValidationError("non default result/content can only be "
                                  "applied to a specific node (specify an id)")

        ## Set the type of query
        self.set_query_type(
            query_type,
            alist=alist,
            nalist=nalist,
            elist=elist,
            nelist=nelist,
            downloadformat=downloadformat,
            visformat=visformat,
            filename=filename,
            rtype=rtype)

        ## Define projections
        if self._content_type is not None:
            # Use '*' so that the object itself will be returned.
            # In get_results() we access attributes/extras by
            # calling the attributes/extras.
            projections = ['*']
        else:
            pass  # i.e. use the input parameter projection

        # TODO this actually works, but the logic is a little bit obscure.
        # Make it clearer
        if self._result_type is not self.__label__:
            projections = self._default_projections

        super(NodeTranslator, self).set_query(filters=filters, orders=orders, projections=projections, node_id=node_id)

    def _get_content(self):
        """
        Used by get_results() in case of endpoint include "content" option
        :return: data: a dictionary containing the results obtained by
        running the query
        """
        if not self._is_qb_initialized:
            raise InvalidOperation("query builder object has not been initialized.")

        ## Count the total number of rows returned by the query (if not
        # already done)
        if self._total_count is None:
            self.count()

        # If count==0 return
        if self._total_count == 0:
            return {}

        # otherwise ...
        node = self.qbobj.first()[0]

        # content/attributes
        if self._content_type == "attributes":
            # Get all attrs if nalist and alist are both None
            if self._alist is None and self._nalist is None:
                data = {self._content_type: node.attributes}
            # Get all attrs except those contained in nalist
            elif self._alist is None and self._nalist is not None:
                attrs = {}
                for key in node.attributes.keys():
                    if key not in self._nalist:
                        attrs[key] = node.get_attribute(key)
                data = {self._content_type: attrs}
            # Get all attrs contained in alist
            elif self._alist is not None and self._nalist is None:
                attrs = {}
                for key in node.attributes.keys():
                    if key in self._alist:
                        attrs[key] = node.get_attribute(key)
                data = {self._content_type: attrs}
            else:
                raise RestValidationError("you cannot specify both alist and nalist")
        # content/extras
        elif self._content_type == "extras":

            # Get all extras if nelist and elist are both None
            if self._elist is None and self._nelist is None:
                data = {self._content_type: node.extras}

            # Get all extras except those contained in nelist
            elif self._elist is None and self._nelist is not None:
                extras = {}
                for key in node.extras.keys():
                    if key not in self._nelist:
                        extras[key] = node.get_extra(key)
                data = {self._content_type: extras}

            # Get all extras contained in elist
            elif self._elist is not None and self._nelist is None:
                extras = {}
                for key in node.extras.keys():
                    if key in self._elist:
                        extras[key] = node.get_extra(key)
                data = {self._content_type: extras}

            else:
                raise RestValidationError("you cannot specify both elist and nelist")

        # Data needed for visualization appropriately serialized (this
        # actually works only for data derived classes)
        # TODO refactor the code so to have this option only in data and
        # derived classes
        elif self._content_type == 'visualization':
            # In this we do not return a dictionary but just an object and
            # the dictionary format is set by get_visualization_data
            data = {self._content_type: self.get_visualization_data(node, self._visformat)}

        elif self._content_type == 'download':
            # In this we do not return a dictionary but download the file in
            # specified format if available
            data = {self._content_type: self.get_downloadable_data(node, self._downloadformat)}

        elif self._content_type == 'retrieved_inputs':
            # This type is only available for calc nodes. In case of job calc it
            # returns calc inputs prepared to submit calc on the cluster else []
            data = {self._content_type: self.get_retrieved_inputs(node, self._filename, self._rtype)}

        elif self._content_type == 'retrieved_outputs':
            # This type is only available for calc nodes. In case of job calc it
            # returns calc outputs retrieved from the cluster else []
            data = {self._content_type: self.get_retrieved_outputs(node, self._filename, self._rtype)}

        else:
            raise ValidationError("invalid content type")

        return data

    def _get_subclasses(self, parent=None, parent_class=None, recursive=True):
        """
        Import all submodules of the package containing the present class.
        Includes subpackages recursively, if specified.

        :param parent: package/class.
            If package looks for the classes in submodules.
            If class, first lookss for the package where it is contained
        :param parent_class: class of which to look for subclasses
        :param recursive: True/False (go recursively into submodules)
        """

        import pkgutil
        import imp
        import inspect
        import os

        # If no parent class is specified set it to self.__class
        parent = self.__class__ if parent is None else parent

        # Suppose parent is class
        if inspect.isclass(parent):

            # Set the package where the class is contained
            classfile = inspect.getfile(parent)
            package_path = os.path.dirname(classfile)

            # If parent class is not specified, assume it is the parent
            if parent_class is None:
                parent_class = parent

        # Suppose parent is a package (directory containing __init__.py).
        # Check if it contains attribute __path__
        elif inspect.ismodule(parent) and hasattr(parent, '__path__'):

            # Assume path is one element list
            package_path = parent.__path__[0]

            # if parent is a package, parent_class cannot be None
            if parent_class is None:
                raise TypeError('argument parent_class cannot be None')

                # Recursively check the subpackages
        results = {}

        for _, name, is_pkg in pkgutil.walk_packages([package_path]):
            # N.B. pkgutil.walk_package requires a LIST of paths.

            full_path_base = os.path.join(package_path, name)

            if is_pkg:
                app_module = imp.load_package(full_path_base, full_path_base)
            else:
                full_path = full_path_base + '.py'
                # I could use load_module but it takes lots of arguments,
                # then I use load_source
                app_module = imp.load_source("rst" + name, full_path)

            # Go through the content of the module
            if not is_pkg:
                for fname, obj in inspect.getmembers(app_module):
                    if inspect.isclass(obj) and issubclass(obj, parent_class):
                        results[fname] = obj
            # Look in submodules
            elif is_pkg and recursive:
                results.update(self._get_subclasses(parent=app_module, parent_class=parent_class))

        return results

    def get_visualization_data(self, node, visformat=None):
        """
        Generic function to get the data required to visualize the node with
        a specific plugin.
        Actual definition is in child classes as the content to be be
        returned and its format depends on the visualization plugin specific
        to the resource

        :param node: node object that has to be visualized
        :param visformat: visualization format
        :returns: data selected and serialized for visualization

        If this method is called by Node resource it will look for the type
        of object and invoke the correct method in the lowest-compatibel
        subclass
        """

        # Look for the translator associated to the class of which this node
        # is instance
        tclass = type(node)

        for subclass in self._subclasses.values():
            if subclass._aiida_type.split('.')[-1] == tclass.__name__:  # pylint: disable=protected-access
                lowtrans = subclass

        visualization_data = lowtrans.get_visualization_data(node, visformat=visformat)

        return visualization_data

    def get_downloadable_data(self, node, download_format=None):
        """
        Generic function to download file in specified format.
        Actual definition is in child classes as the content to be
        returned and its format depends on the visualization plugin specific
        to the resource

        :param node: node object
        :param download_format: file extension format
        :returns: data in selected format to download

        If this method is called by Node resource it will look for the type
        of object and invoke the correct method in the lowest-compatibel
        subclass
        """

        # Look for the translator associated to the class of which this node
        # is instance
        tclass = type(node)

        for subclass in self._subclasses.values():
            if subclass._aiida_type.split('.')[-1] == tclass.__name__:  # pylint: disable=protected-access
                lowtrans = subclass

        downloadable_data = lowtrans.get_downloadable_data(node, download_format=download_format)

        return downloadable_data

    @staticmethod
    def get_retrieved_inputs(node, filename=None, rtype=None):
        """
        Generic function to return output of calc inputls verdi command.
        Actual definition is in child classes as the content to be
        returned and its format depends on the visualization plugin specific
        to the resource

        :param node: node object
        :returns: list of calc inputls command
        """
        # pylint: disable=unused-argument
        return []

    @staticmethod
    def get_retrieved_outputs(node, filename=None, rtype=None):
        """
        Generic function to return output of calc outputls verdi command.
        Actual definition is in child classes as the content to be
        returned and its format depends on the visualization plugin specific
        to the resource

        :param node: node object
        :returns: list of calc outputls command
        """
        # pylint: disable=unused-argument
        return []

    @staticmethod
    def get_file_content(node, file_name):
        """
        It reads the file from directory and returns its content.

        Instead of using "send_from_directory" from flask, this method is written
        because in next aiida releases the file can be stored locally or in object storage.

        :param node: aiida folderData node which contains file
        :param file_name: name of the file to return its contents
        :return:
        """
        import os
        file_parts = file_name.split(os.sep)

        if len(file_parts) > 1:
            file_name = file_parts.pop()
            for folder in file_parts:
                node = node.get_subfolder(folder)

        with node.open(file_name) as fobj:
            return fobj.read()

    def get_results(self):
        """
        Returns either a list of nodes or details of single node from database

        :return: either a list of nodes or the details of single node
            from the database
        """
        if self._content_type is not None:
            return self._get_content()

        return super(NodeTranslator, self).get_results()

    def get_statistics(self, user_pk=None):
        """Return statistics for a given node"""

        qmanager = self._backend.query_manager
        return qmanager.get_creation_statistics(user_pk=user_pk)

    def get_io_tree(self, uuid_pattern, tree_in_limit, tree_out_limit):
        # pylint: disable=too-many-statements,too-many-locals
        """
        json data to display nodes in tree format
        :param uuid_pattern: main node uuid
        :return: json data to display node tree
        """
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm import Node

        def get_node_shape(ntype):
            """
            Get tree node shape depending on node type
            :param ntype: node type
            :return: shape of the node displayed in tree
            """

            node_type = ntype.split(".")[0]

            # default and data node shape
            shape = "dot"

            if node_type == "calculation":
                shape = "square"
            elif node_type == "code":
                shape = "triangle"

            return shape

        # Check whether uuid_pattern identifies a unique node
        self._check_id_validity(uuid_pattern)

        qb_obj = QueryBuilder()
        qb_obj.append(Node, tag="main", project=["*"], filters=self._id_filter)

        nodes = []
        edges = []
        node_count = 0

        if qb_obj.count() > 0:
            main_node = qb_obj.first()[0]
            pk = main_node.pk
            uuid = main_node.uuid
            nodetype = main_node.node_type
            nodelabel = main_node.label
            display_type = nodetype.split('.')[-2]
            description = main_node.get_description()
            if description == '':
                description = main_node.node_type.split('.')[-2]

            nodes.append({
                "id": node_count,
                "nodeid": pk,
                "nodeuuid": uuid,
                "nodetype": nodetype,
                "nodelabel": nodelabel,
                "displaytype": display_type,
                "group": "main_node",
                "description": description,
                "shape": get_node_shape(nodetype)
            })
        node_count += 1

        # get all inputs
        qb_obj = QueryBuilder()
        qb_obj.append(Node, tag="main", project=['*'], filters=self._id_filter)
        qb_obj.append(Node, tag="in", project=['*'], edge_project=['label', 'type'], with_outgoing='main')
        if tree_in_limit is not None:
            qb_obj.limit(tree_in_limit)

        input_node_pks = {}
        sent_no_of_incomings = qb_obj.count()

        if sent_no_of_incomings > 0:
            for node_input in qb_obj.iterdict():
                node = node_input['in']['*']
                pk = node.pk
                linklabel = node_input['main--in']['label']
                linktype = node_input['main--in']['type']

                # add node if it is not present
                if pk not in input_node_pks.keys():
                    input_node_pks[pk] = node_count
                    uuid = node.uuid
                    nodetype = node.node_type
                    nodelabel = node.label
                    display_type = nodetype.split('.')[-2]
                    description = node.get_description()
                    if description == '':
                        description = node.node_type.split('.')[-2]

                    nodes.append({
                        "id": node_count,
                        "nodeid": pk,
                        "nodeuuid": uuid,
                        "nodetype": nodetype,
                        "nodelabel": nodelabel,
                        "displaytype": display_type,
                        "group": "inputs",
                        "description": description,
                        "linklabel": linklabel,
                        "linktype": linktype,
                        "shape": get_node_shape(nodetype)
                    })
                    node_count += 1

                from_edge = input_node_pks[pk]
                edges.append({
                    "from": from_edge,
                    "to": 0,
                    "arrows": "to",
                    "color": {
                        "inherit": 'from'
                    },
                    "linktype": linktype,
                })

        # get all outputs
        qb_obj = QueryBuilder()
        qb_obj.append(Node, tag="main", project=['*'], filters=self._id_filter)
        qb_obj.append(Node, tag="out", project=['*'], edge_project=['label', 'type'], with_incoming='main')
        if tree_out_limit is not None:
            qb_obj.limit(tree_out_limit)

        output_node_pks = {}
        sent_no_of_outgoings = qb_obj.count()

        if sent_no_of_outgoings > 0:
            for output in qb_obj.iterdict():
                node = output['out']['*']
                pk = node.pk
                linklabel = output['main--out']['label']
                linktype = output['main--out']['type']

                # add node if it is not present
                if pk not in output_node_pks.keys():
                    output_node_pks[pk] = node_count
                    uuid = node.uuid
                    nodetype = node.node_type
                    nodelabel = node.label
                    display_type = nodetype.split('.')[-2]
                    description = node.get_description()
                    if description == '':
                        description = node.node_type.split('.')[-2]

                    nodes.append({
                        "id": node_count,
                        "nodeid": pk,
                        "nodeuuid": uuid,
                        "nodetype": nodetype,
                        "nodelabel": nodelabel,
                        "displaytype": display_type,
                        "group": "outputs",
                        "description": description,
                        "linklabel": linklabel,
                        "linktype": linktype,
                        "shape": get_node_shape(nodetype)
                    })
                    node_count += 1

                to_edge = output_node_pks[pk]
                edges.append({
                    "from": 0,
                    "to": to_edge,
                    "arrows": "to",
                    "color": {
                        "inherit": 'to'
                    },
                    "linktype": linktype
                })

        # count total no of nodes
        builder = QueryBuilder()
        builder.append(Node, tag="main", project=['id'], filters=self._id_filter)
        builder.append(Node, tag="in", project=['id'], input_of='main')
        total_no_of_incomings = builder.count()

        builder = QueryBuilder()
        builder.append(Node, tag="main", project=['id'], filters=self._id_filter)
        builder.append(Node, tag="out", project=['id'], output_of='main')
        total_no_of_outgoings = builder.count()

        return {
            "nodes": nodes,
            "edges": edges,
            "total_no_of_incomings": total_no_of_incomings,
            "total_no_of_outgoings": total_no_of_outgoings,
            "sent_no_of_incomings": sent_no_of_incomings,
            "sent_no_of_outgoings": sent_no_of_outgoings
        }
