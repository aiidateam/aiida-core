"""
Plugin for PBSPro.
This has been tested on PBSPro v. 12.
"""

import aida.scheduler
from aida.common.utils import escape_for_bash
from aida.scheduler import SchedulerError, SchedulerParsingError
from aida.scheduler.datastructures import JobInfo, jobStates, NodeInfo

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



class PbsproScheduler(aida.scheduler.Scheduler):
    """
    PBSPro implementation of the scheduler functions.

    TODO: implement __unicode__ and __str__ methods.
    """
    _logger = aida.scheduler.Scheduler._logger.getChild('pbspro')

    @classmethod
    def _get_joblist_command(cls,jobs=None,user=None): 
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
            
        cls._logger.debug("qstat command: {}".format(command))
        return command

    @classmethod
    def _get_submit_command(cls, submit_script):
        """
        Return the string to execute to submit a given script.
        
        Args:
            submit_script: the path of the submit script relative to the working
                directory.
                IMPORTANT: submit_script should be already escaped.
        """
        return 'qsub {}'.format(submit_script)
      
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


            # TODO: check if the assumption
            #       submissionMachine == raw_data['server'] is correct
            try:
                this_job.submissionMachine = raw_data['server']
            except KeyError:
                # No 'server' found; I skip
                pass

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
                        node.machineName, data = exec_host.split('/')
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
                    this_job.allocatedMachines = exec_host_list
                except Exception as e:
                    self.logger.debug("Problem parsing the machine names, I "
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
                this_job.numMachines = int(raw_data['resource_list.nodect'])
            except KeyError:
                self.logger.debug("No 'resource_list.nodect' field for job id "
                    "{}".format(this_job.jobId))
            except IndexError:
                self.logger.warning(";resource_list.nodect' is not an integer "
                                    "({}) for job id {}!".format(
                        raw_data['resource_list.nodect'],
                        this_job.jobId))

            # TODO here: if allocatedMachines is not None, check the length
            # and compare with numMachines

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
            raise SchedulerError("Error during submission")

        if stderr.strip():
            self.logger.warning("in _parse_submit_output for {}: "
                "there was some text in stderr: {}".format(
                    str(self.transport),stderr))
        
        return stdout.strip()

if __name__ == '__main__':
    import logging
    import paramiko
    from aida.transport import Transport
    from aida.common.pluginloader import load_plugin

    SshTransport = load_plugin(Transport, 'aida.transport.plugins', 'ssh')

    PbsproScheduler._logger.setLevel(logging.DEBUG)
#    PbsproScheduler._get_joblist_command(user='pi',jobs=['8392','sdfd'])
    with SshTransport('bellatrix.epfl.ch', #username='cepellot',
                      key_policy=paramiko.AutoAddPolicy()) as t:
        s = PbsproScheduler(t)
        job_list = s.getJobs()
        for j in job_list:
            if j.jobState and j.jobState == jobStates.RUNNING:
                print "{} of {} with status {}".format(
                    j.jobId, j.jobOwner, j.jobState)
                if j.allocatedMachines:
                    num_nodes = 0
                    num_cores = 0
                    for n in j.allocatedMachines:
#                        print "  -> node {}, index {}, cores {}".format(
#                            n.machineName, n.jobIndex, n.numCores)
                        num_nodes += 1
                        num_cores += n.numCores
                       
                    if j.numMachines != num_nodes:
                        print "WARNING! expected nodes = {}, found = {}".format(
                            j.numMachines, num_nodes)
                    if j.numCores != num_cores:
                        print "WARNING! expected cores = {}, found = {}".format(
                            j.numCores, num_cores)
                        
