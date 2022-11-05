# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=redefined-outer-name,unused-argument
"""Collection of pytest fixtures using the TestManager for easy testing of AiiDA plugins."""
from __future__ import annotations

import asyncio
import copy
import pathlib
import shutil
import tempfile
import time
import warnings

import plumpy
import pytest
import wrapt

from aiida import plugins
from aiida.common.lang import type_check
from aiida.common.log import AIIDA_LOGGER
from aiida.common.warnings import warn_deprecation
from aiida.engine import Process, ProcessBuilder, submit
from aiida.engine.daemon.client import DaemonClient
from aiida.manage.tests import get_test_backend_name, get_test_profile_name, test_manager
from aiida.orm import ProcessNode


@pytest.fixture(scope='function')
def aiida_caplog(caplog):
    """A copy of pytest's caplog fixture, which allows ``AIIDA_LOGGER`` to propagate."""
    propogate = AIIDA_LOGGER.propagate
    AIIDA_LOGGER.propagate = True
    yield caplog
    AIIDA_LOGGER.propagate = propogate


@pytest.fixture(scope='session', autouse=True)
def aiida_profile():
    """Set up AiiDA test profile for the duration of the tests.

    Note: scope='session' limits this fixture to run once per session. Thanks to ``autouse=True``, you don't actually
     need to depend on it explicitly - it will activate as soon as you import it in your ``conftest.py``.
    """
    with test_manager(backend=get_test_backend_name(), profile_name=get_test_profile_name()) as manager:
        yield manager
    # Leaving the context manager will automatically cause the `TestManager` instance to be destroyed


@pytest.fixture(scope='function')
def aiida_profile_clean(aiida_profile):
    """Provide an AiiDA test profile, with the storage reset at test function setup."""
    aiida_profile.clear_profile()
    yield aiida_profile


@pytest.fixture(scope='class')
def aiida_profile_clean_class(aiida_profile):
    """Provide an AiiDA test profile, with the storage reset at test class setup."""
    aiida_profile.clear_profile()
    yield aiida_profile


@pytest.fixture(scope='function')
def clear_database(clear_database_after_test):
    """Alias for 'clear_database_after_test'.

    Clears the database after each test. Use of the explicit
    'clear_database_after_test' is preferred.
    """


@pytest.fixture(scope='function')
def clear_database_after_test(aiida_profile):
    """Clear the database after the test."""
    warn_deprecation('the clear_database_after_test fixture is deprecated, use aiida_profile_clean instead', version=3)
    yield aiida_profile
    aiida_profile.clear_profile()


@pytest.fixture(scope='function')
def clear_database_before_test(aiida_profile):
    """Clear the database before the test."""
    warn_deprecation('the clear_database_before_test fixture deprecated, use aiida_profile_clean instead', version=3)
    aiida_profile.clear_profile()
    yield aiida_profile


@pytest.fixture(scope='class')
def clear_database_before_test_class(aiida_profile):
    """Clear the database before a test class."""
    warn_deprecation(
        'the clear_database_before_test_class is deprecated, use aiida_profile_clean_class instead', version=3
    )
    aiida_profile.clear_profile()
    yield


@pytest.fixture(scope='function')
def temporary_event_loop():
    """Create a temporary loop for independent test case"""
    current = asyncio.get_event_loop()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        yield
    finally:
        loop.close()
        asyncio.set_event_loop(current)


@pytest.fixture(scope='function')
def temp_dir():
    """Get a temporary directory.

    E.g. to use as the working directory of an AiiDA computer.

    :return: The path to the directory
    :rtype: str

    """
    warn_deprecation('This fixture is deprecated, use the `tmp_path` fixture of `pytest` instead.', version=3)
    try:
        dirpath = tempfile.mkdtemp()
        yield dirpath
    finally:
        # after the test function has completed, remove the directory again
        shutil.rmtree(dirpath)


@pytest.fixture(scope='function')
def aiida_localhost(tmp_path):
    """Get an AiiDA computer for localhost.

    Usage::

      def test_1(aiida_localhost):
          label = aiida_localhost.label
          # proceed to set up code or use 'aiida_local_code_factory' instead


    :return: The computer node
    :rtype: :py:class:`aiida.orm.Computer`
    """
    from aiida.common.exceptions import NotExistent
    from aiida.orm import Computer

    label = 'localhost-test'

    try:
        computer = Computer.collection.get(label=label)
    except NotExistent:
        computer = Computer(
            label=label,
            description='localhost computer set up by test manager',
            hostname=label,
            workdir=str(tmp_path),
            transport_type='core.local',
            scheduler_type='core.direct'
        )
        computer.store()
        computer.set_minimum_job_poll_interval(0.)
        computer.set_default_mpiprocs_per_machine(1)
        computer.configure()

    return computer


@pytest.fixture(scope='function')
def aiida_local_code_factory(aiida_localhost):
    """Get an AiiDA code on localhost.

    Searches in the PATH for a given executable and creates an AiiDA code with provided entry point.

    Usage::

      def test_1(aiida_local_code_factory):
          code = aiida_local_code_factory('quantumespresso.pw', '/usr/bin/pw.x')
          # use code for testing ...

    :return: A function get_code(entry_point, executable) that returns the `Code` node.
    :rtype: object
    """

    def get_code(entry_point, executable, computer=aiida_localhost, label=None, prepend_text=None, append_text=None):
        """Get local code.

        Sets up code for given entry point on given computer.

        :param entry_point: Entry point of calculation plugin
        :param executable: name of executable; will be searched for in local system PATH.
        :param computer: (local) AiiDA computer
        :param prepend_text: a string of code that will be put in the scheduler script before the execution of the code.
        :param append_text: a string of code that will be put in the scheduler script after the execution of the code.
        :return: the `Code` either retrieved from the database or created if it did not yet exist.
        :rtype: :py:class:`aiida.orm.Code`
        """
        from aiida.common import exceptions
        from aiida.orm import Computer, InstalledCode, QueryBuilder

        if label is None:
            label = executable

        builder = QueryBuilder().append(Computer, filters={'uuid': computer.uuid}, tag='computer')
        builder.append(
            InstalledCode, filters={
                'label': label,
                'attributes.input_plugin': entry_point
            }, with_computer='computer'
        )

        try:
            code = builder.one()[0]
        except (exceptions.MultipleObjectsError, exceptions.NotExistent):
            code = None
        else:
            return code

        executable_path = shutil.which(executable)
        if not executable_path:
            raise ValueError(f'The executable "{executable}" was not found in the $PATH.')

        code = InstalledCode(
            label=label,
            description=label,
            default_calc_job_plugin=entry_point,
            computer=computer,
            filepath_executable=executable_path
        )

        if prepend_text is not None:
            code.prepend_text = prepend_text

        if append_text is not None:
            code.append_text = append_text

        return code.store()

    return get_code


@pytest.fixture(scope='session')
def daemon_client(aiida_profile):
    """Return a daemon client for the configured test profile for the test session.

    The daemon will be automatically stopped at the end of the test session.
    """
    daemon_client = DaemonClient(aiida_profile._manager._profile)  # pylint: disable=protected-access

    try:
        yield daemon_client
    finally:
        daemon_client.stop_daemon(wait=True)
        assert not daemon_client.is_daemon_running


@pytest.fixture()
def started_daemon_client(daemon_client):
    """Ensure that the daemon is running for the test profile and return the associated client."""
    if not daemon_client.is_daemon_running:
        daemon_client.start_daemon()
        assert daemon_client.is_daemon_running

    yield daemon_client


@pytest.fixture()
def stopped_daemon_client(daemon_client):
    """Ensure that the daemon is not running for the test profile and return the associated client."""
    if daemon_client.is_daemon_running:
        daemon_client.stop_daemon(wait=True)
        assert not daemon_client.is_daemon_running

    yield daemon_client


@pytest.fixture
def submit_and_await(started_daemon_client):
    """Submit a process and wait for it to achieve the given state."""

    def _factory(
        submittable: Process | ProcessBuilder | ProcessNode,
        state: plumpy.ProcessState = plumpy.ProcessState.FINISHED,
        timeout: int = 20
    ):
        """Submit a process and wait for it to achieve the given state.

        :param submittable: A process, a process builder or a process node. If it is a process or builder, it is
            submitted first before awaiting the desired state.
        :param state: The process state to wait for, by default it waits for the submittable to be ``FINISHED``.
        :param timeout: The time to wait for the process to achieve the state.
        :raises RuntimeError: If the process fails to achieve the specified state before the timeout expires.
        """
        if not isinstance(submittable, ProcessNode):
            node = submit(submittable)
        else:
            node = submittable

        start_time = time.time()

        while node.process_state is not state:

            if node.is_excepted:
                raise RuntimeError(f'The process excepted: {node.exception}')

            if time.time() - start_time >= timeout:
                daemon_log_file = pathlib.Path(started_daemon_client.daemon_log_file).read_text(encoding='utf-8')
                daemon_status = 'running' if started_daemon_client.is_daemon_running else 'stopped'
                raise RuntimeError(
                    f'Timed out waiting for process with state `{node.process_state}` to enter state `{state}`.\n'
                    f'Daemon <{started_daemon_client.profile.name}|{daemon_status}> log file content: \n'
                    f'{daemon_log_file}'
                )

        return node

    return _factory


@wrapt.decorator
def suppress_deprecations(wrapped, _, args, kwargs):
    """Decorator that suppresses all ``DeprecationWarning``."""
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=DeprecationWarning)
        return wrapped(*args, **kwargs)


class EntryPointManager:
    """Manager to temporarily add or remove entry points."""

    @staticmethod
    def eps():
        return plugins.entry_point.eps()

    @staticmethod
    def _validate_entry_point(entry_point_string: str | None, group: str | None, name: str | None) -> tuple[str, str]:
        """Validate the definition of the entry point.

        :param entry_point_string: Fully qualified entry point string.
        :param name: Entry point name.
        :param group: Entry point group.
        :returns: The entry point group and name.
        :raises TypeError: If `entry_point_string`, `group` or `name` are not a string, when defined.
        :raises ValueError: If `entry_point_string` is not defined, nor a `group` and `name`.
        :raises ValueError: If `entry_point_string` is not a complete entry point string with group and name.
        """
        if entry_point_string is not None:
            try:
                group, name = plugins.entry_point.parse_entry_point_string(entry_point_string)
            except TypeError as exception:
                raise TypeError('`entry_point_string` should be a string when defined.') from exception
            except ValueError as exception:
                raise ValueError('invalid `entry_point_string` format, should `group:name`.') from exception

        if name is None or group is None:
            raise ValueError('neither `entry_point_string` is defined, nor `name` and `group`.')

        type_check(group, str)
        type_check(name, str)

        return group, name

    @suppress_deprecations
    def add(
        self,
        value: type | str,
        entry_point_string: str | None = None,
        *,
        name: str | None = None,
        group: str | None = None
    ) -> None:
        """Add an entry point.

        :param value: The class or function to register as entry point. The resource needs to be importable, so it can't
            be inlined. Alternatively, the fully qualified name can be passed as a string.
        :param entry_point_string: Fully qualified entry point string.
        :param name: Entry point name.
        :param group: Entry point group.
        :returns: The entry point group and name.
        :raises TypeError: If `entry_point_string`, `group` or `name` are not a string, when defined.
        :raises ValueError: If `entry_point_string` is not defined, nor a `group` and `name`.
        :raises ValueError: If `entry_point_string` is not a complete entry point string with group and name.
        """
        if not isinstance(value, str):
            value = f'{value.__module__}:{value.__name__}'

        group, name = self._validate_entry_point(entry_point_string, group, name)
        entry_point = plugins.entry_point.EntryPoint(name, value, group)
        self.eps()[group].append(entry_point)

    @suppress_deprecations
    def remove(
        self, entry_point_string: str | None = None, *, name: str | None = None, group: str | None = None
    ) -> None:
        """Remove an entry point.

        :param value: Entry point value, fully qualified import path name.
        :param entry_point_string: Fully qualified entry point string.
        :param name: Entry point name.
        :param group: Entry point group.
        :returns: The entry point group and name.
        :raises TypeError: If `entry_point_string`, `group` or `name` are not a string, when defined.
        :raises ValueError: If `entry_point_string` is not defined, nor a `group` and `name`.
        :raises ValueError: If `entry_point_string` is not a complete entry point string with group and name.
        """
        group, name = self._validate_entry_point(entry_point_string, group, name)

        for entry_point in self.eps()[group]:
            if entry_point.name == name:
                self.eps()[group].remove(entry_point)
                break
        else:
            raise KeyError(f'entry point `{name}` does not exist in group `{group}`.')


@pytest.fixture
def entry_points(monkeypatch) -> EntryPointManager:
    """Return an instance of the ``EntryPointManager`` which allows to temporarily add or remove entry points.

    This fixture creates a deep copy of the entry point cache returned by the :func:`aiida.plugins.entry_point.eps`
    method and then monkey patches that function to return the deepcopy. This ensures that the changes on the entry
    point cache performed during the test through the manager are undone at the end of the function scope.

    .. note:: This fixture does not use the ``suppress_deprecations`` decorator on purpose, but instead adds it manually
        inside the fixture's body. The reason is that otherwise all deprecations would be suppressed for the entire
        scope of the fixture, including those raised by the code run in the test using the fixture, which is not
        desirable.

    """
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=DeprecationWarning)
        eps_copy = copy.deepcopy(plugins.entry_point.eps())
    monkeypatch.setattr(plugins.entry_point, 'eps', lambda: eps_copy)
    yield EntryPointManager()
