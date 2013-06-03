"""
Plugin for PBSPro.
This has been tested on PBSPro v. 12.
"""
from __future__ import division
import aiida.scheduler
from aiida.common.utils import escape_for_bash
from aiida.scheduler import SchedulerError, SchedulerParsingError
from aiida.scheduler.datastructures import (
    JobInfo, job_states, MachineInfo)

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
    'B': job_states.RUNNING,
    'E': job_states.RUNNING, # If exiting, for our purposes it is still running
    'F': job_states.DONE,
    'H': job_states.QUEUED_HELD,
    'M': job_states.UNDETERMINED, # TODO: check if this is ok?
    'Q': job_states.QUEUED,
    'R': job_states.RUNNING,
    'S': job_states.SUSPENDED,
#    'T': job_states., # TODO: what to do here?
    'U': job_states.SUSPENDED,
    'W': job_states.QUEUED,
    'X': job_states.DONE,
    }



class PbsproScheduler(aiida.scheduler.Scheduler):
    """
    PBSPro implementation of the scheduler functions.

    TODO: implement __unicode__ and __str__ methods.
    """
    _logger = aiida.scheduler.Scheduler._logger.getChild('pbspro')


    def _get_joblist_command(self,jobs=None): 
        """
        The command to report full information on existing jobs.

        TODO: in the case of job arrays, decide what to do (i.e., if we want
              to pass the -t options to list each subjob).
        """
        command = 'qstat -f'
        if jobs:
            if isinstance(jobs, basestring):
                command += ' {}'.format(escape_for_bash(jobs))
            else:
                try:
                    command += ' {}'.format(' '.join(escape_for_bash(j) for j in jobs))
                except TypeError:
                    raise TypeError(
                        "If provided, the 'jobs' variable must be a string or a list of strings")
            
        self.logger.debug("qstat command: {}".format(command))
        return command

    def _get_detailed_jobinfo_command(self,jobid):
        """
        Return the command to run to get the detailed information on a job,
        even after the job has finished.

        The output text is just retrieved, and returned for logging purposes.
        """
        return "tracejob -v {}".format(escape_for_bash(jobid))

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
        if job_tmpl.submit_as_hold:
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
        if job_tmpl.email_on_started:
            email_events += "b"
        if job_tmpl.email_on_terminated:
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
            
        if job_tmpl.job_name:
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
            job_title = re.sub(r'[^a-zA-Z0-9_.-]+', '', job_tmpl.job_name)

            # prepend a 'j' (for 'job') before the string if the string
            # is now empty or does not start with a valid charachter
            if not job_title or (
                job_title[0] not in string.letters + string.digits):
                job_title = 'j' + job_title
            
            # Truncate to the first 15 characters 
            # Nothing is done if the string is shorter.
            job_title = job_title[:15]
            
            lines.append("#PBS -N {}".format(job_title))
            
        if job_tmpl.sched_output_path:
            lines.append("#PBS -o {}".format(job_tmpl.sched_output_path))

        if job_tmpl.sched_join_files:
            # from qsub man page:
            # 'oe': Standard error and standard output are merged  into 
            #       standard output
            # 'eo': Standard error and standard output are merged  into 
            #       standard error
            # 'n' : Standard error and standard output are not merged (default)
            lines.append("#PBS -j oe")
            if job_tmpl.sched_error_path:
                self.logger.info(
                    "sched_join_files is True, but sched_error_path is set in "
                    "PBSPro script; ignoring sched_error_path")
        else:
            if job_tmpl.sched_error_path:
                lines.append("#PBS -e {}".format(job_tmpl.sched_error_path))

        if job_tmpl.queue_name:
            lines.append("#PBS -q {}".format(job_tmpl.queue_name))
            
        if job_tmpl.priority:
            # Priority of the job.  Format: host-dependent integer.  Default:
            # zero.   Range:  [-1024,  +1023] inclusive.  Sets job's Priority
            # attribute to priority.
            # TODO: Here I expect that priority is passed in the correct PBSPro
            # format. To fix.
            lines.append("#PBS -p {}".format(job_tmpl.priority))

        
        if not job_tmpl.num_machines:
            raise ValueError("num_machines is required for the PBSPro scheduler "
                             "plugin")
        select_string = "select={}".format(job_tmpl.num_machines)
        if job_tmpl.num_cpus_per_machine:
            select_string += ":ncpus={}".format(job_tmpl.num_cpus_per_machine)

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
            lines.append("#PBS -l walltime={:02d}:{:02d}:{:02d}".format(
                hours, minutes, seconds))

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
            select_string += ":mem={}kb".format(virtualMemoryKb)
                
        lines.append("#PBS -l {}".format(select_string))

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
        # I don't raise because if I pass a list of jobs, I get a non-zero status
        # if one of the job is not in the list anymore

        # retval should be zero
        #if retval != 0:
            #self.logger.warning("Error in _parse_joblist_output: retval={}; "
            #    "stdout={}; stderr={}".format(retval, stdout, stderr))


        # issue a warning if there is any stderr output
        # but I strip lines containing "Unknown Job Id", that happens
        # also when I ask for a calculation that has finished
        filtered_stderr = '\n'.join(l for l in stderr.split('\n') if "Unknown Job Id" not in l)
        if filtered_stderr.strip():
            self.logger.warning("Warning in _parse_joblist_output, non-empty "
                "(filtered) stderr='{}'".format(filtered_stderr))
            if retval != 0:
                raise SchedulerError(
                    "Error during qstat parsing (_parse_joblist_output function)")

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
                        # only before the first job. 
                        raise SchedulerParsingError("I did not find the header for the first job")
                        #self.logger.warning("I found some text before the "
                        #"first job: {}".format(l))
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
            this_job.job_id = job['id']

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

            # I believe that exit_status and terminating_signal cannot be
            # retrieved from the qstat -f output.
            
            # I wrap calls in try-except clauses to avoid errors if a field
            # is missing
            try:
                this_job.title = raw_data['job_name']
            except KeyError:
                self.logger.debug("No 'job_name' field for job id "
                    "{}".format(this_job.job_id))

            try:
                this_job.annotation = raw_data['comment']
            except KeyError:
                # Many jobs do not have a comment; I do not complain about it.
                pass
                #self.logger.debug("No 'comment' field for job id {}".format(
                #    this_job.job_id))
            
            try:
                job_state_string = raw_data['job_state']
                try:
                    this_job.job_state = _map_status_pbspro[job_state_string]
                except KeyError:
                    self.logger.warning("Unrecognized job_state '{}' for job "
                                        "id {}".format(job_state_string,
                                                       this_job.job_id))
                    this_job.job_state = job_states.UNDETERMINED
            except KeyError:
                self.logger.debug("No 'job_state' field for job id {}".format(
                    this_job.job_id))
                this_job.job_state = job_states.UNDETERMINED

            try:
                this_job.job_substate = raw_data['substate']
            except KeyError:
                self.logger.debug("No 'substate' field for job id {}".format(
                    this_job.job_id))

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
                        node = MachineInfo()
                        node.name, data = exec_host.split('/')
                        data = data.split('*')
                        if len(data) == 1:
                            node.jobIndex = int(data[0])
                            node.num_cpus = 1
                        elif len(data) == 2:
                            node.jobIndex = int(data[0])
                            node.num_cpus = int(data[1])
                        else:
                            raise ValueError("Wrong number of pieces: {} "
                                             "instead of 1 or 2 in exec_hosts: "
                                             "{}".format(len(data), exec_hosts))
                        exec_host_list.append(node)
                    this_job.allocated_machines = exec_host_list
                except Exception as e:
                    self.logger.debug("Problem parsing the node names, I "
                                      "got Exception {} with message {}; "
                                      "exec_hosts was {}".format(
                            str(type(e)), e.message, exec_hosts))

            try:
                # I strip the part after the @: is this always ok?
                this_job.job_owner = raw_data['job_owner'].split('@')[0]
            except KeyError:
                self.logger.debug("No 'job_owner' field for job id {}".format(
                    this_job.job_id))

            try:
                this_job.num_cpus = int(raw_data['resource_list.ncpus'])
                # TODO: understand if this is the correct field also for
                #       multithreaded (OpenMP) jobs.
            except KeyError:
                self.logger.debug("No 'resource_list.ncpus' field for job id "
                    "{}".format(this_job.job_id))
            except ValueError:
                self.logger.warning("'resource_list.ncpus' is not an integer "
                                    "({}) for job id {}!".format(
                        raw_data['resource_list.ncpus'],
                        this_job.job_id))

            try:
                this_job.num_machines = int(raw_data['resource_list.nodect'])
            except KeyError:
                self.logger.debug("No 'resource_list.nodect' field for job id "
                    "{}".format(this_job.job_id))
            except ValueError:
                self.logger.warning("'resource_list.nodect' is not an integer "
                                    "({}) for job id {}!".format(
                        raw_data['resource_list.nodect'],
                        this_job.job_id))

            # Double check of redundant info
            if (this_job.allocated_machines is not None and 
                this_job.num_machines is not None):
                if len(this_job.allocated_machines) != this_job.num_machines:
                    self.logger.error("The length of the list of allocated "
                                      "nodes ({}) is different from the "
                                      "expected number of nodes ({})!".format(
                        len(this_job.allocated_machines), this_job.num_machines))

            try:
                this_job.queue_name = raw_data['queue']
            except KeyError:
                self.logger.debug("No 'queue' field for job id "
                    "{}".format(this_job.job_id))

            try:
                this_job.RequestedWallclockTime = (self._convert_time(
                    raw_data['resource_list.walltime']))
            except KeyError:
                self.logger.debug("No 'resource_list.walltime' field for "
                    "job id {}".format(this_job.job_id))
            except ValueError:
                self.logger.warning("Error parsing 'resource_list.walltime' "
                    "for job id {}".format(this_job.job_id))

            try:
                this_job.wallclock_time_seconds = (self._convert_time(
                    raw_data['resources_used.walltime']))
            except KeyError:
                # May not have started yet
                pass
            except ValueError:
                self.logger.warning("Error parsing 'resources_used.walltime' "
                    "for job id {}".format(this_job.job_id))

            try:
                this_job.cpu_time = (self._convert_time(
                    raw_data['resources_used.cput']))
            except KeyError:
                # May not have started yet
                pass
            except ValueError:
                self.logger.warning("Error parsing 'resources_used.cput' "
                    "for job id {}".format(this_job.job_id))

            #
            # ctime: The time that the job was created
            # mtime: The time that the job was last modified, changed state,
            #        or changed locations. 
            # qtime: The time that the job entered the current queue
            # stime: The time when the job started execution.  
            # etime: The time that the job became eligible to run, i.e. in a
            #        queued state while residing in an execution queue.

            try:
                this_job.submission_time = self._parse_time_string(
                    raw_data['ctime'])
            except KeyError:
                self.logger.debug("No 'ctime' field for job id "
                    "{}".format(this_job.job_id))
            except ValueError:
                self.logger.warning("Error parsing 'ctime' for job id "
                    "{}".format(this_job.job_id))

            try:
                this_job.dispatch_time = self._parse_time_string(
                    raw_data['stime'])
            except KeyError:
                # The job may not have been started yet
                pass
            except ValueError:
                self.logger.warning("Error parsing 'stime' for job id "
                    "{}".format(this_job.job_id))
            
            # TODO: see if we want to set also finish_time for finished jobs,
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


    def _parse_time_string(self,string,fmt='%a %b %d %H:%M:%S %Y'):
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

