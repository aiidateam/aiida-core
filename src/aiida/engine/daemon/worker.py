###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Function that starts a daemon worker."""

import asyncio
import logging
import signal
import sys
import threading

from aiida.common.log import configure_logging
from aiida.engine.daemon.client import get_daemon_client
from aiida.engine.runners import Runner
from aiida.manage import get_config_option, get_manager
from aiida.manage.manager import Manager

LOGGER = logging.getLogger(__name__)


async def shutdown_worker(runner: Runner) -> None:
    """Cleanup tasks tied to the service's shutdown."""
    from asyncio import all_tasks, current_task

    LOGGER.info('Received signal to shut down the daemon worker')
    tasks = [task for task in all_tasks() if task is not current_task()]

    for task in tasks:
        task.cancel()

    await asyncio.gather(*tasks, return_exceptions=True)
    runner.close()

    LOGGER.info('Daemon worker stopped')

def create_daemon_runner(manager: Manager) -> 'Runner':
    """Create and return a new daemon runner.

    This is used by workers when the daemon is running and in testing.

    :param loop: the (optional) asyncio event loop to use

    :return: a runner configured to work in the daemon configuration

    """
    from plumpy.persistence import LoadSaveContext

    from aiida.engine import persistence
    from aiida.engine.processes.launcher import ProcessLauncher

    runner = manager.create_runner(broker_submit=True, loop=None)
    runner_loop = runner.loop

    # Listen for incoming launch requests
    task_receiver = ProcessLauncher(
        loop=runner_loop,
        persister=manager.get_persister(),
        load_context=LoadSaveContext(runner=runner),
        loader=persistence.get_object_loader(),
    )

    coordinator = manager.get_coordinator()
    assert coordinator is not None, 'coordinator not set for runner'
    coordinator.add_task_subscriber(task_receiver)

    return runner

def start_daemon_worker(foreground: bool = False) -> None:
    """Start a daemon worker for the currently configured profile.

    :param foreground: If true, the logging will be configured to write to stdout, otherwise it will be configured to
        write to the daemon log file.
    """
    daemon_client = get_daemon_client()
    configure_logging(with_orm=True, daemon=not foreground, daemon_log_file=daemon_client.daemon_log_file)

    LOGGER.debug(f'sys.executable: {sys.executable}')
    LOGGER.debug(f'sys.path: {sys.path}')

    try:
        manager = get_manager()
        runner = create_daemon_runner(manager)
        manager.set_runner(runner)
    except Exception:
        LOGGER.exception('daemon worker failed to start')
        raise

    if isinstance(rlimit := get_config_option('daemon.recursion_limit'), int):
        LOGGER.info('Setting maximum recursion limit of daemon worker to %s', rlimit)
        sys.setrecursionlimit(rlimit)

    signals = (signal.SIGTERM, signal.SIGINT)
    for s in signals:
        # https://github.com/python/mypy/issues/12557
        runner.loop.add_signal_handler(s, lambda s=s: asyncio.create_task(shutdown_worker(runner)))  # type: ignore[misc]

    # XXX: check the threading use is elegantly implemented: e.g. log handle, error handle, shutdown handle.
    # it should work and it is better to have runner has its own event loop to handle the aiida processes only.
    # however, it randomly fail some test because of resources not elegantly handled.
    # The problem is the runner running in thread is not closed when thread join, the join should be the shutdown operation.

    LOGGER.info('Starting a daemon worker')
    # runner_thread = threading.Thread(target=runner.start, daemon=False)
    # runner_thread.start()

    try:
        runner.start()
        # runner_thread.join()
    except SystemError as exception:
        LOGGER.info('Received a SystemError: %s', exception)
        runner.close()

    LOGGER.info('Daemon worker started')
