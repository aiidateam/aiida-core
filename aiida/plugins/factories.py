# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name,cyclic-import
"""Definition of factories to load classes from the various plugin groups."""
from inspect import isclass
from typing import TYPE_CHECKING, Any, Callable, Optional, Tuple, Type, Union

from importlib_metadata import EntryPoint

from aiida.common.exceptions import InvalidEntryPointTypeError

__all__ = (
    'BaseFactory', 'CalculationFactory', 'CalcJobImporterFactory', 'DataFactory', 'DbImporterFactory', 'GroupFactory',
    'OrbitalFactory', 'ParserFactory', 'SchedulerFactory', 'TransportFactory', 'WorkflowFactory'
)

if TYPE_CHECKING:
    from aiida.engine import CalcJob, CalcJobImporter, WorkChain
    from aiida.orm import Data, Group
    from aiida.parsers import Parser
    from aiida.schedulers import Scheduler
    from aiida.tools.data.orbital import Orbital
    from aiida.tools.dbimporters import DbImporter
    from aiida.transports import Transport


def raise_invalid_type_error(entry_point_name: str, entry_point_group: str, valid_classes: Tuple[Any, ...]) -> None:
    """Raise an `InvalidEntryPointTypeError` with formatted message.

    :param entry_point_name: name of the entry point
    :param entry_point_group: name of the entry point group
    :param valid_classes: tuple of valid classes for the given entry point group
    :raises aiida.common.InvalidEntryPointTypeError: always
    """
    template = 'entry point `{}` registered in group `{}` is invalid because its type is not one of: {}'
    args = (entry_point_name, entry_point_group, ', '.join([e.__name__ for e in valid_classes]))
    raise InvalidEntryPointTypeError(template.format(*args))


def BaseFactory(group: str, name: str, load: bool = True) -> Union[EntryPoint, Any]:
    """Return the plugin class registered under a given entry point group and name.

    :param group: entry point group
    :param name: entry point name
    :param load: if True, load the matched entry point and return the loaded resource instead of the entry point itself.
    :return: the plugin class
    :raises aiida.common.MissingEntryPointError: entry point was not registered
    :raises aiida.common.MultipleEntryPointError: entry point could not be uniquely resolved
    :raises aiida.common.LoadingEntryPointError: entry point could not be loaded
    """
    from .entry_point import get_entry_point, load_entry_point

    if load is True:
        return load_entry_point(group, name)

    return get_entry_point(group, name)


def CalculationFactory(entry_point_name: str, load: bool = True) -> Optional[Union[EntryPoint, 'CalcJob', Callable]]:
    """Return the `CalcJob` sub class registered under the given entry point.

    :param entry_point_name: the entry point name.
    :param load: if True, load the matched entry point and return the loaded resource instead of the entry point itself.
    :return: sub class of :py:class:`~aiida.engine.processes.calcjobs.calcjob.CalcJob`
    :raises aiida.common.InvalidEntryPointTypeError: if the type of the loaded entry point is invalid.
    """
    from aiida.engine import CalcJob, calcfunction, is_process_function
    from aiida.orm import CalcFunctionNode

    entry_point_group = 'aiida.calculations'
    entry_point = BaseFactory(entry_point_group, entry_point_name, load=load)
    valid_classes = (CalcJob, calcfunction)

    if not load:
        return entry_point

    if ((isclass(entry_point) and issubclass(entry_point, CalcJob)) or
        (is_process_function(entry_point) and entry_point.node_class is CalcFunctionNode)):  # type: ignore[union-attr]
        return entry_point

    raise_invalid_type_error(entry_point_name, entry_point_group, valid_classes)


def CalcJobImporterFactory(entry_point_name: str, load: bool = True) -> Optional[Union[EntryPoint, 'CalcJobImporter']]:
    """Return the plugin registered under the given entry point.

    :param entry_point_name: the entry point name.
    :return: the loaded :class:`~aiida.engine.processes.calcjobs.importer.CalcJobImporter` plugin.
    :raises ``aiida.common.InvalidEntryPointTypeError``: if the type of the loaded entry point is invalid.
    """
    from aiida.engine import CalcJobImporter

    entry_point_group = 'aiida.calculations.importers'
    entry_point = BaseFactory(entry_point_group, entry_point_name, load=load)
    valid_classes = (CalcJobImporter,)

    if not load:
        return entry_point

    if isclass(entry_point) and issubclass(entry_point, CalcJobImporter):
        return entry_point  # type: ignore[return-value]

    raise_invalid_type_error(entry_point_name, entry_point_group, valid_classes)


def DataFactory(entry_point_name: str, load: bool = True) -> Optional[Union[EntryPoint, 'Data']]:
    """Return the `Data` sub class registered under the given entry point.

    :param entry_point_name: the entry point name.
    :param load: if True, load the matched entry point and return the loaded resource instead of the entry point itself.
    :return: sub class of :py:class:`~aiida.orm.nodes.data.data.Data`
    :raises aiida.common.InvalidEntryPointTypeError: if the type of the loaded entry point is invalid.
    """
    from aiida.orm import Data

    entry_point_group = 'aiida.data'
    entry_point = BaseFactory(entry_point_group, entry_point_name, load=load)
    valid_classes = (Data,)

    if not load:
        return entry_point

    if isclass(entry_point) and issubclass(entry_point, Data):
        return entry_point

    raise_invalid_type_error(entry_point_name, entry_point_group, valid_classes)


def DbImporterFactory(entry_point_name: str, load: bool = True) -> Optional[Union[EntryPoint, 'DbImporter']]:
    """Return the `DbImporter` sub class registered under the given entry point.

    :param entry_point_name: the entry point name.
    :param load: if True, load the matched entry point and return the loaded resource instead of the entry point itself.
    :return: sub class of :py:class:`~aiida.tools.dbimporters.baseclasses.DbImporter`
    :raises aiida.common.InvalidEntryPointTypeError: if the type of the loaded entry point is invalid.
    """
    from aiida.tools.dbimporters import DbImporter

    entry_point_group = 'aiida.tools.dbimporters'
    entry_point = BaseFactory(entry_point_group, entry_point_name, load=load)
    valid_classes = (DbImporter,)

    if not load:
        return entry_point

    if isclass(entry_point) and issubclass(entry_point, DbImporter):
        return entry_point

    raise_invalid_type_error(entry_point_name, entry_point_group, valid_classes)


def GroupFactory(entry_point_name: str, load: bool = True) -> Optional[Union[EntryPoint, 'Group']]:
    """Return the `Group` sub class registered under the given entry point.

    :param entry_point_name: the entry point name.
    :param load: if True, load the matched entry point and return the loaded resource instead of the entry point itself.
    :return: sub class of :py:class:`~aiida.orm.groups.Group`
    :raises aiida.common.InvalidEntryPointTypeError: if the type of the loaded entry point is invalid.
    """
    from aiida.orm import Group

    entry_point_group = 'aiida.groups'
    entry_point = BaseFactory(entry_point_group, entry_point_name, load=load)
    valid_classes = (Group,)

    if not load:
        return entry_point

    if isclass(entry_point) and issubclass(entry_point, Group):
        return entry_point

    raise_invalid_type_error(entry_point_name, entry_point_group, valid_classes)


def OrbitalFactory(entry_point_name: str, load: bool = True) -> Optional[Union[EntryPoint, 'Orbital']]:
    """Return the `Orbital` sub class registered under the given entry point.

    :param entry_point_name: the entry point name.
    :param load: if True, load the matched entry point and return the loaded resource instead of the entry point itself.
    :return: sub class of :py:class:`~aiida.tools.data.orbital.orbital.Orbital`
    :raises aiida.common.InvalidEntryPointTypeError: if the type of the loaded entry point is invalid.
    """
    from aiida.tools.data.orbital import Orbital

    entry_point_group = 'aiida.tools.data.orbitals'
    entry_point = BaseFactory(entry_point_group, entry_point_name, load=load)
    valid_classes = (Orbital,)

    if not load:
        return entry_point

    if isclass(entry_point) and issubclass(entry_point, Orbital):
        return entry_point

    raise_invalid_type_error(entry_point_name, entry_point_group, valid_classes)


def ParserFactory(entry_point_name: str, load: bool = True) -> Optional[Union[EntryPoint, 'Parser']]:
    """Return the `Parser` sub class registered under the given entry point.

    :param entry_point_name: the entry point name.
    :param load: if True, load the matched entry point and return the loaded resource instead of the entry point itself.
    :return: sub class of :py:class:`~aiida.parsers.parser.Parser`
    :raises aiida.common.InvalidEntryPointTypeError: if the type of the loaded entry point is invalid.
    """
    from aiida.parsers import Parser

    entry_point_group = 'aiida.parsers'
    entry_point = BaseFactory(entry_point_group, entry_point_name, load=load)
    valid_classes = (Parser,)

    if not load:
        return entry_point

    if isclass(entry_point) and issubclass(entry_point, Parser):
        return entry_point

    raise_invalid_type_error(entry_point_name, entry_point_group, valid_classes)


def SchedulerFactory(entry_point_name: str, load: bool = True) -> Optional[Union[EntryPoint, 'Scheduler']]:
    """Return the `Scheduler` sub class registered under the given entry point.

    :param entry_point_name: the entry point name.
    :param load: if True, load the matched entry point and return the loaded resource instead of the entry point itself.
    :return: sub class of :py:class:`~aiida.schedulers.scheduler.Scheduler`
    :raises aiida.common.InvalidEntryPointTypeError: if the type of the loaded entry point is invalid.
    """
    from aiida.schedulers import Scheduler

    entry_point_group = 'aiida.schedulers'
    entry_point = BaseFactory(entry_point_group, entry_point_name, load=load)
    valid_classes = (Scheduler,)

    if not load:
        return entry_point

    if isclass(entry_point) and issubclass(entry_point, Scheduler):
        return entry_point

    raise_invalid_type_error(entry_point_name, entry_point_group, valid_classes)


def TransportFactory(entry_point_name: str, load: bool = True) -> Optional[Union[EntryPoint, Type['Transport']]]:
    """Return the `Transport` sub class registered under the given entry point.

    :param entry_point_name: the entry point name.
    :param load: if True, load the matched entry point and return the loaded resource instead of the entry point itself.
    :raises aiida.common.InvalidEntryPointTypeError: if the type of the loaded entry point is invalid.
    """
    from aiida.transports import Transport

    entry_point_group = 'aiida.transports'
    entry_point = BaseFactory(entry_point_group, entry_point_name, load=load)
    valid_classes = (Transport,)

    if not load:
        return entry_point

    if isclass(entry_point) and issubclass(entry_point, Transport):
        return entry_point

    raise_invalid_type_error(entry_point_name, entry_point_group, valid_classes)


def WorkflowFactory(entry_point_name: str, load: bool = True) -> Optional[Union[EntryPoint, 'WorkChain', Callable]]:
    """Return the `WorkChain` sub class registered under the given entry point.

    :param entry_point_name: the entry point name.
    :param load: if True, load the matched entry point and return the loaded resource instead of the entry point itself.
    :return: sub class of :py:class:`~aiida.engine.processes.workchains.workchain.WorkChain` or a `workfunction`
    :raises aiida.common.InvalidEntryPointTypeError: if the type of the loaded entry point is invalid.
    """
    from aiida.engine import WorkChain, is_process_function, workfunction
    from aiida.orm import WorkFunctionNode

    entry_point_group = 'aiida.workflows'
    entry_point = BaseFactory(entry_point_group, entry_point_name, load=load)
    valid_classes = (WorkChain, workfunction)

    if not load:
        return entry_point

    if ((isclass(entry_point) and issubclass(entry_point, WorkChain)) or
        (is_process_function(entry_point) and entry_point.node_class is WorkFunctionNode)):  # type: ignore[union-attr]
        return entry_point

    raise_invalid_type_error(entry_point_name, entry_point_group, valid_classes)
