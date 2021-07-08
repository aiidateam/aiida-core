# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=too-many-public-methods,redefined-outer-name
"""Test for the `CalcJob` process sub class."""
from copy import deepcopy
from functools import partial
import io
import os
from unittest.mock import patch

import pytest

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.common import exceptions, LinkType, CalcJobState, StashMode
from aiida.engine import launch, CalcJob, Process, ExitCode
from aiida.engine.processes.ports import PortNamespace
from aiida.engine.processes.calcjobs.calcjob import validate_stash_options
from aiida.plugins import CalculationFactory

ArithmeticAddCalculation = CalculationFactory('arithmetic.add')  # pylint: disable=invalid-name


def raise_exception(exception):
    """Raise an exception of the specified class.

    :param exception: exception class to raise
    """
    raise exception()


@pytest.mark.requires_rmq
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


@pytest.mark.requires_rmq
class TestCalcJob(AiidaTestCase):
    """Test for the `CalcJob` process sub class."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.computer.configure()  # pylint: disable=no-member
        cls.remote_code = orm.Code(remote_computer_exec=(cls.computer, '/bin/bash')).store()
        cls.local_code = orm.Code(local_executable='bash', files=['/bin/bash']).store()
        cls.inputs = {'x': orm.Int(1), 'y': orm.Int(2), 'metadata': {'options': {}}}

    def instantiate_process(self, state=CalcJobState.PARSING):
        """Instantiate a process with default inputs and return the `Process` instance."""
        from aiida.engine.utils import instantiate_process
        from aiida.manage.manager import get_manager

        inputs = deepcopy(self.inputs)
        inputs['code'] = self.remote_code

        manager = get_manager()
        runner = manager.get_runner()

        process_class = CalculationFactory('arithmetic.add')
        process = instantiate_process(runner, process_class, **inputs)
        process.node.set_state(state)

        return process

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

        with self.assertRaises(ValueError):
            ArithmeticAddCalculation(inputs=inputs)

    def test_remote_code_set_computer_explicit(self):
        """Test launching a `CalcJob` with a remote code *with* explicitly defining a computer.

        This should work as long as the explicitly defined computer is the same as the one configured for the `code`
        input. If this is not the case, it should raise.
        """
        inputs = deepcopy(self.inputs)
        inputs['code'] = self.remote_code

        # Setting explicitly a computer that is not the same as that of the `code` should raise
        with self.assertRaises(ValueError):
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

        with self.assertRaises(ValueError):
            ArithmeticAddCalculation(inputs=inputs)

    def test_invalid_parser_name(self):
        """Passing an invalid parser name should already stop during input validation."""
        inputs = deepcopy(self.inputs)
        inputs['code'] = self.remote_code
        inputs['metadata']['options']['parser_name'] = 'invalid_parser'

        with self.assertRaises(ValueError):
            ArithmeticAddCalculation(inputs=inputs)

    def test_invalid_resources(self):
        """Passing invalid resources should already stop during input validation."""
        inputs = deepcopy(self.inputs)
        inputs['code'] = self.remote_code
        inputs['metadata']['options']['resources'] = {'num_machines': 'invalid_type'}

        with self.assertRaises(ValueError):
            ArithmeticAddCalculation(inputs=inputs)

    def test_par_env_resources_computer(self):
        """Test launching a `CalcJob` an a computer with a scheduler using `ParEnvJobResource` as resources.

        Even though the computer defines a default number of MPI procs per machine, it should not raise when the
        scheduler that is defined does not actually support it, for example SGE or LSF.
        """
        inputs = deepcopy(self.inputs)
        computer = orm.Computer('sge_computer', 'localhost', 'desc', 'local', 'sge').store()
        computer.set_default_mpiprocs_per_machine(1)

        inputs['code'] = orm.Code(remote_computer_exec=(computer, '/bin/bash')).store()
        inputs['metadata']['options']['resources'] = {'parallel_env': 'environment', 'tot_num_mpiprocs': 10}

        # Just checking that instantiating does not raise, meaning the inputs were valid
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

    def test_parse_no_retrieved_folder(self):
        """Test the `CalcJob.parse` method when there is no retrieved folder."""
        process = self.instantiate_process()
        exit_code = process.parse()
        assert exit_code == process.exit_codes.ERROR_NO_RETRIEVED_FOLDER

    def test_parse_retrieved_folder(self):
        """Test the `CalcJob.parse` method when there is a retrieved folder."""
        process = self.instantiate_process()
        retrieved = orm.FolderData().store()
        retrieved.add_incoming(process.node, link_label='retrieved', link_type=LinkType.CREATE)
        exit_code = process.parse()

        # The following exit code is specific to the `ArithmeticAddCalculation` we are testing here and is returned
        # because the retrieved folder does not contain the output file it expects
        assert exit_code == process.exit_codes.ERROR_READING_OUTPUT_FILE


@pytest.fixture
def generate_process(aiida_local_code_factory):
    """Instantiate a process with default inputs and return the `Process` instance."""
    from aiida.engine.utils import instantiate_process
    from aiida.manage.manager import get_manager

    def _generate_process(inputs=None):

        base_inputs = {
            'code': aiida_local_code_factory('arithmetic.add', '/bin/bash'),
            'x': orm.Int(1),
            'y': orm.Int(2),
            'metadata': {
                'options': {}
            }
        }

        if inputs is not None:
            base_inputs = {**base_inputs, **inputs}

        manager = get_manager()
        runner = manager.get_runner()

        process_class = CalculationFactory('arithmetic.add')
        process = instantiate_process(runner, process_class, **base_inputs)
        process.node.set_state(CalcJobState.PARSING)

        return process

    return _generate_process


@pytest.mark.requires_rmq
@pytest.mark.usefixtures('clear_database_before_test', 'override_logging')
def test_parse_insufficient_data(generate_process):
    """Test the scheduler output parsing logic in `CalcJob.parse`.

    Here we check explicitly that the parsing does not except even if the required information is not available.
    """
    process = generate_process()

    retrieved = orm.FolderData().store()
    retrieved.add_incoming(process.node, link_label='retrieved', link_type=LinkType.CREATE)
    process.parse()

    filename_stderr = process.node.get_option('scheduler_stderr')
    filename_stdout = process.node.get_option('scheduler_stdout')

    # The scheduler parsing requires three resources of information, the `detailed_job_info` dictionary which is
    # stored as an attribute on the calculation job node and the output of the stdout and stderr which are both
    # stored in the repository. In this test, we haven't created these on purpose. This should not except the
    # process but should log a warning, so here we check that those expected warnings are attached to the node
    logs = [log.message for log in orm.Log.objects.get_logs_for(process.node)]
    expected_logs = [
        'could not parse scheduler output: the `detailed_job_info` attribute is missing',
        f'could not parse scheduler output: the `{filename_stderr}` file is missing',
        f'could not parse scheduler output: the `{filename_stdout}` file is missing'
    ]

    for log in expected_logs:
        assert log in logs


@pytest.mark.requires_rmq
@pytest.mark.usefixtures('clear_database_before_test', 'override_logging')
def test_parse_non_zero_retval(generate_process):
    """Test the scheduler output parsing logic in `CalcJob.parse`.

    This is testing the case where the `detailed_job_info` is incomplete because the call failed. This is checked
    through the return value that is stored within the attribute dictionary.
    """
    process = generate_process()

    retrieved = orm.FolderData().store()
    retrieved.add_incoming(process.node, link_label='retrieved', link_type=LinkType.CREATE)

    process.node.set_attribute('detailed_job_info', {'retval': 1, 'stderr': 'accounting disabled', 'stdout': ''})
    process.parse()

    logs = [log.message for log in orm.Log.objects.get_logs_for(process.node)]
    assert 'could not parse scheduler output: return value of `detailed_job_info` is non-zero' in logs


@pytest.mark.requires_rmq
@pytest.mark.usefixtures('clear_database_before_test', 'override_logging')
def test_parse_not_implemented(generate_process):
    """Test the scheduler output parsing logic in `CalcJob.parse`.

    Here we check explicitly that the parsing does not except even if the scheduler does not implement the method.
    """
    process = generate_process()

    retrieved = orm.FolderData()
    retrieved.add_incoming(process.node, link_label='retrieved', link_type=LinkType.CREATE)

    process.node.set_attribute('detailed_job_info', {})

    filename_stderr = process.node.get_option('scheduler_stderr')
    filename_stdout = process.node.get_option('scheduler_stdout')

    retrieved.put_object_from_filelike(io.BytesIO(b'\n'), filename_stderr)
    retrieved.put_object_from_filelike(io.BytesIO(b'\n'), filename_stdout)
    retrieved.store()

    process.parse()

    # The `DirectScheduler` at this point in time does not implement the `parse_output` method. Instead of raising
    # a warning message should be logged. We verify here that said message is present.
    logs = [log.message for log in orm.Log.objects.get_logs_for(process.node)]
    expected_logs = ['`DirectScheduler` does not implement scheduler output parsing']

    for log in expected_logs:
        assert log in logs


@pytest.mark.requires_rmq
@pytest.mark.usefixtures('clear_database_before_test', 'override_logging')
def test_parse_scheduler_excepted(generate_process, monkeypatch):
    """Test the scheduler output parsing logic in `CalcJob.parse`.

    Here we check explicitly the case where the `Scheduler.parse_output` method excepts
    """
    from aiida.schedulers.plugins.direct import DirectScheduler

    process = generate_process()

    retrieved = orm.FolderData()
    retrieved.add_incoming(process.node, link_label='retrieved', link_type=LinkType.CREATE)

    process.node.set_attribute('detailed_job_info', {})

    filename_stderr = process.node.get_option('scheduler_stderr')
    filename_stdout = process.node.get_option('scheduler_stdout')

    retrieved.put_object_from_filelike(io.BytesIO(b'\n'), filename_stderr)
    retrieved.put_object_from_filelike(io.BytesIO(b'\n'), filename_stdout)
    retrieved.store()

    msg = 'crash'

    def raise_exception(*args, **kwargs):
        raise RuntimeError(msg)

    # Monkeypatch the `DirectScheduler.parse_output` to raise an exception
    monkeypatch.setattr(DirectScheduler, 'parse_output', raise_exception)
    process.parse()
    logs = [log.message for log in orm.Log.objects.get_logs_for(process.node)]
    expected_logs = [f'the `parse_output` method of the scheduler excepted: {msg}']

    for log in expected_logs:
        assert log in logs


@pytest.mark.requires_rmq
@pytest.mark.parametrize(('exit_status_scheduler', 'exit_status_retrieved', 'final'), (
    (None, None, 0),
    (100, None, 100),
    (None, 400, 400),
    (100, 400, 400),
    (100, 0, 0),
))
@pytest.mark.usefixtures('clear_database_before_test')
def test_parse_exit_code_priority(
    exit_status_scheduler,
    exit_status_retrieved,
    final,
    generate_calc_job,
    fixture_sandbox,
    aiida_local_code_factory,
    monkeypatch,
):  # pylint: disable=too-many-arguments
    """Test the logic around exit codes in the `CalcJob.parse` method.

    The `parse` method will first call the `Scheduler.parse_output` method, which if implemented by the relevant
    scheduler plugin, will parse the scheduler output and potentially return an exit code. Next, the output parser
    plugin is called if defined in the inputs that can also optionally return an exit code. This test is designed
    to make sure the right logic is implemented in terms of which exit code should be dominant.

    Scheduler result | Retrieved result | Final result    | Scenario
    -----------------|------------------|-----------------|-----------------------------------------
    `None`           | `None`           | `ExitCode(0)`   | Neither parser found any problem
    `ExitCode(100)`  | `None`           | `ExitCode(100)` | Scheduler found issue, output parser does not override
    `None`           | `ExitCode(400)`  | `ExitCode(400)` | Only output parser found a problem
    `ExitCode(100)`  | `ExitCode(400)`  | `ExitCode(400)` | Scheduler found issue, but output parser overrides
                     |                  |                 | with a more specific error code
    `ExitCode(100)`  | `ExitCode(0)`    | `ExitCode(0)`   | Scheduler found issue but output parser overrides saying
                     |                  |                 | that despite that the calculation should be considered
                     |                  |                 | finished successfully.

    To test this, we just need to test the `CalcJob.parse` method and the easiest way is to simply mock the scheduler
    parser and output parser calls called `parse_scheduler_output` and `parse_retrieved_output`, respectively. We will
    just mock them by a simple method that returns `None` or an `ExitCode`. We then check that the final exit code
    returned by `CalcJob.parse` is the one we expect according to the table above.
    """
    from aiida.orm import Int

    def parse_scheduler_output(_, __):
        if exit_status_scheduler is not None:
            return ExitCode(exit_status_scheduler)

    def parse_retrieved_output(_, __):
        if exit_status_retrieved is not None:
            return ExitCode(exit_status_retrieved)

    monkeypatch.setattr(CalcJob, 'parse_scheduler_output', parse_scheduler_output)
    monkeypatch.setattr(CalcJob, 'parse_retrieved_output', parse_retrieved_output)

    inputs = {
        'code': aiida_local_code_factory('arithmetic.add', '/bin/bash'),
        'x': Int(1),
        'y': Int(2),
    }
    process = generate_calc_job(fixture_sandbox, 'arithmetic.add', inputs, return_process=True)
    retrieved = orm.FolderData().store()
    retrieved.add_incoming(process.node, link_label='retrieved', link_type=LinkType.CREATE)

    result = process.parse()
    assert isinstance(result, ExitCode)
    assert result.status == final


@pytest.mark.requires_rmq
@pytest.mark.usefixtures('clear_database_before_test')
def test_additional_retrieve_list(generate_process, fixture_sandbox):
    """Test the ``additional_retrieve_list`` option."""
    process = generate_process()
    process.presubmit(fixture_sandbox)
    retrieve_list = process.node.get_attribute('retrieve_list')

    # Keep reference of the base contents of the retrieve list.
    base_retrieve_list = retrieve_list

    # Test that the code works if no explicit additional retrieve list is specified
    assert len(retrieve_list) != 0
    assert isinstance(process.node.get_attribute('retrieve_list'), list)

    # Defining explicit additional retrieve list that is disjoint with the base retrieve list
    additional_retrieve_list = ['file.txt', 'folder/file.txt']
    process = generate_process({'metadata': {'options': {'additional_retrieve_list': additional_retrieve_list}}})
    process.presubmit(fixture_sandbox)
    retrieve_list = process.node.get_attribute('retrieve_list')

    # Check that the `retrieve_list` is a list and contains the union of the base and additional retrieve list
    assert isinstance(process.node.get_attribute('retrieve_list'), list)
    assert set(retrieve_list) == set(base_retrieve_list).union(set(additional_retrieve_list))

    # Defining explicit additional retrieve list with elements that overlap with `base_retrieve_list
    additional_retrieve_list = ['file.txt', 'folder/file.txt'] + base_retrieve_list
    process = generate_process({'metadata': {'options': {'additional_retrieve_list': additional_retrieve_list}}})
    process.presubmit(fixture_sandbox)
    retrieve_list = process.node.get_attribute('retrieve_list')

    # Check that the `retrieve_list` is a list and contains the union of the base and additional retrieve list
    assert isinstance(process.node.get_attribute('retrieve_list'), list)
    assert set(retrieve_list) == set(base_retrieve_list).union(set(additional_retrieve_list))

    # Test the validator
    with pytest.raises(ValueError, match=r'`additional_retrieve_list` should only contain relative filepaths.*'):
        process = generate_process({'metadata': {'options': {'additional_retrieve_list': [None]}}})

    with pytest.raises(ValueError, match=r'`additional_retrieve_list` should only contain relative filepaths.*'):
        process = generate_process({'metadata': {'options': {'additional_retrieve_list': ['/abs/path']}}})


@pytest.mark.usefixtures('clear_database_before_test')
@pytest.mark.parametrize(('stash_options', 'expected'), (
    ({
        'target_base': None
    }, '`metadata.options.stash.target_base` should be'),
    ({
        'target_base': 'relative/path'
    }, '`metadata.options.stash.target_base` should be'),
    ({
        'target_base': '/path'
    }, '`metadata.options.stash.source_list` should be'),
    ({
        'target_base': '/path',
        'source_list': ['/abspath']
    }, '`metadata.options.stash.source_list` should be'),
    ({
        'target_base': '/path',
        'source_list': ['rel/path'],
        'mode': 'test'
    }, '`metadata.options.stash.mode` should be'),
    ({
        'target_base': '/path',
        'source_list': ['rel/path']
    }, None),
    ({
        'target_base': '/path',
        'source_list': ['rel/path'],
        'mode': StashMode.COPY.value
    }, None),
))
def test_validate_stash_options(stash_options, expected):
    """Test the ``validate_stash_options`` function."""
    if expected is None:
        assert validate_stash_options(stash_options, None) is expected
    else:
        assert expected in validate_stash_options(stash_options, None)
