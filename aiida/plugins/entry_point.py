# -*- coding: utf-8 -*-
import traceback
try:
    from reentry import manager as epm
except ImportError:
    import pkg_resources as epm

from aiida.common.exceptions import MissingEntryPointError, MultipleEntryPointError, LoadingEntryPointError


ENTRY_POINT_STRING_SEPARATOR = ':'


def load_entry_point(group, name):
    """
    Load the class registered under the entry point for a given name and group

    :param group: the entry point group
    :param name: the name of the entry point
    :return: class registered at the given entry point
    :raises LoadingEntryPointError: entry point could not be loaded
    """
    entry_point = get_entry_point(group, name)

    try:
        loaded_entry_point = entry_point.load()
    except ImportError as exception:
        raise LoadingEntryPointError("Failed to load entry point '{}':\n{}".format(name, traceback.format_exc()))

    return loaded_entry_point


def load_entry_point_from_string(entry_point_string):
    """
    Load the class registered for a given entry point string that determines group and name

    :param entry_point_string: the entry point string
    :return: class registered at the given entry point
    :raises LoadingEntryPointError: entry point could not be loaded
    """
    group, name = entry_point_string.split(ENTRY_POINT_STRING_SEPARATOR)
    return load_entry_point(group, name)


def get_entry_point_names(group, sort=True):
    """
    Return a list of all the entry point names within a specific group

    :param group: the entry point group
    :param sort: if True, the returned list will be sorted alphabetically
    :return: a list of entry point names
    """
    entry_point_names = [ep.name for ep in get_entry_points(group)]

    if sort is True:
        sorted(entry_point_names)

    return entry_point_names


def get_entry_points(group):
    """
    Return a list of all the entry points within a specific group

    :param group: the entry point group
    :return: a list of entry points
    """
    return [ep for ep in epm.iter_entry_points(group=group)]


def get_entry_point(group, name):
    """
    Return an entry point with a given name within a specific group

    :param group: the entry point group
    :param name: the name of the entry point
    :return: the entry point if it exists else None
    :raises MissingEntryPointError: entry point was not registered
    :raises MultipleEntryPointError: entry point could not be uniquely resolved
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
    prefix = 'JobProcess_'

    # Curiosity of the dynamically generated JobProcess classes
    if class_name.startswith(prefix):
        class_path = class_name[len(prefix):]
        class_module, class_name = class_path.rsplit('.', 1)

    for group in epm.get_entry_map().keys():
        for entry_point in epm.iter_entry_points(group):

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
    """
    group, entry_point = get_entry_point_from_class(class_module, class_name)

    if group and entry_point:
        return ENTRY_POINT_STRING_SEPARATOR.join([group, entry_point.name])
    else:
        return None
