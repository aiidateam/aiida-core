# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import enum
import six
import traceback

try:
    from reentry.default_manager import PluginManager
    # I don't use the default manager as it has scan_for_not_found=True
    # by default, which re-runs scan if no entrypoints are found (which is
    # quite possible if no aiida.tests entrypoints are registered)
    ENTRYPOINT_MANAGER = PluginManager(scan_for_not_found=False)
except ImportError:
    import pkg_resources as ENTRYPOINT_MANAGER

from aiida.common.exceptions import MissingEntryPointError, MultipleEntryPointError, LoadingEntryPointError

__all__ = ('load_entry_point', 'load_entry_point_from_string')


ENTRY_POINT_GROUP_PREFIX = 'aiida.'
ENTRY_POINT_STRING_SEPARATOR = ':'


class EntryPointFormat(enum.Enum):
    """
    Enum to distinguish between the various possible entry point string formats. An entry point string
    is fully qualified by its group and name concatenated by the entry point string separator character.
    The group in AiiDA has the prefix `aiida.` and the separator character is the colon `:`.

    Under these definitions a potentially valid entry point string may have the following formats:

        * FULL:    prefixed group plus entry point name     aiida.transports:ssh
        * PARTIAL: unprefixed group plus entry point name   transports:ssh
        * MINIMAL: no group but only entry point name:      ssh

    Note that the MINIMAL format can potentially lead to ambiguity if the name appears in multiple
    entry point groups.
    """

    INVALID = 0
    FULL = 1
    PARTIAL = 2
    MINIMAL = 3


entry_point_group_to_module_path_map = {
    'aiida.calculations': 'aiida.orm.nodes.process.calculation.calcjob',
    'aiida.data': 'aiida.orm.nodes.data',
    'aiida.node': 'aiida.orm.nodes',
    'aiida.parsers': 'aiida.parsers.plugins',
    'aiida.schedulers': 'aiida.schedulers.plugins',
    'aiida.tools.dbexporters': 'aiida.tools.dbexporters',
    'aiida.tools.dbimporters': 'aiida.tools.dbimporters.plugins',
    'aiida.transports': 'aiida.transports.plugins',
    'aiida.workflows': 'aiida.workflows',
}


def format_entry_point_string(group, name, fmt=EntryPointFormat.FULL):
    """
    Format an entry point string for a given entry point group and name, based on the specified format

    :param group: the entry point group
    :param name: the name of the entry point
    :param fmt: the desired output format
    :raises TypeError: if fmt is not instance of EntryPointFormat
    :raises ValueError: if fmt value is invalid
    """
    if not isinstance(fmt, EntryPointFormat):
        raise TypeError('fmt should be an instance of EntryPointFormat')

    if fmt == EntryPointFormat.FULL:
        return '{}{}{}'.format(group, ENTRY_POINT_STRING_SEPARATOR, name)
    elif fmt == EntryPointFormat.PARTIAL:
        return '{}{}{}'.format(group[len(ENTRY_POINT_GROUP_PREFIX):], ENTRY_POINT_STRING_SEPARATOR, name)
    elif fmt == EntryPointFormat.MINIMAL:
        return '{}'.format(name)
    else:
        raise ValueError('invalid EntryPointFormat')


def parse_entry_point_string(entry_point_string):
    """
    Validate the entry point string and attempt to parse the entry point group and name

    :param entry_point_string: the entry point string
    :return: the entry point group and name if the string is valid
    :raises TypeError: if the entry_point_string is not a string type
    :raises ValueError: if the entry_point_string cannot be split into two parts on the entry point string separator
    """
    if not isinstance(entry_point_string, six.string_types):
        raise TypeError('the entry_point_string should be a string')

    try:
        group, name = entry_point_string.split(ENTRY_POINT_STRING_SEPARATOR)
    except ValueError:
        raise ValueError('invalid entry_point_string format')

    return group, name


def get_entry_point_string_format(entry_point_string):
    """
    Determine the format of an entry point string. Note that it does not validate the actual entry point
    string and it may not correspond to any actual entry point. This will only assess the string format

    :param entry_point_string: the entry point string
    :returns: the entry point type
    :rtype: EntryPointFormat
    """
    try:
        group, name = entry_point_string.split(ENTRY_POINT_STRING_SEPARATOR)
    except ValueError:
        return EntryPointFormat.MINIMAL
    else:
        if group.startswith(ENTRY_POINT_GROUP_PREFIX):
            return EntryPointFormat.FULL
        else:
            return EntryPointFormat.PARTIAL


def get_entry_point_from_string(entry_point_string):
    """
    Return an entry point for the given entry point string

    :param entry_point_string: the entry point string
    :return: the entry point if it exists else None
    :raises TypeError: if the entry_point_string is not a string type
    :raises ValueError: if the entry_point_string cannot be split into two parts on the entry point string separator
    :raises aiida.common.MissingEntryPointError: entry point was not registered
    :raises aiida.common.MultipleEntryPointError: entry point could not be uniquely resolved
    """
    group, name = parse_entry_point_string(entry_point_string)
    return get_entry_point(group, name)


def load_entry_point_from_string(entry_point_string):
    """
    Load the class registered for a given entry point string that determines group and name

    :param entry_point_string: the entry point string
    :return: class registered at the given entry point
    :raises TypeError: if the entry_point_string is not a string type
    :raises ValueError: if the entry_point_string cannot be split into two parts on the entry point string separator
    :raises aiida.common.MissingEntryPointError: entry point was not registered
    :raises aiida.common.MultipleEntryPointError: entry point could not be uniquely resolved
    :raises aiida.common.LoadingEntryPointError: entry point could not be loaded
    """
    group, name = parse_entry_point_string(entry_point_string)
    return load_entry_point(group, name)


def load_entry_point(group, name):
    """
    Load the class registered under the entry point for a given name and group

    :param group: the entry point group
    :param name: the name of the entry point
    :return: class registered at the given entry point
    :raises TypeError: if the entry_point_string is not a string type
    :raises ValueError: if the entry_point_string cannot be split into two parts on the entry point string separator
    :raises aiida.common.MissingEntryPointError: entry point was not registered
    :raises aiida.common.MultipleEntryPointError: entry point could not be uniquely resolved
    :raises aiida.common.LoadingEntryPointError: entry point could not be loaded
    """
    entry_point = get_entry_point(group, name)

    try:
        loaded_entry_point = entry_point.load()
    except ImportError:
        raise LoadingEntryPointError("Failed to load entry point '{}':\n{}".format(name, traceback.format_exc()))

    return loaded_entry_point


def get_entry_point_groups():
    """
    Return a list of all the recognized entry point groups

    :return: a list of valid entry point groups
    """
    return entry_point_group_to_module_path_map.keys()


def get_entry_point_names(group, sort=True):
    """
    Return a list of all the entry point names within a specific group

    :param group: the entry point group
    :param sort: if True, the returned list will be sorted alphabetically
    :return: a list of entry point names
    """
    entry_point_names = [ep.name for ep in get_entry_points(group)]

    if sort is True:
        entry_point_names.sort()

    return entry_point_names


def get_entry_points(group):
    """
    Return a list of all the entry points within a specific group

    :param group: the entry point group
    :return: a list of entry points
    """
    return [ep for ep in ENTRYPOINT_MANAGER.iter_entry_points(group=group)]


def get_entry_point(group, name):
    """
    Return an entry point with a given name within a specific group

    :param group: the entry point group
    :param name: the name of the entry point
    :return: the entry point if it exists else None
    :raises aiida.common.MissingEntryPointError: entry point was not registered
    :raises aiida.common.MultipleEntryPointError: entry point could not be uniquely resolved
    """
    entry_points = [ep for ep in get_entry_points(group) if ep.name == name]

    if not entry_points:
        raise MissingEntryPointError("Entry point '{}' not found in group '{}'".format(name, group))

    if len(entry_points) > 1:
        raise MultipleEntryPointError("Multiple entry points '{}' found in group".format(name, group))

    return entry_points[0]


def get_entry_point_from_class(class_module, class_name):
    """
    Given the module and name of a class, attempt to obtain the corresponding entry point if it exists

    :param class_module: module of the class
    :param class_name: name of the class
    :return: a tuple of the corresponding group and entry point or None if not found
    """
    for group in ENTRYPOINT_MANAGER.get_entry_map().keys():
        for entry_point in ENTRYPOINT_MANAGER.iter_entry_points(group):

            if entry_point.module_name != class_module:
                continue

            for entry_point_class_name in entry_point.attrs:
                if entry_point_class_name == class_name:
                    return group, entry_point

    return None, None


def get_entry_point_string_from_class(class_module, class_name):
    """
    Given the module and name of a class, attempt to obtain the corresponding entry point if it
    exists and return the entry point string which will be the entry point group and entry point
    name concatenated by the entry point string separator

        entry_point_string = '{group:}:{entry_point_name:}'

    This ensures that given the entry point string, one can load the corresponding class
    by splitting on the separator, which will give the group and entry point, which should
    the corresponding factory to uniquely determine and load the class


    :param class_module: module of the class
    :param class_name: name of the class
    :return: the corresponding entry point string or None
    :rtype: str
    """
    group, entry_point = get_entry_point_from_class(class_module, class_name)

    if group and entry_point:
        return ENTRY_POINT_STRING_SEPARATOR.join([group, entry_point.name])
    else:
        return None


def is_valid_entry_point_string(entry_point_string):
    """
    Verify whether the given entry point string is a valid one. For the string to be valid means that it is composed
    of two strings, the entry point group and name, concatenated by the entry point string separator. If that is the
    case, the group name will be verified to see if it is known. If the group can be retrieved and it is known, the
    string is considered to be valid. It is invalid otherwise

    :param entry_point_string: the entry point string, generated by get_entry_point_string_from_class
    :return: True if the string is considered valid, False otherwise
    """
    try:
        group, name = entry_point_string.split(ENTRY_POINT_STRING_SEPARATOR)
    except ValueError:
        return False

    if group in entry_point_group_to_module_path_map:
        return True
    else:
        return False
