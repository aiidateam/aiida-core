###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module to manage loading entrypoints."""

from __future__ import annotations

import enum
import functools
import traceback
from typing import TYPE_CHECKING, Any, List, Optional, Sequence, Set, Tuple

from aiida.common.exceptions import LoadingEntryPointError, MissingEntryPointError, MultipleEntryPointError
from aiida.common.warnings import warn_deprecation

from . import factories

if TYPE_CHECKING:
    # importlib.metadata was introduced into the standard library in python 3.8,
    # but was then updated in python 3.10 to use an improved API.
    # So for now we use the backport importlib_metadata package.
    from importlib_metadata import EntryPoint, EntryPoints

__all__ = ('get_entry_points', 'load_entry_point', 'load_entry_point_from_string', 'parse_entry_point')

ENTRY_POINT_GROUP_PREFIX = 'aiida.'
ENTRY_POINT_STRING_SEPARATOR = ':'


@functools.cache
def eps() -> EntryPoints:
    """Cache around entry_points()

    This call takes around 50ms!
    NOTE: For faster lookups, we sort the ``EntryPoints`` alphabetically
    by the group name so that 'aiida.' groups come up first.
    Unfortunately, this does not help with the entry_points.select() filter,
    which will always iterate over all entry points since it looks for
    possible duplicate entries.
    """
    from importlib_metadata import EntryPoints, entry_points

    all_eps = entry_points()
    return EntryPoints(sorted(all_eps, key=lambda x: x.group))


@functools.lru_cache(maxsize=100)
def eps_select(group: str, name: str | None = None) -> EntryPoints:
    """A thin wrapper around entry_points.select() calls, which are
    expensive so we want to cache them.
    """
    if name is None:
        return eps().select(group=group)
    return eps().select(group=group, name=name)


class EntryPointFormat(enum.Enum):
    """Enum to distinguish between the various possible entry point string formats. An entry point string
    is fully qualified by its group and name concatenated by the entry point string separator character.
    The group in AiiDA has the prefix `aiida.` and the separator character is the colon `:`.

    Under these definitions a potentially valid entry point string may have the following formats:

        * FULL:    prefixed group plus entry point name     aiida.transports:core.ssh
        * PARTIAL: unprefixed group plus entry point name   transports:core.ssh
        * MINIMAL: no group but only entry point name:      core.ssh

    Note that the MINIMAL format can potentially lead to ambiguity if the name appears in multiple
    entry point groups.
    """

    INVALID = 0
    FULL = 1
    PARTIAL = 2
    MINIMAL = 3


ENTRY_POINT_GROUP_TO_MODULE_PATH_MAP = {
    'aiida.calculations': 'aiida.orm.nodes.process.calculation.calcjob',
    'aiida.calculations.importers': 'aiida.calculations.importers',
    'aiida.calculations.monitors': 'aiida.calculations.monitors',
    'aiida.cmdline.computer.configure': 'aiida.cmdline.computer.configure',
    'aiida.cmdline.data': 'aiida.cmdline.data',
    'aiida.cmdline.data.structure.import': 'aiida.cmdline.data.structure.import',
    'aiida.cmdline.verdi': 'aiida.cmdline.verdi',
    'aiida.data': 'aiida.orm.nodes.data',
    'aiida.groups': 'aiida.orm.groups',
    'aiida.orm': 'aiida.orm',
    'aiida.node': 'aiida.orm.nodes',
    'aiida.parsers': 'aiida.parsers.plugins',
    'aiida.schedulers': 'aiida.schedulers.plugins',
    'aiida.storage': 'aiida.storage',
    'aiida.transports': 'aiida.transports.plugins',
    'aiida.tools.calculations': 'aiida.tools.calculations',
    'aiida.tools.data.orbitals': 'aiida.tools.data.orbitals',
    'aiida.tools.dbexporters': 'aiida.tools.dbexporters',
    'aiida.tools.dbimporters': 'aiida.tools.dbimporters.plugins',
    'aiida.workflows': 'aiida.workflows',
}

DEPRECATED_ENTRY_POINTS_MAPPING = {
    'aiida.calculations': ['arithmetic.add', 'templatereplacer'],
    'aiida.data': [
        'array',
        'array.bands',
        'array.kpoints',
        'array.projection',
        'array.trajectory',
        'array.xy',
        'base',
        'bool',
        'cif',
        'code',
        'dict',
        'float',
        'folder',
        'int',
        'list',
        'numeric',
        'orbital',
        'remote',
        'remote.stash',
        'remote.stash.folder',
        'singlefile',
        'str',
        'structure',
        'upf',
    ],
    'aiida.tools.dbimporters': ['cod', 'icsd', 'materialsproject', 'mpds', 'mpod', 'nninc', 'oqmd', 'pcod', 'tcod'],
    'aiida.tools.data.orbitals': ['orbital', 'realhydrogen'],
    'aiida.parsers': ['arithmetic.add', 'templatereplacer.doubler'],
    'aiida.schedulers': ['direct', 'lsf', 'pbspro', 'sge', 'slurm', 'torque'],
    'aiida.transports': ['local', 'ssh'],
    'aiida.workflows': ['arithmetic.multiply_add', 'arithmetic.add_multiply'],
}

ENTRY_POINT_GROUP_FACTORY_MAPPING = {
    'aiida.calculations': factories.CalculationFactory,
    'aiida.data': factories.DataFactory,
    'aiida.groups': factories.GroupFactory,
    'aiida.parsers': factories.ParserFactory,
    'aiida.schedulers': factories.SchedulerFactory,
    'aiida.storage': factories.StorageFactory,
    'aiida.transports': factories.TransportFactory,
    'aiida.tools.dbimporters': factories.DbImporterFactory,
    'aiida.tools.data.orbital': factories.OrbitalFactory,
    'aiida.workflows': factories.WorkflowFactory,
}


def parse_entry_point(group: str, spec: str) -> EntryPoint:
    """Return an entry point, given its group and spec (as formatted in the setup)"""
    from importlib_metadata import EntryPoint

    name, value = spec.split('=', maxsplit=1)
    return EntryPoint(group=group, name=name.strip(), value=value.strip())


def validate_registered_entry_points() -> None:
    """Validate all registered entry points by loading them with the corresponding factory.

    :raises EntryPointError: if any of the registered entry points cannot be loaded. This can happen if:
        * The entry point cannot uniquely be resolved
        * The resource registered at the entry point cannot be imported
        * The resource's type is incompatible with the entry point group that it is defined in.

    """
    for entry_point_group, factory in ENTRY_POINT_GROUP_FACTORY_MAPPING.items():
        entry_points = get_entry_points(entry_point_group)
        for entry_point in entry_points:
            factory(entry_point.name)


def format_entry_point_string(group: str, name: str, fmt: EntryPointFormat = EntryPointFormat.FULL) -> str:
    """Format an entry point string for a given entry point group and name, based on the specified format

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
    """Validate the entry point string and attempt to parse the entry point group and name

    :param entry_point_string: the entry point string
    :return: the entry point group and name if the string is valid
    :raises TypeError: if the entry_point_string is not a string type
    :raises ValueError: if the entry_point_string cannot be split into two parts on the entry point string separator
    """
    if not isinstance(entry_point_string, str):
        raise TypeError('the entry_point_string should be a string')

    try:
        group, name = entry_point_string.split(ENTRY_POINT_STRING_SEPARATOR)
    except ValueError as exc:
        raise ValueError(f'invalid entry_point_string format: {entry_point_string}') from exc

    return group, name


def get_entry_point_string_format(entry_point_string: str) -> EntryPointFormat:
    """Determine the format of an entry point string. Note that it does not validate the actual entry point
    string and it may not correspond to any actual entry point. This will only assess the string format

    :param entry_point_string: the entry point string
    :returns: the entry point type
    """
    try:
        group, _ = entry_point_string.split(ENTRY_POINT_STRING_SEPARATOR)
    except ValueError:
        return EntryPointFormat.MINIMAL

    if group.startswith(ENTRY_POINT_GROUP_PREFIX):
        return EntryPointFormat.FULL

    return EntryPointFormat.PARTIAL


def get_entry_point_from_string(entry_point_string: str) -> EntryPoint:
    """Return an entry point for the given entry point string

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
    """Load the class registered for a given entry point string that determines group and name

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
    """Load the class registered under the entry point for a given name and group

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
    """Return a list of all the recognized entry point groups

    :return: a list of valid entry point groups
    """
    return eps().groups


def get_entry_point_names(group: str, sort: bool = True) -> List[str]:
    """Return the entry points within a group."""
    group_names = list(get_entry_points(group).names)
    if sort:
        return sorted(group_names)
    return group_names


def get_entry_points(group: str) -> EntryPoints:
    """Return a list of all the entry points within a specific group

    :param group: the entry point group
    :return: a list of entry points
    """
    return eps_select(group=group)


def get_entry_point(group: str, name: str) -> EntryPoint:
    """Return an entry point with a given name within a specific group

    :param group: the entry point group
    :param name: the name of the entry point
    :return: the entry point if it exists else None
    :raises aiida.common.MissingEntryPointError: entry point was not registered

    """
    # The next line should be removed for ``aiida-core==3.0`` when the old deprecated entry points are fully removed.
    name = convert_potentially_deprecated_entry_point(group, name)
    found = eps_select(group=group, name=name)
    if name not in found.names:
        raise MissingEntryPointError(f"Entry point '{name}' not found in group '{group}'")
    # If multiple entry points are found and they have different values we raise, otherwise if they all
    # correspond to the same value, we simply return one of them
    if len(found) > 1 and len(set(ep.value for ep in found)) != 1:
        raise MultipleEntryPointError(f"Multiple entry points '{name}' found in group '{group}': {found}")
    return found[name]


def convert_potentially_deprecated_entry_point(group: str, name: str) -> str:
    """Check whether the specified entry point is deprecated, in which case print warning and convert to new name.

    For `aiida-core==2.0` all existing entry points where properly prefixed with ``core.`` and the old entry points were
    deprecated. To provide a smooth transition these deprecated entry points are detected in ``get_entry_point``, which
    is the lowest function that tries to resolve an entry point string, by calling this function.

    If the entry point corresponds to a deprecated one, a warning is raised and the new corresponding entry point name
    is returned.

    This method should be removed in ``aiida-core==3.0``.
    """
    try:
        deprecated_entry_points = DEPRECATED_ENTRY_POINTS_MAPPING[group]
    except KeyError:
        return name

    if name in deprecated_entry_points:
        warn_deprecation(f'The entry point `{name}` is deprecated. Please replace it with `core.{name}`.', version=3)
        name = f'core.{name}'

    return name


@functools.lru_cache(maxsize=100)
def get_entry_point_from_class(class_module: str, class_name: str) -> Tuple[Optional[str], Optional[EntryPoint]]:
    """Given the module and name of a class, attempt to obtain the corresponding entry point if it exists

    :param class_module: module of the class
    :param class_name: name of the class
    :return: a tuple of the corresponding group and entry point or None if not found
    """
    for entry_point in eps():
        if entry_point.module == class_module and entry_point.attr == class_name:
            return entry_point.group, entry_point
    return None, None


def get_entry_point_string_from_class(class_module: str, class_name: str) -> Optional[str]:
    """Given the module and name of a class, attempt to obtain the corresponding entry point if it
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
    """Verify whether the given entry point string is a valid one. For the string to be valid means that it is composed
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


@functools.lru_cache(maxsize=100)
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
