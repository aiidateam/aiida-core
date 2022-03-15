# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utilities to operate on `Node` classes."""
from abc import ABCMeta
import logging
import warnings

from aiida.common import exceptions
from aiida.common.utils import strip_prefix

__all__ = (
    'load_node_class',
    'get_type_string_from_class',
    'get_query_type_from_type_string',
    'AbstractNodeMeta',
)


def load_node_class(type_string):
    """
    Return the `Node` sub class that corresponds to the given type string.

    :param type_string: the `type` string of the node
    :return: a sub class of `Node`
    """
    from aiida.orm import Data, Node
    from aiida.plugins.entry_point import load_entry_point

    if type_string == '':
        return Node

    if type_string == 'data.Data.':
        return Data

    if not type_string.endswith('.'):
        raise exceptions.DbContentError(f'The type string `{type_string}` is invalid')

    try:
        base_path = type_string.rsplit('.', 2)[0]
    except ValueError:
        raise exceptions.EntryPointError from ValueError

    # This exception needs to be there to make migrations work that rely on the old type string starting with `node.`
    # Since now the type strings no longer have that prefix, we simply strip it and continue with the normal logic.
    if base_path.startswith('node.'):
        base_path = strip_prefix(base_path, 'node.')

    # Data nodes are the only ones with sub classes that are still external, so if the plugin is not available
    # we fall back on the base node type
    if base_path.startswith('data.'):
        entry_point_name = strip_prefix(base_path, 'data.')
        try:
            return load_entry_point('aiida.data', entry_point_name)
        except exceptions.MissingEntryPointError:
            return Data

    if base_path.startswith('process'):
        entry_point_name = strip_prefix(base_path, 'nodes.')
        return load_entry_point('aiida.node', entry_point_name)

    # At this point we really have an anomalous type string. At some point, storing nodes with unresolvable type strings
    # was allowed, for example by creating a sub class in a shell and then storing an instance. Attempting to load the
    # node then would fail miserably. This is now no longer allowed, but we need a fallback for existing cases, which
    # should be rare. We fallback on `Data` and not `Node` because bare node instances are also not storable and so the
    # logic of the ORM is not well defined for a loaded instance of the base `Node` class.
    warnings.warn(f'unknown type string `{type_string}`, falling back onto `Data` class')  # pylint: disable=no-member

    return Data


def get_type_string_from_class(class_module, class_name):
    """
    Given the module and name of a class, determine the orm_class_type string, which codifies the
    orm class that is to be used. The returned string will always have a terminating period, which
    is required to query for the string in the database

    :param class_module: module of the class
    :param class_name: name of the class
    """
    from aiida.plugins.entry_point import ENTRY_POINT_GROUP_TO_MODULE_PATH_MAP, get_entry_point_from_class

    group, entry_point = get_entry_point_from_class(class_module, class_name)

    # If we can reverse engineer an entry point group and name, we're dealing with an external class
    if group and entry_point:
        module_base_path = ENTRY_POINT_GROUP_TO_MODULE_PATH_MAP[group]
        type_string = f'{module_base_path}.{entry_point.name}.{class_name}.'

    # Otherwise we are dealing with an internal class
    else:
        type_string = f'{class_module}.{class_name}.'

    prefixes = ('aiida.orm.nodes.',)

    # Sequentially and **in order** strip the prefixes if present
    for prefix in prefixes:
        type_string = strip_prefix(type_string, prefix)

    # This needs to be here as long as `aiida.orm.nodes.data` does not live in `aiida.orm.nodes.data` because all the
    # `Data` instances will have a type string that starts with `data.` instead of `nodes.`, so in order to match any
    # `Node` we have to look for any type string essentially.
    if type_string == 'node.Node.':
        type_string = ''

    return type_string


def is_valid_node_type_string(type_string, raise_on_false=False):
    """
    Checks whether type string of a Node is valid.

    :param type_string: the plugin_type_string attribute of a Node
    :return: True if type string is valid, else false
    """
    # Currently the type string for the top-level node is empty.
    # Change this when a consistent type string hierarchy is introduced.
    if type_string == '':
        return True

    # Note: this allows for the user-defined type strings like 'group' in the QueryBuilder
    # as well as the usual type strings like 'data.parameter.ParameterData.'
    if type_string.count('.') == 1 or not type_string.endswith('.'):
        if raise_on_false:
            raise exceptions.DbContentError(f'The type string {type_string} is invalid')
        return False

    return True


def get_query_type_from_type_string(type_string):
    """
    Take the type string of a Node and create the queryable type string

    :param type_string: the plugin_type_string attribute of a Node
    :return: the type string that can be used to query for
    """
    is_valid_node_type_string(type_string, raise_on_false=True)

    # Currently the type string for the top-level node is empty.
    # Change this when a consistent type string hierarchy is introduced.
    if type_string == '':
        return ''

    type_path = type_string.rsplit('.', 2)[0]
    type_string = f'{type_path}.'

    return type_string


class AbstractNodeMeta(ABCMeta):
    """Some python black magic to set correctly the logger also in subclasses."""

    def __new__(cls, name, bases, namespace, **kwargs):
        newcls = ABCMeta.__new__(cls, name, bases, namespace, **kwargs)  # pylint: disable=too-many-function-args
        newcls._logger = logging.getLogger(f"{namespace['__module__']}.{name}")

        # Set the plugin type string and query type string based on the plugin type string
        newcls._plugin_type_string = get_type_string_from_class(namespace['__module__'], name)  # pylint: disable=protected-access
        newcls._query_type_string = get_query_type_from_type_string(newcls._plugin_type_string)  # pylint: disable=protected-access

        return newcls
