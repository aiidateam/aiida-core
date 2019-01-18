# -*- coding: utf-8 -*-
"""Utilities to operate on `Node` classes."""
from __future__ import absolute_import

from aiida.common import exceptions

__all__ = ('load_node_class', 'get_type_string_from_class', 'get_query_type_from_type_string')


def load_node_class(type_string):
    """
    Return the `Node` sub class that corresponds to the given type string.

    :param type_string: the `type` string of the node
    :return: a sub class of `Node`
    """
    from aiida.orm.data import Data
    from aiida.plugins.entry_point import load_entry_point

    if not type_string.endswith('.'):
        raise exceptions.DbContentError('The type string {} is invalid'.format(type_string))

    try:
        base_path = type_string.rsplit('.', 2)[0]
    except ValueError:
        raise exceptions.MissingPluginError

    if base_path == 'data':
        return Data

    # Data nodes are the only ones with sub classes that are still external, so if the plugin is not available
    # we fall back on the base node type
    if base_path.startswith('data.'):
        entry_point_name = strip_prefix(base_path, 'data.')
        try:
            return load_entry_point('aiida.data', entry_point_name)
        except exceptions.MissingEntryPointError:
            return Data

    if base_path.startswith('node.'):
        entry_point_name = strip_prefix(base_path, 'node.')
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

    prefixes = ('aiida.orm.', 'implementation.general.', 'implementation.django.', 'implementation.sqlalchemy.')

    # Sequentially and **in order** strip the prefixes if present
    for prefix in prefixes:
        type_string = strip_prefix(type_string, prefix)

    # This needs to be here as long as `aiida.orm.data` does not live in `aiida.orm.node.data` because all the `Data`
    # instances will have a type string that starts with `data.` instead of `node.`, so in order to match any `Node`
    # we have to look for any type string essentially.
    if type_string == 'node.Node.':
        type_string = ''

    return type_string


def get_query_type_from_type_string(type_string):
    """
    Take the type string of a Node and create the queryable type string

    :param type_string: the plugin_type_string attribute of a Node
    :return: the type string that can be used to query for
    """
    if type_string == '':
        return ''

    if not type_string.endswith('.') or type_string.count('.') == 1:
        raise exceptions.DbContentError('The type string {} is invalid'.format(type_string))

    type_path = type_string.rsplit('.', 2)[0]
    type_string = type_path + '.'

    return type_string


def strip_prefix(string, prefix):
    """
    Strip the prefix from the given string and return it. If the prefix is not present
    the original string will be returned unaltered

    :param string: the string from which to remove the prefix
    :param prefix: the prefix to remove
    :return: the string with prefix removed
    """
    if string.startswith(prefix):
        return string.rsplit(prefix)[1]

    return string
