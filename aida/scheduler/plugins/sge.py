"""
Plugin for PBSPro.
This has been tested on PBSPro v. 12.
"""

import aida.scheduler
from aida.common.utils import escape_for_bash
from aida.scheduler import SchedulerError, SchedulerParsingError
from aida.scheduler.datastructures import (
    JobInfo, jobStates, NodeInfo)

# This maps PbsPro status letters to our own status list

## List of states from the man page of qstat
#B  Array job has at least one subjob running.
#E  Job is exiting after having run.
#F  Job is finished.
#H  Job is held.
#M  Job was moved to another server.
#Q  Job is queued.
#R  Job is running.
#S  Job is suspended.
#T  Job is being moved to new location.
#U  Cycle-harvesting job is suspended due to  keyboard  activity.
#W  Job is waiting for its submitter-assigned start time to be reached.
#X  Subjob has completed execution or has been deleted.

_map_status_pbspro = {
    'B': jobStates.RUNNING,
    'E': jobStates.RUNNING, # If exiting, for our purposes it is still running
    'F': jobStates.DONE,
    'H': jobStates.QUEUED_HELD,
    'M': jobStates.UNDETERMINED, # TODO: check if this is ok?
    'Q': jobStates.QUEUED,
    'R': jobStates.RUNNING,
    'S': jobStates.SUSPENDED,
#    'T': jobStates., # TODO: what to do here?
    'U': jobStates.SUSPENDED,
    'W': jobStates.QUEUED,
    'X': jobStates.DONE,
    }



class SGEScheduler(aida.scheduler.Scheduler):
    """
    SGEPro implementation of the scheduler functions.

    TODO: implement __unicode__ and __str__ methods.
    """
    _logger = aida.scheduler.Scheduler._logger.getChild('pbspro')

    def _get_joblist_command(self,jobs=None,user=None): 
        """
        The command to report full information on existing jobs.

        TODO: in the case of job arrays, decide what to do (i.e., if we want
              to pass the -t options to list each subjob).
        """
        command = 'qstat -f'
        if user:
            command += ' -u {}'.format(escape_for_bash(user))
        if jobs:
            if isinstance(jobs, basestring):
                command += ' {}'.format(jobs)
            else:
                try:
                    command += ' {}'.format(' '.join(jobs))
                except TypeError:
                    raise TypeError(
                        "If provided, the 'jobs' variable must be a list of strings")
            
        self.logger.debug("qstat command: {}".format(command))
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
        import copy

        empty_line = ""
        
        lines = []
        if job_tmpl.submitAsHold:
            lines.append("#PBS -h")

        if job_tmpl.rerunnable:
            lines.append("#PBS -r y")
        else:
            lines.append("#PBS -r n")

        if job_tmpl.email:
            # If not specified, but email events are set, PBSPro
            # sends the mail to the job owner by default
            lines.append('#PBS -M {}'.format(job_tmpl.email))
            
        email_events = ""
        if job_tmpl.emailOnStarted:
            email_events += "b"
        if job_tmpl.emailOnTerminated:
            email_events += "ea"
        if email_events:
            lines.append("#PBS -m {}".format(email_events))
            if not job_tmpl.email:
                self.logger.info(
                    "Email triggers provided to PBSPro script for job,"
                    "but no email field set; will send emails to "
                    "the job owner as set in the scheduler")
        else:
            lines.append("#PBS -m n")
            
        if job_tmpl.jobName:
            # From qsub man page:
            # string, up to 15 characters in length.  It must
            # consist of an  alphabetic  or  numeric  character 
            # followed  by printable, non-white-space characters.
            # Default:  if a script is used to submit the job, the job's name
            # is the name of the script.  If no script  is  used,  the  job's
            # name is "STDIN".
            #
            # I leave only letters, numbers, dots, dashes and underscores
            # Note: I don't compile the regexp, I am going to use it only once
            job_title = re.sub(r'[^a-zA-Z0-9_.-]+', '', job_tmpl.jobName)

            # prepend a 'j' (for 'job') before the string if the string
            # is now empty or does not start with a valid charachter
            if not job_title or (
                job_title[0] not in string.letters + string.digits):
                job_title = 'j' + job_title
            
            # Truncate to the first 15 characters 
            # Nothing is done if the string is shorter.
            job_title = job_title[:15]
            
            lines.append("#PBS -N {}".format(job_title))
            
        if job_tmpl.schedOutputPath:
            lines.append("#PBS -o {}".format(job_tmpl.schedOutputPath))

        if job_tmpl.schedJoinFiles:
            # from qsub man page:
            # 'oe': Standard error and standard output are merged  into 
            #       standard output
            # 'eo': Standard error and standard output are merged  into 
            #       standard error
            # 'n' : Standard error and standard output are not merged (default)
            lines.append("#PBS -j oe")
            if job_tmpl.schedErrorPath:
                self.logger.info(
                    "schedJoinFiles is True, but schedErrorPath is set in "
                    "PBSPro script; ignoring schedErrorPath")
        else:
            if job_tmpl.schedErrorPath:
                lines.append("#PBS -e {}".format(job_tmpl.schedErrorPath))

        if job_tmpl.queueName:
            lines.append("#PBS -q {}".format(job_tmpl.queueName))
            
        if job_tmpl.priority:
            # Priority of the job.  Format: host-dependent integer.  Default:
            # zero.   Range:  [-1024,  +1023] inclusive.  Sets job's Priority
            # attribute to priority.
            # TODO: Here I expect that priority is passed in the correct PBSPro
            # format. To fix.
            lines.append("#PBS -p {}".format(job_tmpl.priority))

        
        if not job_tmpl.numNodes:
            raise ValueError("numNodes is required for the PBSPro scheduler "
                             "plugin")
        select_string = "select={}".format(job_tmpl.numNodes)
        if job_tmpl.numCpusPerNode:
            select_string += ":ncpus={}".format(job_tmpl.numCpusPerNode)

        if job_tmpl.maxWallclockSeconds is not None:
            try:
                tot_secs = int(job_tmpl.maxWallclockSeconds)
                if tot_secs <= 0:
                    raise ValueError
            except ValueError:
                raise ValueError(
                    "maxWallclockSeconds must be "
                    "a positive integer (in seconds)! It is instead '{}'"
                    "".format((job_tmpl.maxWallclockTime)))
            hours = tot_secs / 3600
            tot_minutes = tot_secs % 3600
            minutes = tot_minutes / 60
            seconds = tot_minutes % 60
            lines.append("#PBS -l walltime={:02d}:{:02d}:{:02d}".format(
                hours, minutes, seconds))

        if job_tmpl.maxMemoryKb:
            try:
                virtualMemoryKb = int(job_tmpl.maxMemoryKb)
                if virtualMemoryKb <= 0:
                    raise ValueError
            except ValueError:
                raise ValueError(
                    "maxMemoryKb must be "
                    "a positive integer (in kB)! It is instead '{}'"
                    "".format((job_tmpl.MaxMemoryKb)))
                select_string += ":mem={}kb".format(virtualMemoryKb)
                
        lines.append("#PBS -l {}".format(select_string))

        # Job environment variables are to be set on one single line. 
        # This is a tough job due to the escaping of commas, etc.
        # moreover, I am having issues making it work.
        # Therefore, I assume that this is bash and export variables by
        # and.
        
        if job_tmpl.jobEnvironment:
            lines.append(empty_line)
            lines.append("# ENVIRONMENT VARIABLES BEGIN ###")
            if not isinstance(job_tmpl.jobEnvironment, dict):
                raise ValueError("If you provide jobEnvironment, it must be "
                                 "a dictionary")
            for k, v in job_tmpl.jobEnvironment.iteritems():
                lines.append("export {}={}".format(
                        k.strip(),
                        escape_for_bash(v)))
            lines.append("# ENVIRONMENT VARIABLES  END  ###")
            lines.append(empty_line)

        # Required to change directory to the working directory, that is
        # the one from which the job was submitted
        lines.append('cd "$PBS_O_WORKDIR"')
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
        submit_command = 'qsub {}'.format(submit_script)

        self.logger.info("submitting with: " + submit_command)

        return submit_command
      
    def _parse_joblist_output(self, retval, stdout, stderr):
        """
        Parse the queue output string, as returned by executing the
        command returned by _get_joblist_command command (qstat -f).
        
        Return a list of JobInfo objects, one of each job, 
        each relevant parameters implemented.

        Note: depending on the scheduler configuration, finished jobs may 
            either appear here, or not. 
            This function will only return one element for each job find
            in the qstat output; missing jobs (for whatever reason) simply
            will not appear here.
        """
        # retval should be zero
        if retval != 0:
            self.logger.error("Error in _parse_joblist_output: retval={}; "
                "stdout={}; stderr={}".format(retval, stdout, stderr))
            raise SchedulerError(
                "Error during qstat parsing (_parse_joblist_output function)")

        # issue a warning if there is any stderr output
        if stderr.strip():
            self.logger.error("Warning in _parse_joblist_output, non-empty "
                "stderr='{}'".format(stderr))

        jobdata_raw = [] # will contain raw data parsed from qstat output
        # Get raw data and split in lines
        for line_num, l in enumerate(stdout.split('\n'),start=1):
            # Each new job stanza starts with the string 'Job Id:': I 
            # create a new item in the jobdata_raw list
            if l.startswith('Job Id:'):
                jobdata_raw.append(
                    {'id': l.split(':',1)[1].strip(),
                    'lines': []})
            else:
                if l.strip():
                    # This is a non-empty line, therefore it is an attribute
                    # of the last job found
                    if not jobdata_raw:
                        # The list is still empty! (This means that I found a
                        # non-empty line, before finding the first 'Job Id:'
                        # string: it is an error. However this may happen
                        # only before the first job. To err on the safe side,
                        # I print a warning instead of crashing).
                        #raise SchedulerParsingError("I did not find the header for the first job")
                        self.logger.warning("I found some text before the "
                        "first job: {}".format(l))
                    else:
                        if l.startswith(' '):
                            # If it starts with a space, it is a new field
                            jobdata_raw[-1]['lines'].append(l)
                        elif l.startswith('\t'):
                            # If a line starts with a TAB,
                            # I append to the previous string 
                            # stripping the TAB
                            if not jobdata_raw[-1]['lines']:
                                raise SchedulerParsingError(
                            "Line {} is the first line of the job, but it "
                            "starts with a TAB! ({})".format(line_num, l))
                            jobdata_raw[-1]['lines'][-1] += l[1:]
                        else:
                            raise SchedulerParsingError(
                                "Wrong starting character at line {}! ({})"
                                "".format(line_num, l))

        # Create dictionary and parse specific fields
        job_list = []
        for job in jobdata_raw:
            this_job = JobInfo()
            this_job.jobId = job['id']

            lines_without_equals_sign = [i for i in job['lines']
                if '=' not in i]

            # There are lines without equals sign: this is bad
            if lines_without_equals_sign:
                # Should I only warn?
                self.logger.error("There are lines without equals sign! {}"
                    "".format(lines_without_equals_sign))
                raise(SchedulerParsingError("There are lines without equals "
                                            "sign."))

            raw_data = {i.split('=',1)[0].strip().lower(): 
                i.split('=',1)[1].lstrip()
                for i in job['lines'] if '=' in i}

            # I believe that exitStatus and terminatingSignal cannot be
            # retrieved from the qstat -f output.
            
            # I wrap calls in try-except clauses to avoid errors if a field
            # is missing
            try:
                this_job.title = raw_data['job_name']
            except KeyError:
                self.logger.debug("No 'job_name' field for job id "
                    "{}".format(this_job.jobId))

            try:
                this_job.annotation = raw_data['comment']
            except KeyError:
                # Many jobs do not have a comment; I do not complain about it.
                pass
                #self.logger.debug("No 'comment' field for job id {}".format(
                #    this_job.jobId))
            
            try:
                job_state_string = raw_data['job_state']
                try:
                    this_job.jobState = _map_status_pbspro[job_state_string]
                except KeyError:
                    self.logger.warning("Unrecognized job_state '{}' for job "
                                        "id {}".format(job_state_string,
                                                       this_job.jobID))
                    this_job.jobState = jobStates.UNDETERMINED
            except KeyError:
                self.logger.debug("No 'job_state' field for job id {}".format(
                    this_job.jobId))
                this_job.jobState = jobStates.UNDETERMINED

            try:
                this_job.jobSubState = raw_data['substate']
            except KeyError:
                self.logger.debug("No 'substate' field for job id {}".format(
                    this_job.jobId))


            # TODO: we are not setting it because probably the assumption
            #       submissionMachine == raw_data['server'] is not correct
#            try:
#                this_job.submissionMachine = raw_data['server']
#            except KeyError:
#                # No 'server' found; I skip
#                pass

            try:
                exec_hosts = raw_data['exec_host'].split('+')
            except KeyError:
                # No exec_host information found (it may be ok, if the job
                # is not running)
                pass
            else:
                # parse each host; syntax, from the man page:
                # hosta/J1+hostb/J2*P+...
                # where  J1 and J2 are an index of the job
                # on the named host and P is the number of
                # processors allocated from that host to this job.
                # P does not appear if it is 1.
                try:
                    exec_host_list = []
                    for exec_host in exec_hosts:
                        node = NodeInfo()
                        node.nodeName, data = exec_host.split('/')
                        data = data.split('*')
                        if len(data) == 1:
                            node.jobIndex = int(data[0])
                            node.numCores = 1
                        elif len(data) == 2:
                            node.jobIndex = int(data[0])
                            node.numCores = int(data[1])
                        else:
                            raise ValueError("Wrong number of pieces: {} "
                                             "instead of 1 or 2 in exec_hosts: "
                                             "{}".format(len(data), exec_hosts))
                        exec_host_list.append(node)
                    this_job.allocatedNodes = exec_host_list
                except Exception as e:
                    self.logger.debug("Problem parsing the node names, I "
                                      "got Exception {} with message {}; "
                                      "exec_hosts was {}".format(
                            str(type(e)), e.message, exec_hosts))

            try:
                # I strip the part after the @: is this always ok?
                this_job.jobOwner = raw_data['job_owner'].split('@')[0]
            except KeyError:
                self.logger.debug("No 'job_owner' field for job id {}".format(
                    this_job.jobId))

            try:
                this_job.numCores = int(raw_data['resource_list.ncpus'])
                # TODO: understand if this is the correct field also for
                #       multithreaded (OpenMP) jobs.
            except KeyError:
                self.logger.debug("No 'resource_list.ncpus' field for job id "
                    "{}".format(this_job.jobId))
            except IndexError:
                self.logger.warning(";resource_list.ncpus' is not an integer "
                                    "({}) for job id {}!".format(
                        raw_data['resource_list.ncpus'],
                        this_job.jobId))

            try:
                this_job.numNodes = int(raw_data['resource_list.nodect'])
            except KeyError:
                self.logger.debug("No 'resource_list.nodect' field for job id "
                    "{}".format(this_job.jobId))
            except IndexError:
                self.logger.warning(";resource_list.nodect' is not an integer "
                                    "({}) for job id {}!".format(
                        raw_data['resource_list.nodect'],
                        this_job.jobId))

            # Double check of redundant info
            if (this_job.allocatedNodes is not None and 
                this_job.numNodes is not None):
                if len(this_job.allocatedNodes) != this_job.numNodes:
                    self.logger.error("The length of the list of allocated "
                                      "nodes ({}) is different from the "
                                      "expected number of nodes ({})!".format(
                        len(this_job.allocatedNodes), this_job.numNodes))

            try:
                this_job.queueName = raw_data['queue']
            except KeyError:
                self.logger.debug("No 'queue' field for job id "
                    "{}".format(this_job.jobId))

            try:
                this_job.RequestedWallclockTime = (self._convert_time(
                    raw_data['resource_list.walltime']))
            except KeyError:
                self.logger.debug("No 'resource_list.walltime' field for "
                    "job id {}".format(this_job.jobId))
            except ValueError:
                self.logger.warning("Error parsing 'resource_list.walltime' "
                    "for job id {}".format(this_job.jobId))

            try:
                this_job.wallclockTime = (self._convert_time(
                    raw_data['resources_used.walltime']))
            except KeyError:
                # May not have started yet
                pass
            except ValueError:
                self.logger.warning("Error parsing 'resources_used.walltime' "
                    "for job id {}".format(this_job.jobId))

            try:
                this_job.cpuTime = (self._convert_time(
                    raw_data['resources_used.cput']))
            except KeyError:
                # May not have started yet
                pass
            except ValueError:
                self.logger.warning("Error parsing 'resources_used.cput' "
                    "for job id {}".format(this_job.jobId))

            #
            # ctime: The time that the job was created
            # mtime: The time that the job was last modified, changed state,
            #        or changed locations. 
            # qtime: The time that the job entered the current queue
            # stime: The time when the job started execution.  
            # etime: The time that the job became eligible to run, i.e. in a
            #        queued state while residing in an execution queue.

            try:
                this_job.submissionTime = self._parse_time_string(
                    raw_data['ctime'])
            except KeyError:
                self.logger.debug("No 'ctime' field for job id "
                    "{}".format(this_job.jobId))
            except ValueError:
                self.logger.warning("Error parsing 'ctime' for job id "
                    "{}".format(this_job.jobId))

            try:
                this_job.dispatchTime = self._parse_time_string(
                    raw_data['stime'])
            except KeyError:
                # The job may not have been started yet
                pass
            except ValueError:
                self.logger.warning("Error parsing 'stime' for job id "
                    "{}".format(this_job.jobId))
            
            # TODO: see if we want to set also finishTime for finished jobs,
            # if there are any

            # Everything goes here anyway for debugging purposes
            this_job.rawData = raw_data

            # I append to the list of jobs to return
            job_list.append(this_job)

        return job_list

    def _convert_time(self,string):
        """
        Convert a string in the format HH:MM:SS to a number of seconds.
        """
        pieces = string.split(':')
        if len(pieces) != 3:
            self.logger.warning("Wrong number of pieces (expected 3) for "
                "time string {}".format(string))
            raise ValueError("Wrong number of pieces for time string.")
        
        try:
            hours = int(pieces[0])
            if hours < 0:
                raise ValueError
        except ValueError:
            self.logger.warning("Not a valid number of hours: {}".format(
                pieces[0]))
            raise ValueError("Not a valid number of hours.")

        try:
            mins = int(pieces[1])
            if mins < 0:
                raise ValueError
        except ValueError:
            self.logger.warning("Not a valid number of minutes: {}".format(
                pieces[1]))
            raise ValueError("Not a valid number of minutes.")

        try:
            secs = int(pieces[2])
            if secs < 0:
                raise ValueError
        except ValueError:
            self.logger.warning("Not a valid number of seconds: {}".format(
                pieces[2]))
            raise ValueError("Not a valid number of seconds.")
        
        return hours * 3600 + mins * 60 + secs


    def _parse_time_string(self,string,format='%a %b %d %H:%M:%S %Y'):
        """
        Parse a time string in the format returned from qstat -f and
        returns a datetime object.
        """
        import time, datetime

        try:
            time_struct = time.strptime(string,format)
        except Exception as e:
            self.logger.debug("Unable to parse time string {}, the message "
                "was {}".format(string, e.message))
            raise ValueError("Problem parsing the time string.")

        # I convert from a time_struct to a datetime object going through
        # the seconds since epoch, as suggested on stackoverflow:
        # http://stackoverflow.com/questions/1697815
        return datetime.datetime.fromtimestamp(time.mktime(time_struct))

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
            raise SchedulerError("Error during submission, retval={}".format(
                retval))

        if stderr.strip():
            self.logger.warning("in _parse_submit_output for {}: "
                "there was some text in stderr: {}".format(
                    str(self.transport),stderr))
        
        return stdout.strip()

if __name__ == '__main__':
    import unittest
    import logging
    import uuid
    from aida.common.pluginloader import load_plugin
    
    # TODO : clean the old commands when the test will be possible to be carried offline
    
    # from aida.transport import Transport
    
    # SshTransport = load_plugin(Transport, 'aida.transport.plugins', 'ssh')
    
    text_qstat_f_to_test = """Job Id: 68350.mycluster
    Job_Name = cell-Qnormal
    Job_Owner = usernum1@mycluster.cluster
    job_state = Q
    queue = Q_express
    server = mycluster
    Checkpoint = u
    ctime = Tue Apr  9 15:01:47 2013
    Error_Path = mycluster.cluster:/home/usernum1/scratch/cptest/scaletest/PTOs
    caletest/testjob.err
    Hold_Types = n
    Join_Path = n
    Keep_Files = n
    Mail_Points = a
    mtime = Mon Apr 22 13:13:53 2013
    Output_Path = mycluster.cluster:/home/usernum1/scratch/cptest/scaletest/PTO
    scaletest/testjob.out
    Priority = 0
    qtime = Tue Apr  9 18:26:32 2013
    Rerunable = False
    Resource_List.mpiprocs = 15
    Resource_List.ncpus = 240
    Resource_List.nodect = 15
    Resource_List.place = free
    Resource_List.select = 15:ncpus=16
    Resource_List.walltime = 01:00:00
    substate = 10
    Variable_List = PBS_O_SYSTEM=Linux,PBS_O_SHELL=/bin/bash,
    PBS_O_HOME=/home/usernum1,PBS_O_LOGNAME=usernum1,
    PBS_O_WORKDIR=/home/usernum1/scratch/cptest/scaletest/PTOscaletest,
    PBS_O_LANG=en_US.UTF-8,
    PBS_O_PATH=/opt/xcat/bin:/opt/xcat/sbin:/usr/lib64/qt-3.3/bin:/usr/loc
    al/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin:/opt/pbs/default/b
    in:/opt/software/python/3.3.0/bin:/opt/software/bin,
    PBS_O_MAIL=/var/spool/mail/usernum1,PBS_O_QUEUE=P_share_queue,
    PBS_O_HOST=mycluster.cluster
    comment = Not Running: Node is in an ineligible state: offline
    etime = Tue Apr  9 18:26:32 2013
    Submit_arguments = job-PTO64cell-Qnormal.6.15.1.64.4
    project = _pbs_project_default

Job Id: 68351.mycluster
    Job_Name = cell-Qnormal
    Job_Owner = usernum1@mycluster.cluster
    job_state = Q
    queue = Q_express
    server = mycluster
    Checkpoint = u
    ctime = Tue Apr  9 15:01:47 2013
    Error_Path = mycluster.cluster:/home/usernum1/scratch/cptest/scaletest/PTOs
    caletest/testjob.err
    Hold_Types = n
    Join_Path = n
    Keep_Files = n
    Mail_Points = a
    mtime = Mon Apr 22 13:13:53 2013
    Output_Path = mycluster.cluster:/home/usernum1/scratch/cptest/scaletest/PTO
    scaletest/testjob.out
    Priority = 0
    qtime = Tue Apr  9 18:26:32 2013
    Rerunable = False
    Resource_List.mpiprocs = 15
    Resource_List.ncpus = 240
    Resource_List.nodect = 15
    Resource_List.place = free
    Resource_List.select = 15:ncpus=16
    Resource_List.walltime = 01:00:00
    substate = 10
    Variable_List = PBS_O_SYSTEM=Linux,PBS_O_SHELL=/bin/bash,
    PBS_O_HOME=/home/usernum1,PBS_O_LOGNAME=usernum1,
    PBS_O_WORKDIR=/home/usernum1/scratch/cptest/scaletest/PTOscaletest,
    PBS_O_LANG=en_US.UTF-8,
    PBS_O_PATH=/opt/xcat/bin:/opt/xcat/sbin:/usr/lib64/qt-3.3/bin:/usr/loc
    al/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin:/opt/pbs/default/b
    in:/opt/software/python/3.3.0/bin:/opt/software/bin,
    PBS_O_MAIL=/var/spool/mail/usernum1,PBS_O_QUEUE=P_share_queue,
    PBS_O_HOST=mycluster.cluster
    comment = Not Running: Node is in an ineligible state: offline
    etime = Tue Apr  9 18:26:32 2013
    Submit_arguments = job-PTO64cell-Qnormal.6.15.1.64.8
    project = _pbs_project_default

Job Id: 69301.mycluster
    Job_Name = Cu-dbp
    Job_Owner = user02@mycluster.cluster
    resources_used.cpupercent = 6384
    resources_used.cput = 4090:56:03
    resources_used.mem = 13378420kb
    resources_used.ncpus = 64
    resources_used.vmem = 9866188kb
    resources_used.walltime = 64:26:16
    job_state = R
    queue = P_lsu
    server = mycluster
    Account_Name = lsu
    Checkpoint = u
    ctime = Wed Apr 10 17:10:29 2013
    depend = afterok:69299.mycluster@mycluster.cluster,
    beforeok:69302.mycluster@mycluster.cluster
    Error_Path = mycluster.cluster:/scratch/user02/QMMM-CuPhens/dbp/NOSE/RUN7/C
    u-dbp.e69301
    exec_host = b141/0*16+b142/0*16+b143/0*16+b144/0*16
    exec_vnode = (b141:ncpus=16)+(b142:ncpus=16)+(b143:ncpus=16)+(b144:ncpus=16
    )
    Hold_Types = n
    Join_Path = oe
    Keep_Files = n
    Mail_Points = a
    mtime = Sat Apr 20 01:37:01 2013
    Output_Path = mycluster.cluster:/scratch/user02/QMMM-CuPhens/dbp/NOSE/RUN7/
    Cu-dbp.o69301
    Priority = 0
    qtime = Wed Apr 10 17:10:29 2013
    Rerunable = False
    Resource_List.mpiprocs = 4
    Resource_List.ncpus = 64
    Resource_List.nodect = 4
    Resource_List.place = excl
    Resource_List.select = 4:ncpus=16
    Resource_List.walltime = 72:00:00
    stime = Sat Apr 20 01:36:59 2013
    session_id = 118473
    Shell_Path_List = /bin/tcsh
    jobdir = /home/user02
    substate = 42
    Variable_List = SSH_ASKPASS=/usr/libexec/openssh/gnome-ssh-askpass,
    PERL_BADLANG=0,KDE_IS_PRELINKED=1,PBS_O_HOME=/home/user02,
    module=() {  eval `/usr/bin/modulecmd bash $*`,},
    LESSOPEN=|/usr/bin/lesspipe.sh %s,PBS_O_LOGNAME=user02,
    SSH_CLIENT=128.178.54.94 46714 22,CVS_RSH=ssh,PBS_O_LANG=C,USER=user02,
    HOME=/home/user02,LIBGL_ALWAYS_INDIRECT=yes,
    PATH=/opt/xcat/bin:/opt/xcat/sbin:/usr/lib64/qt-3.3/bin:/usr/local/bin
    :/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin:/opt/pbs/default/bin:/op
    t/software/python/3.3.0/bin:/opt/software/bin,
    LD_LIBRARY_PATH=/opt/software/python/3.3.0/lib,
    SSH_CONNECTION=128.178.54.94 46714 128.178.209.70 22,LANG=C,
    QTLIB=/usr/lib64/qt-3.3/lib,TERM=xterm,SHELL=/bin/bash,
    QTINC=/usr/lib64/qt-3.3/include,G_BROKEN_FILENAMES=1,HISTSIZE=1000,
    PBS_O_WORKDIR=/scratch/user02/QMMM-CuPhens/dbp/NOSE/RUN7,
    PBS_O_PATH=/opt/xcat/bin:/opt/xcat/sbin:/usr/lib64/qt-3.3/bin:/usr/loc
    al/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin:/opt/pbs/default/b
    in:/opt/software/python/3.3.0/bin:/opt/software/bin,
    MANPATH=/opt/xcat/share/man:,XCATROOT=/opt/xcat,
    MODULESHOME=/usr/share/Modules,PBS_O_SYSTEM=Linux,MSM_PRODUCT=MSM,
    HOST=mycluster,MAIL=/var/spool/mail/user02,
    PBS_O_MAIL=/var/spool/mail/user02,_=/opt/pbs/default/bin/qsub,
    MODULEPATH=/etc/modulefiles:/opt/software/modulefiles:/opt/software/cs
    e-software/modulefiles,KDEDIRS=/usr,PBS_O_SHELL=/bin/bash,
    SSH_TTY=/dev/pts/55,OLDPWD=/scratch/user02/QMMM-CuPhens/dbp/NOSE/RUN6,
    LOADEDMODULES=,HISTCONTROL=ignoredups,SHLVL=1,
    PWD=/scratch/user02/QMMM-CuPhens/dbp/NOSE/RUN7,HOSTNAME=mycluster,
    MSM_HOME=/usr/local/MegaRAID Storage Manager,LOGNAME=user02,
    PBS_O_HOST=mycluster.cluster
    comment = Job run at Sat Apr 20 at 01:36 on (b141:ncpus=16)+(b142:ncpus=16)
    +(b143:ncpus=16)+(b144:ncpus=16)
    etime = Sat Apr 20 01:36:59 2013
    Submit_arguments = job.sh
    project = _pbs_project_default

Job Id: 69302.mycluster
    Job_Name = Cu-dbp
    Job_Owner = user02@mycluster.cluster
    job_state = H
    queue = P_lsu
    server = mycluster
    Account_Name = lsu
    Checkpoint = u
    ctime = Wed Apr 10 17:11:21 2013
    depend = afterok:69301.mycluster@mycluster.cluster
    Error_Path = mycluster.cluster:/scratch/user02/QMMM-CuPhens/dbp/NOSE/RUN8/C
    u-dbp.e69302
    Hold_Types = s
    Join_Path = oe
    Keep_Files = n
    Mail_Points = a
    mtime = Wed Apr 10 17:11:21 2013
    Output_Path = mycluster.cluster:/scratch/user02/QMMM-CuPhens/dbp/NOSE/RUN8/
    Cu-dbp.o69302
    Priority = 0
    qtime = Wed Apr 10 17:11:21 2013
    Rerunable = False
    Resource_List.mpiprocs = 4
    Resource_List.ncpus = 64
    Resource_List.nodect = 4
    Resource_List.place = excl
    Resource_List.select = 4:ncpus=16
    Resource_List.walltime = 72:00:00
    Shell_Path_List = /bin/tcsh
    substate = 22
    Variable_List = SSH_ASKPASS=/usr/libexec/openssh/gnome-ssh-askpass,
    PERL_BADLANG=0,KDE_IS_PRELINKED=1,PBS_O_HOME=/home/user02,
    module=() {  eval `/usr/bin/modulecmd bash $*`,},
    LESSOPEN=|/usr/bin/lesspipe.sh %s,PBS_O_LOGNAME=user02,
    SSH_CLIENT=128.178.54.94 46714 22,CVS_RSH=ssh,PBS_O_LANG=C,USER=user02,
    HOME=/home/user02,LIBGL_ALWAYS_INDIRECT=yes,
    PATH=/opt/xcat/bin:/opt/xcat/sbin:/usr/lib64/qt-3.3/bin:/usr/local/bin
    :/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin:/opt/pbs/default/bin:/op
    t/software/python/3.3.0/bin:/opt/software/bin,
    LD_LIBRARY_PATH=/opt/software/python/3.3.0/lib,
    SSH_CONNECTION=128.178.54.94 46714 128.178.209.70 22,LANG=C,
    QTLIB=/usr/lib64/qt-3.3/lib,TERM=xterm,SHELL=/bin/bash,
    QTINC=/usr/lib64/qt-3.3/include,G_BROKEN_FILENAMES=1,HISTSIZE=1000,
    PBS_O_WORKDIR=/scratch/user02/QMMM-CuPhens/dbp/NOSE/RUN8,
    PBS_O_PATH=/opt/xcat/bin:/opt/xcat/sbin:/usr/lib64/qt-3.3/bin:/usr/loc
    al/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin:/opt/pbs/default/b
    in:/opt/software/python/3.3.0/bin:/opt/software/bin,
    MANPATH=/opt/xcat/share/man:,XCATROOT=/opt/xcat,
    MODULESHOME=/usr/share/Modules,PBS_O_SYSTEM=Linux,MSM_PRODUCT=MSM,
    HOST=mycluster,MAIL=/var/spool/mail/user02,
    PBS_O_MAIL=/var/spool/mail/user02,_=/opt/pbs/default/bin/qsub,
    MODULEPATH=/etc/modulefiles:/opt/software/modulefiles:/opt/software/cs
    e-software/modulefiles,KDEDIRS=/usr,PBS_O_SHELL=/bin/bash,
    SSH_TTY=/dev/pts/55,OLDPWD=/scratch/user02/QMMM-CuPhens/dbp/NOSE/RUN7,
    LOADEDMODULES=,HISTCONTROL=ignoredups,SHLVL=1,
    PWD=/scratch/user02/QMMM-CuPhens/dbp/NOSE/RUN8,HOSTNAME=mycluster,
    MSM_HOME=/usr/local/MegaRAID Storage Manager,LOGNAME=user02,
    PBS_O_HOST=mycluster.cluster
    Submit_arguments = job.sh
    project = _pbs_project_default

Job Id: 74164.mycluster
    Job_Name = u-100-l-96.job
    Job_Owner = user3@mycluster.cluster
    resources_used.cpupercent = 3889
    resources_used.cput = 343:11:42
    resources_used.mem = 1824176kb
    resources_used.ncpus = 32
    resources_used.vmem = 3796376kb
    resources_used.walltime = 10:45:13
    job_state = R
    queue = Q_normal
    server = mycluster
    Checkpoint = u
    ctime = Fri Apr 12 15:21:55 2013
    depend = afterany:74163.mycluster@mycluster.cluster,
    beforeany:74165.mycluster@mycluster.cluster
    Error_Path = mycluster.cluster:/scratch/user3/ubiquitin/100gL/starting-from
    -left/production/u-100-l-96.job.e74164
    exec_host = b270/0*16+b275/0*16
    exec_vnode = (b270:ncpus=16)+(b275:ncpus=16)
    Hold_Types = n
    Join_Path = oe
    Keep_Files = n
    Mail_Points = abe
    Mail_Users = enrico.user3@epfl.ch
    mtime = Mon Apr 22 07:17:36 2013
    Output_Path = mycluster.cluster:/scratch/user3/ubiquitin/100gL/starting-fro
    m-left/production/u-100-l-96.job.o74164
    Priority = 0
    qtime = Fri Apr 12 15:21:55 2013
    Rerunable = False
    Resource_List.mpiprocs = 32
    Resource_List.ncpus = 32
    Resource_List.nodect = 2
    Resource_List.place = excl
    Resource_List.select = 2:ncpus=16:mpiprocs=16
    Resource_List.walltime = 24:00:00
    stime = Mon Apr 22 07:17:36 2013
    session_id = 14147
    jobdir = /home/user3
    substate = 42
    Variable_List = PBS_O_SYSTEM=Linux,PBS_O_SHELL=/bin/bash,
    PBS_O_HOME=/home/user3,PBS_O_LOGNAME=user3,
    PBS_O_WORKDIR=/scratch/user3/ubiquitin/100gL/starting-from-left/produc
    tion,PBS_O_LANG=en_US.utf8,
    PBS_O_PATH=/opt/pbs/default/sbin/:/home/bovigny/bin:/opt/xcat/bin:/opt
    /xcat/sbin:/opt/xcat/bin:/opt/xcat/sbin:/usr/lib64/qt-3.3/bin:/usr/loca
    l/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin:/opt/pbs/default/bi
    n:/opt/software/python/3.3.0/bin:/opt/software/bin:/opt/pbs/default/bin
    :/opt/software/python/3.3.0/bin:/opt/software/bin,
    PBS_O_MAIL=/var/spool/mail/user3,PBS_O_QUEUE=P_share_queue,
    PBS_O_HOST=mycluster.cluster
    comment = Job run at Mon Apr 22 at 07:17 on (b270:ncpus=16)+(b275:ncpus=16)
    
    etime = Mon Apr 22 07:17:34 2013
    Submit_arguments = -W depend=afterany:74163 u-100-l-96.job
    project = _pbs_project_default

Job Id: 74165.mycluster
    Job_Name = u-100-l-97.job
    Job_Owner = user3@mycluster.cluster
    job_state = H
    queue = Q_normal
    server = mycluster
    Checkpoint = u
    ctime = Fri Apr 12 15:22:01 2013
    depend = afterany:74164.mycluster@mycluster.cluster,
    beforeany:74166.mycluster@mycluster.cluster
    Error_Path = mycluster.cluster:/scratch/user3/ubiquitin/100gL/starting-from
    -left/production/u-100-l-97.job.e74165
    Hold_Types = s
    Join_Path = oe
    Keep_Files = n
    Mail_Points = abe
    Mail_Users = enrico.user3@epfl.ch
    mtime = Fri Apr 12 15:22:07 2013
    Output_Path = mycluster.cluster:/scratch/user3/ubiquitin/100gL/starting-fro
    m-left/production/u-100-l-97.job.o74165
    Priority = 0
    qtime = Fri Apr 12 15:22:01 2013
    Rerunable = False
    Resource_List.mpiprocs = 32
    Resource_List.ncpus = 32
    Resource_List.nodect = 2
    Resource_List.place = excl
    Resource_List.select = 2:ncpus=16:mpiprocs=16
    Resource_List.walltime = 24:00:00
    substate = 22
    Variable_List = PBS_O_SYSTEM=Linux,PBS_O_SHELL=/bin/bash,
    PBS_O_HOME=/home/user3,PBS_O_LOGNAME=user3,
    PBS_O_WORKDIR=/scratch/user3/ubiquitin/100gL/starting-from-left/produc
    tion,PBS_O_LANG=en_US.utf8,
    PBS_O_PATH=/opt/pbs/default/sbin/:/home/bovigny/bin:/opt/xcat/bin:/opt
    /xcat/sbin:/opt/xcat/bin:/opt/xcat/sbin:/usr/lib64/qt-3.3/bin:/usr/loca
    l/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin:/opt/pbs/default/bi
    n:/opt/software/python/3.3.0/bin:/opt/software/bin:/opt/pbs/default/bin
    :/opt/software/python/3.3.0/bin:/opt/software/bin,
    PBS_O_MAIL=/var/spool/mail/user3,PBS_O_QUEUE=P_share_queue,
    PBS_O_HOST=mycluster.cluster
    Submit_arguments = -W depend=afterany:74164 u-100-l-97.job
    project = _pbs_project_default

"""

    class TestParserQstat(unittest.TestCase):
        """
        Tests to verify if teh function _parse_joblist_output behave correctly
        The tests is done parsing a string defined above, to be used offline
        """
        
        def test_parse_common_joblist_output(self):
            """
            Test whether _parse_joblist can parse the qstat -f output
            """
            s = PbsproScheduler()
            
            retval = 0
            stdout = text_qstat_f_to_test
            stderr = ''
            
            job_list = s._parse_joblist_output(retval, stdout, stderr)

            # The parameters are hard coded in the text to parse
            job_on_cluster = 6
            job_parsed = len(job_list)
            self.assertEquals(job_parsed, job_on_cluster)

            job_running = 2
            job_running_parsed = len([ j for j in job_list if j.jobState \
                                       and j.jobState == jobStates.RUNNING ])
            self.assertEquals(job_running,job_running_parsed)

            job_held = 2
            job_held_parsed = len([ j for j in job_list if j.jobState \
                                       and j.jobState == jobStates.QUEUED_HELD ])
            self.assertEquals(job_held,job_held_parsed)

            job_queued = 2
            job_queued_parsed = len([ j for j in job_list if j.jobState \
                                       and j.jobState == jobStates.QUEUED ])
            self.assertEquals(job_queued,job_queued_parsed)

            running_users = ['user02','user3']
            parsed_running_users = [ j.jobOwner for j in job_list if j.jobState \
                                     and j.jobState == jobStates.RUNNING ]
            self.assertEquals( set(running_users) , set(parsed_running_users) )

            running_jobs = ['69301.mycluster','74164.mycluster']
            parsed_running_jobs = [ j.jobId for j in job_list if j.jobState \
                                     and j.jobState == jobStates.RUNNING ]
            self.assertEquals( set(running_jobs) , set(parsed_running_jobs) )
            
            for j in job_list:
                if j.allocatedNodes:
                    num_nodes = 0
                    num_cores = 0
                    for n in j.allocatedNodes:
                        num_nodes += 1
                        num_cores += n.numCores
                        
                    self.assertTrue( j.numNodes==num_nodes )
                    self.assertTrue( j.numCores==num_cores )
            # TODO : parse the env_vars
        def test_parse_with_error_retval(self):
            """
            The qstat -f command has received a retval != 0
            """
            s = PbsproScheduler()            
            retval = 1
            stdout = text_qstat_f_to_test
            stderr = ''
            # Disable logging to avoid excessive output during test
            logging.disable(logging.ERROR)
            with self.assertRaises(SchedulerError):
                job_list = s._parse_joblist_output(retval, stdout, stderr)
            # Reset logging level
            logging.disable(logging.NOTSET)

#        def test_parse_with_error_stderr(self):
#            """
#            The qstat -f command has received a stderr
#            """
#            s = PbsproScheduler()            
#            retval = 0
#            stdout = text_qstat_f_to_test
#            stderr = 'A non empty error message'
#            # TODO : catch the logging error
#            job_list = s._parse_joblist_output(retval, stdout, stderr)
#            #            print s._logger._log, dir(s._logger._log),'!!!!'

    class TestSubmitScript(unittest.TestCase):
        def test_submit_script(self):
            """
            """
            from aida.scheduler.datastructures import JobTemplate
            s = PbsproScheduler()

            job_tmpl = JobTemplate()
            job_tmpl.argv = ["mpirun", "-np", "23", "pw.x", "-npool", "1"]
            job_tmpl.stdinName = 'aida.in'
            job_tmpl.numNodes = 1
            job_tmpl.uuid = str(uuid.uuid4())
            job_tmpl.maxWallclockSeconds = 24 * 3600 
    
            submit_script_text = s.get_submit_script(job_tmpl)

            self.assertTrue( '#PBS -r n' in submit_script_text )
            self.assertTrue( submit_script_text.startswith('#!/bin/bash') )
            self.assertTrue( '#PBS -l walltime=24:00:00' in submit_script_text )
            self.assertTrue( '#PBS -l select=1' in submit_script_text )
            self.assertTrue( "'mpirun' '-np' '23' 'pw.x' '-npool' '1'" + \
                             " < 'aida.in'" in submit_script_text )
            
    unittest.main()
