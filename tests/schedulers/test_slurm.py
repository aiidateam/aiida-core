# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the SLURM scheduler plugin."""
import unittest
import logging
import uuid
import datetime

from aiida.schedulers.plugins.slurm import SlurmScheduler, JobState

# pylint: disable=line-too-long
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


class TestParserSqueue(unittest.TestCase):
    """
    Tests to verify if teh function _parse_joblist_output behave correctly
    The tests is done parsing a string defined above, to be used offline
    """

    def test_parse_common_joblist_output(self):
        """
        Test whether _parse_joblist can parse the qstat -f output
        """
        scheduler = SlurmScheduler()

        retval = 0
        stdout = TEXT_SQUEUE_TO_TEST
        stderr = ''

        job_list = scheduler._parse_joblist_output(retval, stdout, stderr)  # pylint: disable=protected-access
        job_dict = {j.job_id: j for j in job_list}

        # The parameters are hard coded in the text to parse
        job_parsed = len(job_list)
        self.assertEqual(job_parsed, JOBS_ON_CLUSTER)

        job_running_parsed = len([j for j in job_list if j.job_state \
                                  and j.job_state == JobState.RUNNING])
        self.assertEqual(len(JOBS_RUNNING), job_running_parsed)

        job_held_parsed = len([j for j in job_list if j.job_state and j.job_state == JobState.QUEUED_HELD])
        self.assertEqual(JOBS_HELD, job_held_parsed)

        job_queued_parsed = len([j for j in job_list if j.job_state and j.job_state == JobState.QUEUED])
        self.assertEqual(JOBS_QUEUED, job_queued_parsed)

        parsed_running_users = [j.job_owner for j in job_list if j.job_state and j.job_state == JobState.RUNNING]
        self.assertEqual(set(USERS_RUNNING), set(parsed_running_users))

        parsed_running_jobs = [j.job_id for j in job_list if j.job_state and j.job_state == JobState.RUNNING]
        self.assertEqual(set(JOBS_RUNNING), set(parsed_running_jobs))

        self.assertEqual(job_dict['863553'].requested_wallclock_time_seconds, 30 * 60)  # pylint: disable=invalid-name
        self.assertEqual(job_dict['863553'].wallclock_time_seconds, 29 * 60 + 29)
        self.assertEqual(job_dict['863553'].dispatch_time, datetime.datetime(2013, 5, 23, 11, 44, 11))
        self.assertEqual(job_dict['863553'].submission_time, datetime.datetime(2013, 5, 23, 10, 42, 11))

        self.assertEqual(job_dict['863100'].annotation, 'Resources')
        self.assertEqual(job_dict['863100'].num_machines, 32)
        self.assertEqual(job_dict['863100'].num_mpiprocs, 1024)
        self.assertEqual(job_dict['863100'].queue_name, 'normal')

        self.assertEqual(job_dict['861352'].title, 'Pressure_PBEsol_0')

        self.assertEqual(job_dict['863554'].requested_wallclock_time_seconds, None)  # pylint: disable=invalid-name

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


class TestTimes(unittest.TestCase):
    """Test time parsing of SLURM scheduler plugin."""

    def test_time_conversion(self):
        """
        Test conversion of (relative) times.

        From docs, acceptable time formats include
        "minutes", "minutes:seconds", "hours:minutes:seconds",
        "days-hours", "days-hours:minutes" and "days-hours:minutes:seconds".
        """
        # pylint: disable=protected-access
        scheduler = SlurmScheduler()
        self.assertEqual(scheduler._convert_time('2'), 2 * 60)
        self.assertEqual(scheduler._convert_time('02'), 2 * 60)

        self.assertEqual(scheduler._convert_time('02:3'), 2 * 60 + 3)
        self.assertEqual(scheduler._convert_time('02:03'), 2 * 60 + 3)

        self.assertEqual(scheduler._convert_time('1:02:03'), 3600 + 2 * 60 + 3)
        self.assertEqual(scheduler._convert_time('01:02:03'), 3600 + 2 * 60 + 3)

        self.assertEqual(scheduler._convert_time('1-3'), 86400 + 3 * 3600)
        self.assertEqual(scheduler._convert_time('01-3'), 86400 + 3 * 3600)
        self.assertEqual(scheduler._convert_time('01-03'), 86400 + 3 * 3600)

        self.assertEqual(scheduler._convert_time('1-3:5'), 86400 + 3 * 3600 + 5 * 60)
        self.assertEqual(scheduler._convert_time('01-3:05'), 86400 + 3 * 3600 + 5 * 60)
        self.assertEqual(scheduler._convert_time('01-03:05'), 86400 + 3 * 3600 + 5 * 60)

        self.assertEqual(scheduler._convert_time('1-3:5:7'), 86400 + 3 * 3600 + 5 * 60 + 7)
        self.assertEqual(scheduler._convert_time('01-3:05:7'), 86400 + 3 * 3600 + 5 * 60 + 7)
        self.assertEqual(scheduler._convert_time('01-03:05:07'), 86400 + 3 * 3600 + 5 * 60 + 7)

        self.assertEqual(scheduler._convert_time('UNLIMITED'), 2**31 - 1)
        self.assertEqual(scheduler._convert_time('NOT_SET'), None)

        # Disable logging to avoid excessive output during test
        logging.disable(logging.ERROR)
        with self.assertRaises(ValueError):
            # Empty string not valid
            scheduler._convert_time('')
        with self.assertRaises(ValueError):
            # there should be something after the dash
            scheduler._convert_time('1-')
        with self.assertRaises(ValueError):
            # there should be something after the dash
            # there cannot be a dash after the colons
            scheduler._convert_time('1:2-3')
        # Reset logging level
        logging.disable(logging.NOTSET)


class TestSubmitScript(unittest.TestCase):
    """Test submit script generation by SLURM scheduler plugin."""

    def test_submit_script(self):
        """
        Test the creation of a simple submission script.
        """
        from aiida.schedulers.datastructures import JobTemplate
        from aiida.common.datastructures import CodeInfo, CodeRunMode

        scheduler = SlurmScheduler()

        job_tmpl = JobTemplate()
        job_tmpl.shebang = '#!/bin/bash'
        job_tmpl.uuid = str(uuid.uuid4())
        job_tmpl.job_resource = scheduler.create_job_resource(num_machines=1, num_mpiprocs_per_machine=1)
        job_tmpl.max_wallclock_seconds = 24 * 3600
        code_info = CodeInfo()
        code_info.cmdline_params = ['mpirun', '-np', '23', 'pw.x', '-npool', '1']
        code_info.stdin_name = 'aiida.in'
        job_tmpl.codes_info = [code_info]
        job_tmpl.codes_run_mode = CodeRunMode.SERIAL

        submit_script_text = scheduler.get_submit_script(job_tmpl)

        self.assertTrue(submit_script_text.startswith('#!/bin/bash'))

        self.assertTrue('#SBATCH --no-requeue' in submit_script_text)
        self.assertTrue('#SBATCH --time=1-00:00:00' in submit_script_text)
        self.assertTrue('#SBATCH --nodes=1' in submit_script_text)

        self.assertTrue("'mpirun' '-np' '23' 'pw.x' '-npool' '1'" + \
                        " < 'aiida.in'" in submit_script_text)

    def test_submit_script_bad_shebang(self):
        """Test that first line of submit script is as expected."""
        from aiida.schedulers.datastructures import JobTemplate
        from aiida.common.datastructures import CodeInfo, CodeRunMode

        scheduler = SlurmScheduler()
        code_info = CodeInfo()
        code_info.cmdline_params = ['mpirun', '-np', '23', 'pw.x', '-npool', '1']
        code_info.stdin_name = 'aiida.in'

        for (shebang, expected_first_line) in ((None, '#!/bin/bash'), ('', ''), ('NOSET', '#!/bin/bash')):
            job_tmpl = JobTemplate()
            if shebang == 'NOSET':
                pass
            else:
                job_tmpl.shebang = shebang
            job_tmpl.job_resource = scheduler.create_job_resource(num_machines=1, num_mpiprocs_per_machine=1)
            job_tmpl.codes_info = [code_info]
            job_tmpl.codes_run_mode = CodeRunMode.SERIAL

            submit_script_text = scheduler.get_submit_script(job_tmpl)

            # This tests if the implementation correctly chooses the default:
            self.assertEqual(submit_script_text.split('\n')[0], expected_first_line)

    def test_submit_script_with_num_cores_per_machine(self):  # pylint: disable=invalid-name
        """
        Test to verify if script works fine if we specify only
        num_cores_per_machine value.
        """
        from aiida.schedulers.datastructures import JobTemplate
        from aiida.common.datastructures import CodeInfo, CodeRunMode

        scheduler = SlurmScheduler()

        job_tmpl = JobTemplate()
        job_tmpl.shebang = '#!/bin/bash'
        job_tmpl.job_resource = scheduler.create_job_resource(
            num_machines=1, num_mpiprocs_per_machine=2, num_cores_per_machine=24
        )
        job_tmpl.uuid = str(uuid.uuid4())
        job_tmpl.max_wallclock_seconds = 24 * 3600
        code_info = CodeInfo()
        code_info.cmdline_params = ['mpirun', '-np', '23', 'pw.x', '-npool', '1']
        code_info.stdin_name = 'aiida.in'
        job_tmpl.codes_info = [code_info]
        job_tmpl.codes_run_mode = CodeRunMode.SERIAL

        submit_script_text = scheduler.get_submit_script(job_tmpl)

        self.assertTrue('#SBATCH --no-requeue' in submit_script_text)
        self.assertTrue('#SBATCH --time=1-00:00:00' in submit_script_text)
        self.assertTrue('#SBATCH --nodes=1' in submit_script_text)
        self.assertTrue('#SBATCH --ntasks-per-node=2' in submit_script_text)
        self.assertTrue('#SBATCH --cpus-per-task=12' in submit_script_text)

        self.assertTrue("'mpirun' '-np' '23' 'pw.x' '-npool' '1'" + \
                        " < 'aiida.in'" in submit_script_text)

    def test_submit_script_with_num_cores_per_mpiproc(self):  # pylint: disable=invalid-name
        """
        Test to verify if scripts works fine if we pass only num_cores_per_mpiproc value
        """
        from aiida.schedulers.datastructures import JobTemplate
        from aiida.common.datastructures import CodeInfo, CodeRunMode

        scheduler = SlurmScheduler()

        job_tmpl = JobTemplate()
        job_tmpl.shebang = '#!/bin/bash'
        job_tmpl.job_resource = scheduler.create_job_resource(
            num_machines=1, num_mpiprocs_per_machine=1, num_cores_per_mpiproc=24
        )
        job_tmpl.uuid = str(uuid.uuid4())
        job_tmpl.max_wallclock_seconds = 24 * 3600
        code_info = CodeInfo()
        code_info.cmdline_params = ['mpirun', '-np', '23', 'pw.x', '-npool', '1']
        code_info.stdin_name = 'aiida.in'
        job_tmpl.codes_info = [code_info]
        job_tmpl.codes_run_mode = CodeRunMode.SERIAL

        submit_script_text = scheduler.get_submit_script(job_tmpl)

        self.assertTrue('#SBATCH --no-requeue' in submit_script_text)
        self.assertTrue('#SBATCH --time=1-00:00:00' in submit_script_text)
        self.assertTrue('#SBATCH --nodes=1' in submit_script_text)
        self.assertTrue('#SBATCH --ntasks-per-node=1' in submit_script_text)
        self.assertTrue('#SBATCH --cpus-per-task=24' in submit_script_text)

        self.assertTrue("'mpirun' '-np' '23' 'pw.x' '-npool' '1'" + \
                        " < 'aiida.in'" in submit_script_text)

    def test_submit_script_with_num_cores_per_machine_and_mpiproc1(self):  # pylint: disable=invalid-name
        """
        Test to verify if scripts works fine if we pass both
        num_cores_per_machine and num_cores_per_mpiproc correct values.
        It should pass in check:
        res.num_cores_per_mpiproc * res.num_mpiprocs_per_machine = res.num_cores_per_machine
        """
        from aiida.schedulers.datastructures import JobTemplate
        from aiida.common.datastructures import CodeInfo, CodeRunMode

        scheduler = SlurmScheduler()

        job_tmpl = JobTemplate()
        job_tmpl.shebang = '#!/bin/bash'
        job_tmpl.job_resource = scheduler.create_job_resource(
            num_machines=1, num_mpiprocs_per_machine=1, num_cores_per_machine=24, num_cores_per_mpiproc=24
        )
        job_tmpl.uuid = str(uuid.uuid4())
        job_tmpl.max_wallclock_seconds = 24 * 3600
        code_info = CodeInfo()
        code_info.cmdline_params = ['mpirun', '-np', '23', 'pw.x', '-npool', '1']
        code_info.stdin_name = 'aiida.in'
        job_tmpl.codes_info = [code_info]
        job_tmpl.codes_run_mode = CodeRunMode.SERIAL

        submit_script_text = scheduler.get_submit_script(job_tmpl)

        self.assertTrue('#SBATCH --no-requeue' in submit_script_text)
        self.assertTrue('#SBATCH --time=1-00:00:00' in submit_script_text)
        self.assertTrue('#SBATCH --nodes=1' in submit_script_text)
        self.assertTrue('#SBATCH --ntasks-per-node=1' in submit_script_text)
        self.assertTrue('#SBATCH --cpus-per-task=24' in submit_script_text)

        self.assertTrue("'mpirun' '-np' '23' 'pw.x' '-npool' '1'" + \
                        " < 'aiida.in'" in submit_script_text)

    def test_submit_script_with_num_cores_per_machine_and_mpiproc2(self):  # pylint: disable=invalid-name
        """
        Test to verify if scripts works fine if we pass
        num_cores_per_machine and num_cores_per_mpiproc wrong values.

        It should fail in check:
        res.num_cores_per_mpiproc * res.num_mpiprocs_per_machine = res.num_cores_per_machine
        """
        from aiida.schedulers.datastructures import JobTemplate

        scheduler = SlurmScheduler()

        job_tmpl = JobTemplate()
        with self.assertRaises(ValueError):
            job_tmpl.job_resource = scheduler.create_job_resource(
                num_machines=1, num_mpiprocs_per_machine=1, num_cores_per_machine=24, num_cores_per_mpiproc=23
            )


if __name__ == '__main__':
    unittest.main()
