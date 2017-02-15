#-*- coding: utf8 -*-
"""
utilities to provide information about available plugins

The plugin registry (in cache) is expected to be a dict where
the keys are base entry point names of plugins (unique for registered plugins)

example registry
registry = {
    'quantumespresso': {
        'name': 'aiida-quantumespresso',
        'package_name': 'aiida_quantumespresso',
        'pip_url': 'git+https://...',
        'other_key': 'other_value'
    }
    'vasp': {
        'name': aiida-vasp',
        'package_name': 'aiida_vasp',
        '...': '...'
    }
}
"""


def plugin_ep_iterator():
    """
    return an iterator over the plugin entrypoint base strings
    """
    from aiida.plugins.registry import load_cached
    plugins = load_cached()
    return plugins.iterkeys()


def find_by_name(plugin_key):
    """
    returns the pickled RegistryEntry object for a given plugin_key
    """
    from aiida.plugins.utils import unpickle_from_registry_cache_folder
    return unpickle_from_registry_cache_folder(plugin_key)


def find_for_typestring(typestring):
    """
    find the plugin with the base entry point name of the given typestring

    :return: dict with plugin keys if found, None if not found
    """
    from aiida.plugins.registry import load_cached
    from aiida.common.ep_pluginloader import entry_point_from_tpstr
    plugins = load_cached()
    entry_point = entry_point_from_tpstr(typestring)
    return plugins.get(entry_point, None)
