# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Plugin for SGE.
This has been tested on GE 6.2u3.

Plugin originally written by Marco Dorigo.
Email: marco(DOT)dorigo(AT)rub(DOT)de
"""
from __future__ import division
import aiida.scheduler
import xml.parsers.expat
from aiida.common.utils import escape_for_bash
from aiida.scheduler import SchedulerError, SchedulerParsingError
from aiida.scheduler.datastructures import (
    JobInfo, job_states, MachineInfo, ParEnvJobResource)

"""
'http://www.loni.ucla.edu/twiki/bin/view/Infrastructure/GridComputing?skin=plain':
Jobs Status:
    'qw' - Queued and waiting,
    'w' - Job waiting,
    's' - Job suspended,
    't' - Job transferring and about to start,
    'r' - Job running,
    'h' - Job hold,
    'R' - Job restarted,
    'd' - Job has been marked for deletion,
    'Eqw' - An error occurred with the job.

'http://confluence.rcs.griffith.edu.au:8080/display/v20zCluster/
Sun+Grid+Engine+SGE+state+letter+symbol+codes+meanings':

Category     State     SGE Letter Code
Pending:     pending     qw
Pending:     pending, user hold     qw
Pending:     pending, system hold     hqw
Pending:     pending, user and system hold     hqw
Pending:     pending, user hold, re-queue     hRwq
Pending:     pending, system hold, re-queue     hRwq
Pending:     pending, user and system hold, re-queue     hRwq
Pending:     pending, user hold     qw
Pending:     pending, user hold     qw
Running     running     r
Running     transferring     t
Running     running, re-submit     Rr
Running     transferring, re-submit     Rt
Suspended     job suspended     s, ts
Suspended     queue suspended     S, tS
Suspended     queue suspended by alarm     T, tT
Suspended     all suspended with re-submit     Rs, Rts, RS, RtS, RT, RtT
Error     all pending states with error     Eqw, Ehqw, EhRqw
Deleted     all running and suspended states with deletion     dr, dt, dRr, dRt, 
                                                               ds, dS, dT, dRs, 
                                                               dRS, dRT
"""




_map_status_sge = {
    'qw'    : job_states.QUEUED,
    'w'     : job_states.QUEUED,
    'hqw'   : job_states.QUEUED_HELD,
    'hRwq'  : job_states.QUEUED_HELD,
    'r'     : job_states.RUNNING,
    't'     : job_states.RUNNING,
    'R'     : job_states.RUNNING,
    'Rr'    : job_states.RUNNING,
    'Rt'    : job_states.RUNNING,
    's'     : job_states.SUSPENDED,
    'st'    : job_states.SUSPENDED,
    'Rs'    : job_states.SUSPENDED,
    'Rts'   : job_states.SUSPENDED,  
    'dr'    : job_states.UNDETERMINED,
    'dt'    : job_states.UNDETERMINED,
    'ds'    : job_states.UNDETERMINED,
    'dRr'   : job_states.UNDETERMINED,
    'dRt'   : job_states.UNDETERMINED,
    'dRs'   : job_states.UNDETERMINED, 
    'Eqw'   : job_states.UNDETERMINED,
    'Ehqw'  : job_states.UNDETERMINED,
    'EhRqw' : job_states.UNDETERMINED
    }

class SgeJobResource(ParEnvJobResource):
    pass

class SgeScheduler(aiida.scheduler.Scheduler):
    """
    Support for the Sun Grid Engine scheduler and its variants/forks (Son of Grid Engine, Oracle Grid Engine, ...) 
    """
    _logger = aiida.scheduler.Scheduler._logger.getChild('sge')
    
    # For SGE, we can have a good qstat xml output by querying by
    # user, but not by job id
    _features = {
        'can_query_by_user': True,
        }
    
    # The class to be used for the job resource.
    _job_resource_class = SgeJobResource
    
    def _get_joblist_command(self,jobs=None,user=None):
        """
        The command to report full information on existing jobs.

        TODO: in the case of job arrays, decide what to do (i.e., if we want
              to pass the -t options to list each subjob).
        
        !!!ALL COPIED FROM PBSPRO!!!
        TODO: understand if it is worth escaping the username, 
        or rather leave it unescaped to allow to pass $USER
        """
        from aiida.common.exceptions import FeatureNotAvailable
        
        if jobs:
            raise FeatureNotAvailable("Cannot query by jobid in SGE")

        command = "qstat -ext -urg -xml "

        if user:
            command += "-u {}".format(str(user))
        else:
            # All users if no user is specified
            command += "-u '*'"
            
        self.logger.debug("qstat command: {}".format(command))
        return command 
        #raise NotImplementedError

    def _get_detailed_jobinfo_command(self,jobid):
        command = "qacct -j {}".format(escape_for_bash(jobid))
        return command

    def _get_submit_script_header(self, job_tmpl):
        """
        Return the submit script header, using the parameters from the
        job_tmpl.

        Args:
           job_tmpl: an JobTemplate instance with relevant parameters set.

        TODO: truncate the title if too long
        """
        import re 
        import string

        

        empty_line = ""
        
        lines = []
        
        # SGE provides flags for wd and cwd
        if job_tmpl.working_directory:
            lines.append('#$ -wd {}'.format(job_tmpl.working_directory))
        else:
            lines.append('#$ -cwd')

        # Enforce bash shell
        lines.append('#$ -S /bin/bash')                 
        
        if job_tmpl.submit_as_hold:
            #if isinstance(job_tmpl.submit_as_hold, str):
            lines.append('#$ -h {}'.format(job_tmpl.submit_as_hold))
            
        if job_tmpl.rerunnable:
            #if isinstance(job_tmpl.rerunnable, str):
            lines.append('#$ -r {}'.format(job_tmpl.rerunnable))
              
        if job_tmpl.email:
            # If not specified, but email events are set, PBSPro
            # sends the mail to the job owner by default
            lines.append('#$ -M {}'.format(job_tmpl.email))
            
        email_events = ""
        if job_tmpl.email_on_started:
            email_events += "b"
        if job_tmpl.email_on_terminated:
            email_events += "ea"
        if email_events:
            lines.append("#$ -m {}".format(email_events))
            if not job_tmpl.email:
                self.logger.info(
                    "Email triggers provided to SGE script for job,"
                    "but no email field set; will send emails to "
                    "the job owner as set in the scheduler")
        else:
            lines.append("#$ -m n")
        
        #From the qsub man page:
        #"The name may be any arbitrary alphanumeric ASCII string, but
        # may  not contain  "\n", "\t", "\r", "/", ":", "@", "\", "*",
        # or "?"."
        if job_tmpl.job_name:
            job_title = re.sub(r'[^a-zA-Z0-9_.-]+', '', job_tmpl.job_name)

            # prepend a 'j' (for 'job') before the string if the string
            # is now empty or does not start with a valid character
            # (the first symbol cannot be digit, at least in some versions
            #  of the scheduler)
            if not job_title or (
                job_title[0] not in string.letters):
                job_title = 'j' + job_title
                
            lines.append('#$ -N {}'.format(job_tmpl.job_name))
        
        if job_tmpl.import_sys_environment:
            lines.append("#$ -V")
            
        if job_tmpl.sched_output_path:
            lines.append("#$ -o {}".format(job_tmpl.sched_output_path))
        
        if job_tmpl.sched_join_files:
            # from qsub man page:
            # 'y': Standard error and standard output are merged  into 
            #       standard output
            # 'n' : Standard error and standard output are not merged (default)
            lines.append("#$ -j y")
            if job_tmpl.sched_error_path:
                self.logger.info(
                    "sched_join_files is True, but sched_error_path is set in "
                    "SGE script; ignoring sched_error_path")
        else:
            if job_tmpl.sched_error_path:
                lines.append("#$ -e {}".format(job_tmpl.sched_error_path))
                
        if job_tmpl.queue_name:
            lines.append("#$ -q {}".format(job_tmpl.queue_name))
            
        if job_tmpl.priority:
            # Priority of the job.  Format: host-dependent integer.  Default:
            # zero.   Range:  [-1023,  +1024].  Sets job's Priority
            # attribute to priority.
            lines.append("#$ -p {}".format(job_tmpl.priority))
        
        if not job_tmpl.job_resource:
            raise ValueError("Job resources (as the tot_num_mpiprocs) are required "
                             "for the SGE scheduler plugin")
        #Setting up the parallel environment
        lines.append('#$ -pe {} {}'.\
                     format(str(job_tmpl.job_resource.parallel_env),\
                            int(job_tmpl.job_resource.tot_num_mpiprocs)))
        
        if job_tmpl.max_wallclock_seconds is not None:
            try:
                tot_secs = int(job_tmpl.max_wallclock_seconds)
                if tot_secs <= 0:
                    raise ValueError
            except ValueError:
                raise ValueError(
                    "max_wallclock_seconds must be "
                    "a positive integer (in seconds)! It is instead '{}'"
                    "".format((job_tmpl.max_wallclock_seconds)))
            hours = tot_secs // 3600
            tot_minutes = tot_secs % 3600
            minutes = tot_minutes // 60
            seconds = tot_minutes % 60
            lines.append("#$ -l h_rt={:02d}:{:02d}:{:02d}".format(
                hours, minutes, seconds))
        
        if job_tmpl.custom_scheduler_commands:
            lines.append(job_tmpl.custom_scheduler_commands)
            
        #TAKEN FROM PBSPRO:  
        # Job environment variables are to be set on one single line. 
        # This is a tough job due to the escaping of commas, etc.
        # moreover, I am having issues making it work.
        # Therefore, I assume that this is bash and export variables by
        # and.
        if job_tmpl.job_environment:
            lines.append(empty_line)
            lines.append("# ENVIRONMENT VARIABLES BEGIN ###")
            if not isinstance(job_tmpl.job_environment, dict):
                raise ValueError("If you provide job_environment, it must be "
                                 "a dictionary")
            for k, v in job_tmpl.job_environment.iteritems():
                lines.append("export {}={}".format(
                        k.strip(),
                        escape_for_bash(v)))
            lines.append("# ENVIRONMENT VARIABLES  END  ###")
            lines.append(empty_line)
            
        return "\n".join(lines)
        
    def _get_submit_command(self, submit_script):
        """
        Return the string to execute to submit a given script.
        
        Args:
            submit_script: the path of the submit script relative to the working
                directory.
                IMPORTANT: submit_script should be already escaped.
        """
        submit_command = 'qsub -terse {}'.format(submit_script)

        self.logger.info("submitting with: " + submit_command)

        return submit_command

    def _parse_joblist_output(self, retval, stdout, stderr):
        import xml.dom.minidom
        
        if retval != 0:
            self.logger.error("Error in _parse_joblist_output: retval={}; "
                "stdout={}; stderr={}".format(retval, stdout, stderr))
            raise SchedulerError("Error during joblist retrieval, retval={}".\
                                 format(retval))

        if stderr.strip():
            self.logger.warning("in _parse_joblist_output for {}: "
                "there was some text in stderr: {}".format(
                    str(self.transport),stderr))
           
        if stdout:
            try:
                xmldata = xml.dom.minidom.parseString(stdout)
            except xml.parsers.expat.ExpatError:
                self.logger.error("in sge._parse_joblist_output: "
                "xml parsing of stdout failed:"
                "{}".format(stdout))
                raise SchedulerParsingError("Error during joblist retrieval,"
                                            "xml parsing of stdout failed")
        else:
            self.logger.error("Error in sge._parse_joblist_output: retval={}; "
                "stdout={}; stderr={}".format(retval, stdout, stderr))
            raise SchedulerError("Error during joblist retrieval,"
                                 "no stdout produced")
        
        try:
            first_child = xmldata.firstChild
            second_childs = first_child.childNodes
            tag_names_sec = [elem.tagName for elem in second_childs \
                             if elem.nodeType == 1]
            if not 'queue_info' in tag_names_sec:
                self.logger.error("Error in sge._parse_joblist_output: "
                                  "no queue_info: {}".\
                                  format(stdout))
                raise SchedulerError
            if not 'job_info' in tag_names_sec:
                self.logger.error("Error in sge._parse_joblist_output: "
                                  "no job_info: {}".\
                                  format(stdout))
                raise SchedulerError
        except SchedulerError:
            self.logger.error("Error in sge._parse_joblist_output: stdout={}"\
                              .format(stdout))
            raise SchedulerError("Error during xml processing, of stdout:"
                                 "There is no 'job_info' or no 'queue_info'"
                                 "element or there are no jobs!")
        #If something weird happens while firstChild, pop, etc:
        except Exception: 
            self.logger.error("Error in sge._parse_joblist_output: stdout={}"\
                              .format(stdout))
            raise SchedulerError("Error during xml processing, of stdout")
            
        jobs = [i for i in first_child.getElementsByTagName('job_list')]
        #jobs = [i for i in jobinfo.getElementsByTagName('job_list')]
        #print [i[0].childNodes[0].data for i in job_numbers if i]
        joblist = []
        for job in jobs:
            this_job = JobInfo()
            
            #In case the user needs more information the xml-data for 
            #each job is stored:
            this_job.raw_data = job.toxml()
            
            try:
                job_element = job.getElementsByTagName('JB_job_number').pop(0)
                element_child = job_element.childNodes.pop(0)
                this_job.job_id = str(element_child.data).strip()
                if not this_job.job_id:
                    raise SchedulerError
            except SchedulerError:
                self.logger.error("Error in sge._parse_joblist_output:"
                                  "no job id is given, stdout={}"\
                                  .format(stdout))
                raise SchedulerError("Error in sge._parse_joblist_output:"
                "no job id is given")
            except IndexError:
                self.logger.error("No 'job_number' given for job index {} in "
                                  "job list, stdout={}".format(jobs.index(job)\
                                  ,stdout))
                raise IndexError("Error in sge._parse_joblist_output:"
                "no job id is given")
            
            try:
                job_element = job.getElementsByTagName('state').pop(0)
                element_child = job_element.childNodes.pop(0)
                job_state_string = str(element_child.data).strip()
                try:
                    this_job.job_state = _map_status_sge[job_state_string]
                except KeyError:
                    self.logger.warning("Unrecognized job_state '{}' for job "
                                        "id {}".format(job_state_string,
                                                       this_job.job_id))
                    this_job.job_state = job_states.UNDETERMINED
            except IndexError:
                self.logger.warning("No 'job_state' field for job id {} in" 
                                  "stdout={}".format(this_job.job_id,stdout))
                this_job.job_state = job_states.UNDETERMINED
            
            try:
                job_element = job.getElementsByTagName('JB_owner').pop(0)
                element_child = job_element.childNodes.pop(0)
                this_job.job_owner = str(element_child.data).strip()
            except IndexError:
                self.logger.warning("No 'job_owner' field for job "
                                  "id {}".format(this_job.job_id))
            
            try:
                job_element = job.getElementsByTagName('JB_name').pop(0)
                element_child = job_element.childNodes.pop(0)
                this_job.title = str(element_child.data).strip()
            except IndexError:
                self.logger.warning("No 'title' field for job "
                                  "id {}".format(this_job.job_id))
             
            try:
                job_element = job.getElementsByTagName('queue_name').pop(0)
                element_child = job_element.childNodes.pop(0)
                this_job.queue_name = str(element_child.data).strip()
            except IndexError:
                if this_job.job_state == job_states.RUNNING:
                    self.logger.warning("No 'queue_name' field for job "
                                        "id {}".format(this_job.job_id))
            
            try:
                job_element = job.getElementsByTagName('JB_submission_time').pop(0)
                element_child = job_element.childNodes.pop(0)
                time_string = str(element_child.data).strip()
                try:
                    this_job.submission_time = self._parse_time_string(
                       time_string)
                except ValueError:
                    self.logger.warning("Error parsing 'JB_submission_time' "
                        "for job id {} ('{}')".format(this_job.job_id,
                                                      time_string)) 
            except IndexError:
                try:
                    job_element = job.getElementsByTagName('JAT_start_time').pop(0)
                    element_child = job_element.childNodes.pop(0)
                    time_string = str(element_child.data).strip()
                    try:
                        this_job.dispatch_time = self._parse_time_string(
                                                            time_string)
                    except ValueError:
                        self.logger.warning("Error parsing 'JAT_start_time'"
                        "for job id {} ('{}')".format(this_job.job_id,
                                                      time_string))
                except IndexError:
                    self.logger.warning("No 'JB_submission_time' and no "
                                        "'JAT_start_time' field for job "
                                        "id {}".format(this_job.job_id))
                
            #There is also cpu_usage, mem_usage, io_usage information available:
            if this_job.job_state == job_states.RUNNING:
                try:
                    job_element = job.getElementsByTagName('slots').pop(0)
                    element_child = job_element.childNodes.pop(0)
                    this_job.num_mpiprocs = str(element_child.data).strip()
                except IndexError:
                    self.logger.warning("No 'slots' field for job "
                                  "id {}".format(this_job.job_id))
                
            joblist.append(this_job)
        #self.logger.debug("joblist final: {}".format(joblist))
        return joblist

    def _parse_submit_output(self, retval, stdout, stderr):
        """
        Parse the output of the submit command, as returned by executing the
        command returned by _get_submit_command command.
        
        To be implemented by the plugin.
        
        Return a string with the JobID.
        """
        import re
        
        if retval != 0:
            self.logger.error("Error in _parse_submit_output: retval={}; "
                "stdout={}; stderr={}".format(retval, stdout, stderr))
            raise SchedulerError("Error during submission, retval={}\n"
                                 "stdout={}\nstderr={}".format(
                retval, stdout, stderr))

        if stderr.strip():
            self.logger.warning("in _parse_submit_output for {}: "
                "there was some text in stderr: {}".format(
                    str(self.transport),stderr))
        
        return stdout.strip()

    def _parse_time_string(self,string,fmt='%Y-%m-%dT%H:%M:%S'):
        """
        Parse a time string in the format returned from qstat -xml -ext and
        returns a datetime object.
        Example format: 2013-06-13T11:53:11
        """
        import time, datetime

        try:
            time_struct = time.strptime(string,fmt)
        except Exception as e:
            self.logger.debug("Unable to parse time string {}, the message "
                "was {}".format(string, e.message))
            raise ValueError("Problem parsing the time string.")

        # I convert from a time_struct to a datetime object going through
        # the seconds since epoch, as suggested on stackoverflow:
        # http://stackoverflow.com/questions/1697815
        return datetime.datetime.fromtimestamp(time.mktime(time_struct))

    def _get_kill_command(self, jobid):
        """
        Return the command to kill the job with specified jobid.
        """
        submit_command = 'qdel {}'.format(jobid)

        self.logger.info("killing job {}".format(jobid))

        return submit_command

    def _parse_kill_output(self, retval, stdout, stderr):
        """
        Parse the output of the kill command.

        To be implemented by the plugin.

        :return: True if everything seems ok, False otherwise.
        """
        if retval != 0:
            self.logger.error("Error in _parse_kill_output: retval={}; "
                              "stdout={}; stderr={}".format(retval, stdout, stderr))
            return False

        if stderr.strip():
            self.logger.warning("in _parse_kill_output for {}: "
                                "there was some text in stderr: {}".format(
                str(self.transport), stderr))

        if stdout.strip():
            self.logger.info("in _parse_kill_output for {}: "
                                "there was some text in stdout: {}".format(
                str(self.transport), stdout))

        return True
