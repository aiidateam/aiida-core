import aida.scheduler
from aida.common.utils import escape_for_bash
from aida.scheduler import SchedulerError

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
        
        TODO: IMPLEMENT!

        Return a list of JobInfo objects, one of each job, 
        each with at least its default params implemented.
        """
        raise NotImplementedError
      
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