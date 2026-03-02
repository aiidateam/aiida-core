###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the ``DirectScheduler`` plugin."""

import pytest

from aiida.common.datastructures import CodeRunMode
from aiida.schedulers import SchedulerError
from aiida.schedulers.datastructures import JobTemplate, JobTemplateCodeInfo
from aiida.schedulers.plugins.direct import DirectScheduler


@pytest.fixture
def scheduler():
    """Return an instance of the ``DirectScheduler``."""
    return DirectScheduler()


@pytest.fixture
def template():
    """Return an instance of the ``JobTemplate`` with some required presets."""
    tmpl_code_info = JobTemplateCodeInfo()
    tmpl_code_info.cmdline_params = []

    template = JobTemplate()
    template.codes_info = [tmpl_code_info]
    template.codes_run_mode = CodeRunMode.SERIAL

    return template


@pytest.mark.parametrize(
    'stdout',
    (
        """21259 S+   broeder   0:00.04\n87619 S+   broeder   0:00.44\n87634 S+   broeder   0:00.01""",  # MacOS
        """11354 Ss   aiida    00:00:00\n\n87619 R+   aiida    00:00:00\n11384 S+   aiida    00:00:00""",  # Linux
    ),
)
def test_parse_joblist_output(scheduler, stdout):
    """Test the ``_parse_joblist_output`` for output taken from MacOS and Linux."""
    result = scheduler._parse_joblist_output(retval=0, stdout=stdout, stderr='')
    assert len(result) == 3
    assert '87619' in [job.job_id for job in result]


def test_parse_joblist_output_incorrect(scheduler):
    """Test the ``_parse_joblist_output`` for invalid output."""
    with pytest.raises(SchedulerError):
        scheduler._parse_joblist_output(retval=0, stdout='aaa', stderr='')


def test_submit_script_rerunnable(scheduler, template, caplog):
    """Test that setting the ``rerunnable`` option gives a warning."""
    template.rerunnable = True
    scheduler.get_submit_script(template)
    assert 'rerunnable' in caplog.text
    assert 'has no effect' in caplog.text


def test_submit_script_with_num_cores_per_mpiproc(scheduler, template):
    """Test that passing ``num_cores_per_mpiproc`` in job resources results in ``OMP_NUM_THREADS`` being set."""
    num_cores_per_mpiproc = 24
    template.job_resource = scheduler.create_job_resource(
        num_machines=1, tot_num_mpiprocs=1, num_cores_per_mpiproc=num_cores_per_mpiproc
    )
    result = scheduler.get_submit_script(template)
    assert f'export OMP_NUM_THREADS={num_cores_per_mpiproc}' in result


# TODO(danielhollas): It's not clear if the fork method can lead to actual deadlock in this case
_FORK_WARNING = 'This process .* is multi-threaded, use of fork\\(\\) may lead to deadlocks in the child'


@pytest.mark.timeout(timeout=10)
@pytest.mark.filterwarnings(f'ignore:{_FORK_WARNING}:DeprecationWarning')
def test_kill_job(scheduler, tmpdir):
    """Test if kill_job kill all descendant children from the process.
    For that we spawn a new process that runs a sleep command, then we
    kill it and check if the sleep process is still alive.

    current process     forked process                 run script.sh
         python─────────────python───────────────────bash──────sleep
                     we kill this process       we check if still running
    """
    import multiprocessing
    import time

    from psutil import Process

    from aiida.transports.plugins.local import LocalTransport

    def run_sleep_100():
        import subprocess

        script = tmpdir / 'sleep.sh'
        script.write('sleep 100')
        # this is blocking for the process entering
        subprocess.run(['bash', script.strpath], check=False)

    # NOTE: If we need to switch away from 'fork',
    # we need to define the `run_sleep_100` function outside of the test.
    ctx = multiprocessing.get_context(method='fork')
    forked_process = ctx.Process(target=run_sleep_100)
    forked_process.start()
    while len(forked_process_children := Process(forked_process.pid).children(recursive=True)) != 2:
        time.sleep(0.1)
    bash_process = forked_process_children[0]
    sleep_process = forked_process_children[1]
    with LocalTransport() as transport:
        scheduler.set_transport(transport)
        scheduler.kill_job(forked_process.pid)
    while bash_process.is_running() or sleep_process.is_running():
        time.sleep(0.1)
    forked_process.join()
