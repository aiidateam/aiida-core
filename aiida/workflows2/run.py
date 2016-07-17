# -*- coding: utf-8 -*-

from aiida.workflows2 import util as util
from aiida.workflows2.defaults import execution_engine
from aiida.workflows2.process import Process
import aiida.workflows2.defaults as defaults
import plum.wait_ons

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.5.0"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi, Martin Uhrin"


def async(process_class, *args, **kwargs):
    if util.is_workfunction(process_class):
        kwargs['__async'] = True
        return process_class(*args, **kwargs)
    elif issubclass(process_class, Process):
        # No need to consider args as a Process can't deal with positional
        # arguments anyway
        return execution_engine.submit(process_class, inputs=kwargs)


def asyncd(process_class, _jobs_store=None, **kwargs):
    assert not util.is_workfunction(process_class),\
        "You cannot submit a workfunction to the daemon"

    if _jobs_store is None:
        _jobs_store = defaults.storage

    return queue_up(process_class, kwargs, _jobs_store)


def run(process_class, *args, **inputs):
    """
    Synchronously (i.e. blocking) run a workfunction or Process.

    :param process_class: The process class or workfunction
    :param _attributes: Optional attributes (only for Processes)
    :param args: Positional arguments for a workfunction
    :param inputs: The list of inputs
    """
    if util.is_workfunction(process_class):
        return process_class(*args, **inputs)
    elif issubclass(process_class, Process):
        return execution_engine.submit(process_class, inputs).result()
    else:
        raise ValueError("Unsupported type supplied for process_class.")


def restart(pid):
    cp = defaults.storage.load_checkpoint(pid)
    return defaults.execution_engine.run_from_and_block(cp)


def queue_up(process_class, inputs, storage):
    """
    This queues up the Process so that it's executed by the daemon when it gets
    around to it.

    :param process_class: The process class to queue up.
    :param inputs: The inputs to the process.
    :return: The pid of the queued process.
    """

    proc = defaults.factory.create_process(process_class, inputs)
    pid = proc.pid
    proc.perform_run(None, defaults.registry)
    cp = plum.wait_ons.Checkpoint('run_after_queueing')
    proc.perform_wait(cp)
    storage.save(proc, cp)
    proc.perform_stop()
    proc.perform_destroy()
    del proc
    return pid
