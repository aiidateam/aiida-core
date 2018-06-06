# -*- coding: utf-8 -*-
# yapf: disable
import click

from aiida.cmdline.params import types
from aiida.cmdline.params.options.conditional import ConditionalOption
from aiida.cmdline.params.options.interactive import InteractiveOption
from aiida.cmdline.params.options.multivalue import MultipleValueOption
from aiida.cmdline.params.options.overridable import OverridableOption


CALCULATION = OverridableOption('-C', '--calculation', 'calculation', type=types.CalculationParamType(),
    help='a single calculation identified by its ID or UUID')


CALCULATIONS = OverridableOption('-C', '--calculations', 'calculations', cls=MultipleValueOption, type=types.CalculationParamType(),
    help='one or multiple calculations identified by their ID or UUID')


CODE = OverridableOption('-X', '--code', 'code', type=types.CodeParamType(),
    help='a single code identified by its ID, UUID or label')


CODES = OverridableOption('-X', '--codes', 'codes', cls=MultipleValueOption, type=types.CodeParamType(),
    help='one or multiple codes identified by their ID, UUID or label')


COMPUTER = OverridableOption('-Y', '--computer', 'computer', type=types.ComputerParamType(),
    help='a single computer identified by its ID, UUID or label')


COMPUTERS = OverridableOption('-Y', '--computers', 'computers', cls=MultipleValueOption, type=types.ComputerParamType(),
    help='one or multiple computers identified by their ID, UUID or label')


DATUM = OverridableOption('-D', '--datum', 'datum', type=types.DataParamType(),
    help='a single datum identified by its ID, UUID or label')


DATA = OverridableOption('-D', '--data', 'data', cls=MultipleValueOption, type=types.DataParamType(),
    help='one or multiple data identified by their ID, UUID or label')


GROUP = OverridableOption('-G', '--group', 'group', type=types.GroupParamType(),
    help='a single group identified by its ID, UUID or name')


GROUPS = OverridableOption('-G', '--groups', 'groups', cls=MultipleValueOption, type=types.GroupParamType(),
    help='one or multiple groups identified by their ID, UUID or name')


NODE = OverridableOption('-N', '--node', 'node', type=types.NodeParamType(),
    help='a single node identified by its ID or UUID')


NODES = OverridableOption('-N', '--nodes', 'nodes', cls=MultipleValueOption, type=types.NodeParamType(),
    help='one or multiple nodes identified by their ID or UUID')


FORCE = OverridableOption('-f', '--force', is_flag=True, default=False,
    help='do not ask for confirmation')


SILENT = OverridableOption('-s', '--silent', is_flag=True, default=False,
    help='suppres any output printed to stdout')


ARCHIVE_FORMAT = OverridableOption('-F', '--archive-format', type=click.Choice(['zip', 'zip-uncompressed', 'tar.gz']),
    help='the format of the archive file', default='zip', show_default=True)


NON_INTERACTIVE = OverridableOption('-n', '--non-interactive', is_flag=True, is_eager=True,
    help='noninteractive mode: never prompt the user for input')


PREPEND_TEXT = OverridableOption('--prepend-text', type=str, default='',
    help='bash script to be executed before an action')


APPEND_TEXT = OverridableOption('--append-text', type=str, default='',
    help='bash script to be executed after an action has completed')


LABEL = OverridableOption('-L', '--label', help='short name to be used as a label')


DESCRIPTION = OverridableOption('-D', '--description', help='a detailed description')


INPUT_PLUGIN = OverridableOption('-P', '--input-plugin', help='input plugin string', type=types.PluginParamType(group='calculations'))
