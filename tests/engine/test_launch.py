###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module to test processess launch."""

import os
import shutil

import pytest

from aiida import orm
from aiida.common import exceptions
from aiida.engine import CalcJob, Process, WorkChain, calcfunction, launch
from aiida.plugins import CalculationFactory

ArithmeticAddCalculation = CalculationFactory('core.arithmetic.add')


@pytest.fixture
def arithmetic_add_builder(aiida_code_installed):
    builder = ArithmeticAddCalculation.get_builder()
    builder.code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash')
    builder.x = orm.Int(1)
    builder.y = orm.Int(1)
    builder.metadata = {'options': {'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 1}}}
    return builder


@calcfunction
def add(term_a, term_b):
    return term_a + term_b


class FileCalcJob(CalcJob):
    """Calculation that takes single file as input."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('single_file', valid_type=orm.SinglefileData)
        spec.input_namespace('files', valid_type=orm.SinglefileData, dynamic=True)

    def prepare_for_submission(self, folder):
        from aiida.common.datastructures import CalcInfo, CodeInfo

        # Use nested path for the target filename, where the directory does not exist, to check that the engine will
        # create intermediate directories as needed. Regression test for #4350
        local_copy_list = [(self.inputs.single_file.uuid, self.inputs.single_file.filename, 'path/single_file')]

        for name, node in self.inputs.files.items():
            local_copy_list.append((node.uuid, node.filename, name))

        codeinfo = CodeInfo()
        codeinfo.code_uuid = self.inputs.code.uuid

        calcinfo = CalcInfo()
        calcinfo.codes_info = [codeinfo]
        calcinfo.local_copy_list = local_copy_list
        return calcinfo


class AddWorkChain(WorkChain):
    """Workchain that adds two nubers and returns the sum."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('term_a', valid_type=orm.Int)
        spec.input('term_b', valid_type=orm.Int)
        spec.outline(cls.add)
        spec.output('result', valid_type=orm.Int)

    def add(self):
        self.out('result', orm.Int(self.inputs.term_a + self.inputs.term_b).store())


@pytest.mark.usefixtures('started_daemon_client')
def test_submit_wait(arithmetic_add_builder):
    """Test the ``wait`` argument of :meth:`aiida.engine.launch.submit`."""
    node = launch.submit(arithmetic_add_builder, wait=True, wait_interval=0.1)
    assert node.is_finished, node.process_state
    assert node.is_finished_ok, node.exit_code


def test_submit_no_broker(arithmetic_add_builder, monkeypatch, manager):
    """Test that ``submit`` raises ``InvalidOperation`` if the runner does not have a controller.

    The runner does not have a controller if the runner was not provided a communicator which is the case for profiles
    that do not define a broker.
    """
    runner = manager.get_runner()
    monkeypatch.setattr(runner, '_controller', None)

    with pytest.raises(
        exceptions.InvalidOperation, match=r'Cannot submit because the runner does not have a process controller.*'
    ):
        launch.submit(arithmetic_add_builder)


def test_await_processes_invalid():
    """Test :func:`aiida.engine.launch.await_processes` for invalid inputs."""
    with pytest.raises(TypeError):
        launch.await_processes(None)

    with pytest.raises(TypeError):
        launch.await_processes([orm.Data()])

    with pytest.raises(TypeError):
        launch.await_processes(orm.ProcessNode())


@pytest.mark.usefixtures('started_daemon_client')
def test_await_processes(aiida_code_installed, caplog):
    """Test :func:`aiida.engine.launch.await_processes`."""
    builder = ArithmeticAddCalculation.get_builder()
    builder.code = aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash')
    builder.x = orm.Int(1)
    builder.y = orm.Int(2)
    builder.metadata = {'options': {'resources': {'num_machines': 1}}}
    node = launch.submit(builder)

    assert not node.is_terminated
    launch.await_processes([node])
    assert node.is_terminated
    assert len(caplog.records) > 0
    assert 'out of 1 processes terminated.' in caplog.records[0].message


@pytest.mark.requires_rmq
class TestLaunchers:
    """Class to test process launchers."""

    @pytest.fixture(autouse=True)
    def init_profile(self):
        """Initialize the profile."""
        assert Process.current() is None
        self.term_a = orm.Int(1)
        self.term_b = orm.Int(2)
        self.result = 3
        assert Process.current() is None

    def test_calcfunction_run(self):
        """Test calcfunction run."""
        result = launch.run(add, term_a=self.term_a, term_b=self.term_b)
        assert result == self.result

    def test_calcfunction_run_get_node(self):
        """Test calcfunction run by run_get_node."""
        result, node = launch.run_get_node(add, term_a=self.term_a, term_b=self.term_b)
        assert result == self.result
        assert isinstance(node, orm.CalcFunctionNode)

    def test_calcfunction_run_get_pk(self):
        """Test calcfunction run by run_get_pk."""
        result, pk = launch.run_get_pk(add, term_a=self.term_a, term_b=self.term_b)
        assert result == self.result
        assert isinstance(pk, int)

    def test_workchain_run(self):
        """Test workchain run."""
        result = launch.run(AddWorkChain, term_a=self.term_a, term_b=self.term_b)
        assert result['result'] == self.result

    def test_workchain_run_get_node(self):
        """Test workchain run by run_get_node."""
        result, node = launch.run_get_node(AddWorkChain, term_a=self.term_a, term_b=self.term_b)
        assert result['result'] == self.result
        assert isinstance(node, orm.WorkChainNode)

    def test_workchain_run_get_pk(self):
        """Test workchain run by run_get_pk."""
        result, pk = launch.run_get_pk(AddWorkChain, term_a=self.term_a, term_b=self.term_b)
        assert result['result'] == self.result
        assert isinstance(pk, int)

    def test_workchain_builder_run(self):
        """Test workchain builder run."""
        builder = AddWorkChain.get_builder()
        builder.term_a = self.term_a
        builder.term_b = self.term_b
        result = launch.run(builder)
        assert result['result'] == self.result

    def test_workchain_builder_run_get_node(self):
        """Test workchain builder that run by run_get_node."""
        builder = AddWorkChain.get_builder()
        builder.term_a = self.term_a
        builder.term_b = self.term_b
        result, node = launch.run_get_node(builder)
        assert result['result'] == self.result
        assert isinstance(node, orm.WorkChainNode)

    def test_workchain_builder_run_get_pk(self):
        """Test workchain builder that run by run_get_pk."""
        builder = AddWorkChain.get_builder()
        builder.term_a = self.term_a
        builder.term_b = self.term_b
        result, pk = launch.run_get_pk(builder)
        assert result['result'] == self.result
        assert isinstance(pk, int)

    def test_submit_store_provenance_false(self):
        """Verify that submitting with `store_provenance=False` raises."""
        with pytest.raises(exceptions.InvalidOperation):
            launch.submit(AddWorkChain, term_a=self.term_a, term_b=self.term_b, metadata={'store_provenance': False})


@pytest.mark.requires_rmq
class TestLaunchersDryRun:
    """Test the launchers when performing a dry-run."""

    @pytest.fixture(autouse=True)
    def init_profile(self, aiida_localhost):
        """Initialize the profile."""
        from aiida.common.folders import CALC_JOB_DRY_RUN_BASE_PATH

        assert Process.current() is None
        self.computer = aiida_localhost
        self.code = orm.InstalledCode(
            default_calc_job_plugin='core.arithmetic.add', computer=self.computer, filepath_executable='/bin/bash'
        ).store()
        yield
        assert Process.current() is None
        # Make sure to clean the test directory that will be generated by the dry-run
        filepath = os.path.join(os.getcwd(), CALC_JOB_DRY_RUN_BASE_PATH)
        try:
            shutil.rmtree(filepath)
        except Exception:
            pass

    def test_launchers_dry_run(self):
        """All launchers should work with `dry_run=True`, even `submit` which forwards to `run`."""
        inputs = {
            'code': self.code,
            'x': orm.Int(1),
            'y': orm.Int(1),
            'metadata': {'dry_run': True, 'options': {'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 1}}},
        }

        result = launch.run(ArithmeticAddCalculation, **inputs)
        assert result == {}

        result, pk = launch.run_get_pk(ArithmeticAddCalculation, **inputs)
        assert result == {}
        assert isinstance(pk, int)

        result, node = launch.run_get_node(ArithmeticAddCalculation, **inputs)
        assert result == {}
        assert isinstance(node, orm.CalcJobNode)
        assert isinstance(node.dry_run_info, dict)
        assert 'folder' in node.dry_run_info
        assert 'script_filename' in node.dry_run_info

        node = launch.submit(ArithmeticAddCalculation, **inputs)
        assert isinstance(node, orm.CalcJobNode)

    def test_launchers_dry_run_no_provenance(self):
        """Test the launchers in `dry_run` mode with `store_provenance=False`."""
        inputs = {
            'code': self.code,
            'x': orm.Int(1),
            'y': orm.Int(1),
            'metadata': {
                'dry_run': True,
                'store_provenance': False,
                'options': {'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 1}},
            },
        }

        result = launch.run(ArithmeticAddCalculation, **inputs)
        assert result == {}

        result, pk = launch.run_get_pk(ArithmeticAddCalculation, **inputs)
        assert result == {}
        assert pk is None

        result, node = launch.run_get_node(ArithmeticAddCalculation, **inputs)
        assert result == {}
        assert isinstance(node, orm.CalcJobNode)
        assert not node.is_stored
        assert isinstance(node.dry_run_info, dict)
        assert 'folder' in node.dry_run_info
        assert 'script_filename' in node.dry_run_info

        node = launch.submit(ArithmeticAddCalculation, **inputs)
        assert isinstance(node, orm.CalcJobNode)
        assert not node.is_stored

    def test_calcjob_dry_run_no_provenance(self):
        """Test that dry run with `store_provenance=False` still works for unstored inputs.

        The special thing about this test is that the unstored input nodes that will be used in the `local_copy_list`.
        This was broken as the code in `upload_calculation` assumed that the nodes could be loaded through their UUID
        which is not the case in the `store_provenance=False` mode with unstored nodes. Note that it also explicitly
        tests nested namespaces as that is a non-trivial case.
        """
        import tempfile

        with tempfile.NamedTemporaryFile('w+') as handle:
            handle.write('dummy_content')
            handle.flush()
            single_file = orm.SinglefileData(file=handle.name)
            file_one = orm.SinglefileData(file=handle.name)
            file_two = orm.SinglefileData(file=handle.name)

        inputs = {
            'code': self.code,
            'single_file': single_file,
            'files': {
                'file_one': file_one,
                'file_two': file_two,
            },
            'metadata': {
                'dry_run': True,
                'store_provenance': False,
                'options': {'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 1}},
            },
        }

        _, node = launch.run_get_node(FileCalcJob, **inputs)
        assert 'folder' in node.dry_run_info
        for filename in ['path', 'file_one', 'file_two']:
            assert filename in os.listdir(node.dry_run_info['folder'])


@pytest.mark.requires_rmq
@pytest.mark.usefixtures('aiida_profile_clean')
class TestProcessQueueRouting:
    """Tests for process queue routing functionality (requires RabbitMQ broker)."""

    @pytest.fixture
    def queue_config(self, aiida_profile):
        """Set up queue configuration for tests."""
        from aiida.manage.configuration import get_config

        profile = aiida_profile
        profile.set_queue_config(
            {
                'default': {'root_workchain_prefetch': 200, 'calcjob_prefetch': 'UNLIMITED'},
                'priority': {'root_workchain_prefetch': 50, 'calcjob_prefetch': 'UNLIMITED'},
            }
        )
        get_config().update_profile(profile)
        get_config().store()
        return profile

    def test_process_queue_name_methods(self):
        """Test Process.set_queue_name() and get_queue_name() methods."""
        from aiida.engine import Process

        class SimpleProcess(Process):
            _node_class = orm.WorkflowNode

            @classmethod
            def define(cls, spec):
                super().define(spec)

            async def run(self):
                pass

        proc = SimpleProcess()

        # Initially no queue name set
        assert proc.get_queue_name() is None

        # Set queue name
        proc.set_queue_name('default')
        assert proc.get_queue_name() == 'default'

        # Update queue name
        proc.set_queue_name('priority')
        assert proc.get_queue_name() == 'priority'

    def test_submit_stores_queue_name(self, queue_config, arithmetic_add_builder, manager):
        """Test that submit() stores the queue name on the process node."""
        from unittest.mock import MagicMock

        from aiida.orm import ProcessNode

        # Get the actual runner and patch its internal _controller
        runner = manager.get_runner()

        # Store original controller and replace with mock
        original_controller = runner._controller
        runner._controller = MagicMock()

        try:
            node = launch.submit(arithmetic_add_builder)

            # Queue name should be stored on the node
            queue_name = node.base.attributes.get(ProcessNode.QUEUE_NAME_KEY, None)
            assert queue_name == 'default'
        finally:
            runner._controller = original_controller

    def test_submit_to_custom_queue(self, queue_config, arithmetic_add_builder, manager):
        """Test that submit() with user_queue parameter routes to the specified queue."""
        from unittest.mock import MagicMock

        from aiida.orm import ProcessNode

        runner = manager.get_runner()

        original_controller = runner._controller
        mock_controller = MagicMock()
        runner._controller = mock_controller

        try:
            node = launch.submit(arithmetic_add_builder, user_queue='priority')

            # Queue name should be stored on the node
            queue_name = node.base.attributes.get(ProcessNode.QUEUE_NAME_KEY, None)
            assert queue_name == 'priority'

            # Verify continue_process was called with the correct queue
            mock_controller.continue_process.assert_called_once()
            call_kwargs = mock_controller.continue_process.call_args.kwargs
            assert 'priority' in call_kwargs['queue_name']
        finally:
            runner._controller = original_controller

    def test_workchain_submit_stores_queue_name(self, queue_config, manager):
        """Test that submitting a workchain stores the queue name."""
        from unittest.mock import MagicMock

        from aiida.orm import ProcessNode

        # Get the actual runner and patch its internal _controller
        runner = manager.get_runner()

        # Store original controller and replace with mock
        original_controller = runner._controller
        runner._controller = MagicMock()

        try:
            node = launch.submit(AddWorkChain, term_a=orm.Int(1), term_b=orm.Int(2))

            # Queue name should be stored on the node
            queue_name = node.base.attributes.get(ProcessNode.QUEUE_NAME_KEY, None)
            assert queue_name == 'default'
        finally:
            runner._controller = original_controller

    def test_nested_queue_name_calcjob(self, queue_config, manager):
        """Test _get_nested_queue_name routes CalcJobs correctly."""
        from unittest.mock import MagicMock

        from aiida.engine import processes
        from aiida.engine.processes.calcjobs import CalcJob

        runner = manager.get_runner()

        # Mock a process with a queue name
        class MockProcess:
            @staticmethod
            def current():
                class CurrentProcess:
                    def get_queue_name(self):
                        return 'default'

                return CurrentProcess()

        # Store original and replace
        original_process = processes.Process
        processes.Process = MockProcess

        try:
            # Create a mock process that is not a WorkChain
            mock_process = MagicMock(spec=CalcJob)
            mock_process.pid = 123

            queue_name = runner._get_nested_queue_name(mock_process)
            # Full queue name includes profile prefix, e.g. 'aiida-{uuid}.default.calcjob.queue'
            assert 'default.calcjob' in queue_name
        finally:
            processes.Process = original_process

    def test_nested_queue_name_workchain(self, queue_config, manager):
        """Test _get_nested_queue_name routes WorkChains correctly."""
        from unittest.mock import MagicMock

        from aiida.engine import processes
        from aiida.engine.processes.workchains import WorkChain

        runner = manager.get_runner()

        # Mock a process with a queue name
        class MockProcess:
            @staticmethod
            def current():
                class CurrentProcess:
                    def get_queue_name(self):
                        return 'priority'

                return CurrentProcess()

        # Store original and replace
        original_process = processes.Process
        processes.Process = MockProcess

        try:
            # Create a mock process that is a WorkChain
            mock_process = MagicMock(spec=WorkChain)
            mock_process.pid = 456

            queue_name = runner._get_nested_queue_name(mock_process)
            # Full queue name includes profile prefix
            assert 'priority.nested-workchain' in queue_name
        finally:
            processes.Process = original_process

    def test_nested_queue_name_inherits_parent_queue(self, queue_config, manager):
        """Test _get_nested_queue_name inherits parent's queue name."""
        from unittest.mock import MagicMock

        from aiida.engine import processes
        from aiida.engine.processes.calcjobs import CalcJob

        runner = manager.get_runner()

        # Mock a process with a custom queue name
        class MockProcess:
            @staticmethod
            def current():
                class CurrentProcess:
                    def get_queue_name(self):
                        return 'priority'

                return CurrentProcess()

        # Store original and replace
        original_process = processes.Process
        processes.Process = MockProcess

        try:
            mock_process = MagicMock(spec=CalcJob)
            mock_process.pid = 789

            queue_name = runner._get_nested_queue_name(mock_process)
            # Should inherit 'priority' from parent - full name includes profile prefix
            assert 'priority.calcjob' in queue_name
        finally:
            processes.Process = original_process

    def test_nested_queue_name_auto_creates_config(self, manager):
        """Test _get_nested_queue_name auto-creates queue config when missing."""
        from unittest.mock import MagicMock

        from aiida.engine import processes
        from aiida.engine.processes.calcjobs import CalcJob
        from aiida.manage.configuration import get_config

        # Remove queue config
        profile = manager.get_profile()
        profile.set_queue_config(None)
        get_config().update_profile(profile)
        get_config().store()

        runner = manager.get_runner()

        # Mock a process with no queue name
        class MockProcess:
            @staticmethod
            def current():
                class CurrentProcess:
                    def get_queue_name(self):
                        return None

                return CurrentProcess()

        # Store original and replace
        original_process = processes.Process
        processes.Process = MockProcess

        try:
            mock_process = MagicMock(spec=CalcJob)
            mock_process.pid = 123

            # Should auto-create queue config and succeed
            queue_name = runner._get_nested_queue_name(mock_process)
            assert 'default.calcjob' in queue_name

            # Verify config was created
            assert profile.get_queue_config() is not None
            assert 'default' in profile.get_queue_config()
        finally:
            processes.Process = original_process
