#-*- coding: utf8 -*-
"""
functionality to access / cache the plugin registry
"""


def registry_cache_file_name():
    """
    return the name of the cache file
    """
    return 'plugin_registry_cache'


def registry_cache_file_path():
    """
    return the path to the cache file
    """
    from os import path as osp
    from aiida.common.setup import get_aiida_dir
    aiida_dir = get_aiida_dir()
    cache_name = registry_cache_file_name()
    return osp.join(aiida_dir, cache_name)


def registry_cache_exists():
    """
    check if the registry cache exists

    :return bool: True if exists, False if not
    """
    from os import path as osp
    return osp.exists(registry_cache_file_path())


def registry_cache_openable():
    """
    return true if the registry cache file can be opened
    """
    if registry_cache_exists():
        try:
            with open(registry_cache_file_path):
                return True
        except:
            return False


def registry_file_url():
    """
    return the url for the plugins.json file
    """
    return 'https://raw.github.com/DropD/aiida-registry/master/plugins.json'


def registry_load_online():
    """
    loads the registry file and returns the list of plugins
    """
    import requests
    reply = requests.get(registry_file_url())
    return reply.json()


def registry_update():
    """
    load the registry from its online location and pickle it
    """
    from cPickle import dump as pdump
    cache_path = registry_cache_file_path()
    pluginlist = registry_load_online()
    with open(cache_path, 'w') as cache:
        pdump(pluginlist, cache)


def registry_load_cached():
    """
    load the registry from the local cache
    """
    from cPickle import load as pload
    cache_path = registry_cache_file_path()
    with open(cache_path, 'r') as cache:
        return pload(cache)
