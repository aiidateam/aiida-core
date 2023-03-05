# -*- coding: utf-8 -*-
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

from aiida.common.log import configure_logging
from aiida.engine.daemon.client import get_daemon_client
from aiida.engine.runners import Runner
from aiida.manage import get_manager

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


def start_daemon_worker() -> None:
    """Start a daemon worker for the currently configured profile."""
    daemon_client = get_daemon_client()
    configure_logging(daemon=True, daemon_log_file=daemon_client.daemon_log_file)

    try:
        manager = get_manager()
        runner = manager.create_daemon_runner()
        manager.set_runner(runner)
    except Exception:
        LOGGER.exception('daemon worker failed to start')
        raise

    signals = (signal.SIGTERM, signal.SIGINT)
    for s in signals:  # pylint: disable=invalid-name
        runner.loop.add_signal_handler(s, lambda s=s: asyncio.create_task(shutdown_worker(runner)))

    try:
        LOGGER.info('Starting a daemon worker')
        runner.start()
    except SystemError as exception:
        LOGGER.info('Received a SystemError: %s', exception)
        runner.close()

    LOGGER.info('Daemon worker started')
