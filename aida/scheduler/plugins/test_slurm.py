import sys
import unittest
import logging
import uuid
import datetime

from aida.scheduler.plugins.slurm import *
from aida.common import aidalogger
aidalogger.addHandler(logging.StreamHandler(sys.stderr))

text_squeue_to_test = """862540^^^PD^^^Dependency^^^n/a^^^user1^^^20^^^640^^^(Dependency)^^^normal^^^1-00:00:00^^^0:00^^^N/A^^^longsqw_L24_q_10_0
863100^^^PD^^^Resources^^^n/a^^^user2^^^32^^^1024^^^(Resources)^^^normal^^^10:00^^^0:00^^^2013-05-23T14:44:44^^^eq_solve_e4.slm
863546^^^PD^^^Priority^^^n/a^^^user3^^^2^^^64^^^(Priority)^^^normal^^^8:00:00^^^0:00^^^2013-05-23T14:44:44^^^S2-H2O
863313^^^PD^^^JobHeldUser^^^n/a^^^user4^^^1^^^1^^^(JobHeldUser)^^^normal^^^1:00:00^^^0:00^^^N/A^^^test
862538^^^R^^^None^^^rosa10^^^user5^^^20^^^640^^^nid0[0099,0156-0157,0162-0163,0772-0773,0826,0964-0965,1018-1019,1152-1153,1214-1217,1344-1345]^^^normal^^^1-00:00:00^^^32:10^^^2013-05-23T11:41:30^^^longsqw_L24_q_11_0
861352^^^R^^^None^^^rosa11^^^user6^^^4^^^128^^^nid00[192,246,264-265]^^^normal^^^1-00:00:00^^^23:30:20^^^2013-05-22T12:43:20^^^Pressure_PBEsol_0
863553^^^R^^^None^^^rosa1^^^user5^^^1^^^32^^^nid00471^^^normal^^^30:00^^^29:29^^^2013-05-23T11:44:11^^^bash
"""

class TestParserSqueue(unittest.TestCase):
    """
    Tests to verify if teh function _parse_joblist_output behave correctly
    The tests is done parsing a string defined above, to be used offline
    """
    
    def test_parse_common_joblist_output(self):
        """
        Test whether _parse_joblist can parse the qstat -f output
        """
        s = SlurmScheduler()
        
        retval = 0
        stdout = text_squeue_to_test
        stderr = ''
        
        job_list = s._parse_joblist_output(retval, stdout, stderr)

        # The parameters are hard coded in the text to parse
        job_on_cluster = 7
        job_parsed = len(job_list)
        self.assertEquals(job_parsed, job_on_cluster)

        job_running = 3
        job_running_parsed = len([ j for j in job_list if j.jobState \
                                   and j.jobState == jobStates.RUNNING ])
        self.assertEquals(job_running,job_running_parsed)

        job_held = 2
        job_held_parsed = len([ j for j in job_list if j.jobState 
                                   and j.jobState == jobStates.QUEUED_HELD ])
        self.assertEquals(job_held,job_held_parsed)

        job_queued = 2
        job_queued_parsed = len([ j for j in job_list if j.jobState 
                                   and j.jobState == jobStates.QUEUED ])
        self.assertEquals(job_queued,job_queued_parsed)

        running_users = ['user5','user6']
        parsed_running_users = [ j.jobOwner for j in job_list if j.jobState 
                                 and j.jobState == jobStates.RUNNING ]
        self.assertEquals( set(running_users) , set(parsed_running_users) )

        running_jobs = ['862538','861352', '863553']
        parsed_running_jobs = [ j.jobId for j in job_list if j.jobState 
                                 and j.jobState == jobStates.RUNNING ]
        self.assertEquals( set(running_jobs) , set(parsed_running_jobs) )
 
        self.assertEquals( [j.requestedWallclockTime for j in job_list
                            if j.jobId == '863553'][0], 
                           30*60 )
        self.assertEquals( [j.wallclockTime for j in job_list
                            if j.jobId == '863553'][0], 
                           29*60 + 29 )
        self.assertEquals( [j.submissionTime for j in job_list
                            if j.jobId == '863553'][0], 
                           datetime.datetime(2013,05,23,11,44,11) )
        self.assertEquals( [j.annotation for j in job_list
                            if j.jobId == '863100'][0], 
                           'Resources' )
        self.assertEquals( [j.num_nodes for j in job_list
                            if j.jobId == '863100'][0], 
                           32 )
        self.assertEquals( [j.numCores for j in job_list
                            if j.jobId == '863100'][0], 
                           1024 )
        self.assertEquals( [j.queue_name for j in job_list
                            if j.jobId == '863100'][0], 
                           'normal' )
        self.assertEquals( [j.title for j in job_list
                            if j.jobId == '861352'][0], 
                           'Pressure_PBEsol_0' )

        # allocatedNodes is not implemented in this version of the plugin       
        #        for j in job_list:
        #            if j.allocatedNodes:
        #                num_nodes = 0
        #                num_cores = 0
        #                for n in j.allocatedNodes:
        #                    num_nodes += 1
        #                    num_cores += n.numCores
        #                    
        #                self.assertTrue( j.num_nodes==num_nodes )
        #                self.assertTrue( j.numCores==num_cores )

class TestTimes(unittest.TestCase):
    def test_time_conversion(self):
        """
        Test conversion of (relative) times.
        
        From docs,
        acceptable  time  formats include 
        "minutes",  "minutes:seconds",  "hours:minutes:seconds", 
        "days-hours",  "days-hours:minutes" and "days-hours:minutes:seconds".
        """
        s = SlurmScheduler()
        self.assertEquals(s._convert_time("2"), 2*60)
        self.assertEquals(s._convert_time("02"), 2*60)
        
        self.assertEquals(s._convert_time("02:3"), 2*60+3)
        self.assertEquals(s._convert_time("02:03"), 2*60+3)

        self.assertEquals(s._convert_time("1:02:03"), 3600+2*60+3)
        self.assertEquals(s._convert_time("01:02:03"), 3600+2*60+3)

        self.assertEquals(s._convert_time("1-3"), 86400 + 3*3600)
        self.assertEquals(s._convert_time("01-3"), 86400 + 3*3600)
        self.assertEquals(s._convert_time("01-03"), 86400 + 3*3600)

        self.assertEquals(s._convert_time("1-3:5"), 86400 + 3*3600 + 5*60)
        self.assertEquals(s._convert_time("01-3:05"), 86400 + 3*3600 + 5*60)
        self.assertEquals(s._convert_time("01-03:05"), 86400 + 3*3600 + 5*60)

        self.assertEquals(s._convert_time("1-3:5:7"), 
                          86400 + 3*3600 + 5*60 + 7)
        self.assertEquals(s._convert_time("01-3:05:7"), 
                          86400 + 3*3600 + 5*60 + 7)
        self.assertEquals(s._convert_time("01-03:05:07"), 
                          86400 + 3*3600 + 5*60 + 7)

        # Disable logging to avoid excessive output during test
        logging.disable(logging.ERROR)
        with self.assertRaises(ValueError):
            # Empty string not valid
            s._convert_time("")
        with self.assertRaises(ValueError):
            # there should be something after the dash
            s._convert_time("1-")
        with self.assertRaises(ValueError):
            # there should be something after the dash
            # there cannot be a dash after the colons
            s._convert_time("1:2-3")
        # Reset logging level
        logging.disable(logging.NOTSET)


class TestSubmitScript(unittest.TestCase):
    def test_submit_script(self):
        """
        Test the creation of a simple submission script.
        """
        from aida.scheduler.datastructures import JobTemplate
        s = SlurmScheduler()

        job_tmpl = JobTemplate()
        job_tmpl.argv = ["mpirun", "-np", "23", "pw.x", "-npool", "1"]
        job_tmpl.stdin_name = 'aida.in'
        job_tmpl.num_nodes = 1
        job_tmpl.uuid = str(uuid.uuid4())
        job_tmpl.max_wallclock_seconds = 24 * 3600 

        submit_script_text = s.get_submit_script(job_tmpl)

        self.assertTrue( submit_script_text.startswith('#!/bin/bash') )

        self.assertTrue( '#SBATCH --no-requeue' in submit_script_text )
        self.assertTrue( '#SBATCH --time=1-00:00:00' in submit_script_text )
        self.assertTrue( '#SBATCH --nodes=1' in submit_script_text )

        self.assertTrue( "'mpirun' '-np' '23' 'pw.x' '-npool' '1'" + \
                         " < 'aida.in'" in submit_script_text )

if __name__ == '__main__':        
    unittest.main()
