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
Plugin for SLURM.
This has been tested on SLURM 14.03.7 on the CSCS.ch machines.
"""
from __future__ import division
import re

import aiida.scheduler
from aiida.common.utils import escape_for_bash
from aiida.scheduler import SchedulerError
from aiida.scheduler.datastructures import (
    JobInfo, job_states, NodeNumberJobResource)


# This maps SLURM state codes to our own status list

## List of states from the man page of squeue
## CA  CANCELLED       Job  was explicitly cancelled by the user or system
##                     administrator.  The job may or may  not  have  been
##                     initiated.
## CD  COMPLETED       Job has terminated all processes on all nodes.
## CF  CONFIGURING     Job  has  been allocated resources, but are waiting
##                     for them to become ready for use (e.g. booting).
## CG  COMPLETING      Job is in the process of completing. Some processes
##                     on some nodes may still be active.
## F   FAILED          Job  terminated  with  non-zero  exit code or other
##                     failure condition.
## NF  NODE_FAIL       Job terminated due to failure of one or more  allo-
##                     cated nodes.
## PD  PENDING         Job is awaiting resource allocation.
## PR  PREEMPTED       Job terminated due to preemption.
## R   RUNNING         Job currently has an allocation.
## S   SUSPENDED       Job  has an allocation, but execution has been sus-
##                     pended.
## TO  TIMEOUT         Job terminated upon reaching its time limit.


_map_status_slurm = {
    'CA': job_states.DONE,
    'CD': job_states.DONE,
    'CF': job_states.QUEUED,
    'CG': job_states.RUNNING,
    'F':  job_states.DONE,
    'NF': job_states.DONE,
    'PD': job_states.QUEUED,
    'PR': job_states.DONE,
    'R': job_states.RUNNING,
    'S': job_states.SUSPENDED,
    'TO': job_states.DONE,
    }

# From the manual,
# possible lines are:
# salloc: Granted job allocation 65537
# sbatch: Submitted batch job 65541
# and in practice, often the part before the colon can be absent.
_slurm_submitted_regexp = re.compile(
    r'(.*:\s*)?([Gg]ranted job allocation|[Ss]ubmitted batch job)\s+(?P<jobid>\d+)')

# From docs,
# acceptable  time  formats include 
# "minutes",  "minutes:seconds",  "hours:minutes:seconds", 
# "days-hours",  "days-hours:minutes" and "days-hours:minutes:seconds".
_time_regexp = re.compile(
    r"""
    ^                            # beginning of string
    \s*                          # any number of white spaces
    (?=\d)                       # I check that there is at least a digit
                                 # in the string, without consuming it
    ((?P<days>\d+)(?P<dash>-)    # the number of days, if a dash is present,
                                 # composed by any number of digits;
                                 # may be absent
     (?=\d))?                    # in any case, I check that there is at least
                                 # a digit afterwards, without consuming it
    ((?P<hours>\d{1,2})          # match an hour (one or two digits)
     (?(dash)                    # check if the dash was found
       |                         # match nothing if the dash was found: 
                                 # if the dash was found, we are sure that 
                                 # the first number is a hour
       (?=:\d{1,2}:\d{1,2})))?   # if no dash was found, the first
                                 # element found is an hour only if
                                 # it is followed by two more fields (mm:ss)
       (?P<firstcolon>:)?        # there (can) possibly be a further colon,
                                 # consume it
    ((?<!-)(?P<minutes>\d{1,2})
     (:(?P<seconds>\d{1,2}))?)?  # number of minutes (one or two digits)
                                 # and seconds. A number only means minutes.
                                 # (?<!-) means that the location BEFORE
                                 # the current position does NOT
                                 # match a dash, because the string 1-2 
                                 # means 1 day and 2 hours, NOT one day and
                                 # 2 minutes
    \s*                          # any number of whitespaces
    $                            # end of line
   """, re.VERBOSE)

# Separator between fields in the output of squeue
_field_separator = "^^^"

class SlurmJobResource(NodeNumberJobResource):
    def __init__(self, *args, **kwargs):
        """
        It extends the base class init method and calculates the 
        num_cores_per_mpiproc fields to pass to Slurm schedulers.
        
        * Check: num_cores_per_machine should be a multiple of
        num_cores_per_mpiproc and/or num_mpiprocs_per_machine 
        
        * Check sequence:
        1. If num_cores_per_mpiproc and num_cores_per_machine both are 
        specified check whether it satisfies the check
        2. If only num_cores_per_machine is passed, calculate 
        num_cores_per_mpiproc which should always be an integer value
        3. If only num_cores_per_mpiproc is passed, use it
        """
        super(SlurmJobResource, self).__init__(*args, **kwargs)

        value_error = ("num_cores_per_machine must be equal to "
                      "num_cores_per_mpiproc * num_mpiprocs_per_machine, "
                      "and in perticular it should be a multiple of "
                      "num_cores_per_mpiproc and/or num_mpiprocs_per_machine")

        if (self.num_cores_per_machine is not None and
                self.num_cores_per_mpiproc is not None):
            if self.num_cores_per_machine != (self.num_cores_per_mpiproc
                                        * self.num_mpiprocs_per_machine):
                # If user specify both values, check if specified 
                # values are correct
                raise ValueError(value_error)
        elif self.num_cores_per_machine is not None:
            if self.num_cores_per_machine <= 0:
                raise ValueError("num_cores_per_machine must be >=1")
            # calculate num_cores_per_mpiproc
            # In this plugin we never used num_cores_per_machine so if it 
            # is not defined it is OK.
            self.num_cores_per_mpiproc = (self.num_cores_per_machine
                                 / self.num_mpiprocs_per_machine)
            if(isinstance(self.num_cores_per_mpiproc, int)):
                raise ValueError(value_error)


class SlurmScheduler(aiida.scheduler.Scheduler):
    """
    Support for the SLURM scheduler (http://slurm.schedmd.com/).
    """
    _logger = aiida.scheduler.Scheduler._logger.getChild('slurm')

    # Query only by list of jobs and not by user
    _features = {
        'can_query_by_user': False,
        }
    
    # The class to be used for the job resource.
    _job_resource_class = SlurmJobResource

    # Fields to query or to parse
    # Unavailable fields: substate, cputime
    fields = [
      ("%i",'job_id'), # job or job step id
      ("%t",'state_raw'), # job state in compact form
      ("%r",'annotation'), # reason for the job being in its current state
      ("%B",'executing_host'), # Executing (batch) host
      ("%u",'username'), # username
      ("%D",'number_nodes'), # number of nodes allocated
      ("%C",'number_cpus'), # number of allocated cores (if already running)
      ("%R",'allocated_machines'), # list of allocated nodes when running, otherwise 
             # reason within parenthesis
      ("%P",'partition'), # partition (queue) of the job
      ("%l",'time_limit'), # time limit in days-hours:minutes:seconds
      ("%M",'time_used'), # Time used by the job in days-hours:minutes:seconds
      ("%S",'dispatch_time'), # actual or expected dispatch time (start time)
      ("%j",'job_name'), # job name (title)
      ("%V", 'submission_time') # This is probably new, it exists in version
                                # 14.03.7 and later  
      ]

    def _get_joblist_command(self, jobs=None, user=None):
        """
        The command to report full information on existing jobs.

        I separate the fields with the _field_separator string
        order: jobnum, state, walltime, queue[=partition],
               user, numnodes, numcores, title
        """
        from aiida.common.exceptions import FeatureNotAvailable
        
        # I add the environment variable SLURM_TIME_FORMAT in front to be
        # sure to get the times in 'standard' format
        command = ["SLURM_TIME_FORMAT='standard'", "squeue", "--noheader",
                   "-o '{}'".format(_field_separator.join(
                       _[0] for _ in self.fields))]

        if user and jobs:
            raise FeatureNotAvailable("Cannot query by user and job(s) in SLURM")

        if user:
            command.append('-u{}'.format(user))

        if jobs:
            joblist = []
            if isinstance(jobs, basestring):
                joblist.append(jobs)
            else:
                if not isinstance(jobs, (tuple, list)):
                    raise TypeError(
                        "If provided, the 'jobs' variable must be a string or "
                        "a list of strings")
                joblist = jobs
            command.append('--jobs={}'.format(','.join(joblist)))

        comm = ' '.join(command)
        self.logger.debug("squeue command: {}".format(comm))
        return comm

    def _get_detailed_jobinfo_command(self,jobid):
        """
        Return the command to run to get the detailed information on a job,
        even after the job has finished.

        The output text is just retrieved, and returned for logging purposes.
        --parsable split the fields with a pipe (|), adding a pipe also at 
        the end.
        """
        return "sacct --format=AllocCPUS,Account,AssocID,AveCPU,AvePages,AveRSS,AveVMSize,Cluster,Comment,CPUTime,CPUTimeRAW,DerivedExitCode,Elapsed,Eligible,End,ExitCode,GID,Group,JobID,JobName,MaxRSS,MaxRSSNode,MaxRSSTask,MaxVMSize,MaxVMSizeNode,MaxVMSizeTask,MinCPU,MinCPUNode,MinCPUTask,NCPUS,NNodes,NodeList,NTasks,Priority,Partition,QOSRAW,ReqCPUS,Reserved,ResvCPU,ResvCPURAW,Start,State,Submit,Suspended,SystemCPU,Timelimit,TotalCPU,UID,User,UserCPU --parsable --jobs={}".format(jobid)

    def _get_submit_script_header(self, job_tmpl):
        """
        Return the submit script header, using the parameters from the
        job_tmpl.

        Args:
           job_tmpl: an JobTemplate instance with relevant parameters set.

        TODO: truncate the title if too long
        """
        import string

        empty_line = ""
        
        lines = []
        if job_tmpl.submit_as_hold:
            lines.append("#SBATCH -H")

        if job_tmpl.rerunnable:
            lines.append("#SBATCH --requeue")
        else:
            lines.append("#SBATCH --no-requeue")

        if job_tmpl.email:
            # If not specified, but email events are set, SLURM
            # sends the mail to the job owner by default
            lines.append('#SBATCH --mail-user={}'.format(job_tmpl.email))
            
        if job_tmpl.email_on_started:            
            lines.append("#SBATCH --mail-type=BEGIN")
        if job_tmpl.email_on_terminated:
            lines.append("#SBATCH --mail-type=FAIL")
            lines.append("#SBATCH --mail-type=END")
        
        if job_tmpl.job_name:
            # The man page does not specify any specific limitation
            # on the job name.
            # Just to be sure, I remove unwanted characters, and I
            # trim it to length 128

            # I leave only letters, numbers, dots, dashes and underscores
            # Note: I don't compile the regexp, I am going to use it only once
            job_title = re.sub(r'[^a-zA-Z0-9_.-]+', '', job_tmpl.job_name)

            # prepend a 'j' (for 'job') before the string if the string
            # is now empty or does not start with a valid charachter
            if not job_title or (
                job_title[0] not in string.letters + string.digits):
                job_title = 'j' + job_title
            
            # Truncate to the first 128 characters 
            # Nothing is done if the string is shorter.
            job_title = job_title[:128]
            
            lines.append('#SBATCH --job-name="{}"'.format(job_title))
        
        if job_tmpl.import_sys_environment:
            lines.append("#SBATCH --get-user-env")
            
        if job_tmpl.sched_output_path:
            lines.append("#SBATCH --output={}".format(job_tmpl.sched_output_path))

        if job_tmpl.sched_join_files:
            # TODO: manual says:
            #By  default both standard output and standard error are directed
            #to a file of the name "slurm-%j.out", where the "%j" is replaced
            #with  the  job  allocation  number. 
            # See that this automatic redirection works also if 
            # I specify a different --output file
            if job_tmpl.sched_error_path:
                self.logger.info(
                    "sched_join_files is True, but sched_error_path is set in "
                    "SLURM script; ignoring sched_error_path")
        else:
            if job_tmpl.sched_error_path:
                lines.append("#SBATCH --error={}".format(job_tmpl.sched_error_path))
            else:
                # To avoid automatic join of files
                lines.append("#SBATCH --error=slurm-%j.err")

        if job_tmpl.queue_name:
            lines.append("#SBATCH --partition={}".format(job_tmpl.queue_name))
            
        if job_tmpl.priority:
            #  Run the job with an adjusted scheduling priority  within  SLURM.
            #  With no adjustment value the scheduling priority is decreased by
            #  100. The adjustment range is from -10000 (highest  priority)  to
            #  10000  (lowest  priority). 
            lines.append("#SBATCH --nice={}".format(job_tmpl.priority))
      
        if not job_tmpl.job_resource:
            raise ValueError("Job resources (as the num_machines) are required "
                             "for the SLURM scheduler plugin")
        
                    
        lines.append("#SBATCH --nodes={}".format(job_tmpl.job_resource.num_machines))
        if job_tmpl.job_resource.num_mpiprocs_per_machine:
            lines.append("#SBATCH --ntasks-per-node={}".format(
                    job_tmpl.job_resource.num_mpiprocs_per_machine))

        if job_tmpl.job_resource.num_cores_per_mpiproc:
            lines.append("#SBATCH --cpus-per-task={}".format(
                    job_tmpl.job_resource.num_cores_per_mpiproc))

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
            days = tot_secs // 86400
            tot_hours = tot_secs % 86400
            hours = tot_hours // 3600
            tot_minutes = tot_hours % 3600
            minutes = tot_minutes // 60
            seconds = tot_minutes % 60
            if days == 0:
                lines.append("#SBATCH --time={:02d}:{:02d}:{:02d}".format(
                        hours, minutes, seconds))
            else:
                lines.append("#SBATCH --time={:d}-{:02d}:{:02d}:{:02d}".format(
                        days, hours, minutes, seconds))

        # It is the memory per node, not per cpu!
        if job_tmpl.max_memory_kb:
            try:
                virtualMemoryKb = int(job_tmpl.max_memory_kb)
                if virtualMemoryKb <= 0:
                    raise ValueError
            except ValueError:
                raise ValueError(
                    "max_memory_kb must be "
                    "a positive integer (in kB)! It is instead '{}'"
                    "".format((job_tmpl.MaxMemoryKb)))
            # --mem: Specify the real memory required per node in MegaBytes. 
            # --mem and  --mem-per-cpu  are  mutually exclusive.
            lines.append("#SBATCH --mem={}".format(virtualMemoryKb//1024))

        if job_tmpl.custom_scheduler_commands:
            lines.append(job_tmpl.custom_scheduler_commands)

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
        submit_command = 'sbatch {}'.format(submit_script)

        self.logger.info("submitting with: " + submit_command)

        return submit_command
      
    def _parse_submit_output(self, retval, stdout, stderr):
        """
        Parse the output of the submit command, as returned by executing the
        command returned by _get_submit_command command.
        
        To be implemented by the plugin.
        
        Return a string with the JobID.
        """
        if retval != 0:
            self.logger.error("Error in _parse_submit_output: retval={}; "
                "stdout={}; stderr={}".format(retval, stdout, stderr))
            raise SchedulerError("Error during submission, retval={}\n"
                                 "stdout={}\nstderr={}".format(
                retval, stdout, stderr))

        try:
            transport_string = " for {}".format(self.transport)
        except SchedulerError:
            transport_string = ""
 
        if stderr.strip():
            self.logger.warning("in _parse_submit_output{}: "
                "there was some text in stderr: {}".format(
                    transport_string,stderr))
         
        # I check for a valid string in the output.
        # See comments near the regexp above.
        # I check for the first line that matches.
        for l in stdout.split('\n'):
            match = _slurm_submitted_regexp.match(l.strip())
            if match:
                return match.group('jobid')
        # If I am here, no valid line could be found.
        self.logger.error("in _parse_submit_output{}: "
                          "unable to find the job id: {}".format(
                transport_string,stdout))
        raise SchedulerError(
            "Error during submission, could not retrieve the jobID from "
            "sbatch output; see log for more info.")

    def _parse_joblist_output(self, retval, stdout, stderr):
        """
        Parse the queue output string, as returned by executing the
        command returned by _get_joblist_command command,
        that is here implemented as a list of lines, one for each
        job, with _field_separator as separator. The order is described
        in the _get_joblist_command function.
        
        Return a list of JobInfo objects, one of each job, 
        each relevant parameters implemented.

        Note: depending on the scheduler configuration, finished jobs may 
            either appear here, or not. 
            This function will only return one element for each job find
            in the qstat output; missing jobs (for whatever reason) simply
            will not appear here.
        """
        num_fields = len(self.fields)

        # I don't raise because if I pass a list of jobs,
        # I get a non-zero status
        # if one of the job is not in the list anymore
        # retval should be zero
        #if retval != 0:
            #self.logger.warning("Error in _parse_joblist_output: retval={}; "
            #    "stdout={}; stderr={}".format(retval, stdout, stderr))

        # issue a warning if there is any stderr output and
        # there is no line containing "Invalid job id specified", that happens
        # when I ask for specific calculations, and they are all finished
        if stderr.strip() and "Invalid job id specified" not in stderr:
            self.logger.warning("Warning in _parse_joblist_output, non-empty "
                "stderr='{}'".format(stderr.strip()))
            if retval != 0:
                raise SchedulerError(
                    "Error during squeue parsing (_parse_joblist_output function)")

        # will contain raw data parsed from output: only lines with the
        # separator, and already split in fields
        # I put num_fields, because in this way
        # if the symbol _field_separator appears in the title (that is
        # the last field), I don't split the title.
        # This assumes that _field_separator never
        # appears in any previous field.
        jobdata_raw = [l.split(_field_separator,num_fields)
                       for l in stdout.splitlines()
                       if _field_separator in l]

        # Create dictionary and parse specific fields
        job_list = []
        for job in jobdata_raw:

            thisjob_dict = {k[1]: v for k, v in zip(self.fields, job)}

            this_job = JobInfo()
            try:
                this_job.job_id = thisjob_dict['job_id']

                this_job.annotation = thisjob_dict['annotation']
                job_state_raw = thisjob_dict['state_raw']
            except KeyError:
                # I skip this calculation if I couldn't find this basic info
                # (I don't append anything to job_list before continuing)
                self.logger.error("Wrong line length in squeue output! '{}'"
                                  "".format(job))
                continue
            
            try:
                job_state_string = _map_status_slurm[job_state_raw]
            except KeyError:
                self.logger.warning("Unrecognized job_state '{}' for job "
                                    "id {}".format(job_state_raw,
                                                   this_job.job_id))
                job_state_string = job_states.UNDETERMINED
            # QUEUED_HELD states are not specific states in SLURM;
            # they are instead set with state QUEUED, and then the
            # annotation tells if the job is held.
            # I check for 'Dependency', 'JobHeldUser',
            # 'JobHeldAdmin', 'BeginTime'.
            # Other states should not bring the job in QUEUED_HELD, I believe
            # (the man page of slurm seems to be incomplete, for instance
            # JobHeld* are not reported there; I also checked at the source code
            # of slurm 2.6 on github (https://github.com/SchedMD/slurm),
            # file slurm/src/common/slurm_protocol_defs.c, 
            # and these seem all the states to be taken into account for the
            # QUEUED_HELD status).
            # There are actually a few others, like possible
            # failures, or partition-related reasons, but for the moment I 
            # leave them in the QUEUED state.
            if (job_state_string == job_states.QUEUED and
                  this_job.annotation in 
                  ['Dependency', 'JobHeldUser', 'JobHeldAdmin', 'BeginTime']):
                job_state_string = job_states.QUEUED_HELD
            
            this_job.job_state = job_state_string

            ####
            # Up to here, I just made sure that there were at least three
            # fields, to set the most important fields for a job.
            # I now check if the length is equal to the number of fields
            if len(job) < num_fields:
                # I store this job only with the information
                # gathered up to now, and continue to the next job
                # Also print a warning
                self.logger.warning("Wrong line length in squeue output!"
                                    "Skipping optional fields. Line: '{}'"
                                    "".format(jobdata_raw))
                # I append this job before continuing
                job_list.append(this_job)
                continue
            
            # TODO: store executing_host?

            this_job.job_owner = thisjob_dict['username']

            try:
                this_job.num_machines = int(thisjob_dict['number_nodes'])
            except ValueError:
                self.logger.warning("The number of allocated nodes is not "
                                    "an integer ({}) for job id {}!".format(
                        thisjob_dict['number_nodes'],
                        this_job.job_id))

            try:
                this_job.num_mpiprocs = int(thisjob_dict['number_cpus'])
            except ValueError:
                self.logger.warning("The number of allocated cores is not "
                                    "an integer ({}) for job id {}!".format(
                        thisjob_dict['number_cpus'],
                        this_job.job_id))

            # ALLOCATED NODES HERE
            # string may be in the format
            # nid00[684-685,722-723,748-749,958-959]
            # therefore it requires some parsing, that is unnecessary now.
            # I just store is as a raw string for the moment, and I leave
            # this_job.allocated_machines undefined
            if this_job.job_state == job_states.RUNNING:
                this_job.allocated_machines_raw = thisjob_dict[
                    'allocated_machines']

            this_job.queue_name = thisjob_dict['partition']

            try:
                this_job.requested_wallclock_time_seconds = (self._convert_time(
                    thisjob_dict['time_limit']))
            except ValueError:
                self.logger.warning("Error parsing the time limit "
                    "for job id {}".format(this_job.job_id))

            # Only if it is RUNNING; otherwise it is not meaningful,
            # and may be not set (in my test, it is set to zero)
            if this_job.job_state == job_states.RUNNING:
                try:
                    this_job.wallclock_time_seconds = (self._convert_time(
                            thisjob_dict['time_used']))
                except ValueError:
                    self.logger.warning("Error parsing time_used "
                                        "for job id {}".format(this_job.job_id))

                try:
                    this_job.dispatch_time = self._parse_time_string(
                        thisjob_dict['dispatch_time'])
                except ValueError:
                    self.logger.warning("Error parsing dispatch_time for job "
                                        "id {}".format(this_job.job_id))

            try:
                this_job.submission_time = self._parse_time_string(
                    thisjob_dict['submission_time'])
            except ValueError:
                self.logger.warning("Error parsing submission_time for job "
                                    "id {}".format(this_job.job_id))

            this_job.title = thisjob_dict['job_name']

            # Everything goes here anyway for debugging purposes
            this_job.raw_data = job

            # Double check of redundant info
            # Not really useful now, allocated_machines in this
            # version of the plugin is never set
            if (this_job.allocated_machines is not None and 
                this_job.num_machines is not None):
                if len(this_job.allocated_machines) != this_job.num_machines:
                    self.logger.error("The length of the list of allocated "
                                      "nodes ({}) is different from the "
                                      "expected number of nodes ({})!".format(
                        len(this_job.allocated_machines), 
                        this_job.num_machines))

            # I append to the list of jobs to return
            job_list.append(this_job)

        return job_list

    def _convert_time(self,string):
        """
        Convert a string in the format DD-HH:MM:SS to a number of seconds.
        """
        groups = _time_regexp.match(string)
        if groups is None:
            self.logger.warning("Unrecognized format for "
                "time string '{}'".format(string))
            raise ValueError("Unrecognized format for time string.")
            
        groupdict = groups.groupdict()
        # should not raise a ValueError, they all match digits only
        days  = int(groupdict['days'] if groupdict['days'] is not None 
                    else 0)
        hours = int(groupdict['hours'] if groupdict['hours'] is not None 
                    else 0)
        mins  = int(groupdict['minutes'] if groupdict['minutes'] is not None 
                    else 0)
        secs  = int(groupdict['seconds'] if groupdict['seconds'] is not None
                    else 0)
        
        return days * 86400 + hours * 3600 + mins * 60 + secs


    def _parse_time_string(self,string,fmt='%Y-%m-%dT%H:%M:%S'):
        """
        Parse a time string in the format returned from qstat -f and
        returns a datetime object.
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
        submit_command = 'scancel {}'.format(jobid)

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

        try:
            transport_string = " for {}".format(self.transport)
        except SchedulerError:
            transport_string = ""

        if stderr.strip():
            self.logger.warning("in _parse_kill_output{}: "
                "there was some text in stderr: {}".format(
                    transport_string,stderr))

        if stdout.strip():
            self.logger.warning("in _parse_kill_output{}: "
                "there was some text in stdout: {}".format(
                    transport_string,stdout))

        return True
    
    
