# -*- coding: utf-8 -*-
import logging
import time

from aiida.orm.querybuilder import QueryBuilder
from aiida.orm import load_node
from aiida.orm.calculation.job import JobCalculation
from aiida.work.legacy.job_process import ContinueJobCalculation
from aiida.work.util import CalculationHeartbeat
from aiida.work.process import load
import aiida.work.globals
import aiida.work.persistence
from plum.exceptions import LockError

_LOGGER = logging.getLogger(__name__)



def launch_pending_jobs(storage=None):
    if storage is None:
        storage = aiida.work.globals.get_persistence()

    procman = aiida.work.globals.get_process_manager()
    for proc in _load_all_processes(storage):
        try:
            storage.persist_process(proc)
            f = procman.start(proc)
        except LockError:
            pass


def _load_all_processes(storage):
    procs = []
    for cp in storage.load_all_checkpoints():
        try:
            procs.append(load(cp))
        except KeyboardInterrupt:
            raise
        except BaseException as exception:
            import traceback
            _LOGGER.warning("Failed to load process from checkpoint with "
                            "pid '{}'\n{}: {}".format(cp['pid'], exception.__class__.__name__, exception))
            _LOGGER.error(traceback.format_exc())
    return procs


def launch_all_pending_job_calculations():
    """
    Launch all JobCalculations that are not currently being processed
    """
    process_manager = aiida.work.globals.get_process_manager()
    for calc in get_all_pending_job_calculations():
        try:
            process_manager.launch(ContinueJobCalculation, inputs={'_calc': calc})
        except BaseException as e:
            _LOGGER.error("Failed to launch job '{}'\n{}: {}".format(
                calc, e.__class__.__name__, e.message))


def get_all_pending_job_calculations():
    """
    Get all JobCalculations that are in an active state but have no heartbeat

    :return: A list of those calculations
    :rtype: list
    """
    q = QueryBuilder()
    q.append(
        JobCalculation,
        filters={
            'state': {'in': ContinueJobCalculation.ACTIVE_CALC_STATES},
            'or': [
                {'attributes': {'!has_key': CalculationHeartbeat.HEARTBEAT_EXPIRES}},
                {'attributes.{}'.format(CalculationHeartbeat.HEARTBEAT_EXPIRES): {'<': time.time()}}
            ],
        },
    )

    return [_[0] for _ in q.all()]
