# -*- coding: utf-8 -*-

from aiida.backends.utils import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()

import aiida.workflows2.defaults as defaults
from plum.process import ProcessState
from plum.engine.ticking import TickingEngine
from aiida.workflows2.process import Process

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."


def tick_workflow_engine(storage=None):
    if storage is None:
        storage = defaults.storage

    more_work = False
    procs = [Process.create_from(cp) for cp in storage.load_all_checkpoints()]
    for proc in procs:
        storage.persist_process(proc)

        # Get the Process running but break if ta wait on isn't ready
        proc.run_until(ProcessState.RUNNING, break_on_wait_not_ready=True)

        # Now stop the process and let it finish running through the states
        # until it is destroyed
        proc.stop()
        proc.run_until(ProcessState.DESTROYED)

        # Check if the process finished or was stopped early
        if not proc.has_finished():
            more_work = True

    return more_work


if __name__ == "__main__":
    """
    A convenience method so that this module can be ran ticking the engine once.
    """
    from aiida.backends.utils import load_dbenv, is_dbenv_loaded

    if not is_dbenv_loaded():
        load_dbenv()

    tick_workflow_engine()
