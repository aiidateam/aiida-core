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


def connection_error_msg(e):
    msg = 'There seems to be a problem with your internet connection.'
    msg += ' The original error message reads:\n\n'
    '''apparently ConnectionErrors can have an exception as message'''
    while isinstance(e.message, Exception):
        e = e.message
    msg += e.message
    return msg


def value_error_msg(e):
    msg = 'The AiiDA plugin registry seems to be temporarily unavailable.'
    msg += ' Please try again later. If the problem persists,'
    msg += ' look at github.com/aiidateam/aiida-registry and file an issue'
    msg += ' if there is none yet.'
    return msg
