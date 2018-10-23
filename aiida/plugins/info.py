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
Utilities for high-level querying of available plugins.

These tools read information from the cached registry.
The plugin registry (in cache) is expected to be a dict where
the keys are base entry point names of plugins (unique for registered plugins)

example registry::

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


from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
def entry_point_from_tpstr(typestring):
    if typestring.startswith('calculation.job.'):
        typestring = typestring.split('.', 2)[-1]
    elif typestring.startswith('calculation.'):
        typestring = typestring.split('.', 1)[-1]
    elif typestring.startswith('data.'):
        typestring = typestring.split('.', 1)[-1]
    else:
        raise ValueError('weird typestring')
    return typestring.split('.', 1)[0]


def plugin_ep_iterator():
    """
    return an iterator over the plugin entrypoint base strings
    """
    from aiida.plugins.registry import load_cached
    plugins = load_cached()
    return iter(plugins.keys())


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
    plugins = load_cached()
    entry_point = entry_point_from_tpstr(typestring)
    return plugins.get(entry_point, None)


def find_by_pattern(pattern, ranking=False):
    """
    returns a list of RegistryEntry objects for all matches
    """
    allplugs = plugin_ep_iterator()
    matching = []
    for plug in allplugs:
        append = 0
        entry = find_by_name(plug)

        if not ranking:
            if pattern.search(plug):
                append += 1
            elif pattern.search(entry.name):
                append += 1
            elif pattern.search(entry.package_name):
                append += 1
            elif pattern.search(entry.description):
                append += 1
            elif pattern.search(entry.author):
                append += 1
        else:
            append += bool(pattern.search(plug)) and 1 or 0
            append += bool(pattern.search(entry.name)) and 1 or 0
            append += bool(pattern.search(entry.package_name)) and 1 or 0
            append += bool(pattern.search(entry.description)) and 0.5 or 0
            append += bool(pattern.search(entry.author)) and 1 or 0

        if append:
            matching.append((append, entry))
    matching.sort()
    return [i[1] for i in matching]
