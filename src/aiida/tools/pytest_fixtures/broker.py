###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Fixtures to provide the message broker required by a test profile."""

from __future__ import annotations

import contextlib
import shutil
import signal
import subprocess
import sys
import time
import typing as t

import pytest

if t.TYPE_CHECKING:
    from aiida.brokers import ZeromqBroker
    from aiida.manage.configuration.profile import Profile


@pytest.fixture(scope='session')
def run_aiida_broker_service_for_profile() -> t.Callable[..., t.ContextManager[ZeromqBroker]]:
    """Return a context manager that runs a ZeroMQ broker service for a given profile.

    This exposes the same mechanism that the :func:`aiida_broker` fixture uses to launch the ZeroMQ service directly,
    independently of the daemon. It is intended for tests that provide their own profile (e.g. one whose broker service
    is rooted in a temporary directory) and need its service running for the duration of a block, without going through
    the session-scoped :func:`aiida_broker` fixture.

    Usage::

        def test(run_aiida_broker_service_for_profile, some_profile):
            with run_aiida_broker_service_for_profile(some_profile) as broker:
                ...

    :returns: A context manager that takes a :class:`~aiida.manage.configuration.profile.Profile` (and an optional
        ``timeout``) and runs the ZeroMQ broker service for the duration of the context, yielding the
        :class:`~aiida.brokers.zeromq.broker.ZeromqBroker` constructed from that profile.
    """

    @contextlib.contextmanager
    def run_broker_service(profile: Profile, timeout: float = 60.0):
        from aiida.brokers import ZeromqBroker

        broker = ZeromqBroker(profile)

        if broker.check_service_reachable():
            msg = f'The ZeroMQ broker service is already running at `{broker._service_dir}`.'
            raise RuntimeError(msg)

        broker._service_dir.mkdir(exist_ok=False)

        process = subprocess.Popen(
            [sys.executable, '-m', 'aiida.brokers.zeromq.service', '--service-dir', str(broker._service_dir)],
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        try:
            start_time = time.monotonic()
            while not broker.check_service_reachable():
                if process.poll() is not None:
                    msg = f'The ZeroMQ broker service exited before becoming reachable with code {process.returncode}.'
                    raise RuntimeError(msg)
                if time.monotonic() - start_time > timeout:
                    msg = f'The ZeroMQ broker service did not become reachable within {timeout} seconds.'
                    raise TimeoutError(msg)
                time.sleep(0.1)

            yield broker
        finally:
            if process.poll() is None:
                process.send_signal(signal.SIGINT)
                try:
                    process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()

            shutil.rmtree(broker._service_dir, ignore_errors=True)

    return run_broker_service


@pytest.fixture(scope='session', autouse=True)
def run_aiida_broker_service(aiida_profile: Profile, run_aiida_broker_service_for_profile) -> t.Iterator[None]:
    """Run the ZeroMQ broker service for the currently loaded test profile for the duration of the session."""
    if aiida_profile.process_control_backend != 'core.zeromq':
        yield None
        return

    with run_aiida_broker_service_for_profile(aiida_profile):
        yield None
