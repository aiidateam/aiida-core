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
from __future__ import annotations

import abc
import typing as t

from aiida.common import exceptions, log, warnings
from aiida.common.datastructures import CodeRunMode
from aiida.common.escaping import escape_for_bash
from aiida.common.lang import classproperty
from aiida.engine.processes.exit_code import ExitCode
from aiida.schedulers.datastructures import JobInfo, JobResource, JobTemplate, JobTemplateCodeInfo

if t.TYPE_CHECKING:
    from aiida.transports import Transport

__all__ = ('Scheduler', 'SchedulerError', 'SchedulerParsingError')


class SchedulerError(exceptions.AiidaException):
    pass


class SchedulerParsingError(SchedulerError):
    pass


class Scheduler(metaclass=abc.ABCMeta):
    """Base class for a job scheduler."""

    _logger = log.AIIDA_LOGGER.getChild('scheduler')

    # A list of features
    # Features that should be defined in the plugins:
    # 'can_query_by_user': True if I can pass the 'user' argument to
    # get_joblist_command (and in this case, no 'jobs' should be given).
    # Otherwise, if False, a list of jobs is passed, and no 'user' is given.
    _features: dict[str, bool] = {}

    # The class to be used for the job resource.
    _job_resource_class: t.Type[JobResource] | None = None

    def __str__(self):
        return self.__class__.__name__

    @classmethod
    def preprocess_resources(cls, resources: dict[str, t.Any], default_mpiprocs_per_machine: int | None = None):
        """Pre process the resources.

        Add the `num_mpiprocs_per_machine` key to the `resources` if it is not already defined and it cannot be deduced
        from the `num_machines` and `tot_num_mpiprocs` being defined. The value is also not added if the job resource
        class of this scheduler does not accept the `num_mpiprocs_per_machine` keyword. Note that the changes are made
        in place to the `resources` argument passed.
        """
        num_machines: int | None = resources.get('num_machines', None)
        tot_num_mpiprocs: int | None = resources.get('tot_num_mpiprocs', None)
        num_mpiprocs_per_machine: int | None = resources.get('num_mpiprocs_per_machine', None)

        if (
            num_mpiprocs_per_machine is None and cls.job_resource_class.accepts_default_mpiprocs_per_machine()  # pylint: disable=no-member
            and (num_machines is None or tot_num_mpiprocs is None)
        ):
            resources['num_mpiprocs_per_machine'] = default_mpiprocs_per_machine

    @classmethod
    def validate_resources(cls, **resources):
        """Validate the resources against the job resource class of this scheduler.

        :param resources: keyword arguments to define the job resources
        :raises ValueError: if the resources are invalid or incomplete
        """
        assert cls._job_resource_class is not None and issubclass(cls._job_resource_class, JobResource)
        cls._job_resource_class.validate_resources(**resources)

    def __init__(self):
        assert self._job_resource_class is not None and issubclass(self._job_resource_class, JobResource)
        self._transport = None

    @classmethod
    def get_short_doc(cls):
        """Return the first non-empty line of the class docstring, if available."""
        # Remove empty lines
        docstring = cls.__doc__
        if not docstring:
            return 'No documentation available'

        doclines = [i for i in docstring.splitlines() if i.strip()]
        if doclines:
            return doclines[0].strip()

        return 'No documentation available'

    def get_feature(self, feature_name: str) -> bool:
        try:
            return self._features[feature_name]
        except KeyError:
            raise NotImplementedError(f'Feature {feature_name} not implemented for this scheduler')

    @property
    def logger(self):
        """Return the internal logger."""
        try:
            return self._logger
        except AttributeError:
            raise exceptions.InternalError('No self._logger configured for {}!')

    @classproperty
    def job_resource_class(cls) -> t.Type[JobResource]:  # pylint: disable=no-self-argument
        assert cls._job_resource_class is not None and issubclass(cls._job_resource_class, JobResource)
        return cls._job_resource_class

    @classmethod
    def create_job_resource(cls, **kwargs):
        """Create a suitable job resource from the kwargs specified."""
        assert cls._job_resource_class is not None and issubclass(cls._job_resource_class, JobResource)
        return cls._job_resource_class(**kwargs)  # pylint: disable=not-callable

    def get_submit_script(self, job_tmpl: JobTemplate) -> str:
        """Return the submit script as a string.

        :parameter job_tmpl: a `aiida.schedulers.datastrutures.JobTemplate` instance.

        The plugin returns something like

        #!/bin/bash <- this shebang line is configurable to some extent
        scheduler_dependent stuff to choose numnodes, numcores, walltime, ...
        prepend_computer [also from calcinfo, joined with the following?]
        prepend_code [from calcinfo]
        output of _get_script_main_content
        postpend_code
        postpend_computer
        """
        if not isinstance(job_tmpl, JobTemplate):
            raise exceptions.InternalError('job_tmpl should be of type JobTemplate')

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
            raise ValueError(f'Invalid shebang set: {job_tmpl.shebang}')

        script_header = self._get_submit_script_header(job_tmpl)
        script_lines.append(script_header)
        script_lines.append(empty_line)

        if '# ENVIRONMENT VARIABLES BEGIN ###' in script_header:
            warnings.warn_deprecation(
                f'Environment variables added by `{self.__class__.__name__}._get_submit_script_environment_variables`, '
                'however, this is no longer necessary and automatically done by the base `Scheduler` class.',
                version=3
            )

        if job_tmpl.job_environment:
            script_lines.append(self._get_submit_script_environment_variables(job_tmpl))
            script_lines.append(empty_line)

        if job_tmpl.prepend_text:
            script_lines.append(job_tmpl.prepend_text)
            script_lines.append(empty_line)

        script_lines.append(self._get_run_line(job_tmpl.codes_info, job_tmpl.codes_run_mode))
        script_lines.append(empty_line)

        if job_tmpl.append_text:
            script_lines.append(job_tmpl.append_text)
            script_lines.append(empty_line)

        footer = self._get_submit_script_footer(job_tmpl)
        if footer:
            script_lines.append(footer)
            script_lines.append(empty_line)

        return '\n'.join(script_lines)

    def _get_submit_script_environment_variables(self, template: JobTemplate) -> str:
        """Return the part of the submit script header that defines environment variables.

        :parameter template: a `aiida.schedulers.datastrutures.JobTemplate` instance.
        :return: string containing environment variable declarations.
        """
        if not isinstance(template.job_environment, dict):
            raise ValueError('If you provide job_environment, it must be a dictionary')

        lines = ['# ENVIRONMENT VARIABLES BEGIN ###']

        for key, value in template.job_environment.items():
            lines.append(f'export {key.strip()}={escape_for_bash(value, template.environment_variables_double_quotes)}')

        lines.append('# ENVIRONMENT VARIABLES END ###')

        return '\n'.join(lines)

    @abc.abstractmethod
    def _get_submit_script_header(self, job_tmpl: JobTemplate) -> str:
        """Return the submit script header, using the parameters from the job template.

        :param job_tmpl: a `JobTemplate` instance with relevant parameters set.
        :return: string with the submission script header.
        """

    def _get_submit_script_footer(self, job_tmpl: JobTemplate) -> str:
        """Return the submit script final part, using the parameters from the job template.

        :param job_tmpl: a `JobTemplate` instance with relevant parameters set.
        :return: string with the submission script footer.
        """
        # pylint: disable=unused-argument
        return ''

    def _get_run_line(self, codes_info: list[JobTemplateCodeInfo], codes_run_mode: CodeRunMode) -> str:
        """Return a string with the line to execute a specific code with specific arguments.

        :parameter codes_info: a list of `aiida.scheduler.datastructures.JobTemplateCodeInfo` objects.
            Each contains the information needed to run the code. I.e. `cmdline_params`, `stdin_name`,
            `stdout_name`, `stderr_name`, `join_files`. See
            the documentation of `JobTemplate` and `JobTemplateCodeInfo`.
        :parameter codes_run_mode: instance of `aiida.common.datastructures.CodeRunMode` contains the information on how
            to launch the multiple codes.
        :return: string with format: [executable] [args] {[ < stdin ]} {[ < stdout ]} {[2>&1 | 2> stderr]}
        """
        # pylint: disable=too-many-locals
        list_of_runlines = []

        for code_info in codes_info:
            computer_use_double_quotes = code_info.use_double_quotes[0]
            code_use_double_quotes = code_info.use_double_quotes[1]

            prepend_cmdline_params = []
            for arg in code_info.prepend_cmdline_params:
                prepend_cmdline_params.append(escape_for_bash(arg, use_double_quotes=computer_use_double_quotes))

            cmdline_params = []
            for arg in code_info.cmdline_params:
                cmdline_params.append(escape_for_bash(arg, use_double_quotes=code_use_double_quotes))

            escape_stdin_name = escape_for_bash(code_info.stdin_name, use_double_quotes=computer_use_double_quotes)
            escape_stdout_name = escape_for_bash(code_info.stdout_name, use_double_quotes=computer_use_double_quotes)
            escape_sterr_name = escape_for_bash(code_info.stderr_name, use_double_quotes=computer_use_double_quotes)

            stdin_str = f'< {escape_stdin_name}' if code_info.stdin_name else ''
            stdout_str = f'> {escape_stdout_name}' if code_info.stdout_name else ''

            join_files = code_info.join_files
            if join_files:
                stderr_str = '2>&1'
            else:
                stderr_str = f'2> {escape_sterr_name}' if code_info.stderr_name else ''

            cmdline_params.extend([stdin_str, stdout_str, stderr_str])

            prepend_cmdline_params_string = ' '.join(prepend_cmdline_params)
            cmdline_params_string = ' '.join(cmdline_params)

            if code_info.wrap_cmdline_params:
                cmdline_params_string = escape_for_bash(cmdline_params_string, use_double_quotes=True)

            run_line = f'{prepend_cmdline_params_string} {cmdline_params_string}'.strip()

            list_of_runlines.append(run_line)

        self.logger.debug(f'_get_run_line output: {list_of_runlines}')

        if codes_run_mode == CodeRunMode.PARALLEL:
            list_of_runlines.append('wait\n')
            return ' &\n\n'.join(list_of_runlines)

        if codes_run_mode == CodeRunMode.SERIAL:
            return '\n\n'.join(list_of_runlines)

        raise NotImplementedError('Unrecognized code run mode')

    @abc.abstractmethod
    def _get_joblist_command(self, jobs: list[str] | None = None, user: str | None = None) -> str:
        """Return the command to get the most complete description possible of currently active jobs.

        .. note::

            Typically one can pass only either jobs or user, depending on the specific plugin. The choice can be done
            according to the value returned by `self.get_feature('can_query_by_user')`

        :param jobs: either None to get a list of all jobs in the machine, or a list of jobs.
        :param user: either None, or a string with the username (to show only jobs of the specific user).
        """

    def _get_detailed_job_info_command(self, job_id: str) -> dict[str, t.Any]:
        """Return the command to run to get detailed information for a given job.

        This is typically called after the job has finished, to retrieve the most detailed information possible about
        the job. This is done because most schedulers just make finished jobs disappear from the `qstat` command, and
        instead sometimes it is useful to know some more detailed information about the job exit status, etc.

        :raises: :class:`aiida.common.exceptions.FeatureNotAvailable`
        """
        # pylint: disable=not-callable,unused-argument
        raise exceptions.FeatureNotAvailable('Cannot get detailed job info')

    def get_detailed_job_info(self, job_id: str) -> dict[str, str | int]:
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

    @abc.abstractmethod
    def _parse_joblist_output(self, retval: int, stdout: str, stderr: str) -> list[JobInfo]:
        """Parse the joblist output as returned by executing the command returned by `_get_joblist_command` method.

        :return: list of `JobInfo` objects, one of each job each with at least its default params implemented.
        """

    def get_jobs(
        self,
        jobs: list[str] | None = None,
        user: str | None = None,
        as_dict: bool = False,
    ) -> list[JobInfo] | dict[str, JobInfo]:
        """Return the list of currently active jobs.

        .. note:: typically, only either jobs or user can be specified. See also comments in `_get_joblist_command`.

        :param list jobs: a list of jobs to check; only these are checked
        :param str user: a string with a user: only jobs of this user are checked
        :param list as_dict: if False (default), a list of JobInfo objects is returned. If True, a dictionary is
            returned, having as key the job_id and as value the JobInfo object.
        :return: list of active jobs
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
        """Return the transport set for this scheduler."""
        if self._transport is None:
            raise SchedulerError('Use the set_transport function to set the transport for the scheduler first.')

        return self._transport

    def set_transport(self, transport: Transport):
        """Set the transport to be used to query the machine or to submit scripts.

        This class assumes that the transport is open and active.
        """
        self._transport = transport

    @abc.abstractmethod
    def _get_submit_command(self, submit_script: str) -> str:
        """Return the string to execute to submit a given script.

        .. warning:: the `submit_script` should already have been bash-escaped

        :param submit_script: the path of the submit script relative to the working directory.
        :return: the string to execute to submit a given script.
        """

    @abc.abstractmethod
    def _parse_submit_output(self, retval: int, stdout: str, stderr: str) -> str | ExitCode:
        """Parse the output of the submit command returned by calling the `_get_submit_command` command.

        :return: a string with the job ID or an exit code if the submission failed because the submission script is
            invalid and the job should be terminated.
        """

    def submit_from_script(self, working_directory: str, submit_script: str) -> str | ExitCode:
        """Submit the submission script to the scheduler.

        :return: return a string with the job ID in a valid format to be used for querying.
        """
        self.transport.chdir(working_directory)
        result = self.transport.exec_command_wait(self._get_submit_command(escape_for_bash(submit_script)))
        return self._parse_submit_output(*result)

    def kill(self, jobid: str) -> bool:
        """Kill a remote job and parse the return value of the scheduler to check if the command succeeded.

        ..note::

            On some schedulers, even if the command is accepted, it may take some seconds for the job to actually
            disappear from the queue.

        :param jobid: the job ID to be killed
        :return: True if everything seems ok, False otherwise.
        """
        retval, stdout, stderr = self.transport.exec_command_wait(self._get_kill_command(jobid))
        return self._parse_kill_output(retval, stdout, stderr)

    @abc.abstractmethod
    def _get_kill_command(self, jobid: str) -> str:
        """Return the command to kill the job with specified jobid."""

    @abc.abstractmethod
    def _parse_kill_output(self, retval: int, stdout: str, stderr: str) -> bool:
        """Parse the output of the kill command.

        :return: True if everything seems ok, False otherwise.
        """

    def parse_output(
        self,
        detailed_job_info: dict[str, str | int] | None = None,
        stdout: str | None = None,
        stderr: str | None = None
    ) -> ExitCode | None:
        """Parse the output of the scheduler.

        :param detailed_job_info: dictionary with the output returned by the `Scheduler.get_detailed_job_info` command.
            This should contain the keys `retval`, `stdout` and `stderr` corresponding to the return value, stdout and
            stderr returned by the accounting command executed for a specific job id.
        :param stdout: string with the output written by the scheduler to stdout.
        :param stderr: string with the output written by the scheduler to stderr.
        :return: None or an instance of :class:`aiida.engine.processes.exit_code.ExitCode`.
        """
        raise exceptions.FeatureNotAvailable(f'output parsing is not available for `{self.__class__.__name__}`')
