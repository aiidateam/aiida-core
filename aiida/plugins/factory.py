# -*- coding: utf-8 -*-
from aiida.plugins.entry_point import module_path_to_entry_point_group_map, load_entry_point


def BaseFactory(module, base_class, base_modname, suffix=None):
    """
    Return the plugin class registered under a given entry point name for
    a given entry point group

    :param module: entry point name
    :param base_modname: entry point group
    :return: the plugin class
    """
    group = module_path_to_entry_point_group_map[base_modname]

    return load_entry_point(group, module)
