###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module to define commonly used data structures.

Submodules are prefixed with an underscore to signal that they are implementation details; import public names
directly from this package instead.
"""

from aiida.common.datastructures._calcjob import (
    CalcInfo,
    CalcJobState,
    CodeInfo,
    CodeRunMode,
    FileCopyOperation,
    StashMode,
    UnstashTargetMode,
)
from aiida.common.datastructures._orbital import Orbital, RealhydrogenOrbital
from aiida.common.datastructures._scheduler import (
    JobInfo,
    JobResource,
    JobState,
    JobTemplate,
    JobTemplateCodeInfo,
    MachineInfo,
    NodeNumberJobResource,
    ParEnvJobResource,
)

__all__ = (
    'CalcInfo',
    'CalcJobState',
    'CodeInfo',
    'CodeRunMode',
    'FileCopyOperation',
    'JobInfo',
    'JobResource',
    'JobState',
    'JobTemplate',
    'JobTemplateCodeInfo',
    'MachineInfo',
    'NodeNumberJobResource',
    'Orbital',
    'ParEnvJobResource',
    'RealhydrogenOrbital',
    'StashMode',
    'UnstashTargetMode',
)
