# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import click
import logging
from tabulate import tabulate

from aiida.cmdline.baseclass import VerdiCommandWithSubcommands
from aiida.cmdline.commands import work, verdi
from aiida.common.log import LOG_LEVELS
from aiida.utils.cli.types import LazyChoice


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
LIST_CMDLINE_PROJECT_CHOICES = ('pk', 'uuid', 'ctime', 'mtime', 'state', 'process_state', 'finish_status', 'sealed', 'process_label', 'label', 'description', 'type')
LIST_CMDLINE_PROJECT_DEFAULT = ('pk', 'ctime', 'state', 'process_label')


def valid_process_states():
    from plumpy import ProcessState
    return ([state.value for state in ProcessState])


class Work(VerdiCommandWithSubcommands):
    """
    Manage the (new) AiiDA workflows
    """

    def __init__(self):
        self.valid_subcommands = {
            'list': (self.cli, self.complete_none),
            'pause': (self.cli, self.complete_none),
            'play': (self.cli, self.complete_none),
            'report': (self.cli, self.complete_none),
            'status': (self.cli, self.complete_none),
            'checkpoint': (self.cli, self.complete_none),
            'kill': (self.cli, self.complete_none),
            'plugins': (self.cli, self.complete_plugins),
            'watch': (self.cli, self.complete_none),
        }

    def cli(self, *args):
        verdi()

    def complete_plugins(self, subargs_idx, subargs):
        """
        Return the list of plugins registered under the 'workflows' category
        """
        from aiida import try_load_dbenv
        try_load_dbenv()

        from aiida.plugins.entry_point import get_entry_point_names

        plugins = get_entry_point_names('aiida.workflows')
        # Do not return plugins that are already on the command line
        other_subargs = subargs[:subargs_idx] + subargs[subargs_idx + 1:]
        return_plugins = [_ for _ in plugins if _ not in other_subargs]
        return '\n'.join(return_plugins)


@work.command('list', context_settings=CONTEXT_SETTINGS)
@click.option(
    '-p', '--past-days', type=int, default=1, metavar='N',
    help='Only include entries created in the past N days'
)
@click.option(
    '-a', '--all-states', 'all_states', is_flag=True,
    help='Include all entries, regardless of process state'
)
@click.option(
    '-S', '--process-state', type=LazyChoice(valid_process_states),
    help='Only include entries with this process state'
)
@click.option(
    '-f', '--finish-status', type=click.INT,
    help='Only include entries with this finish status'
)
@click.option(
    '-n', '--failed', is_flag=True,
    help='Only include entries that are failed, i.e. whose finish status is non-zero'
)
@click.option(
    '-l', '--limit', type=int, default=None,
    help='Limit the number of entries to display'
)
@click.option(
    '-P', '--project', type=click.Choice(LIST_CMDLINE_PROJECT_CHOICES), default=LIST_CMDLINE_PROJECT_DEFAULT,
    multiple=True, help='Define the list of properties to show'
)
@click.option(
    '-r', '--raw', is_flag=True,
    help='Only print the query result, without any headers, footers or other additional information'
)
def do_list(past_days, all_states, process_state, finish_status, failed, limit, project, raw):
    """
    Return a list of work calculations that are still running
    """
    from plumpy import ProcessState
    from aiida.backends.utils import load_dbenv, is_dbenv_loaded
    if not is_dbenv_loaded():
        load_dbenv()

    from aiida.cmdline.utils.common import print_last_process_state_change
    from aiida.common.utils import str_timedelta
    from aiida.orm.mixins import Sealable
    from aiida.orm.calculation import Calculation
    from aiida.utils import timezone


    SEALED_KEY = 'attributes.{}'.format(Sealable.SEALED_KEY)
    PROCESS_LABEL_KEY = 'attributes.{}'.format(Calculation.PROCESS_LABEL_KEY)
    PROCESS_STATE_KEY = 'attributes.{}'.format(Calculation.PROCESS_STATE_KEY)
    FINISH_STATUS_KEY = 'attributes.{}'.format(Calculation.FINISH_STATUS_KEY)
    TERMINAL_STATES = [ProcessState.FINISHED.value, ProcessState.KILLED.value, ProcessState.EXCEPTED.value]

    now = timezone.now()

    projection_label_map = {
        'pk': 'PK',
        'uuid': 'UUID',
        'ctime': 'Creation',
        'mtime': 'Modification',
        'type': 'Type',
        'state': 'State',
        'process_state': 'Process state',
        'finish_status': 'Finish status',
        'sealed': 'Sealed',
        'process_label': 'Process label',
        'label': 'Label',
        'description': 'Description',
    }

    projection_attribute_map = {
        'pk': 'id',
        'uuid': 'uuid',
        'ctime': 'ctime',
        'mtime': 'mtime',
        'type': 'type',
        'process_state': PROCESS_STATE_KEY,
        'finish_status': FINISH_STATUS_KEY,
        'sealed': SEALED_KEY,
        'process_label': PROCESS_LABEL_KEY,
        'label': 'label',
        'description': 'description',
    }

    projection_format_map = {
        'pk': lambda value: value['id'],
        'uuid': lambda value: value['uuid'],
        'ctime': lambda value: str_timedelta(timezone.delta(value['ctime'], now), negative_to_zero=True, max_num_fields=1),
        'mtime': lambda value: str_timedelta(timezone.delta(value['mtime'], now), negative_to_zero=True, max_num_fields=1),
        'type': lambda value: value['type'],
        'state': lambda value: '{} | {}'.format(value[PROCESS_STATE_KEY].capitalize() if value[PROCESS_STATE_KEY] else None, value[FINISH_STATUS_KEY]),
        'process_state': lambda value: value[PROCESS_STATE_KEY].capitalize(),
        'finish_status': lambda value: value[FINISH_STATUS_KEY],
        'sealed': lambda value: 'True' if value[SEALED_KEY] == 1 else 'False',
        'process_label': lambda value: value[PROCESS_LABEL_KEY],
        'label': lambda value: value['label'],
        'description': lambda value: value['description'],
    }

    table = []
    filters = {}

    if not all_states:
        filters[PROCESS_STATE_KEY] = {'!in': TERMINAL_STATES}

    if process_state:
        filters[PROCESS_STATE_KEY] = {'==': process_state}

    if failed:
        filters[PROCESS_STATE_KEY] = {'==': ProcessState.FINISHED.value}
        filters[FINISH_STATUS_KEY] = {'!==': 0}

    if finish_status is not None:
        filters[PROCESS_STATE_KEY] = {'==': ProcessState.FINISHED.value}
        filters[FINISH_STATUS_KEY] = {'==': finish_status}

    query = _build_query(
        limit=limit,
        projections=projection_attribute_map.values(),
        filters=filters,
        past_days=past_days,
        order_by={'ctime': 'desc'}
    )

    for result in query:

        table_row = []
        calculation = result['calculation']

        for p in project:
            value = projection_format_map[p](calculation)
            table_row.append(value)

        table.append(table_row)

    # Since we sorted by descending creation time, we revert the list to print the most recent entries last
    projection_labels = list(map(lambda p: projection_label_map[p], project))
    table = table[::-1]

    if raw:
        tabulated = tabulate(table, tablefmt='plain')
        click.echo(tabulated)
    else:
        tabulated = tabulate(table, headers=projection_labels)
        click.echo(tabulated)
        click.echo('\nTotal results: {}\n'.format(len(table)))
        print_last_process_state_change(process_type='work')


@work.command('report', context_settings=CONTEXT_SETTINGS)
@click.argument(
    'pk', nargs=1, type=int
)
@click.option(
    '-i', '--indent-size', type=int, default=2,
    help='Set the number of spaces to indent each level by'
)
@click.option(
    '-l', '--levelname', type=click.Choice(LOG_LEVELS.keys()), default='REPORT',
    help='Filter the results by name of the log level'
)
@click.option(
    '-o', '--order-by', type=click.Choice(['id', 'time', 'levelname']), default='time',
    help='Order the results by column'
)
@click.option(
    '-m', '--max-depth', 'max_depth', type=int, default=None,
    help='Limit the number of levels to be printed'
)
def report(pk, levelname, order_by, indent_size, max_depth):
    """
    Return a list of recorded log messages for the WorkChain with pk=PK
    """
    from aiida.backends.utils import load_dbenv, is_dbenv_loaded
    if not is_dbenv_loaded():
        load_dbenv()

    import itertools
    from aiida.orm.backend import construct_backend
    from aiida.orm.querybuilder import QueryBuilder
    from aiida.orm.calculation.work import WorkCalculation

    def get_report_messages(pk, depth, levelname):
        backend = construct_backend()
        filters = {
            'objpk': pk,
        }

        entries = backend.log.find(filter_by=filters)
        entries = [
            entry for entry in entries
            if LOG_LEVELS[entry.levelname] >= LOG_LEVELS[levelname]
        ]
        return [(_, depth) for _ in entries]

    def get_subtree(pk, level=0):
        qb = QueryBuilder()
        qb.append(
            cls=WorkCalculation,
            filters={'id': pk},
            tag='workcalculation'
        )
        qb.append(
            cls=WorkCalculation,
            project=['id'],
            # In the future, we should specify here the type of link
            # for now, CALL links are the only ones allowing calc-calc
            # (we here really want instead to follow CALL links)
            output_of='workcalculation',
            tag='subworkchains'
        )
        result = list(itertools.chain(*qb.distinct().all()))

        # This will return a single flat list of tuples, where the first element
        # corresponds to the WorkChain pk and the second element is an integer
        # that represents its level of nesting within the chain
        return [(pk, level)] + list(itertools.chain(*[get_subtree(subpk, level=level + 1) for subpk in result]))

    def print_subtree(tree, prepend=""):
        click.echo("{}{}".format(prepend, tree[0]))
        for subtree in tree[1]:
            print_subtree(subtree, prepend=prepend + "  ")

    workchain_tree = get_subtree(pk)

    if max_depth:
        report_list = [get_report_messages(pk, depth, levelname) for pk, depth in workchain_tree if depth < max_depth]
    else:
        report_list = [get_report_messages(pk, depth, levelname) for pk, depth in workchain_tree]

    reports = list(itertools.chain(*report_list))
    reports.sort(key=lambda r: r[0].time)

    if reports is None or len(reports) == 0:
        click.echo("No log messages recorded for this work calculation")
        return

    object_ids = [entry[0].id for entry in reports]
    levelnames = [len(entry[0].levelname) for entry in reports]
    width_id = len(str(max(object_ids)))
    width_levelname = max(levelnames)
    for entry, depth in reports:
        click.echo('{time:%Y-%m-%d %H:%M:%S} [{id:<{width_id}} | {levelname:>{width_levelname}}]:{indent} {message}'.format(
            id=entry.id,
            levelname=entry.levelname,
            message=entry.message,
            time=entry.time,
            width_id=width_id,
            width_levelname=width_levelname,
            indent=' ' * (depth * indent_size)
        ))

    return


@work.command('checkpoint', context_settings=CONTEXT_SETTINGS)
@click.argument('pks', nargs=-1, type=int)
def checkpoint(pks):
    from aiida.backends.utils import load_dbenv, is_dbenv_loaded
    if not is_dbenv_loaded():
        load_dbenv()
    import aiida.work.persistence
    storage = aiida.work.persistence.get_default()

    for pk in pks:
        try:
            try:
                cp = storage.load_checkpoint(pk)
            except BaseException as e:
                click.echo("Failed to load checkpoint {}".format(pk))
                click.echo("{}: {}".format(e.__class__.__name__, e.message))
            else:
                click.echo("Last checkpoint for calculation '{}'".format(pk))
                click.echo(str(cp))
        except ValueError:
            click.echo("Unable to show checkpoint for calculation '{}'".format(pk))


@work.command('kill', context_settings=CONTEXT_SETTINGS)
@click.argument('pks', nargs=-1, type=int)
def kill(pks):
    from aiida import try_load_dbenv
    try_load_dbenv()
    from aiida import work

    with work.new_blocking_control_panel() as control_panel:
        for pk in pks:
            try:
                if control_panel.kill_process(pk):
                    click.echo("Killed '{}'".format(pk))
                else:
                    click.echo("Problem killing '{}'".format(pk))
            except (work.RemoteException, work.DeliveryFailed) as e:
                click.echo("Failed to kill '{}': {}".format(pk, e.message))


@work.command('pause', context_settings=CONTEXT_SETTINGS)
@click.argument('pks', nargs=-1, type=int)
def pause(pks):
    from aiida import try_load_dbenv
    try_load_dbenv()
    from aiida import work

    with work.new_blocking_control_panel() as control_panel:
        for pk in pks:
            try:
                if control_panel.pause_process(pk):
                    click.echo("Paused '{}'".format(pk))
                else:
                    click.echo("Problem pausing '{}'".format(pk))
            except (work.RemoteException, work.DeliveryFailed) as e:
                click.echo("Failed to pause '{}': {}".format(pk, e.message))


@work.command('play', context_settings=CONTEXT_SETTINGS)
@click.argument('pks', nargs=-1, type=int)
def play(pks):
    from aiida import try_load_dbenv
    try_load_dbenv()
    from aiida import work

    with work.new_blocking_control_panel() as control_panel:
        for pk in pks:
            try:
                if control_panel.play_process(pk):
                    click.echo("Played '{}'".format(pk))
                else:
                    click.echo("Problem playing '{}'".format(pk))
            except (work.RemoteException, work.DeliveryFailed) as e:
                click.echo("Failed to play '{}': {}".format(pk, e.message))


@work.command('status', context_settings=CONTEXT_SETTINGS)
@click.argument('pks', nargs=-1, type=int)
def status(pks):
    from aiida import try_load_dbenv
    try_load_dbenv()
    from aiida.orm import load_node
    from aiida.utils.ascii_vis import format_call_graph

    if not pks:
        click.echo('No pks specified')
    else:
        for pk in pks:
            calc_node = load_node(pk)
            graph = format_call_graph(calc_node)
            click.echo(graph)


def _create_status_info(calc_node):
    status_line = _format_status_line(calc_node)
    called = calc_node.called
    if called:
        return status_line, [_create_status_info(child) for child in called]
    else:
        return status_line


def _format_status_line(calc_node):
    from aiida.orm.calculation.work import WorkCalculation
    from aiida.orm.calculation.job import JobCalculation

    if isinstance(calc_node, WorkCalculation):
        label = calc_node.get_attr('_process_label')
        state = calc_node.get_attr('process_state')
    elif isinstance(calc_node, JobCalculation):
        label = type(calc_node).__name__
        state = str(calc_node.get_state())
    else:
        raise TypeError("Unknown type")
    return "{} <pk={}> [{}]".format(label, calc_node.pk, state)


@work.command('plugins', context_settings=CONTEXT_SETTINGS)
@click.argument('entry_point', type=str, required=False)
def plugins(entry_point):
    from aiida.backends.utils import load_dbenv, is_dbenv_loaded
    if not is_dbenv_loaded():
        load_dbenv()
    from aiida.common.exceptions import LoadingPluginFailed, MissingPluginError
    from aiida.plugins.entry_point import get_entry_point_names, load_entry_point

    if entry_point:
        try:
            plugin = load_entry_point('aiida.workflows', entry_point)
        except (LoadingPluginFailed, MissingPluginError) as exception:
            click.echo("Error: {}".format(exception))
        else:
            click.echo(plugin.get_description())
    else:
        entry_points = get_entry_point_names('aiida.workflows')
        if entry_points:
            click.echo('Registered workflow entry points:')
            for entry_point in entry_points:
                click.echo("* {}".format(entry_point))
            click.echo("\nPass the entry point as an argument to display detailed information")
        else:
            click.echo("No workflow plugins found")


@work.command('watch', context_settings=CONTEXT_SETTINGS)
@click.argument('pks', nargs=-1, type=int)
def watch(pks):
    from aiida import try_load_dbenv
    try_load_dbenv()
    import kiwipy
    import aiida.work.rmq

    communicator = aiida.work.rmq.create_communicator()

    for pk in pks:
        communicator.add_broadcast_subscriber(kiwipy.BroadcastFilter(_print, sender=pk))

    try:
        communicator.await()
    except (SystemExit, KeyboardInterrupt):
        communicator.close()


def _print(body, sender, subject, correlation_id):
    click.echo("pk={}, subject={}, body={}".format(sender, subject, body))


def _build_query(projections=None, filters=None, order_by=None, limit=None, past_days=None):
    import datetime
    from aiida.orm.calculation import Calculation
    from aiida.orm.calculation.function import FunctionCalculation
    from aiida.orm.calculation.work import WorkCalculation
    from aiida.orm.querybuilder import QueryBuilder
    from aiida.utils import timezone

    # Define filters
    if filters is None:
        filters = {}

    # Until the QueryBuilder supports passing a tuple of classes in the append method, we have to query
    # for the base Calculation class and match the type to get all WorkCalculation AND FunctionCalculation nodes
    filters['or'] = [
        {'type': WorkCalculation._plugin_type_string},
        {'type': FunctionCalculation._plugin_type_string}
    ]

    if past_days is not None:
        n_days_ago = timezone.now() - datetime.timedelta(days=past_days)
        filters['ctime'] = {'>': n_days_ago}

    # Build the query
    qb = QueryBuilder()
    qb.append(
        cls=Calculation,
        filters=filters,
        project=projections,
        tag='calculation'
    )

    # Ordering of queryset
    if order_by is not None:
        qb.order_by({'calculation': order_by})

    # Limiting the queryset
    if limit is not None:
        qb.limit(limit)

    return qb.iterdict()
