# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utility functions to work with node "full types" which are unique node identifiers.

A node's `full_type` is defined as a string that uniquely defines the node type. A valid `full_type` is constructed by
concatenating the `node_type` and `process_type` of a node with the `FULL_TYPE_CONCATENATOR`. Each segment of the full
type can optionally be terminated by a single `LIKE_OPERATOR_CHARACTER` to indicate that the `node_type` or
`process_type` should start with that value but can be followed by any amount of other characters. A full type is
invalid if it does not contain exactly one `FULL_TYPE_CONCATENATOR` character. Additionally, each segment can contain
at most one occurrence of the `LIKE_OPERATOR_CHARACTER` and it has to be at the end of the segment.

Examples of valid full types:

    'data.bool.Bool.|'
    'process.calculation.calcfunction.%|%'
    'process.calculation.calcjob.CalcJobNode.|aiida.calculations:arithmetic.add'
    'process.calculation.calcfunction.CalcFunctionNode.|aiida.workflows:codtools.primitive_structure_from_cif'

Examples of invalid full types:

    'data.bool'  # Only a single segment without concatenator
    'data.|bool.Bool.|process.'  # More than one concatenator
    'process.calculation%.calcfunction.|aiida.calculations:arithmetic.add'  # Like operator not at end of segment
    'process.calculation%.calcfunction.%|aiida.calculations:arithmetic.add'  # More than one operator in segment

"""
from collections.abc import MutableMapping

from aiida.common.escaping import escape_for_sql_like

FULL_TYPE_CONCATENATOR = '|'
LIKE_OPERATOR_CHARACTER = '%'
DEFAULT_NAMESPACE_LABEL = '~no-entry-point~'


def validate_full_type(full_type):
    """Validate that the `full_type` is a valid full type unique node identifier.

    :param full_type: a `Node` full type
    :raises ValueError: if the `full_type` is invalid
    :raises TypeError: if the `full_type` is not a string type
    """
    from aiida.common.lang import type_check

    type_check(full_type, str)

    if FULL_TYPE_CONCATENATOR not in full_type:
        raise ValueError(
            f'full type `{full_type}` does not include the required concatenator symbol `{FULL_TYPE_CONCATENATOR}`.'
        )
    elif full_type.count(FULL_TYPE_CONCATENATOR) > 1:
        raise ValueError(
            f'full type `{full_type}` includes the concatenator symbol `{FULL_TYPE_CONCATENATOR}` more than once.'
        )


def construct_full_type(node_type, process_type):
    """Return the full type, which uniquely identifies any `Node` with the given `node_type` and `process_type`.

    :param node_type: the `node_type` of the `Node`
    :param process_type: the `process_type` of the `Node`
    :return: the full type, which is a unique identifier
    """
    if node_type is None:
        node_type = ''

    if process_type is None:
        process_type = ''

    return f'{node_type}{FULL_TYPE_CONCATENATOR}{process_type}'


def get_full_type_filters(full_type):
    """Return the `QueryBuilder` filters that will return all `Nodes` identified by the given `full_type`.

    :param full_type: the `full_type` unique node identifier
    :return: dictionary of filters to be passed for the `filters` keyword in `QueryBuilder.append`
    :raises ValueError: if the `full_type` is invalid
    :raises TypeError: if the `full_type` is not a string type
    """
    validate_full_type(full_type)

    filters = {}
    node_type, process_type = full_type.split(FULL_TYPE_CONCATENATOR)

    for entry in (node_type, process_type):
        if entry.count(LIKE_OPERATOR_CHARACTER) > 1:
            raise ValueError(f'full type component `{entry}` contained more than one like-operator character')

        if LIKE_OPERATOR_CHARACTER in entry and entry[-1] != LIKE_OPERATOR_CHARACTER:
            raise ValueError(f'like-operator character in full type component `{entry}` is not at the end')

    if LIKE_OPERATOR_CHARACTER in node_type:
        # Remove the trailing `LIKE_OPERATOR_CHARACTER`, escape the string and reattach the character
        node_type = node_type[:-1]
        node_type = escape_for_sql_like(node_type) + LIKE_OPERATOR_CHARACTER
        filters['node_type'] = {'like': node_type}
    else:
        filters['node_type'] = {'==': node_type}

    if LIKE_OPERATOR_CHARACTER in process_type:
        # Remove the trailing `LIKE_OPERATOR_CHARACTER` ()
        # If that was the only specification, just ignore this filter (looking for any process_type)
        # If there was more: escape the string and reattach the character
        process_type = process_type[:-1]
        if process_type:
            process_type = escape_for_sql_like(process_type) + LIKE_OPERATOR_CHARACTER
            filters['process_type'] = {'like': process_type}
    else:
        if process_type:
            filters['process_type'] = {'==': process_type}
        else:
            # A `process_type=''` is used to represents both `process_type='' and `process_type=None`.
            # This is because there is no simple way to single out null `process_types`, and therefore
            # we consider them together with empty-string process_types.
            # Moreover, the existence of both is most likely a bug of migrations and thus both share
            # this same "erroneous" origin.
            filters['process_type'] = {'or': [{'==': ''}, {'==': None}]}

    return filters


def load_entry_point_from_full_type(full_type):
    """Return the loaded entry point for the given `full_type` unique node identifier.

    :param full_type: the `full_type` unique node identifier
    :raises ValueError: if the `full_type` is invalid
    :raises TypeError: if the `full_type` is not a string type
    :raises `~aiida.common.exceptions.EntryPointError`: if the corresponding entry point cannot be loaded
    """
    from aiida.common import EntryPointError
    from aiida.common.utils import strip_prefix
    from aiida.plugins.entry_point import is_valid_entry_point_string, load_entry_point, load_entry_point_from_string

    data_prefix = 'data.'

    validate_full_type(full_type)

    node_type, process_type = full_type.split(FULL_TYPE_CONCATENATOR)

    if is_valid_entry_point_string(process_type):

        try:
            return load_entry_point_from_string(process_type)
        except EntryPointError:
            raise EntryPointError(f'could not load entry point `{process_type}`')

    elif node_type.startswith(data_prefix):

        base_name = strip_prefix(node_type, data_prefix)
        entry_point_name = base_name.rsplit('.', 2)[0]

        try:
            return load_entry_point('aiida.data', entry_point_name)
        except EntryPointError:
            raise EntryPointError(f'could not load entry point `{process_type}`')

    # Here we are dealing with a `ProcessNode` with a `process_type` that is not an entry point string.
    # Which means it is most likely a full module path (the fallback option) and we cannot necessarily load the
    # class from this. We could try with `importlib` but not sure that we should
    raise EntryPointError('entry point of the given full type cannot be loaded')


class Namespace(MutableMapping):
    """Namespace that can be used to map the node class hierarchy."""

    namespace_separator = '.'

    # Very ugly ad-hoc mapping of `path` to `label` for the non-leaf entries in the nested `Namespace` mapping:
    mapping_path_to_label = {
        'node': 'Node',
        'node.data': 'Data',
        'node.process': 'Process',
        'node.process.calculation': 'Calculation',
        'node.process.calculation.calcjob': 'Calculation job',
        'node.process.calculation.calcfunction': 'Calculation function',
        'node.process.workflow': 'Workflow',
        'node.process.workflow.workchain': 'Work chain',
        'node.process.workflow.workfunction': 'Work function',
    }

    # This is a hard-coded mapping to generate the correct full types for process node namespaces of external
    # plugins. The `node_type` in that case is fixed and the `process_type` should start with the entry point group
    # followed by the plugin name and the wildcard.
    process_full_type_mapping = {
        'process.calculation.calcjob.': 'process.calculation.calcjob.CalcJobNode.|aiida.calculations:{plugin_name}.%',
        'process.calculation.calcfunction.':
        'process.calculation.calcfunction.CalcFunctionNode.|aiida.calculations:{plugin_name}.%',
        'process.workflow.workfunction.':
        'process.workflow.workfunction.WorkFunctionNode.|aiida.workflows:{plugin_name}.%',
        'process.workflow.workchain.': 'process.workflow.workchain.WorkChainNode.|aiida.workflows:{plugin_name}.%',
    }

    process_full_type_mapping_unplugged = {
        'process.calculation.calcjob.': 'process.calculation.calcjob.CalcJobNode.|{plugin_name}.%',
        'process.calculation.calcfunction.': 'process.calculation.calcfunction.CalcFunctionNode.|{plugin_name}.%',
        'process.workflow.workfunction.': 'process.workflow.workfunction.WorkFunctionNode.|{plugin_name}.%',
        'process.workflow.workchain.': 'process.workflow.workchain.WorkChainNode.|{plugin_name}.%',
    }

    def __str__(self):
        import json
        return json.dumps(self.get_description(), sort_keys=True, indent=4)

    def __init__(self, namespace, path=None, label=None, full_type=None, counter=None, is_leaf=True):
        """Construct a new node class namespace."""
        # pylint: disable=super-init-not-called, too-many-arguments
        self._namespace = namespace
        self._path = path if path else namespace
        self._full_type = self._infer_full_type(full_type)
        self._subspaces = {}
        self._is_leaf = is_leaf
        self._counter = counter

        try:
            self._label = label if label is not None else self.mapping_path_to_label[path]
        except KeyError:
            self._label = self._path.rpartition('.')[-1]

        # Manual override for process subspaces that contain entries corresponding to nodes with "unregistered" process
        # types. In this case, the label should become `Unregistered` and the full type set to `None` because we cannot
        # query for all nodes that fall under this category.
        if namespace == DEFAULT_NAMESPACE_LABEL:
            self._label = 'Unregistered'
            self._full_type = None

    def _infer_full_type(self, full_type):
        """Infer the full type based on the current namespace path and the given full type of the leaf."""
        from aiida.common.utils import strip_prefix

        if full_type or self._path is None:
            return full_type

        full_type = strip_prefix(self._path, 'node.')

        if full_type.startswith('process.'):
            for basepath, full_type_template in self.process_full_type_mapping.items():
                if full_type.startswith(basepath):
                    plugin_name = strip_prefix(full_type, basepath)
                    if plugin_name.startswith(DEFAULT_NAMESPACE_LABEL):
                        temp_type_template = self.process_full_type_mapping_unplugged[basepath]
                        plugin_name = strip_prefix(plugin_name, DEFAULT_NAMESPACE_LABEL + '.')
                        full_type = temp_type_template.format(plugin_name=plugin_name)
                    else:
                        full_type = full_type_template.format(plugin_name=plugin_name)
                    return full_type

        full_type += f'.{LIKE_OPERATOR_CHARACTER}{FULL_TYPE_CONCATENATOR}'

        if full_type.startswith('process.'):
            full_type += LIKE_OPERATOR_CHARACTER

        return full_type

    def __iter__(self):
        return self._subspaces.__iter__()

    def __len__(self):
        return len(self._subspaces)

    def __delitem__(self, key):
        del self._subspaces[key]

    def __getitem__(self, key):
        return self._subspaces[key]

    def __setitem__(self, key, port):
        self._subspaces[key] = port

    @property
    def is_leaf(self):
        return self._is_leaf

    def get_description(self):
        """Return a dictionary with a description of the ports this namespace contains.

        Nested PortNamespaces will be properly recursed and Ports will print their properties in a list

        :returns: a dictionary of descriptions of the Ports contained within this PortNamespace
        """
        result = {
            'namespace': self._namespace,
            'full_type': self._full_type,
            'label': self._label,
            'path': self._path,
            'subspaces': [],
        }

        for _, port in self._subspaces.items():
            subspace_result = port.get_description()
            result['subspaces'].append(subspace_result)
            if 'counter' in subspace_result:
                if self._counter is None:
                    self._counter = 0
                self._counter = self._counter + subspace_result['counter']

        if self._counter is not None:
            result['counter'] = self._counter

        return result

    def create_namespace(self, name, **kwargs):
        """Create and return a new `Namespace` in this `Namespace`.

        If the name is namespaced, the sub `Namespaces` will be created recursively, except if one of the namespaces is
        already occupied at any level by a Port in which case a ValueError will be thrown

        :param name: name (potentially namespaced) of the port to create and return
        :param kwargs: constructor arguments that will be used *only* for the construction of the terminal Namespace
        :returns: Namespace
        :raises: ValueError if any sub namespace is occupied by a non-Namespace port
        """
        if not isinstance(name, str):
            raise ValueError(f'name has to be a string type, not {type(name)}')

        if not name:
            raise ValueError('name cannot be an empty string')

        namespace = name.split(self.namespace_separator)
        port_name = namespace.pop(0)

        path = f'{self._path}{self.namespace_separator}{port_name}'

        # If this is True, the (sub) port namespace does not yet exist, so we create it
        if port_name not in self:

            # If there still is a `namespace`, we create a sub namespace, *without* the constructor arguments
            if namespace:
                self[port_name] = self.__class__(port_name, path=path, is_leaf=False)

            # Otherwise it is the terminal port and we construct *with* the keyword arugments
            else:
                kwargs['is_leaf'] = True
                self[port_name] = self.__class__(port_name, path=path, **kwargs)
        else:
            # The port does already exist: if it is a leaf and `namespace` is not empty, then the current leaf node is
            # also a namespace itself, so create a namespace with the same name and put the leaf within itself
            if self[port_name].is_leaf and namespace:
                clone = self[port_name]
                self[port_name] = self.__class__(port_name, path=path, is_leaf=False)
                self[port_name][port_name] = clone

            # If the current existing port is not a leaf and we do not have remaining namespace, that means the current
            # namespace is the "concrete" version of the namespace, so we add the leaf version to the namespace.
            elif not self[port_name].is_leaf and not namespace:
                kwargs['is_leaf'] = True
                self[port_name][port_name] = self.__class__(port_name, path=f'{path}.{port_name}', **kwargs)

        # If there is still `namespace` left, we create the next namespace
        if namespace:
            kwargs['is_leaf'] = True
            return self[port_name].create_namespace(self.namespace_separator.join(namespace), **kwargs)

        return self[port_name]


def get_node_namespace(user_pk=None, count_nodes=False):
    """Return the full namespace of all available nodes in the current database.

    :return: complete node `Namespace`
    """
    # pylint: disable=too-many-branches
    from aiida import orm
    from aiida.plugins.entry_point import is_valid_entry_point_string, parse_entry_point_string

    filters = {}
    if user_pk is not None:
        filters['user_id'] = user_pk

    builder = orm.QueryBuilder().append(orm.Node, filters=filters, project=['node_type', 'process_type']).distinct()

    # All None instances of process_type are turned into ''
    unique_types = {(node_type, process_type if process_type else '') for node_type, process_type in builder.all()}

    # First we create a flat list of all "leaf" node types.
    namespaces = []

    for node_type, process_type in unique_types:

        label = None
        counter = None
        namespace = None

        if process_type:
            # Only process nodes
            parts = node_type.rsplit('.', 2)
            if is_valid_entry_point_string(process_type):
                _, entry_point_name = parse_entry_point_string(process_type)
                label = entry_point_name.rpartition('.')[-1]
                namespace = '.'.join(parts[:-2] + [entry_point_name])
            else:
                label = process_type.rsplit('.', 1)[-1]
                namespace = '.'.join(parts[:-2] + [DEFAULT_NAMESPACE_LABEL, process_type])

        else:
            # Data nodes and process nodes without process type (='' or =None)
            parts = node_type.rsplit('.', 2)
            try:
                label = parts[-2]
                namespace = '.'.join(parts[:-2])
            except IndexError:
                continue

        if count_nodes:
            builder = orm.QueryBuilder()
            concat_filters = [{'node_type': {'==': node_type}}]

            if node_type.startswith('process.'):
                if process_type:
                    concat_filters.append({'process_type': {'==': process_type}})
                else:
                    concat_filters.append({'process_type': {'or': [{'==': ''}, {'==': None}]}})

            if user_pk:
                concat_filters.append({'user_id': {'==': user_pk}})

            if len(concat_filters) == 1:
                builder.append(orm.Node, filters=concat_filters[0])
            else:
                builder.append(orm.Node, filters={'and': concat_filters})

            counter = builder.count()

        full_type = construct_full_type(node_type, process_type)
        namespaces.append((namespace, label, full_type, counter))

    node_namespace = Namespace('node')

    for namespace, label, full_type, counter in sorted(namespaces, key=lambda x: x[0], reverse=False):
        node_namespace.create_namespace(namespace, label=label, full_type=full_type, counter=counter)

    return node_namespace
