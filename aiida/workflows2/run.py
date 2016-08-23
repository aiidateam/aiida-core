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
        return_pid = kwargs.pop('_result_pid', False)
        fut = execution_engine.submit(process_class, inputs=kwargs)
        if return_pid:
            return fut, fut.pid
        else:
            return fut


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
        return_pid = inputs.pop('_return_pid', False)
        fut = execution_engine.submit(process_class, inputs)
        result = fut.result()
        if return_pid:
            return result, fut.pid
        else:
            return result
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

    # The straregy for queueing up is this:
    # 1) Create the process which will set up all the provenance info, pid, etc
    proc = process_class.new_instance(inputs)
    pid = proc.pid
    # 2) Save the instance state of the Process
    storage.save(proc)
    # 3) Ask it to stop itself
    proc.stop()
    proc.run_until_complete()
    del proc
    return pid
