# -*- coding: utf-8 -*-
# yapf: disable
import click

from aiida.cmdline.params import types
from aiida.cmdline.params.options.conditional import ConditionalOption
from aiida.cmdline.params.options.interactive import InteractiveOption
from aiida.cmdline.params.options.multivalue import MultipleValueOption
from aiida.cmdline.params.options.overridable import OverridableOption


def valid_process_states():
    """
    Return a list of valid values for the ProcessState enum.
    """
    from plumpy import ProcessState
    return ([state.value for state in ProcessState])


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
    help='suppress any output printed to stdout')


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


PROCESS_STATE = OverridableOption('-S', '--process-state', 'process_state', type=types.LazyChoice(valid_process_states),
    help='only include entries with this process state')


FINISH_STATUS = OverridableOption('-F', '--finish-status', 'finish_status', type=click.INT,
    help='only include entries with this finish status')


FAILED = OverridableOption('-x', '--failed', 'failed', is_flag=True, default=False,
    help='only include entries that have failed')


LIMIT = OverridableOption('-l', '--limit', 'limit', type=click.INT, default=None,
    help='limit the number of entries to display')


PROJECT = OverridableOption('-P', '--project', 'project', cls=MultipleValueOption,
    help='select the list of entity attributes to project')


PAST_DAYS = OverridableOption('-p', '--past-days', 'past_days', type=click.INT, default=1, metavar='PAST_DAYS',
    help='only include entries created in the last PAST_DAYS number of days')


ALL = OverridableOption('-a', '--all', 'all', is_flag=True, default=False,
    help='include all entries, disregarding all other filter options and flags')

ALL_USERS = OverridableOption('-A', '--all-users', 'all_users', is_flag=True, default=False,
    help='include entries from all users')

RAW = OverridableOption('-r', '--raw', 'raw', is_flag=True, default=False,
    help='display only raw query results, without any headers or footers')
