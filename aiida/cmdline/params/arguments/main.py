# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# yapf: disable
"""Module with pre-defined reusable commandline arguments that can be used as `click` decorators."""

import click

from .. import types
from .overridable import OverridableArgument

__all__ = (
    'PROFILE', 'PROFILES', 'CALCULATION', 'CALCULATIONS', 'CODE', 'CODES', 'COMPUTER', 'COMPUTERS', 'DATUM', 'DATA',
    'GROUP', 'GROUPS', 'NODE', 'NODES', 'PROCESS', 'PROCESSES', 'WORKFLOW', 'WORKFLOWS', 'INPUT_FILE', 'OUTPUT_FILE',
    'LABEL', 'USER', 'CONFIG_OPTION'
)


PROFILE = OverridableArgument('profile', type=types.ProfileParamType())

PROFILES = OverridableArgument('profiles', type=types.ProfileParamType(), nargs=-1)

CALCULATION = OverridableArgument('calculation', type=types.CalculationParamType())

CALCULATIONS = OverridableArgument('calculations', nargs=-1, type=types.CalculationParamType())

CODE = OverridableArgument('code', type=types.CodeParamType())

CODES = OverridableArgument('codes', nargs=-1, type=types.CodeParamType())

COMPUTER = OverridableArgument('computer', type=types.ComputerParamType())

COMPUTERS = OverridableArgument('computers', nargs=-1, type=types.ComputerParamType())

DATUM = OverridableArgument('datum', type=types.DataParamType())

DATA = OverridableArgument('data', nargs=-1, type=types.DataParamType())

GROUP = OverridableArgument('group', type=types.GroupParamType())

GROUPS = OverridableArgument('groups', nargs=-1, type=types.GroupParamType())

NODE = OverridableArgument('node', type=types.NodeParamType())

NODES = OverridableArgument('nodes', nargs=-1, type=types.NodeParamType())

PROCESS = OverridableArgument('process', type=types.ProcessParamType())

PROCESSES = OverridableArgument('processes', nargs=-1, type=types.ProcessParamType())

WORKFLOW = OverridableArgument('workflow', type=types.WorkflowParamType())

WORKFLOWS = OverridableArgument('workflows', nargs=-1, type=types.WorkflowParamType())

INPUT_FILE = OverridableArgument('input_file', metavar='INPUT_FILE', type=click.Path(exists=True))

OUTPUT_FILE = OverridableArgument('output_file', metavar='OUTPUT_FILE', type=click.Path())

LABEL = OverridableArgument('label', type=click.STRING)

USER = OverridableArgument('user', metavar='USER', type=types.UserParamType())

CONFIG_OPTION = OverridableArgument('option', type=types.ConfigOptionParamType())
