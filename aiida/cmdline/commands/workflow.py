# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The CLI for legacy workflows."""
import click

from aiida.cmdline.baseclass import VerdiCommandWithSubcommands
from aiida.cmdline.commands import verdi_workflow, verdi
from aiida.cmdline.params.types import LegacyWorkflowParamType
from aiida.cmdline.params.options.multivalue import MultipleValueOption
from aiida.cmdline.params import options
from aiida.cmdline.utils.decorators import with_dbenv, deprecated_command
from aiida.cmdline.utils import echo

DEPRECATION_MSG = 'Legacy workflows have been deprecated in AiiDA v1.0.'


def format_pk(workflow):
    return '(pk: {})'.format(workflow.pk)


class Workflow(VerdiCommandWithSubcommands):
    """
    Manage the AiiDA legacy worflow manager

    Valid subcommands are:
    * list: list the running workflows running and their state. Pass a -h
    |        option for further help on valid options.
    * kill: kill a given workflow
    * report: show the report of a given workflow
    """

    def __init__(self):
        """
        A dictionary with valid commands and functions to be called:
        list.
        """
        super(Workflow, self).__init__()
        self.valid_subcommands = {
            'list': (self.cli, self.complete_none),
            'kill': (self.cli, self.complete_none),
            'report': (self.cli, self.complete_none),
            'logshow': (self.cli, self.complete_none),
        }

    @staticmethod
    def cli(*args):  # pylint: disable=unused-argument
        verdi()  # pylint: disable=no-value-for-parameter


@verdi_workflow.command('logshow')
@click.argument('workflows', type=LegacyWorkflowParamType(), nargs=-1)
@deprecated_command(DEPRECATION_MSG)
def workflow_logshow(workflows):
    """Show the log for each workflow in a list of WORKFLOWS."""
    from aiida.backends.utils import get_log_messages
    for workflow in workflows:
        log_messages = get_log_messages(workflow)
        label_str = ' [{}]'.format(workflow.label) if workflow.label else ''
        state = workflow.get_state()
        echo.echo('*** {pk}{label}: {state}'.format(pk=format_pk(workflow), label=label_str, state=state))

        if workflow.get_report():
            echo.echo('Print the report with `verdi workflow report {}`'.format(format_pk(workflow)))
        else:
            echo.echo('*** Report is empty')

        if log_messages:
            echo.echo('*** {} LOG MESSAGES:'.format(len(log_messages)))
        else:
            echo.echo('*** NO LOG MESSAGES')

        for log in log_messages:
            echo.echo('+-> {} at {}'.format(log['levelname'], log['time']))
            echo.echo('\n'.join(['|\t{}'.format(msg) for msg in log.get('message', '').splitlines()]))


@verdi_workflow.command('kill')
@options.FORCE()
@click.option('-v', '--verbose', is_flag=True)
@click.argument('workflows', type=LegacyWorkflowParamType(), nargs=-1)
@deprecated_command(DEPRECATION_MSG)
@with_dbenv()
def workflow_kill(force, verbose, workflows):
    """Kill each in a list of WORKFLOWS (given by ID, UUID or label)"""
    from aiida.orm.workflow import WorkflowKillError, WorkflowUnkillable
    plural = '' if len(workflows) <= 1 else 's'
    if not force and workflows:
        click.confirm('Are you sure you want to kill {} workflow{}?'.format(len(workflows), plural), abort=True)
    counter = 0
    for workflow in workflows:
        try:
            workflow.kill(verbose=verbose)
            counter += 1
        except WorkflowKillError as error:
            echo.echo_error(error.__class__.__name__)
            for msg in error.error_message_list:
                echo.echo_error('\t' + msg)
        except WorkflowUnkillable as error:
            echo.echo_error(error.__class__.__name__)
            echo.echo_error(error.message)

    if verbose:
        echo.echo_success('{} workflow{} killed.'.format(counter, plural))


@verdi_workflow.command('report')
@click.argument('workflow', type=LegacyWorkflowParamType())
@deprecated_command(DEPRECATION_MSG)
def workflow_report(workflow):
    """Report on a WORKFLOW (given by ID, UUID or label)."""
    echo.echo('### WORKFLOW {} ###'.format(format_pk(workflow)))
    echo.echo('\n'.join(workflow.get_report()))


@verdi_workflow.command('list')
@click.option('-s', '--short', is_flag=True, help='short form (only subworkflows and steps, no calculations)')
@options.ALL_STATES(help='show all existing AiiDA workflows, not only running ones')
@click.option('-d', '--depth', type=int, default=16,
    help='show only steps down to a depth of DEPTH levels in subworkflows (0 means only the parent)')  # yapf: disable
@click.option(
    '-p', '--past-days', type=int, help='add a filter to show only workflows created in the past PAST_DAYS days')
@click.option('-W', '--workflows', default=[], type=LegacyWorkflowParamType(), cls=MultipleValueOption,
    help='limit the listing to these workflows')  # yapf: disable
@deprecated_command(DEPRECATION_MSG)
@with_dbenv()
def workflow_list(short, all_states, depth, past_days, workflows):
    """List legacy workflows"""
    from aiida.backends.utils import get_workflow_list
    from aiida.orm.workflow import get_workflow_info
    from aiida.orm.backend import construct_backend  # pylint: disable=no-name-in-module
    tab_size = 2

    backend = construct_backend()
    current_user = backend.users.get_automatic_user()

    wf_list = get_workflow_list(
        [workflow.pk for workflow in workflows], user=current_user, all_states=all_states, n_days_ago=past_days)
    for workflow in wf_list:
        if not workflow.is_subworkflow() or workflow in workflows:
            echo.echo('\n'.join(get_workflow_info(workflow, tab_size=tab_size, short=short, depth=depth)))

    if not workflows:
        if all_states:
            echo.echo_info('# No workflows found')
        else:
            echo.echo_info('# No running workflows found')
