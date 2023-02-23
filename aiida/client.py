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

- `Transport._get_safe_interval_suggestion_string` removed as never used
- `Transport._get_use_login_shell_suggestion_string` removed as never used

TODO: `get_client_class`
"""
from __future__ import annotations

from pathlib import PurePath
import typing as t

if t.TYPE_CHECKING:
    from logging import Logger

    from aiida.engine.processes.exit_code import ExitCode
    # TODO can these be dataclasses instead or something?
    from aiida.schedulers.datastructures import JobInfo, JobResource, JobTemplate

Self = t.TypeVar('Self', bound='ClientProtocol')


@t.runtime_checkable
class ClientProtocol(t.Protocol):
    """A user-facing protocol for a client, that can interact with a compute resource."""

    # FROM SCHEDULER

    @classmethod
    def create_job_resource(cls, **kwargs: t.Any) -> JobResource:
        """Create a suitable job resource from the kwargs specified."""

    @classmethod
    def preprocess_resources(
        cls, resources: ResourcesType, default_mpiprocs_per_machine: None | int = int
    ) -> ResourcesType:
        """Preprocess the resources before submission.

        :param resources: The resources to preprocess.
        :return: The preprocessed resources.
        """
        # Note: this originally mutated in place, but now returns

    @classmethod
    def validate_resources(cls, **resources: t.Any) -> None:
        """Validate the resources against the job resource class of this scheduler.

        :param resources: keyword arguments to define the job resources
        :raises ValueError: if the resources are invalid or incomplete
        """

    def get_feature(self, feature_name: t.Literal['can_query_by_user']) -> bool:
        """Return a feature flag for the client.

        :param feature_name: The name of the feature to query
            - can_query_by_user: Whether the submission query supports querying by jobs by user
        """

    def logger(self) -> Logger:
        """Return a logger instance."""
        # TODO separate for scheduler or transport

    def set_logger_extra(self, extra: t.Dict[str, t.Any]) -> None:
        """Set extra information to be added to the logger messages.

        :param extra: a dictionary with the extra information to add
        """

    def get_submit_script(self, job_tmpl: JobTemplate) -> str:
        """Return the submit script as a string.

        :return: the submit script as a string
        """

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

    @t.overload
    def get_jobs(
        self,
        jobs: list[str] | None = None,
        user: str | None = None,
        as_dict: t.Literal[False] = False,
    ) -> list[JobInfo]:
        ...

    @t.overload
    def get_jobs(
        self,
        jobs: list[str] | None = None,
        user: str | None = None,
        as_dict: t.Literal[True] = ...,
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

    def parse_output(
        self,
        detailed_job_info: None | DetailedJobInfo = None,
        stdout: str | None = None,
        stderr: str | None = None
    ) -> ExitCode | None:
        """Parse the output of the scheduler, for a returned job

        :param stdout: string with the output written by the scheduler to stdout.
        :param stderr: string with the output written by the scheduler to stderr.

        :raises: `FeatureNotAvailable` if not supported
        """
        # TODO instead of raising FeatureNotAvailable, use get_feature?

    # FROM TRANSPORT

    @property
    def is_open(self) -> bool:
        """Return whether the client is open."""

    def open(self) -> None:
        """Open the client, in an omnipotent manner."""

    def close(self) -> None:
        """Close th client."""

    def __enter__(self: Self) -> Self:
        """Open the client, in an omnipotent manner."""

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: t.Any,
    ) -> None:
        """Close the client."""

    @classmethod
    def get_auth_params(cls) -> t.Dict[str, AuthParamType]:
        """Return the authentication parameters.

        This maps the name of the parameter, to an option list
        """
        # replaces Transport.get_valid_auth_params and Transport.auth_options

    def get_safe_open_interval(self) -> float:
        """
        Get an interval (in seconds) that suggests how long the user should wait
        between consecutive calls to open the transport.  This can be used as
        a way to get the user to not swamp a limited number of connections, etc.
        However it is just advisory.

        If returns 0, it is taken that there are no reasons to limit the
        frequency of open calls.
        """

    @property
    def cwd(self) -> PurePath:
        """Return the current working directory."""

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


class AuthParamType(t.TypedDict, total=False):
    """A single authentication parameter."""
    type: type
    default: bool
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
