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
from typing import Union

from aiida.common.log import configure_logging
from aiida.engine.daemon.client import get_daemon_client
from aiida.engine.runners import Runner
from aiida.manage import get_config_option, get_manager

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


def start_daemon_worker(foreground: bool = False, profile_name: Union[str, None] = None) -> None:
    """Start a daemon worker for the currently configured profile.

    :param foreground: If true, the logging will be configured to write to stdout, otherwise it will be configured to
        write to the daemon log file.
    """

    daemon_client = get_daemon_client(profile_name)
    configure_logging(with_orm=True, daemon=not foreground, daemon_log_file=daemon_client.daemon_log_file)

    LOGGER.debug(f'sys.executable: {sys.executable}')
    LOGGER.debug(f'sys.path: {sys.path}')

    try:
        manager = get_manager()
        runner = manager.create_daemon_runner()
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

    try:
        LOGGER.info('Starting a daemon worker')
        runner.start()
    except SystemError as exception:
        LOGGER.info('Received a SystemError: %s', exception)
        runner.close()

    LOGGER.info('Daemon worker started')
