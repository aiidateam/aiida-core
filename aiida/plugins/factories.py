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
from aiida.common.exceptions import InvalidEntryPointTypeError

__all__ = (
    'BaseFactory', 'CalculationFactory', 'DataFactory', 'DbImporterFactory', 'GroupFactory', 'OrbitalFactory',
    'ParserFactory', 'SchedulerFactory', 'TransportFactory', 'WorkflowFactory'
)


def raise_invalid_type_error(entry_point_name, entry_point_group, valid_classes):
    """Raise an `InvalidEntryPointTypeError` with formatted message.

    :param entry_point_name: name of the entry point
    :param entry_point_group: name of the entry point group
    :param valid_classes: tuple of valid classes for the given entry point group
    :raises aiida.common.InvalidEntryPointTypeError: always
    """
    template = 'entry point `{}` registered in group `{}` is invalid because its type is not one of: {}'
    args = (entry_point_name, entry_point_group, ', '.join([e.__name__ for e in valid_classes]))
    raise InvalidEntryPointTypeError(template.format(*args))


def BaseFactory(group, name):
    """Return the plugin class registered under a given entry point group and name.

    :param group: entry point group
    :param name: entry point name
    :return: the plugin class
    :raises aiida.common.MissingEntryPointError: entry point was not registered
    :raises aiida.common.MultipleEntryPointError: entry point could not be uniquely resolved
    :raises aiida.common.LoadingEntryPointError: entry point could not be loaded
    """
    from .entry_point import load_entry_point
    return load_entry_point(group, name)


def CalculationFactory(entry_point_name):
    """Return the `CalcJob` sub class registered under the given entry point.

    :param entry_point_name: the entry point name
    :return: sub class of :py:class:`~aiida.engine.processes.calcjobs.calcjob.CalcJob`
    :raises aiida.common.InvalidEntryPointTypeError: if the type of the loaded entry point is invalid.
    """
    from aiida.engine import CalcJob, calcfunction, is_process_function
    from aiida.orm import CalcFunctionNode

    entry_point_group = 'aiida.calculations'
    entry_point = BaseFactory(entry_point_group, entry_point_name)
    valid_classes = (CalcJob, calcfunction)

    if isclass(entry_point) and issubclass(entry_point, CalcJob):
        return entry_point

    if is_process_function(entry_point) and entry_point.node_class is CalcFunctionNode:
        return entry_point

    raise_invalid_type_error(entry_point_name, entry_point_group, valid_classes)


def DataFactory(entry_point_name):
    """Return the `Data` sub class registered under the given entry point.

    :param entry_point_name: the entry point name
    :return: sub class of :py:class:`~aiida.orm.nodes.data.data.Data`
    :raises aiida.common.InvalidEntryPointTypeError: if the type of the loaded entry point is invalid.
    """
    from aiida.orm import Data

    entry_point_group = 'aiida.data'
    entry_point = BaseFactory(entry_point_group, entry_point_name)
    valid_classes = (Data,)

    if isclass(entry_point) and issubclass(entry_point, Data):
        return entry_point

    raise_invalid_type_error(entry_point_name, entry_point_group, valid_classes)


def DbImporterFactory(entry_point_name):
    """Return the `DbImporter` sub class registered under the given entry point.

    :param entry_point_name: the entry point name
    :return: sub class of :py:class:`~aiida.tools.dbimporters.baseclasses.DbImporter`
    :raises aiida.common.InvalidEntryPointTypeError: if the type of the loaded entry point is invalid.
    """
    from aiida.tools.dbimporters import DbImporter

    entry_point_group = 'aiida.tools.dbimporters'
    entry_point = BaseFactory(entry_point_group, entry_point_name)
    valid_classes = (DbImporter,)

    if isclass(entry_point) and issubclass(entry_point, DbImporter):
        return entry_point

    raise_invalid_type_error(entry_point_name, entry_point_group, valid_classes)


def GroupFactory(entry_point_name):
    """Return the `Group` sub class registered under the given entry point.

    :param entry_point_name: the entry point name
    :return: sub class of :py:class:`~aiida.orm.groups.Group`
    :raises aiida.common.InvalidEntryPointTypeError: if the type of the loaded entry point is invalid.
    """
    from aiida.orm import Group

    entry_point_group = 'aiida.groups'
    entry_point = BaseFactory(entry_point_group, entry_point_name)
    valid_classes = (Group,)

    if isclass(entry_point) and issubclass(entry_point, Group):
        return entry_point

    raise_invalid_type_error(entry_point_name, entry_point_group, valid_classes)


def OrbitalFactory(entry_point_name):
    """Return the `Orbital` sub class registered under the given entry point.

    :param entry_point_name: the entry point name
    :return: sub class of :py:class:`~aiida.tools.data.orbital.orbital.Orbital`
    :raises aiida.common.InvalidEntryPointTypeError: if the type of the loaded entry point is invalid.
    """
    from aiida.tools.data.orbital import Orbital

    entry_point_group = 'aiida.tools.data.orbitals'
    entry_point = BaseFactory(entry_point_group, entry_point_name)
    valid_classes = (Orbital,)

    if isclass(entry_point) and issubclass(entry_point, Orbital):
        return entry_point

    raise_invalid_type_error(entry_point_name, entry_point_group, valid_classes)


def ParserFactory(entry_point_name):
    """Return the `Parser` sub class registered under the given entry point.

    :param entry_point_name: the entry point name
    :return: sub class of :py:class:`~aiida.parsers.parser.Parser`
    :raises aiida.common.InvalidEntryPointTypeError: if the type of the loaded entry point is invalid.
    """
    from aiida.parsers import Parser

    entry_point_group = 'aiida.parsers'
    entry_point = BaseFactory(entry_point_group, entry_point_name)
    valid_classes = (Parser,)

    if isclass(entry_point) and issubclass(entry_point, Parser):
        return entry_point

    raise_invalid_type_error(entry_point_name, entry_point_group, valid_classes)


def SchedulerFactory(entry_point_name):
    """Return the `Scheduler` sub class registered under the given entry point.

    :param entry_point_name: the entry point name
    :return: sub class of :py:class:`~aiida.schedulers.scheduler.Scheduler`
    :raises aiida.common.InvalidEntryPointTypeError: if the type of the loaded entry point is invalid.
    """
    from aiida.schedulers import Scheduler

    entry_point_group = 'aiida.schedulers'
    entry_point = BaseFactory(entry_point_group, entry_point_name)
    valid_classes = (Scheduler,)

    if isclass(entry_point) and issubclass(entry_point, Scheduler):
        return entry_point

    raise_invalid_type_error(entry_point_name, entry_point_group, valid_classes)


def TransportFactory(entry_point_name):
    """Return the `Transport` sub class registered under the given entry point.

    :param entry_point_name: the entry point name
    :return: sub class of :py:class:`~aiida.transports.transport.Transport`
    :raises aiida.common.InvalidEntryPointTypeError: if the type of the loaded entry point is invalid.
    """
    from aiida.transports import Transport

    entry_point_group = 'aiida.transports'
    entry_point = BaseFactory(entry_point_group, entry_point_name)
    valid_classes = (Transport,)

    if isclass(entry_point) and issubclass(entry_point, Transport):
        return entry_point

    raise_invalid_type_error(entry_point_name, entry_point_group, valid_classes)


def WorkflowFactory(entry_point_name):
    """Return the `WorkChain` sub class registered under the given entry point.

    :param entry_point_name: the entry point name
    :return: sub class of :py:class:`~aiida.engine.processes.workchains.workchain.WorkChain` or a `workfunction`
    :raises aiida.common.InvalidEntryPointTypeError: if the type of the loaded entry point is invalid.
    """
    from aiida.engine import WorkChain, is_process_function, workfunction
    from aiida.orm import WorkFunctionNode

    entry_point_group = 'aiida.workflows'
    entry_point = BaseFactory(entry_point_group, entry_point_name)
    valid_classes = (WorkChain, workfunction)

    if isclass(entry_point) and issubclass(entry_point, WorkChain):
        return entry_point

    if is_process_function(entry_point) and entry_point.node_class is WorkFunctionNode:
        return entry_point

    raise_invalid_type_error(entry_point_name, entry_point_group, valid_classes)
