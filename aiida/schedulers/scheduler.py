# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Implementation of `Scheduler` base class."""
from abc import abstractmethod

import aiida.common
from aiida.common.lang import classproperty
from aiida.common.escaping import escape_for_bash
from aiida.common.exceptions import AiidaException, FeatureNotAvailable
from aiida.schedulers.datastructures import JobTemplate

__all__ = ('Scheduler', 'SchedulerError', 'SchedulerParsingError')


class SchedulerError(AiidaException):
    pass


class SchedulerParsingError(SchedulerError):
    pass


class Scheduler:
    """
    Base class for all schedulers.
    """

    _logger = aiida.common.AIIDA_LOGGER.getChild('scheduler')

    # A list of features
    # Features that should be defined in the plugins:
    # 'can_query_by_user': True if I can pass the 'user' argument to
    # get_joblist_command (and in this case, no 'jobs' should be given).
    # Otherwise, if False, a list of jobs is passed, and no 'user' is given.
    _features = {}

    # The class to be used for the job resource.
    _job_resource_class = None

    def __init__(self):
        self._transport = None

    def set_transport(self, transport):
        """
        Set the transport to be used to query the machine or to submit scripts.
        This class assumes that the transport is open and active.
        """
        self._transport = transport

    @classmethod
    def get_valid_schedulers(cls):
        from aiida.plugins.entry_point import get_entry_point_names

        return get_entry_point_names('aiida.schedulers')

    @classmethod
    def get_short_doc(cls):
        """
        Return the first non-empty line of the class docstring, if available
        """
        # Remove empty lines
        docstring = cls.__doc__
        if not docstring:
            return 'No documentation available'

        doclines = [i for i in docstring.splitlines() if i.strip()]
        if doclines:
            return doclines[0].strip()

        return 'No documentation available'

    def get_feature(self, feature_name):
        try:
            return self._features[feature_name]
        except KeyError:
            raise NotImplementedError('Feature {} not implemented for this scheduler'.format(feature_name))

    @property
    def logger(self):
        """
        Return the internal logger.
        """
        try:
            return self._logger
        except AttributeError:
            from aiida.common.exceptions import InternalError

            raise InternalError('No self._logger configured for {}!')

    @classproperty
    def job_resource_class(self):
        return self._job_resource_class

    @classmethod
    def create_job_resource(cls, **kwargs):
        """
        Create a suitable job resource from the kwargs specified
        """
        # pylint: disable=not-callable

        if cls._job_resource_class is None:
            raise NotImplementedError

        return cls._job_resource_class(**kwargs)

    def get_submit_script(self, job_tmpl):
        """
        Return the submit script as a string.
        :parameter job_tmpl: a aiida.schedulers.datastrutures.JobTemplate object.

        The plugin returns something like

        #!/bin/bash <- this shebang line is configurable to some extent
        scheduler_dependent stuff to choose numnodes, numcores, walltime, ...
        prepend_computer [also from calcinfo, joined with the following?]
        prepend_code [from calcinfo]
        output of _get_script_main_content
        postpend_code
        postpend_computer
        """

        from aiida.common.exceptions import InternalError

        if not isinstance(job_tmpl, JobTemplate):
            raise InternalError('job_tmpl should be of type JobTemplate')

        empty_line = ''

        # I fill the list with the lines, and finally join them and return
        script_lines = []

        if job_tmpl.shebang:
            script_lines.append(job_tmpl.shebang)
        elif job_tmpl.shebang == '':
            # Here I check whether the shebang was set explicitly as an empty line.
            # In such a case, the first line is empty, if that's what the user wants:
            script_lines.append(job_tmpl.shebang)
        elif job_tmpl.shebang is None:
            script_lines.append('#!/bin/bash')
        else:
            raise ValueError('Invalid shebang set: {}'.format(job_tmpl.shebang))
        script_lines.append(self._get_submit_script_header(job_tmpl))
        script_lines.append(empty_line)

        if job_tmpl.prepend_text:
            script_lines.append(job_tmpl.prepend_text)
            script_lines.append(empty_line)

        script_lines.append(self._get_run_line(job_tmpl.codes_info, job_tmpl.codes_run_mode))
        script_lines.append(empty_line)

        if job_tmpl.append_text:
            script_lines.append(job_tmpl.append_text)
            script_lines.append(empty_line)

        footer = self._get_submit_script_footer(job_tmpl)  # pylint: disable=assignment-from-none
        if footer:
            script_lines.append(footer)
            script_lines.append(empty_line)

        return '\n'.join(script_lines)

    @abstractmethod
    def _get_submit_script_header(self, job_tmpl):
        """
        Return the submit script header, using the parameters from the
        job_tmpl.

        :param job_tmpl: a JobTemplate instance with relevant parameters set.
        """
        raise NotImplementedError

    def _get_submit_script_footer(self, job_tmpl):
        """
        Return the submit script final part, using the parameters from the
        job_tmpl.

        :param job_tmpl: a JobTemplate instance with relevant parameters set.
        """
        # pylint: disable=no-self-use, unused-argument
        return None

    def _get_run_line(self, codes_info, codes_run_mode):
        """
        Return a string with the line to execute a specific code with
        specific arguments.

        :parameter codes_info: a list of aiida.common.datastructures.CodeInfo
          objects. Each contains the information needed to run the code. I.e.
          cmdline_params, stdin_name, stdout_name, stderr_name, join_files.
          See the documentation of JobTemplate and CodeInfo
        :parameter codes_run_mode: contains the information on how to launch the
          multiple codes. As described in aiida.common.datastructures.CodeRunMode


            argv: an array with the executable and the command line arguments.
              The first argument is the executable. This should contain
              everything, including the mpirun command etc.
            stdin_name: the filename to be used as stdin, relative to the
              working dir, or None if no stdin redirection is required.
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
        from aiida.common.datastructures import CodeRunMode

        list_of_runlines = []

        for code_info in codes_info:
            command_to_exec_list = []
            for arg in code_info.cmdline_params:
                command_to_exec_list.append(escape_for_bash(arg))
            command_to_exec = ' '.join(command_to_exec_list)

            stdin_str = '< {}'.format(escape_for_bash(code_info.stdin_name)) if code_info.stdin_name else ''
            stdout_str = '> {}'.format(escape_for_bash(code_info.stdout_name)) if code_info.stdout_name else ''

            join_files = code_info.join_files
            if join_files:
                stderr_str = '2>&1'
            else:
                stderr_str = '2> {}'.format(escape_for_bash(code_info.stderr_name)) if code_info.stderr_name else ''

            output_string = ('{} {} {} {}'.format(command_to_exec, stdin_str, stdout_str, stderr_str))

            list_of_runlines.append(output_string)

        self.logger.debug('_get_run_line output: {}'.format(list_of_runlines))

        if codes_run_mode == CodeRunMode.PARALLEL:
            list_of_runlines.append('wait\n')
            return ' &\n\n'.join(list_of_runlines)

        if codes_run_mode == CodeRunMode.SERIAL:
            return '\n\n'.join(list_of_runlines)

        raise NotImplementedError('Unrecognized code run mode')

    @abstractmethod
    def _get_joblist_command(self, jobs=None, user=None):
        """
        Return the qstat (or equivalent) command to run with the required
        command-line parameters to get the most complete description possible;
        also specifies the output format of qsub to be the one to be used
        by the parse_queue_output method.

        Must be implemented in the plugin.

        :param jobs: either None to get a list of all jobs in the machine,
               or a list of jobs.
        :param user: either None, or a string with the username (to show only
                     jobs of the specific user).

        Note: typically one can pass only either jobs or user, depending on the
            specific plugin. The choice can be done according to the value
            returned by self.get_feature('can_query_by_user')
        """
        raise NotImplementedError

    def _get_detailed_job_info_command(self, job_id):
        """
        Return the command to run to get the detailed information on a job.
        This is typically called after the job has finished, to retrieve
        the most detailed information possible about the job. This is done
        because most schedulers just make finished jobs disappear from the
        'qstat' command, and instead sometimes it is useful to know some
        more detailed information about the job exit status, etc.

        :raises: :class:`aiida.common.exceptions.FeatureNotAvailable`
        """
        # pylint: disable=no-self-use,not-callable,unused-argument
        raise FeatureNotAvailable('Cannot get detailed job info')

    def get_detailed_job_info(self, job_id):
        """Return the detailed job info.

        This will be a dictionary with the return value, stderr and stdout content returned by calling the command that
        is returned by `_get_detailed_job_info_command`.

        :param job_id: the job identifier
        :return: dictionary with `retval`, `stdout` and `stderr`.
        """
        command = self._get_detailed_job_info_command(job_id)  # pylint: disable=assignment-from-no-return
        with self.transport:
            retval, stdout, stderr = self.transport.exec_command_wait(command)

        detailed_job_info = {
            'retval': retval,
            'stdout': stdout,
            'stderr': stderr,
        }

        return detailed_job_info

    def get_detailed_jobinfo(self, jobid):
        """
        Return a string with the output of the detailed_jobinfo command.

        .. deprecated:: 1.1.0
            Will be removed in `v2.0.0`, use :meth:`aiida.schedulers.scheduler.Scheduler.get_detailed_job_info` instead.

        At the moment, the output text is just retrieved
        and stored for logging purposes, but no parsing is performed.

        :raises: :class:`aiida.common.exceptions.FeatureNotAvailable`
        """
        import warnings
        from aiida.common.warnings import AiidaDeprecationWarning
        warnings.warn('function is deprecated, use `get_detailed_job_info` instead', AiidaDeprecationWarning)  # pylint: disable=no-member

        command = self._get_detailed_job_info_command(job_id=jobid)  # pylint: disable=assignment-from-no-return
        with self.transport:
            retval, stdout, stderr = self.transport.exec_command_wait(command)

        return u"""Detailed jobinfo obtained with command '{}'
Return Code: {}
-------------------------------------------------------------
stdout:
{}
stderr:
{}
""".format(command, retval, stdout, stderr)

    @abstractmethod
    def _parse_joblist_output(self, retval, stdout, stderr):
        """
        Parse the joblist output ('qstat'), as returned by executing the
        command returned by _get_joblist_command method.

        To be implemented by the plugin.

        Return a list of JobInfo objects, one of each job,
        each with at least its default params implemented.
        """
        raise NotImplementedError

    def get_jobs(self, jobs=None, user=None, as_dict=False):
        """
        Get the list of jobs and return it.

        Typically, this function does not need to be modified by the plugins.

        :param list jobs: a list of jobs to check; only these are checked
        :param str user: a string with a user: only jobs of this user are checked
        :param list as_dict: if False (default), a list of JobInfo objects is
             returned. If True, a dictionary is returned, having as key the
             job_id and as value the JobInfo object.

        Note: typically, only either jobs or user can be specified. See also
        comments in _get_joblist_command.
        """
        with self.transport:
            retval, stdout, stderr = self.transport.exec_command_wait(self._get_joblist_command(jobs=jobs, user=user))

        joblist = self._parse_joblist_output(retval, stdout, stderr)
        if as_dict:
            jobdict = {job.job_id: job for job in joblist}
            if None in jobdict:
                raise SchedulerError('Found at least one job without jobid')
            return jobdict

        return joblist

    @property
    def transport(self):
        """
        Return the transport set for this scheduler.
        """
        if self._transport is None:
            raise SchedulerError('Use the set_transport function to set the transport for the scheduler first.')

        return self._transport

    @abstractmethod
    def _get_submit_command(self, submit_script):
        """
        Return the string to execute to submit a given script.

        To be implemented by the plugin.

        :param str submit_script: the path of the submit script relative to the
            working directory.
            IMPORTANT: submit_script should be already escaped.
        :return: the string to execute to submit a given script.
        """
        raise NotImplementedError

    @abstractmethod
    def _parse_submit_output(self, retval, stdout, stderr):
        """
        Parse the output of the submit command, as returned by executing the
        command returned by _get_submit_command command.

        To be implemented by the plugin.

        :return: a string with the JobID.
        """
        raise NotImplementedError

    def submit_from_script(self, working_directory, submit_script):
        """
        Goes in the working directory and submits the submit_script.

        Return a string with the JobID in a valid format to be used for
        querying.

        Typically, this function does not need to be modified by the plugins.
        """

        self.transport.chdir(working_directory)
        retval, stdout, stderr = self.transport.exec_command_wait(
            self._get_submit_command(escape_for_bash(submit_script))
        )
        return self._parse_submit_output(retval, stdout, stderr)

    def kill(self, jobid):
        """
        Kill a remote job, and try to parse the output message of the scheduler
        to check if the scheduler accepted the command.

        ..note:: On some schedulers, even if the command is accepted, it may
        take some seconds for the job to actually disappear from the queue.

        :param str jobid: the job id to be killed

        :return: True if everything seems ok, False otherwise.
        """
        retval, stdout, stderr = self.transport.exec_command_wait(self._get_kill_command(jobid))
        return self._parse_kill_output(retval, stdout, stderr)

    def _get_kill_command(self, jobid):
        """
        Return the command to kill the job with specified jobid.

        To be implemented by the plugin.
        """
        raise NotImplementedError

    def _parse_kill_output(self, retval, stdout, stderr):
        """
        Parse the output of the kill command.

        To be implemented by the plugin.

        :return: True if everything seems ok, False otherwise.
        """
        raise NotImplementedError
