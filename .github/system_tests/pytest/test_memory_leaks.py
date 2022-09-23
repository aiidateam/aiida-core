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
from aiida import orm
from aiida.engine import processes, run_get_node
from aiida.plugins import CalculationFactory
from tests.utils import processes as test_processes  # pylint: disable=no-name-in-module,import-error
from tests.utils.memory import get_instances  # pylint: disable=no-name-in-module,import-error

ArithmeticAddCalculation = CalculationFactory('core.arithmetic.add')


def run_finished_ok(*args, **kwargs):
    """Convenience function to check that run worked fine."""
    _, node = run_get_node(*args, **kwargs)
    assert node.is_finished_ok, (node.exit_status, node.exit_message)


def test_leak_run_process():
    """Test whether running a dummy process leaks memory."""
    inputs = {'a': orm.Int(2), 'b': orm.Str('test')}
    run_finished_ok(test_processes.DummyProcess, **inputs)

    # check that no reference to the process is left in memory
    # some delay is necessary in order to allow for all callbacks to finish
    process_instances = get_instances(processes.Process, delay=0.2)
    assert not process_instances, f'Memory leak: process instances remain in memory: {process_instances}'


def test_leak_local_calcjob(aiida_local_code_factory):
    """Test whether running a local CalcJob leaks memory."""
    inputs = {'x': orm.Int(1), 'y': orm.Int(2), 'code': aiida_local_code_factory('core.arithmetic.add', '/bin/bash')}
    run_finished_ok(ArithmeticAddCalculation, **inputs)

    # check that no reference to the process is left in memory
    # some delay is necessary in order to allow for all callbacks to finish
    process_instances = get_instances(processes.Process, delay=0.2)
    assert not process_instances, f'Memory leak: process instances remain in memory: {process_instances}'


def test_leak_ssh_calcjob():
    """Test whether running a CalcJob over SSH leaks memory.

    Note: This relies on the 'slurm-ssh' computer being set up.
    """
    code = orm.InstalledCode(
        default_calc_job_plugin='core.arithmetic.add',
        computer=orm.load_computer('slurm-ssh'),
        filepath_executable='/bin/bash'
    )
    inputs = {'x': orm.Int(1), 'y': orm.Int(2), 'code': code}
    run_finished_ok(ArithmeticAddCalculation, **inputs)

    # check that no reference to the process is left in memory
    # some delay is necessary in order to allow for all callbacks to finish
    process_instances = get_instances(processes.Process, delay=0.2)
    assert not process_instances, f'Memory leak: process instances remain in memory: {process_instances}'
