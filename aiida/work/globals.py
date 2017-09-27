# -*- coding: utf-8 -*-

import plum.class_loader
from aiida.work.class_loader import ClassLoader

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__version__ = "0.7.0"
__authors__ = "The AiiDA team."



# Have globals that can be used by all of AiiDA
class_loader = plum.class_loader.ClassLoader(ClassLoader())
_loop = None
_thread_executor = None
_rmq_control_panel = None
_persistence = None


def get_persistence():
    """
    Get the global persistence object

    :return: The persistence object
    :rtype: :class:`aiida.work.persistence.Persistence`
    """
    from aiida.work.persistence import get_global_persistence
    return get_global_persistence()


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
