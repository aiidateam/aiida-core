# -*- coding: utf-8 -*-
from aiida.plugins.entry_point import load_entry_point


def BaseFactory(group, name):
    """
    Return the plugin class registered under a given entry point group and name

    :param group: entry point group
    :param name: entry point name
    :return: the plugin class
    """
    return load_entry_point(group, name)
