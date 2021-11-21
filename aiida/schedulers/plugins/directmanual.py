# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Plugin for direct manual execution.
"""

from aiida.common.escaping import escape_for_bash
import aiida.schedulers
from aiida.schedulers.datastructures import JobInfo, JobState, NodeNumberJobResource

_MAP_STATUS = {  # the order of the states are important
    'UNDETERMINED': JobState.UNDETERMINED,
    'QUEUED': JobState.QUEUED,
    'RUNNING': JobState.RUNNING,
    'DONE': JobState.DONE,
}

_PREFIX = '_scheduler_state.'


class DirectManualJobResource(NodeNumberJobResource):
    pass


class DirectManualScheduler(aiida.schedulers.Scheduler):
    """
    Support for the direct execution bypassing schedulers.
    """
    _logger = aiida.schedulers.Scheduler._logger.getChild('direct')

    # Query only by list of jobs and not by user
    _features = {
        'can_query_by_user': True,
    }

    # The class to be used for the job resource.
    _job_resource_class = DirectManualJobResource

    def _get_joblist_command(self, jobs=None, user=None):
        """
        The command to report full information on existing jobs.
        """

        if jobs and not isinstance(jobs, (str, tuple, list)):
            raise TypeError("If provided, the 'jobs' variable must be a string or a list/tuple of strings")

        command = [
            'LC_ALL=C',  # avoid any localization effects
            'find',
        ]

        if jobs:
            # job ids are absolute paths:
            command += [jobs] if isinstance(jobs, str) else jobs
        else:
            # unfortunately this will likely run in the users $HOME, rather than in
            command.append('$(pwd)')

        command += ['-name', f"'{_PREFIX}*'"]

        return ' '.join(command)

    def _parse_joblist_output(self, _, stdout, stderr):
        """
        Parse the queue output string, as returned by executing the
        command returned by _get_joblist_command command.

        Return a list of JobInfo objects, one of each job,
        each relevant parameters implemented.
        """

        def map_status(state: str):
            try:
                return _MAP_STATUS[state]
            except KeyError:
                return JobState.UNDETERMINED

        def state_idx(job_state: JobState):
            return list(_MAP_STATUS.values()).index(job_state)

        def create_job(jobid: str, job_state: JobState):
            job = JobInfo()
            job.job_id = jobid
            job.job_state = job_state
            return job

        jobs = {}
        for line in stdout.split('\n'):
            if not line:  # ignore empty
                continue

            jobid, statefile = line.rsplit('/', maxsplit=1)
            if not statefile.startswith(_PREFIX):
                self.logger.info(f'found unexpected output from jobfile listing: {statefile}')
                continue

            if f'{_PREFIX}KILL' in statefile:
                # ignore the KILL request "state"
                self.logger.info(f'ignoring the KILL pseudo-state file for: {jobid}')
                continue

            state = map_status(statefile[len(_PREFIX):])

            if jobid not in jobs:
                jobs[jobid] = create_job(jobid, state)
            else:
                if state_idx(state) > state_idx(jobs[jobid].job_state):
                    jobs[jobid].job_state = state  # "upgrade" the state

        for line in stderr.split('\n'):
            if not line:  # ignore empty
                continue

            prog, path, errmsg = line.split(':', maxsplit=2)
            if prog != 'find':
                self.logger.info(f'found error message from something else than find: {line}')
                continue

            if 'Operation not permitted' in errmsg or 'Permission denied' in errmsg:
                self.logger.info(
                    f'ignoring permission denied error: {line}'
                )  # likely from the wildcard search which starts in $HOME
                continue

            jobid = path.strip()
            if jobid in jobs:
                self.logger.warning(f'found an error for a job where we previously found a valid state: {line}')
                continue

            jobs[jobid] = create_job(jobid, JobState.UNDETERMINED)

        return list(jobs.values())

    def _get_submit_script_header(self, job_tmpl):
        """
        Return the submit script header, using the parameters from the
        job_tmpl.

        Args:
           job_tmpl: an JobTemplate instance with relevant parameters set.
        """
        # pylint: disable=too-many-branches

        lines = []
        empty_line = ''

        # Redirecting script output on the correct files
        # Should be one of the first commands
        if job_tmpl.sched_output_path:
            lines.append(f'exec > {job_tmpl.sched_output_path}')

        if job_tmpl.sched_join_files:
            # TODO: manual says:  # pylint: disable=fixme
            # By  default both standard output and standard error are directed
            # to a file of the name "slurm-%j.out", where the "%j" is replaced
            # with  the  job  allocation  number.
            # See that this automatic redirection works also if
            # I specify a different --output file
            if job_tmpl.sched_error_path:
                self.logger.info('sched_join_files is True, but sched_error_path is set; ignoring sched_error_path')
        else:
            if job_tmpl.sched_error_path:
                lines.append(f'exec 2> {job_tmpl.sched_error_path}')
            else:
                # To avoid automatic join of files
                lines.append('exec 2>&1')

        if job_tmpl.max_memory_kb:
            self.logger.warning('Physical memory limiting is not supported by the direct scheduler.')

        if not job_tmpl.import_sys_environment:
            lines.append('env --ignore-environment \\')

        if job_tmpl.custom_scheduler_commands:
            lines.append(job_tmpl.custom_scheduler_commands)

        env_lines = []

        if job_tmpl.job_resource and job_tmpl.job_resource.num_cores_per_mpiproc:
            # since this was introduced after the environment injection below,
            # it is intentionally put before it to avoid breaking current users script by overruling
            # any explicit OMP_NUM_THREADS they may have set in their job_environment
            env_lines.append(f'export OMP_NUM_THREADS={job_tmpl.job_resource.num_cores_per_mpiproc}')

        # Job environment variables are to be set on one single line.
        # This is a tough job due to the escaping of commas, etc.
        # moreover, I am having issues making it work.
        # Therefore, I assume that this is bash and export variables by
        # and.
        if job_tmpl.job_environment:
            if not isinstance(job_tmpl.job_environment, dict):
                raise ValueError('If you provide job_environment, it must be a dictionary')
            for key, value in job_tmpl.job_environment.items():
                env_lines.append(f'export {key.strip()}={escape_for_bash(value)}')

        if env_lines:
            lines.append(empty_line)
            lines.append('# ENVIRONMENT VARIABLES BEGIN ###')
            lines += env_lines
            lines.append('# ENVIRONMENT VARIABLES  END  ###')
            lines.append(empty_line)

        if job_tmpl.rerunnable:
            self.logger.warning(
                "The 'rerunnable' option is set to 'True', but has no effect when using the direct scheduler."
            )

        lines.append(empty_line)

        return '\n'.join(lines)

    def _get_submit_command(self, submit_script):
        """
        Return the string to execute to submit a given script.

        .. note:: One needs to redirect stdout and stderr to /dev/null
           otherwise the daemon remains hanging for the script to run

        :param submit_script: the path of the submit script relative to the working
            directory.
            IMPORTANT: submit_script should be already escaped.
        """

        # this runs in the calculation directory, using the pwd as jobid assumed to be safe
        submit_command = f'echo {submit_script} > "{_PREFIX}QUEUED" ; pwd'

        self.logger.info(f'submitting with: {submit_command}')

        return submit_command

    def _parse_submit_output(self, retval, stdout, stderr):
        """
        Parse the output of the submit command, as returned by executing the
        command returned by _get_submit_command command.

        To be implemented by the plugin.

        Return a string with the JobID.
        """

        return stdout.strip()

    def _get_kill_command(self, jobid):
        """
        Return the command to kill the job with specified jobid.
        """
        submit_command = f'touch {jobid}/{_PREFIX}KILL'

        self.logger.info(f'killing job {jobid}')

        return submit_command

    def _parse_kill_output(self, retval, stdout, stderr):
        """
        Parse the output of the kill command.

        To be implemented by the plugin.

        :return: True if everything seems ok, False otherwise.
        """
        if retval != 0:
            self.logger.error(f'Error in _parse_kill_output: retval={retval}; stdout={stdout}; stderr={stderr}')
            return False

        if stderr.strip():
            self.logger.warning(
                f'in _parse_kill_output for {str(self.transport)}: there was some text in stderr: {stderr}'
            )

        if stdout.strip():
            self.logger.warning(
                f'in _parse_kill_output for {str(self.transport)}: there was some text in stdout: {stdout}'
            )

        return True
