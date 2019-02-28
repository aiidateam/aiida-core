# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Function that starts a daemon runner."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import logging
import signal

from aiida.common.log import configure_logging
from aiida.engine.daemon.client import get_daemon_client
from aiida.manage.manager import get_manager

LOGGER = logging.getLogger(__name__)


def start_daemon():
    """
    Start a daemon runner for the currently configured profile
    """
    daemon_client = get_daemon_client()
    configure_logging(daemon=True, daemon_log_file=daemon_client.daemon_log_file)

    try:
        runner = get_manager().create_daemon_runner()
    except Exception as exception:
        LOGGER.exception('daemon runner failed to start')
        raise

    def shutdown_daemon(_num, _frame):
        LOGGER.info('Received signal to shut down the daemon runner')
        runner.close()

    signal.signal(signal.SIGINT, shutdown_daemon)
    signal.signal(signal.SIGTERM, shutdown_daemon)

    LOGGER.info('Starting a daemon runner')

    try:
        runner.start()
    except SystemError as exception:
        LOGGER.info('Received a SystemError: %s', exception)
        runner.close()

    LOGGER.info('Daemon runner stopped')
