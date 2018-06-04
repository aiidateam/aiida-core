# -*- coding: utf-8 -*-
# yapf: disable
import click

from aiida.cmdline.params import types
from aiida.cmdline.params.arguments.overridable import OverridableArgument


CODE = OverridableArgument('code', type=types.CodeParamType())


CODES = OverridableArgument('codes', nargs=-1, type=types.CodeParamType())


COMPUTER = OverridableArgument('computer', type=types.ComputerParamType())


COMPUTERS = OverridableArgument('computers', nargs=-1, type=types.ComputerParamType())


GROUP = OverridableArgument('group', type=types.GroupParamType())


GROUPS = OverridableArgument('groups', nargs=-1, type=types.GroupParamType())


NODE = OverridableArgument('node', type=types.NodeParamType())


NODES = OverridableArgument('nodes', nargs=-1, type=types.NodeParamType())


INPUT_FILE = OverridableArgument('input_file', metavar='INPUT_FILE', type=click.Path(exists=True))


OUTPUT_FILE = OverridableArgument('output_file', metavar='OUTPUT_FILE', type=click.Path())
