# -*- coding: utf-8 -*-
"""Template for a scheduler plugins."""
import datetime
import logging

from aiida.common.escaping import escape_for_bash
from aiida.schedulers import Scheduler, SchedulerError, SchedulerParsingError
from aiida.schedulers.datastructures import (JobInfo, JobState, MachineInfo, NodeNumberJobResource, ParEnvJobResource)

_LOGGER = logging.getLogger(__name__)


_MAP_SCHEDULER_AIIDA_STATUS = {
    'SET_ME_STATUS_1': JobState.RUNNING,
    'SET_ME_STATUS_5': JobState.QUEUED,
    'SET_ME_STATUS_2': JobState.DONE,
    'SET_ME_STATUS_3': JobState.QUEUED_HELD,
    'SET_ME_STATUS_4': JobState.UNDETERMINED,
    'SET_ME_STATUS_6': JobState.SUSPENDED,
}


class TemplateJobResource(NodeNumberJobResource):  # or TemplateJobResource(ParEnvJobResource)
    """Template class for job resources."""

    @classmethod
    def validate_resources(cls, **kwargs):
        """Validate the resources against the job resource class of this scheduler.

        This extends the base class validator.

        :param kwargs: dictionary of values to define the job resources
        :return: attribute dictionary with the parsed parameters populated
        :raises ValueError: if the resources are invalid or incomplete
        """
        resources = super().validate_resources(**kwargs)

        # Put some validation code here.

        return resources


class TemplateScheduler(Scheduler):
    """Base class template for a scheduler."""

    # Query only by list of jobs and not by user
    _features = {
        'can_query_by_user': False,
    }

    # The class to be used for the job resource.
    _job_resource_class = TemplateJobResource

    _map_status = _MAP_SCHEDULER_AIIDA_STATUS

    def _get_resource_lines(
        self, num_machines, num_mpiprocs_per_machine, num_cores_per_machine, max_memory_kb, max_wallclock_seconds
    ):
        """
        Return a list of lines (possibly empty) with the header
        lines relative to:

        * num_machines
        * num_mpiprocs_per_machine
        * num_cores_per_machine
        * max_memory_kb
        * max_wallclock_seconds

        This is done in an external function because it may change in
        different subclasses.
        """
        return []

    def _get_joblist_command(self, jobs=None, user=None):
        """The command to report full information on existing jobs."""

        return []  # for instance ['qstat', '-f']

    def _get_detailed_job_info_command(self, job_id):
        """Return the command to run to get the detailed information on a job,
        even after the job has finished.

        The output text is just retrieved, and returned for logging purposes.
        """
        return '' # for instance f'tracejob -v {escape_for_bash(job_id)}'

    def _get_submit_script_header(self, job_tmpl):
        """Return the submit script header, using the parameters from the job_tmpl.

        Args:
           job_tmpl: an JobTemplate instance with relevant parameters set.

        """
        return ''

    def _get_submit_command(self, submit_script):
        """Return the string to submit a given script.

        Args:
            submit_script: the path of the submit script relative to the working
                directory.
                IMPORTANT: submit_script should be already escaped.
        """
        submit_command = '' # for instance f'qsub {submit_script}'

        _LOGGER.info(f'submitting with: {submit_command}')

        return submit_command

    def _parse_joblist_output(self, retval, stdout, stderr):
        """Parse the queue output string, as returned by executing the command returned by
        `_get_joblist_command command`.

        Return a list of JobInfo objects, one of each job, each relevant parameters implemented.

        Note: depending on the scheduler configuration, finished jobs may
            either appear here, or not.
            This function will only return one element for each job find
            in the qstat output; missing jobs (for whatever reason) simply
            will not appear here.
        """
        return []

    @staticmethod
    def _convert_time(string):
        """Convert a time string to a number of seconds."""
        hours = 0
        mins = 0
        secs = 20

        return hours * 3600 + mins * 60 + secs

    @staticmethod
    def _parse_time_string(string, fmt='%a %b %d %H:%M:%S %Y'):
        """Parses a time string returned by scheduler and returns a datetime object."""

        return datetime.datetime.now()

    def _parse_submit_output(self, retval, stdout, stderr):
        """Parses the output of the submit command, as returned by executing the
        command returned by _get_submit_command command.

        To be implemented by the plugin.

        Return a string with the JobID.
        """
        if retval != 0:
            _LOGGER.error(f'Error in _parse_submit_output: retval={retval}; stdout={stdout}; stderr={stderr}')
            raise SchedulerError(f'Error during submission, retval={retval}; stdout={stdout}; stderr={stderr}')

        if stderr.strip():
            _LOGGER.warning(f'in _parse_submit_output there was some text in stderr: {stderr}')

        return stdout.strip()

    def _get_kill_command(self, jobid):
        """Return the command to kill the job with specified jobid."""

        _LOGGER.info(f'killing job {jobid}')

        return ''  # for instance f'qdel {jobid}'

    def _parse_kill_output(self, retval, stdout, stderr):
        """Parse the output of the kill command.

        :return: True if everything seems ok, False otherwise.
        """

        return True

    def parse_output(self, detailed_job_info, stdout, stderr):  # pylint: disable=inconsistent-return-statements
        """Parse the output of the scheduler.

        :param detailed_job_info: dictionary with the output returned by the `Scheduler.get_detailed_job_info` command.
            This should contain the keys `retval`, `stdout` and `stderr` corresponding to the return value, stdout and
            stderr returned by the accounting command executed for a specific job id.
        :param stdout: string with the output written by the scheduler to stdout
        :param stderr: string with the output written by the scheduler to stderr
        :return: None or an instance of `aiida.engine.processes.exit_code.ExitCode`
        :raises TypeError or ValueError: if the passed arguments have incorrect type or value
        """
        return None
