# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from aiida.cmdline.dbenv_lazyloading import with_dbenv


def tick_legacy_workflows(runner, interval=30):
    from functools import partial
    from aiida.daemon.tasks import legacy_workflow_stepper
    print 'ticking legacy workflows.'
    legacy_workflow_stepper()
    runner.loop.call_later(interval, partial(tick_legacy_workflows, runner))


@with_dbenv()
def start_daemon():
    """
    Start a daemon runner
    """
    from aiida import work
    from aiida.cmdline.commands.daemon import ProfileConfig, get_current_profile_config
    from aiida.common.log import configure_logging
    from aiida.daemon import settings

    profile_config = ProfileConfig()
    configure_logging(daemon=True, daemon_log_file=profile_config.daemon_log_file)

    rmq_config = {
        'url': 'amqp://localhost',
        'prefix': work.rmq._get_prefix(),
    }
    runner = work.DaemonRunner(rmq_config=rmq_config, rmq_submit=False)
    work.set_runner(runner)

    config = get_current_profile_config()
    interval = config.get('DAEMON_INTERVALS_WFSTEP', settings.DAEMON_INTERVALS_WFSTEP)
    tick_legacy_workflows(runner, interval)

    try:
        runner.start()
    except (SystemError, KeyboardInterrupt):
        print("Shutting down daemon")
        runner.close()
