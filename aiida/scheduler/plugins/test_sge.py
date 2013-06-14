from aiida.scheduler.plugins.sge import *
import unittest
import logging
import uuid

from aiida.common import aiidalogger

aiidalogger.setLevel(logging.DEBUG)

text_qstat_ext_urg_xml_test="""<?xml version='1.0'?>
<job_info  xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <queue_info>
  </queue_info>
  <job_info>
    <job_list state="running">
      <JB_job_number>1177697</JB_job_number>
      <JAT_prio>0.05435</JAT_prio>
      <JAT_ntix>0.00043</JAT_ntix>
      <JB_nurg>0.32632</JB_nurg>
      <JB_urg>32000</JB_urg>
      <JB_rrcontr>32000</JB_rrcontr>
      <JB_wtcontr>0</JB_wtcontr>
      <JB_dlcontr>0</JB_dlcontr>
      <JB_name>Heusler</JB_name>
      <JB_owner>dorigm7s</JB_owner>
      <JB_project>ams.p</JB_project>
      <JB_department>defaultdepartment</JB_department>
      <state>r</state>
      <JB_submission_time>2013-06-13T11:27:08</JB_submission_time>
      <tickets>176</tickets>
      <JB_override_tickets>0</JB_override_tickets>
      <JB_jobshare>0</JB_jobshare>
      <otickets>0</otickets>
      <ftickets>0</ftickets>
      <stickets>176</stickets>
      <JAT_share>0.00067</JAT_share>
      <queue_name></queue_name>
      <slots>32</slots>
    </job_list>
    <job_list state="hold"> 
      <JB_job_number>1177893</JB_job_number>
      <JAT_prio>0.05433</JAT_prio>
      <JAT_ntix>0.00043</JAT_ntix>
      <JB_nurg>0.32632</JB_nurg>
      <JB_urg>32000</JB_urg>
      <JB_rrcontr>32000</JB_rrcontr>
      <JB_wtcontr>0</JB_wtcontr>
      <JB_dlcontr>0</JB_dlcontr>
      <JB_name>Heusler</JB_name>
      <JB_owner>dorigm7s</JB_owner>
      <JB_project>ams.p</JB_project>
      <JB_department>defaultdepartment</JB_department>
      <state>h</state>
      <JB_submission_time>2013-06-13T11:53:11</JB_submission_time>
      <tickets>176</tickets>
      <JB_override_tickets>0</JB_override_tickets>
      <JB_jobshare>0</JB_jobshare>
      <otickets>0</otickets>
      <ftickets>0</ftickets>
      <stickets>176</stickets>
      <JAT_share>0.00067</JAT_share>
      <queue_name></queue_name>
      <slots>32</slots>
    </job_list>
    <job_list state="pending">
      <JB_job_number>1177902</JB_job_number>
      <JAT_prio>0.05431</JAT_prio>
      <JAT_ntix>0.00043</JAT_ntix>
      <JB_nurg>0.32632</JB_nurg>
      <JB_urg>32000</JB_urg>
      <JB_rrcontr>32000</JB_rrcontr>
      <JB_wtcontr>0</JB_wtcontr>
      <JB_dlcontr>0</JB_dlcontr>
      <JB_name>Heusler</JB_name>
      <JB_owner>dorigm7s</JB_owner>
      <JB_project>ams.p</JB_project>
      <JB_department>defaultdepartment</JB_department>
      <state>qw</state>
      <JB_submission_time>2013-06-13T11:55:29</JB_submission_time>
      <tickets>175</tickets>
      <JB_override_tickets>0</JB_override_tickets>
      <JB_jobshare>0</JB_jobshare>
      <otickets>0</otickets>
      <ftickets>0</ftickets>
      <stickets>175</stickets>
      <JAT_share>0.00067</JAT_share>
      <queue_name></queue_name>
      <slots>32</slots>
    </job_list>
  </job_info>
</job_info>
"""

text_qstat_ext_urg_xml_test_raise="""<?xml version='1.0'?>
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
        
text_xml_parsing_fails_raise="""<?xml version='1.0'?>
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

class TestCommand(unittest.TestCase):
    """
    def test_get_joblist_command_str(self):
        sge=SgeScheduler()  
    
        sge_get_joblist_command=sge._get_joblist_command(jobs='123456,789456')

        self.assertTrue('123456' in sge_get_joblist_command)
        self.assertTrue('789456' in sge_get_joblist_command)
        self.assertTrue('qstat' in sge_get_joblist_command)
        self.assertTrue('-xml' in sge_get_joblist_command)
        self.assertTrue('-ext' in sge_get_joblist_command)
    
    def test_get_joblist_command_list(self):
        sge=SgeScheduler()  
    
        sge_get_joblist_command=sge._get_joblist_command(jobs=['123456','789456'])
                
        self.assertTrue('123456' in sge_get_joblist_command)
        self.assertTrue('789456' in sge_get_joblist_command)
        self.assertTrue('qstat' in sge_get_joblist_command)
        self.assertTrue('-xml' in sge_get_joblist_command)
        self.assertTrue('-ext' in sge_get_joblist_command)
    """    
    def test_get_joblist_command(self):
        sge=SgeScheduler()  
        
        #TEST 1:
        sge_get_joblist_command=sge._get_joblist_command(user='ExamplUsr')
                
        self.assertTrue('qstat' in sge_get_joblist_command)
        self.assertTrue('-xml' in sge_get_joblist_command)
        self.assertTrue('-ext' in sge_get_joblist_command)
        self.assertTrue('-u' in sge_get_joblist_command)
        #self.assertTrue('-urg' in sge_get_joblist_command)
        self.assertTrue('ExamplUsr' in sge_get_joblist_command)
        
        #TEST 2:
        sge_get_joblist_command=sge._get_joblist_command()
        
        self.assertTrue('qstat' in sge_get_joblist_command)
        self.assertTrue('-xml' in sge_get_joblist_command)
        self.assertTrue('-ext' in sge_get_joblist_command)
        self.assertTrue('-u' in sge_get_joblist_command)
        #self.assertTrue('-urg' in sge_get_joblist_command)
        self.assertTrue('*' in sge_get_joblist_command)

    def test_detailed_jobinfo_command(self):
        sge=SgeScheduler()  
    
        sge_get_djobinfo_command=sge._get_detailed_jobinfo_command('123456')

        self.assertTrue('123456' in sge_get_djobinfo_command)
        self.assertTrue('qacct' in sge_get_djobinfo_command)
        self.assertTrue('-j' in sge_get_djobinfo_command)
        
    def test_get_submit_command(self):
        sge=SgeScheduler()  
    
        sge_get_submit_command=sge._get_submit_command('script.sh')

        self.assertTrue('qsub' in sge_get_submit_command)
        self.assertTrue('terse' in sge_get_submit_command)
        self.assertTrue('script.sh' in sge_get_submit_command)
        
    def test_parse_submit_output(self):
        sge=SgeScheduler()
        
        #TEST 1:
        sge_parse_submit_output=sge._parse_submit_output(0,' 1176936','')
        self.assertTrue('1176936' in sge_parse_submit_output)#176936
        
        #TEST 2:
        with self.assertRaises(SchedulerError) as e:
            sge_parse_submit_output=sge._parse_submit_output(1,'','')
        
        self.assertEqual(e.exception.message, 'Error during submission, retval=1')
        
    def test_parse_joblist_output(self):
        sge=SgeScheduler()
        
        retval = 0
        stdout = text_qstat_ext_urg_xml_test
        stderr = ''
        
        job_list = sge._parse_joblist_output(retval, stdout, stderr)
        
        #Is job_list parsed correctly?:
        job_on_cluster = 3
        job_parsed = len(job_list)
        self.assertEquals(job_parsed, job_on_cluster)
        
        #Check if different job states are realized:
        job_running = 1
        job_running_parsed = len([ j for j in job_list if j.job_state \
                                   and j.job_state == job_states.RUNNING ])
        self.assertEquals(job_running,job_running_parsed)
        
        job_held = 1
        job_held_parsed = len([ j for j in job_list if j.job_state \
                                   and j.job_state == job_states.QUEUED_HELD ])
        self.assertEquals(job_held,job_held_parsed)

        job_queued = 1
        job_queued_parsed = len([ j for j in job_list if j.job_state \
                                   and j.job_state == job_states.QUEUED ])
        self.assertEquals(job_queued,job_queued_parsed)
        
        #check if job id is recognized:
        running_jobs = ['1177697']
        parsed_running_jobs = [ j.job_id for j in job_list if j.job_state \
                                 and j.job_state == job_states.RUNNING ]
        self.assertEquals( set(running_jobs) , set(parsed_running_jobs) )
        
        submission_times = ['2013-06-13T11:55:29', '2013-06-13T11:53:11', \
                            '2013-06-13T11:27:08']
        parsed_submission_times = [j.submission_time for j in job_list]
        self.assertEquals( set(submission_times) , set(parsed_submission_times) )
        
        #job_list_raise=sge._parse_joblist_output(retval, \
        #                                         text_qstat_ext_urg_xml_test_raise, stderr)
        logging.disable(logging.ERROR)
        stdout=text_xml_parsing_fails_raise
        with self.assertRaises(SchedulerParsingError) as e:
            job_list_raise=sge._parse_joblist_output(retval, stdout, stderr)
        
        #Test: Is the except of IndexErrors raised correctly?
        stdout = text_qstat_ext_urg_xml_test_raise
        with self.assertRaises(IndexError) as e:
            job_list_raise=sge._parse_joblist_output(retval, stdout, stderr)
        logging.disable(logging.NOTSET)
            

        
        
        
        
        
        