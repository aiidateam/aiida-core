# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import absolute_import
from collections import namedtuple, OrderedDict
from aiida.common.exceptions import DbContentError, MissingPluginError
from aiida.common.exceptions import MissingEntryPointError, MultipleEntryPointError, LoadingEntryPointError
from aiida.plugins.entry_point import load_entry_point, get_entry_point_from_class, entry_point_group_to_module_path_map


EntryPoint = namedtuple('EntryPoint', ['group', 'base_class'])


def load_plugin(plugin_type, safe=False):
    """
    Load a plugin class from its plugin type, which is essentially its ORM type string
    minus the trailing period

    :param plugin_type: the plugin type string
    :param safe: when set to True, will always attempt to return the base class closest to the plugin_type if
        the actual entry point is not recognized
    :return: the plugin class
    :raises MissingPluginError: plugin_type could not be resolved to registered entry point
    :raises LoadingPluginFailed: the entry point matching the plugin_type could not be loaded
    """
    from aiida.orm.code import Code
    from aiida.orm.calculation import Calculation
    from aiida.orm.calculation.job import JobCalculation
    from aiida.orm.data import Data
    from aiida.orm.node import Node

    plugin = None
    base_class = Node

    if plugin_type == 'data.Data':
        return Data

    try:
        base_path, class_name = plugin_type.rsplit('.', 1)
    except ValueError:
        raise MissingPluginError

    type_string_to_entry_point_type_map = OrderedDict({
        'calculation.job.': EntryPoint('aiida.calculations', JobCalculation),
        'calculation.': EntryPoint('aiida.calculations', Calculation),
        'code.': EntryPoint('aiida.code', Code),
        'data.': EntryPoint('aiida.data', Data),
        'node.': EntryPoint('aiida.node', Node),
    })

    if base_path.count('.') == 0:
        base_path = '{}.{}'.format(base_path, base_path)

    for prefix, entry_point_type in type_string_to_entry_point_type_map.items():
        if base_path.startswith(prefix):
            entry_point = strip_prefix(base_path, prefix)
            try:
                plugin = load_entry_point(entry_point_type.group, entry_point)
            except (MissingEntryPointError, MultipleEntryPointError, LoadingEntryPointError):
                base_class = entry_point_type.base_class
            finally:
                break

    if not plugin and safe is False:
        raise MissingPluginError

    if plugin:
        return plugin
    else:
        return base_class


def get_plugin_type_from_type_string(type_string):
    """
    Take the type string of a Node and create the loadable plugin type string

    :param type_string: the value from the 'type' column of the Node table
    :return: the type string that can be used to load the plugin
    """
    if type_string == '':
        type_string = 'node.Node.'

    if not type_string.endswith('.'):
        raise DbContentError("The type string '{}' is invalid".format(type_string))

    # Return the type string minus the trailing period
    return type_string[:-1]


def get_query_type_from_type_string(type_string):
    """
    Take the type string of a Node and create the queryable type string

    :param type_string: the plugin_type_string attribute of a Node
    :return: the type string that can be used to query for
    """
    if type_string == '':
        return ''

    if not type_string.endswith('.') or type_string.count('.') == 1:
        raise DbContentError("The type string '{}' is invalid".format(type_string))

    type_path, type_class, sep = type_string.rsplit('.', 2)
    type_string = type_path + '.'

    return type_string


def get_type_string_from_class(class_module, class_name):
    """
    Given the module and name of a class, determine the orm_class_type string, which codifies the
    orm class that is to be used. The returned string will always have a terminating period, which
    is required to query for the string in the database

    :param class_module: module of the class
    :param class_name: name of the class
    """
    group, entry_point = get_entry_point_from_class(class_module, class_name)

    # If we can reverse engineer an entry point group and name, we're dealing with an external class
    if group and entry_point:
        module_base_path = entry_point_group_to_module_path_map[group]
        orm_class = '{}.{}.{}.'.format(module_base_path, entry_point.name, class_name)

    # Otherwise we are dealing with an internal class
    else:
        orm_class = '{}.{}.'.format(class_module, class_name)

    type_string = get_type_string_from_class_path(orm_class)

    return type_string


def get_type_string_from_class_path(class_path):
    """
    From a fully qualified orm class path, derive the orm class base string, which essentially
    means stripping the `aiida.orm.` and `implementation.*` prefixes. For the base node `node.Node.`
    the returned base string will be the empty string

    :param class_path: the full path of the orm class
    :return: the base string of the orm class
    """
    prefixes = ('aiida.orm.', 'implementation.general.', 'implementation.django.', 'implementation.sqlalchemy.')

    # Sequentially and **in order** strip the prefixes if present
    for prefix in prefixes:
        class_path = strip_prefix(class_path, prefix)

    if class_path == 'node.Node.':
        class_path = ''

    return class_path


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
    else:
        return string