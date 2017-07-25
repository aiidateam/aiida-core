# -*- coding: utf-8 -*-

import plum.class_loader
from aiida.work.class_loader import ClassLoader
from aiida.work.process_registry import ProcessRegistry

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."


def _build_registry():
    return ProcessRegistry()


# Have globals that can be used by all of AiiDA
class_loader = plum.class_loader.ClassLoader(ClassLoader())
_loop = None
_thread_executor = None
REGISTRY = _build_registry()
_rmq_control_panel = None
_persistence = None
_heartbeat_pool = None
_max_parallel_processes = None


def _get_max_parallel_processes():
    global _max_parallel_processes
    if _max_parallel_processes is None:
        from aiida.backends import settings
        from aiida.common.setup import get_profile_config
        from aiida.daemon.settings import DAEMON_MAX_PARALLEL_PROCESSES

        config = get_profile_config(settings.AIIDADB_PROFILE)
        _max_parallel_processes = config.get("DAEMON_MAX_PARALLEL_PROCESSES",
                                             DAEMON_MAX_PARALLEL_PROCESSES)

    return _max_parallel_processes


def get_thread_executor():
    global _thread_executor
    if _thread_executor is None:
        from plum.thread_executor import SchedulingExecutor
        _thread_executor = SchedulingExecutor(max_threads=_get_max_parallel_processes())

    return _thread_executor


def get_heartbeat_pool():
    global _heartbeat_pool
    if _heartbeat_pool is None:
        from concurrent.futures import ThreadPoolExecutor
        _heartbeat_pool = ThreadPoolExecutor(max_workers=_get_max_parallel_processes())

    return _heartbeat_pool


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
