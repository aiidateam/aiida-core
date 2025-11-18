"""Tests for :mod:`aiida.orm.nodes.process.process`."""

import tempfile
from pathlib import Path

import pytest

from aiida import orm
from aiida.engine import ExitCode, ProcessState, launch
from aiida.orm import Int
from aiida.orm.nodes.caching import NodeCaching
from aiida.orm.nodes.process.process import ProcessNode
from aiida.orm.nodes.process.workflow import WorkflowNode
from aiida.plugins import CalculationFactory

ArithmeticAddCalculation = CalculationFactory('core.arithmetic.add')


def test_exit_code():
    """Test the :meth:`aiida.orm.nodes.process.process.ProcessNode.exit_code` property."""
    node = ProcessNode()
    assert node.exit_code is None

    node.set_exit_status(418)
    assert node.exit_code is None

    node.set_exit_message('I am a teapot')
    assert node.exit_code == ExitCode(418, 'I am a teapot')


@pytest.fixture
@pytest.mark.usefixtures('aiida_profile')
def process_nodes():
    """Return a list of tuples of a process node and whether they should be a valid cache source."""
    entry_point = 'aiida.calculations:core.arithmetic.add'

    node_invalid_cache_extra = WorkflowNode(label='node_invalid_cache_extra')
    node_invalid_cache_extra.set_process_state(ProcessState.FINISHED)
    node_invalid_cache_extra.base.extras.set(NodeCaching._VALID_CACHE_KEY, False)

    node_no_process_class = WorkflowNode(label='node_no_process_class')
    node_no_process_class.set_process_state(ProcessState.FINISHED)

    node_invalid_process_class = WorkflowNode(label='node_invalid_process_class', process_type='aiida.calculations:no')
    node_invalid_process_class.set_process_state(ProcessState.FINISHED)

    node_excepted = WorkflowNode(label='node_excepted', process_type=entry_point)
    node_excepted.set_process_state(ProcessState.EXCEPTED)

    node_excepted_stored = WorkflowNode(label='node_excepted_stored', process_type=entry_point)
    node_excepted_stored.set_process_state(ProcessState.EXCEPTED)

    node_excepted_sealed = WorkflowNode(label='node_excepted_sealed', process_type=entry_point)
    node_excepted_sealed.set_process_state(ProcessState.EXCEPTED)

    node_finished = WorkflowNode(label='node_finished', process_type=entry_point)
    node_finished.set_process_state(ProcessState.FINISHED)

    node_finished_stored = WorkflowNode(label='node_finished_stored', process_type=entry_point)
    node_finished_stored.set_process_state(ProcessState.FINISHED)

    node_finished_sealed = WorkflowNode(label='node_finished_sealed', process_type=entry_point)
    node_finished_sealed.set_process_state(ProcessState.FINISHED)

    return (
        (node_invalid_cache_extra.store().seal(), False),
        (node_no_process_class.store().seal(), False),
        (node_invalid_process_class.store().seal(), False),
        (node_excepted, False),
        (node_excepted_stored.store(), False),
        (node_excepted_sealed.store().seal(), False),
        (node_finished, False),
        (node_finished_stored.store(), False),
        (node_finished_sealed.store().seal(), True),
    )


def test_is_valid_cache(process_nodes):
    """Test the :meth:`aiida.orm.nodes.process.process.ProcessNode.is_valid_cache` property."""
    for node, is_valid_cache in process_nodes:
        assert node.base.caching.is_valid_cache == is_valid_cache, node


def test_get_builder_restart(aiida_code_installed):
    """Test :meth:`aiida.orm.nodes.process.process.ProcessNode.get_builder_restart`."""
    inputs = {
        'code': aiida_code_installed(default_calc_job_plugin='core.arithmetic.add', filepath_executable='/bin/bash'),
        'x': Int(1),
        'y': Int(1),
        'metadata': {'options': {'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 1}}},
    }
    _, node = launch.run_get_node(ArithmeticAddCalculation, inputs)
    assert node.get_builder_restart()._inputs(prune=True) == inputs


@pytest.mark.usefixtures('aiida_profile_clean')
class TestProcessNodeDump:
    """Test the dump method of ProcessNode."""

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_dump_dry_run(self, tmp_path, generate_calculation_node_add):
        """Test dry run mode doesn't create files."""
        node = generate_calculation_node_add()

        output_path = tmp_path / 'process_dump'
        result_path = node.dump(output_path=output_path, dry_run=True)

        # In dry run, the path is returned but no files are created
        assert result_path == output_path
        assert not result_path.exists()

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_dump_basic(self, tmp_path, generate_calculation_node_add):
        """Test basic dumping of a process node."""
        # Create and run a simple calculation
        node = generate_calculation_node_add()
        output_path = tmp_path / 'process_dump'
        result_path = node.dump(output_path=output_path)

        # Check that dump was created
        assert result_path.exists()
        assert result_path.is_dir()

        # Check for expected files
        assert (result_path / 'aiida_node_metadata.yaml').exists()
        assert (result_path / '.aiida_dump_safeguard').exists()
        assert (result_path / 'README.md').exists()

    @pytest.mark.usefixtures('aiida_profile_clean')
    def test_dump_include_outputs(self, tmp_path, generate_calculation_node_io):
        """Test dumping with outputs included."""
        node = generate_calculation_node_io(attach_outputs=True)
        node.seal()

        output_path = tmp_path / 'process_dump'
        result_path = node.dump(output_path=output_path)

        assert result_path.exists()

    def test_dump_flat_structure(self, tmp_path, generate_calculation_node_add):
        """Test dumping with flat directory structure."""
        node = generate_calculation_node_add()

        output_path = tmp_path / 'process_dump_flat'
        result_path = node.dump(output_path=output_path, flat=True)

        assert result_path.exists()
        assert (result_path / 'aiida_node_metadata.yaml').exists()

    def test_dump_overwrite(self, tmp_path, generate_calculation_node_add):
        """Test overwrite functionality."""
        node = generate_calculation_node_add()
        output_path = tmp_path / 'process_dump'

        # First dump
        result_path1 = node.dump(output_path=output_path)
        assert result_path1.exists()

        # Second dump with overwrite should succeed
        result_path2 = node.dump(output_path=output_path, overwrite=True)
        assert result_path2.exists()
        assert result_path1 == result_path2

    def test_dump_unsealed_node_fails(self):
        """Test that dumping unsealed node fails by default."""
        node = orm.CalculationNode()
        node.store()  # Store but don't seal

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / 'process_dump'

            # Should raise error for unsealed node
            with pytest.raises(Exception):  # The actual exception type from your implementation
                node.dump(output_path=output_path)

    def test_dump_unsealed_node_allowed(self):
        """Test that dumping unsealed node works with dump_unsealed=True."""
        node = orm.CalculationNode()
        node.store()  # Store but don't seal

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / 'process_dump'
            result_path = node.dump(output_path=output_path, dump_unsealed=True)

            assert result_path.exists()
            assert (result_path / 'aiida_node_metadata.yaml').exists()
