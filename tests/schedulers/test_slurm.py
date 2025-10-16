###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# ruff: noqa: E501
"""Tests for the SLURM scheduler plugin."""

import datetime
import logging
import unittest
import uuid

import pytest

from aiida.engine import CalcJob
from aiida.schedulers import JobState, SchedulerError
from aiida.schedulers.plugins.slurm import SlurmJobResource, SlurmScheduler

# job_id, state_raw, annotation, executing_host, username, number_nodes, number_cpus, allocated_machines, partition, time_limit, time_used, dispatch_time, job_name, submission_time
# See SlurmScheduler.fields
TEXT_SQUEUE_TO_TEST = """862540^^^PD^^^Dependency^^^n/a^^^user1^^^20^^^640^^^(Dependency)^^^normal^^^1-00:00:00^^^0:00^^^N/A^^^longsqw_L24_q_10_0^^^2013-05-22T01:41:11
863100^^^PD^^^Resources^^^n/a^^^user2^^^32^^^1024^^^(Resources)^^^normal^^^10:00^^^0:00^^^2013-05-23T14:44:44^^^eq_solve_e4.slm^^^2013-05-22T04:23:59
863546^^^PD^^^Priority^^^n/a^^^user3^^^2^^^64^^^(Priority)^^^normal^^^8:00:00^^^0:00^^^2013-05-23T14:44:44^^^S2-H2O^^^2013-05-22T08:08:41
863313^^^PD^^^JobHeldUser^^^n/a^^^user4^^^1^^^1^^^(JobHeldUser)^^^normal^^^1:00:00^^^0:00^^^N/A^^^test^^^2013-05-23T00:28:12
862538^^^R^^^None^^^rosa10^^^user5^^^20^^^640^^^nid0[0099,0156-0157,0162-0163,0772-0773,0826,0964-0965,1018-1019,1152-1153,1214-1217,1344-1345]^^^normal^^^1-00:00:00^^^32:10^^^2013-05-23T11:41:30^^^longsqw_L24_q_11_0^^^2013-05-23T03:04:21
861352^^^R^^^None^^^rosa11^^^user6^^^4^^^128^^^nid00[192,246,264-265]^^^normal^^^1-00:00:00^^^23:30:20^^^2013-05-22T12:43:20^^^Pressure_PBEsol_0^^^2013-05-23T09:35:23
863553^^^R^^^None^^^rosa1^^^user5^^^1^^^32^^^nid00471^^^normal^^^30:00^^^29:29^^^2013-05-23T11:44:11^^^bash^^^2013-05-23T10:42:11
863554^^^R^^^None^^^rosa1^^^user5^^^1^^^32^^^nid00471^^^normal^^^NOT_SET^^^29:29^^^2013-05-23T11:44:11^^^bash^^^2013-05-23T10:42:11
"""
JOBS_ON_CLUSTER = 8
JOBS_HELD = 2
JOBS_QUEUED = 2
USERS_RUNNING = ['user5', 'user6']
JOBS_RUNNING = ['862538', '861352', '863553', '863554']


def test_resource_validation():
    """Tests to verify that resources are correctly validated."""
    with pytest.raises(
        ValueError,
        match='At least two among `num_machines`, `num_mpiprocs_per_machine` or `tot_num_mpiprocs` must be specified.',
    ):
        SlurmJobResource()

    output = SlurmJobResource(num_machines=1, num_mpiprocs_per_machine=2)
    assert output == {
        'num_machines': 1,
        'num_mpiprocs_per_machine': 2,
        'num_cores_per_machine': None,
        'num_cores_per_mpiproc': None,
        'tot_num_mpiprocs': 2,
    }

    with pytest.raises(
        ValueError, match='`tot_num_mpiprocs` is not equal to `num_mpiprocs_per_machine \\* num_machines`.'
    ):
        SlurmJobResource(num_cores_per_machine=1, tot_num_mpiprocs=1, num_mpiprocs_per_machine=2)

    with pytest.raises(ValueError, match='num_cores_per_machine must be greater than or equal to one.'):
        SlurmJobResource(num_machines=1, tot_num_mpiprocs=1, num_cores_per_machine=0)

    with pytest.raises(
        ValueError, match='num_cores_per_machine` must be equal to `num_cores_per_mpiproc \\* num_mpiprocs_per_machine`'
    ):
        SlurmJobResource(num_machines=1, tot_num_mpiprocs=4, num_cores_per_machine=3)


class TestParserSqueue(unittest.TestCase):
    """Tests to verify if the function _parse_joblist_output behave correctly
    The tests is done parsing a string defined above, to be used offline
    """

    def test_parse_common_joblist_output(self):
        """Test whether _parse_joblist_output can parse the squeue output"""
        scheduler = SlurmScheduler()

        retval = 0
        stdout = TEXT_SQUEUE_TO_TEST
        stderr = ''

        job_list = scheduler._parse_joblist_output(retval, stdout, stderr)
        job_dict = {j.job_id: j for j in job_list}

        # The parameters are hard coded in the text to parse
        job_parsed = len(job_list)
        assert job_parsed == JOBS_ON_CLUSTER

        job_running_parsed = len([j for j in job_list if j.job_state and j.job_state == JobState.RUNNING])
        assert len(JOBS_RUNNING) == job_running_parsed

        job_held_parsed = len([j for j in job_list if j.job_state and j.job_state == JobState.QUEUED_HELD])
        assert JOBS_HELD == job_held_parsed

        job_queued_parsed = len([j for j in job_list if j.job_state and j.job_state == JobState.QUEUED])
        assert JOBS_QUEUED == job_queued_parsed

        parsed_running_users = [j.job_owner for j in job_list if j.job_state and j.job_state == JobState.RUNNING]
        assert set(USERS_RUNNING) == set(parsed_running_users)

        parsed_running_jobs = [j.job_id for j in job_list if j.job_state and j.job_state == JobState.RUNNING]
        assert set(JOBS_RUNNING) == set(parsed_running_jobs)

        assert job_dict['863553'].requested_wallclock_time_seconds, 30 * 60
        assert job_dict['863553'].wallclock_time_seconds, 29 * 60 + 29
        assert job_dict['863553'].dispatch_time, datetime.datetime(2013, 5, 23, 11, 44, 11)
        assert job_dict['863553'].submission_time, datetime.datetime(2013, 5, 23, 10, 42, 11)

        assert job_dict['863100'].annotation == 'Resources'
        assert job_dict['863100'].num_machines == 32
        assert job_dict['863100'].num_mpiprocs == 1024
        assert job_dict['863100'].queue_name == 'normal'

        assert job_dict['861352'].title == 'Pressure_PBEsol_0'

        assert job_dict['863554'].requested_wallclock_time_seconds is None

        # allocated_machines is not implemented in this version of the plugin
        #        for j in job_list:
        #            if j.allocated_machines:
        #                num_machines = 0
        #                num_mpiprocs = 0
        #                for n in j.allocated_machines:
        #                    num_machines += 1
        #                    num_mpiprocs += n.num_mpiprocs
        #
        #                self.assertTrue( j.num_machines==num_machines )
        #                self.assertTrue( j.num_mpiprocs==num_mpiprocs )

    def test_parse_failed_squeue_output(self):
        """Test that _parse_joblist_output reacts as expected to failures."""
        scheduler = SlurmScheduler()

        # non-zero return value should raise
        with pytest.raises(SchedulerError, match='squeue returned exit code 1'):
            scheduler._parse_joblist_output(1, TEXT_SQUEUE_TO_TEST, '')

        # non-empty stderr should be logged
        with self.assertLogs(scheduler.logger, logging.WARNING):
            scheduler._parse_joblist_output(0, TEXT_SQUEUE_TO_TEST, 'error message')


@pytest.mark.parametrize(
    'value,expected',
    [
        ('2', 2 * 60),
        ('02', 2 * 60),
        ('02:3', 2 * 60 + 3),
        ('02:03', 2 * 60 + 3),
        ('1:02:03', 3600 + 2 * 60 + 3),
        ('01:02:03', 3600 + 2 * 60 + 3),
        ('1-3', 86400 + 3 * 3600),
        ('01-3', 86400 + 3 * 3600),
        ('01-03', 86400 + 3 * 3600),
        ('1-3:5', 86400 + 3 * 3600 + 5 * 60),
        ('01-3:05', 86400 + 3 * 3600 + 5 * 60),
        ('01-03:05', 86400 + 3 * 3600 + 5 * 60),
        ('1-3:5:7', 86400 + 3 * 3600 + 5 * 60 + 7),
        ('01-3:05:7', 86400 + 3 * 3600 + 5 * 60 + 7),
        ('01-03:05:07', 86400 + 3 * 3600 + 5 * 60 + 7),
        ('UNLIMITED', 2**31 - 1),
        ('NOT_SET', None),
    ],
)
def test_time_conversion(value, expected):
    """Test conversion of (relative) times.

    From docs, acceptable time formats include
    "minutes", "minutes:seconds", "hours:minutes:seconds",
    "days-hours", "days-hours:minutes" and "days-hours:minutes:seconds".
    """
    scheduler = SlurmScheduler()
    assert scheduler._convert_time(value) == expected


def test_time_conversion_errors(caplog):
    """Test conversion of (relative) times for bad inputs."""
    scheduler = SlurmScheduler()

    # Disable logging to avoid excessive output during test
    with caplog.at_level(logging.CRITICAL):
        with pytest.raises(ValueError, match='Unrecognized format for time string.'):
            # Empty string not valid
            scheduler._convert_time('')
        with pytest.raises(ValueError, match='Unrecognized format for time string.'):
            # there should be something after the dash
            scheduler._convert_time('1-')
        with pytest.raises(ValueError, match='Unrecognized format for time string.'):
            # there should be something after the dash
            # there cannot be a dash after the colons
            scheduler._convert_time('1:2-3')


class TestSubmitScript:
    """Test submit script generation by SLURM scheduler plugin."""

    def test_submit_script(self):
        """Test the creation of a simple submission script."""
        from aiida.common.datastructures import CodeRunMode
        from aiida.schedulers.datastructures import JobTemplate, JobTemplateCodeInfo

        scheduler = SlurmScheduler()

        job_tmpl = JobTemplate()
        job_tmpl.shebang = '#!/bin/bash'
        job_tmpl.uuid = str(uuid.uuid4())
        job_tmpl.job_resource = scheduler.create_job_resource(num_machines=1, num_mpiprocs_per_machine=1)
        job_tmpl.max_wallclock_seconds = 24 * 3600
        tmpl_code_info = JobTemplateCodeInfo()
        tmpl_code_info.cmdline_params = ['mpirun', '-np', '23', 'pw.x', '-npool', '1']
        tmpl_code_info.stdin_name = 'aiida.in'
        job_tmpl.codes_info = [tmpl_code_info]
        job_tmpl.codes_run_mode = CodeRunMode.SERIAL

        submit_script_text = scheduler.get_submit_script(job_tmpl)

        assert submit_script_text.startswith('#!/bin/bash')

        assert '#SBATCH --no-requeue' in submit_script_text
        assert '#SBATCH --time=1-00:00:00' in submit_script_text
        assert '#SBATCH --nodes=1' in submit_script_text

        assert "'mpirun' '-np' '23' 'pw.x' '-npool' '1' < 'aiida.in'" in submit_script_text

    def test_submit_script_bad_shebang(self):
        """Test that first line of submit script is as expected."""
        from aiida.common.datastructures import CodeRunMode
        from aiida.schedulers.datastructures import JobTemplate, JobTemplateCodeInfo

        scheduler = SlurmScheduler()
        tmpl_code_info = JobTemplateCodeInfo()
        tmpl_code_info.cmdline_params = ['mpirun', '-np', '23', 'pw.x', '-npool', '1']
        tmpl_code_info.stdin_name = 'aiida.in'

        for shebang, expected_first_line in ((None, '#!/bin/bash'), ('', ''), ('NOSET', '#!/bin/bash')):
            job_tmpl = JobTemplate()
            if shebang == 'NOSET':
                pass
            else:
                job_tmpl.shebang = shebang
            job_tmpl.job_resource = scheduler.create_job_resource(num_machines=1, num_mpiprocs_per_machine=1)
            job_tmpl.codes_info = [tmpl_code_info]
            job_tmpl.codes_run_mode = CodeRunMode.SERIAL

            submit_script_text = scheduler.get_submit_script(job_tmpl)

            # This tests if the implementation correctly chooses the default:
            assert submit_script_text.split('\n', maxsplit=1)[0] == expected_first_line

    def test_submit_script_with_num_cores_per_machine(self):
        """Test to verify if script works fine if we specify only
        num_cores_per_machine value.
        """
        from aiida.common.datastructures import CodeRunMode
        from aiida.schedulers.datastructures import JobTemplate, JobTemplateCodeInfo

        scheduler = SlurmScheduler()

        job_tmpl = JobTemplate()
        job_tmpl.shebang = '#!/bin/bash'
        job_tmpl.job_resource = scheduler.create_job_resource(
            num_machines=1, num_mpiprocs_per_machine=2, num_cores_per_machine=24
        )
        job_tmpl.uuid = str(uuid.uuid4())
        job_tmpl.max_wallclock_seconds = 24 * 3600
        tmpl_code_info = JobTemplateCodeInfo()
        tmpl_code_info.cmdline_params = ['mpirun', '-np', '23', 'pw.x', '-npool', '1']
        tmpl_code_info.stdin_name = 'aiida.in'
        job_tmpl.codes_info = [tmpl_code_info]
        job_tmpl.codes_run_mode = CodeRunMode.SERIAL

        submit_script_text = scheduler.get_submit_script(job_tmpl)

        assert '#SBATCH --no-requeue' in submit_script_text
        assert '#SBATCH --time=1-00:00:00' in submit_script_text
        assert '#SBATCH --nodes=1' in submit_script_text
        assert '#SBATCH --ntasks-per-node=2' in submit_script_text
        assert '#SBATCH --cpus-per-task=12' in submit_script_text

        assert "'mpirun' '-np' '23' 'pw.x' '-npool' '1' < 'aiida.in'" in submit_script_text

    def test_submit_script_with_num_cores_per_mpiproc(self):
        """Test to verify if scripts works fine if we pass only num_cores_per_mpiproc value"""
        from aiida.common.datastructures import CodeRunMode
        from aiida.schedulers.datastructures import JobTemplate, JobTemplateCodeInfo

        scheduler = SlurmScheduler()

        job_tmpl = JobTemplate()
        job_tmpl.shebang = '#!/bin/bash'
        job_tmpl.job_resource = scheduler.create_job_resource(
            num_machines=1, num_mpiprocs_per_machine=1, num_cores_per_mpiproc=24
        )
        job_tmpl.uuid = str(uuid.uuid4())
        job_tmpl.max_wallclock_seconds = 24 * 3600
        tmpl_code_info = JobTemplateCodeInfo()
        tmpl_code_info.cmdline_params = ['mpirun', '-np', '23', 'pw.x', '-npool', '1']
        tmpl_code_info.stdin_name = 'aiida.in'
        job_tmpl.codes_info = [tmpl_code_info]
        job_tmpl.codes_run_mode = CodeRunMode.SERIAL

        submit_script_text = scheduler.get_submit_script(job_tmpl)

        assert '#SBATCH --no-requeue' in submit_script_text
        assert '#SBATCH --time=1-00:00:00' in submit_script_text
        assert '#SBATCH --nodes=1' in submit_script_text
        assert '#SBATCH --ntasks-per-node=1' in submit_script_text
        assert '#SBATCH --cpus-per-task=24' in submit_script_text

        assert "'mpirun' '-np' '23' 'pw.x' '-npool' '1' < 'aiida.in'" in submit_script_text

    def test_submit_script_with_num_cores_per_machine_and_mpiproc1(self):
        """Test to verify if scripts works fine if we pass both
        num_cores_per_machine and num_cores_per_mpiproc correct values.
        It should pass in check:
        res.num_cores_per_mpiproc * res.num_mpiprocs_per_machine = res.num_cores_per_machine
        """
        from aiida.common.datastructures import CodeRunMode
        from aiida.schedulers.datastructures import JobTemplate, JobTemplateCodeInfo

        scheduler = SlurmScheduler()

        job_tmpl = JobTemplate()
        job_tmpl.shebang = '#!/bin/bash'
        job_tmpl.job_resource = scheduler.create_job_resource(
            num_machines=1, num_mpiprocs_per_machine=1, num_cores_per_machine=24, num_cores_per_mpiproc=24
        )
        job_tmpl.uuid = str(uuid.uuid4())
        job_tmpl.max_wallclock_seconds = 24 * 3600
        tmpl_code_info = JobTemplateCodeInfo()
        tmpl_code_info.cmdline_params = ['mpirun', '-np', '23', 'pw.x', '-npool', '1']
        tmpl_code_info.stdin_name = 'aiida.in'
        job_tmpl.codes_info = [tmpl_code_info]
        job_tmpl.codes_run_mode = CodeRunMode.SERIAL

        submit_script_text = scheduler.get_submit_script(job_tmpl)

        assert '#SBATCH --no-requeue' in submit_script_text
        assert '#SBATCH --time=1-00:00:00' in submit_script_text
        assert '#SBATCH --nodes=1' in submit_script_text
        assert '#SBATCH --ntasks-per-node=1' in submit_script_text
        assert '#SBATCH --cpus-per-task=24' in submit_script_text

        assert "'mpirun' '-np' '23' 'pw.x' '-npool' '1' < 'aiida.in'" in submit_script_text

    def test_submit_script_with_num_cores_per_machine_and_mpiproc2(self):
        """Test to verify if scripts works fine if we pass
        num_cores_per_machine and num_cores_per_mpiproc wrong values.

        It should fail in check:
        res.num_cores_per_mpiproc * res.num_mpiprocs_per_machine = res.num_cores_per_machine
        """
        from aiida.schedulers.datastructures import JobTemplate

        scheduler = SlurmScheduler()

        job_tmpl = JobTemplate()
        with pytest.raises(ValueError, match='`num_cores_per_machine` must be equal to'):
            job_tmpl.job_resource = scheduler.create_job_resource(
                num_machines=1, num_mpiprocs_per_machine=1, num_cores_per_machine=24, num_cores_per_mpiproc=23
            )

    def test_submit_script_with_mem(self):
        """Test to verify if script can be created with memory specification.

        It should pass this check:
            if physical_memory_kb < 0:  # 0 is allowed and means no limit (https://slurm.schedmd.com/sbatch.html)
                raise ValueError
        and correctly set the memory value in the script with the --mem option.
        """
        from aiida.common.datastructures import CodeRunMode
        from aiida.schedulers.datastructures import JobTemplate, JobTemplateCodeInfo

        scheduler = SlurmScheduler()
        job_tmpl = JobTemplate()

        job_tmpl.uuid = str(uuid.uuid4())
        job_tmpl.max_wallclock_seconds = 24 * 3600
        tmpl_code_info = JobTemplateCodeInfo()
        tmpl_code_info.cmdline_params = ['mpirun', '-np', '23', 'pw.x', '-npool', '1']
        tmpl_code_info.stdin_name = 'aiida.in'
        job_tmpl.codes_info = [tmpl_code_info]
        job_tmpl.codes_run_mode = CodeRunMode.SERIAL
        job_tmpl.job_resource = scheduler.create_job_resource(num_machines=1, num_mpiprocs_per_machine=1)
        # Check for a regular (positive) value
        job_tmpl.max_memory_kb = 316 * 1024
        submit_script_text = scheduler.get_submit_script(job_tmpl)
        assert '#SBATCH --mem=316' in submit_script_text
        # Check for the special zero value
        job_tmpl.max_memory_kb = 0
        submit_script_text = scheduler.get_submit_script(job_tmpl)
        assert '#SBATCH --mem=0' in submit_script_text

    def test_submit_script_with_negative_mem_value(self):
        """Test to verify if script can be created with an invalid memory value.

        It should fail in check:
            if physical_memory_kb < 0:  # 0 is allowed and means no limit (https://slurm.schedmd.com/sbatch.html)
                raise ValueError
        """
        import re

        from aiida.schedulers.datastructures import JobTemplate

        scheduler = SlurmScheduler()
        job_tmpl = JobTemplate()

        with pytest.raises(
            ValueError, match=re.escape('max_memory_kb must be a non-negative integer (in kB)! It is instead `-9`')
        ):
            job_tmpl.job_resource = scheduler.create_job_resource(num_machines=1, num_mpiprocs_per_machine=1)
            job_tmpl.max_memory_kb = -9
            scheduler.get_submit_script(job_tmpl)

    def test_submit_script_rerunnable(self):
        """Test the creation of a submission script with the `rerunnable` option."""
        from aiida.common.datastructures import CodeRunMode
        from aiida.schedulers.datastructures import JobTemplate, JobTemplateCodeInfo

        scheduler = SlurmScheduler()

        # minimal job template setup
        job_tmpl = JobTemplate()
        job_tmpl.job_resource = scheduler.create_job_resource(num_machines=1, num_mpiprocs_per_machine=1)
        tmpl_code_info = JobTemplateCodeInfo()
        tmpl_code_info.cmdline_params = []
        job_tmpl.codes_info = [tmpl_code_info]
        job_tmpl.codes_run_mode = CodeRunMode.SERIAL

        # Test the `rerunnable` setting
        job_tmpl.rerunnable = True
        submit_script_text = scheduler.get_submit_script(job_tmpl)
        assert '#SBATCH --requeue' in submit_script_text
        assert '#SBATCH --no-requeue' not in submit_script_text

        job_tmpl.rerunnable = False
        submit_script_text = scheduler.get_submit_script(job_tmpl)
        assert '#SBATCH --requeue' not in submit_script_text
        assert '#SBATCH --no-requeue' in submit_script_text


class TestJoblistCommand:
    """Tests of the issued squeue command."""

    def test_joblist_single(self):
        """Test that asking for a single job results in duplication of the list."""
        scheduler = SlurmScheduler()

        command = scheduler._get_joblist_command(jobs=['123'])
        assert '123,123' in command

    def test_joblist_multi(self):
        """Test that asking for multiple jobs does not result in duplications."""
        scheduler = SlurmScheduler()

        command = scheduler._get_joblist_command(jobs=['123', '456'])
        assert '123,456' in command
        assert '456,456' not in command


def test_parse_out_of_memory():
    """Test that for job that failed due to OOM `parse_output` return the `ERROR_SCHEDULER_OUT_OF_MEMORY` code."""
    scheduler = SlurmScheduler()
    stdout = ''
    stderr = ''
    detailed_job_info = {
        'retval': 0,
        'stderr': '',
        'stdout': 'Account|State|\nroot|OUT_OF_MEMORY|\n',
    }

    exit_code = scheduler.parse_output(detailed_job_info, stdout, stderr)
    assert exit_code == CalcJob.exit_codes.ERROR_SCHEDULER_OUT_OF_MEMORY


def test_parse_node_failure():
    """Test that `ERROR_SCHEDULER_NODE_FAILURE` code is returned if `STATE == NODE_FAIL`."""
    scheduler = SlurmScheduler()
    detailed_job_info = {
        'retval': 0,
        'stderr': '',
        'stdout': 'Account|State|\nroot|NODE_FAIL|\n',
    }

    exit_code = scheduler.parse_output(detailed_job_info, '', '')
    assert exit_code == CalcJob.exit_codes.ERROR_SCHEDULER_NODE_FAILURE


@pytest.mark.parametrize(
    'detailed_job_info, expected',
    [
        ('string', TypeError),  # Not a dictionary
        ({'stderr': ''}, ValueError),  # Key `stdout` missing
        ({'stdout': None}, TypeError),  # `stdout` is not a string
        ({'stdout': ''}, ValueError),  # `stdout` does not contain at least two lines
        (
            {'stdout': 'Account|State|\nValue|'},
            ValueError,
        ),  # `stdout` second line contains too few elements separated by pipe
    ],
)
def test_parse_output_invalid(detailed_job_info, expected):
    """Test `SlurmScheduler.parse_output` for various invalid arguments."""
    scheduler = SlurmScheduler()

    with pytest.raises(expected):
        scheduler.parse_output(detailed_job_info, '', '')


def test_parse_output_valid():
    """Test `SlurmScheduler.parse_output` for valid arguments."""
    detailed_job_info = {'stdout': 'State|Account|\n||\n'}
    scheduler = SlurmScheduler()
    assert scheduler.parse_output(detailed_job_info, '', '') is None


def test_parse_submit_output_invalid_account():
    """Test ``SlurmScheduler._parse_submit_output`` returns exit code if stderr contains error about invalid account."""
    scheduler = SlurmScheduler()
    stderr = 'Batch job submission failed: Invalid account or account/partition combination specified'
    result = scheduler._parse_submit_output(1, '', stderr)
    assert result == CalcJob.exit_codes.ERROR_SCHEDULER_INVALID_ACCOUNT
