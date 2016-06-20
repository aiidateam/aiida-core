# -*- coding: utf-8 -*-
import sys

from aiida.cmdline.baseclass import VerdiCommandWithSubcommands
import click
import sys
from tabulate import tabulate

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0"
__authors__ = "The AiiDA team."


class Workflow2(VerdiCommandWithSubcommands):
    """
    Manage the AiiDA worflow2 manager
    """
    def __init__(self):
        self.valid_subcommands = {
            'list': (self.list, self.complete_none),
        }

    def list(self, *args):
        ctx = do_list.make_context('list', sys.argv[3:])
        with ctx:
            result = do_list.invoke(ctx)


@click.command('list')
@click.option('-p', '--past-days', type=int,
              help="add a filter to show only workflows created in the past N"
                   " days")
def do_list(past_days):
    """
    Return a list of running workflows on screen
    """
    from aiida.backends.utils import load_dbenv, is_dbenv_loaded
    from aiida.workflows2.defaults import storage

    if not is_dbenv_loaded():
        pass
    load_dbenv()

    cps = storage.load_all_checkpoints()
    table = []
    for cp in cps:
        table.append([cp.pid, cp.process_class.__name__, cp.wait_on_instance_state])

    print(tabulate(table, headers=["PID", "Process class", "Wait on"]))
