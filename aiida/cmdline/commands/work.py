# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import logging
from functools import partial

import click
from tabulate import tabulate

from aiida.cmdline.baseclass import VerdiCommandWithSubcommands
from aiida.cmdline.commands import work, verdi
from aiida.utils.ascii_vis import print_tree_descending

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
LIST_CMDLINE_PROJECT_CHOICES = ['id', 'ctime', 'label', 'uuid', 'descr', 'mtime', 'state', 'sealed']

LOG_LEVEL_MAPPING = {
    levelname: i for levelname, i in [
    (logging.getLevelName(i), i) for i in range(logging.CRITICAL + 1)
]
    if not levelname.startswith('Level')
}
LOG_LEVELS = LOG_LEVEL_MAPPING.keys()


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
            'tree': (self.cli, self.complete_none),
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

        from aiida.common.pluginloader import plugin_list

        plugins = sorted(plugin_list('workflows'))
        # Do not return plugins that are already on the command line
        other_subargs = subargs[:subargs_idx] + subargs[subargs_idx + 1:]
        return_plugins = [_ for _ in plugins if _ not in other_subargs]
        return "\n".join(return_plugins)


@work.command('list', context_settings=CONTEXT_SETTINGS)
@click.option(
    '-p', '--past-days', type=int, default=1,
    help='add a filter to show only work calculations created in the past N days'
)
@click.option(
    '-a', '--all-states', 'all_states', is_flag=True,
    help='return all work calculations regardless of their sealed state'
)
@click.option(
    '-l', '--limit', type=int, default=None,
    help='limit the final result set to this size'
)
@click.option(
    '-P', '--project', type=click.Choice(LIST_CMDLINE_PROJECT_CHOICES),
    multiple=True, help='define the list of properties to show'
)
def do_list(past_days, all_states, limit, project):
    """
    Return a list of running workflows on screen
    """
    from aiida.backends.utils import load_dbenv, is_dbenv_loaded
    if not is_dbenv_loaded():
        load_dbenv()

    from aiida.common.utils import str_timedelta
    from aiida.utils import timezone
    from aiida.orm.mixins import Sealable
    from aiida.orm.calculation import Calculation

    _SEALED_ATTRIBUTE_KEY = 'attributes.{}'.format(Sealable.SEALED_KEY)
    _PROCESS_STATE_KEY = 'attributes.{}'.format(Calculation.PROCESS_STATE_KEY)

    if not project:
        project = ('id', 'ctime', 'label', 'state', 'sealed')  # default projections

    # Mapping of projections to list table headers.
    hmap_dict = {
        'id': 'PID',
        'ctime': 'Creation time',
        'label': 'Process Label',
        'uuid': 'UUID',
        'descr': 'Description',
        'mtime': 'Modification time'
    }

    def map_header(p):
        try:
            return hmap_dict[p]
        except KeyError:
            return p.capitalize()

    # Mapping of querybuilder keys that differ from projections.
    pmap_dict = {
        'label': 'attributes._process_label',
        'sealed': _SEALED_ATTRIBUTE_KEY,
        'state': _PROCESS_STATE_KEY,
        'descr': 'description',
    }

    def map_projection(p):
        try:
            return pmap_dict[p]
        except KeyError:
            return p

    # Mapping of to-string formatting of projections that do need it.
    rmap_dict = {
        'ctime': lambda calc: str_timedelta(timezone.delta(calc[map_projection('ctime')], now),
                                            negative_to_zero=True,
                                            max_num_fields=1),
        'mtime': lambda calc: str_timedelta(timezone.delta(calc[map_projection('mtime')], now),
                                            negative_to_zero=True,
                                            max_num_fields=1),
        'sealed': lambda calc: str(calc[map_projection('sealed')]),
        'state': lambda calc: str(calc[map_projection('state')]),
    }

    def map_result(p, obj):
        try:
            return rmap_dict[p](obj)
        except:
            return obj[map_projection(p)]

    mapped_projections = list(map(lambda p: map_projection(p), project))
    table = []

    for res in _build_query(limit=limit, projections=mapped_projections, past_days=past_days,
                            order_by={'ctime': 'desc'}):
        calc = res['calculation']
        if calc[_SEALED_ATTRIBUTE_KEY] and not all_states:
            continue
        table.append(list(map(lambda p: map_result(p, calc), project)))

    # Since we sorted by descending creation time, we revert the list to print the most
    # recent entries last
    table = table[::-1]

    print(tabulate(table, headers=(list(map(lambda p: map_header(p), project)))))


@work.command('report', context_settings=CONTEXT_SETTINGS)
@click.argument(
    'pk', nargs=1, type=int
)
@click.option(
    '-i', '--indent-size', type=int, default=2,
    help='Set the number of spaces to indent each level by'
)
@click.option(
    '-l', '--levelname', type=click.Choice(LOG_LEVELS), default='REPORT',
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
    from aiida.orm.backend import construct
    from aiida.orm.querybuilder import QueryBuilder
    from aiida.orm.calculation.work import WorkCalculation

    def get_report_messages(pk, depth, levelname):
        backend = construct()
        filters = {
            'objpk': pk,
        }

        entries = backend.log.find(filter_by=filters)
        entries = [
            entry for entry in entries
            if LOG_LEVEL_MAPPING[entry.levelname] >= LOG_LEVEL_MAPPING[levelname]
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
        print "{}{}".format(prepend, tree[0])
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
        print "No log messages recorded for this work calculation"
        return

    object_ids = [entry[0].id for entry in reports]
    levelnames = [len(entry[0].levelname) for entry in reports]
    width_id = len(str(max(object_ids)))
    width_levelname = max(levelnames)
    for entry, depth in reports:
        print '{time:%Y-%m-%d %H:%M:%S} [{id:<{width_id}} | {levelname:>{width_levelname}}]:{indent} {message}'.format(
            id=entry.id,
            levelname=entry.levelname,
            message=entry.message,
            time=entry.time,
            width_id=width_id,
            width_levelname=width_levelname,
            indent=' ' * (depth * indent_size)
        )

    return


@work.command('tree', context_settings=CONTEXT_SETTINGS)
@click.option('--node-label', default='_process_label', type=str)
@click.option('--depth', '-d', type=int, default=1)
@click.argument('pks', nargs=-1, type=int)
def tree(node_label, depth, pks):
    from aiida.backends.utils import load_dbenv, is_dbenv_loaded
    from aiida.utils.ascii_vis import build_tree
    if not is_dbenv_loaded():
        load_dbenv()

    from aiida.orm import load_node
    from ete3 import Tree

    for pk in pks:
        node = load_node(pk=pk)
        t = Tree("({});".format(build_tree(node, node_label, max_depth=depth)),
                 format=1)
        print(t.get_ascii(show_internal=True))


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
                print("Failed to load checkpoint {}".format(pk))
                print("{}: {}".format(e.__class__.__name__, e.message))
            else:
                print("Last checkpoint for calculation '{}'".format(pk))
                print(str(cp))
        except ValueError:
            print("Unable to show checkpoint for calculation '{}'".format(pk))


@work.command('kill', context_settings=CONTEXT_SETTINGS)
@click.argument('pks', nargs=-1, type=int)
def kill_old(pks):
    from aiida import try_load_dbenv
    try_load_dbenv()
    from aiida.orm import load_node
    from aiida.orm.calculation.work import WorkCalculation

    nodes = [load_node(pk) for pk in pks]
    workchain_nodes = [n for n in nodes if isinstance(n, WorkCalculation)]
    running_workchain_nodes = [n for n in nodes if not n.is_terminated]

    num_workchains = len(running_workchain_nodes)
    if num_workchains > 0:
        answer = click.prompt(
            'Are you sure you want to kill {} workflows and all their children? [y/n]'.format(
                num_workchains
            )
        ).lower()
        if answer == 'y':
            click.echo('Killing workflows.')
            for n in running_workchain_nodes:
                n.kill()
        else:
            click.echo('Abort!')
    else:
        click.echo('No pks of valid running workchains given.')


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
                print("Failed to kill '{}': {}".format(pk, e.message))


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
                print("Failed to pause '{}': {}".format(pk, e.message))


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
                print("Failed to play '{}': {}".format(pk, e.message))


@work.command('status', context_settings=CONTEXT_SETTINGS)
@click.argument('pks', nargs=-1, type=int)
def status(pks):
    from aiida import try_load_dbenv
    try_load_dbenv()
    import aiida.orm
    from aiida.utils.ascii_vis import print_call_graph

    if not pks:
        click.echo("No pks specified")
    else:
        for pk in pks:
            calc_node = aiida.orm.load_node(pk)
            print_call_graph(calc_node)


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
    from aiida.common.pluginloader import plugin_list, get_plugin

    if entry_point:
        try:
            plugin = get_plugin('workflows', entry_point)
        except (LoadingPluginFailed, MissingPluginError) as exception:
            click.echo("Error: {}".format(exception))
        else:
            click.echo(plugin.get_description())
    else:
        entry_points = sorted(plugin_list('workflows'))
        if entry_points:
            click.echo('Registered workflow entry points:')
            for entry_point in entry_points:
                click.echo("* {}".format(entry_point))
            click.echo("\nPass the entry point of a workflow as an argument to display detailed information")
        else:
            click.echo("# No workflows found")


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
    print("pk={}, subject={}, body={}".format(sender, subject, body))


def _build_query(projections=None, order_by=None, limit=None, past_days=None):
    import datetime
    from aiida.utils import timezone
    from aiida.orm.querybuilder import QueryBuilder
    from aiida.orm.calculation.work import WorkCalculation

    # Define filters
    filters = {}

    if past_days is not None:
        n_days_ago = timezone.now() - datetime.timedelta(days=past_days)
        filters['ctime'] = {'>': n_days_ago}

    # Build the query
    qb = QueryBuilder()
    qb.append(
        cls=WorkCalculation,
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
