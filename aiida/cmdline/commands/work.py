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
from aiida.cmdline.commands import work, verdi
from aiida.cmdline.baseclass import VerdiCommandWithSubcommands

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

LOG_LEVEL_MAPPING = {
    levelname: i for levelname, i in [
        (logging.getLevelName(i), i) for i in range(logging.CRITICAL + 1)
    ]
    if not levelname.startswith('Level')
}
LOG_LEVELS = LOG_LEVEL_MAPPING.keys()

class Work(VerdiCommandWithSubcommands):
    """
    Manage the AiiDA worflow manager
    """

    def __init__(self):
        self.valid_subcommands = {
            'list': (self.cli, self.complete_none),
            'report': (self.cli, self.complete_none),
            'tree': (self.cli, self.complete_none),
            'checkpoint': (self.cli, self.complete_none),
            'kill': (self.cli, self.complete_none),
        }

    def cli(self, *args):
        verdi()


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
def do_list(past_days, all_states, limit):
    """
    Return a list of running workflows on screen
    """
    from aiida.backends.utils import load_dbenv, is_dbenv_loaded
    if not is_dbenv_loaded():
        load_dbenv()

    from aiida.common.utils import str_timedelta
    from aiida.utils import timezone
    from aiida.orm.mixins import Sealable
    from aiida.orm.calculation.work import WorkCalculation

    _SEALED_ATTRIBUTE_KEY = 'attributes.{}'.format(Sealable.SEALED_KEY)
    _ABORTED_ATTRIBUTE_KEY = 'attributes.{}'.format(WorkCalculation.ABORTED_KEY)
    _FAILED_ATTRIBUTE_KEY = 'attributes.{}'.format(WorkCalculation.FAILED_KEY)
    _FINISHED_ATTRIBUTE_KEY = 'attributes.{}'.format(WorkCalculation.FINISHED_KEY)

    table = []
    for res in _build_query(limit=limit, past_days=past_days, order_by={'ctime': 'desc'}):

        calculation = res['calculation']

        creation_time = str_timedelta(
            timezone.delta(calculation['ctime'], timezone.now()), negative_to_zero=True,
            max_num_fields=1
        )

        if _SEALED_ATTRIBUTE_KEY in calculation and calculation[_SEALED_ATTRIBUTE_KEY]:
            sealed = True
        else:
            sealed = False

        if _FINISHED_ATTRIBUTE_KEY in calculation and calculation[_FINISHED_ATTRIBUTE_KEY]:
            state = 'Finished'
        elif _FAILED_ATTRIBUTE_KEY in calculation and calculation[_FAILED_ATTRIBUTE_KEY]:
            state = 'Failed'
        elif _ABORTED_ATTRIBUTE_KEY in calculation and calculation[_ABORTED_ATTRIBUTE_KEY]:
            state = 'Aborted'
        elif sealed:
            # If it is not in terminal state but sealed, we have an inconsistent state
            state = 'Unknown'
        else:
            state = 'Running'

        # By default we only display unsealed entries, unless all_states flag is set
        if sealed and not all_states:
            continue

        table.append([
            calculation['id'],
            creation_time,
            state,
            str(sealed),
            calculation['attributes._process_label']
        ])

    # Since we sorted by descending creation time, we revert the list to print the most
    # recent entries last
    table = table[::-1]

    print(tabulate(table, headers=['PK', 'Creation', 'State', 'Sealed', 'ProcessLabel']))


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
    from aiida.orm.log import OrderSpecifier, ASCENDING, DESCENDING
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
                checkpoint = storage.get_checkpoint_state(pk)
            except BaseException as e:
                print("Failed to load checkpoint {}".format(pk))
                print("Exception: {}".format(e.message))
            else:
                print("Last checkpoint for calculation '{}'".format(pk))
                print(str(checkpoint))
        except ValueError:
            print("Unable to show checkpoint for calculation '{}'".format(pk))

@work.command('kill', context_settings=CONTEXT_SETTINGS)
@click.argument('pks', nargs=-1, type=int)
def kill(pks):
    from aiida import try_load_dbenv
    try_load_dbenv()
    from aiida.orm import load_node
    from aiida.orm.calculation.work import WorkCalculation

    nodes = [load_node(pk) for pk in pks]
    workchain_nodes = [n for n in nodes if isinstance(n, WorkCalculation)]
    running_workchain_nodes = [n for n in nodes if not n.has_finished()]

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


def _build_query(order_by=None, limit=None, past_days=None):
    import datetime
    from aiida.utils import timezone
    from aiida.orm.mixins import Sealable
    from aiida.orm.querybuilder import QueryBuilder
    from aiida.orm.calculation.work import WorkCalculation

    _SEALED_ATTRIBUTE_KEY = 'attributes.{}'.format(Sealable.SEALED_KEY)
    _ABORTED_ATTRIBUTE_KEY = 'attributes.{}'.format(WorkCalculation.ABORTED_KEY)
    _FAILED_ATTRIBUTE_KEY = 'attributes.{}'.format(WorkCalculation.FAILED_KEY)
    _FINISHED_ATTRIBUTE_KEY = 'attributes.{}'.format(WorkCalculation.FINISHED_KEY)

    calculation_projections = [
        'id', 'ctime', 'attributes._process_label',
        _SEALED_ATTRIBUTE_KEY, _ABORTED_ATTRIBUTE_KEY, _FAILED_ATTRIBUTE_KEY, _FINISHED_ATTRIBUTE_KEY
    ]

    # Define filters
    calculation_filters = {}

    if past_days is not None:
        n_days_ago = timezone.now() - datetime.timedelta(days=past_days)
        calculation_filters['ctime'] = {'>': n_days_ago}

    # Build the query
    qb = QueryBuilder()
    qb.append(
        cls=WorkCalculation,
        filters=calculation_filters,
        project=calculation_projections,
        tag='calculation'
    )

    # Ordering of queryset
    if order_by is not None:
        qb.order_by({'calculation': order_by})

    # Limiting the queryset
    if limit is not None:
        qb.limit(limit)

    return qb.iterdict()
