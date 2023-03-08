# -*- coding: utf-8 -*-
"""Reimplemnt the current scheduler/transport to be based on a ComputeClient.
"""
# pylint: disable=protected-access
from __future__ import annotations

from copy import deepcopy
import datetime
import inspect
import os
from pathlib import PurePath
import tempfile
import time
import traceback
from types import TracebackType
import typing as t

from aiida.common.exceptions import InvalidOperation
from aiida.schedulers import Scheduler
from aiida.transports import Transport

from .protocol import (
    AuthCliOptionType,
    ComputeClientOpenProtocol,
    ConnectionTestResult,
    DetailedJobInfo,
    ListResult,
    ResourcesType,
)

if t.TYPE_CHECKING:
    from aiida.engine.processes.exit_code import ExitCode
    from aiida.orm import AuthInfo, Computer
    from aiida.schedulers.datastructures import JobInfo, JobResource, JobTemplate
    from aiida.transports.util import FileAttribute

SelfTv = t.TypeVar('SelfTv', bound='ComputeClientXY')


class ComputeClientXY(ComputeClientOpenProtocol):  # pylint: disable=too-many-public-methods
    """A compute client that uses a separate transport and scheduler."""

    def __init__(self, computer: Computer, scheduler_cls: type[Scheduler], transport_cls: type[Transport]) -> None:
        """Construct a new instance."""
        self._scheduler = scheduler_cls()
        self._transport_class = transport_cls
        # TODO we can't directly instantiate the transport here, because it requires an authinfo
        # and, at least in some existing tests, the authinfo is not yet set.
        self._maybe_transport: Transport | None = None
        # we have to save the authinfo, currently only for a few validate_connection tests
        self._maybe_authinfo: AuthInfo | None = None
        # we have to save the computer, currently only for get_auth_param_default,
        # and that only uses it to get the hostname (in some _suggestion_string methods)
        self._computer = computer
        super().__init__()

    def _set_authinfo(self, authinfo: AuthInfo) -> None:
        self._maybe_authinfo = authinfo
        self._maybe_transport = self._transport_class(machine=authinfo.computer.hostname, **authinfo.get_auth_params())
        self._scheduler.set_transport(self._maybe_transport)

    @property
    def _authinfo(self):
        if self._maybe_authinfo is None:
            raise InvalidOperation('AuthInfo is not set')
        return self._maybe_authinfo

    @property
    def _transport(self):
        if self._maybe_transport is None:
            raise InvalidOperation('AuthInfo is not set')
        return self._maybe_transport

    def validate_connection(self) -> t.Iterable[ConnectionTestResult]:
        if not self.is_open:
            raise ValueError('Connection is not open')
        tests: list[tuple[str, t.Callable[[ComputeClientXY], tuple[bool, str]]]] = [
            ('Checking for spurious output', _computer_test_no_unexpected_output),
            ('Getting number of jobs from scheduler', _computer_test_get_jobs),
            ('Determining remote user name', _computer_get_remote_username),
            ('Creating and deleting temporary file', _computer_create_temp_file),
            ('Checking for possible delay from using login shell', _computer_use_login_shell_performance),
        ]
        for test_name, test in tests:
            try:
                success, message = test(self)
            except Exception as exc:  # pylint: disable=broad-except
                yield ConnectionTestResult(test_name, False, '', exc, traceback.format_exc())
            else:
                if success:
                    yield ConnectionTestResult(test_name, True, message)
                else:
                    yield ConnectionTestResult(test_name, False, message)

    def valid_job_resource_keys(self) -> list[str]:
        return self._scheduler.job_resource_class.get_valid_keys()

    def create_job_resource(self, **kwargs: t.Any) -> JobResource:
        return self._scheduler.create_job_resource(**kwargs)

    def preprocess_resources(
        self, resources: ResourcesType, default_mpiprocs_per_machine: None | int = None
    ) -> ResourcesType:
        # TODO perhaps should create a copy here
        self._scheduler.preprocess_resources(resources, default_mpiprocs_per_machine)  # type: ignore
        return resources

    def validate_resources(self, **resources: t.Any) -> None:
        return self._scheduler.validate_resources(**resources)

    def get_feature(self, feature_name: t.Literal['can_query_by_user']) -> bool:
        return self._scheduler.get_feature(feature_name)

    # TODO maybe nice to have, but not actually used
    # def logger(self, type_: t.Literal['scheduler', 'transport']) -> Logger:
    #     """Return a logger instance."""
    #     if type_ == 'scheduler':
    #         return self._scheduler._logger
    #     if type_ == 'transport':
    #         return self._transport._logger
    #     raise ValueError(f'Invalid type {type_}')

    def get_submit_script(self, job_tmpl: JobTemplate) -> str:
        return self._scheduler.get_submit_script(job_tmpl)

    def submit_from_script(self, working_directory: str, submit_script: str) -> str | ExitCode:
        return self._scheduler.submit_from_script(working_directory, submit_script)

    def get_detailed_job_info(self, job_id: str) -> None | DetailedJobInfo:
        return self._scheduler.get_detailed_job_info(job_id)  # type: ignore

    def get_jobs(  # type: ignore[override]
        self,
        jobs: list[str] | None = None,
        user: str | None = None,
        as_dict: bool = False,
    ) -> list[JobInfo] | dict[str, JobInfo]:
        return self._scheduler.get_jobs(jobs, user, as_dict)

    def kill(self, jobid: str) -> bool:
        return self._scheduler.kill(jobid)

    def parse_output(
        self,
        detailed_job_info: None | DetailedJobInfo = None,
        stdout: str | None = None,
        stderr: str | None = None,
    ) -> ExitCode | None:
        return self._scheduler.parse_output(detailed_job_info, stdout, stderr)  # type: ignore

    def set_logger_extra(self, extra: t.Dict[str, t.Any]) -> None:
        self._transport.set_logger_extra(extra)

    @property
    def is_open(self) -> bool:
        return self._transport.is_open

    def open(self: SelfTv) -> SelfTv:
        self._transport.open()
        return self

    def close(self: SelfTv) -> SelfTv:
        self._transport.close()
        return self

    def __enter__(self: SelfTv) -> SelfTv:
        self._transport.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,  # pylint: disable=redefined-outer-name
    ) -> None:
        self._transport.__exit__(exc_type, exc_value, traceback)

    def get_cli_auth_options(self) -> t.Dict[str, AuthCliOptionType]:
        return self._transport_class.auth_options

    def get_auth_param_default(self, name: str) -> t.Any:
        suggester_name = f'_get_{name}_suggestion_string'
        members = dict(inspect.getmembers(self._transport_class))
        suggester = members.get(suggester_name, None)
        default = None
        if suggester:
            default = suggester(self._computer)
        else:
            default = self.get_cli_auth_options().get(name, {}).get('default')
        return default

    def get_minimum_job_poll_interval(self) -> float:
        return self._transport_class.DEFAULT_MINIMUM_JOB_POLL_INTERVAL

    def get_safe_open_interval(self) -> float:
        if self._maybe_transport is None:
            return self._transport_class._DEFAULT_SAFE_OPEN_INTERVAL
        return self._transport.get_safe_open_interval()

    @property
    def hostname(self) -> str | None:
        return self._transport.hostname

    @property
    def cwd(self) -> PurePath:
        return self._transport.getcwd()

    def chdir(self, path: str | PurePath) -> None:
        self._transport.chdir(path)

    def chmod(self, path: str | PurePath, mode: int) -> None:
        self._transport.chmod(path, mode)

    def chown(self, path: str | PurePath, uid: str, gid: str) -> None:
        self._transport.chown(path, uid, gid)

    def copy(
        self,
        remotesource: str,
        remotedestination: str,
        dereference: bool = False,
        recursive: bool = True,
    ) -> None:
        self._transport.copy(remotesource, remotedestination, dereference, recursive)

    def copyfile(self, remotesource: str, remotedestination: str, dereference: bool = False) -> None:
        self._transport.copyfile(remotesource, remotedestination, dereference)

    def copytree(self, remotesource: str, remotedestination: str, dereference: bool = False) -> None:
        self._transport.copytree(remotesource, remotedestination, dereference)

    def get(self, remotepath: str, localpath: str, *args, **kwargs) -> None:
        self._transport.get(remotepath, localpath, *args, **kwargs)

    def getfile(self, remotepath: str, localpath: str, *args, **kwargs) -> None:
        self._transport.getfile(remotepath, localpath, *args, **kwargs)

    def gettree(self, remotepath: str, localpath: str, *args, **kwargs) -> None:
        self._transport.gettree(remotepath, localpath, *args, **kwargs)

    def getcwd(self) -> str:
        return self._transport.getcwd()

    def get_attribute(self, path: str) -> FileAttribute:
        return self._transport.get_attribute(path)

    def get_mode(self, path: str) -> int:
        return self._transport.get_mode(path)

    def isdir(self, path: str) -> bool:
        return self._transport.isdir(path)

    def isfile(self, path: str) -> bool:
        return self._transport.isfile(path)

    def listdir(self, path: str = '.', pattern: str | None = None) -> list[str]:
        return self._transport.listdir(path, pattern)

    def listdir_withattributes(self, path: str = '.', pattern: str | None = None) -> list[ListResult]:
        return self._transport.listdir_withattributes(path, pattern)

    def makedirs(self, path: str, ignore_existing: bool = False) -> None:
        self._transport.makedirs(path, ignore_existing)

    def mkdir(self, path: str, ignore_existing: bool = False) -> None:
        self._transport.mkdir(path, ignore_existing)

    def normalize(self, path: str = '.') -> str:
        return self._transport.normalize(path)

    def put(self, localpath: str, remotepath: str, *args, **kwargs) -> None:
        self._transport.put(localpath, remotepath, *args, **kwargs)

    def putfile(self, localpath: str, remotepath: str, *args, **kwargs) -> None:
        self._transport.putfile(localpath, remotepath, *args, **kwargs)

    def puttree(self, localpath: str, remotepath: str, *args, **kwargs) -> None:
        self._transport.puttree(localpath, remotepath, *args, **kwargs)

    def remove(self, path: str) -> None:
        self._transport.remove(path)

    def rename(self, oldpath: str, newpath: str) -> None:
        self._transport.rename(oldpath, newpath)

    def rmdir(self, path: str) -> None:
        self._transport.rmdir(path)

    def rmtree(self, path: str) -> None:
        self._transport.rmtree(path)

    def gotocomputer_command(self, remotedir: str) -> str | None:
        return self._transport.gotocomputer_command(remotedir)

    def symlink(self, remotesource: str, remotedestination: str) -> None:
        self._transport.symlink(remotesource, remotedestination)

    def whoami(self) -> str:
        return self._transport.whoami()

    def path_exists(self, path: str) -> bool:
        return self._transport.path_exists(path)

    def iglob(self, pathname: str) -> t.Iterable[str]:
        return self._transport.iglob(pathname)

    def has_magic(self, string: str) -> bool:
        return self._transport.has_magic(string)


def _computer_test_get_jobs(client: ComputeClientXY) -> tuple[bool, str]:  # pylint: disable=unused-argument
    """Internal test to check if it is possible to check the queue state.

    :param client: an open compute client
    :param authinfo: the AuthInfo object (from which one can get computer and aiidauser)
    :return: tuple of boolean indicating success or failure and an optional string message
    """
    found_jobs = client.get_jobs(as_dict=True)
    return True, f'{len(found_jobs)} jobs found in the queue'


def _computer_test_no_unexpected_output(client: ComputeClientXY) -> tuple[bool, str]:  # pylint: disable=unused-argument
    """Test that there is no unexpected output from the connection.

    This can happen if e.g. there is some spurious command in the
    .bashrc or .bash_profile that is not guarded in case of non-interactive
    shells.

    :param client: an open compute client
    :param authinfo: the AuthInfo object (from which one can get computer and aiidauser)
    :return: tuple of boolean indicating success or failure and an optional string message
    """
    # Execute a command that should not return any error
    retval, stdout, stderr = client._transport.exec_command_wait('echo -n')
    if retval != 0:
        return False, f'The command `echo -n` returned a non-zero return code ({retval})'

    template = """
We detected some spurious output in the {} when connecting to the computer, as shown between the bars
=====================================================================================================
{}
=====================================================================================================
Please check that you don't have code producing output in your ~/.bash_profile, ~/.bashrc or similar.
If you don't want to remove the code, but just to disable it for non-interactive shells, see comments
in this troubleshooting section of the online documentation: https://bit.ly/2FCRDc5
"""
    if stdout:
        return False, template.format('stdout', stdout)

    if stderr:
        return False, template.format('stderr', stderr)

    return True, ''


def _computer_get_remote_username(client: ComputeClientXY) -> tuple[bool, str]:  # pylint: disable=unused-argument
    """Internal test to check if it is possible to determine the username on the remote.

    :param client: an open compute client
    :param authinfo: the AuthInfo object
    :return: tuple of boolean indicating success or failure and an optional string message
    """
    remote_user = client.whoami()
    return True, remote_user


def _computer_create_temp_file(client: ComputeClientXY) -> tuple[bool, str]:  # pylint: disable=unused-argument
    """
    Internal test to check if it is possible to create a temporary file
    and then delete it in the work directory

    :note: exceptions could be raised

    :param client: an open compute client
    :param authinfo: the AuthInfo object (from which one can get computer and aiidauser)
    :return: tuple of boolean indicating success or failure and an optional string message
    """
    file_content = f"Test from 'verdi computer test' on {datetime.datetime.now().isoformat()}"
    workdir = client._authinfo.get_workdir().format(username=client.whoami())

    try:
        client.chdir(workdir)
    except IOError:
        client.makedirs(workdir)
        client.chdir(workdir)

    with tempfile.NamedTemporaryFile(mode='w+') as tempf:
        fname = os.path.split(tempf.name)[1]
        remote_file_path = os.path.join(workdir, fname)
        tempf.write(file_content)
        tempf.flush()
        client.putfile(tempf.name, remote_file_path)

    if not client.path_exists(remote_file_path):
        return False, f'failed to create the file `{remote_file_path}` on the remote'

    handle, destfile = tempfile.mkstemp()
    os.close(handle)

    try:
        client.getfile(remote_file_path, destfile)
        with open(destfile, encoding='utf8') as dfile:
            read_string = dfile.read()

        if read_string != file_content:
            message = 'retrieved file content is different from what was expected'
            message += f'\n  Expected: {file_content}'
            message += f'\n  Retrieved: {read_string}'
            return False, message

    finally:
        os.remove(destfile)

    client.remove(remote_file_path)

    return True, ''


def _computer_use_login_shell_performance(client: ComputeClientXY) -> tuple[bool, str]:  # pylint: disable=unused-argument
    """Execute a command over the client with and without the ``use_login_shell`` option enabled.

    By default, AiiDA uses a login shell when connecting to a computer in order to operate in the same environment as a
    user connecting to the computer. However, loading the login scripts of the shell can take time, which can
    significantly slow down all commands executed by AiiDA and impact the throughput of calculation jobs. This test
    executes a simple command both with and without using a login shell and emits a warning if the login shell is slower
    by at least 100 ms. If the computer is already configured to avoid using a login shell, the test is skipped and the
    function returns a successful test result.
    """
    tolerance = 0.1  # 100 ms
    iterations = 3

    authinfo = client._authinfo
    auth_params = authinfo.get_auth_params()

    # If ``use_login_shell=False`` we don't need to test for it being slower.
    if not auth_params.get('use_login_shell', True):
        return True, ''

    auth_params_clone = deepcopy(auth_params)

    try:
        timing_false = time_use_login_shell(authinfo, auth_params_clone, False, iterations)
        timing_true = time_use_login_shell(authinfo, auth_params_clone, True, iterations)
    finally:
        authinfo.set_auth_params(auth_params)

    if timing_true - timing_false > tolerance:
        message = (
            'computer is configured to use a login shell, which is slower compared to a normal shell (Command execution'
            f' time of {timing_true} s versus {timing_false}, respectively).\nUnless this setting is really necessary, '
            'consider disabling it with: verdi computer configure core.local COMPUTER_NAME -n --no-use-login-shell'
        )
        return False, message

    return True, f'Execution time: {timing_true} vs {timing_false} for login shell and normal, respectively'


def time_use_login_shell(
    authinfo: 'AuthInfo', auth_params: t.Dict[str, t.Any], use_login_shell: bool, iterations: int = 3
) -> float:
    """Execute the ``whoami`` over the compute client for the given ``use_login_shell`` and report the time taken.

    :param authinfo: The ``AuthInfo`` instance to use.
    :param auth_params: The base authentication parameters.
    :param use_login_shell: Whether to use a login shell or not.
    :param iterations: The number of iterations of the command to call. Command will return the average call time.
    :return: The average call time of the ``client.whoami`` command.
    """
    auth_params['use_login_shell'] = use_login_shell
    authinfo.set_auth_params(auth_params)

    timings = []

    for _ in range(iterations):
        time_start = time.time()
        with authinfo.get_client() as client:
            client.whoami()
        timings.append(time.time() - time_start)

    return sum(timings) / iterations
