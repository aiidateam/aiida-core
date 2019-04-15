# -*- coding: utf-8 -*-
import sys

from aiida.cmdline.baseclass import VerdiCommandWithSubcommands
import click
import sys
from tabulate import tabulate
from aiida.workflows2.process import Process
from aiida.common.links import LinkType

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.1.1"
__authors__ = "The AiiDA team."


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


class Workflow2(VerdiCommandWithSubcommands):
    """
    Manage the AiiDA worflow2 manager
    """

    def __init__(self):
        self.valid_subcommands = {
            self.list.__name__: (self.list, self.complete_none),
            self.tree.__name__: (self.tree, self.complete_none),
            self.checkpoint.__name__: (self.checkpoint, self.complete_none),
        }

    def list(self, *args):
        ctx = do_list.make_context('list', sys.argv[3:])
        with ctx:
            do_list.invoke(ctx)

    def tree(self, *args):
        ctx = do_tree.make_context('tree', sys.argv[3:])
        with ctx:
            do_tree.invoke(ctx)

    def checkpoint(self, *args):
        ctx = do_checkpoint.make_context('checkpoint', sys.argv[3:])
        with ctx:
            do_checkpoint.invoke(ctx)


@click.command('list', context_settings=CONTEXT_SETTINGS)
@click.option('-p', '--past-days', type=int,
              help="add a filter to show only workflows created in the past N"
                   " days")
@click.option('--limit', type=int, default=100,
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
    from aiida.orm.mixins import SealableMixin
    _SEALED_ATTRIBUTE_KEY = 'attributes.{}'.format(SealableMixin.SEALED_KEY)

    now = timezone.now()

    table = []
    for res in _build_query(limit=limit, past_days=past_days):
        calc = res['calculation']
        creation_time = str_timedelta(
            timezone.delta(calc['ctime'], now), negative_to_zero=True,
            max_num_fields=1)

        table.append([
            calc['id'],
            creation_time,
            calc['type'],
            str(calc[_SEALED_ATTRIBUTE_KEY])
        ])

    print(tabulate(table, headers=["PID", "Creation time", "Type", "Sealed"]))


@click.command('tree', context_settings=CONTEXT_SETTINGS)
@click.option('--node-label', default=Process.PROCESS_LABEL_ATTR, type=str)
@click.option('--depth', '-d', type=int, default=1)
@click.argument('pks', nargs=-1, type=int)
def do_tree(node_label, depth, pks):
    from aiida.backends.utils import load_dbenv, is_dbenv_loaded
    if not is_dbenv_loaded():
        load_dbenv()

    from aiida.orm import load_node
    from ete3 import Tree

    for pk in pks:
        node = load_node(pk=pk)
        t = Tree("({});".format(_build_tree(node, node_label, max_depth=depth)),
                 format=1)
        print(t.get_ascii(show_internal=True))


@click.command('checkpoint', context_settings=CONTEXT_SETTINGS)
@click.argument('pks', nargs=-1, type=int)
def do_checkpoint(pks):
    from aiida.workflows2.defaults import storage

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


def _ctime(node):
    return node.ctime


def _build_tree(node, node_label='type', show_pk=True, depth=0, max_depth=1):
    out_values = []

    if depth < max_depth:
        children =[]
        for child in sorted(node.get_outputs(link_type=LinkType.CALL), key=_ctime):
            children.append(_build_tree(child, node_label, depth=depth + 1,
                                        max_depth=max_depth))

        if children:
            out_values.append("(")
            out_values.append(", ".join(children))
            out_values.append(")")

    try:
        label = str(getattr(node, node_label))
    except AttributeError:
        try:
            label = node.get_attr(node_label)
        except AttributeError:
            label = node.__class__.__name__
    if show_pk:
        label += " [{}]".format(node.pk)

    out_values.append(label)

    return "".join(out_values)


def _build_query(order_by=None, limit=None, past_days=None):
    from aiida.orm.querybuilder import QueryBuilder
    from aiida.orm.calculation import Calculation
    import aiida.utils.timezone as timezone
    import datetime
    from aiida.orm.mixins import SealableMixin
    _SEALED_ATTRIBUTE_KEY = 'attributes.{}'.format(SealableMixin.SEALED_KEY)

    # The things that we want to get out
    calculation_projections = \
        ['id', 'ctime', 'type', _SEALED_ATTRIBUTE_KEY]

    now = timezone.now()

    # The things to filter by
    calculation_filters = {}

    if past_days is not None:
        n_days_ago = now - datetime.timedelta(days=past_days)
        calculation_filters['ctime'] = {'>': n_days_ago}

    qb = QueryBuilder()

    # ORDER
    if order_by is not None:
        qb.order_by({'calculation': [order_by]})

    # LIMIT
    if limit is not None:
        qb.limit(limit)

    # Build the quiery
    qb.append(
        cls=Calculation,
        filters=calculation_filters,
        project=calculation_projections,
        tag='calculation'
    )
    return qb.iterdict()
