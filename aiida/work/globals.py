# -*- coding: utf-8 -*-

from aiida.work.class_loader import ClassLoader
from aiida.work.process_registry import ProcessRegistry

import plum.class_loader
from plum.event import EmitterAggregator

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."


def _build_registry():
    return ProcessRegistry()


# Have globals that can be used by all of AiiDA
class_loader = plum.class_loader.ClassLoader(ClassLoader())
_thread_executor = None
_event_emitter = None
REGISTRY = _build_registry()
_rmq_control_panel = None
_persistence = None


def get_thread_executor():
    global _thread_executor
    if _thread_executor is None:
        from plum.thread_executor import SchedulingExecutor
        _thread_executor = SchedulingExecutor(max_threads=20)

    return _thread_executor


def get_heartbeat_pool():
    import threading
    global _heartbeat_pool



def get_event_emitter():
    global _event_emitter
    if _event_emitter is None:
        from aiida.work.event import DbPollingEmitter, ProcessMonitorEmitter, \
            SchedulerEmitter
        from aiida.work.legacy.event import WorkflowEmitter

        aggregator = EmitterAggregator()
        aggregator.add_child(ProcessMonitorEmitter())
        aggregator.add_child(DbPollingEmitter())
        aggregator.add_child(SchedulerEmitter())
        aggregator.add_child(WorkflowEmitter())
        _event_emitter = aggregator

    return _event_emitter


def get_persistence():
    """
    Get the global persistence object

    :return: The persistence object
    :rtype: :class:`aiida.work.persistence.Persistence`
    """
    from aiida.work.persistence import get_global_persistence
    return get_global_persistence()


def enable_persistence():
    get_persistence().enable_persist_all()


def disable_persistence():
    get_persistence().disable_persist_all()


def enable_rmq_subscribers():
    """
    Enable RMQ subscribers for the global process manager.  This means that RMQ
    launch, status and control messages will be listened for and processed.

    Use this to enable RMQ support for AiiDA.
    """
    import aiida.work.rmq as rmq
    rmq.enable_subscribers(get_thread_executor(), "aiida")


def enable_rmq_event_publisher():
    import aiida.work.rmq as rmq
    rmq.enable_process_event_publisher()


def enable_rmq_all():
    enable_rmq_subscribers()
    enable_rmq_event_publisher()


def get_rmq_control_panel():
    global _rmq_control_panel
    if _rmq_control_panel is None:
        from aiida.work.rmq import ProcessControlPanel
        cp = ProcessControlPanel("aiida")
        _rmq_control_panel = cp

    return _rmq_control_panel
