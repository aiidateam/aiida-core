# -*- coding: utf-8 -*-
"""Provide reusable options, helping to keep interfaces consistent."""
# yapf: disable

import click

from aiida.backends.profile import BACKEND_DJANGO, BACKEND_SQLA
from aiida.cmdline.params import types
from aiida.cmdline.params.options.conditional import ConditionalOption
from aiida.cmdline.params.options.interactive import InteractiveOption
from aiida.cmdline.params.options.multivalue import MultipleValueOption
from aiida.cmdline.params.options.overridable import OverridableOption


def valid_process_states():
    """Return a list of valid values for the ProcessState enum."""
    from plumpy import ProcessState
    return tuple(state.value for state in ProcessState)


def valid_calculation_states():
    """Return a list of valid values for the CalcState enum."""
    from aiida.common.datastructures import calc_states
    return tuple(state for state in calc_states)


def active_calculation_states():
    """Return a list of calculation states that are considered active."""
    from aiida.common.datastructures import calc_states
    return ([
        calc_states.NEW,
        calc_states.TOSUBMIT,
        calc_states.SUBMITTING,
        calc_states.WITHSCHEDULER,
        calc_states.COMPUTED,
        calc_states.RETRIEVING,
        calc_states.PARSING,
    ])


def active_process_states():
    """Return a list of process states that are considered active."""
    from plumpy import ProcessState
    return ([
        ProcessState.CREATED.value,
        ProcessState.WAITING.value,
        ProcessState.RUNNING.value,
    ])


CALCULATION = OverridableOption(
    '-C', '--calculation', 'calculation',
    type=types.CalculationParamType(),
    help='A single calculation identified by its ID or UUID.')

CALCULATIONS = OverridableOption(
    '-C', '--calculations', 'calculations',
    type=types.CalculationParamType(), cls=MultipleValueOption,
    help='One or multiple calculations identified by their ID or UUID.')

CODE = OverridableOption(
    '-X', '--code', 'code',
    type=types.CodeParamType(),
    help='A single code identified by its ID, UUID or label.')

CODES = OverridableOption(
    '-X', '--codes', 'codes',
    type=types.CodeParamType(), cls=MultipleValueOption,
    help='One or multiple codes identified by their ID, UUID or label.')

COMPUTER = OverridableOption(
    '-Y', '--computer', 'computer',
    type=types.ComputerParamType(),
    help='A single computer identified by its ID, UUID or label.')

COMPUTERS = OverridableOption(
    '-Y', '--computers', 'computers',
    type=types.ComputerParamType(), cls=MultipleValueOption,
    help='One or multiple computers identified by their ID, UUID or label.')

DATUM = OverridableOption(
    '-D', '--datum', 'datum',
    type=types.DataParamType(),
    help='A single datum identified by its ID, UUID or label.')

DATA = OverridableOption(
    '-D', '--data', 'data',
    type=types.DataParamType(), cls=MultipleValueOption,
    help='One or multiple data identified by their ID, UUID or label.')

GROUP = OverridableOption(
    '-G', '--group', 'group',
    type=types.GroupParamType(),
    help='A single group identified by its ID, UUID or name.')

GROUPS = OverridableOption(
    '-G', '--groups', 'groups',
    type=types.GroupParamType(), cls=MultipleValueOption,
    help='One or multiple groups identified by their ID, UUID or name.')

NODE = OverridableOption(
    '-N', '--node', 'node',
    type=types.NodeParamType(),
    help='A single node identified by its ID or UUID.')

NODES = OverridableOption(
    '-N', '--nodes', 'nodes',
    type=types.NodeParamType(), cls=MultipleValueOption,
    help='One or multiple nodes identified by their ID or UUID.')

FORCE = OverridableOption(
    '-f', '--force',
    is_flag=True, default=False,
    help='Do not ask for confirmation.')

SILENT = OverridableOption(
    '-s', '--silent',
    is_flag=True, default=False,
    help='Suppress any output printed to stdout.')

ARCHIVE_FORMAT = OverridableOption(
    '-F', '--archive-format',
    type=click.Choice(['zip', 'zip-uncompressed', 'tar.gz']), default='zip', show_default=True,
    help='The format of the archive file.')

NON_INTERACTIVE = OverridableOption(
    '-n', '--non-interactive',
    is_flag=True, is_eager=True,
    help='Non-interactive mode: never prompt for input.')

USER_EMAIL = OverridableOption(
    '--email',
    type=click.STRING, prompt='Email Address (identifies your data when sharing)',
    help='Email address that will be associated with your data and will be exported along with it, '
    'should you choose to share any of your work.')

USER_FIRST_NAME = OverridableOption(
    '--first-name',
    type=click.STRING, prompt='First name',
    help='First name of the user.')

USER_LAST_NAME = OverridableOption(
    '--last-name',
    type=click.STRING, prompt='Last name',
    help='Last name of the user.')

USER_INSTITUTION = OverridableOption(
    '--institution',
    type=click.STRING, prompt='Institution',
    help='Institution name of the user.')

BACKEND = OverridableOption(
    '--backend',
    type=click.Choice([BACKEND_DJANGO, BACKEND_SQLA]), default=BACKEND_DJANGO,
    help='Database backend to use.')

DB_HOST = OverridableOption(
    '--db-host',
    type=click.STRING,
    help='Database server host.')

DB_PORT = OverridableOption(
    '--db-port',
    type=click.INT,
    help='Database server port.')

DB_USERNAME = OverridableOption(
    '--db-username',
    type=click.STRING,
    help='Database user name.')

DB_PASSWORD = OverridableOption(
    '--db-password',
    type=click.STRING,
    help='Database user password.')

DB_NAME = OverridableOption(
    '--db-name',
    type=click.STRING,
    help='Database name.')

REPOSITORY_PATH = OverridableOption(
    '--repository',
    type=click.Path(file_okay=False),
    help='Absolute path for the file system repository.')

PROFILE_ONLY_CONFIG = OverridableOption(
    '--only-config',
    is_flag=True, default=False,
    help='Only configure the user and skip creating the database.')

PROFILE_SET_DEFAULT = OverridableOption(
    '--set-default',
    is_flag=True, default=False,
    help='Set the profile as the new default.')

PREPEND_TEXT = OverridableOption(
    '--prepend-text',
    type=click.STRING, default='',
    help='Bash script to be executed before an action.')

APPEND_TEXT = OverridableOption(
    '--append-text',
    type=click.STRING, default='',
    help='Bash script to be executed after an action has completed.')

LABEL = OverridableOption(
    '-L', '--label',
    type=click.STRING, metavar='LABEL',
    help='Short name to be used as a label.')

DESCRIPTION = OverridableOption(
    '-D', '--description',
    type=click.STRING, metavar='DESCRIPTION', default='', required=False,
    help='A detailed description.')

INPUT_PLUGIN = OverridableOption(
    '-P', '--input-plugin',
    type=types.PluginParamType(group='calculations'),
    help='Calculation input plugin string.')

CALCULATION_STATE = OverridableOption(
    '-s', '--calculation-state', 'calculation_state',
    type=types.LazyChoice(valid_calculation_states), cls=MultipleValueOption, default=active_calculation_states,
    help='Only include entries with this calculation state.')

PROCESS_STATE = OverridableOption(
    '-S', '--process-state', 'process_state',
    type=types.LazyChoice(valid_process_states), cls=MultipleValueOption, default=active_process_states,
    help='Only include entries with this process state.')

EXIT_STATUS = OverridableOption(
    '-E', '--exit-status', 'exit_status',
    type=click.INT,
    help='Only include entries with this exit status.')

FAILED = OverridableOption(
    '-X', '--failed', 'failed',
    is_flag=True, default=False,
    help='Only include entries that have failed.')

LIMIT = OverridableOption(
    '-l', '--limit', 'limit',
    type=click.INT, default=None,
    help='Limit the number of entries to display.')

PROJECT = OverridableOption(
    '-P', '--project', 'project',
    cls=MultipleValueOption,
    help='Select the list of entity attributes to project.')

ORDER_BY = OverridableOption(
    '-O', '--order-by', 'order_by',
    type=click.Choice(['id', 'ctime']), default='ctime', show_default=True,
    help='Order the entries by this attribute.')

PAST_DAYS = OverridableOption(
    '-p', '--past-days', 'past_days',
    type=click.INT, metavar='PAST_DAYS',
    help='Only include entries created in the last PAST_DAYS number of days.')

OLDER_THAN = OverridableOption(
    '-o', '--older-than', 'older_than',
    type=click.INT, metavar='OLDER_THAN',
    help='Only include entries created before OLDER_THAN days ago.')

ALL = OverridableOption(
    '-a', '--all', 'all_entries',
    is_flag=True, default=False,
    help='Include all entries, disregarding all other filter options and flags.')

ALL_STATES = OverridableOption(
    '-A', '--all-states',
    is_flag=True,
    help='Do not limit to items in running state.')

ALL_USERS = OverridableOption(
    '-A', '--all-users', 'all_users',
    is_flag=True, default=False,
    help='Include all entries regardless of the owner.')

RAW = OverridableOption(
    '-r', '--raw', 'raw',
    is_flag=True, default=False,
    help='Display only raw query results, without any headers or footers.')

HOSTNAME = OverridableOption(
    '-H', '--hostname',
    help='Hostname.')

TRANSPORT = OverridableOption(
    '-T', '--transport',
    type=types.PluginParamType(group='transports'), required=True,
    help='Transport type.')

SCHEDULER = OverridableOption(
    '-S', '--scheduler',
    type=types.PluginParamType(group='schedulers'), required=True,
    help='Scheduler type.')

USER = OverridableOption(
    '-u', '--user', 'user',
    type=types.UserParamType(),
    help='Email address of the user.')

PORT = OverridableOption(
    '-P', '--port', 'port',
    type=click.INT,
    help='Port number.')

FREQUENCY = OverridableOption(
    '-F', '--frequency', 'frequency',
    type=click.INT)

VERBOSE = OverridableOption(
    '-v', '--verbose',
    is_flag=True, default=False,
    help='Be more verbose in printing output.')

TIMEOUT = OverridableOption(
    '-t', '--timeout',
    type=click.FLOAT, default=5.0, show_default=True,
    help='Time in seconds to wait for a response before timing out.')
