###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module with pre-defined reusable commandline options that can be used as `click` decorators."""

import pathlib

import click

from aiida.brokers.rabbitmq.defaults import BROKER_DEFAULTS
from aiida.common.log import LOG_LEVELS, configure_logging
from aiida.manage.external.postgres import DEFAULT_DBINFO

from ...utils import defaults, echo
from .. import types
from .callable import CallableDefaultOption
from .config import ConfigFileOption
from .multivalue import MultipleValueOption
from .overridable import OverridableOption

__all__ = (
    'ALL',
    'ALL_STATES',
    'ALL_USERS',
    'ALSO_UNGROUPED',
    'APPEND_TEXT',
    'ARCHIVE_FORMAT',
    'BROKER_HOST',
    'BROKER_PASSWORD',
    'BROKER_PORT',
    'BROKER_PROTOCOL',
    'BROKER_USERNAME',
    'BROKER_VIRTUAL_HOST',
    'CALCULATION',
    'CALCULATIONS',
    'CALC_JOB_STATE',
    'CODE',
    'CODES',
    'COMPUTER',
    'COMPUTERS',
    'CONFIG_FILE',
    'DATA',
    'DATUM',
    'DB_BACKEND',
    'DB_ENGINE',
    'DB_HOST',
    'DB_NAME',
    'DB_PASSWORD',
    'DB_PORT',
    'DB_USERNAME',
    'DEBUG',
    'DELETE_MISSING',
    'DESCRIPTION',
    'DICT_FORMAT',
    'DICT_KEYS',
    'DRY_RUN',
    'DUMP_UNSEALED',
    'END_DATE',
    'EXIT_STATUS',
    'EXPORT_FORMAT',
    'FAILED',
    'FILTER_BY_LAST_DUMP_TIME',
    'FLAT',
    'FORCE',
    'FORMULA_MODE',
    'FREQUENCY',
    'GROUP',
    'GROUPS',
    'GROUP_CLEAR',
    'HOSTNAME',
    'IDENTIFIER',
    'INCLUDE_ATTRIBUTES',
    'INCLUDE_EXTRAS',
    'INCLUDE_INPUTS',
    'INCLUDE_OUTPUTS',
    'INPUT_FORMAT',
    'INPUT_PLUGIN',
    'LABEL',
    'LIMIT',
    'MOST_RECENT_NODE',
    'NODE',
    'NODES',
    'NON_INTERACTIVE',
    'OLDER_THAN',
    'ONLY_TOP_LEVEL_CALCS',
    'ONLY_TOP_LEVEL_WORKFLOWS',
    'ORDER_BY',
    'ORDER_DIRECTION',
    'ORGANIZE_BY_GROUPS',
    'OVERWRITE',
    'PAST_DAYS',
    'PATH',
    'PAUSED',
    'PORT',
    'PREPEND_TEXT',
    'PRINT_TRACEBACK',
    'PROCESS_LABEL',
    'PROCESS_STATE',
    'PROFILE',
    'PROFILE_ONLY_CONFIG',
    'PROFILE_SET_DEFAULT',
    'PROJECT',
    'RAW',
    'RELABEL_GROUPS',
    'REPOSITORY_PATH',
    'SCHEDULER',
    'SILENT',
    'SORT',
    'START_DATE',
    'SYMLINK_CALCS',
    'TIMEOUT',
    'TRAJECTORY_INDEX',
    'TRANSPORT',
    'TRAVERSAL_RULE_HELP_STRING',
    'TYPE_STRING',
    'USER',
    'USER_EMAIL',
    'USER_FIRST_NAME',
    'USER_INSTITUTION',
    'USER_LAST_NAME',
    'VERBOSITY',
    'VISUALIZATION_FORMAT',
    'WAIT',
    'WITH_ELEMENTS',
    'WITH_ELEMENTS_EXCLUSIVE',
    'active_process_states',
    'graph_traversal_rules',
    'valid_calc_job_states',
    'valid_process_states',
)

TRAVERSAL_RULE_HELP_STRING = {
    'call_calc_backward': 'CALL links to calculations backwards',
    'call_calc_forward': 'CALL links to calculations forwards',
    'call_work_backward': 'CALL links to workflows backwards',
    'call_work_forward': 'CALL links to workflows forwards',
    'input_calc_backward': 'INPUT links to calculations backwards',
    'input_calc_forward': 'INPUT links to calculations forwards',
    'input_work_backward': 'INPUT links to workflows backwards',
    'input_work_forward': 'INPUT links to workflows forwards',
    'return_backward': 'RETURN links backwards',
    'return_forward': 'RETURN links forwards',
    'create_backward': 'CREATE links backwards',
    'create_forward': 'CREATE links forwards',
}


def valid_process_states():
    """Return a list of valid values for the ProcessState enum."""
    from plumpy import ProcessState

    return tuple(state.value for state in ProcessState)


def valid_calc_job_states():
    """Return a list of valid values for the CalcState enum."""
    from aiida.common.datastructures import CalcJobState

    return tuple(state.value for state in CalcJobState)


def active_process_states():
    """Return a list of process states that are considered active."""
    from plumpy import ProcessState

    return [
        ProcessState.CREATED.value,
        ProcessState.WAITING.value,
        ProcessState.RUNNING.value,
    ]


def graph_traversal_rules(rules):
    """Apply the graph traversal rule options to the command."""

    def decorator(command):
        """Only apply to traversal rules if they are toggleable."""
        for name, traversal_rule in sorted(rules.items(), reverse=True):
            if traversal_rule.toggleable:
                option_name = name.replace('_', '-')
                option_label = '--{option_name}/--no-{option_name}'.format(option_name=option_name)
                help_string = f'Whether to expand the node set by following {TRAVERSAL_RULE_HELP_STRING[name]}.'
                click.option(option_label, default=traversal_rule.default, show_default=True, help=help_string)(command)

        return command

    return decorator


def set_log_level(ctx, _param, value):
    """Configure the logging for the CLI command being executed.

    Note that we cannot use the most obvious approach of directly setting the level on the various loggers. The reason
    is that after this callback is finished, the :meth:`aiida.common.log.configure_logging` method can be called again,
    for example when the database backend is loaded, and this will undo this change. So instead, we set to globals in
    the :mod:`aiida.common.log` module: ``CLI_ACTIVE`` and ``CLI_LOG_LEVEL``. The ``CLI_ACTIVE`` global is always set to
    ``True``. The ``configure_logging`` function will interpret this as the code being executed through a ``verdi``
    call. The ``CLI_LOG_LEVEL`` global is only set if an explicit value is set for the ``--verbosity`` option. In this
    case, it is set to the specified log level and ``configure_logging`` will then set this log level for all loggers.

    This approach tightly couples the generic :mod:`aiida.common.log` module to the :mod:`aiida.cmdline` module, which
    is not the cleanest, but given that other module code can undo the logging configuration by calling that method,
    there seems no easy way around this approach.
    """
    from aiida.common import log

    if log.CLI_ACTIVE:
        return value

    log.CLI_ACTIVE = True

    # If the value is ``None``, it means the option was not specified, but we still configure logging for the CLI
    # However, we skip this when we are in a tab-completion context.
    if value is None:
        if not ctx.resilient_parsing:
            configure_logging()
        return None

    try:
        log_level = value.upper()
    except AttributeError:
        raise click.BadParameter(f'`{value}` is not a string.')

    if log_level not in LOG_LEVELS:
        raise click.BadParameter(f'`{log_level}` is not a valid log level.')

    log.CLI_LOG_LEVEL = log_level

    # Make sure the logging is configured, even if it may be undone in the future by another call to this method.
    configure_logging()

    return log_level


VERBOSITY = OverridableOption(
    '-v',
    '--verbosity',
    type=click.Choice(tuple(map(str.lower, LOG_LEVELS.keys())), case_sensitive=False),
    callback=set_log_level,
    expose_value=False,  # Ensures that the option is not actually passed to the command, because it doesn't need it
    help='Set the verbosity of the output.',
)

PROFILE = OverridableOption(
    '-p',
    '--profile',
    'profile',
    type=types.ProfileParamType(),
    default=defaults.get_default_profile,
    cls=CallableDefaultOption,
    help='Execute the command for this profile instead of the default profile.',
)

CALCULATION = OverridableOption(
    '-C',
    '--calculation',
    'calculation',
    type=types.CalculationParamType(),
    help='A single calculation identified by its ID or UUID.',
)

CALCULATIONS = OverridableOption(
    '-C',
    '--calculations',
    'calculations',
    type=types.CalculationParamType(),
    cls=MultipleValueOption,
    help='One or multiple calculations identified by their ID or UUID.',
)

CODE = OverridableOption(
    '-X', '--code', 'code', type=types.CodeParamType(), help='A single code identified by its ID, UUID or label.'
)

CODES = OverridableOption(
    '-X',
    '--codes',
    'codes',
    type=types.CodeParamType(),
    cls=MultipleValueOption,
    help='One or multiple codes identified by their ID, UUID or label.',
)

COMPUTER = OverridableOption(
    '-Y',
    '--computer',
    'computer',
    type=types.ComputerParamType(),
    help='A single computer identified by its ID, UUID or label.',
)

COMPUTERS = OverridableOption(
    '-Y',
    '--computers',
    'computers',
    type=types.ComputerParamType(),
    cls=MultipleValueOption,
    help='One or multiple computers identified by their ID, UUID or label.',
)

DATUM = OverridableOption(
    '-D', '--datum', 'datum', type=types.DataParamType(), help='A single datum identified by its ID, UUID or label.'
)

DATA = OverridableOption(
    '-D',
    '--data',
    'data',
    type=types.DataParamType(),
    cls=MultipleValueOption,
    help='One or multiple data identified by their ID, UUID or label.',
)

GROUP = OverridableOption(
    '-G', '--group', 'group', type=types.GroupParamType(), help='A single group identified by its ID, UUID or label.'
)

GROUPS = OverridableOption(
    '-G',
    '--groups',
    'groups',
    type=types.GroupParamType(),
    cls=MultipleValueOption,
    help='One or multiple groups identified by their ID, UUID or label.',
)

NODE = OverridableOption(
    '-N', '--node', 'node', type=types.NodeParamType(), help='A single node identified by its ID or UUID.'
)

NODES = OverridableOption(
    '-N',
    '--nodes',
    'nodes',
    type=types.NodeParamType(),
    cls=MultipleValueOption,
    help='One or multiple nodes identified by their ID or UUID.',
)

FORCE = OverridableOption('-f', '--force', is_flag=True, default=False, help='Do not ask for confirmation.')

SILENT = OverridableOption('-s', '--silent', is_flag=True, default=False, help='Suppress any output printed to stdout.')

VISUALIZATION_FORMAT = OverridableOption(
    '-F', '--format', 'fmt', show_default=True, help='Format of the visualized output.'
)

INPUT_FORMAT = OverridableOption('-F', '--format', 'fmt', show_default=True, help='Format of the input file.')

EXPORT_FORMAT = OverridableOption('-F', '--format', 'fmt', show_default=True, help='Format of the exported file.')

ARCHIVE_FORMAT = OverridableOption(
    '-F',
    '--archive-format',
    type=click.Choice(['zip', 'zip-uncompressed', 'tar.gz']),
    default='zip',
    show_default=True,
    help='The format of the archive file.',
)

NON_INTERACTIVE = OverridableOption(
    '-n/-I',
    '--non-interactive/--interactive',
    is_eager=True,
    help=(
        'In non-interactive mode, the CLI never prompts for options but simply uses default values for options that '
        'define one. In interactive mode, the CLI will prompt for each interactive option. '
    ),
    default=False,
    show_default='--interactive',
)

DRY_RUN = OverridableOption('-n', '--dry-run', is_flag=True, help='Perform a dry run.')

USER_EMAIL = OverridableOption(
    '--email',
    'email',
    type=types.EmailType(),
    help='Email address associated with the data you generate. The email address is exported along with the data, '
    'when sharing it.',
)

USER_FIRST_NAME = OverridableOption(
    '--first-name', type=types.NonEmptyStringParamType(), help='First name of the user.'
)

USER_LAST_NAME = OverridableOption('--last-name', type=types.NonEmptyStringParamType(), help='Last name of the user.')

USER_INSTITUTION = OverridableOption(
    '--institution', type=types.NonEmptyStringParamType(), help='Institution of the user.'
)

DB_ENGINE = OverridableOption(
    '--db-engine',
    required=True,
    help='Engine to use to connect to the database.',
    default='postgresql_psycopg',
    type=click.Choice(['postgresql_psycopg']),
)

DB_BACKEND = OverridableOption(
    '--db-backend',
    required=True,
    type=click.Choice(['core.psql_dos']),
    default='core.psql_dos',
    help='Database backend to use.',
)

DB_HOST = OverridableOption(
    '--db-host',
    required=True,
    type=types.HostnameType(),
    help='Database server host. Leave empty for "peer" authentication.',
    default='localhost',
)

DB_PORT = OverridableOption(
    '--db-port',
    required=True,
    type=click.INT,
    help='Database server port.',
    default=DEFAULT_DBINFO['port'],
)

DB_USERNAME = OverridableOption(
    '--db-username', type=types.NonEmptyStringParamType(), help='Name of the database user.'
)

DB_PASSWORD = OverridableOption(
    '--db-password',
    type=click.STRING,
    help='Password of the database user.',
    hide_input=True,
)

DB_NAME = OverridableOption('--db-name', type=types.NonEmptyStringParamType(), help='Database name.')

BROKER_PROTOCOL = OverridableOption(
    '--broker-protocol',
    type=click.Choice(('amqp', 'amqps')),
    default=BROKER_DEFAULTS.protocol,
    show_default=True,
    help='Protocol to use for the message broker.',
)

BROKER_USERNAME = OverridableOption(
    '--broker-username',
    type=types.NonEmptyStringParamType(),
    default=BROKER_DEFAULTS.username,
    show_default=True,
    help='Username to use for authentication with the message broker.',
)

BROKER_PASSWORD = OverridableOption(
    '--broker-password',
    type=types.NonEmptyStringParamType(),
    default=BROKER_DEFAULTS.password,
    show_default=True,
    help='Password to use for authentication with the message broker.',
    hide_input=True,
)

BROKER_HOST = OverridableOption(
    '--broker-host',
    type=types.HostnameType(),
    default=BROKER_DEFAULTS.host,
    show_default=True,
    help='Hostname for the message broker.',
)

BROKER_PORT = OverridableOption(
    '--broker-port',
    type=click.INT,
    default=BROKER_DEFAULTS.port,
    show_default=True,
    help='Port for the message broker.',
)

BROKER_VIRTUAL_HOST = OverridableOption(
    '--broker-virtual-host',
    type=click.types.StringParamType(),
    default=BROKER_DEFAULTS.virtual_host,
    show_default=True,
    help='Name of the virtual host for the message broker without leading forward slash.',
)

REPOSITORY_PATH = OverridableOption(
    '--repository', type=click.Path(file_okay=False), help='Absolute path to the file repository.'
)

PROFILE_ONLY_CONFIG = OverridableOption(
    '--only-config', is_flag=True, default=False, help='Only configure the user and skip creating the database.'
)

PROFILE_SET_DEFAULT = OverridableOption(
    '--set-default', is_flag=True, default=False, help='Set the profile as the new default.'
)

PREPEND_TEXT = OverridableOption(
    '--prepend-text', type=click.STRING, default='', help='Bash script to be executed before an action.'
)

APPEND_TEXT = OverridableOption(
    '--append-text', type=click.STRING, default='', help='Bash script to be executed after an action has completed.'
)

LABEL = OverridableOption('-L', '--label', type=click.STRING, metavar='LABEL', help='Short name to be used as a label.')

DESCRIPTION = OverridableOption(
    '-D',
    '--description',
    type=click.STRING,
    metavar='DESCRIPTION',
    default='',
    required=False,
    help='A detailed description.',
)

INPUT_PLUGIN = OverridableOption(
    '-P',
    '--input-plugin',
    type=types.PluginParamType(group='calculations', load=False),
    help='Calculation input plugin string.',
)

CALC_JOB_STATE = OverridableOption(
    '-s',
    '--calc-job-state',
    'calc_job_state',
    type=types.LazyChoice(valid_calc_job_states),
    cls=MultipleValueOption,
    help='Only include entries with this calculation job state.',
)

PROCESS_STATE = OverridableOption(
    '-S',
    '--process-state',
    'process_state',
    type=types.LazyChoice(valid_process_states),
    cls=MultipleValueOption,
    default=active_process_states,
    help='Only include entries with this process state.',
)

PAUSED = OverridableOption('--paused', 'paused', is_flag=True, help='Only include entries that are paused.')

PROCESS_LABEL = OverridableOption(
    '-L',
    '--process-label',
    'process_label',
    type=click.STRING,
    required=False,
    help='Only include entries whose process label matches this filter.',
)

TYPE_STRING = OverridableOption(
    '-T',
    '--type-string',
    'type_string',
    type=click.STRING,
    required=False,
    help='Only include entries whose type string matches this filter. Can include `_` to match a single arbitrary '
    'character or `%` to match any number of characters.',
)

EXIT_STATUS = OverridableOption(
    '-E', '--exit-status', 'exit_status', type=click.INT, help='Only include entries with this exit status.'
)

FAILED = OverridableOption(
    '-X', '--failed', 'failed', is_flag=True, default=False, help='Only include entries that have failed.'
)

LIMIT = OverridableOption(
    '-l', '--limit', 'limit', type=click.INT, default=None, help='Limit the number of entries to display.'
)

PROJECT = OverridableOption(
    '-P', '--project', 'project', cls=MultipleValueOption, help='Select the list of entity attributes to project.'
)

ORDER_BY = OverridableOption(
    '-O',
    '--order-by',
    'order_by',
    type=click.Choice(['id', 'ctime']),
    default='ctime',
    show_default=True,
    help='Order the entries by this attribute.',
)

ORDER_DIRECTION = OverridableOption(
    '-D',
    '--order-direction',
    'order_dir',
    type=click.Choice(['asc', 'desc']),
    default='asc',
    show_default=True,
    help='List the entries in ascending or descending order',
)

PAST_DAYS = OverridableOption(
    '-p',
    '--past-days',
    'past_days',
    type=click.INT,
    metavar='PAST_DAYS',
    help='Only include entries created in the last PAST_DAYS number of days.',
)

OLDER_THAN = OverridableOption(
    '-o',
    '--older-than',
    'older_than',
    type=click.INT,
    metavar='OLDER_THAN',
    help='Only include entries created before OLDER_THAN days ago.',
)

MOST_RECENT_NODE = OverridableOption(
    '-M',
    '--most-recent-node',
    is_flag=True,
    help='Select the most recently created node.',
)

ALL = OverridableOption(
    '-a',
    '--all',
    'all_entries',
    is_flag=True,
    default=False,
    help='Include all entries, disregarding all other filter options and flags.',
)

ALL_STATES = OverridableOption('-A', '--all-states', is_flag=True, help='Do not limit to items in running state.')

ALL_USERS = OverridableOption(
    '-A', '--all-users', 'all_users', is_flag=True, default=False, help='Include all entries regardless of the owner.'
)

GROUP_CLEAR = OverridableOption(
    '-c', '--clear', is_flag=True, default=False, help='Remove all the nodes from the group.'
)

RAW = OverridableOption(
    '-r',
    '--raw',
    'raw',
    is_flag=True,
    default=False,
    help='Display only raw query results, without any headers or footers.',
)

HOSTNAME = OverridableOption('-H', '--hostname', type=types.HostnameType(), help='Hostname.')

TRANSPORT = OverridableOption(
    '-T',
    '--transport',
    type=types.PluginParamType(group='transports'),
    required=True,
    help='A transport plugin (as listed in `verdi plugin list aiida.transports`).',
)

SCHEDULER = OverridableOption(
    '-S',
    '--scheduler',
    type=types.PluginParamType(group='schedulers'),
    required=True,
    help='A scheduler plugin (as listed in `verdi plugin list aiida.schedulers`).',
)

USER = OverridableOption('-u', '--user', 'user', type=types.UserParamType(), help='Email address of the user.')

PORT = OverridableOption('-P', '--port', 'port', type=click.INT, help='Port number.')

FREQUENCY = OverridableOption('-F', '--frequency', 'frequency', type=click.INT)

TIMEOUT = OverridableOption(
    '-t',
    '--timeout',
    type=click.FLOAT,
    default=5.0,
    show_default=True,
    help='Time in seconds to wait for a response before timing out.',
)

WAIT = OverridableOption(
    '--wait/--no-wait',
    default=False,
    help='Wait for the action to be completed otherwise return as soon as it is scheduled.',
)

FORMULA_MODE = OverridableOption(
    '-f',
    '--formula-mode',
    type=click.Choice(['hill', 'hill_compact', 'reduce', 'group', 'count', 'count_compact']),
    default='hill',
    help='Mode for printing the chemical formula.',
)

TRAJECTORY_INDEX = OverridableOption(
    '-i',
    '--trajectory-index',
    'trajectory_index',
    type=click.INT,
    default=None,
    help='Specific step of the Trajectory to select.',
)

WITH_ELEMENTS = OverridableOption(
    '-e',
    '--with-elements',
    'elements',
    type=click.STRING,
    cls=MultipleValueOption,
    default=None,
    help='Only select objects containing these elements.',
)

WITH_ELEMENTS_EXCLUSIVE = OverridableOption(
    '-E',
    '--with-elements-exclusive',
    'elements_exclusive',
    type=click.STRING,
    cls=MultipleValueOption,
    default=None,
    help='Only select objects containing only these and no other elements.',
)

CONFIG_FILE = ConfigFileOption(
    '--config',
    type=types.FileOrUrl(),
    help='Load option values from configuration file in yaml format (local path or URL).',
)

IDENTIFIER = OverridableOption(
    '-i',
    '--identifier',
    'identifier',
    help='The type of identifier used for specifying each node.',
    default='pk',
    type=click.Choice(['pk', 'uuid']),
)

DICT_FORMAT = OverridableOption(
    '-f',
    '--format',
    'fmt',
    type=click.Choice(list(echo.VALID_DICT_FORMATS_MAPPING.keys())),
    default=next(iter(echo.VALID_DICT_FORMATS_MAPPING.keys())),
    help='The format of the output data.',
)

DICT_KEYS = OverridableOption(
    '-k', '--keys', type=click.STRING, cls=MultipleValueOption, help='Filter the output by one or more keys.'
)

DEBUG = OverridableOption(
    '--debug', is_flag=True, default=False, help='Show debug messages. Mostly relevant for developers.', hidden=True
)

PRINT_TRACEBACK = OverridableOption(
    '-t',
    '--print-traceback',
    is_flag=True,
    help='Print the full traceback in case an exception is raised.',
)

PATH = OverridableOption(
    '-p',
    '--path',
    type=click.Path(path_type=pathlib.Path),
    show_default=False,
    help='Base path for dump operations that write to disk.',
)

OVERWRITE = OverridableOption(
    '-o',
    '--overwrite',
    is_flag=True,
    default=False,
    show_default=True,
    help='Overwrite file/directory when writing to disk.',
)

SORT = OverridableOption(
    '--sort/--no-sort',
    'sort',
    is_flag=True,
    default=True,
    help='Sort the keys of the output YAML.',
    show_default=True,
)

ORGANIZE_BY_GROUPS = OverridableOption(
    '--organize-by-groups/--no-organize-by-groups',
    default=True,
    is_flag=True,
    type=bool,
    show_default=True,
    help='If the collection of nodes to be dumped is organized in groups, reproduce its hierarchy.',
)

INCLUDE_INPUTS = OverridableOption(
    '--include-inputs/--exclude-inputs',
    default=True,
    show_default=True,
    help='Include linked input nodes of `CalculationNode`(s).',
)

INCLUDE_OUTPUTS = OverridableOption(
    '--include-outputs/--exclude-outputs',
    default=False,
    show_default=True,
    help='Include linked output nodes of `CalculationNode`(s).',
)

INCLUDE_ATTRIBUTES = OverridableOption(
    '--include-attributes/--exclude-attributes',
    default=True,
    show_default=True,
    help='Include attributes in the `aiida_node_metadata.yaml` written for every `ProcessNode`.',
)

INCLUDE_EXTRAS = OverridableOption(
    '--include-extras/--exclude-extras',
    default=True,
    show_default=True,
    help='Include extras in the `aiida_node_metadata.yaml` written for every `ProcessNode`.',
)

FLAT = OverridableOption(
    '-f',
    '--flat',
    is_flag=True,
    default=False,
    help='Dump files in a flat directory for every step of a workflow.',
)

SYMLINK_CALCS = OverridableOption(
    '--symlink-calcs/--no-symlink-calcs',
    default=False,
    show_default=True,
    help='Symlink workflow sub-calculations to their own dedicated directories.',
    #   (must be used in conjunction with no-only-top-level-calcs)
)

DELETE_MISSING = OverridableOption(
    '--delete-missing/--no-delete-missing',
    default=True,
    show_default=True,
    help='If a previously dumped group or node is deleted from the DB, delete the corresponding dump directory.',
)

ALSO_UNGROUPED = OverridableOption(
    '--also-ungrouped/--no-also-ungrouped',
    default=False,
    show_default=True,
    help='Dump also data of nodes that are not part of any group.',
)

ONLY_TOP_LEVEL_CALCS = OverridableOption(
    '--only-top-level-calcs/--no-only-top-level-calcs',
    default=True,
    show_default=True,
    help='Dump calculations in their own dedicated directories, not just as part of the dumped workflow.',
)

ONLY_TOP_LEVEL_WORKFLOWS = OverridableOption(
    '--only-top-level-workflows/--no-only-top-level-workflows',
    default=True,
    show_default=True,
    help='If a top-level workflow calls sub-workflows, create a designated directory only for the top-level workflow.',
)

RELABEL_GROUPS = OverridableOption(
    '--relabel-groups/--no-relabel-groups',
    default=True,
    show_default=True,
    help='Update directories and log entries for the dumping if groups have been relabeled since the last dump.',
)

DUMP_UNSEALED = OverridableOption(
    '--dump-unsealed/--no-dump-unsealed',
    is_flag=True,
    default=False,
    show_default=True,
    help='Also allow the dumping of unsealed process nodes.',
)

FILTER_BY_LAST_DUMP_TIME = OverridableOption(
    '--filter-by-last-dump-time/--no-filter-by-last-dump-time',
    is_flag=True,
    default=True,
    show_default=True,
    help='Only select nodes whose `mtime` is after the last dump time.',
)

FILTER_BY_LAST_DUMP_TIME = OverridableOption(
    '--filter-by-last-dump-time/--no-filter-by-last-dump-time',
    is_flag=True,
    default=True,
    show_default=True,
    help='Only select nodes whose `mtime` is after the last dump time.',
)

START_DATE = OverridableOption(
    '--start-date',
    is_flag=False,
    default=None,
    show_default=True,
    help='Start date for node mtime range selection for profile dumping.',
)

END_DATE = OverridableOption(
    '--end-date',
    is_flag=False,
    default=None,
    show_default=True,
    help='End date for node mtime range selection for profile dumping.',
)
