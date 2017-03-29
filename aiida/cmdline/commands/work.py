# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import sys
import click

from aiida.cmdline.baseclass import VerdiCommandWithSubcommands
from tabulate import tabulate



CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


class Work(VerdiCommandWithSubcommands):
    """
    Manage the AiiDA worflow2 manager
    """

    def __init__(self):
        self.valid_subcommands = {
            self.list.__name__: (self.list, self.complete_none),
            self.report.__name__: (self.report, self.complete_none),
            self.tree.__name__: (self.tree, self.complete_none),
            self.checkpoint.__name__: (self.checkpoint, self.complete_none),
        }

    def list(self, *args):
        ctx = do_list.make_context('list', list(args))
        with ctx:
            do_list.invoke(ctx)

    def report(self, *args):
        ctx = do_report.make_context('report', sys.argv[3:])
        with ctx:
            do_report.invoke(ctx)

    def tree(self, *args):
        ctx = do_tree.make_context('tree', list(args))
        with ctx:
            do_tree.invoke(ctx)

    def checkpoint(self, *args):
        ctx = do_checkpoint.make_context('checkpoint', list(args))
        with ctx:
            do_checkpoint.invoke(ctx)


@click.command('list', context_settings=CONTEXT_SETTINGS)
@click.option('-p', '--past-days', type=int,
              help="add a filter to show only workflows created in the past N"
                   " days")

@click.option('-l', '--limit', type=int, default=None,
              help="Limit to this many results")
def do_list(past_days, limit):
    """
    Return a list of running workflows on screen
    """
    from aiida.common.utils import str_timedelta
    from aiida.backends.utils import load_dbenv, is_dbenv_loaded
    if not is_dbenv_loaded():
        load_dbenv()
    import aiida.utils.timezone as timezone
    from aiida.orm.mixins import Sealable
    _SEALED_ATTRIBUTE_KEY = 'attributes.{}'.format(Sealable.SEALED_KEY)

    now = timezone.now()

    table = []
    for res in _build_query(limit=limit, past_days=past_days, order_by={'ctime': 'desc'}):
        calc = res['calculation']
        creation_time = str_timedelta(
            timezone.delta(calc['ctime'], now), negative_to_zero=True,
            max_num_fields=1)

        table.append([
            calc['id'],
            creation_time,
            calc['attributes._process_label'],
            str(calc[_SEALED_ATTRIBUTE_KEY])
        ])

    # Revert table:
    # in this way, I order by 'desc', so I start by the most recent, but then 
    # I print this as the las one (like 'verdi calculation list' does)
    # This is useful when 'limit' is set to not None
    table = table[::-1]
    print(tabulate(table, headers=["PID", "Creation time", "ProcessLabel", "Sealed"]))


@click.command('report', context_settings=CONTEXT_SETTINGS)
@click.argument('pk', nargs=1, type=int)
@click.option('-l', '--levelname',
    type=click.Choice(['DEBUG', 'INFO', 'REPORT', 'WARNING', 'ERROR', 'CRITICAL']),
    default=None,
    help='Filter the results by name of the log level'
)
@click.option('-o', '--order-by',
    type=click.Choice(['id', 'time', 'levelname']),
    default='time',
    help='Order the results by column'
)
def do_report(pk, levelname, order_by):
    """
    Return a list of recorded log messages for the WorkChain with pk=PK
    """
    from aiida.backends.utils import load_dbenv, is_dbenv_loaded
    if not is_dbenv_loaded():
        load_dbenv()

    from aiida.orm.backend import construct
    from aiida.orm.log import OrderSpecifier, ASCENDING, DESCENDING

    backend  = construct()
    order_by = [OrderSpecifier(order_by, ASCENDING)]
    filters  = {
        'objpk' : pk,
    }

    if levelname:
        filters['levelname'] = levelname

    entries    = backend.log.find(filter_by=filters, order_by=order_by)
    object_ids = [entry.id for entry in entries]
    levelnames = [len(entry.levelname) for entry in entries]
    width_id   = len(str(max(object_ids)))
    width_levelname = max(levelnames)

    for entry in entries:
        print '{time:%Y-%m-%d %H:%M:%S} [{id:<{width_id}} | {levelname:>{width_levelname}}]: {message}'.format(
            id=entry.id,
            levelname=entry.levelname,
            message=entry.message,
            time=entry.time,
            width_id=width_id,
            width_levelname=width_levelname
        )


@click.command('tree', context_settings=CONTEXT_SETTINGS)
@click.option('--node-label', default='_process_label', type=str)
@click.option('--depth', '-d', type=int, default=1)
@click.argument('pks', nargs=-1, type=int)
def do_tree(node_label, depth, pks):
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


@click.command('checkpoint', context_settings=CONTEXT_SETTINGS)
@click.argument('pks', nargs=-1, type=int)
def do_checkpoint(pks):
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
                print("Exception: {}".format(e.message))
            else:
                print("Last checkpoint for calculation '{}'".format(pk))
                print(str(cp))
        except ValueError:
            print("Unable to show checkpoint for calculation '{}'".format(pk))


def _build_query(order_by=None, limit=None, past_days=None):
    from aiida.orm.querybuilder import QueryBuilder
    from aiida.orm.calculation.work import WorkCalculation
    import aiida.utils.timezone as timezone
    import datetime
    from aiida.orm.mixins import Sealable
    _SEALED_ATTRIBUTE_KEY = 'attributes.{}'.format(Sealable.SEALED_KEY)

    # The things that we want to get out
    calculation_projections = \
        ['id', 'ctime', 'attributes._process_label', _SEALED_ATTRIBUTE_KEY]

    now = timezone.now()

    # The things to filter by
    calculation_filters = {}

    if past_days is not None:
        n_days_ago = now - datetime.timedelta(days=past_days)
        calculation_filters['ctime'] = {'>': n_days_ago}

    qb = QueryBuilder()

    # Build the quiery
    qb.append(
        cls=WorkCalculation,
        filters=calculation_filters,
        project=calculation_projections,
        tag='calculation'
    )

    # ORDER
    if order_by is not None:
        qb.order_by({'calculation': order_by})

    # LIMIT
    if limit is not None:
        qb.limit(limit)

    return qb.iterdict()
