###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module with all the internals that make up the engine of `aiida-core`."""

# AUTO-GENERATED

# fmt: off

from aiida.engine.daemon import *
from aiida.engine.exceptions import *
from aiida.engine.launch import *
from aiida.engine.persistence import *
from aiida.engine.processes import *
from aiida.engine.runners import *
from aiida.engine.utils import *

__all__ = (
    'PORT_NAMESPACE_SEPARATOR',
    'AiidaCheckpointPersister',
    'Awaitable',
    'AwaitableAction',
    'AwaitableTarget',
    'BaseRestartWorkChain',
    'Branch',
    'CalcJob',
    'CalcJobImporter',
    'CalcJobOutputPort',
    'CalcJobProcessSpec',
    'DaemonClient',
    'Each',
    'ExecutionGraphHandle',
    'ExitCode',
    'ExitCodesNamespace',
    'Fanout',
    'FunctionProcess',
    'GraphBuilder',
    'GraphHandle',
    'GraphInput',
    'GraphProcess',
    'InputPort',
    'InterruptableFuture',
    'JobManager',
    'JobsList',
    'Launchable',
    'Loop',
    'Many',
    'MappedOutput',
    'MappedOutputs',
    'Met',
    'MonitorProcess',
    'ObjectLoader',
    'Orchestrated',
    'OutputNames',
    'OutputPort',
    'PastException',
    'PortNamespace',
    'Process',
    'ProcessBuilder',
    'ProcessBuilderNamespace',
    'ProcessFuture',
    'ProcessHandle',
    'ProcessHandlerReport',
    'ProcessSpec',
    'ProcessState',
    'Region',
    'Runner',
    'SourceGraphHandle',
    'Stop',
    'Subgraph',
    'TaskHandle',
    'TaskHandler',
    'TaskNodes',
    'TaskOutput',
    'TaskOutputs',
    'TaskProcess',
    'TaskWorkChain',
    'ToContext',
    'WaitProcess',
    'Whole',
    'WithNonDb',
    'WithSerialize',
    'WorkChain',
    'append_',
    'assign_',
    'await_processes',
    'branch',
    'calcfunction',
    'construct_awaitable',
    'each',
    'get_daemon_client',
    'get_object_loader',
    'graph',
    'graph_execution',
    'graph_source',
    'handler',
    'if_',
    'interruptable_task',
    'is_process_function',
    'launched_as',
    'loop',
    'monitor',
    'process_handler',
    'rerun_from',
    'return_',
    'run',
    'run_get_node',
    'run_get_pk',
    'select',
    'subgraph',
    'submit',
    'task',
    'task_execution',
    'task_node',
    'task_source',
    'tasks',
    'wait_for',
    'while_',
    'workfunction',
)

# fmt: on

import typing as t
from collections.abc import Callable

from aiida.engine.processes.graphs.build_source import graph as graph_source
from aiida.engine.processes.graphs.build_source import task as task_source


def graph(function: Callable[..., t.Any] | None = None, *, identifier: str | None = None) -> t.Any:
    """Declare a function as a source graph of tasks.

    Thin wrapper around :func:`graph_source`, so ``from aiida.engine import graph`` defaults to the
    source flavour without executing the graph body.
    """
    return graph_source(function, identifier=identifier)


def task(function: Callable[..., t.Any]) -> t.Any:
    """Register a Python function as a source task.

    Thin wrapper around :func:`task_source`.
    """
    return task_source(function)
