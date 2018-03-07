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
Extension and eventually replacement of the aiida.common.old_pluginloader module

Allows loading plugins registered as setuptools entry points by separate pip-installed
packages.
defines drop-in replacement functionality to use the old filesystem based and the
new setuptools based plugin systems in parallel.
"""

try:
    from reentry import manager as epm
except ImportError:
    import pkg_resources as epm

from aiida.common.exceptions import LoadingPluginFailed, MissingPluginError


_category_mapping = {
    'calculations': 'aiida.orm.calculation.job',
    'data': 'aiida.orm.data',
    'parsers': 'aiida.parsers',
    'schedulers': 'aiida.scheduler.plugins',
    'transports': 'aiida.transport.plugins',
    'workflows': 'aiida.workflows',
    'tools.dbexporters': 'aiida.tools.dbexporters',
    'tools.dbimporters': 'aiida.tools.dbimporters',
    'tools.dbexporters.tcod_plugins': 'aiida.tools.dbexporters.tcod_plugins'
}


_inv_category_mapping = {v: k for k, v in _category_mapping.iteritems()}


def _supercls_for_category(category):
    from aiida.orm.calculation.job import JobCalculation
    from aiida.orm.data import Data
    from aiida.parsers import Parser
    from aiida.scheduler import Scheduler
    from aiida.transport import Transport
    from aiida.orm import Workflow
    from aiida.tools.dbexporters.tcod_plugins import BaseTcodtranslator
    supercls_mapping = {
        'calculations': JobCalculation,
        'data': Data,
        'parsers': Parser,
        'schedulers': Scheduler,
        'transports': Transport,
        'workflows': Workflow,
        'tools.dbexporters.tcod_plugins': BaseTcodtranslator
    }
    return supercls_mapping.get(category)

_category_suffix_map = {
    'calculations': 'Calculation',
    'tools.dbexporters.tcod_plugins': 'Tcodtranslator'
}


def plugin_list(category):
    """
    Get a list of plugins for the given category.

    Passing `example` for the category will list all plugins registered under the
    entry point `aiida.example`.
    """
    group = 'aiida.{}'.format(category)

    return [ep.name for ep in epm.iter_entry_points(group=group)]


def all_plugins(category):
    """
    find old and new plugins

    If both are available for a given name, the old style plugin takes precedence.
    """
    from aiida.common.old_pluginloader import existing_plugins
    from aiida.orm.calculation.job import JobCalculation
    from aiida.parsers import Parser
    supercls = _supercls_for_category(category)
    internal = _category_mapping.get(category)
    suffix = _category_suffix_map.get(category)
    plugins = existing_plugins(supercls, internal, suffix=suffix)
    plugins += [i for i in plugin_list(category) if i not in plugins]
    return [unicode(_) for _ in set(plugins)]


def get_plugin(category, name):
    """
    Return an instance of the class registered under the given name and
    for the specified plugin category.

    :param category: the plugin category to load the plugin from, e.g. 'transports'.
    :param name: the name of the plugin
    """
    group = 'aiida.{}'.format(category)

    eps = [ep for ep in epm.iter_entry_points(group=group) if ep.name == name]

    if not eps:
        raise MissingPluginError(
            "No plugin named '{}' found for '{}'".format(name, category))

    if len(eps) > 1:
        raise MissingPluginError(
            "Multiple plugins found for '{}' in '{}'".format(name, category))

    entrypoint = eps[0]

    try:
        plugin = entrypoint.load()
    except ImportError as exception:
        import traceback
        raise LoadingPluginFailed("Loading the plugin '{}' failed:\n{}"
            .format(name, traceback.format_exc()))

    return plugin

def load_plugin_safe(base_class, plugins_module, plugin_type, node_type, node_pk):
    """
    It is a wrapper of load_plugin function to return closely related node class
    if plugin is not available. By default it returns base Node class and does not
    raise exception.

    params: Look at the docstring of aiida.common.old_pluginloader.load_plugin for more Info +
    :param: node_type: type of the node
    :param node_pk: node pk

    :return: The plugin class
    """
    from aiida.common import aiidalogger

    try:
        PluginClass = load_plugin(base_class, plugins_module, plugin_type)
    except MissingPluginError:
        node_parts = plugin_type.partition(".")
        base_node_type = node_parts[0]

        ## data node: temporarily returning base data node.
        # In future its better to check the closest available plugin and return it.
        # For example if type is "aiida.orm.data.array.kpoints_tmp.KpointsData"
        # it should return array data node and not base data node
        if base_node_type == "data":
            PluginClass = load_plugin(base_class, plugins_module, 'data.Data')

        ## code node
        elif base_node_type == "code":
            PluginClass = load_plugin(base_class, plugins_module, 'code.Code')

        ## calculation node: for calculation currently we are hardcoding cases
        elif base_node_type == "calculation":
            sub_node_parts = node_parts[2].partition(".")
            sub_node_type = sub_node_parts[0]
            if sub_node_type == "job":
                PluginClass = load_plugin(base_class, plugins_module, 'calculation.job.JobCalculation')
            elif sub_node_type == "inline":
                PluginClass = load_plugin(base_class, plugins_module, 'calculation.inline.InlineCalculation')
            elif sub_node_type == "work":
                PluginClass = load_plugin(base_class, plugins_module, 'calculation.work.WorkCalculation')
            else:
                PluginClass = load_plugin(base_class, plugins_module, 'calculation.Calculation')

        ## for base node
        elif base_node_type == "node":
            PluginClass = base_class

        ## default case
        else:
            aiidalogger.error("Unable to find plugin for type '{}' (node= {}), "
                              "will use base Node class".format(node_type, node_pk))
            PluginClass = base_class

    return PluginClass


def load_plugin(base_class, plugins_module, plugin_type):
    """
    load file or extension point plugins using the file plugin interface.

    Prefer file plugins and if not found, translate the arguments to extension point notation

    :params: Look at the docstring of aiida.common.old_pluginloader.load_plugin for more Info
    :return: The plugin class
    """
    from aiida.common.old_pluginloader import load_plugin as load_old
    try:
        plugin = load_old(base_class, plugins_module, plugin_type)
    except MissingPluginError as e:
        full_name = plugins_module + '.' + plugin_type
        catlist = [(c, pm) for c, pm in _category_mapping.iteritems() if pm in full_name]
        if not catlist:  # find category for new style type string
            catlist = [(c, 'aiida.orm.' + c) for c in _category_mapping.iterkeys() if c in full_name]
        if not catlist:
            raise e
        category, path = catlist.pop(0)
        classname = full_name.replace(path, '').strip('.')
        name = '.'.join(classname.split('.')[:-1])
        plugin = get_plugin(category, name)
    return plugin


def BaseFactory(module, base_class, base_modname, suffix=None):
    """
    Return a plugin class, also find external plugins


    This is a front end to aiida.common.old_pluginloader.BaseFactory
    with a fallback to aiida.common.pluginloader.get_plugin
    check their relative docs for more info.

    Note not all possible notations work for new plugins. Example::

        BaseFactory('quantumespresso.cp', JobCalculation,
                    'aiida.orm.calculation.job',
                    suffix='Calculation') # <- finds cp also if new style

        BaseFactory('job.quantumespresso.cp', Calculation,
                    'aiida.orm.calculation') <- will find cp only if old style
    """
    from aiida.common.old_pluginloader import BaseFactory as old_factory
    try:
        return old_factory(module, base_class, base_modname, suffix)
    except MissingPluginError as e:
        category = _inv_category_mapping.get(base_modname)
        if not category:
            raise e
        return get_plugin(category, module)


def get_class_to_entry_point_map(short_group_name=False):
    """
    create a mapping of modules to entry point groups / names

    :param short_group_name: bool, if True the leading 'aiida.' is cut off group names
    :return: dictionary, keys are modules, values are (group, entrypoint-name)
    """
    groups = (g for g in epm.get_entry_map('aiida-core').iterkeys() if g.startswith('aiida'))
    class_ep_map = {}
    for group in groups:
        for ep in epm.iter_entry_points(group):
            for classname in ep.attrs:
                key = '.'.join([ep.module_name, classname])
                if short_group_name:
                    groupname = '.'.join(group.split('.')[1:])
                else:
                    groupname = group
                value = (groupname, ep.name)
                class_ep_map[key] = value
    # ~ module_ep_map = {'.'.join([ep.module_name, ep.attrs]): (group, ep.name) for group in groups for ep in iter_entry_points(group)}
    return class_ep_map


def entry_point_tpstr_from(plugin_class):
    """
    gives group and entry point name for a given module if module is registered

    :return: tuple (group, entrypoint-name) if one entry point is found
    """
    if isinstance(plugin_class, (str, unicode)):
        class_path = plugin_class
        class_name = plugin_class.split('.')[-1]
    else:
        class_name = plugin_class.__name__
        class_path = '.'.join([plugin_class.__module__, class_name])
    mapping = get_class_to_entry_point_map(short_group_name=True).get(class_path)
    typestr = None
    if mapping:
        group, epname = mapping
        typestr = '.'.join([_category_mapping[group].replace('aiida.orm.', ''), epname, class_name]) + '.'
    return typestr


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
