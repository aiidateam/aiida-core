"""Tests for :mod:`aiida.orm.nodes.process.process`."""
import pytest
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


@pytest.fixture
def default_inputs(aiida_local_code_factory):
    return {
        'code': aiida_local_code_factory('core.arithmetic.add', '/bin/bash'),
        'x': Int(1),
        'y': Int(1),
        'metadata': {'options': {'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 1}}},
    }


def test_get_builder_restart(default_inputs):
    """Test :meth:`aiida.orm.nodes.process.process.ProcessNode.get_builder_restart`."""
    _, node = launch.run_get_node(ArithmeticAddCalculation, default_inputs)
    assert node.get_builder_restart()._inputs(prune=True) == default_inputs


def test_cache_version_attribute(default_inputs, monkeypatch, manager):
    """Test that the ``Node.CACHE_VERSION`` attribute can be used to control hashes.

    If the implementation of a ``Data`` or ``CalcJob`` plugin changes significantly, a plugin developer can change
    the ``CACHE_VERSION`` attribute to cause the hash to be changed, ensuring old completed instances of the
    class no longer to be valid cache sources.
    """
    from aiida.plugins.utils import KEY_VERSION_CACHE

    _, node_a = launch.run_get_node(ArithmeticAddCalculation, default_inputs)

    monkeypatch.setattr(ArithmeticAddCalculation, 'CACHE_VERSION', 'v1.0')

    # The runner keeps an instance of :class:`aiida.plugins.utils.PluginVersionProvider` which keeps an internal cache
    # of the version information for plugins, so we need to reset it for the monkeypatched change above to be picked up.
    manager.reset_runner()

    _, node_b = launch.run_get_node(ArithmeticAddCalculation, default_inputs)
    assert node_b.base.attributes.get('version')[KEY_VERSION_CACHE] == 'v1.0'
    assert node_a.base.caching.get_hash() != node_b.base.caching.get_hash()
