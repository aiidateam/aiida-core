# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################


def tick_legacy_workflows(runner, interval=30):
    from functools import partial
    from aiida.daemon.tasks import workflow_stepper
    workflow_stepper()
    runner.loop.call_later(interval, partial(tick_legacy_workflows, runner))

def start_daemon():
    """
    """
    from aiida.backends.utils import load_dbenv, is_dbenv_loaded
    if not is_dbenv_loaded():
        load_dbenv(process='daemon')

    from aiida import work
    from aiida.backends import settings as backend_settings
    from aiida.common.log import configure_logging
    from aiida.common.setup import get_profile_config
    from aiida.daemon import settings as daemon_settings

    configure_logging()

    rmq_config = {
        'url': 'amqp://localhost',
        'prefix': work.rmq._get_prefix(),
    }
    runner = work.DaemonRunner(rmq_config=rmq_config, rmq_submit=False)
    work.set_runner(runner)

    config = get_profile_config(backend_settings.AIIDADB_PROFILE)
    interval = config.get('DAEMON_INTERVALS_WFSTEP', daemon_settings.DAEMON_INTERVALS_WFSTEP)
    tick_legacy_workflows(runner, interval)

    try:
        runner.start()
    except (SystemError, KeyboardInterrupt):
        print("Shutting down daemon")
        runner.close()