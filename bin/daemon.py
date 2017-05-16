import click
import logging
import time

from aiida.backends.utils import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()

from aiida.work.daemon import launch_pending_jobs
import aiida.work.daemon as work_daemon


@click.command()
@click.option('-v', '--verbose', count=True)
def run_daemon(verbose):
    if verbose is not None:
        if verbose == 1:
            level = logging.INFO
        else:
            level = logging.DEBUG

        FORMAT = "[%(filename)s:%(lineno)s - %(funcName)s()] %(message)s"
        logging.basicConfig(level=level, format=FORMAT)

    while True:
        work_daemon.launch_all_pending_job_calculations()
        launch_pending_jobs()
        time.sleep(10)


if __name__ == "__main__":
    run_daemon()
