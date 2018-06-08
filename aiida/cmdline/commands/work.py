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
from tabulate import tabulate

from aiida.cmdline.baseclass import VerdiCommandWithSubcommands
from aiida.cmdline.commands import verdi_work, verdi
from aiida.cmdline.params import arguments, options, types
from aiida.cmdline.utils import decorators, echo
from aiida.common.log import LOG_LEVELS


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
LIST_CMDLINE_PROJECT_CHOICES = ('pk', 'uuid', 'ctime', 'mtime', 'state', 'process_state', 'finish_status', 'sealed', 'process_label', 'label', 'description', 'type')
LIST_CMDLINE_PROJECT_DEFAULT = ('pk', 'ctime', 'state', 'process_label')


class Work(VerdiCommandWithSubcommands):
    """
    Manage the AiiDA workflows
    """

    def __init__(self):
        self.valid_subcommands = {
            'kill': (self.cli, self.complete_none),
            'list': (self.cli, self.complete_none),
            'pause': (self.cli, self.complete_none),
            'play': (self.cli, self.complete_none),
            'plugins': (self.cli, self.complete_plugins),
            'report': (self.cli, self.complete_none),
            'status': (self.cli, self.complete_none),
            'watch': (self.cli, self.complete_none),
        }

    def cli(self, *args):
        verdi()

    @decorators.with_dbenv()
    def complete_plugins(self, subargs_idx, subargs):
        """
        Return the list of plugins registered under the 'workflows' category
        """
        from aiida.plugins.entry_point import get_entry_point_names

        other_subargs = subargs[:subargs_idx] + subargs[subargs_idx + 1:]
        return_plugins = [_ for _ in get_entry_point_names('aiida.workflows') if _ not in other_subargs]
        return '\n'.join(return_plugins)


@verdi_work.command('list', context_settings=CONTEXT_SETTINGS)
@options.PROJECT(type=click.Choice(LIST_CMDLINE_PROJECT_CHOICES), default=LIST_CMDLINE_PROJECT_DEFAULT)
@options.PROCESS_STATE()
@options.FINISH_STATUS()
@options.FAILED()
@options.PAST_DAYS()
@options.LIMIT()
@options.ALL()
@options.RAW()
@decorators.with_dbenv()
def do_list(past_days, all, process_state, finish_status, failed, limit, project, raw):
    """
    Return a list of work calculations that are still running
    """
    from aiida.cmdline.utils.common import print_last_process_state_change
    from aiida.common.utils import str_timedelta
    from aiida.orm.mixins import Sealable
    from aiida.orm.calculation import Calculation
    from aiida.utils import timezone
    from aiida.work import ProcessState


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

    if not all:
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
        echo.echo(tabulated)
    else:
        tabulated = tabulate(table, headers=projection_labels)
        echo.echo(tabulated)
        echo.echo('\nTotal results: {}\n'.format(len(table)))
        print_last_process_state_change(process_type='work')


@verdi_work.command('report', context_settings=CONTEXT_SETTINGS)
@arguments.CALCULATIONS(type=types.CalculationParamType(sub_classes=('aiida.calculations:work', 'aiida.calculations:function')))
@click.option(
    '-i', '--indent-size', type=int, default=2,
    help='set the number of spaces to indent each level by'
)
@click.option(
    '-l', '--levelname', type=click.Choice(LOG_LEVELS.keys()), default='REPORT',
    help='filter the results by name of the log level'
)
@click.option(
    '-o', '--order-by', type=click.Choice(['id', 'time', 'levelname']), default='time',
    help='order the results by column'
)
@click.option(
    '-m', '--max-depth', 'max_depth', type=int, default=None,
    help='limit the number of levels to be printed'
)
def report(calculations, levelname, order_by, indent_size, max_depth):
    """
    Return a list of recorded log messages for the WorkChain with pk=PK
    """
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
        echo.echo("{}{}".format(prepend, tree[0]))
        for subtree in tree[1]:
            print_subtree(subtree, prepend=prepend + "  ")

    for calculation in calculations:

        workchain_tree = get_subtree(calculation.pk)

        if max_depth:
            report_list = [get_report_messages(pk, depth, levelname) for pk, depth in workchain_tree if depth < max_depth]
        else:
            report_list = [get_report_messages(pk, depth, levelname) for pk, depth in workchain_tree]

        reports = list(itertools.chain(*report_list))
        reports.sort(key=lambda r: r[0].time)

        if reports is None or len(reports) == 0:
            echo.echo("No log messages recorded for this work calculation")
            return

        object_ids = [entry[0].id for entry in reports]
        levelnames = [len(entry[0].levelname) for entry in reports]
        width_id = len(str(max(object_ids)))
        width_levelname = max(levelnames)
        for entry, depth in reports:
            echo.echo('{time:%Y-%m-%d %H:%M:%S} [{id:<{width_id}} | {levelname:>{width_levelname}}]:{indent} {message}'.format(
                id=entry.id,
                levelname=entry.levelname,
                message=entry.message,
                time=entry.time,
                width_id=width_id,
                width_levelname=width_levelname,
                indent=' ' * (depth * indent_size)
            ))

    return


@verdi_work.command('kill', context_settings=CONTEXT_SETTINGS)
@arguments.CALCULATIONS(type=types.CalculationParamType(sub_classes=('aiida.calculations:work', 'aiida.calculations:function')))
def kill(calculations):
    """
    Kill work calculations
    """
    from aiida.work import RemoteException, DeliveryFailed, new_blocking_control_panel

    with new_blocking_control_panel() as control_panel:
        for calculation in calculations:

            if calculation.is_terminated:
                echo.echo_error('Calculation<{}> is already terminated'.format(calculation.pk))
                continue

            try:
                if control_panel.kill_process(calculation.pk):
                    echo.echo_success('killed Calculation<{}>'.format(calculation.pk))
                else:
                    echo.echo_error('problem killing Calculation<{}>'.format(calculation.pk))
            except (RemoteException, DeliveryFailed) as e:
                echo.echo_error('failed to kill Calculation<{}>: {}'.format(calculation.pk, e.message))


@verdi_work.command('pause', context_settings=CONTEXT_SETTINGS)
@arguments.CALCULATIONS(type=types.CalculationParamType(sub_classes=('aiida.calculations:work', 'aiida.calculations:function')))
def pause(calculations):
    """
    Pause running work calculations
    """
    from aiida.work import RemoteException, DeliveryFailed, new_blocking_control_panel

    with new_blocking_control_panel() as control_panel:
        for calculation in calculations:

            if calculation.is_terminated:
                echo.echo_error('Calculation<{}> is already terminated'.format(calculation.pk))
                continue

            try:
                if control_panel.pause_process(calculation.pk):
                    echo.echo_success('paused Calculation<{}>'.format(calculation.pk))
                else:
                    echo.echo_error('problem pausing Calculation<{}>'.format(calculation.pk))
            except (RemoteException, DeliveryFailed) as e:
                echo.echo_error('failed to pause Calculation<{}>: {}'.format(calculation.pk, e.message))


@verdi_work.command('play', context_settings=CONTEXT_SETTINGS)
@arguments.CALCULATIONS(type=types.CalculationParamType(sub_classes=('aiida.calculations:work', 'aiida.calculations:function')))
def play(calculations):
    """
    Play paused work calculations
    """
    from aiida.work import RemoteException, DeliveryFailed, new_blocking_control_panel

    with new_blocking_control_panel() as control_panel:
        for calculation in calculations:

            if calculation.is_terminated:
                echo.echo_error('Calculation<{}> is already terminated'.format(calculation.pk))
                continue

            try:
                if control_panel.play_process(calculation.pk):
                    echo.echo_success('played Calculation<{}>'.format(calculation.pk))
                else:
                    echo.echo_critical('problem playing Calculation<{}>'.format(calculation.pk))
            except (RemoteException, DeliveryFailed) as e:
                echo.echo_critical('failed to play Calculation<{}>: {}'.format(calculation.pk, e.message))


@verdi_work.command('watch', context_settings=CONTEXT_SETTINGS)
@arguments.CALCULATIONS(type=types.CalculationParamType(sub_classes=('aiida.calculations:work', 'aiida.calculations:function')))
def watch(calculations):
    """
    Watch the state transitions for work calculations
    """
    from kiwipy import BroadcastFilter
    from aiida.work.rmq import create_communicator

    def _print(body, sender, subject, correlation_id):
        echo.echo("pk={}, subject={}, body={}".format(sender, subject, body))

    communicator = create_communicator()

    for calculation in calculations:

        if calculation.is_terminated:
            echo.echo_warning('Calculation<{}> is already terminated'.format(calculation.pk))
        communicator.add_broadcast_subscriber(BroadcastFilter(_print, sender=calculation.pk))

    try:
        communicator.await()
    except (SystemExit, KeyboardInterrupt):
        try:
            communicator.disconnect()
        except RuntimeError:
            pass


@verdi_work.command('status', context_settings=CONTEXT_SETTINGS)
@arguments.CALCULATIONS(type=types.CalculationParamType(sub_classes=('aiida.calculations:work', 'aiida.calculations:function')))
def status(calculations):
    """
    Print the status of work calculations
    """
    from aiida.utils.ascii_vis import format_call_graph

    for calculation in calculations:
        graph = format_call_graph(calculation)
        echo.echo(graph)


@verdi_work.command('plugins', context_settings=CONTEXT_SETTINGS)
@click.argument('entry_point', type=click.STRING, required=False)
@decorators.with_dbenv()
def plugins(entry_point):
    """
    Print a list of registered workflow plugins or details of a specific workflow plugin
    """
    from aiida.common.exceptions import LoadingPluginFailed, MissingPluginError
    from aiida.plugins.entry_point import get_entry_point_names, load_entry_point

    if entry_point:
        try:
            plugin = load_entry_point('aiida.workflows', entry_point)
        except (LoadingPluginFailed, MissingPluginError) as exception:
            echo.echo_critical(exception)
        else:
            echo.echo_info(entry_point)
            echo.echo(plugin.get_description())
    else:
        entry_points = get_entry_point_names('aiida.workflows')
        if entry_points:
            echo.echo('Registered workflow entry points:')
            for entry_point in entry_points:
                echo.echo("* {}".format(entry_point))

            echo.echo_info('Pass the entry point as an argument to display detailed information', prefix='\n')
        else:
            echo.echo_error('No workflow plugins found')


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
