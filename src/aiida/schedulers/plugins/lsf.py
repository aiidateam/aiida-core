###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Plugin for LSF.
This has been tested on the CERN lxplus cluster (LSF 9.1.3)
"""

import datetime

import aiida.schedulers
from aiida.common.escaping import escape_for_bash
from aiida.common.extendeddicts import AttributeDict
from aiida.schedulers import SchedulerError, SchedulerParsingError
from aiida.schedulers.datastructures import JobInfo, JobResource, JobState

from .bash import BashCliScheduler

# This maps LSF status codes to our own state list
#
# List of states from
# 'https://www-01.ibm.com/support/knowledgecenter/SSETD4_9.1.2/lsf_command_ref/bjobs.1.dita'
#
# PEND    The job is pending. That is, it has not yet been started.
#
# PROV    The job has been dispatched to a power-saved host that is waking up.
#         Before the job can be sent to the sbatchd, it is in a PROV state.
#
# PSUSP   The job has been suspended, either by its owner or the LSF administrator,
#         while pending.
#
# RUN     The job is currently running.
#
# USUSP   The job has been suspended, either by its owner or the LSF administrator,
#         while running.
#
# SSUSP   The job has been suspended by LSF due to either of the following two
#         causes:
#         - The load conditions on the execution host or hosts have exceeded a
#           threshold according to the loadStop vector defined for the host or queue.
#         - The run window of the job's queue is closed. See bqueues(1), bhosts(1),
#           and lsb.queues(5).
#
# DONE    The job has terminated with status of 0.
#
# EXIT    The job has terminated with a non-zero status - it may have been aborted
#         due to an error in its execution, or killed by its owner or the LSF
#         administrator.
#         For example, exit code 131 means that the job exceeded a configured
#         resource usage limit and LSF killed the job.
#
# UNKWN   mbatchd has lost contact with the sbatchd on the host on which the job runs.
#
# WAIT    For jobs submitted to a chunk job queue, members of a chunk job that
#         are waiting to run.
#
# ZOMBI   A job becomes ZOMBI if:
#         - A non-rerunnable job is killed by bkill while the sbatchd on the
#           execution host is unreachable and the job is shown as UNKWN.
#         - The host on which a rerunnable job is running is unavailable and the
#           job has been requeued by LSF with a new job ID, as if the job were submitted as a new job.
#         - After the execution host becomes available, LSF tries to kill the
#           ZOMBI job. Upon successful termination of the ZOMBI job, the job's
#           status is changed to EXIT.
#         With MultiCluster, when a job running on a remote execution cluster
#         becomes a ZOMBI job, the execution cluster treats the job the same way
#         as local ZOMBI jobs. In addition, it notifies the submission cluster
#         that the job is in ZOMBI state and the submission cluster requeues the job.
_MAP_STATUS_LSF = {
    'PEND': JobState.QUEUED,
    'PROV': JobState.QUEUED,
    'PSUSP': JobState.QUEUED_HELD,
    'USUSP': JobState.SUSPENDED,
    'SSUSP': JobState.SUSPENDED,
    'RUN': JobState.RUNNING,
    'DONE': JobState.DONE,
    'EXIT': JobState.DONE,
    'UNKWN': JobState.UNDETERMINED,
    'WAIT': JobState.QUEUED,
    'ZOMBI': JobState.UNDETERMINED,
}

# Separator between fields in the output of bjobs
_FIELD_SEPARATOR = '|'


class LsfJobResource(JobResource):
    """An implementation of JobResource for LSF, that supports
    the OPTIONAL specification of a parallel environment (a string) + the total
    number of processors.

    'parallel_env' should contain a string of the form
    "host1 host2! hostgroupA! host3 host4" where the "!" symbol indicates the
    first execution host candidates. Other hosts are added only if the number of
    processors asked is more than those of the first execution host.
    See https://www-01.ibm.com/support/knowledgecenter/SSETD4_9.1.2/lsf_command_ref/bsub.1.dita?lang=en
    for more details about the parallel environment definition (the -m option of bsub).
    """

    _default_fields = ('parallel_env', 'tot_num_mpiprocs', 'default_mpiprocs_per_machine', 'num_machines')

    @classmethod
    def validate_resources(cls, **kwargs):
        """Validate the resources against the job resource class of this scheduler.

        :param kwargs: dictionary of values to define the job resources
        :return: attribute dictionary with the parsed parameters populated
        :raises ValueError: if the resources are invalid or incomplete
        """
        from aiida.common.exceptions import ConfigurationError

        resources = AttributeDict()
        resources.parallel_env = kwargs.pop('parallel_env', '')
        resources.use_num_machines = kwargs.pop('use_num_machines', False)
        num_machines = kwargs.pop('num_machines', None)
        default_mpiprocs_per_machine = kwargs.pop('default_mpiprocs_per_machine', None)

        if not isinstance(resources.parallel_env, str):
            raise TypeError('`parallel_env` must be a string')

        if default_mpiprocs_per_machine is not None:
            raise ConfigurationError('`default_mpiprocs_per_machine` cannot be set.')

        if not resources.use_num_machines and num_machines is not None:
            raise ConfigurationError('`num_machines` cannot be set unless `use_num_machines` is `True`.')

        if resources.use_num_machines and num_machines is None:
            raise ConfigurationError('must set `num_machines` when `use_num_machines` is `True`.')

        if resources.use_num_machines and num_machines is not None:
            try:
                resources.num_machines = int(num_machines)
            except (KeyError, ValueError):
                raise TypeError('`num_machines` must be an integer')

        try:
            resources.tot_num_mpiprocs = int(kwargs.pop('tot_num_mpiprocs'))
        except (KeyError, ValueError) as exc:
            raise TypeError('`tot_num_mpiprocs` must be specified and must be an integer') from exc

        if resources.tot_num_mpiprocs <= 0:
            raise ValueError('tot_num_mpiprocs must be >= 1')

        return resources

    def __init__(self, **kwargs):
        """Initialize the job resources from the passed arguments (the valid keys can be
        obtained with the function self.get_valid_keys()).

        :raise ValueError: on invalid parameters.
        :raise TypeError: on invalid parameters.
        :raise aiida.common.ConfigurationError: if default_mpiprocs_per_machine was set for this
            computer, since LsfJobResource cannot accept this parameter.
        """
        resources = self.validate_resources(**kwargs)
        super().__init__(resources)

    def get_tot_num_mpiprocs(self):
        """Return the total number of cpus of this job resource."""
        return self.tot_num_mpiprocs

    @classmethod
    def accepts_default_mpiprocs_per_machine(cls):
        """Return True if this JobResource accepts a 'default_mpiprocs_per_machine'
        key, False otherwise.
        """
        return False


class LsfScheduler(BashCliScheduler):
    """Support for the IBM LSF scheduler

    https://www-01.ibm.com/support/knowledgecenter/SSETD4_9.1.2/lsf_welcome.html
    """

    _logger = aiida.schedulers.Scheduler._logger.getChild('lsf')

    # Query only by list of jobs and not by user
    _features = {
        'can_query_by_user': False,
    }

    # The class to be used for the job resource.
    _job_resource_class = LsfJobResource

    # Unavailable field: substate
    # Note! If you change the fields or fields length, update accordingly
    # also the parsing function!
    #     _joblist_fields= ["id", # job id
    #                       "stat", # job state
    #                       "exit_code", # exit code
    #                       "exit_reason", # reason for the job being in an exit state
    #                       "exec_host", # list of executing hosts (separated by ':')
    #                       "user", # user name
    #                       "slots", # number of nodes allocated
    #                       "queue", # queue of the job
    #                       "finish_time", # time at which the job has or should have
    #                                      # finished (date followed by hours:minutes)
    #                                      # It may also give one of the following symbols:
    #                                      # - E: The job has an estimated run time that
    #                                      #      has not been exceeded.
    #                                      # - L: The job has a hard run time limit
    #                                      #      specified but either has no estimated
    #                                      #      run time or the estimated run time is
    #                                      #      more than the hard run time limit.
    #                                      # - X: The job has exceeded its estimated run
    #                                      #      time and the time displayed is the time
    #                                      #      remaining until the job reaches its hard
    #                                      #      run time limit.
    #                                      # Also, a dash alone indicates that the job has no
    #                                      #   estimated run time and no run limit, or
    #                                      # that it has exceeded its run time but does
    #                                      # not have a hard limit and therefore runs until completion.
    #                       "time_left", # time left before completion, i.e. to reach
    #                                    # finish_time (hours:minutes)
    #                                    # See also 'finish_time' (symbols, and dash).
    #                       "run_time", # total time used by the job (in seconds)
    #                       "cpu_used", # CPU time in seconds (all CPUs cumulated, idle
    #                                   # time subtracted)
    #                       "submit_time", # submission time (date followed by hours:minutes)
    #                       "estart_time", # estimated start time (date followed by hours:minutes)
    #                       "start_time", # actual start time (date followed by hours:minutes)
    #                       "name", # job name
    #                       ]
    _joblist_fields = [
        'id',  # job id
        'stat',  # job state
        # "exit_code", # exit code
        'exit_reason',  # reason for the job being in an exit state
        'exec_host',  # list of executing hosts (separated by ':')
        'user',  # user name
        'slots',  # number of nodes allocated
        'max_req_proc',  # max number of CPU requested
        'exec_host',  # names of the hosting nodes
        'queue',  # queue of the job
        'finish_time',  # time at which the job has or should have
        # finished (date followed by hours:minutes)
        # It may also give one of the following symbols:
        # - E: The job has an estimated run time that
        #      has not been exceeded.
        # - L: The job has a hard run time limit
        #      specified but either has no estimated
        #      run time or the estimated run time is
        #      more than the hard run time limit.
        # - X: The job has exceeded its estimated run
        #      time and the time displayed is the time
        #      remaining until the job reaches its hard
        #      run time limit.
        # Also, a dash alone indicates that the job has no
        #   estimated run time and no run limit, or
        # that it has exceeded its run time but does
        # not have a hard limit and therefore runs until completion.
        'start_time',
        '%complete',
        'submit_time',  # submission time (date followed by hours:minutes)
        'name',  # job name
    ]

    def _get_joblist_command(self, jobs=None, user=None):
        """The command to report full information on existing jobs.

        Separates the fields with the _field_separator string order:
        jobnum, state, walltime, queue[=partition], user, numnodes, numcores, title
        """
        from aiida.common.exceptions import FeatureNotAvailable

        # I add the environment variable SLURM_TIME_FORMAT in front to be
        # sure to get the times in 'standard' format
        command = ['bjobs', '-noheader', f"-o '{' '.join(self._joblist_fields)} delimiter=\"{_FIELD_SEPARATOR}\"'"]

        if user and jobs:
            raise FeatureNotAvailable('Cannot query by user and job(s) in LSF')

        if user:
            command.append(f'-u{user}')

        if jobs:
            joblist = []
            if isinstance(jobs, str):
                joblist.append(jobs)
            else:
                if not isinstance(jobs, (tuple, list)):
                    raise TypeError("If provided, the 'jobs' variable must be a string or a list of strings")
                joblist = jobs
            command.append(' '.join(joblist))

        comm = ' '.join(command)
        self.logger.debug(f'bjobs command: {comm}')
        return comm

    def _get_detailed_job_info_command(self, job_id: str) -> str:
        """Return the command to run to get the detailed information on a job,
        even after the job has finished.

        The output text is just retrieved, and returned for logging purposes.
        """
        return f'bjobs -l {escape_for_bash(job_id)}'

    def _get_submit_script_header(self, job_tmpl):
        """Return the submit script header, using the parameters from the
        job_tmpl. See the following manual
        https://www-01.ibm.com/support/knowledgecenter/SSETD4_9.1.2/lsf_command_ref/bsub.1.dita?lang=en
        for more details about the possible options to bsub, in particular for
        the parallel environment definition (with the -m option).

        :param job_tmpl: an JobTemplate instance with relevant parameters set.
        """
        import re
        import string

        lines = []
        if job_tmpl.submit_as_hold:
            lines.append('#BSUB -H')

        if job_tmpl.rerunnable:
            lines.append('#BSUB -r')
        else:
            lines.append('#BSUB -rn')

        if job_tmpl.email:
            # If not specified, but email events are set, SLURM
            # sends the mail to the job owner by default
            lines.append(f'#BSUB -u {job_tmpl.email}')

        if job_tmpl.email_on_started:
            lines.append('#BSUB -B')
        if job_tmpl.email_on_terminated:
            lines.append('#BSUB -N')

        if job_tmpl.job_name:
            # The man page specifies only a limitation
            # on the job name to 4094 characters.
            # To be safe, I remove unwanted characters, and I
            # trim it to length 128.

            # I leave only letters, numbers, dots, dashes and underscores
            # Note: I don't compile the regexp, I am going to use it only once
            job_title = re.sub(r'[^a-zA-Z0-9_.-]+', '', job_tmpl.job_name)

            # prepend a 'j' (for 'job') before the string if the string
            # is now empty or does not start with a valid character
            if not job_title or (job_title[0] not in string.ascii_letters + string.digits):
                job_title = f'j{job_title}'

            # Truncate to the first 128 characters
            # Nothing is done if the string is shorter.
            job_title = job_title[:128]
            lines.append(f'#BSUB -J "{job_title}"')

        if not job_tmpl.import_sys_environment:
            self.logger.warning('LSF scheduler cannot ignore the user environment')

        if job_tmpl.sched_output_path:
            lines.append(f'#BSUB -o {job_tmpl.sched_output_path}')

        sched_error_path = getattr(job_tmpl, 'sched_error_path', None)
        if job_tmpl.sched_join_files:
            sched_error_path = f'{job_tmpl.sched_output_path}_'
            self.logger.warning(
                'LSF scheduler does not support joining '
                'the standard output and standard error '
                'files; std error file assigned instead '
                'to the file {}'.format(sched_error_path)
            )

        if sched_error_path:
            lines.append(f'#BSUB -e {job_tmpl.sched_error_path}')

        if job_tmpl.queue_name:
            lines.append(f'#BSUB -q {job_tmpl.queue_name}')

        if job_tmpl.account:
            lines.append(f'#BSUB -G {job_tmpl.account}')

        if job_tmpl.priority:
            # Specifies user-assigned job priority that orders all jobs
            # (from all users) in a queue. Valid values for priority
            # are any integers between 1 and MAX_USER_PRIORITY
            # (configured in lsb.params, displayed by "bparams -l").
            # Jobs are scheduled based first on their queue priority first, then
            # job priority, and lastly in first-come first-served order.
            lines.append(f'#BSUB -sp {job_tmpl.priority}')

        if not job_tmpl.job_resource:
            raise ValueError('Job resources (as the tot_num_mpiprocs) are required for the LSF scheduler plugin')

        if job_tmpl.job_resource.use_num_machines:
            lines.append(f'#BSUB -nnodes {job_tmpl.job_resource.num_machines}')
        else:
            lines.append(f'#BSUB -n {job_tmpl.job_resource.get_tot_num_mpiprocs()}')
            # Note:  make sure that PARALLEL_SCHED_BY_SLOT=Y is NOT
            # defined in lsb.params (you can check with the output of bparams -l).
            # Note: the -n option of bsub can also contain a maximum number of
            # procs to be used
        if job_tmpl.job_resource.parallel_env:
            lines.append(f'#BSUB -m "{job_tmpl.job_resource.parallel_env}"')

        if job_tmpl.max_wallclock_seconds is not None:
            # ABS_RUNLIMIT=Y should be set, in lsb.params (check with bparams -l)
            try:
                tot_secs = int(job_tmpl.max_wallclock_seconds)
                if tot_secs <= 0:
                    raise ValueError
            except ValueError as exc:
                raise ValueError(
                    'max_wallclock_seconds must be ' "a positive integer (in seconds)! It is instead '{}'" ''.format(
                        (job_tmpl.max_wallclock_seconds)
                    )
                ) from exc
            hours = tot_secs // 3600
            # The double negation results in the ceiling rather than the floor
            # of the division
            minutes = -(-(tot_secs % 3600) // 60)
            lines.append(f'#BSUB -W {hours:02d}:{minutes:02d}')

        # TODO: check if this is the memory per node
        if job_tmpl.max_memory_kb:
            try:
                physical_memory_kb = int(job_tmpl.max_memory_kb)
                if physical_memory_kb <= 0:
                    raise ValueError
            except ValueError as exc:
                raise ValueError(
                    f'max_memory_kb must be a positive integer (in kB)! It is instead `{job_tmpl.max_memory_kb}`'
                ) from exc
            # The -M option sets a per-process (soft) memory limit for all the
            # processes that belong to this job
            lines.append(f'#BSUB -M {physical_memory_kb}')

        if job_tmpl.custom_scheduler_commands:
            lines.append(job_tmpl.custom_scheduler_commands)

        # The following seems to be the only way to copy the input files
        # to the node where the computation are actually launched (the
        # -f option of bsub that does not always work...)
        # TODO: implement the case when LSB_OUTDIR is not properly defined...
        # (need to add the line "#BSUB -outdir PATH_TO_REMOTE_DIRECTORY")
        # IMPORTANT! the -z is needed, because if LSB_OUTDIR is not defined,
        # you would do 'cp -R /* .' basically copying ALL FILES in your
        # computer (including mounted partitions) in the current dir!!
        lines.append(
            """
if [ ! -z "$LSB_OUTDIR" ]
then
  cp -R "$LSB_OUTDIR"/* .
fi
"""
        )

        return '\n'.join(lines)

    def _get_submit_script_footer(self, job_tmpl):
        """Return the submit script final part, using the parameters from the
        job_tmpl.

        :param job_tmpl: a JobTemplate instance with relevant parameters set.
        """
        # line to retrieve back the output of the computation (rather than
        # the -f option of bsub that does not always work...)
        # TODO: implement the case when LSB_OUTDIR is not properly defined...
        # (need to add the line "#BSUB -outdir PATH_TO_REMOTE_DIRECTORY")
        # As above, important to check if the folder variable is defined
        return """
if [ ! -z "$LSB_OUTDIR" ]
then
   cp -R * "$LSB_OUTDIR"
fi
"""

    def _get_submit_command(self, submit_script):
        """Return the string to execute to submit a given script.

        :param submit_script: the path of the submit script relative to the working
                directory.
                IMPORTANT: submit_script should be already escaped.
        """
        submit_command = f'bsub < {submit_script}'

        self.logger.info(f'submitting with: {submit_command}')

        return submit_command

    def _parse_joblist_output(self, retval, stdout, stderr):
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
        num_fields = len(self._joblist_fields)

        if retval != 0:
            self.logger.warning(f'Error in _parse_joblist_output: retval={retval}; stdout={stdout}; stderr={stderr}')
            raise SchedulerError(
                f'Error during parsing joblist output, retval={retval}\nstdout={stdout}\nstderr={stderr}'
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
            # Each job should have all fields.
            if len(job) != num_fields:
                # I skip this calculation
                # (I don't append anything to job_list before continuing)
                self.logger.error(f"Wrong line length in squeue output! '{job}'")
                continue

            this_job = JobInfo()
            this_job.job_id = job[0]
            this_job.annotation = job[2]
            job_state_raw = job[1]

            try:
                job_state_string = _MAP_STATUS_LSF[job_state_raw]
            except KeyError:
                self.logger.warning(f"Unrecognized job_state '{job_state_raw}' for job id {this_job.job_id}")
                job_state_string = JobState.UNDETERMINED

            this_job.job_state = job_state_string

            # I get the remaining fields
            # The first three were already obtained
            # I know that the length is exactly num_fields because
            # I used split(_field_separator, num_fields) before
            # when creting 'job'
            #            (_, _, _, executing_host, username, number_nodes,
            #             number_cpus, allocated_machines, partition,
            #             time_limit, time_used, dispatch_time, job_name) = job
            (
                _,
                _,
                _,
                _,
                username,
                number_nodes,
                number_cpus,
                allocated_machines,
                partition,
                finish_time,
                start_time,
                percent_complete,
                submission_time,
                job_name,
            ) = job

            this_job.job_owner = username
            try:
                this_job.num_machines = int(number_nodes)
            except ValueError:
                self.logger.warning(
                    f'The number of allocated nodes is not an integer ({number_nodes}) for job id {this_job.job_id}!'
                )

            try:
                this_job.num_mpiprocs = int(number_cpus)
            except ValueError:
                self.logger.warning(
                    f'The number of allocated cores is not an integer ({number_cpus}) for job id {this_job.job_id}!'
                )

            # ALLOCATED NODES HERE
            # string may be in the format
            # nid00[684-685,722-723,748-749,958-959]
            # therefore it requires some parsing, that is unnecessary now.
            # I just store is as a raw string for the moment, and I leave
            # this_job.allocated_machines undefined
            if this_job.job_state == JobState.RUNNING:
                this_job.allocated_machines_raw = allocated_machines

            this_job.queue_name = partition

            psd_finish_time = self._parse_time_string(finish_time, fmt='%b %d %H:%M')
            psd_start_time = self._parse_time_string(start_time, fmt='%b %d %H:%M')
            psd_submission_time = self._parse_time_string(submission_time, fmt='%b %d %H:%M')

            # Now get the time in seconds which has been used
            # Only if it is RUNNING; otherwise it is not meaningful,
            # and may be not set (in my test, it is set to zero)
            if this_job.job_state == JobState.RUNNING:
                try:
                    requested_walltime = psd_finish_time - psd_start_time
                    # fix of a weird bug. Since the year is not parsed, it is assumed
                    # to always be 1900. Therefore, job submitted
                    # in december and finishing in january would produce negative time differences
                    if requested_walltime.total_seconds() < 0:
                        import datetime

                        old_month = psd_finish_time.month
                        old_day = psd_finish_time.day
                        old_hour = psd_finish_time.hour
                        old_minute = psd_finish_time.minute
                        new_year = psd_start_time.year + 1
                        # note: we assume that no job will last more than 1 year...
                        psd_finish_time = datetime.datetime(
                            year=new_year, month=old_month, day=old_day, hour=old_hour, minute=old_minute
                        )
                        requested_walltime = psd_finish_time - psd_start_time

                    this_job.requested_wallclock_time_seconds = requested_walltime.total_seconds()
                except (TypeError, ValueError):
                    self.logger.warning(f'Error parsing the time limit for job id {this_job.job_id}')

                try:
                    psd_percent_complete = float(percent_complete.strip(' L').strip('%'))
                    this_job.wallclock_time_seconds = requested_walltime.total_seconds() * psd_percent_complete / 100.0
                except ValueError:
                    self.logger.warning(f'Error parsing the time used for job id {this_job.job_id}')

            try:
                this_job.submission_time = psd_submission_time
            except ValueError:
                self.logger.warning(f'Error parsing submission time for job id {this_job.job_id}')

            this_job.title = job_name

            # Everything goes here anyway for debugging purposes
            this_job.raw_data = job

            # Double check of redundant info
            # Not really useful now, allocated_machines in this
            # version of the plugin is never set
            if this_job.allocated_machines is not None and this_job.num_machines is not None:
                if len(this_job.allocated_machines) != this_job.num_machines:
                    self.logger.error(
                        'The length of the list of allocated '
                        'nodes ({}) is different from the '
                        'expected number of nodes ({})!'.format(len(this_job.allocated_machines), this_job.num_machines)
                    )

            # I append to the list of jobs to return
            job_list.append(this_job)

        return job_list

    def _parse_submit_output(self, retval, stdout, stderr):
        """Parse the output of the submit command, as returned by executing the
        command returned by _get_submit_command command.

        To be implemented by the plugin.

        Return a string with the JobID.
        """
        if retval != 0:
            self.logger.error(f'Error in _parse_submit_output: retval={retval}; stdout={stdout}; stderr={stderr}')
            raise SchedulerError(f'Error during submission, retval={retval}\nstdout={stdout}\nstderr={stderr}')

        try:
            transport_string = f' for {self.transport}'
        except SchedulerError:
            transport_string = ''

        if stderr.strip():
            self.logger.warning(f'in _parse_submit_output{transport_string}: there was some text in stderr: {stderr}')

        try:
            return stdout.strip().split('Job <')[1].split('>')[0]
        except IndexError as exc:
            raise SchedulerParsingError(f'Cannot parse submission output: `{stdout}`') from exc

    def _parse_time_string(self, string, fmt='%b %d %H:%M'):
        """Parse a time string and returns a datetime object.
        Example format: 'Feb  2 07:39' or 'Feb  2 07:39 L'
        """

        if string == '-':
            return None

        # The year is not specified. I have to add it, and I set it to the
        # current year. This is actually not correct, if we are close
        # new year... we should ask the scheduler also the year.
        actual_string = f'{datetime.datetime.now().year} {string}'
        actual_fmt = f'%Y {fmt}'

        try:
            try:
                thetime = datetime.datetime.strptime(actual_string, actual_fmt)
            except ValueError:
                thetime = datetime.datetime.strptime(actual_string, f'{actual_fmt} L')
        except Exception as exc:
            self.logger.debug(f'Unable to parse time string {string}, the message was {exc}')
            raise ValueError(f'Problem parsing the time string: `{string}`') from exc

        return thetime

    def _get_kill_command(self, jobid):
        """Return the command to kill the job with specified jobid."""
        submit_command = f'bkill {jobid}'
        self.logger.info(f'killing job {jobid}')
        return submit_command

    def _parse_kill_output(self, retval, stdout, stderr):
        """Parse the output of the kill command.

        :return: True if everything seems ok, False otherwise.
        """
        if retval == 255:
            self.logger.error(
                f'Error in _parse_kill_output: retval={retval} (Job already finished); stdout={stdout}; stderr={stderr}'
            )
            return False

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
