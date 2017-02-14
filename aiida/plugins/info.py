#-*- coding: utf8 -*-
"""
utilities to provide information about available plugins
"""


def plugin_ep_iterator():
    """
    return an iterator over the plugin entrypoint base strings
    """
    from aiida.plugins.registry import registry_load_cached
    plugins = registry_load_cached()
    return plugins.iterkeys()


def find_for_typestring(typestring):
    from aiida.plugins.registry import registry_load_cached
    from aiida.common.ep_pluginloader import entry_point_from_tpstr
    plugins = registry_load_cached()
    entry_point = entry_point_from_tpstr(typestring)
    return plugins.get(entry_point, None)
