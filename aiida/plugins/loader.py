# -*- coding: utf-8 -*-
from aiida.common.exceptions import DbContentError, MissingPluginError
from aiida.common.exceptions import MissingEntryPointError, MultipleEntryPointError, LoadingEntryPointError
from aiida.plugins.entry_point import load_entry_point, strip_prefix


type_string_to_entry_point_group_map = {
    'calculation.job.': 'aiida.calculations',
    'calculation.': 'aiida.calculations',
    'code.': 'aiida.code',
    'data.': 'aiida.data',
    'node.': 'aiida.node',
}


def type_string_to_plugin_type(type_string):
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


def type_string_to_query_type(type_string):
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


def load_plugin(base_class, plugins_module, plugin_type):
    """
    """
    from aiida.orm.data import Data

    if plugin_type == 'data.Data':
        return Data

    try:
        base_path, class_name = plugin_type.rsplit('.', 1)
    except ValueError:
        raise MissingPluginError

    if base_path.count('.') == 0:
        base_path = '{}.{}'.format(base_path, base_path)

    for prefix, group in type_string_to_entry_point_group_map.iteritems():
        if base_path.startswith(prefix):
            entry_point = strip_prefix(base_path, prefix)
            try:
                plugin = load_entry_point(group, entry_point)
            except (MissingEntryPointError, MultipleEntryPointError, LoadingEntryPointError):
                raise MissingPluginError
            else:
                return plugin

    raise LoadingPluginFailed
