from functools import partial
import logging


def tick_legacy_workflows(runner):
    tasks.workflow_stepper()
    interval = config.get("DAEMON_INTERVALS_WFSTEP", settings.DAEMON_INTERVALS_WFSTEP)
    runner.loop.call_later(interval, partial(tick_legacy_workflows, runner))


if __name__ == "__main__":
    from aiida.backends.utils import load_dbenv, is_dbenv_loaded

    if not is_dbenv_loaded():
        load_dbenv(process="daemon")

    from aiida.backends import settings
    from aiida.common.setup import get_profile_config
    from aiida import work
    from aiida.daemon import tasks
    from aiida.daemon import settings
    from aiida import backends

    # set up logging to console
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)

    logger = logging.getLogger(__name__)

    config = get_profile_config(backends.settings.AIIDADB_PROFILE)

    # TODO: Add the profile name to the RMQ prefix
    rmq_config = {
        'url': 'amqp://localhost',
        'prefix': 'aiida',
    }
    runner = work.DaemonRunner(rmq_config=rmq_config, rmq_submit=True)
    work.set_runner(runner)

    tick_legacy_workflows(runner)

    try:
        runner.start()
    except (SystemError, KeyboardInterrupt):
        print("Shutting down daemon")
        runner.close()
