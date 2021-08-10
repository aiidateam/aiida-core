# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module to manage loading entrypoints."""
import enum
import functools
import traceback
from typing import Any, Optional, List, Sequence, Set, Tuple

# importlib.metadata was introduced into the standard library in python 3.8,
# but also was updated in python 3.10 to use the `select` API for selecting entry points.
# because of https://github.com/python/importlib_metadata/issues/308
# we do not assume that we have this API, and instead use try/except for the new/old APIs
from importlib_metadata import EntryPoint, EntryPoints
from importlib_metadata import entry_points as eps

from aiida.common.exceptions import MissingEntryPointError, MultipleEntryPointError, LoadingEntryPointError

__all__ = ('load_entry_point', 'load_entry_point_from_string', 'parse_entry_point')

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


ENTRY_POINT_GROUP_TO_MODULE_PATH_MAP = {
    'aiida.calculations': 'aiida.orm.nodes.process.calculation.calcjob',
    'aiida.cmdline.data': 'aiida.cmdline.data',
    'aiida.cmdline.data.structure.import': 'aiida.cmdline.data.structure.import',
    'aiida.cmdline.computer.configure': 'aiida.cmdline.computer.configure',
    'aiida.data': 'aiida.orm.nodes.data',
    'aiida.groups': 'aiida.orm.groups',
    'aiida.node': 'aiida.orm.nodes',
    'aiida.parsers': 'aiida.parsers.plugins',
    'aiida.schedulers': 'aiida.schedulers.plugins',
    'aiida.tools.calculations': 'aiida.tools.calculations',
    'aiida.tools.data.orbitals': 'aiida.tools.data.orbitals',
    'aiida.tools.dbexporters': 'aiida.tools.dbexporters',
    'aiida.tools.dbimporters': 'aiida.tools.dbimporters.plugins',
    'aiida.transports': 'aiida.transports.plugins',
    'aiida.workflows': 'aiida.workflows',
}


def parse_entry_point(group: str, spec: str) -> EntryPoint:
    """Return an entry point, given its group and spec (as formatted in the setup)"""
    name, value = spec.split('=', maxsplit=1)
    return EntryPoint(group=group, name=name.strip(), value=value.strip())


def validate_registered_entry_points() -> None:  # pylint: disable=invalid-name
    """Validate all registered entry points by loading them with the corresponding factory.

    :raises EntryPointError: if any of the registered entry points cannot be loaded. This can happen if:
        * The entry point cannot uniquely be resolved
        * The resource registered at the entry point cannot be imported
        * The resource's type is incompatible with the entry point group that it is defined in.

    """
    from . import factories

    factory_mapping = {
        'aiida.calculations': factories.CalculationFactory,
        'aiida.data': factories.DataFactory,
        'aiida.groups': factories.GroupFactory,
        'aiida.parsers': factories.ParserFactory,
        'aiida.schedulers': factories.SchedulerFactory,
        'aiida.transports': factories.TransportFactory,
        'aiida.tools.dbimporters': factories.DbImporterFactory,
        'aiida.tools.data.orbital': factories.OrbitalFactory,
        'aiida.workflows': factories.WorkflowFactory,
    }

    for entry_point_group, factory in factory_mapping.items():
        entry_points = get_entry_points(entry_point_group)
        for entry_point in entry_points:
            factory(entry_point.name)


def format_entry_point_string(group: str, name: str, fmt: EntryPointFormat = EntryPointFormat.FULL) -> str:
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
        return f'{group}{ENTRY_POINT_STRING_SEPARATOR}{name}'
    if fmt == EntryPointFormat.PARTIAL:
        return f'{group[len(ENTRY_POINT_GROUP_PREFIX):]}{ENTRY_POINT_STRING_SEPARATOR}{name}'
    if fmt == EntryPointFormat.MINIMAL:
        return f'{name}'
    raise ValueError('invalid EntryPointFormat')


def parse_entry_point_string(entry_point_string: str) -> Tuple[str, str]:
    """
    Validate the entry point string and attempt to parse the entry point group and name

    :param entry_point_string: the entry point string
    :return: the entry point group and name if the string is valid
    :raises TypeError: if the entry_point_string is not a string type
    :raises ValueError: if the entry_point_string cannot be split into two parts on the entry point string separator
    """
    if not isinstance(entry_point_string, str):
        raise TypeError('the entry_point_string should be a string')

    try:
        group, name = entry_point_string.split(ENTRY_POINT_STRING_SEPARATOR)
    except ValueError:
        raise ValueError('invalid entry_point_string format')

    return group, name


def get_entry_point_string_format(entry_point_string: str) -> EntryPointFormat:
    """
    Determine the format of an entry point string. Note that it does not validate the actual entry point
    string and it may not correspond to any actual entry point. This will only assess the string format

    :param entry_point_string: the entry point string
    :returns: the entry point type
    """
    try:
        group, _ = entry_point_string.split(ENTRY_POINT_STRING_SEPARATOR)
    except ValueError:
        return EntryPointFormat.MINIMAL
    else:
        if group.startswith(ENTRY_POINT_GROUP_PREFIX):
            return EntryPointFormat.FULL
        return EntryPointFormat.PARTIAL


def get_entry_point_from_string(entry_point_string: str) -> EntryPoint:
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


def load_entry_point_from_string(entry_point_string: str) -> Any:
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


def load_entry_point(group: str, name: str) -> Any:
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
        raise LoadingEntryPointError(f"Failed to load entry point '{name}':\n{traceback.format_exc()}")

    return loaded_entry_point


def get_entry_point_groups() -> Set[str]:
    """
    Return a list of all the recognized entry point groups

    :return: a list of valid entry point groups
    """
    try:
        return eps().groups
    except AttributeError:
        return set(eps())


def get_entry_point_names(group: str, sort: bool = True) -> List[str]:
    """Return the entry points within a group."""
    all_eps = eps()
    try:
        # importlib_metadata v4 / python 3.10
        group_names = list(all_eps.select(group=group).names)
    except (AttributeError, TypeError):
        group_names = [ep.name for ep in all_eps.get(group, [])]  # type: ignore
    if sort:
        return list(sorted(group_names))
    return group_names


@functools.lru_cache(maxsize=None)
def get_entry_points(group: str) -> EntryPoints:
    """
    Return a list of all the entry points within a specific group

    :param group: the entry point group
    :return: a list of entry points
    """
    try:
        return eps().select(group=group)
    except (AttributeError, TypeError):
        return eps.get(group, [])  # type: ignore # pylint: disable=no-member


@functools.lru_cache(maxsize=None)
def get_entry_point(group: str, name: str) -> EntryPoint:
    """
    Return an entry point with a given name within a specific group

    :param group: the entry point group
    :param name: the name of the entry point
    :return: the entry point if it exists else None
    :raises aiida.common.MissingEntryPointError: entry point was not registered

    """
    all_eps = eps()
    try:
        # importlib_metadata v4 / python 3.10
        found = all_eps.select(group=group, name=name)
        if len(found.names) > 1:
            raise MultipleEntryPointError(f"Multiple entry points '{name}' found in group '{group}'.")
        entry_point = found[name] if name in found.names else None
    except (AttributeError, TypeError):
        found = {ep.name: ep for ep in all_eps.get(group, []) if ep.name == name}  # type: ignore
        if len(found) > 1:
            raise MultipleEntryPointError(f"Multiple entry points '{name}' found in group '{group}'.")
        entry_point = found[name] if name in found else None
    if not entry_point:
        raise MissingEntryPointError(f"Entry point '{name}' not found in group '{group}'")
    return entry_point


def get_entry_point_from_class(class_module: str, class_name: str) -> Tuple[Optional[str], Optional[EntryPoint]]:
    """
    Given the module and name of a class, attempt to obtain the corresponding entry point if it exists

    :param class_module: module of the class
    :param class_name: name of the class
    :return: a tuple of the corresponding group and entry point or None if not found
    """
    for group in get_entry_point_groups():
        for entry_point in get_entry_points(group):

            if entry_point.module != class_module:
                continue

            if entry_point.attr == class_name:
                return group, entry_point

    return None, None


def get_entry_point_string_from_class(class_module: str, class_name: str) -> Optional[str]:  # pylint: disable=invalid-name
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
    return None


def is_valid_entry_point_string(entry_point_string: str) -> bool:
    """
    Verify whether the given entry point string is a valid one. For the string to be valid means that it is composed
    of two strings, the entry point group and name, concatenated by the entry point string separator. If that is the
    case, the group name will be verified to see if it is known. If the group can be retrieved and it is known, the
    string is considered to be valid. It is invalid otherwise

    :param entry_point_string: the entry point string, generated by get_entry_point_string_from_class
    :return: True if the string is considered valid, False otherwise
    """
    try:
        group, _ = entry_point_string.split(ENTRY_POINT_STRING_SEPARATOR)
    except (AttributeError, ValueError):
        # Either `entry_point_string` is not a string or it does not contain the separator
        return False

    return group in ENTRY_POINT_GROUP_TO_MODULE_PATH_MAP


@functools.lru_cache(maxsize=None)
def is_registered_entry_point(class_module: str, class_name: str, groups: Optional[Sequence[str]] = None) -> bool:
    """Verify whether the class with the given module and class name is a registered entry point.

    .. note:: this function only checks whether the class has a registered entry point. It does explicitly not verify
        if the corresponding class is also importable. Use `load_entry_point` for this purpose instead.

    :param class_module: the module of the class
    :param class_name: the name of the class
    :param groups: optionally consider only these entry point groups to look for the class
    :return: True if the class is a registered entry point, False otherwise.
    """
    for group in get_entry_point_groups() if groups is None else groups:
        for entry_point in get_entry_points(group):
            if class_module == entry_point.module and class_name == entry_point.attr:
                return True
    return False
