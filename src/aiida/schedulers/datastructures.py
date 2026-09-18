# re-export for backwards compatibility: these moved to `aiida.common.datastructures` in v2.10
from aiida.common.datastructures import (
    JobInfo,
    JobResource,
    JobState,
    JobTemplate,
    MachineInfo,
    NodeNumberJobResource,
    ParEnvJobResource,
)

__all__ = (
    'JobInfo',
    'JobResource',
    'JobState',
    'JobTemplate',
    'MachineInfo',
    'NodeNumberJobResource',
    'ParEnvJobResource',
)
