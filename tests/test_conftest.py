"""Tests for fixtures in the ``conftest.py``."""

import pytest
from importlib_metadata import EntryPoint

from aiida.common.exceptions import MissingEntryPointError
from aiida.plugins.entry_point import get_entry_point, load_entry_point

ENTRY_POINT_GROUP = 'aiida.calculations.importers'


def test_entry_points_add_invalid(entry_points):
    """Test the :meth:`EntryPointManager.add` method."""
    with pytest.raises(TypeError, match='`entry_point_string` should be a string when defined.'):
        entry_points.add('some.module:SomeClass', [])

    with pytest.raises(ValueError, match='invalid `entry_point_string` format, should `group:name`'):
        entry_points.add('some.module:SomeClass', 'core.temporary.entry_point')

    with pytest.raises(ValueError, match='neither `entry_point_string` is defined, nor `name` and `group`'):
        entry_points.add('some.module:SomeClass')


def test_entry_points_add_entry_point_string(entry_points):
    """Test the :meth:`EntryPointManager.add` method using a full entry point string."""
    entry_points.add('some.module:SomeClass', f'{ENTRY_POINT_GROUP}:core.test')
    assert isinstance(get_entry_point(ENTRY_POINT_GROUP, 'core.test'), EntryPoint)


def test_entry_points_add_group_and_name(entry_points):
    """Test the :meth:`EntryPointManager.add` method using a separate entry point group and name."""
    entry_points.add('some.module:SomeClass', group=ENTRY_POINT_GROUP, name='core.test')
    assert isinstance(get_entry_point(ENTRY_POINT_GROUP, 'core.test'), EntryPoint)


def test_entry_points_remove_invalid(entry_points):
    """Test the :meth:`EntryPointManager.remove` method."""
    with pytest.raises(TypeError, match='`entry_point_string` should be a string when defined.'):
        entry_points.remove([])

    with pytest.raises(ValueError, match='invalid `entry_point_string` format, should `group:name`'):
        entry_points.remove('core.temporary.entry_point')

    with pytest.raises(ValueError, match='neither `entry_point_string` is defined, nor `name` and `group`'):
        entry_points.remove()


def test_entry_points_remove_entry_point_string(entry_points):
    """Test the :meth:`EntryPointManager.remove` method using a full entry point string."""
    entry_points.add('some.module:SomeClass', f'{ENTRY_POINT_GROUP}:core.test')
    entry_points.remove(f'{ENTRY_POINT_GROUP}:core.test')

    with pytest.raises(MissingEntryPointError):
        get_entry_point(ENTRY_POINT_GROUP, 'core.test')


def test_entry_points_remove_group_and_name(entry_points):
    """Test the :meth:`EntryPointManager.remove` method using a separate entry point group and name."""
    entry_points.add('some.module:SomeClass', f'{ENTRY_POINT_GROUP}:core.test')
    entry_points.remove(group=ENTRY_POINT_GROUP, name='core.test')

    with pytest.raises(MissingEntryPointError):
        get_entry_point(ENTRY_POINT_GROUP, 'core.test')


def raise_runtime_error():
    """Dummy function to be registered as an entry point."""
    raise RuntimeError('inline function was called')


def test_entry_points_add_and_load(entry_points):
    """Test adding an entry point to an inline function loading it and calling it."""
    entry_point_name = 'core.test'
    entry_points.add(raise_runtime_error, group=ENTRY_POINT_GROUP, name=entry_point_name)

    entry_point = load_entry_point(ENTRY_POINT_GROUP, entry_point_name)

    with pytest.raises(RuntimeError, match='inline function was called'):
        entry_point()


def test_arithmetic_add_node_results(generate_calculation_node_add):
    """Test that run and construct methods produce equivalent nodes."""
    x, y = 5, 7

    run_node = generate_calculation_node_add(x=x, y=y, method='run')
    construct_node = generate_calculation_node_add(x=x, y=y, method='construct')

    # Check same basic properties
    assert run_node.outputs.sum.value == construct_node.outputs.sum.value == 12
    assert run_node.exit_status == construct_node.exit_status == 0
    assert run_node.process_state == construct_node.process_state
    assert run_node.inputs.x.value == construct_node.inputs.x.value == x
    assert run_node.inputs.y.value == construct_node.inputs.y.value == y


@pytest.mark.benchmark
@pytest.mark.parametrize('method', ['run', 'construct'])
def test_benchmark_arithmetic_add_node_methods(benchmark, generate_calculation_node_add, method):
    """Benchmark for run and construct methods of ArithmeticAdd CalcJob node."""

    def create_node():
        return generate_calculation_node_add(method=method)

    node = benchmark(create_node)
    assert node.is_stored
    assert node.outputs.sum.value == 3
