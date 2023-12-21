"""Template for a scheduler plugin."""
import logging

from aiida.common import exceptions
from aiida.schedulers import Scheduler, SchedulerError
from aiida.schedulers.datastructures import JobResource, JobState

_LOGGER = logging.getLogger(__name__)


_MAP_SCHEDULER_AIIDA_STATUS = {
    'SET_ME_STATUS_1': JobState.RUNNING,
    'SET_ME_STATUS_5': JobState.QUEUED,
    'SET_ME_STATUS_2': JobState.DONE,
    'SET_ME_STATUS_3': JobState.QUEUED_HELD,
    'SET_ME_STATUS_4': JobState.UNDETERMINED,
    'SET_ME_STATUS_6': JobState.SUSPENDED,
}


class TemplateJobResource(JobResource):
    """Template class for job resources."""

    @classmethod
    def validate_resources(cls, **kwargs):
        """Validate the resources against the job resource class of this scheduler.

        :param kwargs: dictionary of values to define the job resources
        :raises ValueError: if the resources are invalid or incomplete
        :return: optional tuple of parsed resource settings
        """

    @classmethod
    def accepts_default_mpiprocs_per_machine(cls):
        """Return True if this subclass accepts a `default_mpiprocs_per_machine` key, False otherwise."""

    def get_tot_num_mpiprocs(self):
        """Return the total number of cpus of this job resource."""


class TemplateScheduler(Scheduler):
    """Base class template for a scheduler."""

    # Query only by list of jobs and not by user
    _features = {
        'can_query_by_user': False,
    }

    # Class to be used for job resources, Should be a subclass of :class:`~aiida.schedulers.datastructures.JobResource`
    _job_resource_class = JobResource

    _map_status = _MAP_SCHEDULER_AIIDA_STATUS

    def _get_joblist_command(self, jobs=None, user=None):
        """The command to report full information on existing jobs.

        :return: a string of the command to be executed to determine the active jobs.
        """

        return ''

    def _get_detailed_job_info_command(self, job_id):
        """Return the command to run to get the detailed information on a job,
        even after the job has finished.

        The output text is just retrieved, and returned for logging purposes.
        """
        # for instance f'tracejob -v {escape_for_bash(job_id)}'
        raise exceptions.FeatureNotAvailable('Retrieving detailed job info is not implemented')

    def _get_submit_script_header(self, job_tmpl):
        """Return the submit script final part, using the parameters from the job template.

        :param job_tmpl: a ``JobTemplate`` instance with relevant parameters set.
        """
        return ''

    def _get_submit_command(self, submit_script):
        """Return the string to execute to submit a given script.

        .. warning:: the `submit_script` should already have been bash-escaped

        :param submit_script: the path of the submit script relative to the working directory.
        :return: the string to execute to submit a given script.
        """
        submit_command = ''  # for instance f'qsub {submit_script}'

        _LOGGER.info(f'submitting with: {submit_command}')

        return submit_command

    def _parse_joblist_output(self, retval, stdout, stderr):
        """Parse the joblist output as returned by executing the command returned by `_get_joblist_command` method.

        :return: list of `JobInfo` objects, one of each job each with at least its default params implemented.
        """
        return []

    def _parse_submit_output(self, retval, stdout, stderr):
        """Parse the output of the submit command returned by calling the `_get_submit_command` command.

        :return: a string with the job ID.
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

    def parse_output(self, detailed_job_info, stdout, stderr):
        """Parse the output of the scheduler.

        :param detailed_job_info: dictionary with the output returned by the `Scheduler.get_detailed_job_info` command.
            This should contain the keys `retval`, `stdout` and `stderr` corresponding to the return value, stdout and
            stderr returned by the accounting command executed for a specific job id.
        :param stdout: string with the output written by the scheduler to stdout
        :param stderr: string with the output written by the scheduler to stderr
        :return: None or an instance of `aiida.engine.processes.exit_code.ExitCode`
        :raises TypeError or ValueError: if the passed arguments have incorrect type or value
        """
        raise exceptions.FeatureNotAvailable(f'output parsing is not available for `{self.__class__.__name__}`')
