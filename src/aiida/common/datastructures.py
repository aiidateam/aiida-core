###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module to define commonly used data structures."""

from __future__ import annotations

import abc
import enum
import json
import typing as t
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, IntEnum

from typing_extensions import Self

from aiida.common.extendeddicts import AttributeDict, DefaultFieldsAttributeDict
from aiida.common.log import AIIDA_LOGGER
from aiida.common.timezone import make_aware, timezone_from_name

__all__ = (
    'CalcInfo',
    'CalcJobState',
    'CodeInfo',
    'CodeRunMode',
    'JobInfo',
    'JobResource',
    'JobState',
    'JobTemplate',
    'MachineInfo',
    'NodeNumberJobResource',
    'ParEnvJobResource',
    'StashMode',
    'UnstashTargetMode',
)


class StashMode(Enum):
    """Mode to use when stashing files from the working directory of a completed calculation job for safekeeping."""

    COPY = 'copy'
    COMPRESS_TAR = 'tar'
    COMPRESS_TARBZ2 = 'tar.bz2'
    COMPRESS_TARGZ = 'tar.gz'
    COMPRESS_TARXZ = 'tar.xz'
    SUBMIT_CUSTOM_CODE = 'submit_custom_code'


class UnstashTargetMode(Enum):
    """Mode to use when unstashing files."""

    OriginalPlace = 'OriginalPlace'
    NewRemoteData = 'NewRemoteData'


class CalcJobState(Enum):
    """The sub state of a CalcJobNode while its Process is in an active state (i.e. Running or Waiting)."""

    UPLOADING = 'uploading'
    SUBMITTING = 'submitting'
    WITHSCHEDULER = 'withscheduler'
    STASHING = 'stashing'
    UNSTASHING = 'unstashing'
    RETRIEVING = 'retrieving'
    PARSING = 'parsing'


class FileCopyOperation(IntEnum):
    """Enum to represent the copy operations that are used when creating the working directory of a ``CalcJob``.

    There are three different sources of files that are copied to the working directory on the remote computer where a
    calculation job is executed:

        * Local: files written to the temporary sandbox folder by the engine based on the ``local_copy_list`` defined
          by the plugin in the ``prepare_for_submission`` method.
        * Remote: files written directly to the remote working directory by the engine base on the ``remote_copy_list``
          defined by the plugin in the ``prepare_for_submission`` method.
        * Sandbox: files written to a temporary sandbox folder on the local file system written by the ``CalcJob``
          plugin, first in the ``prepare_for_submission`` method, followed by the ``presubmit`` of the base class.

    Historically, these operations were performed in the order of sandbox, local and remote. For certain use cases,
    however, this was deemed non-ideal, for example because files from the remote would override files written by the
    plugin itself in the sandbox. The ``CalcInfo.file_copy_operation_order`` attribute can be used to specify a list
    of this enum to indicate the desired order for file copy operations.
    """

    LOCAL = 0
    REMOTE = 1
    SANDBOX = 2


class CalcInfo(DefaultFieldsAttributeDict):
    """This object will store the data returned by the calculation plugin and to be
    passed to the ExecManager.

    In the following descriptions all paths have to be considered relative

    * retrieve_list: a list of strings or tuples that indicate files that are to be retrieved from the remote after the
        calculation has finished and stored in the ``retrieved_folder`` output node of type ``FolderData``. If the entry
        in the list is just a string, it is assumed to be the filepath on the remote and it will be copied to the base
        directory of the retrieved folder, where the name corresponds to the basename of the remote relative path. This
        means that any remote folder hierarchy is ignored entirely.

        Remote folder hierarchy can be (partially) maintained by using a tuple instead, with the following format

            (source, target, depth)

        The ``source`` and ``target`` elements are relative filepaths in the remote and retrieved folder. The contents
        of ``source`` (whether it is a file or folder) are copied in its entirety to the ``target`` subdirectory in the
        retrieved folder. If no subdirectory should be created, ``'.'`` should be specified for ``target``.

        The ``source`` filepaths support glob patterns ``*`` in case the exact name of the files that are to be
        retrieved are not know a priori.

        The ``depth`` element can be used to control what level of nesting of the source folder hierarchy should be
        maintained. If ``depth`` equals ``0`` or ``1`` (they are equivalent), only the basename of the ``source``
        filepath is kept. For each additional level, another subdirectory of the remote hierarchy is kept. For example:

            ('path/sub/file.txt', '.', 2)

        will retrieve the ``file.txt`` and store it under the path:

            sub/file.txt

    * retrieve_temporary_list: a list of strings or tuples that indicate files that will be retrieved
        and stored temporarily in a FolderData, that will be available only during the parsing call.
        The format of the list is the same as that of 'retrieve_list'

    * local_copy_list: a list of tuples with format ('node_uuid', 'filename', relativedestpath')
    * remote_copy_list: a list of tuples with format ('remotemachinename', 'remoteabspath', 'relativedestpath')
    * remote_symlink_list: a list of tuples with format ('remotemachinename', 'remoteabspath', 'relativedestpath')
    * provenance_exclude_list: a sequence of relative paths of files in the sandbox folder of a `CalcJob` instance that
        should not be stored permanantly in the repository folder of the corresponding `CalcJobNode` that will be
        created, but should only be copied to the remote working directory on the target computer. This is useful for
        input files that should be copied to the working directory but should not be copied as well to the repository
        either, for example, because they contain proprietary information or because they are big and their content is
        already indirectly present in the repository through one of the data nodes passed as input to the calculation.
    * codes_info: a list of dictionaries used to pass the info of the execution of a code
    * codes_run_mode: the mode of execution in which the codes will be run (`CodeRunMode.SERIAL` by default,
        but can also be `CodeRunMode.PARALLEL`)
    * skip_submit: a flag that, when set to True, orders the engine to skip the submit/update steps (so no code will
        run, it will only upload the files and then retrieve/parse).
    * file_copy_operation_order: Order in which input files are copied to the working directory. Should be a list of
      :class:`aiida.common.datastructures.FileCopyOperation` instances.
    """

    _default_fields = (
        'job_environment',
        'email',
        'email_on_started',
        'email_on_terminated',
        'uuid',
        'prepend_text',
        'append_text',
        'num_machines',
        'num_mpiprocs_per_machine',
        'priority',
        'max_wallclock_seconds',
        'max_memory_kb',
        'rerunnable',
        'retrieve_list',
        'retrieve_temporary_list',
        'local_copy_list',
        'remote_copy_list',
        'remote_symlink_list',
        'provenance_exclude_list',
        'codes_info',
        'codes_run_mode',
        'skip_submit',
        'file_copy_operation_order',
    )

    if t.TYPE_CHECKING:
        job_environment: dict[str, str] | None
        email: str | None
        email_on_started: bool
        email_on_terminated: bool
        uuid: str | None
        prepend_text: str | None
        append_text: str | None
        num_machines: int | None
        num_mpiprocs_per_machine: int | None
        priority: int | None
        max_wallclock_seconds: int | None
        max_memory_kb: int | None
        rerunnable: bool
        retrieve_list: list[str | tuple[str, str, int]] | None
        retrieve_temporary_list: list[str | tuple[str, str, int]] | None
        local_copy_list: list[tuple[str, str, str]] | None
        remote_copy_list: list[tuple[str, str, str]] | None
        remote_symlink_list: list[tuple[str, str, str]] | None
        provenance_exclude_list: list[str] | None
        codes_info: list[CodeInfo] | None
        codes_run_mode: CodeRunMode | None
        skip_submit: bool | None
        file_copy_operation_order: list[FileCopyOperation] | None


class CodeInfo(DefaultFieldsAttributeDict):
    """This attribute-dictionary contains the information needed to execute a code.
    Possible attributes are:

    * ``cmdline_params``: a list of strings, containing parameters to be written on
      the command line right after the call to the code, as for example::

        code.x cmdline_params[0] cmdline_params[1] ... < stdin > stdout

    * ``stdin_name``: (optional) the name of the standard input file. Note, it is
      only possible to use the stdin with the syntax::

        code.x < stdin_name

      If no stdin_name is specified, the string "< stdin_name" will not be
      passed to the code.
      Note: it is not possible to substitute/remove the '<' if stdin_name is specified;
      if that is needed, avoid stdin_name and use instead the cmdline_params to
      specify a suitable syntax.
    * ``stdout_name``: (optional) the name of the standard output file. Note, it is
      only possible to pass output to stdout_name with the syntax::

        code.x ... > stdout_name

      If no stdout_name is specified, the string "> stdout_name" will not be
      passed to the code.
      Note: it is not possible to substitute/remove the '>' if stdout_name is specified;
      if that is needed, avoid stdout_name and use instead the cmdline_params to
      specify a suitable syntax.
    * ``stderr_name``: (optional) a string, the name of the error file of the code.
    * ``join_files``: (optional) if True, redirects the error to the output file.
      If join_files=True, the code will be called as::

        code.x ... > stdout_name 2>&1

      otherwise, if join_files=False and stderr is passed::

        code.x ... > stdout_name 2> stderr_name

    * ``withmpi``: if True, executes the code with mpirun (or another MPI installed
      on the remote computer)
    * ``code_uuid``: the uuid of the code associated to the CodeInfo
    """

    _default_fields = (
        'cmdline_params',  # as a list of strings
        'stdin_name',
        'stdout_name',
        'stderr_name',
        'join_files',
        'withmpi',
        'code_uuid',
    )

    if t.TYPE_CHECKING:
        cmdline_params: list[str] | None
        stdin_name: str | None
        stdout_name: str | None
        stderr_name: str | None
        join_files: bool | None
        withmpi: bool | None
        code_uuid: str | None


class CodeRunMode(IntEnum):
    """Enum to indicate the way the codes of a calculation should be run.

    For PARALLEL, the codes for a given calculation will be run in parallel by running them in the background::

        code1.x &
        code2.x &

    For the SERIAL option, codes will be executed sequentially by running for example the following::

        code1.x
        code2.x
    """

    SERIAL = 0
    PARALLEL = 1


SCHEDULER_LOGGER = AIIDA_LOGGER.getChild('scheduler')


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
    def validate_resources(cls, **kwargs: t.Any) -> dict[t.Any, t.Any] | None:
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

    if t.TYPE_CHECKING:
        num_machines: int
        num_mpiprocs_per_machine: int
        num_cores_per_machine: int
        num_cores_per_mpiproc: int

    @classmethod
    def validate_resources(cls, **kwargs: t.Any) -> AttributeDict:
        """Validate the resources against the job resource class of this scheduler.

        :param kwargs: dictionary of values to define the job resources
        :return: attribute dictionary with the parsed parameters populated
        :raises ValueError: if the resources are invalid or incomplete
        """
        resources = AttributeDict()

        def is_greater_equal_one(parameter: str) -> None:
            value = getattr(resources, parameter, None)
            if value is not None and value < 1:
                msg = f'`{parameter}` must be greater than or equal to one.'
                raise ValueError(msg)

        # Validate that all fields are valid integers if they are specified, otherwise initialize them to `None`
        for parameter in list(cls._default_fields) + ['tot_num_mpiprocs']:
            value = kwargs.pop(parameter, None)
            if value is None:
                setattr(resources, parameter, None)
            else:
                try:
                    setattr(resources, parameter, int(value))
                except ValueError:
                    msg = f'`{parameter}` must be an integer when specified'
                    raise ValueError(msg)

        if kwargs:
            msg = f'these parameters were not recognized: {", ".join(list(kwargs.keys()))}'
            raise ValueError(msg)

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

    def __init__(self, **kwargs: t.Any):
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
    def accepts_default_mpiprocs_per_machine(cls) -> t.Literal[True]:
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

    if t.TYPE_CHECKING:
        parallel_env: str
        tot_num_mpiprocs: int

    @classmethod
    def validate_resources(cls, **kwargs: t.Any) -> AttributeDict:
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
            msg = f'these parameters were not recognized: {", ".join(list(kwargs.keys()))}'
            raise ValueError(msg)

        return resources

    def __init__(self, **kwargs: t.Any):
        """Initialize the job resources from the passed arguments (the valid keys can be
        obtained with the function self.get_valid_keys()).

        :raises ValueError: if the resources are invalid or incomplete
        """
        resources = self.validate_resources(**kwargs)
        super().__init__(resources)

    @classmethod
    def accepts_default_mpiprocs_per_machine(cls) -> t.Literal[False]:
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
      * ``codes_info``: a list of aiida.common.datastructures.JobTemplateCodeInfo objects.
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

    if t.TYPE_CHECKING:
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
    stdin_name: str | None = None
    stdout_name: str | None = None
    stderr_name: str | None = None
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
         ``aiida.common.datastructures.JobState``)
       * ``job_substate``: a string with the implementation-specific sub-state
       * ``allocated_machines``: a list of machines used for the current job.
         This is a list of :py:class:`aiida.common.datastructures.MachineInfo` objects.
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

    # NOTE: All of these fields might be undefined, in which case they return `None`,
    # see the definition of DefaultFieldsAttributeDict.__getitem__
    if t.TYPE_CHECKING:
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
        requested_wallclock_time_seconds: int | None
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
            msg = f'invalid type for value {job_state}, should be an instance of `JobState`'  # type: ignore[unreachable]
            raise TypeError(msg)

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
    def serialize_field(cls, value: t.Any, field_type: str | None) -> t.Any:
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
    def deserialize_field(cls, value: t.Any, field_type: str | None) -> t.Any:
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

    def get_dict(self) -> dict[str, t.Any]:
        """Serialise the current data into a dictionary that is JSON-serializable.

        :return: A dictionary
        """
        return {k: self.serialize_field(v, self._special_serializers.get(k, None)) for k, v in self.items()}

    @classmethod
    def load_from_dict(cls, data: dict[str, t.Any]) -> Self:
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
