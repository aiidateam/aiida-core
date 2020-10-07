# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module with pre-defined reusable commandline options that can be used as `click` decorators."""

# AUTO-GENERATED

__all__ = (
    'graph_traversal_rules', 'PROFILE', 'CALCULATION', 'CALCULATIONS', 'CODE', 'CODES', 'COMPUTER', 'COMPUTERS',
    'DATUM', 'DATA', 'GROUP', 'GROUPS', 'NODE', 'NODES', 'FORCE', 'SILENT', 'VISUALIZATION_FORMAT', 'INPUT_FORMAT',
    'EXPORT_FORMAT', 'ARCHIVE_FORMAT', 'NON_INTERACTIVE', 'DRY_RUN', 'USER_EMAIL', 'USER_FIRST_NAME', 'USER_LAST_NAME',
    'USER_INSTITUTION', 'DB_BACKEND', 'DB_ENGINE', 'DB_HOST', 'DB_PORT', 'DB_USERNAME', 'DB_PASSWORD', 'DB_NAME',
    'REPOSITORY_PATH', 'PROFILE_ONLY_CONFIG', 'PROFILE_SET_DEFAULT', 'PREPEND_TEXT', 'APPEND_TEXT', 'LABEL',
    'DESCRIPTION', 'INPUT_PLUGIN', 'CALC_JOB_STATE', 'PROCESS_STATE', 'PROCESS_LABEL', 'TYPE_STRING', 'EXIT_STATUS',
    'FAILED', 'LIMIT', 'PROJECT', 'ORDER_BY', 'PAST_DAYS', 'OLDER_THAN', 'ALL', 'ALL_STATES', 'ALL_USERS',
    'GROUP_CLEAR', 'RAW', 'HOSTNAME', 'TRANSPORT', 'SCHEDULER', 'USER', 'PORT', 'FREQUENCY', 'VERBOSE', 'TIMEOUT',
    'FORMULA_MODE', 'TRAJECTORY_INDEX', 'WITH_ELEMENTS', 'WITH_ELEMENTS_EXCLUSIVE', 'DEBUG', 'PRINT_TRACEBACK'
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
    return ([
        ProcessState.CREATED.value,
        ProcessState.WAITING.value,
        ProcessState.RUNNING.value,
    ])


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


PROFILE = OverridableOption(
    '-p',
    '--profile',
    'profile',
    type=types.ProfileParamType(),
    default=defaults.get_default_profile,
    help='Execute the command for this profile instead of the default profile.'
)

CALCULATION = OverridableOption(
    '-C',
    '--calculation',
    'calculation',
    type=types.CalculationParamType(),
    help='A single calculation identified by its ID or UUID.'
)

CALCULATIONS = OverridableOption(
    '-C',
    '--calculations',
    'calculations',
    type=types.CalculationParamType(),
    cls=MultipleValueOption,
    help='One or multiple calculations identified by their ID or UUID.'
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
    help='One or multiple codes identified by their ID, UUID or label.'
)

COMPUTER = OverridableOption(
    '-Y',
    '--computer',
    'computer',
    type=types.ComputerParamType(),
    help='A single computer identified by its ID, UUID or label.'
)

COMPUTERS = OverridableOption(
    '-Y',
    '--computers',
    'computers',
    type=types.ComputerParamType(),
    cls=MultipleValueOption,
    help='One or multiple computers identified by their ID, UUID or label.'
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
    help='One or multiple data identified by their ID, UUID or label.'
)

GROUP = OverridableOption(
    '-G', '--group', 'group', type=types.GroupParamType(), help='A single group identified by its ID, UUID or label.'
)

SOURCE_GROUP = OverridableOption(
    '-s',
    '--source-group',
    'source_group',
    type=types.GroupParamType(),
    help='A single group identified by its ID, UUID or label.'
)

TARGET_GROUP = OverridableOption(
    '-t',
    '--target-group',
    'target_group',
    type=types.GroupParamType(),
    help='A single group identified by its ID, UUID or label.'
)

GROUPS = OverridableOption(
    '-G',
    '--groups',
    'groups',
    type=types.GroupParamType(),
    cls=MultipleValueOption,
    help='One or multiple groups identified by their ID, UUID or label.'
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
    help='One or multiple nodes identified by their ID or UUID.'
)

FORCE = OverridableOption('-f', '--force', is_flag=True, default=False, help='Do not ask for confirmation.')

from .config import *
from .main import *
from .multivalue import *
from .overridable import *

__all__ = (
    'ALL',
    'ALL_STATES',
    'ALL_USERS',
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
    'ConfigFileOption',
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
    'DESCRIPTION',
    'DICT_FORMAT',
    'DICT_KEYS',
    'DRY_RUN',
    'EXIT_STATUS',
    'EXPORT_FORMAT',
    'FAILED',
    'FORCE',
    'FORMULA_MODE',
    'FREQUENCY',
    'GROUP',
    'GROUPS',
    'GROUP_CLEAR',
    'HOSTNAME',
    'IDENTIFIER',
    'INPUT_FORMAT',
    'INPUT_PLUGIN',
    'LABEL',
    'LIMIT',
    'MultipleValueOption',
    'NODE',
    'NODES',
    'NON_INTERACTIVE',
    'OLDER_THAN',
    'ORDER_BY',
    'ORDER_DIRECTION',
    'OverridableOption',
    'PAST_DAYS',
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
    'REPOSITORY_PATH',
    'SCHEDULER',
    'SILENT',
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

# yapf: enable
