# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Translator for node"""
from importlib._bootstrap import _exec, _load
import importlib.machinery
import importlib.util
import inspect
import os
import pkgutil
import sys

from aiida import orm
from aiida.common.exceptions import (
    EntryPointError,
    InputValidationError,
    InvalidOperation,
    LoadingEntryPointError,
    ValidationError,
)
from aiida.manage import get_manager
from aiida.orm import Data, Node
from aiida.plugins.entry_point import get_entry_point_names, load_entry_point
from aiida.restapi.common.exceptions import RestFeatureNotAvailable, RestInputValidationError, RestValidationError
from aiida.restapi.common.identifiers import (
    construct_full_type,
    get_full_type_filters,
    get_node_namespace,
    load_entry_point_from_full_type,
)
from aiida.restapi.translator.base import BaseTranslator


class NodeTranslator(BaseTranslator):
    # pylint: disable=too-many-instance-attributes,anomalous-backslash-in-string,too-many-arguments,too-many-branches,fixme
    """
    Translator relative to resource 'nodes' and aiida class Node
    """

    # A label associated to the present class (coincides with the resource name)
    __label__ = 'nodes'

    # The AiiDA class one-to-one associated to the present class
    _aiida_class = orm.Node

    # The string name of the AiiDA class
    _aiida_type = 'node.Node'

    # If True (False) the corresponding AiiDA class has (no) uuid property
    _has_uuid = True

    _result_type = __label__

    _content_type = None

    _attributes_filter = None
    _extras_filter = None
    _download_format = None
    _download = None
    _filename = None

    def __init__(self, **kwargs):
        """
        Initialise the parameters.
        Create the basic query_help
        """

        # basic initialization
        super().__init__(**kwargs)

        self._default_projections = ['id', 'label', 'node_type', 'process_type', 'ctime', 'mtime', 'uuid', 'user_id']

        # Inspect the subclasses of NodeTranslator, to avoid hard-coding
        # (should resemble the following tree)
        r"""
                                              /- CodeTranslator
                                             /
                                            /- KpointsTranslator
                                           /
                           /- DataTranslator -- StructureTranslator
                          /                \
                         /                  \- BandsTranslator
                        /
        NodeTranslator
                        \
                         \- CalculationTranslator
        """

        self._subclasses = self._get_subclasses()
        self._backend = get_manager().get_profile_storage()

    def set_query_type(
        self,
        query_type,
        attributes_filter=None,
        extras_filter=None,
        download_format=None,
        download=None,
        filename=None
    ):
        """
        sets one of the mutually exclusive values for self._result_type and
        self._content_type.

        :param query_type:(string) the value assigned to either variable.
        """

        if query_type == 'default':
            pass
        elif query_type == 'incoming':
            self._result_type = 'with_outgoing'
        elif query_type == 'outgoing':
            self._result_type = 'with_incoming'
        elif query_type == 'attributes':
            self._content_type = 'attributes'
            self._attributes_filter = attributes_filter
        elif query_type == 'extras':
            self._content_type = 'extras'
            self._extras_filter = extras_filter
        elif query_type == 'derived_properties':
            self._content_type = 'derived_properties'
        elif query_type == 'download':
            self._content_type = 'download'
            self._download_format = download_format
            self._download = download
        elif query_type == 'comments':
            self._content_type = 'comments'
        elif query_type == 'repo_list':
            self._content_type = 'repo_list'
            self._filename = filename
        elif query_type == 'repo_contents':
            self._content_type = 'repo_contents'
            self._filename = filename
        else:
            raise InputValidationError(f'invalid result/content value: {query_type}')

        # Add input/output relation to the query help
        if self._result_type != self.__label__:
            edge_tag = f'{self.__label__}--{self._result_type}'
            self._query_help['path'].append({
                'cls': self._aiida_class,
                'tag': self._result_type,
                'edge_tag': edge_tag,
                self._result_type: self.__label__
            })
            self._query_help['project'][edge_tag] = [{'label': {}}, {'type': {}}]

    def set_query(
        self,
        filters=None,
        orders=None,
        projections=None,
        query_type=None,
        node_id=None,
        download_format=None,
        download=None,
        filename=None,
        attributes=None,
        attributes_filter=None,
        extras=None,
        extras_filter=None,
        full_type=None
    ):
        """
        Adds filters, default projections, order specs to the query_help,
        and initializes the qb object

        :param filters: dictionary with the filters
        :param orders: dictionary with the order for each tag
        :param projections: dictionary with the projection. It is discarded
            if query_type=='attributes'/'extras'
        :param query_type: (string) specify the result or the content ("attr")
        :param id: (integer) id of a specific node
        :param download_format: file format to download e.g. cif, xyz
        :param filename: name of the file to return its content
        :param attributes: flag to show attributes for nodes
        :param attributes_filter: list of attributes to query
        :param extras: flag to show extras for nodes
        :param extras_filter: list of extras to query
        """
        # pylint: disable=arguments-differ, too-many-locals

        ## Check the compatibility of query_type and id
        if query_type != 'default' and id is None:
            raise ValidationError(
                'non default result/content can only be '
                'applied to a specific node (specify an id)'
            )

        ## Set the type of query
        self.set_query_type(
            query_type,
            attributes_filter=attributes_filter,
            extras_filter=extras_filter,
            download_format=download_format,
            download=download,
            filename=filename
        )

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

        if full_type:
            # If full_type is not none, convert it into node_type
            # and process_type filters to pass it to query help
            full_type_filter = get_full_type_filters(full_type)
            filters.update(full_type_filter)

        super().set_query(
            filters=filters,
            orders=orders,
            projections=projections,
            node_id=node_id,
            attributes=attributes,
            attributes_filter=attributes_filter,
            extras=extras,
            extras_filter=extras_filter
        )

    def _get_content(self):
        """
        Used by get_results() in case of endpoint include "content" option
        :return: data: a dictionary containing the results obtained by
        running the query
        """
        # pylint: disable=too-many-statements

        if not self._is_qb_initialized:
            raise InvalidOperation('query builder object has not been initialized.')

        # Count the total number of rows returned by the query (if not already done)
        if self._total_count is None:
            self.count()

        # If count==0 return
        if self._total_count == 0:
            return {}

        # otherwise ...
        node = self.qbobj.first()[0]  # pylint: disable=unsubscriptable-object

        # content/attributes
        if self._content_type == 'attributes':
            # Get all attrs if attributes_filter is None
            if self._attributes_filter is None:
                data = {self._content_type: node.base.attributes.all}
            # Get all attrs contained in attributes_filter
            else:
                attrs = {}
                for key in node.base.attributes.keys():
                    if key in self._attributes_filter:
                        attrs[key] = node.base.attributes.get(key)
                data = {self._content_type: attrs}

        # content/extras
        elif self._content_type == 'extras':
            # Get all extras if elist is None
            if self._extras_filter is None:
                data = {self._content_type: node.base.extras.all}
            else:
                # Get all extras contained in elist
                extras = {}
                for key in node.base.extras.all.keys():
                    if key in self._extras_filter:
                        extras[key] = node.base.extras.get(key)
                data = {self._content_type: extras}

        # Data needed for visualization appropriately serialized (this
        # actually works only for data derived classes)
        # TODO refactor the code so to have this option only in data and
        # derived classes
        elif self._content_type == 'derived_properties':
            data = {self._content_type: self.get_derived_properties(node)}

        elif self._content_type == 'download':
            # In this we do not return a dictionary but download the file in
            # specified format if available
            data = {self._content_type: self.get_downloadable_data(node, self._download_format)}

        elif self._content_type == 'repo_list':
            # return list of all the files and directories from node file repository
            data = {self._content_type: self.get_repo_list(node, self._filename)}

        elif self._content_type == 'repo_contents':
            # return the contents of single file from node file repository
            data = self.get_repo_contents(node, self._filename)

        elif self._content_type == 'comments':
            # return the node comments
            data = {self._content_type: self.get_comments(node)}

        else:
            raise ValidationError('invalid content type')

        return data

    def _get_subclasses(self, parent=None, parent_class=None, recursive=True):
        """
        Import all submodules of the package containing the present class.
        Includes subpackages recursively, if specified.

        :param parent: package/class.
            If package looks for the classes in submodules.
            If class, first looks for the package where it is contained
        :param parent_class: class of which to look for subclasses
        :param recursive: True/False (go recursively into submodules)
        """

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
            # N.B. pkgutil.walk_packages requires a LIST of paths

            full_path_base = os.path.join(package_path, name)
            if is_pkg:
                # re-implementation of deprecated `imp.load_package`
                if os.path.isdir(full_path_base):
                    #Adds an extension to check for __init__ file in the package directory
                    extensions = (importlib.machinery.SOURCE_SUFFIXES[:] + importlib.machinery.BYTECODE_SUFFIXES[:])
                    for extension in extensions:
                        init_path = os.path.join(full_path_base, '__init__' + extension)
                        if os.path.exists(init_path):
                            path = init_path
                            break
                    else:
                        raise ValueError(f'{full_path_base!r} is not a package')
                #passing [] to submodule_search_locations indicates its a package and python searches for sub-modules
                spec = importlib.util.spec_from_file_location(full_path_base, path, submodule_search_locations=[])
                if full_path_base in sys.modules:
                    #executes from sys.modules
                    app_module = _exec(spec, sys.modules[full_path_base])
                else:
                    #loads and executes the module
                    app_module = _load(spec)
            else:
                full_path = f'{full_path_base}.py'
                # reimplementation of deprecated `imp.load_source`
                spec = importlib.util.spec_from_file_location(name, full_path)
                app_module = importlib.util.module_from_spec(spec)
                sys.modules[name] = app_module
                spec.loader.exec_module(app_module)

            # Go through the content of the module
            if not is_pkg:
                for fname, obj in inspect.getmembers(app_module):
                    if inspect.isclass(obj) and issubclass(obj, parent_class):
                        results[fname] = obj
            # Look in submodules
            elif is_pkg and recursive:
                results.update(self._get_subclasses(parent=app_module, parent_class=parent_class))

        return results

    def get_derived_properties(self, node):
        """
        Generic function to get the derived properties of the node.
        Actual definition is in child classes as the content to be
        returned depends on the plugin specific
        to the resource

        :param node: node object that has to be visualized
        :returns: derived properties of the node

        If this method is called by Node resource it will look for the type
        of object and invoke the correct method in the lowest-compatible
        subclass
        """

        # Look for the translator associated to the class of which this node
        # is instance
        tclass = type(node)

        for subclass in self._subclasses.values():
            if subclass._aiida_type.split('.')[-1] == tclass.__name__:  # pylint: disable=protected-access
                lowtrans = subclass

        derived_properties = lowtrans.get_derived_properties(node)

        return derived_properties

    @staticmethod
    def get_all_download_formats(full_type=None):
        """
        returns dict of possible node formats for all available node types
        """

        all_formats = {}

        if full_type:
            try:
                node_cls = load_entry_point_from_full_type(full_type)
            except (TypeError, ValueError):
                raise RestInputValidationError(f'The full type {full_type} is invalid.')
            except EntryPointError:
                raise RestFeatureNotAvailable('The download formats for this node type are not available.')

            try:
                available_formats = node_cls.get_export_formats()
                all_formats[full_type] = available_formats
            except AttributeError:
                pass
        else:
            entry_point_group = 'aiida.data'

            for name in get_entry_point_names(entry_point_group):
                try:
                    node_cls = load_entry_point(entry_point_group, name)
                    available_formats = node_cls.get_export_formats()
                except (AttributeError, LoadingEntryPointError):
                    continue

                if available_formats:
                    full_type = construct_full_type(node_cls.class_node_type, '')
                    all_formats[full_type] = available_formats

        return all_formats

    @staticmethod
    def get_downloadable_data(node, download_format=None):
        """
        Generic function to download file in specified format.
        Actual definition is in child classes as the content to be
        returned and its format depends on the download plugin specific
        to the resource

        :param node: node object
        :param download_format: file extension format
        :returns: data in selected format to download

        If this method is called for a Data node resource it will
        invoke the get_downloadable_data method in the Data transaltor.
        Otherwise it raises RestFeatureNotAvailable exception
        """

        # This needs to be here because currently, for all nodes the `NodeTranslator` will be instantiated. Once that
        # logic is cleaned where the correct translator sub class is instantiated based on the node type that is
        # referenced, this hack can be removed.
        if isinstance(node, Data):
            from .data import DataTranslator  # pylint: disable=cyclic-import
            downloadable_data = DataTranslator.get_downloadable_data(node, download_format=download_format)
            return downloadable_data

        raise RestFeatureNotAvailable('This endpoint is not available for Process nodes.')

    @staticmethod
    def get_repo_list(node, filename=''):
        """
        Every node in AiiDA is having repo folder.
        This function returns the metadata using list_objects() method
        :param node: node object
        :param filename: folder name (optional)
        :return: folder list
        """
        try:
            flist = node.base.repository.list_objects(filename)
        except NotADirectoryError:
            raise RestInputValidationError(f'{filename} is not a directory in this repository')
        response = []
        for fobj in flist:
            response.append({'name': fobj.name, 'type': fobj.file_type.name})
        return response

    @staticmethod
    def get_repo_contents(node, filename=''):
        """
        Every node in AiiDA is having repo folder.
        This function returns the metadata using get_object() method
        :param node: node object
        :param filename: folder or file name (optional)
        :return: file content in bytes to download
        """

        if filename:
            try:
                data = node.base.repository.get_object_content(filename, mode='rb')
                return data
            except FileNotFoundError:
                raise RestInputValidationError('No such file is present')
        raise RestValidationError('filename is not provided')

    @staticmethod
    def get_comments(node):
        """
        :param node: node object
        :return: node comments
        """
        comments = node.base.comments.all()
        response = []
        for cobj in comments:
            response.append({
                'created_time': cobj.ctime,
                'modified_time': cobj.mtime,
                'user': f'{cobj.user.first_name} {cobj.user.last_name}',
                'message': cobj.content
            })
        return response

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

        return super().get_results()

    def get_formatted_result(self, label):
        """
        Runs the query and retrieves results tagged as "label".

        :param label: the tag of the results to be extracted out of
          the query rows.
        :type label: str
        :return: a list of the query results
        """

        results = super().get_formatted_result(label)

        if self._result_type == 'with_outgoing':
            result_name = 'incoming'
        elif self._result_type == 'with_incoming':
            result_name = 'outgoing'
        else:
            result_name = self.__label__

        for node_entry in results[result_name]:
            # construct full_type and add it to every node
            node_entry['full_type'] = (
                construct_full_type(node_entry.get('node_type'), node_entry.get('process_type'))
                if node_entry.get('node_type') or node_entry.get('process_type') else None
            )

        return results

    def get_statistics(self, user_pk=None):
        """Return statistics for a given node"""
        return self._backend.query().get_creation_statistics(user_pk=user_pk)

    @staticmethod
    def get_namespace(user_pk=None, count_nodes=False):
        """
        return full_types of the nodes
        """

        return get_node_namespace(user_pk=user_pk, count_nodes=count_nodes).get_description()

    def get_io_tree(self, uuid_pattern, tree_in_limit, tree_out_limit):
        # pylint: disable=too-many-statements,too-many-locals
        """
        json data to display nodes in tree format
        :param uuid_pattern: main node uuid
        :return: json data to display node tree
        """

        def get_node_description(node):
            """
            Get the description of the node.
            CalcJobNodes migrated from AiiDA < 1.0.0 do not have a valid CalcJobState,
            in this case the function returns as description the type of the node (CalcJobNode)
            :param node: node object
            :return: description of the node
            """
            try:
                description = node.get_description()
            except ValueError:
                description = node.node_type.split('.')[-2]
            return description

        # Check whether uuid_pattern identifies a unique node
        self._check_id_validity(uuid_pattern)

        qb_obj = orm.QueryBuilder()
        qb_obj.append(Node, tag='main', project=['*'], filters=self._id_filter)

        nodes = []

        if qb_obj.count() > 0:
            main_node = qb_obj.first(flat=True)
            pk = main_node.pk
            uuid = main_node.uuid
            nodetype = main_node.node_type
            nodelabel = main_node.label
            description = get_node_description(main_node)
            ctime = main_node.ctime
            mtime = main_node.mtime

            nodes.append({
                'ctime': ctime,
                'mtime': mtime,
                'id': pk,
                'uuid': uuid,
                'node_type': nodetype,
                'node_label': nodelabel,
                'description': description,
                'incoming': [],
                'outgoing': []
            })

        # get all incoming
        qb_obj = orm.QueryBuilder()
        qb_obj.append(Node, tag='main', project=['*'], filters=self._id_filter)
        qb_obj.append(Node, tag='in', project=['*'], edge_project=['label', 'type'],
                      with_outgoing='main').order_by({'in': [{
                          'id': {
                              'order': 'asc'
                          }
                      }]})
        if tree_in_limit is not None:
            qb_obj.limit(tree_in_limit)

        sent_no_of_incomings = qb_obj.count()

        if sent_no_of_incomings > 0:
            for node_input in qb_obj.iterdict():
                node = node_input['in']['*']
                pk = node.pk
                linklabel = node_input['main--in']['label']
                linktype = node_input['main--in']['type']
                uuid = node.uuid
                nodetype = node.node_type
                nodelabel = node.label
                description = get_node_description(node)
                node_ctime = node.ctime
                node_mtime = node.mtime

                nodes[0]['incoming'].append({
                    'ctime': node_ctime,
                    'mtime': node_mtime,
                    'id': pk,
                    'uuid': uuid,
                    'node_type': nodetype,
                    'node_label': nodelabel,
                    'description': description,
                    'link_label': linklabel,
                    'link_type': linktype
                })

        # get all outgoing
        qb_obj = orm.QueryBuilder()
        qb_obj.append(Node, tag='main', project=['*'], filters=self._id_filter)
        qb_obj.append(Node, tag='out', project=['*'], edge_project=['label', 'type'],
                      with_incoming='main').order_by({'out': [{
                          'id': {
                              'order': 'asc'
                          }
                      }]})
        if tree_out_limit is not None:
            qb_obj.limit(tree_out_limit)

        sent_no_of_outgoings = qb_obj.count()

        if sent_no_of_outgoings > 0:
            for output in qb_obj.iterdict():
                node = output['out']['*']
                pk = node.pk
                linklabel = output['main--out']['label']
                linktype = output['main--out']['type']
                uuid = node.uuid
                nodetype = node.node_type
                nodelabel = node.label
                description = get_node_description(node)
                node_ctime = node.ctime
                node_mtime = node.mtime

                nodes[0]['outgoing'].append({
                    'ctime': node_ctime,
                    'mtime': node_mtime,
                    'id': pk,
                    'uuid': uuid,
                    'node_type': nodetype,
                    'node_label': nodelabel,
                    'description': description,
                    'link_label': linklabel,
                    'link_type': linktype
                })

        # count total no of nodes
        builder = orm.QueryBuilder()
        builder.append(Node, tag='main', project=['id'], filters=self._id_filter)
        builder.append(Node, tag='in', project=['id'], with_outgoing='main')
        total_no_of_incomings = builder.count()

        builder = orm.QueryBuilder()
        builder.append(Node, tag='main', project=['id'], filters=self._id_filter)
        builder.append(Node, tag='out', project=['id'], with_incoming='main')
        total_no_of_outgoings = builder.count()

        metadata = [{
            'total_no_of_incomings': total_no_of_incomings,
            'total_no_of_outgoings': total_no_of_outgoings,
            'sent_no_of_incomings': sent_no_of_incomings,
            'sent_no_of_outgoings': sent_no_of_outgoings
        }]

        return {'nodes': nodes, 'metadata': metadata}

    def get_projectable_properties(self):
        """
        Get projectable properties specific for Node
        :return: dict of projectable properties and column_order list
        """
        projectable_properties = {
            'creator': {
                'display_name': 'Creator',
                'help_text': 'User that created the node',
                'is_foreign_key': False,
                'type': 'str',
                'is_display': True
            },
            'ctime': {
                'display_name': 'Creation time',
                'help_text': 'Creation time of the node',
                'is_foreign_key': False,
                'type': 'datetime.datetime',
                'is_display': True
            },
            'label': {
                'display_name': 'Label',
                'help_text': 'User-assigned label',
                'is_foreign_key': False,
                'type': 'str',
                'is_display': False
            },
            'mtime': {
                'display_name': 'Last Modification time',
                'help_text': 'Last modification time',
                'is_foreign_key': False,
                'type': 'datetime.datetime',
                'is_display': True
            },
            'node_type': {
                'display_name': 'Type',
                'help_text': 'Node type',
                'is_foreign_key': False,
                'type': 'str',
                'is_display': True
            },
            'process_type': {
                'display_name': 'Process type',
                'help_text': 'Process type',
                'is_foreign_key': False,
                'type': 'str',
                'is_display': False
            },
            'user_id': {
                'display_name': 'Id of creator',
                'help_text': 'Id of the user that created the node',
                'is_foreign_key': True,
                'related_column': 'id',
                'related_resource': 'users',
                'type': 'int',
                'is_display': False
            },
            'uuid': {
                'display_name': 'Unique ID',
                'help_text': 'Universally Unique Identifier',
                'is_foreign_key': False,
                'type': 'unicode',
                'is_display': True
            }
        }

        # Note: final schema will contain details for only the fields present in column order
        column_order = ['uuid', 'label', 'node_type', 'ctime', 'mtime', 'creator']

        return projectable_properties, column_order
