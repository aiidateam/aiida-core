# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import logging
import time

import aiida.work.globals
import aiida.work.persistence
from aiida.orm.calculation.job import JobCalculation
from aiida.orm.mixins import Sealable
from aiida.orm.querybuilder import QueryBuilder
from aiida.work.job_processes import ContinueJobCalculation
from aiida.work.utils import CalculationHeartbeat
from plum.exceptions import LockError
from . import runners

_LOGGER = logging.getLogger(__name__)

import traceback
import aiida.work.persistence


def launch_pending_jobs(storage=None, loop=None):
    if storage is None:
        storage = aiida.work.globals.get_persistence()
    if loop is None:
        loop = runners.get_runner()

    executor = aiida.work.globals.get_thread_executor()
    for proc in _load_all_processes(storage, loop):
        if executor.has_process(proc.pid):
            # If already playing, skip
            continue

        try:
            storage.persist_process(proc)
            f = executor.play(proc)
        except LockError:
            pass
        except BaseException:
            _LOGGER.error("Failed to play process '{}':\n{}".format(
                proc.pid, traceback.format_exc()))


def _load_all_processes(storage, loop):
    procs = []
    for cp in storage.get_checkpoints():
        try:
            procs.append(loop.create(cp))
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
    storage = aiida.work.globals.get_persistence()
    executor = aiida.work.globals.get_thread_executor()
    for calc in get_all_pending_job_calculations():
        try:
            if executor.has_process(calc.pk):
                # If already playing, skip
                continue

            proc = ContinueJobCalculation(inputs={'_calc': calc})
            storage.persist_process(proc)
            f = executor.play(proc)
        except BaseException:
            _LOGGER.error("Failed to launch job '{}'\n{}".format(
                calc.pk, traceback.format_exc()))
        else:
            # Check if the process finished or was stopped early
            if not proc.has_finished():
                more_work = True


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
            'attributes': {'!has_key': Sealable.SEALED_KEY},
            'or': [
                {'attributes': {'!has_key': CalculationHeartbeat.HEARTBEAT_EXPIRES}},
                {'attributes.{}'.format(CalculationHeartbeat.HEARTBEAT_EXPIRES): {'<': time.time()}}
            ],
        },
    )

    return [_[0] for _ in q.all()]
