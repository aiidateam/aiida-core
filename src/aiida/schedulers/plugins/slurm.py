###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Plugin for SLURM.
This has been tested on SLURM 14.03.7 on the CSCS.ch machines.
"""

from __future__ import annotations

import datetime
import re
import string
import time
import typing as t

from typing_extensions import override

from aiida.common import AttributeDict
from aiida.common.exceptions import FeatureNotAvailable
from aiida.common.lang import type_check
from aiida.schedulers import Scheduler, SchedulerError
from aiida.schedulers.datastructures import JobInfo, JobState, JobTemplate, NodeNumberJobResource

from .bash import BashCliScheduler

if t.TYPE_CHECKING:
    from aiida.engine.processes.exit_code import ExitCode


# This maps SLURM state codes to our own status list

## List of states from the man page of squeue
## CA  CANCELLED       Job  was explicitly cancelled by the user or system
##                     administrator.  The job may or may  not  have  been
##                     initiated.
## CD  COMPLETED       Job has terminated all processes on all nodes.
## CF  CONFIGURING     Job  has  been allocated resources, but are waiting
##                     for them to become ready for use (e.g. booting).
## CG  COMPLETING      Job is in the process of completing. Some processes
##                     on some nodes may still be active.
## F   FAILED          Job  terminated  with  non-zero  exit code or other
##                     failure condition.
## NF  NODE_FAIL       Job terminated due to failure of one or more  allo-
##                     cated nodes.
## PD  PENDING         Job is awaiting resource allocation.
## PR  PREEMPTED       Job terminated due to preemption.
## R   RUNNING         Job currently has an allocation.
## S   SUSPENDED       Job  has an allocation, but execution has been sus-
##                     pended.
## TO  TIMEOUT         Job terminated upon reaching its time limit.

_MAP_STATUS_SLURM = {
    'CA': JobState.DONE,
    'CD': JobState.DONE,
    'CF': JobState.QUEUED,
    'CG': JobState.RUNNING,
    'F': JobState.DONE,
    'NF': JobState.DONE,
    'PD': JobState.QUEUED,
    'PR': JobState.DONE,
    'R': JobState.RUNNING,
    'S': JobState.SUSPENDED,
    'TO': JobState.DONE,
}

# From the manual,
# possible lines are:
# salloc: Granted job allocation 65537
# sbatch: Submitted batch job 65541
# and in practice, often the part before the colon can be absent.
_SLURM_SUBMITTED_REGEXP = re.compile(r'(.*:\s*)?([Gg]ranted job allocation|[Ss]ubmitted batch job)\s+(?P<jobid>\d+)')

# From docs,
# acceptable  time  formats include
# "minutes",  "minutes:seconds",  "hours:minutes:seconds",
# "days-hours",  "days-hours:minutes" and "days-hours:minutes:seconds".
_TIME_REGEXP = re.compile(
    r"""
    ^                            # beginning of string
    \s*                          # any number of white spaces
    (?=\d)                       # I check that there is at least a digit
                                 # in the string, without consuming it
    ((?P<days>\d+)(?P<dash>-)    # the number of days, if a dash is present,
                                 # composed by any number of digits;
                                 # may be absent
     (?=\d))?                    # in any case, I check that there is at least
                                 # a digit afterwards, without consuming it
    ((?P<hours>\d{1,2})          # match an hour (one or two digits)
     (?(dash)                    # check if the dash was found
       |                         # match nothing if the dash was found:
                                 # if the dash was found, we are sure that
                                 # the first number is a hour
       (?=:\d{1,2}:\d{1,2})))?   # if no dash was found, the first
                                 # element found is an hour only if
                                 # it is followed by two more fields (mm:ss)
       (?P<firstcolon>:)?        # there (can) possibly be a further colon,
                                 # consume it
    ((?<!-)(?P<minutes>\d{1,2})
     (:(?P<seconds>\d{1,2}))?)?  # number of minutes (one or two digits)
                                 # and seconds. A number only means minutes.
                                 # (?<!-) means that the location BEFORE
                                 # the current position does NOT
                                 # match a dash, because the string 1-2
                                 # means 1 day and 2 hours, NOT one day and
                                 # 2 minutes
    \s*                          # any number of whitespaces
    $                            # end of line
   """,
    re.VERBOSE,
)

# Separator between fields in the output of squeue
_FIELD_SEPARATOR = '^^^'


class SlurmJobResource(NodeNumberJobResource):
    """Class for SLURM job resources."""

    @override
    @classmethod
    def validate_resources(cls, **kwargs: t.Any) -> AttributeDict:
        """Validate the resources against the job resource class of this scheduler.

        This extends the base class validator to check that the `num_cores_per_machine` are a multiple of
        `num_cores_per_mpiproc` and/or `num_mpiprocs_per_machine`.

        :param kwargs: dictionary of values to define the job resources
        :return: attribute dictionary with the parsed parameters populated
        :raises ValueError: if the resources are invalid or incomplete
        """
        resources = super().validate_resources(**kwargs)

        # In this plugin we never used num_cores_per_machine so if it is not defined it is OK.
        if resources.num_cores_per_machine is not None and resources.num_cores_per_mpiproc is not None:
            if resources.num_cores_per_machine != resources.num_cores_per_mpiproc * resources.num_mpiprocs_per_machine:
                raise ValueError(
                    '`num_cores_per_machine` must be equal to `num_cores_per_mpiproc * num_mpiprocs_per_machine` and in'
                    ' particular it should be a multiple of `num_cores_per_mpiproc` and/or `num_mpiprocs_per_machine`'
                )

        elif resources.num_cores_per_machine is not None:
            if resources.num_cores_per_machine < 1:
                raise ValueError('num_cores_per_machine must be greater than or equal to one.')

            resources.num_cores_per_mpiproc = resources.num_cores_per_machine / resources.num_mpiprocs_per_machine
            if int(resources.num_cores_per_mpiproc) != resources.num_cores_per_mpiproc:
                raise ValueError(
                    '`num_cores_per_machine` must be equal to `num_cores_per_mpiproc * num_mpiprocs_per_machine` and in'
                    ' particular it should be a multiple of `num_cores_per_mpiproc` and/or `num_mpiprocs_per_machine`'
                )
            resources.num_cores_per_mpiproc = int(resources.num_cores_per_mpiproc)

        return resources


class SlurmScheduler(BashCliScheduler):
    """Support for the SLURM scheduler (http://slurm.schedmd.com/)."""

    _logger = Scheduler._logger.getChild('slurm')

    # Query only by list of jobs and not by user
    _features = {
        'can_query_by_user': False,
    }

    # The class to be used for the job resource.
    _job_resource_class = SlurmJobResource

    # Fields to query or to parse
    # Unavailable fields: substate, cputime
    fields = [
        ('%i', 'job_id'),  # job or job step id
        ('%t', 'state_raw'),  # job state in compact form
        ('%r', 'annotation'),  # reason for the job being in its current state
        ('%B', 'executing_host'),  # Executing (batch) host
        ('%u', 'username'),  # username
        ('%D', 'number_nodes'),  # number of nodes allocated
        ('%C', 'number_cpus'),  # number of allocated cores (if already running)
        ('%R', 'allocated_machines'),  # list of allocated nodes when running, otherwise
        # reason within parenthesis
        ('%P', 'partition'),  # partition (queue) of the job
        ('%l', 'time_limit'),  # time limit in days-hours:minutes:seconds
        ('%M', 'time_used'),  # Time used by the job in days-hours:minutes:seconds
        ('%S', 'dispatch_time'),  # actual or expected dispatch time (start time)
        ('%j', 'job_name'),  # job name (title)
        ('%V', 'submission_time'),  # This is probably new, it exists in version
        # 14.03.7 and later
    ]

    def _get_joblist_command(self, jobs: list[str] | None = None, user: str | None = None) -> str:
        """The command to report full information on existing jobs.

        Separate the fields with the _field_separator string order:
        jobnum, state, walltime, queue[=partition], user, numnodes, numcores, title
        """

        # I add the environment variable SLURM_TIME_FORMAT in front to be
        # sure to get the times in 'standard' format
        command = [
            "SLURM_TIME_FORMAT='standard'",
            'squeue',
            '--noheader',
            f"-o '{_FIELD_SEPARATOR.join(_[0] for _ in self.fields)}'",
        ]

        if user and jobs:
            raise FeatureNotAvailable('Cannot query by user and job(s) in SLURM')

        if user:
            command.append(f'-u{user}')

        if jobs:
            if isinstance(jobs, str):  # type: ignore[unreachable]
                joblist = [jobs]  # type: ignore[unreachable]
            else:
                if not isinstance(jobs, (tuple, list)):
                    raise TypeError("If provided, the 'jobs' variable must be a string or a list of strings")
                # Create a copy to avoid mutating the caller's input when we append below (line 225)
                joblist = list(jobs)

            # Trick: When asking for a single job, append the same job once more.
            # This helps provide a reliable way of knowing whether the squeue command failed (if its exit code is
            # non-zero, _parse_joblist_output assumes that an error has occurred and raises an exception).
            # When asking for a single job, squeue also returns a non-zero exit code if the corresponding job is
            # no longer in the queue (stderr: "slurm_load_jobs error: Invalid job id specified"), which typically
            # happens once in the life time of an AiiDA job,
            # However, when providing two or more jobids via `squeue --jobs=123,234`, squeue stops caring whether
            # the jobs are still in the queue and returns exit code zero irrespectively (allowing AiiDA to rely on the
            # exit code for detection of real issues).
            # Duplicating job ids has no other effect on the output.
            # Verified on slurm versions 17.11.2, 19.05.3-2 and 20.02.2.
            # See also https://github.com/aiidateam/aiida-core/issues/4326
            if len(joblist) == 1:
                joblist += [joblist[0]]

            command.append(f"--jobs={','.join(joblist)}")

        comm = ' '.join(command)
        self.logger.debug(f'squeue command: {comm}')
        return comm

    def _get_detailed_job_info_command(self, job_id: str) -> str:
        """Return the command to run to get the detailed information on a job,
        even after the job has finished.

        The output text is just retrieved, and returned for logging purposes.
        --parsable split the fields with a pipe (|), adding a pipe also at
        the end.
        """
        return f"sacct --format=$(sacct --helpformat | tr -s '\n' ' ' | tr ' ' ',') --parsable --jobs={job_id}"

    def _get_submit_script_header(self, job_tmpl: JobTemplate) -> str:
        """Return the submit script header, using the parameters from the
        job_tmpl.

        Args:
        -----
           job_tmpl: an JobTemplate instance with relevant parameters set.

        TODO: truncate the title if too long
        """

        lines = []
        if job_tmpl.submit_as_hold:
            lines.append('#SBATCH -H')

        if job_tmpl.rerunnable:
            lines.append('#SBATCH --requeue')
        else:
            lines.append('#SBATCH --no-requeue')

        if job_tmpl.email:
            # If not specified, but email events are set, SLURM
            # sends the mail to the job owner by default
            lines.append(f'#SBATCH --mail-user={job_tmpl.email}')

        if job_tmpl.email_on_started:
            lines.append('#SBATCH --mail-type=BEGIN')
        if job_tmpl.email_on_terminated:
            lines.append('#SBATCH --mail-type=FAIL')
            lines.append('#SBATCH --mail-type=END')

        if job_tmpl.job_name:
            # The man page does not specify any specific limitation
            # on the job name.
            # Just to be sure, I remove unwanted characters, and I
            # trim it to length 128

            # I leave only letters, numbers, dots, dashes and underscores
            # Note: I don't compile the regexp, I am going to use it only once
            job_title = re.sub(r'[^a-zA-Z0-9_.-]+', '', job_tmpl.job_name)

            # prepend a 'j' (for 'job') before the string if the string
            # is now empty or does not start with a valid charachter
            if not job_title or (job_title[0] not in string.ascii_letters + string.digits):
                job_title = f'j{job_title}'

            # Truncate to the first 128 characters
            # Nothing is done if the string is shorter.
            job_title = job_title[:128]

            lines.append(f'#SBATCH --job-name="{job_title}"')

        if job_tmpl.import_sys_environment:
            lines.append('#SBATCH --get-user-env')

        if job_tmpl.sched_output_path:
            lines.append(f'#SBATCH --output={job_tmpl.sched_output_path}')

        if job_tmpl.sched_join_files:
            # TODO: manual says:
            # By  default both standard output and standard error are directed
            # to a file of the name "slurm-%j.out", where the "%j" is replaced
            # with  the  job  allocation  number.
            # See that this automatic redirection works also if
            # I specify a different --output file
            if job_tmpl.sched_error_path:
                self.logger.info(
                    'sched_join_files is True, but sched_error_path is set in '
                    'SLURM script; ignoring sched_error_path'
                )
        elif job_tmpl.sched_error_path:
            lines.append(f'#SBATCH --error={job_tmpl.sched_error_path}')
        else:
            # To avoid automatic join of files
            lines.append('#SBATCH --error=slurm-%j.err')

        if job_tmpl.queue_name:
            lines.append(f'#SBATCH --partition={job_tmpl.queue_name}')

        if job_tmpl.account:
            lines.append(f'#SBATCH --account={job_tmpl.account}')

        if job_tmpl.qos:
            lines.append(f'#SBATCH --qos={job_tmpl.qos}')

        if job_tmpl.priority:
            #  Run the job with an adjusted scheduling priority  within  SLURM.
            #  With no adjustment value the scheduling priority is decreased by
            #  100. The adjustment range is from -10000 (highest  priority)  to
            #  10000  (lowest  priority).
            lines.append(f'#SBATCH --nice={job_tmpl.priority}')

        if not job_tmpl.job_resource:
            raise ValueError('Job resources (as the num_machines) are required for the SLURM scheduler plugin')

        lines.append(f'#SBATCH --nodes={job_tmpl.job_resource.num_machines}')
        if job_tmpl.job_resource.num_mpiprocs_per_machine:
            lines.append(f'#SBATCH --ntasks-per-node={job_tmpl.job_resource.num_mpiprocs_per_machine}')

        if job_tmpl.job_resource.num_cores_per_mpiproc:
            lines.append(f'#SBATCH --cpus-per-task={job_tmpl.job_resource.num_cores_per_mpiproc}')

        if job_tmpl.max_wallclock_seconds is not None:
            try:
                tot_secs = int(job_tmpl.max_wallclock_seconds)
                if tot_secs <= 0:
                    raise ValueError
            except ValueError:
                raise ValueError(
                    'max_wallclock_seconds must be ' "a positive integer (in seconds)! It is instead '{}'" ''.format(
                        (job_tmpl.max_wallclock_seconds)
                    )
                )
            days = tot_secs // 86400
            tot_hours = tot_secs % 86400
            hours = tot_hours // 3600
            tot_minutes = tot_hours % 3600
            minutes = tot_minutes // 60
            seconds = tot_minutes % 60
            if days == 0:
                lines.append(f'#SBATCH --time={hours:02d}:{minutes:02d}:{seconds:02d}')
            else:
                lines.append(f'#SBATCH --time={days:d}-{hours:02d}:{minutes:02d}:{seconds:02d}')

        # It is the memory per node, not per cpu!
        if job_tmpl.max_memory_kb is not None:
            try:
                physical_memory_kb = int(job_tmpl.max_memory_kb)
                if physical_memory_kb < 0:  # 0 is allowed and means no limit (https://slurm.schedmd.com/sbatch.html)
                    raise ValueError
            except ValueError:
                raise ValueError(
                    f'max_memory_kb must be a non-negative integer (in kB)! It is instead `{job_tmpl.max_memory_kb}`'
                )
            # --mem: Specify the real memory required per node in MegaBytes.
            # --mem and  --mem-per-cpu  are  mutually exclusive.
            lines.append(f'#SBATCH --mem={physical_memory_kb // 1024}')

        if job_tmpl.custom_scheduler_commands:
            lines.append(job_tmpl.custom_scheduler_commands)

        return '\n'.join(lines)

    def _get_submit_command(self, submit_script: str) -> str:
        """Return the string to execute to submit a given script.

        Args:
        -----
            submit_script: the path of the submit script relative to the working
                directory.
                IMPORTANT: submit_script should be already escaped.
        """
        submit_command = f'sbatch {submit_script}'

        self.logger.info(f'submitting with: {submit_command}')

        return submit_command

    def _parse_submit_output(self, retval: int, stdout: str, stderr: str) -> str | ExitCode:
        """Parse the output of the submit command, as returned by executing the
        command returned by _get_submit_command command.

        To be implemented by the plugin.

        Return a string with the JobID.
        """
        from aiida.engine import CalcJob

        if retval != 0:
            self.logger.error(f'Error in _parse_submit_output: retval={retval}; stdout={stdout}; stderr={stderr}')

            if 'Invalid account' in stderr:
                return CalcJob.exit_codes.ERROR_SCHEDULER_INVALID_ACCOUNT  # type: ignore[no-any-return]

            raise SchedulerError(f'Error during submission, retval={retval}\nstdout={stdout}\nstderr={stderr}')

        try:
            transport_string = f' for {self.transport}'
        except SchedulerError:
            transport_string = ''

        if stderr.strip():
            self.logger.warning(f'in _parse_submit_output{transport_string}: there was some text in stderr: {stderr}')

        # I check for a valid string in the output.
        # See comments near the regexp above.
        # I check for the first line that matches.
        for line in stdout.split('\n'):
            match = _SLURM_SUBMITTED_REGEXP.match(line.strip())
            if match:
                return match.group('jobid')
        # If I am here, no valid line could be found.
        self.logger.error(f'in _parse_submit_output{transport_string}: unable to find the job id: {stdout}')
        raise SchedulerError(
            'Error during submission, could not retrieve the jobID from ' 'sbatch output; see log for more info.'
        )

    def _parse_joblist_output(self, retval: int, stdout: str, stderr: str) -> list[JobInfo]:
        """Parse the queue output string, as returned by executing the
        command returned by _get_joblist_command command,
        that is here implemented as a list of lines, one for each
        job, with _field_separator as separator. The order is described
        in the _get_joblist_command function.

        Return a list of JobInfo objects, one of each job,
        each relevant parameters implemented.

        Note: depending on the scheduler configuration, finished jobs may
            either appear here, or not.
            This function will only return one element for each job find
            in the qstat output; missing jobs (for whatever reason) simply
            will not appear here.
        """
        num_fields = len(self.fields)

        # See discussion in _get_joblist_command on how we ensure that AiiDA can expect exit code 0 here.
        if retval != 0:
            raise SchedulerError(
                f"""squeue returned exit code {retval} (_parse_joblist_output function)
stdout='{stdout.strip()}'
stderr='{stderr.strip()}'"""
            )
        if stderr.strip():
            self.logger.warning(
                f"squeue returned exit code 0 (_parse_joblist_output function) but non-empty stderr='{stderr.strip()}'"
            )

        # will contain raw data parsed from output: only lines with the
        # separator, and already split in fields
        # I put num_fields, because in this way
        # if the symbol _field_separator appears in the title (that is
        # the last field), I don't split the title.
        # This assumes that _field_separator never
        # appears in any previous field.
        jobdata_raw = [
            line.split(_FIELD_SEPARATOR, num_fields) for line in stdout.splitlines() if _FIELD_SEPARATOR in line
        ]

        # Create dictionary and parse specific fields
        job_list = []
        for job in jobdata_raw:
            thisjob_dict = {k[1]: v for k, v in zip(self.fields, job)}

            this_job = JobInfo()
            try:
                this_job.job_id = thisjob_dict['job_id']

                this_job.annotation = thisjob_dict['annotation']
                job_state_raw = thisjob_dict['state_raw']
            except KeyError:
                # I skip this calculation if I couldn't find this basic info
                # (I don't append anything to job_list before continuing)
                self.logger.error(f"Wrong line length in squeue output! '{job}'")
                continue

            try:
                job_state_string = _MAP_STATUS_SLURM[job_state_raw]
            except KeyError:
                self.logger.warning(f"Unrecognized job_state '{job_state_raw}' for job id {this_job.job_id}")
                job_state_string = JobState.UNDETERMINED
            # QUEUED_HELD states are not specific states in SLURM;
            # they are instead set with state QUEUED, and then the
            # annotation tells if the job is held.
            # I check for 'Dependency', 'JobHeldUser',
            # 'JobHeldAdmin', 'BeginTime'.
            # Other states should not bring the job in QUEUED_HELD, I believe
            # (the man page of slurm seems to be incomplete, for instance
            # JobHeld* are not reported there; I also checked at the source code
            # of slurm 2.6 on github (https://github.com/SchedMD/slurm),
            # file slurm/src/common/slurm_protocol_defs.c,
            # and these seem all the states to be taken into account for the
            # QUEUED_HELD status).
            # There are actually a few others, like possible
            # failures, or partition-related reasons, but for the moment I
            # leave them in the QUEUED state.
            if job_state_string == JobState.QUEUED and this_job.annotation in [
                'Dependency',
                'JobHeldUser',
                'JobHeldAdmin',
                'BeginTime',
            ]:
                job_state_string = JobState.QUEUED_HELD

            this_job.job_state = job_state_string

            ####
            # Up to here, I just made sure that there were at least three
            # fields, to set the most important fields for a job.
            # I now check if the length is equal to the number of fields
            if len(job) < num_fields:
                # I store this job only with the information
                # gathered up to now, and continue to the next job
                # Also print a warning
                self.logger.warning(
                    f'Wrong line length in squeue output!Skipping optional fields. Line: `{jobdata_raw}`'
                )
                # I append this job before continuing
                job_list.append(this_job)
                continue

            # TODO: store executing_host?

            this_job.job_owner = thisjob_dict['username']

            try:
                this_job.num_machines = int(thisjob_dict['number_nodes'])
            except ValueError:
                self.logger.warning(
                    'The number of allocated nodes is not ' 'an integer ({}) for job id {}!'.format(
                        thisjob_dict['number_nodes'], this_job.job_id
                    )
                )

            ncpus = thisjob_dict['number_cpus']
            try:
                this_job.num_mpiprocs = int(ncpus)
            except ValueError:
                self.logger.warning(
                    f'The number of allocated cores is not an integer ({ncpus}) for job id {this_job.job_id}!'
                )

            # ALLOCATED NODES HERE
            # string may be in the format
            # nid00[684-685,722-723,748-749,958-959]
            # therefore it requires some parsing, that is unnecessary now.
            # I just store is as a raw string for the moment, and I leave
            # this_job.allocated_machines undefined
            if this_job.job_state == JobState.RUNNING:
                this_job.allocated_machines_raw = thisjob_dict['allocated_machines']

            this_job.queue_name = thisjob_dict['partition']

            try:
                walltime = self._convert_time(thisjob_dict['time_limit'])
                # TODO: Fix this type ignore, _convert_time can return None
                this_job.requested_wallclock_time_seconds = walltime  # type: ignore[assignment]
            except ValueError:
                self.logger.warning(f'Error parsing the time limit for job id {this_job.job_id}')

            # Only if it is RUNNING; otherwise it is not meaningful,
            # and may be not set (in my test, it is set to zero)
            if this_job.job_state == JobState.RUNNING:
                try:
                    wallclock_time_seconds = self._convert_time(thisjob_dict['time_used'])
                    if wallclock_time_seconds is None:
                        raise ValueError('SLURM wallclock time not set on a running job')
                    this_job.wallclock_time_seconds = wallclock_time_seconds
                except ValueError:
                    self.logger.warning(f'Error parsing time_used for job id {this_job.job_id}')

                try:
                    this_job.dispatch_time = self._parse_time_string(thisjob_dict['dispatch_time'])
                except ValueError:
                    self.logger.warning(f'Error parsing dispatch_time for job id {this_job.job_id}')

            try:
                this_job.submission_time = self._parse_time_string(thisjob_dict['submission_time'])
            except ValueError:
                self.logger.warning(f'Error parsing submission_time for job id {this_job.job_id}')

            this_job.title = thisjob_dict['job_name']

            # Everything goes here anyway for debugging purposes
            this_job.raw_data = job

            # Double check of redundant info
            # Not really useful now, allocated_machines in this
            # version of the plugin is never set
            if this_job.allocated_machines is not None and this_job.num_machines is not None:  # type: ignore[redundant-expr]
                if len(this_job.allocated_machines) != this_job.num_machines:
                    self.logger.error(
                        'The length of the list of allocated '
                        'nodes ({}) is different from the '
                        'expected number of nodes ({})!'.format(len(this_job.allocated_machines), this_job.num_machines)
                    )

            # I append to the list of jobs to return
            job_list.append(this_job)

        return job_list

    def _convert_time(self, string: str) -> int | None:
        """Convert a string in the format DD-HH:MM:SS to a number of seconds."""
        if string == 'UNLIMITED':
            return 2147483647  # == 2**31 - 1, largest 32-bit signed integer (68 years)

        if string == 'NOT_SET':
            return None

        groups = _TIME_REGEXP.match(string)
        if groups is None:
            self.logger.warning(f"Unrecognized format for time string '{string}'")
            raise ValueError('Unrecognized format for time string.')

        groupdict = groups.groupdict()
        # should not raise a ValueError, they all match digits only
        days = int(groupdict['days'] if groupdict['days'] is not None else 0)
        hours = int(groupdict['hours'] if groupdict['hours'] is not None else 0)
        mins = int(groupdict['minutes'] if groupdict['minutes'] is not None else 0)
        secs = int(groupdict['seconds'] if groupdict['seconds'] is not None else 0)

        return days * 86400 + hours * 3600 + mins * 60 + secs

    def _parse_time_string(self, string: str, fmt: str = '%Y-%m-%dT%H:%M:%S') -> datetime.datetime:
        """Parse a time string in the format returned from qstat -f and
        returns a datetime object.
        """

        try:
            time_struct = time.strptime(string, fmt)
        except Exception as exc:
            self.logger.debug(f'Unable to parse time string {string}, the message was {exc}')
            raise ValueError('Problem parsing the time string.')

        # I convert from a time_struct to a datetime object going through
        # the seconds since epoch, as suggested on stackoverflow:
        # http://stackoverflow.com/questions/1697815
        return datetime.datetime.fromtimestamp(time.mktime(time_struct))

    def _get_kill_command(self, jobid: str) -> str:
        """Return the command to kill the job with specified jobid."""
        submit_command = f'scancel {jobid}'

        self.logger.info(f'killing job {jobid}')

        return submit_command

    def _parse_kill_output(self, retval: int, stdout: str, stderr: str) -> bool:
        """Parse the output of the kill command.

        To be implemented by the plugin.

        :return: True if everything seems ok, False otherwise.
        """
        if retval != 0:
            self.logger.error(f'Error in _parse_kill_output: retval={retval}; stdout={stdout}; stderr={stderr}')
            return False

        try:
            transport_string = f' for {self.transport}'
        except SchedulerError:
            transport_string = ''

        if stderr.strip():
            self.logger.warning(f'in _parse_kill_output{transport_string}: there was some text in stderr: {stderr}')

        if stdout.strip():
            self.logger.warning(f'in _parse_kill_output{transport_string}: there was some text in stdout: {stdout}')

        return True

    def parse_output(
        self,
        detailed_job_info: dict[str, str | int] | None = None,
        stdout: str | None = None,
        stderr: str | None = None,
    ) -> ExitCode | None:
        """Parse the output of the scheduler.

        :param detailed_job_info: dictionary with the output returned by the `Scheduler.get_detailed_job_info` command.
            This should contain the keys `retval`, `stdout` and `stderr` corresponding to the return value, stdout and
            stderr returned by the accounting command executed for a specific job id.
        :param stdout: string with the output written by the scheduler to stdout.
        :param stderr: string with the output written by the scheduler to stderr.
        :return: None or an instance of :class:`aiida.engine.processes.exit_code.ExitCode`.
        :raises TypeError or ValueError: if the passed arguments have incorrect type or value.
        """
        from aiida.engine import CalcJob

        if detailed_job_info is not None:
            type_check(detailed_job_info, dict)

            try:
                detailed_stdout = detailed_job_info['stdout']
            except KeyError:
                raise ValueError('the `detailed_job_info` does not contain the required key `stdout`.')

            type_check(detailed_stdout, str)

            # The format of the detailed job info should be a multiline string, where the first line is the header, with
            # the labels of the projected attributes. The following line should be the values of those attributes for
            # the entire job. Any additional lines correspond to those values for any additional tasks that were run.
            lines = detailed_stdout.splitlines()  # type: ignore[union-attr]

            if len(lines) < 2:
                raise ValueError('the `detailed_job_info.stdout` contained less than two lines.')

            fields = lines[0].split('|')
            attributes = lines[1].split('|')

            if len(fields) != len(attributes):
                raise ValueError(
                    'first and second line in `detailed_job_info.stdout` differ in length: '
                    f'{len(fields)} vs {len(attributes)}'
                )

            data = dict(zip(fields, attributes))

            if data['State'] == 'OUT_OF_MEMORY':
                return CalcJob.exit_codes.ERROR_SCHEDULER_OUT_OF_MEMORY  # type: ignore[no-any-return]

            if data['State'] == 'TIMEOUT':
                return CalcJob.exit_codes.ERROR_SCHEDULER_OUT_OF_WALLTIME  # type: ignore[no-any-return]

            if data['State'] == 'NODE_FAIL':
                return CalcJob.exit_codes.ERROR_SCHEDULER_NODE_FAILURE  # type: ignore[no-any-return]

        # Alternatively, if the ``detailed_job_info`` is not defined or hasn't already determined an error, try to match
        # known error messages from the output written to the ``stderr`` descriptor.
        if stderr is not None:
            type_check(stderr, str)
            stderr_lower = stderr.lower()

            if re.match(r'.*exceeded.*memory limit.*', stderr_lower):
                return CalcJob.exit_codes.ERROR_SCHEDULER_OUT_OF_MEMORY  # type: ignore[no-any-return]

            if re.match(r'.*cancelled at.*due to time limit.*', stderr_lower):
                return CalcJob.exit_codes.ERROR_SCHEDULER_OUT_OF_WALLTIME  # type: ignore[no-any-return]

        return None
