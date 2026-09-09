###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Process scheduling service.

The :class:`~aiida.scheduler.scheduler.Scheduler` gates process submission:
submitters send process tasks to the scheduler queue instead of the worker
queue, and the scheduler admits them (today: forward; tomorrow: dependencies,
throttling, pool routing) before dispatching to workers.

This is the production landing of the ``broker-scheduler-split`` spike, which
contains the full design discussion.
"""

from aiida.scheduler.event_listener import SchedulerEventListener
from aiida.scheduler.scheduler import (
    COMPLETED_SUBJECT,
    FAILED_SUBJECT,
    KIND_WORKGRAPH,
    SCHEDULER_COMPLETIONS,
    SCHEDULER_QUEUE,
    Scheduler,
)

__all__ = (
    'COMPLETED_SUBJECT',
    'FAILED_SUBJECT',
    'KIND_WORKGRAPH',
    'SCHEDULER_COMPLETIONS',
    'SCHEDULER_QUEUE',
    'Scheduler',
    'SchedulerEventListener',
)
