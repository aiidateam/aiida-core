# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import unittest
import logging
from aiida.schedulers.plugins.sge import *

text_qstat_ext_urg_xml_test = """<?xml version='1.0'?>
<job_info  xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <queue_info>
    <job_list state="running">
      <JB_job_number>1212299</JB_job_number>
      <JAT_prio>10.05000</JAT_prio>
      <JAT_ntix>1.00000</JAT_ntix>
      <JB_nurg>0.00000</JB_nurg>
      <JB_urg>1000</JB_urg>
      <JB_rrcontr>1000</JB_rrcontr>
      <JB_wtcontr>0</JB_wtcontr>
      <JB_dlcontr>0</JB_dlcontr>
      <JB_name>Heusler</JB_name>
      <JB_owner>dorigm7s</JB_owner>
      <JB_project>ams.p</JB_project>
      <JB_department>defaultdepartment</JB_department>
      <state>r</state>
      <JAT_start_time>2013-06-18T12:08:23</JAT_start_time>
      <cpu_usage>81.00000</cpu_usage>
      <mem_usage>15.96530</mem_usage>
      <io_usage>0.00667</io_usage>
      <tickets>126559</tickets>
      <JB_override_tickets>0</JB_override_tickets>
      <JB_jobshare>0</JB_jobshare>
      <otickets>0</otickets>
      <ftickets>0</ftickets>
      <stickets>126559</stickets>
      <JAT_share>0.27043</JAT_share>
      <queue_name>serial.q@node080</queue_name>
      <slots>1</slots>
    </job_list>
  </queue_info>
  <job_info>
    <job_list state="pending">
      <JB_job_number>1212263</JB_job_number>
      <JAT_prio>0.16272</JAT_prio>
      <JAT_ntix>0.01127</JAT_ntix>
      <JB_nurg>0.07368</JB_nurg>
      <JB_urg>8000</JB_urg>
      <JB_rrcontr>8000</JB_rrcontr>
      <JB_wtcontr>0</JB_wtcontr>
      <JB_dlcontr>0</JB_dlcontr>
      <JB_name>Heusler</JB_name>
      <JB_owner>dorigm7s</JB_owner>
      <JB_project>ams.p</JB_project>
      <JB_department>defaultdepartment</JB_department>
      <state>qw</state>
      <JB_submission_time>2013-06-18T12:00:57</JB_submission_time>
      <tickets>1426</tickets>
      <JB_override_tickets>0</JB_override_tickets>
      <JB_jobshare>0</JB_jobshare>
      <otickets>0</otickets>
      <ftickets>0</ftickets>
      <stickets>1426</stickets>
      <JAT_share>0.00419</JAT_share>
      <queue_name></queue_name>
      <slots>8</slots>
    </job_list>
    <job_list state="pending">
      <JB_job_number>1212322</JB_job_number>
      <JAT_prio>0.00000</JAT_prio>
      <JAT_ntix>0.00000</JAT_ntix>
      <JB_nurg>0.00000</JB_nurg>
      <JB_urg>0</JB_urg>
      <JB_rrcontr>0</JB_rrcontr>
      <JB_wtcontr>0</JB_wtcontr>
      <JB_dlcontr>0</JB_dlcontr>
      <JB_name>Heusler</JB_name>
      <JB_owner>dorigm7s</JB_owner>
      <JB_project>ams.p</JB_project>
      <JB_department>defaultdepartment</JB_department>
      <state>hqw</state>
      <JB_submission_time>2013-06-18T12:09:47</JB_submission_time>
      <tickets>0</tickets>
      <JB_override_tickets>0</JB_override_tickets>
      <JB_jobshare>0</JB_jobshare>
      <otickets>0</otickets>
      <ftickets>0</ftickets>
      <stickets>0</stickets>
      <JAT_share>0.00000</JAT_share>
      <queue_name></queue_name>
      <slots>1</slots>
    </job_list>
  </job_info>
</job_info>"""

text_qstat_ext_urg_xml_test_raise = """<?xml version='1.0'?>
            <job_info  xmlns:xsd="http://www.w3.org/2001/XMLSchema">
          <queue_info>
          </queue_info>
          <job_info>
            <job_list state="running">
              <JB_job_number></JB_job_number>
              <JB_owner>dorigm7s</JB_owner>
              <state>qw</state>
            </job_list>
          </job_info>
        </job_info>
        """

text_xml_parsing_fails_raise = """<?xml version='1.0'?>
            <job_info  xmlns:xsd="http://www.w3.org/2001/XMLSchema">
          <queue_infoXXXXXXXX>
          </queue_info>
          <job_info>
            <job_list state="running">
              <JB_job_number></JB_job_number>
              <JB_owner>dorigm7s</JB_owner>
              <state>qw</state>
            </job_list>
          </job_info>
        </job_info>
        """

text_check_queue_job_info = """<?xml version='1.0'?>
        <job_info  xmlns:xsd="http://www.w3.org/2001/XMLSchema">
          <job_info>
            <job_list state="running">
              <JB_job_number>99</JB_job_number>
              <JB_owner>dorigm7s</JB_owner>
              <state>qw</state>
            </job_list>
          </job_info>
        </job_info>
        """

test_raw_data = """<job_list state="running">
      <JB_job_number>1212299</JB_job_number>
      <JAT_prio>10.05000</JAT_prio>
      <JAT_ntix>1.00000</JAT_ntix>
      <JB_nurg>0.00000</JB_nurg>
      <JB_urg>1000</JB_urg>
      <JB_rrcontr>1000</JB_rrcontr>
      <JB_wtcontr>0</JB_wtcontr>
      <JB_dlcontr>0</JB_dlcontr>
      <JB_name>Heusler</JB_name>
      <JB_owner>dorigm7s</JB_owner>
      <JB_project>ams.p</JB_project>
      <JB_department>defaultdepartment</JB_department>
      <state>r</state>
      <JAT_start_time>2013-06-18T12:08:23</JAT_start_time>
      <cpu_usage>81.00000</cpu_usage>
      <mem_usage>15.96530</mem_usage>
      <io_usage>0.00667</io_usage>
      <tickets>126559</tickets>
      <JB_override_tickets>0</JB_override_tickets>
      <JB_jobshare>0</JB_jobshare>
      <otickets>0</otickets>
      <ftickets>0</ftickets>
      <stickets>126559</stickets>
      <JAT_share>0.27043</JAT_share>
      <queue_name>serial.q@node080</queue_name>
      <slots>1</slots>
    </job_list>"""


class TestCommand(unittest.TestCase):

    def test_get_joblist_command(self):
        sge = SgeScheduler()

        # TEST 1:
        sge_get_joblist_command = sge._get_joblist_command(user='ExamplUsr')

        self.assertTrue('qstat' in sge_get_joblist_command)
        self.assertTrue('-xml' in sge_get_joblist_command)
        self.assertTrue('-ext' in sge_get_joblist_command)
        self.assertTrue('-u' in sge_get_joblist_command)
        self.assertTrue('-urg' in sge_get_joblist_command)
        self.assertTrue('ExamplUsr' in sge_get_joblist_command)

        # TEST 2:
        sge_get_joblist_command = sge._get_joblist_command()

        self.assertTrue('qstat' in sge_get_joblist_command)
        self.assertTrue('-xml' in sge_get_joblist_command)
        self.assertTrue('-ext' in sge_get_joblist_command)
        self.assertTrue('-u' in sge_get_joblist_command)
        self.assertTrue('-urg' in sge_get_joblist_command)
        self.assertTrue('*' in sge_get_joblist_command)

    def test_detailed_jobinfo_command(self):
        sge = SgeScheduler()

        sge_get_djobinfo_command = sge._get_detailed_jobinfo_command('123456')

        self.assertTrue('123456' in sge_get_djobinfo_command)
        self.assertTrue('qacct' in sge_get_djobinfo_command)
        self.assertTrue('-j' in sge_get_djobinfo_command)

    def test_get_submit_command(self):
        sge = SgeScheduler()

        sge_get_submit_command = sge._get_submit_command('script.sh')

        self.assertTrue('qsub' in sge_get_submit_command)
        self.assertTrue('terse' in sge_get_submit_command)
        self.assertTrue('script.sh' in sge_get_submit_command)

    def test_parse_submit_output(self):
        sge = SgeScheduler()

        # TEST 1:
        sge_parse_submit_output = sge._parse_submit_output(0, ' 1176936', '')
        self.assertTrue('1176936' in sge_parse_submit_output)

        # TEST 2:
        logging.disable(logging.ERROR)
        with self.assertRaisesRegexp(SchedulerError, '^Error during submission, retval=1'):
            sge_parse_submit_output = sge._parse_submit_output(1, '', '')
        logging.disable(logging.NOTSET)

    def test_parse_joblist_output(self):
        sge = SgeScheduler()

        retval = 0
        stdout = text_qstat_ext_urg_xml_test
        stderr = ''

        job_list = sge._parse_joblist_output(retval, stdout, stderr)

        # Is job_list parsed correctly?:
        job_on_cluster = 3
        job_parsed = len(job_list)
        self.assertEquals(job_parsed, job_on_cluster)

        # Check if different job states are realized:
        job_running = 1
        job_running_parsed = len([j for j in job_list if j.job_state \
                                  and j.job_state == JobState.RUNNING])
        self.assertEquals(job_running, job_running_parsed)

        job_held = 1
        job_held_parsed = len([j for j in job_list if j.job_state \
                               and j.job_state == JobState.QUEUED_HELD])
        self.assertEquals(job_held, job_held_parsed)

        job_queued = 1
        job_queued_parsed = len([j for j in job_list if j.job_state \
                                 and j.job_state == JobState.QUEUED])
        self.assertEquals(job_queued, job_queued_parsed)

        # check if job id is recognized:
        running_jobs = ['1212299']
        parsed_running_jobs = [j.job_id for j in job_list if j.job_state \
                               and j.job_state == JobState.RUNNING]
        self.assertEquals(set(running_jobs), set(parsed_running_jobs))

        dispatch_time = [self._parse_time_string('2013-06-18T12:08:23')]
        parsed_dispatch_time = [j.dispatch_time for j in job_list if j.dispatch_time]
        self.assertEquals(set(dispatch_time), set(parsed_dispatch_time))

        submission_times = [
            self._parse_time_string('2013-06-18T12:00:57'),
            self._parse_time_string('2013-06-18T12:09:47')
        ]
        parsed_submission_times = [j.submission_time for j in job_list if j.submission_time]
        self.assertEquals(set(submission_times), set(parsed_submission_times))

        running_jobs = [test_raw_data]
        parsed_running_jobs = [j.raw_data for j in job_list if j.job_state \
                               and j.job_state == JobState.RUNNING]
        self.assertEquals(set(running_jobs), set(parsed_running_jobs))

        # job_list_raise=sge._parse_joblist_output(retval, \
        #                                         text_qstat_ext_urg_xml_test_raise, stderr)
        logging.disable(logging.ERROR)
        stdout = text_xml_parsing_fails_raise
        with self.assertRaises(SchedulerParsingError):
            sge._parse_joblist_output(retval, stdout, stderr)

        stdout = text_check_queue_job_info
        with self.assertRaises(SchedulerError):
            sge._parse_joblist_output(retval, stdout, stderr)

        # Test: Is the except of IndexErrors raised correctly?
        stdout = text_qstat_ext_urg_xml_test_raise
        with self.assertRaises(IndexError):
            sge._parse_joblist_output(retval, stdout, stderr)
        logging.disable(logging.NOTSET)

    def test_submit_script(self):
        from aiida.schedulers.datastructures import JobTemplate

        sge = SgeScheduler()

        job_tmpl = JobTemplate()
        job_tmpl.job_resource = sge.create_job_resource(parallel_env="mpi8", tot_num_mpiprocs=16)
        job_tmpl.working_directory = "/home/users/dorigm7s/test"
        job_tmpl.submit_as_hold = None
        job_tmpl.rerunnable = None
        job_tmpl.email = None
        job_tmpl.email_on_started = None
        job_tmpl.email_on_terminated = None
        job_tmpl.job_name = "BestJobEver"
        job_tmpl.sched_output_path = None
        job_tmpl.sched_join_files = None
        job_tmpl.queue_name = "FavQ.q"
        job_tmpl.priority = None
        job_tmpl.max_wallclock_seconds = "3600"  # "23:59:59"
        job_tmpl.job_environment = {"HOME": "/home/users/dorigm7s/", "WIENROOT": "$HOME:/WIEN2k"}

        submit_script_text = sge._get_submit_script_header(job_tmpl)

        self.assertTrue('#$ -wd /home/users/dorigm7s/test' in submit_script_text)
        self.assertTrue('#$ -N BestJobEver' in submit_script_text)
        self.assertTrue('#$ -q FavQ.q' in submit_script_text)
        self.assertTrue('#$ -l h_rt=01:00:00' in submit_script_text)
        # self.assertTrue( 'export HOME=/home/users/dorigm7s/'
        #                 in submit_script_text )
        self.assertTrue("# ENVIRONMENT VARIABLES BEGIN ###" in submit_script_text)
        self.assertTrue("export HOME='/home/users/dorigm7s/'" in submit_script_text)
        self.assertTrue("export WIENROOT='$HOME:/WIEN2k'" in submit_script_text)

    @staticmethod
    def _parse_time_string(string, fmt='%Y-%m-%dT%H:%M:%S'):
        """
        Parse a time string in the format returned from qstat -xml -ext and
        returns a datetime object.
        Example format: 2013-06-13T11:53:11
        """
        import time
        import datetime

        try:
            time_struct = time.strptime(string, fmt)
        except Exception as exc:
            raise ValueError("Unable to parse time string {}, the message was {}".format(string, exc))

        # I convert from a time_struct to a datetime object going through
        # the seconds since epoch, as suggested on stackoverflow:
        # http://stackoverflow.com/questions/1697815
        return datetime.datetime.fromtimestamp(time.mktime(time_struct))
