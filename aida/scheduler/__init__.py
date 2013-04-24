import aida.common
from aida.common.utils import escape_for_bash
from aida.common.exceptions import AidaException
from aida.scheduler.datastructures import JobTemplate

# TODO: define some high-level priority values to be used independent
#       of the scheduler plugin

class SchedulerError(AidaException):
    pass

class SchedulerParsingError(SchedulerError):
    pass

class Scheduler(object):
    """
    Note: probably we want to inherit from some more reasonable class.

    Base class for all schedulers.
    
    Note: _parse functions are not class methods because in this way they can
          access the instance information (e.g. the transport info) for useful debug
          messages. Instead, the functions that only generate the commands are 
          class methods.
    """
    _logger = aida.common.aidalogger.getChild('scheduler')
    
    def __init__(self):
        self._transport = None

    def set_transport(self,transport):
        """
        Set the transport to be used to query the machine or to submit scripts.
        This class assumes that the transport is open and active.
        """
        self._transport = transport        

    @property
    def logger(self):
        """
        Return the internal logger
        """
        try:
            return self._logger
        except AttributeError:
            raise InternalError("No self._logger configured for {}!")

    def _get_submit_script(self, calc_info):
        """
        Return the submit script as a string.
        calc_info of type aida.managers.job.calcinfo.CalcInfo
        
        This must be implemented by the plugin subclass. The plugin will
        typically call the _get_run_line method implemented in this
        abstract class, that should be general enough. Nothing avoid to customize it,
        if really needed.

        TODO: understand if, in the future, we want to pass more
        than one calculation, e.g. for job arrays.

        The plugin returns something like

        #!/bin/bash <- this shebang line could be configurable in the future
        scheduler_dependent stuff to choose numnodes, numcores, walltime, ...
        prepend_computer [also from calcinfo, joined with the following?]
        prepend_code [from calcinfo]
        in the future: environment_variables [from calcinfo, possibly,
            and from scheduler_requirements e.g. for OpenMP? or maybe
            the openmp part is better managed in the scheduler_dependent
            part above since it will be machine-dependent]
        output of _get_script_main_content
        postpend_code
        postpend_computer
        
        TODO: improve, generalize, depending on what we define for calc_info!
        """
        empty_line = ""

        shebang = "#!/bin/bash"

        job_tmpl = JobTemplate()
        job_tmpl.submitAsHold = False
        # From the PBSPro documentation (man qrerun):
        # To rerun a job is to kill it and requeue it in the execution
        # queue from which it was run
        job_tmpl.rerunnable = False     # TODO fix, read from job_info
        job_tmpl.jobEnvironment = {}    # TODO fix, read from job_info
                                        # TODO: set email, emailOn...
        if calc_info.uuid:
            job_tmpl.jobName = 'aida-{}'.format(calc_info.uuid) 
        else:
            job_tmpl.jobName = 'aidajob'

        # TODO: different behavior? May be changed by calc_info?
        job_tmpl.schedOutputPath = 'scheduler-stdout.txt'
        job_tmpl.schedErrorPath = 'scheduler-stderr.txt'
        job_tmpl.schedJoinFiles = False

        job_tmpl.queueName = calc_info.queueName

        job_tmpl.numNodes = calc_info.numNodes
        job_tmpl.numCpusPerNode = calc_info.numCpusPerNode
        job_tmpl.priority = calc_info.priority

        job_tmpl.resourceLimits = calc_info.resourceLimits

        # I fill the list with the lines, and finally join them and return
        script_lines = []
        script_lines.append(shebang)
        script_lines.append(empty_line)
        
        script_lines.append(self._get_submit_script_header(job_tmpl))
        script_lines.append(empty_line)

        if calc_info.prependText:
            script_lines.append(calc_info.prependText)
            script_lines.append(empty_line)

        script_lines.append(self._get_run_line(
                calc_info.argv, calc_info.stdinName,
                calc_info.stdoutName, calc_info.stderrName,
                calc_info.joinFiles))
        script_lines.append(empty_line)

        if calc_info.appendText:
            script_lines.append(calc_info.appendText)
            script_lines.append(empty_line)

        return "\n".join(script_lines)
        

    def _get_submit_script_header(self, job_tmpl):
        """
        Return the submit script header, using the parameters from the
        job_tmpl.

        Args:
           job_tmpl: an JobTemplate instance with relevant parameters set.
        """
        raise NotImplementedError

    @classmethod
    def _get_run_line(cls, argv, stdin_name, stdout_name, stderr_name, join_files):
        """
        Return a string with the line to execute a specific code with specific arguments.
        
        Args:  
            argv: an array with the executable and the command line arguments.
                  The first argument is the executable. This should contain everything,
                  including the mpirun command etc.
            stdin_name: the filename to be used as stdin, relative to the working dir,
                        or None if no stdin redirection is required.
            stdout_name: the filename to be used to store the standard output,
                         relative to the working dir,
                         or None if no stdout redirection is required.
            stderr_name: the filename to be used to store the standard error,
                         relative to the working dir,
                         or None if no stderr redirection is required.
            join_files: if True, stderr is redirected to stdout; the value of 
                        stderr_name is ignored.
        
        Return a string with the following format:
        [executable] [args] {[ < stdin ]} {[ < stdout ]} {[2>&1 | 2> stderr]}
        """
        command_to_exec_list = []
        for arg in argv:
            command_to_exec_list.append(escape_for_bash(arg))
        command_to_exec = " ".join(command_to_exec_list)
        
        stdin_str = "< {}".format(
            escape_for_bash(stdin_name)) if stdin_name else ""
        stdout_str = "> {}".format(
            escape_for_bash(stdout_name)) if stdout_name else ""
        if join_files:
            stderr_str = "2>&1"
        else:
            stderr_str = "2> {}".format(
                escape_for_bash(stderr_name)) if stderr_name else ""
            
        output_string= ("{} {} {} {}".format(
                       command_to_exec,
                       stdin_str, stdout_str, stderr_str))
                       
        cls._logger.debug('_get_run_line output: {}'.format(output_string))
        return output_string
    
    @classmethod
    def _get_joblist_command(cls,jobs=None,user=None):
        """
        Return a list with the qsub (or equivalent) command to run + 
        required parameters to get the most complete description possible;
        the format will be the one used by the parse_queue_output.

        Must be implemented in the plugin. 
        Args:
            jobs: either None to get a list of all jobs in the machine, or a list 
                  of jobs.
            user: a string with the username to filter, or None (default) for all users.
    
        TODO: specify here how the filters should work, to have an API that is
              plugin-independent.
        """
        raise NotImplementedError

    def _parse_joblist_output(self, retval, stdout, stderr):
        """
        Parse the queue output string, as returned by executing the
        command returned by _get_joblist_command command.
        
        To be implemented by the plugin.
        
        Return a list of JobInfo objects, one of each job, 
        each with at least its default params implemented.
        """
        raise NotImplementedError
        
    def getJobs(self, jobs=None, user=None, as_dict=False):
        """
        Get the list of jobs and return it.
        
        Typically, this function does not need to be modified by the plugins.
        
        Args:
            jobs: a list of jobs to check; only these are checked
            user: only jobs belonging to a given user are checked
            as_dict: if False (default), a list of JobInfo objects is returned. If
                True, a dictionary is returned, having as key the jobId and as value the
                JobInfo object.
        """
        retval, stdout, stderr = self.transport.exec_command_wait(
            self._get_joblist_command(jobs=jobs, user=user))
        
        joblist = self._parse_joblist_output(retval, stdout, stderr)
        if as_dict:
            jobdict = {j.jobId: j for j in joblist}
            if None in jobdict:
                raise SchedulerError("Found at least a job without jobid")
            return jobdict
        else:
            return joblist

    @property
    def transport(self):
        if self._transport is None:
            raise SchedulerError("Use the set_transport function to set the "
                                 "transport for the scheduler first.")
        else:
            return self._transport
        
    @classmethod
    def _get_submit_command(cls, submit_script):
        """
        Return the string to execute to submit a given script.
        
        Args:
            submit_script: the path of the submit script relative to the working
                directory. 
                IMPORTANT: submit_script should be already escaped.
        
        To be implemented by the plugin.
        """
        raise NotImplementedError
        
    def _parse_submit_output(self, retval, stdout, stderr):
        """
        Parse the output of the submit command, as returned by executing the
        command returned by _get_submit_command command.
        
        To be implemented by the plugin.
        
        Return a string with the JobID.
        """
        raise NotImplementedError
        
    def submit_from_script(self, working_directory, submit_script):
        """
        Goes in the working directory and submits the submit_script.
        
        Return a string with the JobID in a valid format to be used for querying.
        
        Typically, this function does not need to be modified by the plugins.
        """

        self.transport.chdir(working_directory)
        retval, stdout, stderr = self.transport.execute_command_wait(
            self._get_submit_command(escape_for_bash(submit_script)))
        return self._parse_submit_output(retval, stdout, stderr)
        

#if __name__ == '__main__':
#    import logging
#    aida.common.aidalogger.setLevel(logging.DEBUG)
#    
#    s = Scheduler._get_run_line(argv=['mpirun', '-np', '8', 'pw.x'],
#        stdin_name=None, stdout_name=None, stderr_name=None, join_files=True)
