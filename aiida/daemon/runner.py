# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import absolute_import
import logging
import signal
from functools import partial

from aiida.common.log import configure_logging
from aiida.daemon.client import DaemonClient
from aiida.work.rmq import get_rmq_config
from aiida.work import DaemonRunner, set_runner


logger = logging.getLogger(__name__)

DAEMON_LEGACY_WORKFLOW_INTERVAL = 30


def start_daemon():
    """
    Start a daemon runner for the currently configured profile
    """
    daemon_client = DaemonClient()
    configure_logging(daemon=True, daemon_log_file=daemon_client.daemon_log_file)

    runner = DaemonRunner(rmq_config=get_rmq_config(), rmq_submit=False)

    def shutdown_daemon(num, frame):
        logger.info('Received signal to shut down the daemon runner')
        runner.close()

    signal.signal(signal.SIGINT, shutdown_daemon)
    signal.signal(signal.SIGTERM, shutdown_daemon)

    logger.info('Starting a daemon runner')

    set_runner(runner)
    tick_legacy_workflows(runner)

    try:
        runner.start()
    except SystemError as exception:
        logger.info('Received a SystemError: {}'.format(exception))
        runner.close()

    logger.info('Daemon runner stopped')


def tick_legacy_workflows(runner, interval=DAEMON_LEGACY_WORKFLOW_INTERVAL):
    """
    Function that will call the legacy workflow stepper and ask the runner to call the
    same function back after a certain interval, essentially polling the worklow stepper

    :param runner: the DaemonRunner instance to perform the callback
    :param interval: the number of seconds to wait between callbacks
    """
    logger.debug('Ticking the legacy workflows')
    legacy_workflow_stepper()
    runner.loop.call_later(interval, partial(tick_legacy_workflows, runner))


def legacy_workflow_stepper():
    """
    Function to tick the legacy workflows
    """
    from datetime import timedelta
    from aiida.daemon.timestamps import set_timestamp_workflow_stepper, get_timestamp_workflow_stepper
    from aiida.daemon.workflowmanager import execute_steps

    logger.debug('Checking for workflows to manage')
    # RUDIMENTARY way to check if this task is already running (to avoid acting
    # again and again on the same workflow steps)
    try:
        stepper_is_running = (get_timestamp_workflow_stepper(when='stop')
                              - get_timestamp_workflow_stepper(when='start')) <= timedelta(0)
    except TypeError:
        # When some timestamps are None (undefined)
        stepper_is_running = (get_timestamp_workflow_stepper(when='stop')
                              is None and get_timestamp_workflow_stepper(when='start') is not None)

    if not stepper_is_running:
        # The previous wf manager stopped already -> we can run a new one
        set_timestamp_workflow_stepper(when='start')
        logger.debug('Running execute_steps')
        execute_steps()
        set_timestamp_workflow_stepper(when='stop')
    else:
        logger.debug('Execute_steps already running')
