"""Fixtures to interact with the daemon."""

from __future__ import annotations

import pathlib
import typing as t

import pytest

if t.TYPE_CHECKING:
    from aiida.engine import Process, ProcessBuilder
    from aiida.orm import ProcessNode


@pytest.fixture(scope='session')
def daemon_client(aiida_profile):
    """Return a daemon client for the configured test profile for the test session.

    The daemon will be automatically stopped at the end of the test session.

    Usage::

        def test(daemon_client):
            from aiida.engine.daemon.client import DaemonClient
            assert isinstance(daemon_client, DaemonClient)

    """
    from aiida.engine.daemon import get_daemon_client
    from aiida.engine.daemon.client import DaemonNotRunningException, DaemonTimeoutException

    daemon_client = get_daemon_client(aiida_profile.name)

    try:
        yield daemon_client
    finally:
        try:
            daemon_client.stop_daemon(wait=True)
        except DaemonNotRunningException:
            pass
        # Give an additional grace period by manually waiting for the daemon to be stopped. In certain unit test
        # scenarios, the built in wait time in ``daemon_client.stop_daemon`` is not sufficient and even though the
        # daemon is stopped, ``daemon_client.is_daemon_running`` will return false for a little bit longer.
        daemon_client._await_condition(
            lambda: not daemon_client.is_daemon_running,
            DaemonTimeoutException('The daemon failed to stop.'),
        )


@pytest.fixture
def started_daemon_client(daemon_client):
    """Ensure that the daemon is running for the test profile and return the associated client.

    Usage::

        def test(started_daemon_client):
            assert started_daemon_client.is_daemon_running

    """
    if not daemon_client.is_daemon_running:
        daemon_client.start_daemon()
        assert daemon_client.is_daemon_running

    yield daemon_client


@pytest.fixture
def stopped_daemon_client(daemon_client):
    """Ensure that the daemon is not running for the test profile and return the associated client.

    Usage::

        def test(stopped_daemon_client):
            assert not stopped_daemon_client.is_daemon_running

    """
    from aiida.engine.daemon.client import DaemonTimeoutException

    if daemon_client.is_daemon_running:
        daemon_client.stop_daemon(wait=True)
        # Give an additional grace period by manually waiting for the daemon to be stopped. In certain unit test
        # scenarios, the built in wait time in ``daemon_client.stop_daemon`` is not sufficient and even though the
        # daemon is stopped, ``daemon_client.is_daemon_running`` will return false for a little bit longer.
        daemon_client._await_condition(
            lambda: not daemon_client.is_daemon_running,
            DaemonTimeoutException('The daemon failed to stop.'),
        )

    yield daemon_client


@pytest.fixture
def submit_and_await(started_daemon_client):
    """Return a factory to submit a process and wait for it to achieve the given state.

    This fixture automatically loads the ``started_daemon_client`` fixture ensuring the daemon is already running,
    therefore it is not necessary to manually start the daemon.

    Usage::

        def test(submit_and_await):
            inputs = {
                ...
            }
            node = submit_and_await(SomeProcess, **inputs)

    The factory has the following signature:

    :param submittable: A process, a process builder or a process node. If it is a process or builder, it is submitted
        first before awaiting the desired state.
    :param state: The process state to wait for, by default it waits for the submittable to be ``FINISHED``.
    :param timeout: The time to wait for the process to achieve the state.
    :param kwargs: If the ``submittable`` is a process class, it is instantiated with the ``kwargs`` as inputs.
    :raises RuntimeError: If the process fails to achieve the specified state before the timeout expires.
    :returns `~aiida.orm.nodes.process.process.ProcessNode`: The process node.
    """
    from aiida.engine import ProcessState

    def factory(
        submittable: type[Process] | ProcessBuilder | ProcessNode,
        state: ProcessState = ProcessState.FINISHED,
        timeout: int = 20,
        **kwargs,
    ):
        import inspect
        import time

        from aiida.engine import Process, ProcessBuilder, submit
        from aiida.orm import ProcessNode

        if inspect.isclass(submittable) and issubclass(submittable, Process):
            node = submit(submittable, **kwargs)
        elif isinstance(submittable, ProcessBuilder):
            node = submit(submittable)
        elif isinstance(submittable, ProcessNode):
            node = submittable
        else:
            raise ValueError(f'type of submittable `{type(submittable)}` is not supported.')

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

    return factory
