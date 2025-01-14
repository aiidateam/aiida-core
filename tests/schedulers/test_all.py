###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests run for all plugins in :mod:`aiida.schedulers.plugins`."""

from __future__ import annotations

import pytest

from aiida.common.datastructures import CodeRunMode
from aiida.plugins import SchedulerFactory, entry_point
from aiida.schedulers import Scheduler
from aiida.schedulers.datastructures import JobTemplate, JobTemplateCodeInfo, NodeNumberJobResource


def get_scheduler_entry_point_names() -> list[str]:
    """Return the list of entry point names for the scheduler plugins registered by ``aiida-core``.

    :return: List of entry point names.
    """
    entry_points_names = entry_point.get_entry_point_names('aiida.schedulers')
    return [name for name in entry_points_names if name.startswith('core.')]


def get_scheduler_job_resource(scheduler):
    """Create a ``JobResource`` instance for the given scheduler with default resources."""
    if issubclass(scheduler.job_resource_class, NodeNumberJobResource):
        resources = {'num_machines': 1, 'num_mpiprocs_per_machine': 1}
    else:
        resources = {'parallel_env': 'env', 'tot_num_mpiprocs': 1}

    return scheduler.create_job_resource(**resources)


@pytest.fixture(scope='function', params=get_scheduler_entry_point_names())
def scheduler(request) -> Scheduler:
    """Fixture that parametrizes over all the ``Scheduler`` implementations registered by ``aiida-core``."""
    return SchedulerFactory(request.param)()


@pytest.mark.parametrize('environment_variables_double_quotes', (True, False))
def test_job_environment(scheduler, environment_variables_double_quotes):
    """Test that ``JobTemplate.job_environment`` make it into the submission script.

    Also tests that the ``JobTemplate.environment_variables_double_quotes`` is respected.
    """
    job_template = JobTemplate()
    job_template.codes_info = [JobTemplateCodeInfo()]
    job_template.codes_run_mode = CodeRunMode.SERIAL
    job_template.job_resource = get_scheduler_job_resource(scheduler)
    job_template.environment_variables_double_quotes = environment_variables_double_quotes
    job_template.job_environment = {'SOME_STRING': 'value', 'SOME_INTEGER': 1}
    script = scheduler.get_submit_script(job_template)

    if environment_variables_double_quotes:
        assert 'export SOME_STRING="value"' in script
        assert 'export SOME_INTEGER="1"' in script
    else:
        assert "export SOME_STRING='value'" in script
        assert "export SOME_INTEGER='1'" in script
