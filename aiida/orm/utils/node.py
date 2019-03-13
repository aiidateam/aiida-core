# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utilities to operate on `Node` classes."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from abc import ABCMeta
from collections import Iterable, Mapping
import logging
import math
import numbers

import six

from aiida.common import exceptions
from aiida.common.utils import strip_prefix

__all__ = ('load_node_class', 'get_type_string_from_class', 'get_query_type_from_type_string', 'AbstractNodeMeta',
           'clean_value')


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
        raise exceptions.DbContentError('The type string `{}` is invalid'.format(type_string))

    try:
        base_path = type_string.rsplit('.', 2)[0]
    except ValueError:
        raise exceptions.MissingPluginError

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

    raise exceptions.MissingPluginError('unknown type string {}'.format(type_string))


def get_type_string_from_class(class_module, class_name):
    """
    Given the module and name of a class, determine the orm_class_type string, which codifies the
    orm class that is to be used. The returned string will always have a terminating period, which
    is required to query for the string in the database

    :param class_module: module of the class
    :param class_name: name of the class
    """
    from aiida.plugins.entry_point import get_entry_point_from_class, entry_point_group_to_module_path_map

    group, entry_point = get_entry_point_from_class(class_module, class_name)

    # If we can reverse engineer an entry point group and name, we're dealing with an external class
    if group and entry_point:
        module_base_path = entry_point_group_to_module_path_map[group]
        type_string = '{}.{}.{}.'.format(module_base_path, entry_point.name, class_name)

    # Otherwise we are dealing with an internal class
    else:
        type_string = '{}.{}.'.format(class_module, class_name)

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
            raise exceptions.DbContentError('The type string {} is invalid'.format(type_string))
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
    type_string = type_path + '.'

    return type_string


def clean_value(value):
    """
    Get value from input and (recursively) replace, if needed, all occurrences
    of BaseType AiiDA data nodes with their value, and List with a standard list.
    It also makes a deep copy of everything
    The purpose of this function is to convert data to a type which can be serialized and deserialized
    for storage in the DB without its value changing.

    Note however that there is no logic to avoid infinite loops when the
    user passes some perverse recursive dictionary or list.
    In any case, however, this would not be storable by AiiDA...

    :param value: A value to be set as an attribute or an extra
    :return: a "cleaned" value, potentially identical to value, but with
        values replaced where needed.
    """
    # Must be imported in here to avoid recursive imports
    from aiida.orm import BaseType

    def clean_builtin(val):
        """
        A function to clean build-in python values (`BaseType`).

        It mainly checks that we don't store NaN or Inf.
        """
        if isinstance(val, numbers.Real) and (math.isnan(val) or math.isinf(val)):
            # see https://www.postgresql.org/docs/current/static/datatype-json.html#JSON-TYPE-MAPPING-TABLE
            raise exceptions.ValidationError("nan and inf/-inf can not be serialized to the database")

        return val

    if isinstance(value, BaseType):
        return clean_builtin(value.value)

    if isinstance(value, Mapping):
        # Check dictionary before iterables
        return {k: clean_value(v) for k, v in value.items()}
    if (isinstance(value, Iterable) and not isinstance(value, six.string_types)):
        # list, tuple, ... but not a string
        # This should also properly take care of dealing with the
        # basedatatypes.List object
        return [clean_value(v) for v in value]

    # If I don't know what to do I just return the value
    # itself - it's not super robust, but relies on duck typing
    # (e.g. if there is something that behaves like an integer
    # but is not an integer, I still accept it)

    return clean_builtin(value)


class AbstractNodeMeta(ABCMeta):  # pylint: disable=too-few-public-methods
    """
    Some python black magic to set correctly the logger also in subclasses.
    """

    # pylint: disable=arguments-differ,protected-access,too-many-function-args

    def __new__(mcs, name, bases, namespace):
        newcls = ABCMeta.__new__(mcs, name, bases, namespace)
        newcls._logger = logging.getLogger('{}.{}'.format(namespace['__module__'], name))

        # Set the plugin type string and query type string based on the plugin type string
        newcls._plugin_type_string = get_type_string_from_class(namespace['__module__'], name)
        newcls._query_type_string = get_query_type_from_type_string(newcls._plugin_type_string)

        return newcls
