# -*- coding: utf-8 -*-

from aiida.backends.utils import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()

import traceback
import aiida.workflows2.defaults as defaults
from plum.process import ProcessState
from aiida.workflows2.process import Process

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."


def tick_workflow_engine(storage=None, print_exceptions=True):
    if storage is None:
        storage = defaults.storage

    more_work = False

    for proc in _load_all_processes(storage):
        storage.persist_process(proc)
        is_waiting = proc.get_waiting_on()
        try:
            # Get the Process till the point it is about to do some work
            if is_waiting is not None:
                proc.run_until(ProcessState.WAITING)
            else:
                proc.run_until(ProcessState.STARTED)

            proc.tick()

            # Now stop the process and let it finish running through the states
            # until it is destroyed
            proc.stop()
            proc.run_until(ProcessState.DESTROYED)
        except BaseException:
            if print_exceptions:
                traceback.print_exc()
            continue

        # Check if the process finished or was stopped early
        if not proc.has_finished():
            more_work = True

    return more_work


def _load_all_processes(storage):
    procs = []
    for cp in storage.load_all_checkpoints():
        try:
            procs.append(Process.create_from(cp))
        except KeyboardInterrupt:
            raise
        except BaseException:
            # TODO: Log exception
            pass
    return procs


if __name__ == "__main__":
    """
    A convenience method so that this module can be ran ticking the engine once.
    """
    from aiida.backends.utils import load_dbenv, is_dbenv_loaded

    if not is_dbenv_loaded():
        load_dbenv()

    tick_workflow_engine()
