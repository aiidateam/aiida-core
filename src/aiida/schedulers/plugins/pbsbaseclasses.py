###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Base classes for PBSPro and PBS/Torque plugins."""

from __future__ import annotations

import logging

from aiida.common.escaping import escape_for_bash
from aiida.schedulers import SchedulerError, SchedulerParsingError
from aiida.schedulers.datastructures import JobInfo, JobState, MachineInfo, NodeNumberJobResource

from .bash import BashCliScheduler

_LOGGER = logging.getLogger(__name__)

# This maps PbsPro status letters to our own status list

# List of states from the man page of qstat
# B  Array job has at least one subjob running.
# E  Job is exiting after having run.
# F  Job is finished.
# H  Job is held.
# M  Job was moved to another server.
# Q  Job is queued.
# R  Job is running.
# S  Job is suspended.
# T  Job is being moved to new location.
# U  Cycle-harvesting job is suspended due to  keyboard  activity.
# W  Job is waiting for its submitter-assigned start time to be reached.
# X  Subjob has completed execution or has been deleted.

# These are instead the states from PBS/Torque v.2.4.16 (from Ubuntu)
# C -  Job is completed after having run [different from above, but not clashing]
# E -  Job is exiting after having run. [same as above]
# H -  Job is held. [same as above]
# Q -  job is queued, eligible to run or routed. [same as above]
# R -  job is running. [same as above]
# T -  job is being moved to new location. [same as above]
# W -  job is waiting for its execution time
#     (-a option) to be reached. [similar to above]
# S -  (Unicos only) job is suspend. [as above]

_MAP_STATUS_PBS_COMMON = {
    'B': JobState.RUNNING,
    'E': JobState.RUNNING,  # If exiting, for our purposes it is still running
    'F': JobState.DONE,
    'H': JobState.QUEUED_HELD,
    'M': JobState.UNDETERMINED,  # TODO: check if this is ok?
    'Q': JobState.QUEUED,
    'R': JobState.RUNNING,
    'S': JobState.SUSPENDED,
    'T': JobState.QUEUED,  # We assume that from the AiiDA point of view
    # it is still queued
    'U': JobState.SUSPENDED,
    'W': JobState.QUEUED,
    'X': JobState.DONE,
    'C': JobState.DONE,  # This is the completed state of PBS/Torque
}


class PbsJobResource(NodeNumberJobResource):
    """Class for PBS job resources."""

    @classmethod
    def validate_resources(cls, **kwargs):
        """Validate the resources against the job resource class of this scheduler.

        This extends the base class validator and calculates the `num_cores_per_machine` fields to pass to PBSlike
        schedulers. Checks that `num_cores_per_machine` is a multiple of `num_cores_per_mpiproc` and/or
        `num_mpiprocs_per_machine`.

        :param kwargs: dictionary of values to define the job resources
        :return: attribute dictionary with the parsed parameters populated
        :raises ValueError: if the resources are invalid or incomplete
        """
        resources = super().validate_resources(**kwargs)

        if resources.num_cores_per_machine is not None and resources.num_cores_per_mpiproc is not None:
            if resources.num_cores_per_machine != resources.num_cores_per_mpiproc * resources.num_mpiprocs_per_machine:
                raise ValueError(
                    '`num_cores_per_machine` must be equal to `num_cores_per_mpiproc * num_mpiprocs_per_machine` and in'
                    ' particular it should be a multiple of `num_cores_per_mpiproc` and/or `num_mpiprocs_per_machine`'
                )

        elif resources.num_cores_per_mpiproc is not None:
            if resources.num_cores_per_mpiproc < 1:
                raise ValueError('num_cores_per_mpiproc must be greater than or equal to one.')

            # In this plugin we never used num_cores_per_mpiproc so if it is not defined it is OK.
            resources.num_cores_per_machine = resources.num_cores_per_mpiproc * resources.num_mpiprocs_per_machine

        return resources


class PbsBaseClass(BashCliScheduler):
    """Base class with support for the PBSPro scheduler

    (http://www.pbsworks.com/) and for PBS and Torque
    (http://www.adaptivecomputing.com/products/open-source/torque/).

    Only a few properties need to be redefined, see examples of the pbspro and
    torque plugins
    """

    # Query only by list of jobs and not by user
    _features = {
        'can_query_by_user': False,
    }

    # The class to be used for the job resource.
    _job_resource_class = PbsJobResource

    _map_status = _MAP_STATUS_PBS_COMMON

    def _get_resource_lines(
        self,
        num_machines: int,
        num_mpiprocs_per_machine: int | None,
        num_cores_per_machine: int | None,
        max_memory_kb: int | None,
        max_wallclock_seconds: int | None,
    ) -> list[str]:
        """Return a set a list of lines (possibly empty) with the header
        lines relative to:

        * num_machines
        * num_mpiprocs_per_machine
        * num_cores_per_machine
        * max_memory_kb
        * max_wallclock_seconds

        This is done in an external function because it may change in
        different subclasses.
        """
        raise NotImplementedError('Implement the _get_resource_lines in each subclass!')

    def _get_joblist_command(self, jobs=None, user=None):
        """The command to report full information on existing jobs.

        TODO: in the case of job arrays, decide what to do (i.e., if we want
              to pass the -t options to list each subjob).
        """
        from aiida.common.exceptions import FeatureNotAvailable

        command = ['qstat', '-f']

        if jobs and user:
            raise FeatureNotAvailable('Cannot query by user and job(s) in PBS')

        if user:
            command.append(f'-u{user}')

        if jobs:
            if isinstance(jobs, str):
                command.append(f'{escape_for_bash(jobs)}')
            else:
                try:
                    command.append(f"{' '.join(escape_for_bash(j) for j in jobs)}")
                except TypeError:
                    raise TypeError("If provided, the 'jobs' variable must be a string or an iterable of strings")

        comm = ' '.join(command)
        _LOGGER.debug(f'qstat command: {comm}')
        return comm

    def _get_detailed_job_info_command(self, job_id: str) -> str:
        """Return the command to run to get the detailed information on a job,
        even after the job has finished.

        The output text is just retrieved, and returned for logging purposes.
        """
        return f'tracejob -v {escape_for_bash(job_id)}'

    def _get_submit_script_header(self, job_tmpl):
        """Return the submit script header, using the parameters from the
        job_tmpl.

        Args:
        -----
           job_tmpl: an JobTemplate instance with relevant parameters set.

        TODO: truncate the title if too long
        """
        import re
        import string

        empty_line = ''

        lines = []
        if job_tmpl.submit_as_hold:
            lines.append('#PBS -h')

        if job_tmpl.rerunnable:
            lines.append('#PBS -r y')
        else:
            lines.append('#PBS -r n')

        if job_tmpl.email:
            # If not specified, but email events are set, PBSPro
            # sends the mail to the job owner by default
            lines.append(f'#PBS -M {job_tmpl.email}')

        email_events = ''
        if job_tmpl.email_on_started:
            email_events += 'b'
        if job_tmpl.email_on_terminated:
            email_events += 'ea'
        if email_events:
            lines.append(f'#PBS -m {email_events}')
            if not job_tmpl.email:
                _LOGGER.info(
                    'Email triggers provided to PBSPro script for job,'
                    'but no email field set; will send emails to '
                    'the job owner as set in the scheduler'
                )
        else:
            lines.append('#PBS -m n')

        if job_tmpl.job_name:
            # From qsub man page:
            # string, up to 15 characters in length.  It must
            # consist of an  alphabetic  or  numeric  character
            # followed  by printable, non-white-space characters.
            # Default:  if a script is used to submit the job, the job's name
            # is the name of the script.  If no script  is  used,  the  job's
            # name is "STDIN".
            #
            # I leave only letters, numbers, dots, dashes and underscores
            # Note: I don't compile the regexp, I am going to use it only once
            job_title = re.sub(r'[^a-zA-Z0-9_.-]+', '', job_tmpl.job_name)

            # prepend a 'j' (for 'job') before the string if the string
            # is now empty or does not start with a valid charachter
            if not job_title or (job_title[0] not in string.ascii_letters + string.digits):
                job_title = f'j{job_title}'

            # Truncate to the first 15 characters
            # Nothing is done if the string is shorter.
            job_title = job_title[:15]

            lines.append(f'#PBS -N {job_title}')

        if job_tmpl.import_sys_environment:
            lines.append('#PBS -V')

        if job_tmpl.sched_output_path:
            lines.append(f'#PBS -o {job_tmpl.sched_output_path}')

        if job_tmpl.sched_join_files:
            # from qsub man page:
            # 'oe': Standard error and standard output are merged  into
            #       standard output
            # 'eo': Standard error and standard output are merged  into
            #       standard error
            # 'n' : Standard error and standard output are not merged (default)
            lines.append('#PBS -j oe')
            if job_tmpl.sched_error_path:
                _LOGGER.info(
                    'sched_join_files is True, but sched_error_path is set in '
                    'PBSPro script; ignoring sched_error_path'
                )
        elif job_tmpl.sched_error_path:
            lines.append(f'#PBS -e {job_tmpl.sched_error_path}')

        if job_tmpl.queue_name:
            lines.append(f'#PBS -q {job_tmpl.queue_name}')

        if job_tmpl.account:
            lines.append(f'#PBS -A {job_tmpl.account}')

        if job_tmpl.priority:
            # Priority of the job.  Format: host-dependent integer.  Default:
            # zero.   Range:  [-1024,  +1023] inclusive.  Sets job's Priority
            # attribute to priority.
            # TODO: Here I expect that priority is passed in the correct PBSPro
            # format. To fix.
            lines.append(f'#PBS -p {job_tmpl.priority}')

        if not job_tmpl.job_resource:
            raise ValueError('Job resources (as the num_machines) are required for the PBSPro scheduler plugin')

        resource_lines = self._get_resource_lines(
            num_machines=job_tmpl.job_resource.num_machines,
            num_mpiprocs_per_machine=job_tmpl.job_resource.num_mpiprocs_per_machine,
            num_cores_per_machine=job_tmpl.job_resource.num_cores_per_machine,
            max_memory_kb=job_tmpl.max_memory_kb,
            max_wallclock_seconds=job_tmpl.max_wallclock_seconds,
        )

        lines += resource_lines

        if job_tmpl.custom_scheduler_commands:
            lines.append(job_tmpl.custom_scheduler_commands)

        # Required to change directory to the working directory, that is
        # the one from which the job was submitted
        lines.append('cd "$PBS_O_WORKDIR"')
        lines.append(empty_line)

        return '\n'.join(lines)

    def _get_submit_command(self, submit_script):
        """Return the string to execute to submit a given script.

        Args:
        -----
            submit_script: the path of the submit script relative to the working
                directory.
                IMPORTANT: submit_script should be already escaped.
        """
        submit_command = f'qsub {submit_script}'

        _LOGGER.info(f'submitting with: {submit_command}')

        return submit_command

    def _parse_joblist_output(self, retval, stdout, stderr):
        """Parse the queue output string, as returned by executing the
        command returned by _get_joblist_command command (qstat -f).

        Return a list of JobInfo objects, one of each job,
        each relevant parameters implemented.

        Note: depending on the scheduler configuration, finished jobs may
            either appear here, or not.
            This function will only return one element for each job find
            in the qstat output; missing jobs (for whatever reason) simply
            will not appear here.
        """
        # I don't raise because if I pass a list of jobs, I get a non-zero status
        # if one of the job is not in the list anymore

        # retval should be zero
        # if retval != 0:
        # _LOGGER.warning("Error in _parse_joblist_output: retval={}; "
        #    "stdout={}; stderr={}".format(retval, stdout, stderr))

        # issue a warning if there is any stderr output
        # but I strip lines containing "Unknown Job Id", that happens
        # also when I ask for a calculation that has finished
        #
        # I also strip for "Job has finished" because this happens for
        # those schedulers configured to leave the job in the output
        # of qstat for some time after job completion.
        filtered_stderr = '\n'.join(
            line for line in stderr.split('\n') if 'Unknown Job Id' not in line and 'Job has finished' not in line
        )
        if filtered_stderr.strip():
            _LOGGER.warning(f"Warning in _parse_joblist_output, non-empty (filtered) stderr='{filtered_stderr}'")
            if retval != 0:
                raise SchedulerError(f'Error during qstat parsing, retval={retval}\nstdout={stdout}\nstderr={stderr}')

        jobdata_raw = []  # will contain raw data parsed from qstat output
        # Get raw data and split in lines
        for line_num, line in enumerate(stdout.split('\n'), start=1):
            # Each new job stanza starts with the string 'Job Id:': I
            # create a new item in the jobdata_raw list
            if line.startswith('Job Id:'):
                jobdata_raw.append({'id': line.split(':', 1)[1].strip(), 'lines': [], 'warning_lines_idx': []})
                # warning_lines_idx: lines that do not start either with
                # tab or space
            elif line.strip():
                # This is a non-empty line, therefore it is an attribute
                # of the last job found
                if not jobdata_raw:
                    # The list is still empty! (This means that I found a
                    # non-empty line, before finding the first 'Job Id:'
                    # string: it is an error. However this may happen
                    # only before the first job.
                    raise SchedulerParsingError('I did not find the header for the first job')
                    # _LOGGER.warning("I found some text before the "
                    # "first job: {}".format(l))
                elif line.startswith(' '):
                    # If it starts with a space, it is a new field
                    jobdata_raw[-1]['lines'].append(line)
                elif line.startswith('\t'):
                    # If a line starts with a TAB,
                    # I append to the previous string
                    # stripping the TAB
                    if not jobdata_raw[-1]['lines']:
                        raise SchedulerParsingError(
                            f'Line {line_num} is the first line of the job, but it starts with a TAB! ({line})'
                        )
                    jobdata_raw[-1]['lines'][-1] += line[1:]
                else:
                    # raise SchedulerParsingError(
                    #    "Wrong starting character at line {}! ({})"
                    #    "".format(line_num, l))
                    ## For some reasons, the output of 'comment' and
                    ## 'Variable_List', for instance, can have
                    ## newlines if they are included... # I do a
                    ## workaround
                    jobdata_raw[-1]['lines'][-1] += f'\n{line}'
                    jobdata_raw[-1]['warning_lines_idx'].append(len(jobdata_raw[-1]['lines']) - 1)

        # Create dictionary and parse specific fields
        job_list = []
        for job in jobdata_raw:
            this_job = JobInfo()
            this_job.job_id = job['id']

            lines_without_equals_sign = [i for i in job['lines'] if '=' not in i]

            # There are lines without equals sign: this is bad
            if lines_without_equals_sign:
                # Should I only warn?
                _LOGGER.error(f'There are lines without equals sign! {lines_without_equals_sign}')
                raise SchedulerParsingError('There are lines without equals sign.')

            raw_data = {
                i.split('=', 1)[0].strip().lower(): i.split('=', 1)[1].lstrip() for i in job['lines'] if '=' in i
            }

            ## I ignore the errors for the time being - this seems to be
            ## a problem if there are \n in the content of some variables?
            ## I consider this a workaround...
            # for line_with_warning in set(job['warning_lines_idx']):
            #    if job['lines'][line_with_warning].split(
            #        '=',1)[0].strip().lower() != "comment":
            #        raise SchedulerParsingError(
            #            "Wrong starting character in one of the lines "
            #            "of job {}, and it's not a comment! ({})"
            #            "".format(this_job.job_id,
            #                      job['lines'][line_with_warning]))

            problematic_fields = []
            for line_with_warning in set(job['warning_lines_idx']):
                problematic_fields.append(job['lines'][line_with_warning].split('=', 1)[0].strip().lower())
            if problematic_fields:
                # These are the fields that contain unexpected newlines
                raw_data['warning_fields_with_newlines'] = problematic_fields

            # I believe that exit_status and terminating_signal cannot be
            # retrieved from the qstat -f output.

            # I wrap calls in try-except clauses to avoid errors if a field
            # is missing
            try:
                this_job.title = raw_data['job_name']
            except KeyError:
                _LOGGER.debug(f"No 'job_name' field for job id {this_job.job_id}")

            try:
                this_job.annotation = raw_data['comment']
            except KeyError:
                # Many jobs do not have a comment; I do not complain about it.
                pass
                # _LOGGER.debug("No 'comment' field for job id {}".format(
                #    this_job.job_id))

            try:
                job_state_string = raw_data['job_state']
                try:
                    this_job.job_state = self._map_status[job_state_string]
                except KeyError:
                    _LOGGER.warning(f"Unrecognized job_state '{job_state_string}' for job id {this_job.job_id}")
                    this_job.job_state = JobState.UNDETERMINED
            except KeyError:
                _LOGGER.debug(f"No 'job_state' field for job id {this_job.job_id}")
                this_job.job_state = JobState.UNDETERMINED

            try:
                this_job.job_substate = raw_data['substate']
            except KeyError:
                _LOGGER.debug(f"No 'substate' field for job id {this_job.job_id}")

            try:
                exec_hosts = raw_data['exec_host'].split('+')
            except KeyError:
                # No exec_host information found (it may be ok, if the job
                # is not running)
                pass
            else:
                # parse each host; syntax, from the man page:
                # hosta/J1+hostb/J2*P+...
                # where  J1 and J2 are an index of the job
                # on the named host and P is the number of
                # processors allocated from that host to this job.
                # P does not appear if it is 1.
                try:
                    exec_host_list = []
                    for exec_host in exec_hosts:
                        node = MachineInfo()
                        node.name, data = exec_host.split('/')
                        data = data.split('*')
                        if len(data) == 1:
                            node.job_index = int(data[0])
                            node.num_cpus = 1
                        elif len(data) == 2:
                            node.job_index = int(data[0])
                            node.num_cpus = int(data[1])
                        else:
                            raise ValueError(
                                f'Wrong number of pieces: {len(data)} instead of 1 or 2 in exec_hosts: {exec_hosts}'
                            )
                        exec_host_list.append(node)
                    this_job.allocated_machines = exec_host_list
                except Exception as exc:
                    _LOGGER.debug(
                        f'Problem parsing the node names, I got Exception {type(exc)!s} with message {exc}; '
                        f'exec_hosts was {exec_hosts}'
                    )

            try:
                # I strip the part after the @: is this always ok?
                this_job.job_owner = raw_data['job_owner'].split('@')[0]
            except KeyError:
                _LOGGER.debug(f"No 'job_owner' field for job id {this_job.job_id}")

            try:
                this_job.num_cpus = int(raw_data['resource_list.ncpus'])
                # TODO: understand if this is the correct field also for multithreaded (OpenMP) jobs.
            except KeyError:
                _LOGGER.debug(f"No 'resource_list.ncpus' field for job id {this_job.job_id}")
            except ValueError:
                _LOGGER.warning(
                    f"'resource_list.ncpus' is not an integer "
                    f"({raw_data['resource_list.ncpus']}) for job id {this_job.job_id}!"
                )

            try:
                this_job.num_mpiprocs = int(raw_data['resource_list.mpiprocs'])
                # TODO: understand if this is the correct field also for multithreaded (OpenMP) jobs.
            except KeyError:
                _LOGGER.debug(f"No 'resource_list.mpiprocs' field for job id {this_job.job_id}")
            except ValueError:
                _LOGGER.warning(
                    f"'resource_list.mpiprocs' is not an integer "
                    f"({raw_data['resource_list.mpiprocs']}) for job id {this_job.job_id}!"
                )

            try:
                this_job.num_machines = int(raw_data['resource_list.nodect'])
            except KeyError:
                _LOGGER.debug(f"No 'resource_list.nodect' field for job id {this_job.job_id}")
            except ValueError:
                _LOGGER.warning(
                    f"'resource_list.nodect' is not an integer "
                    f"{raw_data['resource_list.nodect']}) for job id {this_job.job_id}!"
                )

            # Double check of redundant info
            if this_job.allocated_machines is not None and this_job.num_machines is not None:
                if len(set(machine.name for machine in this_job.allocated_machines)) != this_job.num_machines:
                    _LOGGER.error(
                        f'The length of the list of allocated nodes ({len(this_job.allocated_machines)}) is different '
                        f'from the expected number of nodes ({this_job.num_machines})!'
                    )

            try:
                this_job.queue_name = raw_data['queue']
            except KeyError:
                _LOGGER.debug(f"No 'queue' field for job id {this_job.job_id}")

            try:
                this_job.requested_wallclock_time = self._convert_time(raw_data['resource_list.walltime'])
            except KeyError:
                _LOGGER.debug(f"No 'resource_list.walltime' field for job id {this_job.job_id}")
            except ValueError:
                _LOGGER.warning(f"Error parsing 'resource_list.walltime' for job id {this_job.job_id}")

            try:
                this_job.wallclock_time_seconds = self._convert_time(raw_data['resources_used.walltime'])
            except KeyError:
                # May not have started yet
                pass
            except ValueError:
                _LOGGER.warning(f"Error parsing 'resources_used.walltime' for job id {this_job.job_id}")

            try:
                this_job.cpu_time = self._convert_time(raw_data['resources_used.cput'])
            except KeyError:
                # May not have started yet
                pass
            except ValueError:
                _LOGGER.warning(f"Error parsing 'resources_used.cput' for job id {this_job.job_id}")

            #
            # ctime: The time that the job was created
            # mtime: The time that the job was last modified, changed state,
            #        or changed locations.
            # qtime: The time that the job entered the current queue
            # stime: The time when the job started execution.
            # etime: The time that the job became eligible to run, i.e. in a
            #        queued state while residing in an execution queue.

            try:
                this_job.submission_time = self._parse_time_string(raw_data['ctime'])
            except KeyError:
                _LOGGER.debug(f"No 'ctime' field for job id {this_job.job_id}")
            except ValueError:
                _LOGGER.warning(f"Error parsing 'ctime' for job id {this_job.job_id}")

            try:
                this_job.dispatch_time = self._parse_time_string(raw_data['stime'])
            except KeyError:
                # The job may not have been started yet
                pass
            except ValueError:
                _LOGGER.warning(f"Error parsing 'stime' for job id {this_job.job_id}")

            # TODO: see if we want to set also finish_time for finished jobs, if there are any

            # Everything goes here anyway for debugging purposes
            this_job.raw_data = raw_data

            # I append to the list of jobs to return
            job_list.append(this_job)

        return job_list

    @staticmethod
    def _convert_time(string):
        """Convert a string in the format HH:MM:SS to a number of seconds."""
        pieces = string.split(':')
        if len(pieces) != 3:
            _LOGGER.warning(f'Wrong number of pieces (expected 3) for time string {string}')
            raise ValueError('Wrong number of pieces for time string.')

        try:
            hours = int(pieces[0])
            if hours < 0:
                raise ValueError
        except ValueError:
            _LOGGER.warning(f'Not a valid number of hours: {pieces[0]}')
            raise ValueError('Not a valid number of hours.')

        try:
            mins = int(pieces[1])
            if mins < 0:
                raise ValueError
        except ValueError:
            _LOGGER.warning(f'Not a valid number of minutes: {pieces[1]}')
            raise ValueError('Not a valid number of minutes.')

        try:
            secs = int(pieces[2])
            if secs < 0:
                raise ValueError
        except ValueError:
            _LOGGER.warning(f'Not a valid number of seconds: {pieces[2]}')
            raise ValueError('Not a valid number of seconds.')

        return hours * 3600 + mins * 60 + secs

    @staticmethod
    def _parse_time_string(string, fmt='%a %b %d %H:%M:%S %Y'):
        """Parse a time string in the format returned from qstat -f and
        returns a datetime object.
        """
        import datetime
        import time

        try:
            time_struct = time.strptime(string, fmt)
        except Exception as exc:
            _LOGGER.debug(f'Unable to parse time string {string}, the message was {exc}')
            raise ValueError('Problem parsing the time string.')

        # I convert from a time_struct to a datetime object going through
        # the seconds since epoch, as suggested on stackoverflow:
        # http://stackoverflow.com/questions/1697815
        return datetime.datetime.fromtimestamp(time.mktime(time_struct))

    def _parse_submit_output(self, retval, stdout, stderr):
        """Parse the output of the submit command, as returned by executing the
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
        submit_command = f'qdel {jobid}'

        _LOGGER.info(f'killing job {jobid}')

        return submit_command

    def _parse_kill_output(self, retval, stdout, stderr):
        """Parse the output of the kill command.

        To be implemented by the plugin.

        :return: True if everything seems ok, False otherwise.
        """
        if retval != 0:
            _LOGGER.error(f'Error in _parse_kill_output: retval={retval}; stdout={stdout}; stderr={stderr}')
            return False

        if stderr.strip():
            _LOGGER.warning(f'in _parse_kill_output there was some text in stderr: {stderr}')

        if stdout.strip():
            _LOGGER.warning(f'in _parse_kill_output there was some text in stdout: {stdout}')

        return True
