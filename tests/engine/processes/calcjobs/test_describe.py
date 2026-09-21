###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for working out what a calculation job would run, with nothing stored."""

from __future__ import annotations

from pathlib import Path

import pytest

from aiida import orm
from aiida.calculations.arithmetic.add import ArithmeticAddCalculation
from aiida.common.exceptions import InputValidationError
from aiida.common.folders import SandboxFolder
from aiida.engine.processes.calcjobs.calcjob import JobDescription


@pytest.fixture
def inputs(aiida_localhost):
    """Return what an `ArithmeticAddCalculation` takes, none of it stored."""
    code = orm.InstalledCode(computer=aiida_localhost, filepath_executable='/bin/bash')

    return {
        'code': code.store(),
        'x': orm.Int(2),
        'y': orm.Int(3),
        'metadata': {'options': {'resources': {'num_machines': 1}}},
    }


def test_a_calculation_says_what_it_would_run(inputs):
    """The description needs no node, so it can be worked out wherever the inputs are."""
    with SandboxFolder() as folder:
        described = ArithmeticAddCalculation.describe(inputs, folder, label='aiida-42')

        written = sorted(folder.get_content_list())

    assert isinstance(described, JobDescription)
    assert written == ['.aiida', '_aiidasubmit.sh', 'aiida.in']
    assert described.calc_info.codes_info[0].stdin_name == 'aiida.in'
    assert 'aiida.out' in described.retrieve_list


def test_what_the_job_is_called_is_given_rather_than_taken_from_a_pk(inputs):
    """A description belongs to no node, so the name of the job comes from the caller."""
    scheduled = orm.Computer(
        label='writes-a-job-name',
        hostname='localhost',
        transport_type='core.local',
        scheduler_type='core.slurm',
        workdir='/tmp',
    ).store()
    scheduled.set_default_mpiprocs_per_machine(1)
    inputs['code'] = orm.InstalledCode(computer=scheduled, filepath_executable='/bin/bash').store()

    with SandboxFolder() as folder:
        ArithmeticAddCalculation.describe(inputs, folder, label='the-name-i-chose')

        content = Path(folder.get_abs_path('_aiidasubmit.sh')).read_text()

    assert '--job-name="the-name-i-chose"' in content


def test_the_retrieve_lists_are_returned_rather_than_written_to_a_node(inputs):
    """They were set on the node, so a step that only brings files back has to be told them."""
    with SandboxFolder() as folder:
        described = ArithmeticAddCalculation.describe(inputs, folder)

    assert described.retrieve_list == ['aiida.out', '_scheduler-stdout.txt', '_scheduler-stderr.txt']
    assert described.retrieve_temporary_list == []


def test_the_code_is_checked_against_the_computer_it_would_run_on(inputs):
    """The codes used to be read off the node's links, which a description does not have."""
    other = orm.Computer(
        label='other',
        hostname='other',
        transport_type='core.local',
        scheduler_type='core.direct',
        workdir='/tmp',
    ).store()

    with SandboxFolder() as folder:
        with pytest.raises(InputValidationError, match='cannot run on computer'):
            ArithmeticAddCalculation.describe(inputs, folder, computer=other)


def test_a_run_describes_itself_the_same_way(aiida_code_installed):
    """`presubmit` is the node's half of the same work, so what it returns is what the description holds."""
    from aiida.engine import run_get_node

    code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash')
    _, node = run_get_node(ArithmeticAddCalculation, code=code, x=orm.Int(2), y=orm.Int(3))

    assert node.is_finished_ok, node.exit_message
    assert node.get_retrieve_list() == ['aiida.out', '_scheduler-stdout.txt', '_scheduler-stderr.txt']
