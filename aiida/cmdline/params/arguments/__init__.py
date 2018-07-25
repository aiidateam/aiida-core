# -*- coding: utf-8 -*-
# yapf: disable
"""
Module to make available commonly used click arguments.
"""

import click

from aiida.cmdline.params import types
from aiida.cmdline.params.arguments.overridable import OverridableArgument

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

INPUT_FILE = OverridableArgument('input_file', metavar='INPUT_FILE', type=click.Path(exists=True))

OUTPUT_FILE = OverridableArgument('output_file', metavar='OUTPUT_FILE', type=click.Path())

LABEL = OverridableArgument('label')

USER = OverridableArgument('user', metavar='USER', type=types.UserParamType())
