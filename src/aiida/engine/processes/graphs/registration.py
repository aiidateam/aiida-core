###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Explicit process-to-task adapters, independent of graph authoring flavours."""

from aiida.engine.processes.builder import ProcessBuilder
from aiida.engine.processes.calcjobs.calcjob import CalcJob
from aiida.engine.processes.graphs.bindings import copy_containers
from aiida.engine.processes.graphs.build_execution import ProcessHandle, task
from aiida.engine.processes.process import Process
from aiida.engine.processes.workchains.workchain import WorkChain

__all__ = ('task_from_builder', 'task_from_calcjob', 'task_from_workchain')


def task_from_builder(builder: ProcessBuilder) -> ProcessHandle:
    """Adapt a populated builder without executing preparation or copying ORM nodes.

    Missing inputs may be supplied at placement. Containers are captured immediately;
    changing an input does not rerun protocol preparation.

    :param builder: an upstream process builder, prepared using concrete arguments.
    :return: a task handle with independently captured launch inputs.
    :raises TypeError: if the argument is not a process builder.
    """
    candidate: object = builder
    if not isinstance(candidate, ProcessBuilder):
        msg = f'Expected a ProcessBuilder, got {candidate!r}.'
        raise TypeError(msg)
    handle = task(builder.process_class)
    return ProcessHandle(handle.process_class, handle.task_spec, copy_containers(builder.get_launch_inputs()))


def task_from_calcjob(process_class: type[CalcJob]) -> ProcessHandle:
    """Create a graph task using a CalcJob's existing process spec.

    :param process_class: the CalcJob subclass to launch when the task runs.
    :return: a handle usable in execution and source graphs.
    :raises TypeError: if the argument is not a CalcJob subclass.
    """
    _validate_class(process_class, CalcJob)
    return task(process_class)


def task_from_workchain(process_class: type[WorkChain]) -> ProcessHandle:
    """Create a graph task using a WorkChain's existing process spec.

    :param process_class: the WorkChain subclass to launch when the task runs.
    :return: a handle usable in execution and source graphs.
    :raises TypeError: if the argument is not a WorkChain subclass.
    """
    _validate_class(process_class, WorkChain)
    return task(process_class)


def _validate_class(candidate: object, expected: type[Process]) -> None:
    if not isinstance(candidate, type) or not issubclass(candidate, expected):
        msg = f'Expected a {expected.__name__} subclass, got {candidate!r}.'
        raise TypeError(msg)
