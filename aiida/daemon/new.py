import time

if __name__ == "__main__":
    from aiida.backends.utils import load_dbenv, is_dbenv_loaded

    if not is_dbenv_loaded():
        load_dbenv(process="daemon")

    from aiida.backends import settings
    from aiida.work.globals import enable_rmq_all
    from aiida.work.daemon import launch_pending_jobs, launch_all_pending_job_calculations
    from aiida.common.setup import get_profile_config
    import aiida.daemon.settings

    config = get_profile_config(settings.AIIDADB_PROFILE)

    interval = config.get("DAEMON_INTERVALS_TICK_WORKFLOWS",
                          aiida.daemon.settings.DAEMON_INTERVALS_TICK_WORKFLOWS)

    print("Starting daemon")
    print("Enabling RMQ")
    enable_rmq_all()

    try:
        while True:
            launch_all_pending_job_calculations()
            launch_pending_jobs()
            time.sleep(interval)
    except (SystemError, KeyboardInterrupt):
        print("Shutting down daemon")
