# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
functionality to access / cache the plugin registry
"""


def registry_cache_file_name():
    """
    return the name of the registry cache file
    """
    return 'plugins'


def registry_cache_file_path():
    """
    return the path to the cache file
    """
    from aiida.plugins.utils import registry_cache_folder_path
    from os import path as osp
    cache_name = registry_cache_file_name()
    cache_dir = registry_cache_folder_path()
    return osp.join(cache_dir, cache_name)


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
    from aiida.plugins.utils import registry_cache_folder_exists
    if not registry_cache_folder_exists():
        return False
    elif not registry_cache_exists():
        return False
    else:
        try:
            with open(registry_cache_file_path()):
                return True
        except Exception as e:
            return False


def registry_file_url():
    """
    return the url for the plugins.json file
    """
    return 'https://raw.github.com/aiidateam/aiida-registry/master/plugins.json'


def load_online(errorhandler=None):
    """
    loads the registry file and returns the list of plugins
    """
    from aiida.plugins.utils import load_json_from_url
    import requests
    url = registry_file_url()
    return load_json_from_url(url, errorhandler=errorhandler)


def update(with_info=True, registry_err_handler=None, info_err_handler=None):
    """
    Load the registry from its online location and pickle it.

    Creates the cache file if necessary.
    By default updates the entry details cache for each entry as well.

    :param with_info: default: True, update info cache for each entry as well
    :param registry_err_handler: callable(exception) -> dict. Must either raise
        or return a registry dict
    :param info_err_handler: callable(exception, plugin, data) -> None. Can
        raise or just print an error / warning.

    If none of the error handlers are given, the function will stop execution if
    any broken links are encountered.
    """
    from aiida.plugins.utils import pickle_to_registry_cache_folder
    cache_fname = registry_cache_file_name()
    pluginlist = load_online(errorhandler=registry_err_handler)
    pickle_to_registry_cache_folder(pluginlist, cache_fname)
    if with_info:
        cleanup_info(pluginlist)
        update_info(pluginlist, errorhandler=info_err_handler)


def load_cached():
    """
    load the registry from the local cache
    if the local cache is not readable, create or update it
    """
    from cPickle import load as pload
    from aiida.plugins.utils import unpickle_from_registry_cache_folder
    cache_fname = registry_cache_file_name()
    if not registry_cache_openable():
        update()
    return unpickle_from_registry_cache_folder(cache_fname)


def update_info(registry=None, errorhandler=None):
    """
    iterate through plugins, download setup info and return as dict
    """
    from aiida.plugins.utils import pickle_to_registry_cache_folder
    from aiida.plugins.entry import RegistryEntry as Entry

    if not registry:
        registry = load_cached()

    for plugin, data in registry.iteritems():
        try:
            entry = Entry(**data)
            pickle_to_registry_cache_folder(entry, plugin)
        except Exception as e:
            if errorhandler:
                errorhandler(e, plugin, data)
            else:
                raise e


def cleanup_info(registry=None):
    """
    delete any plugin info files that do not correspond to a registry entry
    """
    from os import remove, listdir
    from os import path as osp
    from aiida.plugins.utils import registry_cache_folder_path

    if not registry:
        registry = load_cached()

    all_cache_files = listdir(registry_cache_folder_path())
    all_cache_files.remove(registry_cache_file_name())
    plugin_cache_files = all_cache_files
    cache_dir = registry_cache_folder_path()
    for cache_file in plugin_cache_files:
        if cache_file not in registry:
            remove(osp.join(cache_dir, cache_file))

