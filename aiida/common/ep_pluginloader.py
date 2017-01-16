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
    'aiida.transports': 'aiida.transport.plugins',
    'aiida.workflosw': 'aiida.workflows'
}


_inv_category_mapping = {v: k for k, v in _category_mapping.iteritems()}


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
    if category == 'calculations':
        supercls = JobCalculation
        internal = 'aiida.orm.calculation.job'
        suffix = 'Calculation'
    elif category == 'parsers':
        supercls = Parser
        internal = 'aiida.parsers.plugins'
        suffix = 'Parser'
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
    except MissingPluginError:
        full_name = plugins_module + '.' + plugin_type
        category, path = [(v, k) for k, v in _inv_category_mapping.iteritems() if k in full_name].pop(0)
        classname = full_name.replace(path, '').strip('.')
        name = '.'.join(classname.split('.')[:-1])
        plugin = get_plugin(category, name)
    return plugin
