# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Plugin for direct execution.
"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import six

import aiida.schedulers
from aiida.common.escaping import escape_for_bash
from aiida.schedulers import SchedulerError
from aiida.schedulers.datastructures import (JobInfo, JobState, NodeNumberJobResource)

## From the ps man page on Mac OS X 10.12
#     state     The state is given by a sequence of characters, for example,
#               ``RWNA''.  The first character indicates the run state of the
#               process:
#
#               I       Marks a process that is idle (sleeping for longer than
#                       about 20 seconds).
#               R       Marks a runnable process.
#               S       Marks a process that is sleeping for less than about 20
#                       seconds.
#               T       Marks a stopped process.
#               U       Marks a process in uninterruptible wait.
#               Z       Marks a dead process (a ``zombie'').

# From the man page of ps on Ubuntu 14.04:
#       Here are the different values that the s, stat and state output
#       specifiers (header "STAT" or "S") will display to describe the state of
#       a process:
#
#               D    uninterruptible sleep (usually IO)
#               R    running or runnable (on run queue)
#               S    interruptible sleep (waiting for an event to complete)
#               T    stopped, either by a job control signal or because it is
#                    being traced
#               W    paging (not valid since the 2.6.xx kernel)
#               X    dead (should never be seen)
#               Z    defunct ("zombie") process, terminated but not reaped by
#                    its parent

_MAP_STATUS_PS = {
    'D': JobState.RUNNING,
    'I': JobState.RUNNING,
    'R': JobState.RUNNING,
    'S': JobState.RUNNING,
    'T': JobState.SUSPENDED,
    'U': JobState.RUNNING,
    'W': JobState.RUNNING,
    'X': JobState.DONE,
    'Z': JobState.DONE,
    # Not sure about these three, I comment them out (they used to be in
    # here, but they don't appear neither on ubuntu nor on Mac)
    #    'F': JobState.DONE,
    #    'H': JobState.QUEUED_HELD,
    #    'Q': JobState.QUEUED,
}


class DirectJobResource(NodeNumberJobResource):
    pass


class DirectScheduler(aiida.schedulers.Scheduler):
    """
    Support for the direct execution bypassing schedulers.
    """
    _logger = aiida.schedulers.Scheduler._logger.getChild('direct')

    # Query only by list of jobs and not by user
    _features = {
        'can_query_by_user': True,
    }

    # The class to be used for the job resource.
    _job_resource_class = DirectJobResource

    def _get_joblist_command(self, jobs=None, user=None):
        """
        The command to report full information on existing jobs.

        TODO: in the case of job arrays, decide what to do (i.e., if we want
              to pass the -t options to list each subjob).
        """
        command = 'ps -o pid,stat,user,time'

        if jobs:
            if isinstance(jobs, six.string_types):
                command += ' {}'.format(escape_for_bash(jobs))
            else:
                try:
                    command += ' {}'.format(' '.join(escape_for_bash(j) for j in jobs))
                except TypeError:
                    raise TypeError("If provided, the 'jobs' variable must be a string or a list of strings")

        command += '| tail -n +2'  # -header, do not use 'h'

        return command

    def _get_submit_script_header(self, job_tmpl):
        """
        Return the submit script header, using the parameters from the
        job_tmpl.

        Args:
           job_tmpl: an JobTemplate instance with relevant parameters set.
        """

        lines = []
        empty_line = ""

        # Redirecting script output on the correct files
        # Should be one of the first commands
        if job_tmpl.sched_output_path:
            lines.append("exec > {}".format(job_tmpl.sched_output_path))

        if job_tmpl.sched_join_files:
            # TODO: manual says:
            # By  default both standard output and standard error are directed
            # to a file of the name "slurm-%j.out", where the "%j" is replaced
            # with  the  job  allocation  number.
            # See that this automatic redirection works also if
            # I specify a different --output file
            if job_tmpl.sched_error_path:
                self.logger.info("sched_join_files is True, but sched_error_path is set; ignoring sched_error_path")
        else:
            if job_tmpl.sched_error_path:
                lines.append("exec 2> {}".format(job_tmpl.sched_error_path))
            else:
                # To avoid automatic join of files
                lines.append("exec 2>&1")

        if job_tmpl.max_memory_kb:
            try:
                virtual_memory_kb = int(job_tmpl.max_memory_kb)
                if virtual_memory_kb <= 0:
                    raise ValueError
            except ValueError:
                raise ValueError("max_memory_kb must be "
                                 "a positive integer (in kB)! It is instead '{}'"
                                 "".format((job_tmpl.max_memory_kb)))
            lines.append("ulimit -v {}".format(virtual_memory_kb))
        if not job_tmpl.import_sys_environment:
            lines.append("env --ignore-environment \\")

        if job_tmpl.custom_scheduler_commands:
            lines.append(job_tmpl.custom_scheduler_commands)

        # Job environment variables are to be set on one single line.
        # This is a tough job due to the escaping of commas, etc.
        # moreover, I am having issues making it work.
        # Therefore, I assume that this is bash and export variables by
        # and.

        if job_tmpl.job_environment:
            lines.append(empty_line)
            lines.append("# ENVIRONMENT VARIABLES BEGIN ###")
            if not isinstance(job_tmpl.job_environment, dict):
                raise ValueError("If you provide job_environment, it must be a dictionary")
            for key, value in job_tmpl.job_environment.items():
                lines.append("export {}={}".format(key.strip(), escape_for_bash(value)))
            lines.append("# ENVIRONMENT VARIABLES  END  ###")
            lines.append(empty_line)

        lines.append(empty_line)

        ## The following code is not working as there's an empty line
        ## inserted between the header and the actual command.
        # if job_tmpl.max_wallclock_seconds is not None:
        #     try:
        #         tot_secs = int(job_tmpl.max_wallclock_seconds)
        #         if tot_secs <= 0:
        #             raise ValueError
        #     except ValueError:
        #         raise ValueError(
        #             "max_wallclock_seconds must be "
        #             "a positive integer (in seconds)! It is instead '{}'"
        #             "".format((job_tmpl.max_wallclock_seconds)))
        #     lines.append("timeout {} \\".format(tot_secs))

        return "\n".join(lines)

    def _get_submit_command(self, submit_script):
        """
        Return the string to execute to submit a given script.

        .. note:: One needs to redirect stdout and stderr to /dev/null
           otherwise the daemon remains hanging for the script to run

        :param submit_script: the path of the submit script relative to the working
            directory.
            IMPORTANT: submit_script should be already escaped.
        """
        submit_command = 'bash -e {} > /dev/null 2>&1 & echo $!'.format(submit_script)

        self.logger.info("submitting with: " + submit_command)

        return submit_command

    def _parse_joblist_output(self, retval, stdout, stderr):
        """
        Parse the queue output string, as returned by executing the
        command returned by _get_joblist_command command (qstat -f).

        Return a list of JobInfo objects, one of each job,
        each relevant parameters implemented.

        .. note:: depending on the scheduler configuration, finished jobs
            may either appear here, or not.
            This function will only return one element for each job find
            in the qstat output; missing jobs (for whatever reason) simply
            will not appear here.
        """
        import re

        filtered_stderr = '\n'.join(l for l in stderr.split('\n'))
        if filtered_stderr.strip():
            self.logger.warning("Warning in _parse_joblist_output, non-empty "
                                "(filtered) stderr='{}'".format(filtered_stderr))
            if retval != 0:
                raise SchedulerError("Error during direct execution parsing (_parse_joblist_output function)")

        # Create dictionary and parse specific fields
        job_list = []
        for line in stdout.split('\n'):
            if re.search(r'^\s*PID', line) or line == '':
                # Skip the header if present
                continue
            line = re.sub(r'^\s+', '', line)
            job = re.split(r'\s+', line)
            this_job = JobInfo()
            this_job.job_id = job[0]

            if len(job) < 3:
                raise SchedulerError("Unexpected output from the scheduler, "
                                     "not enough fields in line '{}'".format(line))

            try:
                job_state_string = job[1][0]  # I just check the first character
            except IndexError:
                self.logger.debug("No 'job_state' field for job id {}".format(this_job.job_id))
                this_job.job_state = JobState.UNDETERMINED
            else:
                try:
                    this_job.job_state = \
                        _MAP_STATUS_PS[job_state_string]
                except KeyError:
                    self.logger.warning("Unrecognized job_state '{}' for job "
                                        "id {}".format(job_state_string, this_job.job_id))
                    this_job.job_state = JobState.UNDETERMINED

            try:
                # I strip the part after the @: is this always ok?
                this_job.job_owner = job[2]
            except KeyError:
                self.logger.debug("No 'job_owner' field for job id {}".format(this_job.job_id))

            try:
                this_job.wallclock_time_seconds = self._convert_time(job[3])
            except KeyError:
                # May not have started yet
                pass
            except ValueError:
                self.logger.warning("Error parsing 'resources_used.walltime' for job id {}".format(this_job.job_id))

            # I append to the list of jobs to return
            job_list.append(this_job)

        return job_list

    def get_jobs(self, jobs=None, user=None, as_dict=False):
        """
        Overrides original method from DirectScheduler in order to list
        missing processes as DONE.
        """
        job_stats = super(DirectScheduler, self).get_jobs(jobs=jobs, user=user, as_dict=as_dict)

        found_jobs = []
        # Get the list of known jobs
        if as_dict:
            found_jobs = job_stats.keys()
        else:
            found_jobs = [j.job_id for j in job_stats]
        # Now check if there are any the user requested but were not found
        not_found_jobs = list(set(jobs) - set(found_jobs)) if jobs else []

        for job_id in not_found_jobs:
            job = JobInfo()
            job.job_id = job_id
            job.job_state = JobState.DONE
            # Owner and wallclock time is unknown
            if as_dict:
                job_stats[job_id] = job
            else:
                job_stats.append(job)

        return job_stats

    def _convert_time(self, string):
        """
        Convert a string in the format HH:MM:SS to a number of seconds.
        """
        import re

        pieces = re.split('[:.]', string)
        if len(pieces) != 3:
            self.logger.warning("Wrong number of pieces (expected 3) for time string {}".format(string))
            raise ValueError("Wrong number of pieces for time string.")

        days = 0
        pieces_first = pieces[0].split('-')

        if len(pieces_first) == 2:
            days, pieces[0] = pieces_first
            days = int(days)

        try:
            hours = int(pieces[0])
            if hours < 0:
                raise ValueError
        except ValueError:
            self.logger.warning("Not a valid number of hours: {}".format(pieces[0]))
            raise ValueError("Not a valid number of hours.")

        try:
            mins = int(pieces[1])
            if mins < 0:
                raise ValueError
        except ValueError:
            self.logger.warning("Not a valid number of minutes: {}".format(pieces[1]))
            raise ValueError("Not a valid number of minutes.")

        try:
            secs = int(pieces[2])
            if secs < 0:
                raise ValueError
        except ValueError:
            self.logger.warning("Not a valid number of seconds: {}".format(pieces[2]))
            raise ValueError("Not a valid number of seconds.")

        return days * 86400 + hours * 3600 + mins * 60 + secs

    def _parse_submit_output(self, retval, stdout, stderr):
        """
        Parse the output of the submit command, as returned by executing the
        command returned by _get_submit_command command.

        To be implemented by the plugin.

        Return a string with the JobID.
        """
        if retval != 0:
            self.logger.error("Error in _parse_submit_output: retval={}; "
                              "stdout={}; stderr={}".format(retval, stdout, stderr))
            raise SchedulerError("Error during submission, retval={}\n"
                                 "stdout={}\nstderr={}".format(retval, stdout, stderr))

        if stderr.strip():
            self.logger.warning("in _parse_submit_output for {}: "
                                "there was some text in stderr: {}".format(str(self.transport), stderr))

        if not stdout.strip():
            self.logger.debug("Unable to get the PID: retval={}; "
                              "stdout={}; stderr={}".format(retval, stdout, stderr))
            raise SchedulerError("Unable to get the PID: retval={}; "
                                 "stdout={}; stderr={}".format(retval, stdout, stderr))

        return stdout.strip()

    def _get_kill_command(self, jobid):
        """
        Return the command to kill the job with specified jobid.
        """
        submit_command = 'kill {}'.format(jobid)

        self.logger.info("killing job {}".format(jobid))

        return submit_command

    def _parse_kill_output(self, retval, stdout, stderr):
        """
        Parse the output of the kill command.

        To be implemented by the plugin.

        :return: True if everything seems ok, False otherwise.
        """
        if retval != 0:
            self.logger.error("Error in _parse_kill_output: retval={}; "
                              "stdout={}; stderr={}".format(retval, stdout, stderr))
            return False

        if stderr.strip():
            self.logger.warning("in _parse_kill_output for {}: "
                                "there was some text in stderr: {}".format(str(self.transport), stderr))

        if stdout.strip():
            self.logger.warning("in _parse_kill_output for {}: "
                                "there was some text in stdout: {}".format(str(self.transport), stdout))

        return True
