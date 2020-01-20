# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test for the `CalcJob` process sub class."""
from copy import deepcopy
from functools import partial
import os
from unittest.mock import patch

import pytest

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.common import exceptions
from aiida.engine import launch, CalcJob, Process
from aiida.engine.processes.ports import PortNamespace
from aiida.plugins import CalculationFactory

ArithmeticAddCalculation = CalculationFactory('arithmetic.add')  # pylint: disable=invalid-name


def raise_exception(exception):
    """Raise an exception of the specified class.

    :param exception: exception class to raise
    """
    raise exception()


class FileCalcJob(CalcJob):
    """Example `CalcJob` implementation to test the `provenance_exclude_list` functionality.

    The content of the input `files` will be copied to the `folder` sandbox, but also added to the attribute
    `provenance_exclude_list` of the `CalcInfo` which should instruct the engine to copy the files to the remote work
    directory but NOT to the repository of the `CalcJobNode`.
    """

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('settings', valid_type=orm.Dict)
        spec.input_namespace('files', valid_type=orm.SinglefileData, dynamic=True)

    def prepare_for_submission(self, folder):
        from aiida.common.datastructures import CalcInfo, CodeInfo

        for key, node in self.inputs.files.items():
            filepath = key.replace('_', os.sep)
            dirname = os.path.dirname(filepath)
            basename = os.path.basename(filepath)
            with node.open(mode='rb') as source:
                if dirname:
                    subfolder = folder.get_subfolder(dirname, create=True)
                    subfolder.create_file_from_filelike(source, basename)
                else:
                    folder.create_file_from_filelike(source, filepath)

        codeinfo = CodeInfo()
        codeinfo.code_uuid = self.inputs.code.uuid

        calcinfo = CalcInfo()
        calcinfo.codes_info = [codeinfo]
        calcinfo.provenance_exclude_list = self.inputs.settings.get_attribute('provenance_exclude_list')
        return calcinfo


class TestCalcJob(AiidaTestCase):
    """Test for the `CalcJob` process sub class."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        import aiida
        files = [os.path.join(os.path.dirname(aiida.__file__), os.pardir, '.ci', 'add.sh')]
        cls.computer.configure()  # pylint: disable=no-member
        cls.remote_code = orm.Code(remote_computer_exec=(cls.computer, '/bin/true')).store()
        cls.local_code = orm.Code(local_executable='add.sh', files=files).store()
        cls.inputs = {
            'x': orm.Int(1),
            'y': orm.Int(2),
            'metadata': {
                'options': {
                    'resources': {
                        'num_machines': 1,
                        'num_mpiprocs_per_machine': 1
                    },
                }
            }
        }

    def setUp(self):
        super().setUp()
        self.assertIsNone(Process.current())

    def tearDown(self):
        super().tearDown()
        self.assertIsNone(Process.current())

    def test_run_base_class(self):
        """Verify that it is impossible to run, submit or instantiate a base `CalcJob` class."""
        with self.assertRaises(exceptions.InvalidOperation):
            CalcJob()

        with self.assertRaises(exceptions.InvalidOperation):
            launch.run(CalcJob)

        with self.assertRaises(exceptions.InvalidOperation):
            launch.run_get_node(CalcJob)

        with self.assertRaises(exceptions.InvalidOperation):
            launch.run_get_pk(CalcJob)

        with self.assertRaises(exceptions.InvalidOperation):
            launch.submit(CalcJob)

    def test_define_not_calling_super(self):
        """A `CalcJob` that does not call super in `define` classmethod should raise."""

        class IncompleteDefineCalcJob(CalcJob):
            """Test class with incomplete define method"""

            @classmethod
            def define(cls, spec):
                pass

            def prepare_for_submission(self, folder):
                pass

        with self.assertRaises(AssertionError):
            launch.run(IncompleteDefineCalcJob)

    def test_spec_options_property(self):
        """`CalcJob.spec_options` should return the options port namespace of its spec."""
        self.assertIsInstance(CalcJob.spec_options, PortNamespace)
        self.assertEqual(CalcJob.spec_options, CalcJob.spec().inputs['metadata']['options'])

    def test_invalid_options_type(self):
        """Verify that passing an invalid type to `metadata.options` raises a `TypeError`."""

        class SimpleCalcJob(CalcJob):
            """Simple `CalcJob` implementation"""

            @classmethod
            def define(cls, spec):
                super().define(spec)

            def prepare_for_submission(self, folder):
                pass

        # The `metadata.options` input expects a plain dict and not a node `Dict`
        with self.assertRaises(TypeError):
            launch.run(SimpleCalcJob, code=self.remote_code, metadata={'options': orm.Dict(dict={'a': 1})})

    def test_remote_code_set_computer_implicit(self):
        """Test launching a `CalcJob` with a remote code *with* explicitly defining a computer.

        This should work, because the `computer` should be retrieved from the `code` and automatically set for the
        process by the engine itself.
        """
        inputs = deepcopy(self.inputs)
        inputs['code'] = self.remote_code

        process = ArithmeticAddCalculation(inputs=inputs)
        self.assertTrue(process.node.is_stored)
        self.assertEqual(process.node.computer.uuid, self.remote_code.computer.uuid)

    def test_remote_code_unstored_computer(self):
        """Test launching a `CalcJob` with an unstored computer which should raise."""
        inputs = deepcopy(self.inputs)
        inputs['code'] = self.remote_code
        inputs['metadata']['computer'] = orm.Computer('different', 'localhost', 'desc', 'local', 'direct')

        with self.assertRaises(exceptions.InputValidationError):
            ArithmeticAddCalculation(inputs=inputs)

    def test_remote_code_set_computer_explicit(self):
        """Test launching a `CalcJob` with a remote code *with* explicitly defining a computer.

        This should work as long as the explicitly defined computer is the same as the one configured for the `code`
        input. If this is not the case, it should raise.
        """
        inputs = deepcopy(self.inputs)
        inputs['code'] = self.remote_code

        # Setting explicitly a computer that is not the same as that of the `code` should raise
        with self.assertRaises(exceptions.InputValidationError):
            inputs['metadata']['computer'] = orm.Computer('different', 'localhost', 'desc', 'local', 'direct').store()
            process = ArithmeticAddCalculation(inputs=inputs)

        # Setting the same computer as that of the `code` effectively accomplishes nothing but should be fine
        inputs['metadata']['computer'] = self.remote_code.computer
        process = ArithmeticAddCalculation(inputs=inputs)
        self.assertTrue(process.node.is_stored)
        self.assertEqual(process.node.computer.uuid, self.remote_code.computer.uuid)

    def test_local_code_set_computer(self):
        """Test launching a `CalcJob` with a local code *with* explicitly defining a computer, which should work."""
        inputs = deepcopy(self.inputs)
        inputs['code'] = self.local_code
        inputs['metadata']['computer'] = self.computer

        process = ArithmeticAddCalculation(inputs=inputs)
        self.assertTrue(process.node.is_stored)
        self.assertEqual(process.node.computer.uuid, self.computer.uuid)  # pylint: disable=no-member

    def test_local_code_no_computer(self):
        """Test launching a `CalcJob` with a local code *without* explicitly defining a computer, which should raise."""
        inputs = deepcopy(self.inputs)
        inputs['code'] = self.local_code

        with self.assertRaises(exceptions.InputValidationError):
            ArithmeticAddCalculation(inputs=inputs)

    def test_invalid_parser_name(self):
        """Passing an invalid parser name should already stop during input validation."""
        inputs = deepcopy(self.inputs)
        inputs['code'] = self.remote_code
        inputs['metadata']['options']['parser_name'] = 'invalid_parser'

        with self.assertRaises(exceptions.InputValidationError):
            ArithmeticAddCalculation(inputs=inputs)

    def test_invalid_resources(self):
        """Passing invalid resources should already stop during input validation."""
        inputs = deepcopy(self.inputs)
        inputs['code'] = self.remote_code
        inputs['metadata']['options']['resources'].pop('num_machines')

        with self.assertRaises(exceptions.InputValidationError):
            ArithmeticAddCalculation(inputs=inputs)

    @pytest.mark.timeout(5)
    @patch.object(CalcJob, 'presubmit', partial(raise_exception, exceptions.InputValidationError))
    def test_exception_presubmit(self):
        """Test that an exception in the presubmit circumvents the exponential backoff and just excepts the process.

        The `presubmit` call of the `CalcJob` is now called in `aiida.engine.processes.calcjobs.tasks.task_upload_job`
        which is wrapped in the exponential backoff mechanism. The latter was introduced to recover from transient
        problems such as connection problems during the actual upload to a remote machine. However, it should not catch
        exceptions from the `presubmit` call which are not actually transient and thus not automatically recoverable. In
        this case the process should simply except. Here we test this by mocking the presubmit to raise an exception and
        check that it is bubbled up and the process does not end up in a paused state.
        """
        from aiida.engine.processes.calcjobs.tasks import PreSubmitException

        with self.assertRaises(PreSubmitException) as context:
            launch.run(ArithmeticAddCalculation, code=self.remote_code, **self.inputs)

        self.assertIn('exception occurred in presubmit call', str(context.exception))

    def test_run_local_code(self):
        """Run a dry-run with local code."""
        inputs = deepcopy(self.inputs)
        inputs['code'] = self.local_code
        inputs['metadata']['computer'] = self.computer
        inputs['metadata']['dry_run'] = True

        # The following will run `upload_calculation` which will test that uploading files works correctly
        _, node = launch.run_get_node(ArithmeticAddCalculation, **inputs)
        uploaded_files = os.listdir(node.dry_run_info['folder'])

        # Since the repository will only contain files on the top-level due to `Code.set_files` we only check those
        for filename in self.local_code.list_object_names():
            self.assertTrue(filename in uploaded_files)

    def test_provenance_exclude_list(self):
        """Test the functionality of the `CalcInfo.provenance_exclude_list` attribute."""
        import tempfile

        code = orm.Code(input_plugin_name='arithmetic.add', remote_computer_exec=[self.computer, '/bin/true']).store()

        with tempfile.NamedTemporaryFile('w+') as handle:
            handle.write('dummy_content')
            handle.flush()
            file_one = orm.SinglefileData(file=handle.name)

        with tempfile.NamedTemporaryFile('w+') as handle:
            handle.write('dummy_content')
            handle.flush()
            file_two = orm.SinglefileData(file=handle.name)

        inputs = {
            'code': code,
            'files': {
                # Note the `FileCalcJob` will turn underscores in the key into forward slashes making a nested hierarchy
                'base_a_sub_one': file_one,
                'base_b_two': file_two,
            },
            'settings': orm.Dict(dict={'provenance_exclude_list': ['base/a/sub/one']}),
            'metadata': {
                'dry_run': True,
                'options': {
                    'resources': {
                        'num_machines': 1,
                        'num_mpiprocs_per_machine': 1
                    }
                }
            }
        }

        # We perform a `dry_run` because the calculation cannot actually run, however, the contents will still be
        # written to the node's repository so we can check it contains the expected contents.
        _, node = launch.run_get_node(FileCalcJob, **inputs)

        self.assertIn('folder', node.dry_run_info)

        # Verify that the folder (representing the node's repository) indeed do not contain the input files. Note,
        # however, that the directory hierarchy should be there, albeit empty
        self.assertIn('base', node.list_object_names())
        self.assertEqual(sorted(['b']), sorted(node.list_object_names(os.path.join('base'))))
        self.assertEqual(['two'], node.list_object_names(os.path.join('base', 'b')))
