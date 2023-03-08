# -*- coding: utf-8 -*-
"""

Notes:

 - `get_short_doc` was removed (for transport and scheduler),
    since never actually used in the code base

 - only used internally in Scheduler:
    - `_job_resource_class`
    - `_get_submit_script_environment_variables`
    - `_get_submit_script_header`
    - `_get_submit_script_footer`
    - `_get_run_line`
    - `_get_joblist_command`
    - `_get_detailed_job_info_command`
    - `_parse_joblist_output`
    - `_get_submit_command`
    - `_parse_submit_output`
    - `_get_kill_command`
    - `_parse_kill_output`
    - `transport`

- `Transport._get_{name}_suggestion_string` access logic changed (see get_auth_param_default)
- `Transport.copy_from_remote_to_remote` removed as never used

- only used internally in Transport:
    - `_exec_command_internal`
    - `exec_command_wait_bytes`
    - `exec_command_wait`
    - `_gotocomputer_string`

"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePath
from types import TracebackType
import typing as t

if t.TYPE_CHECKING:
    from aiida.engine.processes.exit_code import ExitCode
    from aiida.schedulers.datastructures import JobInfo, JobResource, JobTemplate
    from aiida.transports.util import FileAttribute

SelfTv = t.TypeVar('SelfTv', bound='ComputeClientProtocol')


@dataclass
class ConnectionTestResult:
    """A result of a client connection test."""
    name: str
    """The name of the connection test."""
    success: bool
    """Whether the connection test was successful."""
    info: str = ''
    """Information about the connection test."""
    exception: None | Exception = None
    """The exception raised, if any."""
    traceback: str = ''
    """The traceback of the exception, if any."""


class ListResult(t.TypedDict, total=False):
    """Return type of listdir_withattributes."""

    name: str
    """the file or folder directory"""
    attributes: FileAttribute
    isdir: bool


class AuthCliOptionType(t.TypedDict, total=False):
    """A single authentication parameter, for use by the CLI"""

    type: type
    default: t.Any
    switch: bool
    help: str
    prompt: str
    non_interactive_default: bool
    callback: t.Callable[..., t.Any]


class ResourcesType(t.TypedDict, total=False):
    """Resources used by preprocess_resources."""

    num_machines: int | None
    tot_num_mpiprocs: int | None
    num_mpiprocs_per_machine: int | None


class DetailedJobInfo(t.TypedDict, total=False):
    """Return type of get_detailed_job_info."""

    retval: int  # non-zero if failed
    stdout: str
    stderr: str


# @t.runtime_checkable  # TODO # TODO overriden due to https://github.com/python/cpython/issues/102433
class ComputeClientProtocol(t.Protocol):  # pylint: disable=too-many-public-methods
    """A user-facing protocol for a client, that can interact with a compute resource.

    The interface serves two primary purposes:

    1. Interacting with the compute resource's file system,
       e.g. uploading/downloading files, altering files/directory, etc.
    2. Interacting with the compute resource's job scheduler,
       e.g. submitting jobs, querying job progress, etc.
    """

    # @property
    # def

    # FROM SCHEDULER

    def valid_job_resource_keys(self) -> list[str]:
        """Return a list of valid keys for the scheduler.

        :return: a list of valid keys
        """
        # Note this was originally a classmethod

    def create_job_resource(self, **kwargs: t.Any) -> JobResource:
        """Create a suitable job resource from the kwargs specified."""
        # Note this was originally a classmethod

    def preprocess_resources(
        self, resources: ResourcesType, default_mpiprocs_per_machine: None | int = None
    ) -> ResourcesType:
        """Preprocess the resources before submission.

        :param resources: The resources to preprocess.
        :return: The preprocessed resources.
        """
        # Note this was originally a classmethod
        # Note: this originally mutated in place, but now returns

    def validate_resources(self, **resources: t.Any) -> None:
        """Validate the resources against the job resource class of this scheduler.

        :param resources: keyword arguments to define the job resources
        :raises ValueError: if the resources are invalid or incomplete
        """
        # Note this was originally a classmethod
        # TODO I thing ideally resources would be input as a dict,
        # and then the return type could be a https://docs.python.org/3/library/typing.html#typing.TypeGuard

    def get_feature(self, feature_name: t.Literal['can_query_by_user']) -> bool:
        """Return a feature flag for the client.

        :param feature_name: The name of the feature to query
            - can_query_by_user: Whether the submission query supports querying by jobs by user
        """

    # TODO clash for scheduler and transport, so we insert a type
    # but also not actually used in the code base
    # def logger(self, type_: t.Literal['transport', 'scheduler']) -> Logger:
    #     """Return a logger instance."""

    def get_submit_script(self, job_tmpl: JobTemplate) -> str:
        """Return the submit script as a string.

        :return: the submit script as a string
        """
        # Note this was originally a classmethod

    def parse_output(
        self,
        detailed_job_info: None | DetailedJobInfo = None,
        stdout: str | None = None,
        stderr: str | None = None,
    ) -> ExitCode | None:
        """Parse the output of the scheduler, for a returned job

        :param stdout: string with the output written by the scheduler to stdout.
        :param stderr: string with the output written by the scheduler to stderr.

        :raises: `FeatureNotAvailable` if not supported
        """
        # TODO instead of raising FeatureNotAvailable, use get_feature?

    # FROM TRANSPORT

    def set_logger_extra(self, extra: t.Dict[str, t.Any]) -> None:
        """Set extra information to be added to the logger messages.

        :param extra: a dictionary with the extra information to add
        """

    @property
    def hostname(self) -> str | None:
        """Return the hostname of the remote computer."""
        # TODO is this a generic property of any compute client?
        # It is only actually used one place, in `RemoteData._clean`,
        # to check that the client (taken optionally as input) is compatible with the computer,
        # and this in turn is only used in `cmd_calcjob.calcjob_cleanworkdir`

    def get_cli_auth_options(self) -> t.Dict[str, AuthCliOptionType]:
        """Return authentication parameters for the CLI.

        This maps the name of the parameter, to an option list for use in the CLI
        """
        # Note this was originally a classmethod
        # replaces Transport.get_valid_auth_params and Transport.auth_options

    def get_auth_param_default(self, name: str) -> t.Any:
        """Return the default value for the given authentication parameter.
        """
        # Note this was originally a classmethod
        # replaces aiida.transports.cli.transport_option_default

    def get_minimum_job_poll_interval(self) -> float:
        """Return the minimum interval (in seconds) between job status queries.

        This is used to avoid overloading the scheduler with too many queries.
        """

    def get_safe_open_interval(self) -> float:
        """
        Get an interval (in seconds) that suggests how long the user should wait
        between consecutive calls to open the client.
        This can be used as a way to get the user to not swamp a limited number of connections, etc.
        However it is just advisory.

        If returns 0, it is taken that there are no reasons to limit the
        frequency of open calls.
        """

    def gotocomputer_command(self, remotedir: str) -> str | None:
        """Return a string to be run using os.system in order to connect
        via the to the remote directory, or None if not possible.

        Expected behaviors:

        * A new bash session is opened
        * A reasonable error message is produced if the folder does not exist

        :param remotedir: the full path of the remote directory
        """
        # TODO maybe this needs to be reimplemented
        # for now we allow to return None, if the feature is not available

    def has_magic(self, string: str) -> bool:
        """Return True if the string has shell-style wildcards."""
        # TODO this feels a bit too arbitrary to be part of the interface?

    @property
    def is_open(self) -> bool:
        """Return whether the client is open."""

    def open(self) -> ComputeClientOpenProtocol:
        """Open the client, in an omnipotent manner."""

    def __enter__(self) -> ComputeClientOpenProtocol:
        """Open the client, in an omnipotent manner."""

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close the client."""


class ComputeClientOpenProtocol(ComputeClientProtocol, t.Protocol):  # pylint: disable=too-many-public-methods
    """A user-facing protocol for a client, that can interact with a compute resource.

    This is extended from the base protocol,
    with operations only allowed on a connected compute client.
    """

    def close(self) -> ComputeClientProtocol:
        """Close the client."""

    def validate_connection(self) -> t.Iterable[ConnectionTestResult]:
        """Validate the connection to the compute resource.

        This performs a series of tests,
        to verify that the connection to the compute resource is working correctly.

        :yields: results of specific connection tests
        """
        # Note, this replaces the code in `aiida.cmdline.commands.computer_test`

    # scheduler operations

    def submit_from_script(self, working_directory: str, submit_script: str) -> str | ExitCode:
        """Submit the submission script to the scheduler.

        :param working_directory: the directory in which to execute the submission
        :param submit_script: the submission script file name,
            which should already exist in the working directory

        :return: return a string with the job ID in a valid format to be used for querying,
            or an ExitCode in case of failure.
        """
        # TODO change working_directory to PurePath or tuple of string
        # to make file-system agnostic?

    def get_detailed_job_info(self, job_id: str) -> None | DetailedJobInfo:
        """Return the detailed job info."""

    # TODO this should not need to be ignored: https://stackoverflow.com/a/65556542/5033292
    @t.overload
    def get_jobs(  # type: ignore
        self,
        jobs: list[str] | None = ...,
        user: str | None = ...,
        as_dict: t.Literal[False] = False,
    ) -> list[JobInfo]:
        ...

    @t.overload
    def get_jobs(
        self,
        jobs: list[str] | None = ...,
        user: str | None = ...,
        as_dict: t.Literal[True] = True,
    ) -> dict[str, JobInfo]:
        ...

    def get_jobs(
        self,
        jobs: list[str] | None = None,
        user: str | None = None,
        as_dict: bool = False,
    ) -> list[JobInfo] | dict[str, JobInfo]:
        """Return the list of currently active jobs.

        :param jobs: a list of jobs to check; only these are checked
        :param user: a string with a user: only jobs of this user are checked
        :param as_dict: if False, a list of JobInfo objects is returned. If True, a dictionary is
            returned, having as key the job_id and as value the JobInfo object.
        """

    def kill(self, jobid: str) -> bool:
        """Kill a remote job and parse the return value of the scheduler to check if the command succeeded.

        ..note::

            On some schedulers, even if the command is accepted, it may take some seconds for the job to actually
            disappear from the queue.

        :param jobid: the job ID to be killed
        :return: True if everything seems ok, False otherwise.
        """

    # file system (a.k.a transport) operations

    def chdir(self, path: str | PurePath) -> None:
        """Change the current directory.

        :param path: The absolute path to the new working directory
        :raises: IOError, if the requested path does not exist
        """

    def chmod(self, path: str | PurePath, mode: int) -> None:
        """Change permissions of a path.

        :param path: absolute or relative to the CWD
        """

    def chown(self, path: str | PurePath, uid: str, gid: str) -> None:
        """Change the owner (uid) and group (gid) of a path.

        :param path: absolute or relative to the CWD
        """

    def copy(
        self,
        remotesource: str,
        remotedestination: str,
        dereference: bool = False,
        recursive: bool = True,
    ) -> None:
        """Copy a file or a directory from remote source to remote destination
        (On the same remote machine)

        :param remotesource: path of the remote source directory / file
        :param remotedestination: path of the remote destination directory / file
        :param dereference: if True copy the contents of any symlinks found, otherwise copy the symlinks themselves
        :param recursive: if True copy directories recursively, otherwise only copy the specified file(s)

        :raises: IOError, if one of src or dst does not exist
        """

    def copyfile(self, remotesource: str, remotedestination: str, dereference: bool = False) -> None:
        """Copy a file from remote source to remote destination
        (On the same remote machine)

        :param remotesource: path of the remote source directory / file
        :param remotedestination: path of the remote destination directory / file
        :param dereference: if True copy the contents of any symlinks found, otherwise copy the symlinks themselves

        :raises IOError: if one of src or dst does not exist
        """

    def copytree(self, remotesource: str, remotedestination: str, dereference: bool = False) -> None:
        """Copy a folder from remote source to remote destination
        (On the same remote machine)

        :param remotesource: path of the remote source directory / file
        :param remotedestination: path of the remote destination directory / file
        :param dereference: if True copy the contents of any symlinks found, otherwise copy the symlinks themselves

        :raise IOError: if one of src or dst does not exist
        """

    def get(self, remotepath: str, localpath: str, *args, **kwargs) -> None:
        """Retrieve a file or folder from remote source to local destination
        dst must be an absolute path (src not necessarily)

        :param remotepath: remote_folder_path
        :param localpath: local_folder_path
        """
        # TODO what are the args and kwargs? should make explicit
        # it looks like this method is only used in execmanager.retrieve_files_from_list
        # with `ignore_nonexisting=True`
        # it passes down callback, dereference, overwrite to `gettree`, but not used there

    def getfile(self, remotepath: str, localpath: str, *args, **kwargs) -> None:
        """Retrieve a file from remote source to local destination
        dst must be an absolute path (src not necessarily)

        :param remotepath: remote_folder_path
        :param localpath: local_folder_path
        """

    def gettree(self, remotepath: str, localpath: str, *args, **kwargs) -> None:
        """Retrieve a folder recursively from remote source to local destination
        dst must be an absolute path (src not necessarily)

        :param remotepath: remote_folder_path
        :param localpath: local_folder_path
        """
        # TODO what are the args and kwargs? should make explicit
        # SshTransport sets callback=None, dereference=True, overwrite=True
        # again they do not seem to be used

    def getcwd(self) -> str:
        """Get working directory

        :return: the current working directory
        """

    def get_attribute(self, path: str) -> FileAttribute:
        """Get the stat of a file."""

    def get_mode(self, path: str) -> int:
        """Return the portion of the file's mode that can be set by chmod()."""

    def iglob(self, pathname: str) -> t.Iterable[str]:
        """Return an iterator which yields the paths matching a pathname pattern.

        The pattern may contain simple shell-style wildcards, as per fnmatch.
        """
        # Note removed glob, glob1 and glob0 as superfluous for the interface

    def isdir(self, path: str) -> bool:
        """Return whether the path is an existing directory."""

    def isfile(self, path: str) -> bool:
        """Return whether the path is an existing file."""

    def listdir(self, path: str = '.', pattern: str | None = None) -> list[str]:
        """Return a list of the names of the entries in the given path.

        The list is in arbitrary order. It does not include the special
        entries '.' and '..' even if they are present in the directory.

        :param path: path to list (default to '.')
        :param pattern: if used, listdir returns a list of files matching
                            filters in Unix style. Unix only.
        """

    def listdir_withattributes(self, path: str = '.', pattern: str | None = None) -> list[ListResult]:
        """Return a list of the names of the entries in the given path.

        The list is in arbitrary order. It does not include the special
        entries '.' and '..' even if they are present in the directory.

        :param path: path to list (default to '.')
        :param pattern: if used, listdir returns a list of files matching
                        filters in Unix style. Unix only.
        """

    def makedirs(self, path: str, ignore_existing: bool = False) -> None:
        """Create a leaf directory and all intermediate ones.

        Works like mkdir, except that any intermediate path segment (not
        just the rightmost) will be created if it does not exist.

        :param path: directory to create
        :param ignore_existing: if set to true, it doesn't give any error
                                if the leaf directory does already exist

        :raises: OSError, if directory at path already exists
        """

    def mkdir(self, path: str, ignore_existing: bool = False) -> None:
        """Create a folder (directory) named path.

        :param path: name of the folder to create
        :param ignore_existing: if True, does not give any error if the
                                     directory already exists

        :raises: OSError, if directory at path already exists
        """

    def normalize(self, path: str = '.') -> str:
        """Return the normalized path (on the server) of a given path.

        This can be used to quickly resolve symbolic links or determine
        what the server is considering to be the "current folder".

        :raise IOError: if the path can't be resolved on the server
        """

    def path_exists(self, path: str) -> bool:
        """Returns True if path exists, False otherwise."""

    def put(self, localpath: str, remotepath: str, *args, **kwargs) -> None:
        """Put a file or a directory from local src to remote dst.

        src must be an absolute path (dst not necessarily))
        Redirects to putfile and puttree.

        :param localpath: absolute path to local source
        :param remotepath: path to remote destination
        """
        # TODO what are the args and kwargs? should make explicit

    def putfile(self, localpath: str, remotepath: str, *args, **kwargs) -> None:
        """Put a file from local src to remote dst.

        src must be an absolute path (dst not necessarily))

        :param localpath: absolute path to local file
        :param remotepath: path to remote file
        """
        # TODO what are the args and kwargs? should make explicit

    def puttree(self, localpath: str, remotepath: str, *args, **kwargs) -> None:
        """Put a folder recursively from local src to remote dst.

        src must be an absolute path (dst not necessarily))

        :param localpath: absolute path to local folder
        :param remotepath: path to remote folder
        """
        # TODO what are the args and kwargs? should make explicit

    def remove(self, path: str) -> None:
        """Remove the file at the given path.

        This only works on files;
        for removing folders (directories), use rmdir.

        :raise IOError: if the path is a directory
        """

    def rename(self, oldpath: str, newpath: str) -> None:
        """Rename a file or folder from oldpath to newpath.

        :param oldpath: existing name of the file or folder
        :param newpath: new name for the file or folder

        :raises IOError: if oldpath/newpath is not found
        :raises ValueError: if oldpath/newpath is not a valid string
        """

    def rmdir(self, path: str) -> None:
        """Remove the folder named path.

        This works only for empty folders.
        For recursive remove, use rmtree.

        :param path: absolute path to the folder to remove
        """

    def rmtree(self, path: str) -> None:
        """Remove recursively the content at path

        :param path: absolute path to remove
        """

    def symlink(self, remotesource: str, remotedestination: str) -> None:
        """Create a symbolic link between the remote source and the remote
        destination.

        :param remotesource: remote source
        :param remotedestination: remote destination
        """

    def whoami(self) -> str:
        """Get the remote username.

        :raise IOError: if the username cannot be retrieved
        """
