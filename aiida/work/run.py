# -*- coding: utf-8 -*-

from aiida.work import util as util
from aiida.work.defaults import parallel_engine, serial_engine
from aiida.work.process import Process
import aiida.work.persistence

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."


def async(process_class, *args, **kwargs):
    if util.is_workfunction(process_class):
        kwargs['__async'] = True
        return process_class(*args, **kwargs)
    elif issubclass(process_class, Process):
        # No need to consider args as a Process can't deal with positional
        # arguments anyway
        return_pid = kwargs.pop('_result_pid', False)
        fut = parallel_engine.submit(process_class, inputs=kwargs)
        if return_pid:
            return fut, fut.pid
        else:
            return fut


def run(process_class, *args, **inputs):
    """
    Synchronously (i.e. blocking) run a workfunction or process.

    :param process_class: The process class or workfunction
    :param _attributes: Optional attributes (only for process)
    :param args: Positional arguments for a workfunction
    :param inputs: The list of inputs
    """
    if util.is_workfunction(process_class):
        return process_class(*args, **inputs)
    elif issubclass(process_class, Process):
        return_pid = inputs.pop('_return_pid', False)
        fut = serial_engine.submit(process_class, inputs)
        result = fut.result()
        if return_pid:
            return result, fut.pid
        else:
            return result
    else:
        raise ValueError("Unsupported type supplied for process_class.")


def restart(pid):
    cp = aiida.work.persistence.get_default().load_checkpoint(pid)
    return serial_engine.run_from_and_block(cp)


def submit(process_class, _jobs_store=None, **kwargs):
    assert not util.is_workfunction(process_class),\
        "You cannot submit a workfunction to the daemon"

    if _jobs_store is None:
        _jobs_store = aiida.work.persistence.get_default()

    return queue_up(process_class, kwargs, _jobs_store)


def queue_up(process_class, inputs, storage):
    """
    This queues up the Process so that it's executed by the daemon when it gets
    around to it.

    :param process_class: The process class to queue up.
    :param inputs: The inputs to the process.
    :type inputs: Mapping
    :param storage: The storage engine which will be used to save the process
    :type storage: plum.persistence.
    :return: The pid of the queued process.
    """

    # The strategy for queueing up is this:
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
