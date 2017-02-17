#-*- coding: utf8 -*-
"""
utilities for:

* managing the registry cache folder
* downloading json files
* pickling to the registry cache folder
"""


def registry_cache_folder_name():
    """
    return the name of the subfolder of aiida_dir where registry caches are stored.
    """
    return 'plugin_registry_cache'


def registry_cache_folder_path():
    """
    return the fully resolved path to the cache folder
    """
    from os import path as osp
    from aiida.common.setup import get_aiida_dir
    aiida_dir = get_aiida_dir()
    cache_dir = registry_cache_folder_name()
    return osp.join(aiida_dir, cache_dir)


def registry_cache_folder_exists():
    """
    return True if the cache folder exists, False if not
    """
    from os import path as osp
    cache_dir = registry_cache_folder_path()
    return osp.isdir(cache_dir)


def safe_create_registry_cache_folder():
    """
    creates the registry cache folder if it does not exist
    """
    from os import mkdir
    if not registry_cache_folder_exists():
        cache_dir = registry_cache_folder_path()
        mkdir(cache_dir)


def pickle_to_registry_cache_folder(obj, fname):
    """
    pickles a python object to the registry cache folder
    """
    from cPickle import dump as pdump
    from os import path as osp
    safe_create_registry_cache_folder()
    cache_dir = registry_cache_folder_path()
    fpath = osp.join(cache_dir, fname)
    with open(fpath, 'w') as cache_file:
        pdump(obj, cache_file)


def unpickle_from_registry_cache_folder(fname):
    """
    looks for fname in the registry cache folder and tries to unpickle from it
    """
    from cPickle import load as pload
    from os import path as osp
    cache_dir = registry_cache_folder_path()
    fpath = osp.join(cache_dir, fname)
    with open(fpath, 'r') as cache:
        return pload(cache)


def load_json_from_url(url, errorhandler=None):
    """
    downloads a json file and returns the corresponding python dict
    """
    import requests
    reply = requests.get(url)
    res = None
    try:
        res = reply.json()
    except Exception as e:
        if errorhandler:
            res = errorhandler(e)
        else:
            raise e
    return res
