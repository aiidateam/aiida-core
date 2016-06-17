# -*- coding: utf-8 -*-
import sys

from aiida.cmdline.baseclass import VerdiCommandWithSubcommands
from aiida.workflows2.defaults import registry
import click
import sys

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
        sys.argv = sys.argv[2:]
        return do_list()


@click.command()
@click.option('--verbose')
def do_list(verbose):
    """
    Return a list of workflows on screen
    """
    from aiida.backends.utils import load_dbenv, is_dbenv_loaded

    if not is_dbenv_loaded():
        load_dbenv()

    print("\n".join(registry.get_running_pids()))
