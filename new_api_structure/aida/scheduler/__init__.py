import aida.common
from aida.common.utils import escape_for_bash
from aida.common.exceptions import AidaException

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
    
    def __init__(self, transport):
        """
        Pass an active transport; it is used to perform the required actions.
        This class assumes that the transport is open and active.
        """
        self.transport = transport

    @property
    def logger(self):
        """
        Return the internal logger
        """
        try:
            return self._logger
        except AttributeError:
            raise InternalError("No self._logger configured for {}!")

    @classmethod
    def _get_submit_script(cls, calc_info):
        """
        Return the submit script as a string.
        calc_info of type aida.managers.job.calcinfo.CalcInfo
        
        This must be implemented by the plugin subclass. The plugin will
        typically call the _get_run_line method implemented in this
        abstract class, that should be general enough. Nothing avoid to customize it,
        if really needed.

        TODO: understand if, in the future, we want to pass more than calculation,
        e.g. for job arrays.

        The plugin returns something like

        #!/bin/bash <- this shebang line could be configurable in the future
        scheduler_dependent stuff to choose numnodes, numcores, walltime, ...
        prepend_computer
        prepend_code [from calcinfo]
        in the future: environment_variables [from calcinfo, possibly,
            and from scheduler_requirements e.g. for OpenMP? or maybe
            the openmp part is better managed in the scheduler_dependent
            part above since it will be machine-dependent]
        output of _get_script_main_content
        postpend_code
        postpend_computer
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
        
        stdin_str = "< {}".format(stdin_name) if stdin_name else ""
        stdout_str = "> {}".format(stdout_name) if stdout_name else ""
        if join_files:
            stderr_str = "2>&1"
        else:
            stderr_str = "2> {}".format(stderr_name) if stderr_name else ""
            
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
        
    def getJobs(self,jobs=None,user=None):
        """
        Get the list of jobs and return a list of JobInfo objects.
        
        Typically, this function does not need to be modified by the plugins.
        
        For the meaning of the args, see the _get_joblist_command method.
        """
        retval, stdout, stderr = self.transport.exec_command_wait(
            self._get_joblist_command(jobs=jobs, user=user))
        
        return self._parse_joblist_output(retval, stdout, stderr)
        
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
