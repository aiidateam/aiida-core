# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from collections import namedtuple

from enum import Enum

from aiida.work.default_loop import enqueue, ResultAndPid, get_loop
from plum.wait_ons import run_until as plum_run_until
from . import globals
from . import loop
from . import persistence
from . import process
from . import utils

__all__ = ['run', 'run_get_pid', 'async', 'submit']


class RunningType(Enum):
    """
    A type to indicate what type of object is running: a process,
    a calculation or a workflow
    """
    PROCESS = 0
    LEGACY_CALC = 1
    LEGACY_WORKFLOW = 2


RunningInfo = namedtuple("RunningInfo", ["type", "pid"])


def legacy_workflow(pk):
    """
    Create a :class:`.RunningInfo` object for a legacy workflow.

    This can be used in conjunction with :class:`aiida.work.workchain.ToContext`
    as follows:

    >>> from aiida.work.workchain import WorkChain, ToContext, Outputs
    >>>
    >>> class MyWf(WorkChain):
    >>>     @classmethod
    >>>     def define(cls, spec):
    >>>         super(MyWf, cls).define(spec)
    >>>         spec.outline(cls.step1, cls.step2)
    >>>
    >>>     def step1(self):
    >>>         wf = OldEquationOfState()
    >>>         wf.play()
    >>>         return ToContext(eos=legacy_workflow(wf.pk))
    >>>
    >>>     def step2(self):
    >>>         # Now self.ctx.eos contains the terminated workflow
    >>>         pass

    :param pk: The workflow pk
    :type pk: int
    :return: The running info
    :rtype: :class:`.RunningInfo`
    """
    return RunningInfo(RunningType.LEGACY_WORKFLOW, pk)


def legacy_calc(pk):
    """
    Create a :class:`.RunningInfo` object for a legacy calculation

    :param pk: The calculation pk
    :type pk: int
    :return: The running info
    :rtype: :class:`.RunningInfo`
    """
    return RunningInfo(RunningType.LEGACY_CALC, pk)


def async(process_class, *args, **inputs):
    """
    Run a workfunction or workchain asynchronously.  The inputs get passed
    on to the workchain/workchain.

    :param process_class: The workchain or workfunction to run asynchronously
    :param args:
    :param kwargs: The keyword argument pairs
    :return: A future that represents the execution of the task.
    :rtype: :class:`plum.thread_executor.Future`
    """
    return enqueue(process_class, *args, **inputs)


def run_until(process, state):
    plum_run_until(process, state, globals.get_loop())


def restart(pid, storage=None):
    if storage is None:
        storage = persistence.get_global_persistence()
    cp = storage.load_checkpoint(pid)
    return process.Process.create_from(cp).play()


def submit(process_class, _jobs_store=None, **kwargs):
    assert not utils.is_workfunction(process_class), \
        "You cannot submit a workfunction to the daemon"

    if _jobs_store is None:
        _jobs_store = aiida.work.persistence.get_global_persistence()

    pid = queue_up(process_class, kwargs, _jobs_store)
    return RunningInfo(RunningType.PROCESS, pid)


def queue_up(process_class, inputs, storage):
    """
    This queues up the Process so that it's executed by the daemon when it gets
    around to it.

    :param process_class: The process class to queue up.
    :param inputs: The inputs to the process.
    :type inputs: Mapping
    :param storage: The storage engine which will be used to save the process (of type plum.persistence)
    :return: The pid of the queued process.
    """

    # The strategy for queueing up is this:
    # 1) Create the process which will set up all the provenance info, pid, etc
    proc = enqueue(process_class, **inputs)
    # 2) Save the instance state of the Process
    storage.save(proc)
    return proc.pid


def _get_process_instance(process_class, *args, **kwargs):
    """
    Get a Process instance for a workchain or workfunction

    :param process_class: The workchain or workfunction to instantiate
    :param args: The positional arguments (only for workfunctions)
    :param kwargs: The keyword argument pairs
    :return: The process instance
    :rtype: :class:`aiida.process.Process`
    """

    if isinstance(process_class, process.Process):
        # Nothing to do
        return process_class
    elif utils.is_workfunction(process_class):
        wf_class = process.FunctionProcess.build(process_class._original, **kwargs)
        inputs = wf_class.create_inputs(*args, **kwargs)
        return wf_class(inputs=inputs)
    elif issubclass(process_class, process.Process):
        # No need to consider args as a Process can't deal with positional
        # arguments anyway
        return process_class(inputs=kwargs)
    else:
        raise TypeError("Unknown type for process_class '{}'".format(process_class))


def run(process_class_or_workfunction, *args, **inputs):
    """
    Run a workfunction or process and return the result.

    :param process_class_or_workfunction: The process class or workfunction
    :param args: Positional arguments for a workfunction
    :param inputs: The list of keyword inputs
    :return: The result of the process
    """
    # Create a new loop and run
    proc = _get_process_instance(process_class_or_workfunction, *args, **inputs)

    # Create a new loop and run
    with loop.loop_factory() as evt_loop:
        evt_loop.insert(proc)
        result = evt_loop.run_until_complete(proc)

    return result


def run_get_pid(process_class, *args, **inputs):
    proc = enqueue(process_class, *args, **inputs)
    return ResultAndPid(get_loop().run_until_complete(proc), proc.pid)
