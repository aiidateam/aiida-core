import aida.scheduler
from aida.common.utils import escape_for_bash
from aida.scheduler import SchedulerError
from aida.scheduler.datastructures import JobInfo

class PbsproScheduler(aida.scheduler.Scheduler):
    """
    PBSPro implementation of the scheduler functions.
    """
    _logger = aida.scheduler.Scheduler._logger.getChild('pbspro')

    @classmethod
    def _get_joblist_command(cls,jobs=None,user=None): 
        """
        The command to report full information on existing jobs.
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
        if not strip(stderr):
            self.logger.error("Warning in _parse_joblist_output, non-empty "
                "stderr={}".format(stderr))

        jobdata_raw = [] # will contain raw data parsed from qstat output
        # Get raw data and split in lines
        for line_num, l in enumerate(stdout.split('\n'),start=1):
            # Each new job stanza starts with the string 'Job Id:': I 
            # create a new item in the jobdata_raw list
            if l.startswith('Job Id:'):
                jobdata_raw.append(
                    {'id': l.split(sep=':',maxsplit=1)[1]).strip(),
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
                        #raise ValueError("I did not find the header for the first job")
                        self.logger.warning("I found some text before the "
                        "first job: {}".format(l))



#############################################################################
# CONTINUE TO FIX THE ROUTINE FROM HERE
#############################################################################



                    else:
                        if l.startswith(' '):
                            # If it starts with a space, it is a new field
                            jobdata_raw[-1]['lines'].append(l)
                        elif l.startswith('\t'):
                            # If a line starts with a TAB,
                            # I append to the previous string 
                            # stripping the TAB
                            if not jobdata_raw[-1]['lines']:
                                raise ValueError("Line %s is the first line of the job, but it starts with a TAB! (%s)" % (line_num, l))
                            jobdata_raw[-1]['lines'][-1] += l[1:]
                        else:
                            raise ValueError("Wrong starting character at line %s! (%s)" % (line_num, l))

        # Create dictionary and parse specific fields
        job_data = {}
        for job in jobdata_raw:
            job_data[job['id']] = {}
            this_job_data = {i.split('=')[0].strip().lower(): "=".join(i.split('=')[1:]).lstrip() for i in job['lines']}
            job_data[job['id']]['status'] = _map_status_pbspro.get(this_job_data['job_state'],'unknown')
            job_data[job['id']]['queue'] = this_job_data['queue']
            job_data[job['id']]['num_nodes'] = this_job_data['resource_list.nodect']
            job_data[job['id']]['num_cores'] = this_job_data.get('resource_list.ncpus',None)
            job_data[job['id']]['walltime'] = this_job_data['resource_list.walltime']
            job_data[job['id']]['user'] = this_job_data['job_owner'].split('@')[0]
            job_data[job['id']]['title'] = this_job_data['job_name']
            job_data[job['id']]['raw'] = this_job_data


        return job_data

      
    def _parse_submit_output(self, retval, stdout, stderr):
        """
        Parse the output of the submit command, as returned by executing the
        command returned by _get_submit_command command.
        
        To be implemented by the plugin.
        
        Return a string with the JobID.
        """
        if retval != 0:
            cls._logger.error("Error in _parse_submit_output: retval={}; "
                "stdout={}; stderr={}".format(retval, stdout, stderr))
            raise SchedulerError("Error during submission")

        if stderr.strip():
            cls._logger.warning("in _parse_submit_output for {}: :
                "there was some text in stderr: {}".format(
                    str(self.transport),stderr))
        
        return stdout.strip()

#if __name__ == '__main__':
#    import logging
#    PbsproScheduler._logger.setLevel(logging.DEBUG)
#    PbsproScheduler._get_joblist_command(user='pi',jobs=['8392','sdfd'])
