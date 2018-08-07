# -*- coding: utf-8 -*-
# pylint: disable=too-many-arguments
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi work` command."""
import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments, options, types
from aiida.cmdline.utils import decorators, echo
from aiida.cmdline.utils.query.calculation import CalculationQueryBuilder
from aiida.common.log import LOG_LEVELS


@verdi.group('work')
def verdi_work():
    """Inspect and manage work calculations."""
    pass


@verdi_work.command('list')
@options.PROJECT(
    type=click.Choice(CalculationQueryBuilder.valid_projections), default=CalculationQueryBuilder.default_projections)
@options.ALL(help='Show all entries, regardless of their process state.')
@options.PROCESS_STATE()
@options.EXIT_STATUS()
@options.FAILED()
@options.PAST_DAYS()
@options.LIMIT()
@options.RAW()
@decorators.with_dbenv()
def work_list(all_entries, process_state, exit_status, failed, past_days, limit, project, raw):
    """Show a list of work calculations that are still running."""
    from tabulate import tabulate
    from aiida.cmdline.utils.common import print_last_process_state_change
    from aiida.orm.calculation.function import FunctionCalculation
    from aiida.orm.calculation.work import WorkCalculation

    node_types = (WorkCalculation, FunctionCalculation)

    builder = CalculationQueryBuilder()
    filters = builder.get_filters(all_entries, process_state, exit_status, failed, node_types=node_types)
    query_set = builder.get_query_set(filters=filters, past_days=past_days, limit=limit)
    projected = builder.get_projected(query_set, projections=project)

    headers = projected.pop(0)

    if raw:
        tabulated = tabulate(projected, tablefmt='plain')
        echo.echo(tabulated)
    else:
        tabulated = tabulate(projected, headers=headers)
        echo.echo(tabulated)
        echo.echo('\nTotal results: {}\n'.format(len(projected)))
        print_last_process_state_change(process_type='work')


@verdi_work.command('report')
@arguments.CALCULATIONS(
    type=types.CalculationParamType(sub_classes=('aiida.calculations:work', 'aiida.calculations:function')))
@click.option('-i', '--indent-size', type=int, default=2, help='set the number of spaces to indent each level by')
@click.option(
    '-l',
    '--levelname',
    type=click.Choice(LOG_LEVELS.keys()),
    default='REPORT',
    help='filter the results by name of the log level')
@click.option('-m', '--max-depth', 'max_depth', type=int, default=None, help='limit the number of levels to be printed')
def work_report(calculations, levelname, indent_size, max_depth):
    # pylint: disable=too-many-locals
    """
    Return a list of recorded log messages for the WorkChain with pk=PK
    """
    import itertools
    from aiida.orm.backend import construct_backend
    from aiida.orm.querybuilder import QueryBuilder
    from aiida.orm.calculation.work import WorkCalculation

    def get_report_messages(pk, depth, levelname):
        """Return list of log messages with given levelname and their depth for a node with a given pk."""
        backend = construct_backend()
        filters = {
            'objpk': pk,
        }

        entries = backend.logs.find(filter_by=filters)
        entries = [entry for entry in entries if LOG_LEVELS[entry.levelname] >= LOG_LEVELS[levelname]]
        return [(_, depth) for _ in entries]

    def get_subtree(pk, level=0):
        """Get a nested tree of work calculation nodes and their nesting level starting from this pk."""
        builder = QueryBuilder()
        builder.append(cls=WorkCalculation, filters={'id': pk}, tag='workcalculation')
        builder.append(
            cls=WorkCalculation,
            project=['id'],
            # In the future, we should specify here the type of link
            # for now, CALL links are the only ones allowing calc-calc
            # (we here really want instead to follow CALL links)
            output_of='workcalculation',
            tag='subworkchains')
        result = list(itertools.chain(*builder.distinct().all()))

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
            report_list = [
                get_report_messages(pk, depth, levelname) for pk, depth in workchain_tree if depth < max_depth
            ]
        else:
            report_list = [get_report_messages(pk, depth, levelname) for pk, depth in workchain_tree]

        reports = list(itertools.chain(*report_list))
        reports.sort(key=lambda r: r[0].time)

        if not reports:
            echo.echo("No log messages recorded for this work calculation")
            return

        object_ids = [entry[0].id for entry in reports]
        levelnames = [len(entry[0].levelname) for entry in reports]
        width_id = len(str(max(object_ids)))
        width_levelname = max(levelnames)
        for entry, depth in reports:
            echo.echo('{time:%Y-%m-%d %H:%M:%S} [{id:<{width_id}} | {levelname:>{width_levelname}}]:{indent} {message}'.
                      format(
                          id=entry.id,
                          levelname=entry.levelname,
                          message=entry.message,
                          time=entry.time,
                          width_id=width_id,
                          width_levelname=width_levelname,
                          indent=' ' * (depth * indent_size)))

    return


@verdi_work.command('show')
@arguments.CALCULATIONS(
    type=types.CalculationParamType(sub_classes=('aiida.calculations:work', 'aiida.calculations:function')))
@decorators.with_dbenv()
def work_show(calculations):
    """Show a summary for one or multiple calculations."""
    from aiida.cmdline.utils.common import get_node_info

    for calculation in calculations:
        echo.echo(get_node_info(calculation))


@verdi_work.command('status')
@arguments.CALCULATIONS(
    type=types.CalculationParamType(sub_classes=('aiida.calculations:work', 'aiida.calculations:function')))
def work_status(calculations):
    """
    Print the status of work calculations
    """
    from aiida.utils.ascii_vis import format_call_graph

    for calculation in calculations:
        graph = format_call_graph(calculation)
        echo.echo(graph)


@verdi_work.command('plugins')
@click.argument('entry_point', type=click.STRING, required=False)
@decorators.with_dbenv()
def work_plugins(entry_point):
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
            for registered_entry_point in entry_points:
                echo.echo("* {}".format(registered_entry_point))

            echo.echo('')
            echo.echo_info('Pass the entry point as an argument to display detailed information')
        else:
            echo.echo_error('No workflow plugins found')


def _build_query(projections=None, filters=None, order_by=None, limit=None, past_days=None):
    """Build and execute a query for work type calculations given certain filters and options."""
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
    filters['or'] = [{'type': WorkCalculation.plugin_type_string}, {'type': FunctionCalculation.plugin_type_string}]

    if past_days is not None:
        n_days_ago = timezone.now() - datetime.timedelta(days=past_days)
        filters['ctime'] = {'>': n_days_ago}

    # Build the query
    builder = QueryBuilder()
    builder.append(cls=Calculation, filters=filters, project=projections, tag='calculation')

    # Ordering of queryset
    if order_by is not None:
        builder.order_by({'calculation': order_by})

    # Limiting the queryset
    if limit is not None:
        builder.limit(limit)

    return builder.iterdict()
