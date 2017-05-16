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
import threading
from aiida.cmdline.baseclass import VerdiCommandWithSubcommands



CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


class Work(VerdiCommandWithSubcommands):
    """
    Manage the (new) AiiDA workflows
    """

    def __init__(self):
        self.valid_subcommands = {
            self.abort.__name__: (self.abort, self.complete_none),
            self.list.__name__: (self.list, self.complete_none),
            self.pause.__name__: (self.pause, self.complete_none),
            self.play.__name__: (self.play, self.complete_none),
            self.report.__name__: (self.report, self.complete_none),
            self.status.__name__: (self.status, self.complete_none),
            self.tree.__name__: (self.tree, self.complete_none),
            self.checkpoint.__name__: (self.checkpoint, self.complete_none),
            self.watch.__name__: (self.watch, self.complete_none),
        }

    def abort(self, *args):
        ctx = do_abort.make_context('abort', sys.argv[3:])
        with ctx:
            do_abort.invoke(ctx)

    def list(self, *args):
        ctx = do_list.make_context('list', sys.argv[3:])
        with ctx:
            do_list.invoke(ctx)

    def pause(self, *args):
        ctx = do_pause.make_context('pause', sys.argv[3:])
        with ctx:
            do_pause.invoke(ctx)

    def play(self, *args):
        ctx = do_play.make_context('play', sys.argv[3:])
        with ctx:
            do_play.invoke(ctx)

    def report(self, *args):
        ctx = do_report.make_context('report', sys.argv[3:])
        with ctx:
            do_report.invoke(ctx)

    def status(self, *args):
        ctx = do_status.make_context('status', sys.argv[3:])
        with ctx:
            do_status.invoke(ctx)

    def tree(self, *args):
        ctx = do_tree.make_context('tree', sys.argv[3:])
        with ctx:
            do_tree.invoke(ctx)

    def checkpoint(self, *args):
        ctx = do_checkpoint.make_context('checkpoint', sys.argv[3:])
        with ctx:
            do_checkpoint.invoke(ctx)

    def watch(self, *args):
        ctx = do_watch.make_context('watch', sys.argv[3:])
        with ctx:
            do_watch.invoke(ctx)


def _create_control_response_str(response):
    host_info = response[plum.rmq.util.HOST_KEY]
    return "{} (pid={}@{})".format(
        response[plum.rmq.control.RESULT_KEY],
        host_info['pid'], host_info['hostname'])


def _print_control_response(pid, response):
    if response is None:
        msg = "Response timed out"
    else:
        msg = _create_control_response_str(response)

    click.echo("{}: {}".format(pid, msg))


@click.command('abort', context_settings=CONTEXT_SETTINGS)
@click.option('-m', '--msg', type=str,
              help="A message indicating the reason for aborting")
@click.option('-t', '--timeout', type=float, default=1.,
              help="Wait for this long for the abort message to be acknowledged")
@click.argument('pids', type=str, nargs=-1)
def do_abort(msg, timeout, pids):
    from aiida.backends.utils import load_dbenv, is_dbenv_loaded
    if not is_dbenv_loaded():
        load_dbenv()
    from aiida.work.globals import get_rmq_control_panel

    cp = get_rmq_control_panel()
    for pid in pids:
        response = cp.control.abort(int(pid), msg, timeout)
        _print_control_response(pid, response)


@click.command('pause', context_settings=CONTEXT_SETTINGS)
@click.option('-t', '--timeout', type=float, default=1.,
              help="Wait for this long for the pause message to be acknowledged")
@click.argument('pids', type=str, nargs=-1)
def do_pause(timeout, pids):
    from aiida.backends.utils import load_dbenv, is_dbenv_loaded
    if not is_dbenv_loaded():
        load_dbenv()
    from aiida.work.globals import get_rmq_control_panel

    cp = get_rmq_control_panel()
    for pid in pids:
        response = cp.control.pause(int(pid), timeout)
        _print_control_response(pid, response)


@click.command('play', context_settings=CONTEXT_SETTINGS)
@click.option('-t', '--timeout', type=float,
              help="Wait for this long for the play message to be acknowledged")
@click.argument('pids', type=str, nargs=-1)
def do_play(timeout, pids):
    from aiida.backends.utils import load_dbenv, is_dbenv_loaded
    if not is_dbenv_loaded():
        load_dbenv()
    from aiida.work.globals import get_rmq_control_panel

    cp = get_rmq_control_panel()
    for pid in pids:
        response = cp.control.play(int(pid), timeout)
        _print_control_response(pid, response)


@click.command('list', context_settings=CONTEXT_SETTINGS)
@click.option('-p', '--past-days', type=int, default=1,
              help="add a filter to show only workflows created in the past N"
                   " days")
@click.option('-a', '--all', 'all_nodes', is_flag=True, help='Return all nodes. Overrides the -l flag')
@click.option('-l', '--limit', type=int, default=None,
              help="Limit to this many results")
def do_list(past_days, all_nodes, limit):
    """
    Return a list of running workflows on screen
    """
    from tabulate import tabulate
    from aiida.common.utils import str_timedelta
    from aiida.backends.utils import load_dbenv, is_dbenv_loaded
    if not is_dbenv_loaded():
        load_dbenv()
    import aiida.utils.timezone as timezone
    from aiida.orm.mixins import Sealable
    _SEALED_ATTRIBUTE_KEY = 'attributes.{}'.format(Sealable.SEALED_KEY)

    now = timezone.now()

    if all_nodes:
        past_days = None

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

    import itertools
    from aiida.orm.backend import construct
    from aiida.orm.log import OrderSpecifier, ASCENDING, DESCENDING
    from aiida.orm.querybuilder import QueryBuilder
    from aiida.orm.calculation.work import WorkCalculation

    def get_report_messages(pk, levelname, order_by):
        backend = construct()
        order_by = [OrderSpecifier(order_by, ASCENDING)]
        filters = {
            'objpk' : pk,
        }

        if levelname:
            filters['levelname'] = levelname

        entries = backend.log.find(filter_by=filters, order_by=order_by)

        if entries is None or len(entries) == 0:
            return []
        else:
            return entries

    qb = QueryBuilder(with_dbpath=False)
    qb.append(
        cls=WorkCalculation,
        filters={'id': pk},
        tag='workcalculation'
    )
    qb.append(
        cls=WorkCalculation,
        project=['id'],
        descendant_of='workcalculation',
        tag='subworkchains'
    )
    result = list(itertools.chain(*qb.distinct().all()))
    result.append(pk)
    result.sort()

    reports = []
    for pk in result:
        entries = get_report_messages(pk, levelname, order_by)
        reports.extend(entries)

    reports.sort(key=lambda r: r.time)

    if reports is None or len(reports) == 0:
        print "No log messages recorded for this work calculation"
        return

    object_ids = [entry.id for entry in reports]
    levelnames = [len(entry.levelname) for entry in reports]
    width_id = len(str(max(object_ids)))
    width_levelname = max(levelnames)
    for entry in reports:
        print '{time:%Y-%m-%d %H:%M:%S} [{id:<{width_id}} | {levelname:>{width_levelname}}]: {message}'.format(
            id=entry.id,
            levelname=entry.levelname,
            message=entry.message,
            time=entry.time,
            width_id=width_id,
            width_levelname=width_levelname
        )

    return


@click.command('status', context_settings=CONTEXT_SETTINGS)
@click.option('-t', '--timeout', type=float, default=1.,
              help="wait for this long for all responses from servers")
def do_status(timeout):
    """
    Return a list of running workflows on screen
    """
    from aiida.backends.utils import load_dbenv, is_dbenv_loaded
    if not is_dbenv_loaded():
        load_dbenv()
    from aiida.work.globals import get_rmq_control_panel

    cp = get_rmq_control_panel()
    cp.status.request(timeout=timeout, callback=_print_status)


_print_lock = threading.Lock()


def _print_status(response):
    global _print_lock
    from plum.rmq.status import PROCS_KEY
    from plum.rmq.util import HOST_KEY
    from tabulate import tabulate

    procs = response[PROCS_KEY]
    if not procs:
        return

    table = []
    for pid, status in procs.iteritems():
        table.append([
            pid,
            _create_time_str_from_timestamp(status['creation_time']),
            status['state'],
            "Yes" if status['playing'] else "No",
            status['waiting_on']
        ])

    host_info = response[HOST_KEY]
    with _print_lock:
        print("{} pid={}".format(host_info['hostname'], host_info['pid']))
        print(tabulate(table, headers=["PID", "ctime", "State", "Playing?", 'Waiting on']))


def _create_time_str_from_timestamp(timestamp):
    import aiida.utils.timezone as timezone

    dt = timezone.make_aware(datetime.fromtimestamp(timestamp))
    fmt = ["%H:%M:%S"]
    today = timezone.now().date()
    if dt.date() < today:
        fmt.append("%Y-%m-%d")

    return dt.strftime(" ".join(fmt))


@click.command('tree', context_settings=CONTEXT_SETTINGS)
@click.option('--node-label', default='_process_label', type=str)
@click.option('--depth', '-d', type=int, default=1)
@click.argument('pks', nargs=-1, type=int)
def do_tree(node_label, depth, pks):
    from aiida.utils.ascii_vis import build_tree
    from aiida.backends.utils import load_dbenv, is_dbenv_loaded
    if not is_dbenv_loaded():
        load_dbenv()

    from aiida.orm import load_node
    from ete3 import Tree

    for pk in pks:
        node = load_node(pk=pk)
        t = Tree("({});".format(build_tree(node, node_label, max_depth=depth)),
                 format=1)
        print(t.get_ascii(show_internal=True))


@click.group('checkpoint', context_settings=CONTEXT_SETTINGS)
def do_checkpoint():
    from aiida.backends.utils import load_dbenv, is_dbenv_loaded
    if not is_dbenv_loaded():
        load_dbenv()


@do_checkpoint.command()
@click.argument('pks', nargs=-1, type=int)
def show(pks):
    import aiida.work.persistence
    import pprint

    storage = aiida.work.persistence.get_global_persistence()

    for pk in pks:
        try:
            try:
                cp = storage.load_checkpoint(pk)
            except BaseException as e:
                print("Failed to load checkpoint {}".format(pk))
                print("{}: {}".format(e.__class__.__name__, e.message))
            else:
                print("Last checkpoint for calculation pid='{}'".format(pk))
                pprint.pprint(cp.get_dict())
        except ValueError:
            print("Unable to show checkpoint for calculation '{}'".format(pk))


@click.command('watch', context_settings=CONTEXT_SETTINGS)
def do_watch():
    from aiida.backends.utils import load_dbenv, is_dbenv_loaded
    if not is_dbenv_loaded():
        load_dbenv()

    from aiida.work.rmq import create_process_event_listener
    event_listener = create_process_event_listener()
    event_listener.add_event_callback(_print_event_msg)
    print("Listening for events [Ctrl-C to exit]")
    try:
        event_listener.start()
    except KeyboardInterrupt:
        pass


def _print_event_msg(evt, msg):
    import plum.rmq.event as plum_event
    pid, proc_evt = plum_event.split_event(evt)
    proc_info = msg[plum_event.PROC_INFO_KEY]
    proc_type = proc_info['type']
    info = ["[{}] {} {}".format(pid, proc_type, proc_evt)]

    try:
        info.append(str(msg[plum_event.DETAILS_KEY]))
    except KeyError:
        pass

    print(" ".join(info))


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
