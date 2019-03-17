# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name
"""Definition of factories to load classes from the various plugin groups."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from .entry_point import load_entry_point

__all__ = ('BaseFactory', 'CalculationFactory', 'DataFactory', 'DbImporterFactory', 'OrbitalFactory', 'ParserFactory',
           'SchedulerFactory', 'TransportFactory', 'WorkflowFactory')


def BaseFactory(group, name):
    """Return the plugin class registered under a given entry point group and name.

    :param group: entry point group
    :param name: entry point name
    :return: the plugin class
    :raises aiida.common.MissingEntryPointError: entry point was not registered
    :raises aiida.common.MultipleEntryPointError: entry point could not be uniquely resolved
    :raises aiida.common.LoadingEntryPointError: entry point could not be loaded
    """
    return load_entry_point(group, name)


def CalculationFactory(entry_point):
    """Return the `CalcJob` sub class registered under the given entry point.

    :param entry_point: the entry point name
    :return: sub class of :py:class:`~aiida.engine.processes.calcjobs.calcjob.CalcJob`
    """
    return BaseFactory('aiida.calculations', entry_point)


def DataFactory(entry_point):
    """Return the `Data` sub class registered under the given entry point.

    :param entry_point: the entry point name
    :return: sub class of :py:class:`~aiida.orm.nodes.data.data.Data`
    """
    return BaseFactory('aiida.data', entry_point)


def DbImporterFactory(entry_point):
    """Return the `DbImporter` sub class registered under the given entry point.

    :param entry_point: the entry point name
    :return: sub class of :py:class:`~aiida.tools.dbimporters.baseclasses.DbImporter`
    """
    return BaseFactory('aiida.tools.dbimporters', entry_point)


def OrbitalFactory(entry_point):
    """Return the `Orbital` sub class registered under the given entry point.

    :param entry_point: the entry point name
    :return: sub class of :py:class:`~aiida.tools.data.orbital.orbital.Orbital`
    """
    return BaseFactory('aiida.tools.data.orbital', entry_point)


def ParserFactory(entry_point):
    """Return the `Parser` sub class registered under the given entry point.

    :param entry_point: the entry point name
    :return: sub class of :py:class:`~aiida.parsers.parser.Parser`
    """
    return BaseFactory('aiida.parsers', entry_point)


def SchedulerFactory(entry_point):
    """Return the `Scheduler` sub class registered under the given entry point.

    :param entry_point: the entry point name
    :return: sub class of :py:class:`~aiida.schedulers.scheduler.Scheduler`
    """
    return BaseFactory('aiida.schedulers', entry_point)


def TransportFactory(entry_point):
    """Return the `Transport` sub class registered under the given entry point.

    :param entry_point: the entry point name
    :return: sub class of :py:class:`~aiida.transports.transport.Transport`
    """
    return BaseFactory('aiida.transports', entry_point)


def WorkflowFactory(entry_point):
    """Return the `WorkChain` sub class registered under the given entry point.

    :param entry_point: the entry point name
    :return: sub class of :py:class:`~aiida.engine.processes.workchains.workchain.WorkChain`
    """
    return BaseFactory('aiida.workflows', entry_point)
