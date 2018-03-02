# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.common.log import aiidalogger
from aiida.cmdline.dbenv_lazyloading import with_dbenv

logger = aiidalogger.getChild(__name__)


DAEMON_LEGACY_WORKFLOW_INTERVAL = 30


@with_dbenv()
def start_daemon():
    """
    Start a daemon runner for the currently configured profile
    """
    from aiida.cmdline.commands.daemon import ProfileConfig
    from aiida.common.log import configure_logging
    from aiida.work.rmq import get_rmq_config
    from aiida.work import DaemonRunner, set_runner

    profile_config = ProfileConfig()
    configure_logging(daemon=True, daemon_log_file=profile_config.daemon_log_file)

    runner = DaemonRunner(rmq_config=get_rmq_config(), rmq_submit=False)
    set_runner(runner)

    tick_legacy_workflows(runner)

    try:
        runner.start()
    except (SystemError, KeyboardInterrupt):
        logger.warning('Shutting down daemon')
        runner.close()


def tick_legacy_workflows(runner, interval=DAEMON_LEGACY_WORKFLOW_INTERVAL):
    """
    Function that will call the legacy workflow stepper and ask the runner to call the
    same function back after a certain interval, essentially polling the worklow stepper

    :param runner: the DaemonRunner instance to perform the callback
    :param interval: the number of seconds to wait between callbacks
    """
    from functools import partial

    logger.info('Ticking the legacy workflows')
    legacy_workflow_stepper()
    runner.loop.call_later(interval, partial(tick_legacy_workflows, runner))


def legacy_workflow_stepper():
    """
    Function to tick the legacy workflows
    """
    from datetime import timedelta
    from aiida.daemon.timestamps import set_daemon_timestamp, get_last_daemon_timestamp
    from aiida.daemon.workflowmanager import execute_steps

    logger.info('Checking for workflows to manage')
    # RUDIMENTARY way to check if this task is already running (to avoid acting
    # again and again on the same workflow steps)
    try:
        stepper_is_running = (get_last_daemon_timestamp('workflow', when='stop')
                              - get_last_daemon_timestamp('workflow', when='start')) <= timedelta(0)
    except TypeError:
        # When some timestamps are None (undefined)
        stepper_is_running = (get_last_daemon_timestamp('workflow', when='stop')
                              is None and get_last_daemon_timestamp('workflow', when='start') is not None)

    if not stepper_is_running:
        set_daemon_timestamp(task_name='workflow', when='start')
        # The previous wf manager stopped already -> we can run a new one
        logger.info('Running execute_steps')
        execute_steps()
        set_daemon_timestamp(task_name='workflow', when='stop')
    else:
        logger.info('Execute_steps already running')