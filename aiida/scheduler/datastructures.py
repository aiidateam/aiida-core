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
This module defines the main data structures used by the Scheduler.

In particular, there is the definition of possible job states (job_states),
the data structure to be filled for job submission (JobTemplate), and
the data structure that is returned when querying for jobs in the scheduler
(JobInfo).
"""
from __future__ import division
from aiida.common.extendeddicts import (
    DefaultFieldsAttributeDict, Enumerate)

from aiida.common import aiidalogger


scheduler_logger = aiidalogger.getChild('scheduler')


class JobState(Enumerate):
    pass

# This is the list of possible job states
# Note on names: Jobs are the entities on a
# scheduler; Calcs are the calculations in
#   the AiiDA database (whose list of possible
#   statuses is defined in aida.common.datastructures
#   with the calc_states Enumerate).
# NOTE: for the moment, I don't define FAILED
# (I put everything in DONE)
job_states = JobState((
    'UNDETERMINED',
    'QUEUED',
    'QUEUED_HELD',
    'RUNNING',
    'SUSPENDED',
    'DONE',
))


class JobResource(DefaultFieldsAttributeDict):
    """
    A class to store the job resources. It must be inherited and redefined by the specific
    plugin, that should contain a ``_job_resource_class`` attribute pointing to the correct
    JobResource subclass.

    It should at least define the get_tot_num_mpiprocs() method, plus an __init__ to accept
    its set of variables.

    Typical attributes are:

    * ``num_machines``
    * ``num_mpiprocs_per_machine``

    or (e.g. for SGE)

    * ``tot_num_mpiprocs``
    * ``parallel_env``

    The __init__ should take care of checking the values.
    The init should raise only ValueError or TypeError on invalid parameters.
    """
    _default_fields = tuple()

    @classmethod
    def accepts_default_mpiprocs_per_machine(cls):
        """
        Return True if this JobResource accepts a 'default_mpiprocs_per_machine'
        key, False otherwise.

        Should be implemented in each subclass.
        """
        raise NotImplementedError

    @classmethod
    def get_valid_keys(cls):
        """
        Return a list of valid keys to be passed to the __init__
        """
        return list(cls._default_fields)

    def get_tot_num_mpiprocs(self):
        """
        Return the total number of cpus of this job resource.
        """
        raise NotImplementedError


class NodeNumberJobResource(JobResource):
    """
    An implementation of JobResource for schedulers that support
    the specification of a number of nodes and a number of cpus per node
    """
    _default_fields = (
        'num_machines',
        'num_mpiprocs_per_machine',
        'num_cores_per_machine',
        'num_cores_per_mpiproc',
    )

    @classmethod
    def get_valid_keys(cls):
        """
        Return a list of valid keys to be passed to the __init__
        """
        return super(NodeNumberJobResource, cls).get_valid_keys() + [
            "tot_num_mpiprocs", "default_mpiprocs_per_machine"]

    @classmethod
    def accepts_default_mpiprocs_per_machine(cls):
        """
        Return True if this JobResource accepts a 'default_mpiprocs_per_machine'
        key, False otherwise.
        """
        return True

    def __init__(self, **kwargs):
        """
        Initialize the job resources from the passed arguments (the valid keys can be
        obtained with the function self.get_valid_keys()).

        Should raise only ValueError or TypeError on invalid parameters.
        """
        try:
            num_machines = int(kwargs.pop('num_machines'))
        except KeyError:
            num_machines = None
        except ValueError:
            raise ValueError("num_machines must an integer")

        try:
            default_mpiprocs_per_machine = kwargs.pop('default_mpiprocs_per_machine')
            if default_mpiprocs_per_machine is not None:
                default_mpiprocs_per_machine = int(default_mpiprocs_per_machine)
        except KeyError:
            default_mpiprocs_per_machine = None
        except ValueError:
            raise ValueError("default_mpiprocs_per_machine must an integer")

        try:
            num_mpiprocs_per_machine = int(kwargs.pop('num_mpiprocs_per_machine'))
        except KeyError:
            num_mpiprocs_per_machine = None
        except ValueError:
            raise ValueError("num_mpiprocs_per_machine must an integer")

        try:
            tot_num_mpiprocs = int(kwargs.pop('tot_num_mpiprocs'))
        except KeyError:
            tot_num_mpiprocs = None
        except ValueError:
            raise ValueError("tot_num_mpiprocs must an integer")

        try:
            self.num_cores_per_machine = int(kwargs.pop('num_cores_per_machine'))
        except KeyError:
            self.num_cores_per_machine = None
        except ValueError:
            raise ValueError("num_cores_per_machine must an integer")

        try:
            self.num_cores_per_mpiproc = int(kwargs.pop('num_cores_per_mpiproc'))
        except KeyError:
            self.num_cores_per_mpiproc = None
        except ValueError:
            raise ValueError("num_cores_per_mpiproc must an integer")

        if kwargs:
            raise TypeError("The following parameters were not recognized for "
                            "the JobResource: {}".format(kwargs.keys()))

        if num_machines is None:
            # Use default value, if not provided
            if num_mpiprocs_per_machine is None:
                num_mpiprocs_per_machine = default_mpiprocs_per_machine

            if num_mpiprocs_per_machine is None or tot_num_mpiprocs is None:
                raise TypeError("At least two among num_machines, "
                                "num_mpiprocs_per_machine or tot_num_mpiprocs must be specified")
            else:
                # To avoid divisions by zero
                if num_mpiprocs_per_machine <= 0:
                    raise ValueError("num_mpiprocs_per_machine must be >= 1")
                num_machines = tot_num_mpiprocs // num_mpiprocs_per_machine
        else:
            if tot_num_mpiprocs is None:
                # Only set the default value if tot_num_mpiprocs is not provided.
                # Otherwise, it means that the user provided both
                # num_machines and tot_num_mpiprocs, and we have to ignore
                # the default value of tot_num_mpiprocs
                if num_mpiprocs_per_machine is None:
                    num_mpiprocs_per_machine = default_mpiprocs_per_machine

            if num_mpiprocs_per_machine is None:
                if tot_num_mpiprocs is None:
                    raise TypeError("At least two among num_machines, "
                                    "num_mpiprocs_per_machine or tot_num_mpiprocs must be specified")
                else:
                    # To avoid divisions by zero
                    if num_machines <= 0:
                        raise ValueError("num_machines must be >= 1")
                    num_mpiprocs_per_machine = tot_num_mpiprocs // num_machines

        self.num_machines = num_machines
        self.num_mpiprocs_per_machine = num_mpiprocs_per_machine

        if tot_num_mpiprocs is not None:
            if tot_num_mpiprocs != self.num_mpiprocs_per_machine * self.num_machines:
                raise ValueError("tot_num_mpiprocs must be equal to "
                                 "num_mpiprocs_per_machine * num_machines, and in particular it "
                                 "should be a multiple of num_mpiprocs_per_machine and/or "
                                 "num_machines")

        if self.num_mpiprocs_per_machine <= 0:
            raise ValueError("num_mpiprocs_per_machine must be >= 1")
        if self.num_machines <= 0:
            raise ValueError("num_machine must be >= 1")


    def get_tot_num_mpiprocs(self):
        """
        Return the total number of cpus of this job resource.
        """
        return self.num_machines * self.num_mpiprocs_per_machine


class ParEnvJobResource(JobResource):
    """
    An implementation of JobResource for schedulers that support
    the specification of a parallel environment (a string) + the total number of nodes
    """
    _default_fields = (
        'parallel_env',
        'tot_num_mpiprocs',
        'default_mpiprocs_per_machine',
    )

    def __init__(self, **kwargs):
        """
        Initialize the job resources from the passed arguments (the valid keys can be
        obtained with the function self.get_valid_keys()).

        :raise ValueError: on invalid parameters.
        :raise TypeError: on invalid parameters.
        :raise ConfigurationError: if default_mpiprocs_per_machine was set for this
            computer, since ParEnvJobResource cannot accept this parameter.
        """
        from aiida.common.exceptions import ConfigurationError

        try:
            self.parallel_env = str(kwargs.pop('parallel_env'))
        except (KeyError, TypeError, ValueError):
            raise TypeError("'parallel_env' must be specified and must be a string")

        try:
            self.tot_num_mpiprocs = int(kwargs.pop('tot_num_mpiprocs'))
        except (KeyError, ValueError):
            raise TypeError("tot_num_mpiprocs must be specified and must be an integer")

        default_mpiprocs_per_machine = kwargs.pop('default_mpiprocs_per_machine', None)
        if default_mpiprocs_per_machine is not None:
            raise ConfigurationError("default_mpiprocs_per_machine cannot be set "
                                     "for schedulers that use ParEnvJobResource")

        if self.tot_num_mpiprocs <= 0:
            raise ValueError("tot_num_mpiprocs must be >= 1")

    def get_tot_num_mpiprocs(self):
        """
        Return the total number of cpus of this job resource.
        """
        return self.tot_num_mpiprocs

    @classmethod
    def accepts_default_mpiprocs_per_machine(cls):
        """
        Return True if this JobResource accepts a 'default_mpiprocs_per_machine'
        key, False otherwise.
        """
        return False


class JobTemplate(DefaultFieldsAttributeDict):
    """
    A template for submitting jobs. This contains all required information
    to create the job header.

    The required fields are: working_directory, job_name, num_machines,
      num_mpiprocs_per_machine, argv.

    Fields:

      * ``submit_as_hold``: if set, the job will be in a 'hold' status right
        after the submission
      * ``rerunnable``: if the job is rerunnable (boolean)
      * ``job_environment``: a dictionary with environment variables to set
        before the execution of the code.
      * ``working_directory``: the working directory for this job. During
        submission, the transport will first do a 'chdir' to this directory,
        and then possibly set a scheduler parameter, if this is supported
        by the scheduler.
      * ``email``: an email address for sending emails on job events.
      * ``email_on_started``: if True, ask the scheduler to send an email when the
        job starts.
      * ``email_on_terminated``: if True, ask the scheduler to send an email when
        the job ends. This should also send emails on job failure, when
        possible.
      * ``job_name``: the name of this job. The actual name of the job can be
        different from the one specified here, e.g. if there are unsupported
        characters, or the name is too long.
      * ``sched_output_path``: a (relative) file name for the stdout of this job
      * ``sched_error_path``: a (relative) file name for the stdout of this job
      * ``sched_join_files``: if True, write both stdout and stderr on the same
        file (the one specified for stdout)
      * ``queue_name``: the name of the scheduler queue (sometimes also called
        partition), on which the job will be submitted.
      * ``job_resource``: a suitable :py:class:`JobResource`
        subclass with information on how many
        nodes and cpus it should use. It must be an instance of the
        ``aiida.scheduler.Scheduler._job_resource_class`` class.
        Use the Scheduler.create_job_resource method to create it.
      * ``num_machines``: how many machines (or nodes) should be used
      * ``num_mpiprocs_per_machine``: how many MPI procs should be used on each
        machine (or node).
      * ``priority``: a priority for this job. Should be in the format accepted
        by the specific scheduler.
      * ``max_memory_kb``: The maximum amount of memory the job is allowed
        to allocate ON EACH NODE, in kilobytes
      * ``max_wallclock_seconds``: The maximum wall clock time that all processes
        of a job are allowed to exist, in seconds
      * ``custom_scheduler_commands``: a string that will be inserted right
        after the last scheduler command, and before any other non-scheduler
        command; useful if some specific flag needs to be added and is not
        supported by the plugin
      * ``prepend_text``: a (possibly multi-line) string to be inserted
        in the scheduler script before the main execution line
      * ``append_text``: a (possibly multi-line) string to be inserted
        in the scheduler script after the main execution line
      * ``import_sys_environment``: import the system environment variables
      * ``codes_info``: a list of aiida.common.datastructures.CalcInfo objects.
        Each contains the information necessary to run a single code. At the
        moment, it can contain:

        * ``cmdline_parameters``: a list of strings with the command line arguments
          of the program to run. This is the main program to be executed.
          NOTE: The first one is the executable name.
          For MPI runs, this will probably be "mpirun" or a similar program;
          this has to be chosen at a upper level.
        * ``stdin_name``: the (relative) file name to be used as stdin for the
          program specified with argv.
        * ``stdout_name``: the (relative) file name to be used as stdout for the
          program specified with argv.
        * ``stderr_name``: the (relative) file name to be used as stderr for the
          program specified with argv.
        * ``join_files``: if True, stderr is redirected on the same file
          specified for stdout.

      * ``codes_run_mode``: sets the run_mode with which the (multiple) codes
        have to be executed. For example, parallel execution::

          mpirun -np 8 a.x &
          mpirun -np 8 b.x &
          wait

        The serial execution would be without the &'s.
        Values are given by aiida.common.datastructures.code_run_modes.
    """
    # #TODO: validation key? also call the validate function in the proper
    #        place then.

    _default_fields = (
        'submit_as_hold',
        'rerunnable',
        'job_environment',
        'working_directory',
        'email',
        'email_on_started',
        'email_on_terminated',
        'job_name',
        'sched_output_path',
        'sched_error_path',
        'sched_join_files',
        'queue_name',
        'job_resource',
        #        'num_machines',
        #        'num_mpiprocs_per_machine',
        'priority',
        'max_memory_kb',
        'max_wallclock_seconds',
        'custom_scheduler_commands',
        'prepend_text',
        'append_text',
        'import_sys_environment',
#        'stderr_name', # this 5 5keys have been moved to codes_info
#        'join_files',
#        'argv',
#        'stdin_name',
#        'stdout_name',
        'codes_run_mode',
        'codes_info',
    )


class MachineInfo(DefaultFieldsAttributeDict):
    """
    Similarly to what is defined in the DRMAA v.2 as SlotInfo; this identifies
    each machine (also called 'node' on some schedulers)
    on which a job is running, and how many CPUs are being used. (Some of them
    could be undefined)

    * ``name``: name of the machine
    * ``num_cpus``: number of cores used by the job on this machine
    * ``num_mpiprocs``: number of MPI processes used by the job on this machine
    """
    _default_fields = (
        'name',
        'num_mpiprocs',
        'num_cpus',
    )


class JobInfo(DefaultFieldsAttributeDict):
    """
    Contains properties for a job in the queue.
    Most of the fields are taken from DRMAA v.2.

    Note that default fields may be undefined. This
    is an expected behavior and the application must cope with this
    case. An example for instance is the exit_status for jobs that have
    not finished yet; or features not supported by the given scheduler.

    Fields:

       * ``job_id``: the job ID on the scheduler
       * ``title``: the job title, as known by the scheduler
       * ``exit_status``: the exit status of the job as reported by the operating
         system on the execution host
       * ``terminating_signal``: the UNIX signal that was responsible for the end
         of the job.
       * ``annotation``: human-readable description of the reason for the job
         being in the current state or substate.
       * ``job_state``: the job state (one of those defined in
         ``aiida.scheduler.datastructures.job_states``)
       * ``job_substate``: a string with the implementation-specific sub-state
       * ``allocated_machines``: a list of machines used for the current job.
         This is a list of :py:class:`MachineInfo` objects.
       * ``job_owner``: the job owner as reported by the scheduler
       * ``num_mpiprocs``: the *total* number of requested MPI procs
       * ``num_cpus``: the *total* number of requested CPUs (cores) [may be undefined]
       * ``num_machines``: the number of machines (i.e., nodes), required by the
         job. If ``allocated_machines`` is not None, this number must be equal to
         ``len(allocated_machines)``. Otherwise, for schedulers not supporting
         the retrieval of the full list of allocated machines, this
         attribute can be used to know at least the number of machines.
       * ``queue_name``: The name of the queue in which the job is queued or
         running.
       * ``wallclock_time_seconds``: the accumulated wallclock time, in seconds
       * ``requested_wallclock_time_seconds``: the requested wallclock time,
         in seconds
       * ``cpu_time``: the accumulated cpu time, in seconds
       * ``submission_time``: the absolute time at which the job was submitted,
         of type datetime.datetime
       * ``dispatch_time``: the absolute time at which the job first entered the
         'started' state, of type datetime.datetime
       * ``finish_time``: the absolute time at which the job first entered the
         'finished' state, of type datetime.datetime
    """
    _default_fields = (
        'job_id',
        'title',
        'exit_status',
        'terminating_signal',
        'annotation',
        'job_state',
        'job_substate',
        'allocated_machines',
        'job_owner',
        'num_mpiprocs',
        'num_cpus',
        'num_machines',
        'queue_name',
        'wallclock_time_seconds',
        'requested_wallclock_time_seconds',
        'cpu_time',
        'submission_time',
        'dispatch_time',
        'finish_time'
    )

    # If some fields require special serializers, specify them here.
    # You then need to define also the respective _serialize_FIELDTYPE and
    # _deserialize_FIELDTYPE methods
    _special_serializers = {
        'submission_time': 'date',
        'dispatch_time': 'date',
        'finish_time': 'date',
    }

    def _serialize_date(self, v):
        import datetime
        import pytz

        if v is None:
            return v

        if not isinstance(v, datetime.datetime):
            raise TypeError("Invalid type for the date, should be a datetime")

        # is_naive check from django.utils.timezone
        if v.tzinfo is None or v.tzinfo.utcoffset(v) is None:
            # TODO: FIX TIMEZONE
            scheduler_logger.debug("Datetime to serialize in JobInfo is naive, "
                                   "this should be fixed!")
            #v = v.replace(tzinfo = pytz.utc)
            return {'date': v.strftime(
                '%Y-%m-%dT%H:%M:%S.%f'), 'timezone': None}
        else:
            return {'date': v.astimezone(pytz.utc).strftime(
                '%Y-%m-%dT%H:%M:%S.%f'), 'timezone': 'UTC'}

    def _deserialize_date(self, v):
        import datetime
        import pytz

        if v is None:
            return v

        if v['timezone'] is None:
            # naive date
            return datetime.datetime.strptime(v['date'],
                                              '%Y-%m-%dT%H:%M:%S.%f')
        elif v['timezone'] == 'UTC':
            return datetime.datetime.strptime(v['date'],
                                              '%Y-%m-%dT%H:%M:%S.%f').replace(
                tzinfo=pytz.utc)
        else:
            # Try your best
            return datetime.datetime.strptime(v['date'],
                                              '%Y-%m-%dT%H:%M:%S.%f').replace(
                tzinfo=pytz.timezone(v['timezone']))


    def serialize_field(self, value, field_type):
        if field_type is None:
            return value

        serializer_method = getattr(self, "_serialize_{}".format(field_type))

        return serializer_method(value)

    def deserialize_field(self, value, field_type):
        if field_type is None:
            return value

        deserializer_method = getattr(self, "_deserialize_{}".format(field_type))

        return deserializer_method(value)

    def serialize(self):
        import json

        ser_data = {k: self.serialize_field(
            v, self._special_serializers.get(k, None))
                    for k, v in self.iteritems()}

        return json.dumps(ser_data)


    def load_from_serialized(self, data):
        import json

        deser_data = json.loads(data)

        for k, v in deser_data.iteritems():
            self[k] = self.deserialize_field(
                v, self._special_serializers.get(k, None))



