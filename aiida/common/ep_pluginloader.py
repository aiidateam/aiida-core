# -*- coding: utf-8 -*-
"""
Extension and eventually replacement of the aiida.common.pluginloader module

Allows loading plugins registered as setuptools entry points by separate pip-installed
packages.
defines drop-in replacement functionality to use the old filesystem based and the
new setuptools based plugin systems in parallel.
"""

import pkg_resources

from aiida.common.exceptions import MissingPluginError


_category_mapping = {
    'calculations': 'aiida.orm.calculation.job',
    'data': 'aiida.orm.data',
    'parsers': 'aiida.parsers.plugins',
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

    return [ep.name
            for ep in pkg_resources.iter_entry_points(group=group)]


def all_plugins(category):
    """
    find old and new plugins

    If both are available for a given name, the old style plugin takes precedence.
    """
    from aiida.common.pluginloader import existing_plugins
    from aiida.orm.calculation.job import JobCalculation
    from aiida.parsers import Parser
    supercls = _supercls_for_category(category)
    internal = _category_mapping.get(category)
    suffix = _category_suffix_map.get(category)
    plugins = existing_plugins(supercls, internal, suffix=suffix)
    plugins += [i for i in plugin_list(category) if i not in plugins]
    return plugins


def get_plugin(category, name):
    """
    Return an instance of the class registered under the given name and
    for the specified plugin category.

    :param category: the plugin category to load the plugin from, e.g.
          'transport'.
    :param name: the name of the plugin
    """
    group = 'aiida.{}'.format(category)

    eps = [ep for ep in pkg_resources.iter_entry_points(group=group)
           if ep.name == name]

    if not eps:
        raise MissingPluginError(
            "No plugin named '{}' found for '{}'".format(name, category))

    if len(eps) > 1:
        raise MissingPluginError(
            "Multiple plugins found for '{}' in '{}'".format(name, category))

    entrypoint = eps[0]

    try:
        plugin = entrypoint.load()
    except ImportError:
        raise MissingPluginError("Loading the plugin '{}' failed".format(name))

    return plugin


def load_plugin(base_class, plugins_module, plugin_type):
    """
    load file or extension point plugins using the file plugin interface.

    Prefer file plugins and if not found, translate the arguments to extension point notation

    :params: Look at the docstring of aiida.common.pluginloader.load_plugin for more Info
    :return: The plugin class
    """
    from aiida.common.pluginloader import load_plugin as load_old
    try:
        plugin = load_old(base_class, plugins_module, plugin_type)
    except MissingPluginError as e:
        full_name = plugins_module + '.' + plugin_type
        catlist = [(v, k) for k, v in _inv_category_mapping.iteritems() if k in full_name]
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


    This is a front end to aiida.common.pluginloader.BaseFactory
    with a fallback to aiida.common.ep_pluginloader.get_plugin
    check their relative docs for more info.

    Note not all possible notations work for new plugins. Example::

        BaseFactory('quantumespresso.cp', JobCalculation,
                    'aiida.orm.calculation.job',
                    suffix='Calculation') # <- finds cp also if new style

        BaseFactory('job.quantumespresso.cp', Calculation,
                    'aiida.orm.calculation') <- will find cp only if old style
    """
    from aiida.common.pluginloader import BaseFactory as old_factory
    try:
        return old_factory(module, base_class, base_modname, suffix)
    except MissingPluginError as e:
        category = _inv_category_mapping.get(base_modname)
        if not category:
            raise e
        return get_plugin(category, module)


def existing_plugins(base_class, plugins_module_name, max_depth=5, suffix=None):
    """
    Return a list of plugin names, old and new style

    Refer to aiida.common.pluginloader.existing_plugins for more info
    on behaviour for old style plugins.

    If no old style plugins are found and the plugins_module_name is mappable to a
    group of entry points, aiida.common.ep_pluginloader.list_plugins is returned
    """
    from aiida.common.pluginloader import existing_plugins as old_existing
    try:
        return old_existing(base_class, plugins_module_name, max_depth=max_depth, suffix=suffix)
    except MissingPluginError as e:
        category = _inv_category_mapping.get(plugins_module_name)
        if not category:
            raise e
        return plugin_list(category)
