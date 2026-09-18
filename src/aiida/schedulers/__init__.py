###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for classes and utilities to interact with cluster schedulers."""

# AUTO-GENERATED

# fmt: off

from aiida.common.datastructures import (
    JobInfo,
    JobResource,
    JobState,
    JobTemplate,
    MachineInfo,
    NodeNumberJobResource,
    ParEnvJobResource,
)  # re-export for backwards compatibility: these moved to `aiida.common.datastructures` in v2.10
from aiida.schedulers.plugins import *
from aiida.schedulers.scheduler import *

__all__ = (
    'BashCliScheduler',
    'JobInfo',
    'JobResource',
    'JobState',
    'JobTemplate',
    'MachineInfo',
    'NodeNumberJobResource',
    'ParEnvJobResource',
    'Scheduler',
    'SchedulerError',
    'SchedulerParsingError',
)

# fmt: on
