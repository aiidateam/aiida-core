# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=protected-access,too-many-locals,invalid-name,too-many-public-methods
"""Tests for `verdi calcjob`."""
import io

from click.testing import CliRunner
import pytest

from aiida import orm
from aiida.cmdline.commands import cmd_calcjob as command
from aiida.common.datastructures import CalcJobState
from aiida.common.links import LinkType
from aiida.engine import ProcessState
from aiida.orm.nodes.data.remote.base import RemoteData
from aiida.plugins import CalculationFactory
from aiida.plugins.entry_point import get_entry_point_string_from_class
from tests.utils.archives import import_test_archive


def get_result_lines(result):
    return [e for e in result.output.split('\n') if e]


class TestVerdiCalculation:
    """Tests for `verdi calcjob`."""

    @pytest.fixture(autouse=True)
    def init_profile(self, aiida_profile_clean, aiida_localhost):  # pylint: disable=unused-argument
        """Initialize the profile."""
        # pylint: disable=attribute-defined-outside-init

        self.computer = aiida_localhost
        self.code = orm.Code(remote_computer_exec=(self.computer, '/bin/true')).store()
        self.group = orm.Group(label='test_group').store()
        self.node = orm.Data().store()
        self.calcs = []

        process_class = CalculationFactory('core.templatereplacer')
        process_type = get_entry_point_string_from_class(process_class.__module__, process_class.__name__)

        # Create 5 CalcJobNodes (one for each CalculationState)
        for calculation_state in CalcJobState:

            calc = orm.CalcJobNode(computer=self.computer, process_type=process_type)
            calc.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
            calc.set_remote_workdir('/tmp/aiida/work')
            remote = RemoteData(remote_path='/tmp/aiida/work')
            remote.computer = calc.computer
            remote.add_incoming(calc, LinkType.CREATE, link_label='remote_folder')
            calc.store()
            remote.store()

            calc.set_process_state(ProcessState.RUNNING)
            self.calcs.append(calc)

            if calculation_state == CalcJobState.PARSING:
                self.KEY_ONE = 'key_one'
                self.KEY_TWO = 'key_two'
                self.VAL_ONE = 'val_one'
                self.VAL_TWO = 'val_two'

                output_parameters = orm.Dict(dict={
                    self.KEY_ONE: self.VAL_ONE,
                    self.KEY_TWO: self.VAL_TWO,
                }).store()

                output_parameters.add_incoming(calc, LinkType.CREATE, 'output_parameters')

                # Create shortcut for easy dereferencing
                self.result_job = calc

                # Add a single calc to a group
                self.group.add_nodes([calc])

        # Create a single failed CalcJobNode
        self.EXIT_STATUS = 100
        calc = orm.CalcJobNode(computer=self.computer)
        calc.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        calc.store()
        calc.set_exit_status(self.EXIT_STATUS)
        calc.set_process_state(ProcessState.FINISHED)
        calc.set_remote_workdir('/tmp/aiida/work')
        remote = RemoteData(remote_path='/tmp/aiida/work')
        remote.computer = calc.computer
        remote.add_incoming(calc, LinkType.CREATE, link_label='remote_folder')
        remote.store()
        self.calcs.append(calc)

        # Load the fixture containing a single ArithmeticAddCalculation node
        import_test_archive('calcjob/arithmetic.add.aiida')

        # Get the imported ArithmeticAddCalculation node
        ArithmeticAddCalculation = CalculationFactory('core.arithmetic.add')
        calculations = orm.QueryBuilder().append(ArithmeticAddCalculation).all()[0]
        self.arithmetic_job = calculations[0]

        self.cli_runner = CliRunner()

    def test_calcjob_res(self):
        """Test verdi calcjob res"""
        options = [str(self.result_job.uuid)]
        result = self.cli_runner.invoke(command.calcjob_res, options)
        assert result.exception is None, result.output
        assert self.KEY_ONE in result.output
        assert self.VAL_ONE in result.output
        assert self.KEY_TWO in result.output
        assert self.VAL_TWO in result.output

        for flag in ['-k', '--keys']:
            options = [flag, self.KEY_ONE, '--', str(self.result_job.uuid)]
            result = self.cli_runner.invoke(command.calcjob_res, options)
            assert result.exception is None, result.output
            assert self.KEY_ONE in result.output
            assert self.VAL_ONE in result.output
            assert self.KEY_TWO not in result.output
            assert self.VAL_TWO not in result.output

    def test_calcjob_inputls(self):
        """Test verdi calcjob inputls"""
        options = []
        result = self.cli_runner.invoke(command.calcjob_inputls, options)
        assert result.exception is not None

        options = [self.arithmetic_job.uuid]
        result = self.cli_runner.invoke(command.calcjob_inputls, options)
        assert result.exception is None, result.output
        # There is also an additional fourth file added by hand to test retrieval of binary content
        # see comments in test_calcjob_inputcat
        assert len(get_result_lines(result)) == 4
        assert '.aiida' in get_result_lines(result)
        assert 'aiida.in' in get_result_lines(result)
        assert '_aiidasubmit.sh' in get_result_lines(result)
        assert 'in_gzipped_data' in get_result_lines(result)

        options = [self.arithmetic_job.uuid, '.aiida']
        result = self.cli_runner.invoke(command.calcjob_inputls, options)
        assert result.exception is None, result.output
        assert len(get_result_lines(result)) == 2
        assert 'calcinfo.json' in get_result_lines(result)
        assert 'job_tmpl.json' in get_result_lines(result)

        options = [self.arithmetic_job.uuid, 'non-existing-folder']
        result = self.cli_runner.invoke(command.calcjob_inputls, options)
        assert result.exception is not None
        assert 'does not exist for the given node' in result.output

    def test_calcjob_outputls(self):
        """Test verdi calcjob outputls"""
        options = []
        result = self.cli_runner.invoke(command.calcjob_outputls, options)
        assert result.exception is not None, result.output

        options = [self.arithmetic_job.uuid]
        result = self.cli_runner.invoke(command.calcjob_outputls, options)
        assert result.exception is None, result.output
        # There is also an additional fourth file added by hand to test retrieval of binary content
        # see comments in test_calcjob_outputcat
        assert len(get_result_lines(result)) == 4
        assert '_scheduler-stderr.txt' in get_result_lines(result)
        assert '_scheduler-stdout.txt' in get_result_lines(result)
        assert 'aiida.out' in get_result_lines(result)
        assert 'gzipped_data' in get_result_lines(result)

        options = [self.arithmetic_job.uuid, 'non-existing-folder']
        result = self.cli_runner.invoke(command.calcjob_inputls, options)
        assert result.exception is not None
        assert 'does not exist for the given node' in result.output

    def test_calcjob_inputcat(self):
        """Test verdi calcjob inputcat"""

        options = []
        result = self.cli_runner.invoke(command.calcjob_inputcat, options)
        assert result.exception is not None, result.output

        options = [self.arithmetic_job.uuid]
        result = self.cli_runner.invoke(command.calcjob_inputcat, options)
        assert result.exception is None, result.output
        assert len(get_result_lines(result)) == 1
        assert get_result_lines(result)[0] == '2 3'

        options = [self.arithmetic_job.uuid, 'aiida.in']
        result = self.cli_runner.invoke(command.calcjob_inputcat, options)
        assert result.exception is None, result.output
        assert len(get_result_lines(result)) == 1
        assert get_result_lines(result)[0] == '2 3'

        # Test cat binary files
        self.arithmetic_job._repository.put_object_from_filelike(io.BytesIO(b'COMPRESS'), 'aiida.in')
        self.arithmetic_job._update_repository_metadata()

        options = [self.arithmetic_job.uuid, 'aiida.in']
        result = self.cli_runner.invoke(command.calcjob_inputcat, options)
        assert result.stdout_bytes == b'COMPRESS'

        # Restore the file
        self.arithmetic_job._repository.put_object_from_filelike(io.BytesIO(b'2 3\n'), 'aiida.in')
        self.arithmetic_job._update_repository_metadata()

    def test_calcjob_outputcat(self):
        """Test verdi calcjob outputcat"""

        options = []
        result = self.cli_runner.invoke(command.calcjob_outputcat, options)
        assert result.exception is not None

        options = [self.arithmetic_job.uuid]
        result = self.cli_runner.invoke(command.calcjob_outputcat, options)
        assert result.exception is None, result.output
        assert len(get_result_lines(result)) == 1
        assert get_result_lines(result)[0] == '5'

        options = [self.arithmetic_job.uuid, 'aiida.out']
        result = self.cli_runner.invoke(command.calcjob_outputcat, options)
        assert result.exception is None, result.output
        assert len(get_result_lines(result)) == 1
        assert get_result_lines(result)[0] == '5'

        # Test cat binary files
        retrieved = self.arithmetic_job.outputs.retrieved
        retrieved._repository.put_object_from_filelike(io.BytesIO(b'COMPRESS'), 'aiida.out')
        retrieved._update_repository_metadata()

        options = [self.arithmetic_job.uuid, 'aiida.out']
        result = self.cli_runner.invoke(command.calcjob_outputcat, options)
        assert result.stdout_bytes == b'COMPRESS'

        # Restore the file
        retrieved._repository.put_object_from_filelike(io.BytesIO(b'5\n'), 'aiida.out')
        retrieved._update_repository_metadata()

    def test_calcjob_cleanworkdir(self):
        """Test verdi calcjob cleanworkdir"""

        # Specifying no filtering options and no explicit calcjobs should exit with non-zero status
        options = []
        result = self.cli_runner.invoke(command.calcjob_cleanworkdir, options)
        assert result.exception is not None

        # Without the force flag it should fail
        options = [str(self.result_job.uuid)]
        result = self.cli_runner.invoke(command.calcjob_cleanworkdir, options)
        assert result.exception is not None

        # With force flag we should find one calcjob
        options = ['-f', str(self.result_job.uuid)]
        result = self.cli_runner.invoke(command.calcjob_cleanworkdir, options)
        assert result.exception is None, result.output

        # Do it again should fail as the calcjob has been cleaned
        options = ['-f', str(self.result_job.uuid)]
        result = self.cli_runner.invoke(command.calcjob_cleanworkdir, options)
        assert result.exception is not None, result.output

        # The flag should have been set
        assert self.result_job.outputs.remote_folder.get_extra('cleaned') is True

        # Check applying both p and o filters
        for flag_p in ['-p', '--past-days']:
            for flag_o in ['-o', '--older-than']:
                options = [flag_p, '5', flag_o, '1', '-f']
                result = self.cli_runner.invoke(command.calcjob_cleanworkdir, options)
                # This should fail - the node was just created in the test
                assert result.exception is not None

                options = [flag_p, '5', flag_o, '0', '-f']
                result = self.cli_runner.invoke(command.calcjob_cleanworkdir, options)
                # This should pass fine
                assert result.exception is None
                self.result_job.outputs.remote_folder.delete_extra('cleaned')

                options = [flag_p, '0', flag_o, '0', '-f']
                result = self.cli_runner.invoke(command.calcjob_cleanworkdir, options)
                # This should not pass
                assert result.exception is not None

        # Should fail because the exit code is not 999 - using the failed job for testing
        options = [str(self.calcs[-1].uuid), '-E', '999', '-f']
        result = self.cli_runner.invoke(command.calcjob_cleanworkdir, options)
        assert result.exception is not None

        # Should be fine because the exit code is 100
        self.calcs[-1].outputs.remote_folder.set_extra('cleaned', False)
        options = [str(self.calcs[-1].uuid), '-E', '100', '-f']
        result = self.cli_runner.invoke(command.calcjob_cleanworkdir, options)
        assert result.exception is None

    def test_calcjob_inoutputcat_old(self):
        """Test most recent process class / plug-in can be successfully used to find filenames"""

        # Import old archive of ArithmeticAddCalculation
        import_test_archive('calcjob/arithmetic.add_old.aiida')
        ArithmeticAddCalculation = CalculationFactory('core.arithmetic.add')
        calculations = orm.QueryBuilder().append(ArithmeticAddCalculation).all()
        add_job = None
        for job in calculations:
            if job[0].uuid == self.arithmetic_job.uuid:
                continue

            add_job = job[0]
            break
        assert add_job
        # Make sure add_job does not specify options 'input_filename' and 'output_filename'
        assert add_job.get_option('input_filename') is None, f"'input_filename' should not be an option for {add_job}"
        assert add_job.get_option('output_filename') is None, f"'output_filename' should not be an option for {add_job}"

        # Run `verdi calcjob inputcat add_job`
        options = [add_job.uuid]
        result = self.cli_runner.invoke(command.calcjob_inputcat, options)
        assert result.exception is None, result.output
        assert len(get_result_lines(result)) == 1
        assert get_result_lines(result)[0] == '2 3'

        # Run `verdi calcjob outputcat add_job`
        options = [add_job.uuid]
        result = self.cli_runner.invoke(command.calcjob_outputcat, options)
        assert result.exception is None, result.output
        assert len(get_result_lines(result)) == 1
        assert get_result_lines(result)[0] == '5'
