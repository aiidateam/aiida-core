###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utilities for testing memory leakage."""

import sys

import pytest

from aiida import orm
from aiida.engine import processes, run_get_node
from aiida.plugins import CalculationFactory
from tests.utils import processes as test_processes
from tests.utils.memory import get_instances

ArithmeticAddCalculation = CalculationFactory('core.arithmetic.add')


def run_finished_ok(*args, **kwargs):
    """Convenience function to check that run worked fine."""
    _, node = run_get_node(*args, **kwargs)
    assert node.is_finished_ok, (node.process_state, node.exit_code)


@pytest.fixture
def check_memory_leaks():
    """Check that no processes remain in memory after the test finishes.

    The fixture checks the current processes in memory before running the test which are ignored in the check after the
    test. This is to prevent the test failing because some other test in the suite failed to properly cleanup a process.
    """
    starting_processes = get_instances(processes.Process, delay=0.2)

    yield

    # Check that no reference to the process is left in memory. Some delay is necessary in order to allow for all
    # callbacks to finish.
    process_instances = set(get_instances(processes.Process, delay=0.2)).difference(set(starting_processes))
    assert not process_instances, f'Memory leak: process instances remain in memory: {process_instances}'


@pytest.mark.skipif(sys.version_info >= (3, 12), reason='Garbage collecting hangs on Python 3.12')
@pytest.mark.usefixtures('aiida_profile', 'check_memory_leaks')
def test_leak_run_process():
    """Test whether running a dummy process leaks memory."""
    inputs = {'a': orm.Int(2), 'b': orm.Str('test')}
    run_finished_ok(test_processes.DummyProcess, **inputs)


@pytest.mark.skipif(sys.version_info >= (3, 12), reason='Garbage collecting hangs on Python 3.12')
@pytest.mark.usefixtures('aiida_profile', 'check_memory_leaks')
def test_leak_local_calcjob(aiida_code_installed):
    """Test whether running a local CalcJob leaks memory."""
    inputs = {
        'x': orm.Int(1),
        'y': orm.Int(2),
        'code': aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash'),
    }
    run_finished_ok(ArithmeticAddCalculation, **inputs)


@pytest.mark.skipif(sys.version_info >= (3, 12), reason='Garbage collecting hangs on Python 3.12')
@pytest.mark.usefixtures('aiida_profile', 'check_memory_leaks')
def test_leak_ssh_calcjob(aiida_computer_ssh):
    """Test whether running a CalcJob over SSH leaks memory.

    Note: This relies on the localhost configuring an SSH server and allowing to connect to it from localhost.
    """
    computer = aiida_computer_ssh()

    # Ensure a connection can be opened before launching the calcjob or it will get stuck in the EBM.
    with computer.get_transport() as transport:
        assert transport.whoami()

    code = orm.InstalledCode(
        default_calc_job_plugin='core.arithmetic.add', computer=computer, filepath_executable='/bin/bash'
    )
    inputs = {'x': orm.Int(1), 'y': orm.Int(2), 'code': code}
    run_finished_ok(ArithmeticAddCalculation, **inputs)
