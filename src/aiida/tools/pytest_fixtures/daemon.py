"""Fixtures to interact with the daemon."""

from __future__ import annotations

import contextlib
import logging
import pathlib
import typing as t

import psutil
import pytest

if t.TYPE_CHECKING:
    from aiida.engine import Process, ProcessBuilder
    from aiida.engine.daemon.client import DaemonClient
    from aiida.orm import ProcessNode

LOGGER = logging.getLogger('tests.daemon')


def _kill_daemon_processes(daemon_client: DaemonClient) -> None:
    """Forcefully terminate leftover daemon processes after a graceful stop failed.

    A wedged circus keeps its PID file, so ``is_daemon_running`` stays ``True`` and every later stop, start or
    status call fails, poisoning all remaining tests on the worker. SIGKILL the circus process tree identified
    through the PID file and clean up its runtime files best-effort, so the next start begins from scratch.
    Never raises: callers fall through to a fresh start or report the original timeout.
    """
    from aiida.engine.daemon.client import DaemonException

    pid = daemon_client.get_daemon_pid()
    process = None
    if pid is not None:
        try:
            # Raises if the PID is stale or recycled, in which case it must never be killed.
            daemon_client._check_pid_file()
            process = psutil.Process(pid)
        except DaemonException:
            process = None
        except psutil.NoSuchProcess:
            process = None

    if process is not None:
        try:
            targets = [process, *process.children(recursive=True)]
            for target in targets:
                with contextlib.suppress(psutil.NoSuchProcess, psutil.AccessDenied):
                    target.kill()
            _, alive = psutil.wait_procs(targets, timeout=10)
            for target in alive:
                with contextlib.suppress(psutil.NoSuchProcess, psutil.AccessDenied):
                    LOGGER.warning('Daemon process survived SIGKILL: pid=%s cmdline=%s', target.pid, target.cmdline())
        except Exception as exception:  # best-effort cleanup must never raise
            LOGGER.warning('Failed to kill leftover daemon processes: %s', exception)

    with contextlib.suppress(OSError):
        pathlib.Path(daemon_client.circus_pid_file).unlink(missing_ok=True)
    with contextlib.suppress(OSError):
        daemon_client.delete_circus_socket_directory()


def _stop_daemon(daemon_client: DaemonClient, message: str) -> None:
    """Stop the daemon, forcefully killing leftovers if graceful shutdown fails.

    A wedged circus keeps its PID file, so without the kill fallback every later stop, start or status call on
    the worker fails and poisons all remaining tests. Fail fast with the default timeout: consumers are marked
    non-strict xfail where flakiness is expected, so a slow stop still passes within the window.
    """
    from aiida.engine.daemon.client import DaemonException, DaemonTimeoutException

    if not daemon_client.is_daemon_running:
        return
    try:
        daemon_client.stop_daemon(wait=True)
        # Give an additional grace period by manually waiting for the daemon to be stopped. In certain unit test
        # scenarios, the built in wait time in ``daemon_client.stop_daemon`` is not sufficient and even though the
        # daemon is stopped, ``daemon_client.is_daemon_running`` will return false for a little bit longer.
        daemon_client._await_condition(
            lambda: not daemon_client.is_daemon_running,
            DaemonTimeoutException(message),
        )
    except DaemonException:
        _kill_daemon_processes(daemon_client)


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

    daemon_client = get_daemon_client(aiida_profile.name)

    try:
        yield daemon_client
    finally:
        _stop_daemon(daemon_client, 'The daemon failed to stop.')


@pytest.fixture
def started_daemon_client(daemon_client: DaemonClient):
    """Ensure a freshly restarted daemon for the test profile and return the associated client.

    The daemon caches profile state at startup, so a worker left running by an earlier test may no longer match
    the current profile. Restarting per test trades ~1s of runtime for a worker that always matches the test.
    Tests that only need the client should use ``daemon_client`` to avoid the restart cost.

    Usage::

        def test(started_daemon_client):
            assert started_daemon_client.is_daemon_running

    """
    _stop_daemon(daemon_client, 'The daemon failed to stop before restarting.')
    daemon_client.start_daemon()
    assert daemon_client.is_daemon_running

    logger = logging.getLogger('tests.daemon:started_daemon_client')
    logger.debug(f'Daemon log file is located at: {daemon_client.daemon_log_file}')

    yield daemon_client


@pytest.fixture
def stopped_daemon_client(daemon_client: DaemonClient):
    """Ensure that the daemon is not running for the test profile and return the associated client.

    Usage::

        def test(stopped_daemon_client):
            assert not stopped_daemon_client.is_daemon_running

    """
    _stop_daemon(daemon_client, 'The daemon failed to stop.')

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

        start_time = time.monotonic()

        while node.process_state is not state:
            if node.is_excepted:
                raise RuntimeError(f'The process excepted: {node.exception}')

            if time.monotonic() - start_time >= timeout:
                daemon_log_file = pathlib.Path(started_daemon_client.daemon_log_file).read_text(encoding='utf-8')
                daemon_status = 'running' if started_daemon_client.is_daemon_running else 'stopped'
                raise RuntimeError(
                    f'Timed out waiting for process with state `{node.process_state}` to enter state `{state}`.\n'
                    f'Daemon <{started_daemon_client.profile.name}|{daemon_status}> log file content: \n'
                    f'{daemon_log_file}'
                )
            time.sleep(0.1)

        return node

    return factory
