# -*- coding: utf-8 -*-

from aiida.backends.utils import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()

import aiida.workflows2.defaults as defaults
from plum.process import ProcessState
from plum.engine.ticking import TickingEngine
from aiida.workflows2.process import Process

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.5.0"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi, Martin Uhrin"


def run_all_saved_processes(engine, storage):
    futures = []
    for cp in storage.load_all_checkpoints():
        proc = Process.create_from(cp)
        storage.persist_process(proc)
        futures.append(engine.run(proc))
    return futures


# def tick_workflow_engine(storage=None):
#     if storage is None:
#         storage = defaults.storage
#
#     engine = TickingEngine()
#     run_all_saved_processes(engine, storage)
#     more_work = engine.tick()
#     engine.shutdown()
#     return more_work


def tick_workflow_engine(storage=None):
    if storage is None:
        storage = defaults.storage

    more_work = False
    procs = [Process.create_from(cp) for cp in storage.load_all_checkpoints()]
    for proc in procs:
        storage.persist_process(proc)
        proc.tick()

        # If the process is WAITING then it transitioned from
        # CREATED -> WAITING and we should tick again to see if the
        # thing it is waiting on is ready
        if proc.state is ProcessState.WAITING:
            proc.tick()

        # Now stop the process and let it finish running through the states
        # until it is destroyed
        proc.stop()
        proc.run_until_complete()
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
