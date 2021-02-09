# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utilities for testing memory leakage."""
from tests.utils import processes as test_processes  # pylint: disable=no-name-in-module,import-error
from tests.utils.memory import get_instances  # pylint: disable=no-name-in-module,import-error
from aiida.engine import processes, run
from aiida.plugins import CalculationFactory
from aiida import orm

ArithmeticAddCalculation = CalculationFactory('arithmetic.add')


def test_leak_run_process():
    """Test whether running a dummy process leaks memory."""
    inputs = {'a': orm.Int(2), 'b': orm.Str('test')}
    run(test_processes.DummyProcess, **inputs)

    # check that no reference to the process is left in memory
    # some delay is necessary in order to allow for all callbacks to finish
    process_instances = get_instances(processes.Process, delay=0.2)
    assert not process_instances, f'Memory leak: process instances remain in memory: {process_instances}'


def test_leak_local_calcjob(aiida_local_code_factory):
    """Test whether running a local CalcJob leaks memory."""
    inputs = {'x': orm.Int(1), 'y': orm.Int(2), 'code': aiida_local_code_factory('arithmetic.add', '/usr/bin/diff')}
    run(ArithmeticAddCalculation, **inputs)

    # check that no reference to the process is left in memory
    # some delay is necessary in order to allow for all callbacks to finish
    process_instances = get_instances(processes.Process, delay=0.2)
    assert not process_instances, f'Memory leak: process instances remain in memory: {process_instances}'
