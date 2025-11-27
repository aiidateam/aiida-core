###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Job scheduler that is interacted with through a CLI in bash."""

from __future__ import annotations

import abc
import typing as t

from aiida.common.escaping import escape_for_bash
from aiida.engine.processes.exit_code import ExitCode
from aiida.schedulers.datastructures import JobInfo
from aiida.schedulers.scheduler import Scheduler, SchedulerError

__all__ = ('BashCliScheduler',)


class BashCliScheduler(Scheduler, metaclass=abc.ABCMeta):
    """Job scheduler that is interacted with through a CLI in bash."""

    def submit_job(self, working_directory: str, filename: str) -> str | ExitCode:
        """Submit a job.

        :param working_directory: The absolute filepath to the working directory where the job is to be executed.
        :param filename: The filename of the submission script relative to the working directory.
        """
        result = self.transport.exec_command_wait(
            self._get_submit_command(escape_for_bash(filename)), workdir=working_directory
        )
        return self._parse_submit_output(*result)

    @t.overload
    @abc.abstractmethod
    def get_jobs(
        self,
        jobs: list[str] | None = None,
        user: str | None = None,
        as_dict: t.Literal[False] = False,
    ) -> list[JobInfo] | dict[str, JobInfo]: ...

    @t.overload
    @abc.abstractmethod
    def get_jobs(
        self,
        jobs: list[str] | None = None,
        user: str | None = None,
        as_dict: t.Literal[True] = True,
    ) -> dict[str, JobInfo]: ...

    def get_jobs(
        self,
        jobs: list[str] | None = None,
        user: str | None = None,
        as_dict: bool = False,
    ) -> list[JobInfo] | dict[str, JobInfo]:
        """Return the list of currently active jobs.

        :param jobs: A list of jobs to check; only these are checked.
        :param user: A string with a user: only jobs of this user are checked.
        :param as_dict: If ``False`` (default), a list of ``JobInfo`` objects is returned. If ``True``, a dictionary is
            returned, where the ``job_id`` is the key and the values are the ``JobInfo`` objects.
        :returns: List of active jobs.
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

    def kill_job(self, jobid: str) -> bool:
        """Kill a remote job and parse the return value of the scheduler to check if the command succeeded.

        ..note::

            On some schedulers, even if the command is accepted, it may take some seconds for the job to actually
            disappear from the queue.

        :param jobid: the job ID to be killed
        :returns: True if everything seems ok, False otherwise.
        """
        retval, stdout, stderr = self.transport.exec_command_wait(self._get_kill_command(jobid))
        return self._parse_kill_output(retval, stdout, stderr)

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

    @abc.abstractmethod
    def _get_joblist_command(self, jobs: list[str] | None = None, user: str | None = None) -> str:
        """Return the command to get the most complete description possible of currently active jobs.

        .. note::

            Typically one can pass only either jobs or user, depending on the specific plugin. The choice can be done
            according to the value returned by `self.get_feature('can_query_by_user')`

        :param jobs: either None to get a list of all jobs in the machine, or a list of jobs.
        :param user: either None, or a string with the username (to show only jobs of the specific user).
        """

    @abc.abstractmethod
    def _parse_joblist_output(self, retval: int, stdout: str, stderr: str) -> list[JobInfo]:
        """Parse the joblist output as returned by executing the command returned by `_get_joblist_command` method.

        :return: list of `JobInfo` objects, one of each job each with at least its default params implemented.
        """

    @abc.abstractmethod
    def _get_kill_command(self, jobid: str) -> str:
        """Return the command to kill the job with specified jobid."""

    @abc.abstractmethod
    def _parse_kill_output(self, retval: int, stdout: str, stderr: str) -> bool:
        """Parse the output of the kill command.

        :return: True if everything seems ok, False otherwise.
        """
