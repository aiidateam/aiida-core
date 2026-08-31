###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Fixtures for the tests of the calculation job plugins."""

from __future__ import annotations

import pathlib
import shutil
import typing as t

import pytest

from aiida.common.datastructures import CalcInfo
from aiida.common.folders import Folder
from aiida.engine import CalcJob


@pytest.fixture
def generate_shell_code(aiida_computer_local, aiida_code_installed):
    """Return a factory for an ``InstalledCode`` that runs a command through the ``core.shell`` plugin."""
    default_command = shutil.which('true')
    assert default_command is not None, 'The `true` command must be available on the system for the tests to run.'

    def factory(command: str = default_command, computer_label: str = 'localhost', label: str | None = None):
        """Return a code for ``command``, resolving it to an absolute path on the computer."""
        computer = aiida_computer_local(label=computer_label)

        with computer.get_transport() as transport:
            status, stdout, stderr = transport.exec_command_wait(f'which {command}')

            if status != 0:
                raise ValueError(f'failed to determine the absolute path of the command on the computer: {stderr}')

        return aiida_code_installed(
            label=label,
            computer=computer,
            filepath_executable=stdout.strip(),
            default_calc_job_plugin='core.shell',
        )

    return factory


@pytest.fixture
def generate_shell_calc_job(tmp_path_factory):
    """Return a factory that instantiates a ``CalcJob`` and prepares its input files.

    Unlike the ``generate_calc_job`` fixture in the root conftest, this one creates the temporary folder itself and
    returns it, and can run the full ``presubmit`` so that scheduler-written files are present too.
    """

    def factory(
        entry_point_name: str,
        inputs: dict[str, t.Any] | None = None,
        return_process: bool = False,
        presubmit: bool = False,
    ) -> tuple[pathlib.Path, CalcInfo] | CalcJob:
        from aiida.engine.utils import instantiate_process
        from aiida.manage import get_manager
        from aiida.plugins import CalculationFactory

        tmp_path = tmp_path_factory.mktemp('calc_job_submit_dir')
        runner = get_manager().get_runner()

        process_class: type[CalcJob] = CalculationFactory(entry_point_name)  # type: ignore[assignment]
        process: CalcJob = instantiate_process(runner, process_class, **inputs or {})  # type: ignore[assignment]

        if presubmit:
            calc_info = process.presubmit(Folder(tmp_path))
        else:
            calc_info = process.prepare_for_submission(Folder(tmp_path))

        if return_process:
            return process

        return tmp_path, calc_info

    return factory
