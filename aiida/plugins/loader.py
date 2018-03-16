# -*- coding: utf-8 -*-
from aiida.common.exceptions import MissingPluginError
from aiida.common.new_pluginloader import load_entry_point, strip_prefix, MissingEntryPointError, MultipleEntryPointError, LoadingEntryPointError


type_string_to_entry_point_group_map = {
    'calculation.job.': 'aiida.calculations',
    'calculation.': 'aiida.calculations',
    'code.': 'aiida.code',
    'data.': 'aiida.data',
    'node.': 'aiida.node',
}


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