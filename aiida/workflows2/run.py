# -*- coding: utf-8 -*-

from aiida.workflows2 import util as util
from aiida.workflows2.defaults import execution_engine
from aiida.workflows2.process import Process
import aiida.workflows2.defaults as defaults

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.1.1"
__authors__ = "The AiiDA team."


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
    proc = defaults.factory.create_process(process_class, inputs=kwargs)
    _jobs_store.save(proc)
    pid = proc.pid
    proc.signal_on_destroy()

    return pid


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
