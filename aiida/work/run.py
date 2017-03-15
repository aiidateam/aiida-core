# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from enum import Enum
from collections import namedtuple
from aiida.work import util as util
from aiida.work.defaults import parallel_engine, serial_engine
from aiida.work.process import Process
import aiida.work.persistence



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
    >>>         wf.start()
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


def async(process_class, *args, **kwargs):
    if util.is_workfunction(process_class):
        kwargs['__async'] = True
        return process_class(*args, **kwargs)
    elif issubclass(process_class, Process):
        return parallel_engine.submit(process_class, inputs=kwargs)


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
    proc = process_class.new_instance(inputs)
    pid = proc.pid
    # 2) Save the instance state of the Process
    storage.save(proc)
    # 3) Ask it to stop itself
    proc.stop()
    proc.run_until_complete()
    del proc
    return pid
