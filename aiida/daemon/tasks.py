# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from datetime import timedelta

from aiida.backends.utils import load_dbenv, is_dbenv_loaded
from aiida.daemon.settings import DAEMON_INTERVALS_SUBMIT, DAEMON_INTERVALS_RETRIEVE, DAEMON_INTERVALS_UPDATE, \
    DAEMON_INTERVALS_WFSTEP, DAEMON_INTERVALS_TICK_WORKFLOWS, DAEMON_USE_NEW
from celery import Celery
from celery.task import periodic_task

from aiida.backends import settings
from aiida.backends.profile import BACKEND_SQLA, BACKEND_DJANGO
from aiida.common.setup import AIIDA_CONFIG_FOLDER, DAEMON_SUBDIR

if not is_dbenv_loaded():
    load_dbenv(process="daemon")

from aiida.common.log import configure_logging, aiidalogger
from aiida.common.setup import get_profile_config, DAEMON_LOG_FILE
from aiida.common.exceptions import ConfigurationError
from aiida.daemon.timestamps import set_daemon_timestamp, get_last_daemon_timestamp

LOGGER = aiidalogger.getChild(__name__)
config = get_profile_config(settings.AIIDADB_PROFILE)

engine = config["AIIDADB_ENGINE"]

# defining the broker.
# So far I am using SA for that, but we should totally
# think about using redis or rabbitmq, which is now possibly
# since now it is decoupled from a backend
# one would simply substitute the broker with whatever the user wants...

if not engine.startswith("postgre"):
    raise ConfigurationError("Only PostgreSQL is currently supported as database engine, you have {}".format(engine))
broker = (
    "sqla+postgresql://{AIIDADB_USER}:{AIIDADB_PASS}@"
    "{AIIDADB_HOST}:{AIIDADB_PORT}/{AIIDADB_NAME}"
).format(**config)

app = Celery('tasks', broker=broker)


@periodic_task(
    run_every=timedelta(
        seconds=config.get("DAEMON_INTERVALS_SUBMIT", DAEMON_INTERVALS_SUBMIT)
    )
)
def submitter():
    configure_logging(daemon=True, daemon_log_file=DAEMON_LOG_FILE)
    from aiida.daemon.execmanager import submit_jobs
    LOGGER.info('Checking for calculations to submit')
    set_daemon_timestamp(task_name='submitter', when='start')
    submit_jobs()
    set_daemon_timestamp(task_name='submitter', when='stop')


@periodic_task(
    run_every=timedelta(
        seconds=config.get("DAEMON_INTERVALS_UPDATE", DAEMON_INTERVALS_UPDATE)
    )
)
def updater():
    configure_logging(daemon=True, daemon_log_file=DAEMON_LOG_FILE)
    from aiida.daemon.execmanager import update_jobs
    LOGGER.info('Checking for calculations to update')
    set_daemon_timestamp(task_name='updater', when='start')
    update_jobs()
    set_daemon_timestamp(task_name='updater', when='stop')


@periodic_task(
    run_every=timedelta(
        seconds=config.get("DAEMON_INTERVALS_RETRIEVE", DAEMON_INTERVALS_RETRIEVE)
    )
)
def retriever():
    configure_logging(daemon=True, daemon_log_file=DAEMON_LOG_FILE)
    from aiida.daemon.execmanager import retrieve_jobs
    LOGGER.info('Checking for calculations to retrieve')
    set_daemon_timestamp(task_name='retriever', when='start')
    retrieve_jobs()
    set_daemon_timestamp(task_name='retriever', when='stop')


@periodic_task(
    run_every=timedelta(
        seconds=config.get("DAEMON_INTERVALS_WFSTEP", DAEMON_INTERVALS_WFSTEP)
    )
)
def workflow_stepper():  # daemon for legacy workflow
    configure_logging(daemon=True, daemon_log_file=DAEMON_LOG_FILE)
    from aiida.daemon.workflowmanager import execute_steps
    LOGGER.info('Checking for workflows to manage')
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
        LOGGER.info('running execute_steps')
        execute_steps()
        set_daemon_timestamp(task_name='workflow', when='stop')
    else:
        LOGGER.info('execute_steps already running')


def manual_tick_all():
    from aiida.daemon.execmanager import submit_jobs, update_jobs, retrieve_jobs
    from aiida.daemon.workflowmanager import execute_steps

    submit_jobs()
    update_jobs()
    retrieve_jobs()
    execute_steps()  # legacy workflows
