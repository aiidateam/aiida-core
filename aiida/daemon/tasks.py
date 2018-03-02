# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################



def legacy_workflow_stepper():
    """
    Function to tick the legacy workflows
    """
    from datetime import timedelta
    from aiida.common.log import aiidalogger
    from aiida.daemon.timestamps import set_daemon_timestamp, get_last_daemon_timestamp
    from aiida.daemon.workflowmanager import execute_steps

    logger = aiidalogger.getChild(__name__)

    logger.info('Checking for workflows to manage')
    # RUDIMENTARY way to check if this task is already running (to avoid acting
    # again and again on the same workflow steps)
    try:
        stepper_is_running = (get_last_daemon_timestamp('workflow', when='stop')
                              - get_last_daemon_timestamp('workflow', when='start')) <= timedelta(0)
    except TypeError:
        # when some timestamps are None (undefined)
        stepper_is_running = (get_last_daemon_timestamp('workflow', when='stop')
                              is None and get_last_daemon_timestamp('workflow', when='start') is not None)

    if not stepper_is_running:
        set_daemon_timestamp(task_name='workflow', when='start')
        # the previous wf manager stopped already -> we can run a new one
        logger.info('running execute_steps')
        execute_steps()
        set_daemon_timestamp(task_name='workflow', when='stop')
    else:
        logger.info('execute_steps already running')