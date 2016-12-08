# -*- coding: utf-8 -*-

import pkg_resources

from aiida.common.exceptions import MissingPluginError


def plugin_list(category):
    """
    Get a list of plugins for the given category.

    Passing `example` for the category will list all plugins registered under the
    entry point `aiida.example`.
    """

    group = 'aiida.{}'.format(category)

    return [ep.name
            for ep in pkg_resources.iter_entry_points(group=group)]


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
