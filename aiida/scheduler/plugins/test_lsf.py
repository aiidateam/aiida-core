# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import sys
import unittest
import logging
import uuid
import datetime

from aiida.scheduler import SchedulerError

from aiida.scheduler.plugins.lsf import *
#from aiida.common import aiidalogger
#aiidalogger.addHandler(logging.StreamHandler(sys.stderr))

bjobs_stdout_to_test = "764213236|EXIT|TERM_RUNLIMIT: job killed after reaching LSF run time limit|b681e480bd|inewton|1|-|b681e480bd|test|Feb  2 00:46|Feb  2 00:45|-|Feb  2 00:44|aiida-1033269\n" \
                       "764220165|PEND|-|-|inewton|-|-|-|8nm|-|-|-|Feb  2 01:46|aiida-1033444\n" \
                       "764220167|PEND|-|-|fchopin|-|-|-|test|-|-|-|Feb  2 01:53 L|aiida-1033449\n" \
                       "764254593|RUN|-|lxbsu2710|inewton|1|-|lxbsu2710|test|Feb  2 07:40|Feb  2 07:39|-|Feb  2 07:39|test\n" \
                       "764255172|RUN|-|b68ac74822|inewton|1|-|b68ac74822|test|Feb  2 07:48 L|Feb  2 07:47|15.00% L|Feb  2 07:47|test\n" \
                       "764245175|RUN|-|b68ac74822|dbowie|1|-|b68ac74822|test|Jan  1 05:07|Dec  31 23:48 L|25.00%|Dec  31 23:40|test\n" \
                       "764399747|DONE|-|p05496706j68144|inewton|1|-|p05496706j68144|test|Feb  2 14:56 L|Feb  2 14:54|38.33% L|Feb  2 14:54|test"
bjobs_stderr_to_test = "Job <864220165> is not found"

submit_stdout_to_test = "Job <764254593> is submitted to queue <test>."
bkill_stdout_to_test = "Job <764254593> is being terminated"



class TestParserBjobs(unittest.TestCase):
    """
    Tests to verify if the function _parse_joblist_output behave correctly
    The tests is done parsing a string defined above, to be used offline
    """
    
    def test_parse_common_joblist_output(self):
        """
        Test whether _parse_joblist can parse the bjobs output
        """
        import datetime
        s = LsfScheduler()
        
        # Disable logging to avoid excessive output during test
        logging.disable(logging.ERROR)
        
        retval = 255
        stdout = bjobs_stdout_to_test
        stderr = bjobs_stderr_to_test
        
        with self.assertRaises(SchedulerError):
            job_list = s._parse_joblist_output(retval, stdout, stderr)

        retval = 0
        stdout = bjobs_stdout_to_test
        stderr = ""
        job_list = s._parse_joblist_output(retval, stdout, stderr)

        # The parameters are hard coded in the text to parse
        job_on_cluster = 7
        job_parsed = len(job_list)
        self.assertEquals(job_parsed, job_on_cluster)

        job_queued = 2
        job_queue_name = ['8nm','test']
        job_queued_parsed = len([ j for j in job_list if j.job_state 
                                   and j.job_state == job_states.QUEUED ])
        job_queue_name_parsed = [ j.queue_name for j in job_list if j.job_state 
                                   and j.job_state == job_states.QUEUED ]
        self.assertEquals(job_queued,job_queued_parsed)
        self.assertEquals(job_queue_name,job_queue_name_parsed)

        job_done = 2
        job_done_title = ['aiida-1033269','test']
        job_done_annotation = ['TERM_RUNLIMIT: job killed after reaching LSF run time limit',
                               '-']
        job_done_parsed = len([ j for j in job_list if j.job_state 
                                   and j.job_state == job_states.DONE ])
        job_done_title_parsed = [ j.title for j in job_list if j.job_state 
                                   and j.job_state == job_states.DONE ]
        job_done_annotation_parsed = [ j.annotation for j in job_list if j.job_state 
                                   and j.job_state == job_states.DONE ]
        self.assertEquals(job_done,job_done_parsed)
        self.assertEquals(job_done_title,job_done_title_parsed)
        self.assertEquals(job_done_annotation,job_done_annotation_parsed)

        job_running = 3
        job_running_parsed = len([ j for j in job_list if j.job_state \
                                   and j.job_state == job_states.RUNNING ])
        self.assertEquals(job_running,job_running_parsed)

        running_users = ['inewton','inewton','dbowie']
        parsed_running_users = [ j.job_owner for j in job_list if j.job_state 
                                 and j.job_state == job_states.RUNNING ]
        self.assertEquals( running_users , parsed_running_users )

        running_jobs = ['764254593','764255172','764245175']
        num_machines = [1, 1, 1]
        allocated_machines = ['lxbsu2710', 'b68ac74822', 'b68ac74822']
        parsed_running_jobs = [ j.job_id for j in job_list if j.job_state 
                                 and j.job_state == job_states.RUNNING ]
        parsed_num_machines = [ j.num_machines for j in job_list if j.job_state 
                                 and j.job_state == job_states.RUNNING ]
        parsed_allocated_machines = [ j.allocated_machines_raw for j in job_list if j.job_state 
                                 and j.job_state == job_states.RUNNING ]
        self.assertEquals( running_jobs , parsed_running_jobs )
        self.assertEquals( num_machines , parsed_num_machines )
        self.assertEquals( allocated_machines , parsed_allocated_machines )
 
        self.assertEquals( [j.requested_wallclock_time_seconds for j in job_list
                            if j.job_id == '764254593'][0], 
                           60 )
        self.assertEquals( [j.wallclock_time_seconds for j in job_list
                            if j.job_id == '764255172'][0], 
                           9 )
        self.assertEquals( [j.wallclock_time_seconds for j in job_list
                            if j.job_id == '764245175'][0], 
                           4785 )
        current_year = datetime.datetime.now().year
        self.assertEquals( [j.submission_time for j in job_list
                            if j.job_id == '764245175'][0], 
                           datetime.datetime(current_year, 12, 31, 23, 40) )

        # Important to enable again logs!
        logging.disable(logging.NOTSET)


class TestSubmitScript(unittest.TestCase):
    
    def test_submit_script(self):
        """
        Test the creation of a simple submission script.
        """
        from aiida.scheduler.datastructures import JobTemplate
        from aiida.common.datastructures import CodeInfo, code_run_modes

        s = LsfScheduler()

        job_tmpl = JobTemplate()
        job_tmpl.uuid = str(uuid.uuid4())
        job_tmpl.job_resource = s.create_job_resource(tot_num_mpiprocs=2,
                                                      parallel_env='b681e480bd.cern.ch')
        job_tmpl.max_wallclock_seconds = 24 * 3600 
        code_info = CodeInfo()
        code_info.cmdline_params = ["mpirun", "-np", "2", "pw.x", "-npool", "1"]
        code_info.stdin_name = 'aiida.in'
        job_tmpl.codes_info = [code_info]
        job_tmpl.codes_run_mode = code_run_modes.SERIAL

        submit_script_text = s.get_submit_script(job_tmpl)

        self.assertTrue( submit_script_text.startswith('#!/bin/bash') )

        self.assertTrue( '#BSUB -rn' in submit_script_text )
        self.assertTrue( '#BSUB -W 24:00' in submit_script_text )
        self.assertTrue( '#BSUB -n 2' in submit_script_text )

        self.assertTrue( "'mpirun' '-np' '2' 'pw.x' '-npool' '1'" + \
                         " < 'aiida.in'" in submit_script_text )

    def test_submit_script_with_num_machines(self):
        """
        Test to verify that script fails if we specify only
        num_machines.
        """
        from aiida.scheduler.datastructures import JobTemplate
        from aiida.common.datastructures import CodeInfo, code_run_modes
        
        s = LsfScheduler()
        job_tmpl = JobTemplate()
        with self.assertRaises(TypeError):
            job_tmpl.job_resource = s.create_job_resource(
                num_machines=1,
                num_mpiprocs_per_machine=1,
            )

 
class TestParserSubmit(unittest.TestCase):
    
    def test_submit_output(self):
        """
        Test the parsing of the output of the submission command
        """
        s = LsfScheduler()
        retval = 0
        stdout = submit_stdout_to_test
        stderr = ''
        
        self.assertEquals( s._parse_submit_output(retval, stdout, stderr),
                           '764254593' )


class TestParserBkill(unittest.TestCase):
    
    def test_kill_output(self):
        """
        Test the parsing of the output of the submission command
        """
        s = LsfScheduler()
        retval = 0
        stdout = bkill_stdout_to_test
        stderr = ''
        
        self.assertTrue( s._parse_kill_output(retval, stdout, stderr) )


if __name__ == '__main__':        
    unittest.main()
