###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Data structures used by `Scheduler` instances.

In particular, there is the definition of possible job states (job_states),
the data structure to be filled for job submission (JobTemplate), and
the data structure that is returned when querying for jobs in the scheduler
(JobInfo).
"""

from __future__ import annotations

import abc
import enum
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Literal

from typing_extensions import Self

from aiida.common import AIIDA_LOGGER, CodeRunMode
from aiida.common.extendeddicts import AttributeDict, DefaultFieldsAttributeDict
from aiida.common.timezone import make_aware, timezone_from_name

SCHEDULER_LOGGER = AIIDA_LOGGER.getChild('scheduler')

__all__ = (
    'JobInfo',
    'JobResource',
    'JobState',
    'JobTemplate',
    'MachineInfo',
    'NodeNumberJobResource',
    'ParEnvJobResource',
)


class JobState(enum.Enum):
    """Enumeration of possible scheduler states of a CalcJob.

    There is no FAILED state as every completed job is put in DONE, regardless of success.
    """

    UNDETERMINED = 'undetermined'
    QUEUED = 'queued'
    QUEUED_HELD = 'queued held'
    RUNNING = 'running'
    SUSPENDED = 'suspended'
    DONE = 'done'


class JobResource(DefaultFieldsAttributeDict, metaclass=abc.ABCMeta):
    """Data structure to store job resources.

    Each `Scheduler` implementation must define the `_job_resource_class` attribute to be a subclass of this class.
    It should at least define the `get_tot_num_mpiprocs` method, plus a constructor to accept its set of variables.

    Typical attributes are:

    * ``num_machines``
    * ``num_mpiprocs_per_machine``

    or (e.g. for SGE)

    * ``tot_num_mpiprocs``
    * ``parallel_env``

    The constructor should take care of checking the values.
    The init should raise only ValueError or TypeError on invalid parameters.
    """

    _default_fields = tuple()

    @classmethod
    @abc.abstractmethod
    def validate_resources(cls, **kwargs: Any) -> dict[Any, Any] | None:
        """Validate the resources against the job resource class of this scheduler.

        :param kwargs: dictionary of values to define the job resources
        :raises ValueError: if the resources are invalid or incomplete
        :return: optional dict of parsed resource settings
        """

    @classmethod
    def get_valid_keys(cls) -> list[str]:
        """Return a list of valid keys to be passed to the constructor."""
        return list(cls._default_fields)

    @classmethod
    @abc.abstractmethod
    def accepts_default_mpiprocs_per_machine(cls) -> bool:
        """Return True if this subclass accepts a `default_mpiprocs_per_machine` key, False otherwise."""

    @classmethod
    def accepts_default_memory_per_machine(cls) -> bool:
        """Return True if this subclass accepts a `default_memory_per_machine` key, False otherwise."""
        return True

    @abc.abstractmethod
    def get_tot_num_mpiprocs(self) -> int:
        """Return the total number of cpus of this job resource."""


class NodeNumberJobResource(JobResource):
    """`JobResource` for schedulers that support the specification of a number of nodes and cpus per node."""

    _default_fields = (
        'num_machines',
        'num_mpiprocs_per_machine',
        'num_cores_per_machine',
        'num_cores_per_mpiproc',
    )

    if TYPE_CHECKING:
        num_machines: int
        num_mpiprocs_per_machine: int
        num_cores_per_machine: int
        num_cores_per_mpiproc: int

    @classmethod
    def validate_resources(cls, **kwargs: Any) -> AttributeDict:
        """Validate the resources against the job resource class of this scheduler.

        :param kwargs: dictionary of values to define the job resources
        :return: attribute dictionary with the parsed parameters populated
        :raises ValueError: if the resources are invalid or incomplete
        """
        resources = AttributeDict()

        def is_greater_equal_one(parameter: str) -> None:
            value = getattr(resources, parameter, None)
            if value is not None and value < 1:
                raise ValueError(f'`{parameter}` must be greater than or equal to one.')

        # Validate that all fields are valid integers if they are specified, otherwise initialize them to `None`
        for parameter in list(cls._default_fields) + ['tot_num_mpiprocs']:
            value = kwargs.pop(parameter, None)
            if value is None:
                setattr(resources, parameter, None)
            else:
                try:
                    setattr(resources, parameter, int(value))
                except ValueError:
                    raise ValueError(f'`{parameter}` must be an integer when specified')

        if kwargs:
            raise ValueError(f"these parameters were not recognized: {', '.join(list(kwargs.keys()))}")

        # At least two of the following parameters need to be defined as non-zero
        if [resources.num_machines, resources.num_mpiprocs_per_machine, resources.tot_num_mpiprocs].count(None) > 1:
            raise ValueError(
                'At least two among `num_machines`, `num_mpiprocs_per_machine` or `tot_num_mpiprocs` must be specified.'
            )

        for parameter in ['num_machines', 'num_mpiprocs_per_machine']:
            is_greater_equal_one(parameter)

        # Here we now that at least two of the three required variables are defined and greater equal than one.
        if resources.num_machines is None:
            resources.num_machines = resources.tot_num_mpiprocs // resources.num_mpiprocs_per_machine
        elif resources.num_mpiprocs_per_machine is None:
            resources.num_mpiprocs_per_machine = resources.tot_num_mpiprocs // resources.num_machines
        elif resources.tot_num_mpiprocs is None:
            resources.tot_num_mpiprocs = resources.num_mpiprocs_per_machine * resources.num_machines

        if resources.tot_num_mpiprocs != resources.num_mpiprocs_per_machine * resources.num_machines:
            raise ValueError('`tot_num_mpiprocs` is not equal to `num_mpiprocs_per_machine * num_machines`.')

        is_greater_equal_one('num_mpiprocs_per_machine')
        is_greater_equal_one('num_machines')

        return resources

    def __init__(self, **kwargs: Any):
        """Initialize the job resources from the passed arguments.

        :raises ValueError: if the resources are invalid or incomplete
        """
        resources = self.validate_resources(**kwargs)
        super().__init__(resources)

    @classmethod
    def get_valid_keys(cls) -> list[str]:
        """Return a list of valid keys to be passed to the constructor."""
        return super().get_valid_keys() + ['tot_num_mpiprocs']

    @classmethod
    def accepts_default_mpiprocs_per_machine(cls) -> Literal[True]:
        """Return True if this subclass accepts a `default_mpiprocs_per_machine` key, False otherwise."""
        return True

    def get_tot_num_mpiprocs(self) -> int:
        """Return the total number of cpus of this job resource."""
        return self.num_machines * self.num_mpiprocs_per_machine


class ParEnvJobResource(JobResource):
    """`JobResource` for schedulers that support the specification of a parallel environment and number of MPI procs."""

    _default_fields = (
        'parallel_env',
        'tot_num_mpiprocs',
    )

    if TYPE_CHECKING:
        parallel_env: str
        tot_num_mpiprocs: int

    @classmethod
    def validate_resources(cls, **kwargs: Any) -> AttributeDict:
        """Validate the resources against the job resource class of this scheduler.

        :param kwargs: dictionary of values to define the job resources
        :return: attribute dictionary with the parsed parameters populated
        :raises ValueError: if the resources are invalid or incomplete
        """
        resources = AttributeDict()

        try:
            resources.parallel_env = kwargs.pop('parallel_env')
        except KeyError:
            raise ValueError('`parallel_env` must be specified and must be a string')
        else:
            if not isinstance(resources.parallel_env, str):
                raise ValueError('`parallel_env` must be specified and must be a string')

        try:
            resources.tot_num_mpiprocs = int(kwargs.pop('tot_num_mpiprocs'))
        except (KeyError, TypeError, ValueError):
            raise ValueError('`tot_num_mpiprocs` must be specified and must be an integer')

        if resources.tot_num_mpiprocs < 1:
            raise ValueError('`tot_num_mpiprocs` must be greater than or equal to one.')

        if kwargs:
            raise ValueError(f"these parameters were not recognized: {', '.join(list(kwargs.keys()))}")

        return resources

    def __init__(self, **kwargs: Any):
        """Initialize the job resources from the passed arguments (the valid keys can be
        obtained with the function self.get_valid_keys()).

        :raises ValueError: if the resources are invalid or incomplete
        """
        resources = self.validate_resources(**kwargs)
        super().__init__(resources)

    @classmethod
    def accepts_default_mpiprocs_per_machine(cls) -> Literal[False]:
        """Return True if this subclass accepts a `default_mpiprocs_per_machine` key, False otherwise."""
        return False

    def get_tot_num_mpiprocs(self) -> int:
        """Return the total number of cpus of this job resource."""
        return self.tot_num_mpiprocs


class JobTemplate(DefaultFieldsAttributeDict):
    """A template for submitting jobs to a scheduler.

    This contains all required information to create the job header.

    The required fields are: working_directory, job_name, num_machines, num_mpiprocs_per_machine, argv.

    Fields:

      * ``shebang line``: The first line of the submission script
      * ``submit_as_hold``: if set, the job will be in a 'hold' status right
        after the submission
      * ``rerunnable``: if the job is rerunnable (boolean)
      * ``job_environment``: a dictionary with environment variables to set
        before the execution of the code.
      * ``environment_variables_double_quotes``: if set to True, use double quotes
        instead of single quotes to escape the environment variables specified
        in ``job_environment``.
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
      * ``account``: the name of the scheduler account (sometimes also called
        projectid), on which the job will be submitted.
      * ``qos``: the quality of service of the scheduler account,
        on which the job will be submitted.
      * ``job_resource``: a suitable :py:class:`JobResource`
        subclass with information on how many
        nodes and cpus it should use. It must be an instance of the
        ``aiida.schedulers.Scheduler.job_resource_class`` class.
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
      * ``codes_info``: a list of aiida.scheduler.datastructures.JobTemplateCodeInfo objects.
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
        Values are given by aiida.common.datastructures.CodeRunMode.
    """

    _default_fields = (
        'shebang',
        'submit_as_hold',
        'rerunnable',
        'job_environment',
        'environment_variables_double_quotes',
        'working_directory',
        'email',
        'email_on_started',
        'email_on_terminated',
        'job_name',
        'sched_output_path',
        'sched_error_path',
        'sched_join_files',
        'queue_name',
        'account',
        'qos',
        'job_resource',
        'priority',
        'max_memory_kb',
        'max_wallclock_seconds',
        'custom_scheduler_commands',
        'prepend_text',
        'append_text',
        'import_sys_environment',
        'codes_run_mode',
        'codes_info',
    )

    if TYPE_CHECKING:
        shebang: str | None
        submit_as_hold: bool
        rerunnable: bool
        job_environment: dict[str, str] | None
        environment_variables_double_quotes: bool | None
        working_directory: str
        email: str
        email_on_started: bool
        email_on_terminated: bool
        job_name: str
        sched_output_path: str | None
        sched_error_path: str | None
        sched_join_files: bool
        queue_name: str
        account: str
        qos: str
        job_resource: JobResource
        priority: str
        max_memory_kb: int | None
        max_wallclock_seconds: int
        custom_scheduler_commands: str
        prepend_text: str
        append_text: str
        import_sys_environment: bool | None
        codes_run_mode: CodeRunMode
        codes_info: list[JobTemplateCodeInfo]


@dataclass
class JobTemplateCodeInfo:
    """Data structure to communicate to a `Scheduler` how a code should be run in submit script.

    `Scheduler.get_submit_script` will pass a list of these objects to `Scheduler._get_run_line` which
    should build up the code execution line based on the parameters specified in this dataclass.

    :param preprend_cmdline_params: list of unescaped command line arguments that are to be prepended to the executable.
    :param cmdline_params: list of unescaped command line parameters.
    :param use_double_quotes: list of two booleans. If true, use double quotes to escape command line arguments. The
        first value applies to `prepend_cmdline_params` and the second to `cmdline_params`.
    :param wrap_cmdline_params: Boolean, by default ``False``. If set to ``True``, all the command line arguments,
        which includes the ``cmdline_params`` but also all file descriptor redirections (stdin, stderr and stdoout),
        should be wrapped in double quotes, turning it into a single command line argument. This is necessary to enable
        support for certain containerization technologies such as Docker.
    :param stdin_name: filename of the the stdin file descriptor.
    :param stdout_name: filename of the the `stdout` file descriptor.
    :param stderr_name: filename of the the `stderr` file descriptor.
    :param join_files: boolean, if true, `stderr` should be redirected to `stdout`.
    """

    prepend_cmdline_params: list[str] = field(default_factory=list)
    cmdline_params: list[str] = field(default_factory=list)
    use_double_quotes: list[bool] = field(default_factory=lambda: [False, False])
    wrap_cmdline_params: bool = False
    stdin_name: None | str = None
    stdout_name: None | str = None
    stderr_name: None | str = None
    join_files: bool = False


class MachineInfo(DefaultFieldsAttributeDict):
    """Similarly to what is defined in the DRMAA v.2 as SlotInfo; this identifies
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
    """Contains properties for a job in the queue.
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
         ``aiida.schedulers.datastructures.JobState``)
       * ``job_substate``: a string with the implementation-specific sub-state
       * ``allocated_machines``: a list of machines used for the current job.
         This is a list of :py:class:`aiida.schedulers.datastructures.MachineInfo` objects.
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
       * ``account``: The account/projectid in which the job is queued or
         running in.
       * ``qos``: The quality of service in which the job is queued or
         running in.
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
        'account',
        'qos',
        'wallclock_time_seconds',
        'requested_wallclock_time_seconds',
        'cpu_time',
        'submission_time',
        'dispatch_time',
        'finish_time',
    )

    if TYPE_CHECKING:
        job_id: str
        title: str
        exit_status: int
        terminating_signal: int
        annotation: str
        job_state: JobState
        job_substate: str
        allocated_machines: list[MachineInfo]
        job_owner: str
        num_mpiprocs: int
        num_cpus: int
        num_machines: int
        queue_name: str
        account: str
        qos: str
        wallclock_time_seconds: int
        requested_wallclock_time_seconds: int
        cpu_time: int
        submission_time: datetime
        dispatch_time: datetime
        finish_time: datetime

    # If some fields require special serializers, specify them here.
    # You then need to define also the respective _serialize_FIELDTYPE and
    # _deserialize_FIELDTYPE methods
    _special_serializers = {
        'submission_time': 'date',
        'dispatch_time': 'date',
        'finish_time': 'date',
        'job_state': 'job_state',
    }

    @staticmethod
    def _serialize_job_state(job_state: JobState) -> str:
        """Return the serialized value of the JobState instance."""
        if not isinstance(job_state, JobState):
            raise TypeError(f'invalid type for value {job_state}, should be an instance of `JobState`')

        return job_state.value

    @staticmethod
    def _deserialize_job_state(job_state: str) -> JobState:
        """Return an instance of JobState from the job_state string."""
        return JobState(job_state)

    @staticmethod
    def _serialize_date(value: datetime | None) -> dict[str, str | None] | None:
        """Serialise a data value
        :param value: The value to serialise
        :return: The serialised value
        """
        if value is None:
            return value

        if not isinstance(value, datetime):
            raise TypeError('Invalid type for the date, should be a datetime')

        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            SCHEDULER_LOGGER.debug('Datetime to serialize in JobInfo is naive, this should be fixed!')
            return {'date': value.strftime('%Y-%m-%dT%H:%M:%S.%f'), 'timezone': None}

        return {'date': value.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f'), 'timezone': 'UTC'}

    @staticmethod
    def _deserialize_date(value: dict[str, str] | None) -> datetime | None:
        """Deserialise a date
        :param value: The date vlue
        :return: The deserialised date
        """
        if value is None:
            return value

        if value['timezone'] is None:
            # naive date
            return datetime.strptime(value['date'], '%Y-%m-%dT%H:%M:%S.%f')  # type: ignore[unreachable]
        if value['timezone'] == 'UTC':
            return make_aware(datetime.strptime(value['date'], '%Y-%m-%dT%H:%M:%S.%f'), timezone.utc)

        # Try your best to guess the timezone from the name.
        return make_aware(
            datetime.strptime(value['date'], '%Y-%m-%dT%H:%M:%S.%f'), timezone_from_name(value['timezone'])
        )

    @classmethod
    def serialize_field(cls, value: Any, field_type: str | None) -> Any:
        """Serialise a particular field value

        :param value: The value to serialise
        :param field_type: The field type
        :return: The serialised value
        """
        if field_type is None:
            return value

        serializer_method = getattr(cls, f'_serialize_{field_type}')

        return serializer_method(value)

    @classmethod
    def deserialize_field(cls, value: Any, field_type: str | None) -> Any:
        """Deserialise the value of a particular field with a type
        :param value: The value
        :param field_type: The field type
        :return: The deserialised value
        """
        if field_type is None:
            return value

        deserializer_method = getattr(cls, f'_deserialize_{field_type}')

        return deserializer_method(value)

    def serialize(self) -> str:
        """Serialize the current data (as obtained by ``self.get_dict()``) into a JSON string.

        :return: A string with serialised representation of the current data.
        """
        return json.dumps(self.get_dict())

    def get_dict(self) -> dict[str, Any]:
        """Serialise the current data into a dictionary that is JSON-serializable.

        :return: A dictionary
        """
        return {k: self.serialize_field(v, self._special_serializers.get(k, None)) for k, v in self.items()}

    @classmethod
    def load_from_dict(cls, data: dict[str, Any]) -> Self:
        """Create a new instance loading the values from serialised data in dictionary form

        :param data: The dictionary with the data to load from
        """
        instance = cls()
        for key, value in data.items():
            instance[key] = cls.deserialize_field(value, cls._special_serializers.get(key, None))
        return instance

    @classmethod
    def load_from_serialized(cls, data: str) -> Self:
        """Create a new instance loading the values from JSON-serialised data as a string

        :param data: The string with the JSON-serialised data to load from
        """
        return cls.load_from_dict(json.loads(data))
