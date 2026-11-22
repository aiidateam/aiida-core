###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the ``DirectScheduler`` plugin."""

import logging
import sys

import pytest

from aiida.common.datastructures import CodeRunMode, JobTemplate, JobTemplateCodeInfo
from aiida.schedulers import SchedulerError
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


def test_submit_script_sched_join_files(scheduler, template, caplog):
    """Test stdout/stderr redirection for `sched_join_files` and `sched_error_path`."""
    template.sched_output_path = 'stdout.txt'

    # Case 1: sched_join_files=True -> joins stderr into stdout with 'exec 2>&1'
    template.sched_join_files = True
    script = scheduler.get_submit_script(template)
    assert 'exec > stdout.txt' in script
    assert 'exec 2>&1' in script

    # Case 2: sched_join_files=True with sched_error_path set -> ignores error path and logs info
    template.sched_error_path = 'stderr.txt'
    with caplog.at_level(logging.INFO, logger=scheduler.logger.name):
        script = scheduler.get_submit_script(template)
    assert 'exec 2>&1' in script
    assert 'exec 2> stderr.txt' not in script
    assert 'sched_join_files is True, but sched_error_path is set' in caplog.text

    # Case 3: sched_join_files=False with sched_error_path set -> redirects stderr to file
    template.sched_join_files = False
    script = scheduler.get_submit_script(template)
    assert 'exec 2> stderr.txt' in script
    assert 'exec 2>&1' not in script

    # Case 4: sched_join_files=False with no error path -> does not join files
    template.pop('sched_error_path')
    script = scheduler.get_submit_script(template)
    assert 'exec 2>&1' not in script
    assert 'exec 2>' not in script


# TODO(danielhollas): It's not clear if the fork method can lead to actual deadlock in this case
_FORK_WARNING = 'This process .* is multi-threaded, use of fork\\(\\) may lead to deadlocks in the child'


@pytest.mark.skipif(
    sys.platform == 'darwin',
    reason='Uses multiprocessing fork() which crashes xdist workers on macOS due to corrupted '
    'multi-threaded state in the forked child',
)
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
