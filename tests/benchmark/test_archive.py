###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Performance benchmark tests for import/export utilities.

The purpose of these tests is to benchmark and compare importing and exporting
parts of the database, including comparing loose vs packed storage imports.
"""

import io
from io import StringIO

import pytest

from aiida.common.links import LinkType
from aiida.engine import ProcessState
from aiida.manage import get_manager
from aiida.orm import CalcFunctionNode, Dict, FolderData, Node, QueryBuilder, load_node
from aiida.tools.archive import create_archive, import_archive

GROUP_NAME = 'import-export'

# =============================================================================
# SIZE MULTIPLIER - Adjust for local testing with larger sizes
# =============================================================================
# Default: 1 (CI-friendly). For realistic benchmarks, try 10-100.
SIZE_MULTIPLIER = 1
# =============================================================================


def recursive_provenance(in_node, depth, breadth, num_objects=0):
    """Recursively build a provenance tree."""
    if not in_node.is_stored:
        in_node.store()
    if depth < 1:
        return
    depth -= 1
    for _ in range(breadth):
        calcfunc = CalcFunctionNode()
        calcfunc.set_process_state(ProcessState.FINISHED)
        calcfunc.set_exit_status(0)
        calcfunc.base.links.add_incoming(in_node, link_type=LinkType.INPUT_CALC, link_label='input')
        calcfunc.store()

        out_node = Dict(dict={str(i): i for i in range(10)})
        for idx in range(num_objects):
            out_node.base.repository.put_object_from_filelike(StringIO('a' * 10000), f'key{idx!s}')
        out_node.base.links.add_incoming(calcfunc, link_type=LinkType.CREATE, link_label='output')
        out_node.store()

        calcfunc.seal()

        recursive_provenance(out_node, depth, breadth, num_objects)


def get_export_kwargs(**kwargs):
    """Return default export keyword arguments."""
    obj = {
        'input_calc_forward': True,
        'input_work_forward': True,
        'create_backward': True,
        'return_backward': True,
        'call_calc_backward': True,
        'call_work_backward': True,
        'include_comments': True,
        'include_logs': True,
        'overwrite': True,
    }
    obj.update(kwargs)
    return obj


TREE = {
    'no-objects': (4, 3, 0),
    'with-objects': (4, 3, 2),
}


@pytest.mark.parametrize('depth,breadth,num_objects', TREE.values(), ids=TREE.keys())
@pytest.mark.benchmark(group=GROUP_NAME)
def test_export(benchmark, tmp_path, depth, breadth, num_objects):
    """Benchmark exporting a provenance graph."""
    root_node = Dict()
    recursive_provenance(root_node, depth=depth, breadth=breadth, num_objects=num_objects)
    out_path = tmp_path / 'test.aiida'
    kwargs = get_export_kwargs(filename=str(out_path))

    def _setup():
        if out_path.exists():
            out_path.unlink()

    def _run():
        create_archive([root_node], **kwargs)

    benchmark.pedantic(_run, setup=_setup, iterations=1, rounds=12, warmup_rounds=1)
    assert out_path.exists()


@pytest.mark.parametrize('depth,breadth,num_objects', TREE.values(), ids=TREE.keys())
@pytest.mark.benchmark(group=GROUP_NAME)
def test_import(aiida_profile, benchmark, tmp_path, depth, breadth, num_objects):
    """Benchmark importing a provenance graph."""
    aiida_profile.reset_storage()
    root_node = Dict()
    recursive_provenance(root_node, depth=depth, breadth=breadth, num_objects=num_objects)
    root_uuid = root_node.uuid
    out_path = tmp_path / 'test.aiida'
    kwargs = get_export_kwargs(filename=str(out_path))
    create_archive([root_node], **kwargs)

    def _setup():
        aiida_profile.reset_storage()

    def _run():
        import_archive(str(out_path))

    benchmark.pedantic(_run, setup=_setup, iterations=1, rounds=12, warmup_rounds=1)
    load_node(root_uuid)


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.benchmark(group='large-archive')
def test_large_archive_export_benchmark(tmp_path, benchmark):
    """Benchmark export performance with different filter_size values using 10k nodes."""
    from tests.utils.nodes import create_int_nodes

    num_nodes = 10_000

    # Setup: create nodes (not benchmarked)
    _ = create_int_nodes(num_nodes)
    export_file = tmp_path / 'export_benchmark.aiida'

    def export_operation():
        create_archive(entities=None, filename=export_file, overwrite=True)

    benchmark.pedantic(export_operation, rounds=3, iterations=1)

    # Verify export succeeded
    assert export_file.exists()


@pytest.mark.benchmark(group='large-archive')
def test_large_archive_import_benchmark(tmp_path, benchmark, aiida_profile_clean):
    """Benchmark import performance."""
    from tests.utils.nodes import create_int_nodes

    num_nodes = 10_000

    # Create archive once, outside benchmark (not timed at all)
    _ = create_int_nodes(num_nodes)
    export_file = tmp_path / 'import_benchmark.aiida'
    _ = create_archive(entities=None, filename=export_file)

    def import_operation():
        aiida_profile_clean.reset_storage()
        import_archive(export_file)

    benchmark.pedantic(import_operation, rounds=5, iterations=1)

    # Verify correctness
    all_nodes = QueryBuilder().append(Node).all(flat=True)
    assert len(all_nodes) == num_nodes


def _add_file_to_node(node: FolderData, file_index: int, size: int) -> int:
    """Add a file to the node and return its actual size."""
    header = f'file_{file_index:010d}_'.encode()
    padding_size = max(0, size - len(header))
    content = header + (b'x' * padding_size)
    node.base.repository.put_object_from_filelike(io.BytesIO(content), f'file_{file_index:06d}.dat')
    return len(content)


def _create_folder_node_with_objects(num_files: int, file_size: int) -> tuple[FolderData, int]:
    """Create a FolderData node with uniform-size objects.

    :param num_files: Number of files to create
    :param file_size: Size of each file in bytes
    :return: Tuple of (node, actual_file_count)
    """
    node = FolderData()
    for i in range(num_files):
        _add_file_to_node(node, i, file_size)
    node.store()
    return node, num_files


# Scenarios: (num_files, file_size_bytes)
# These create different file count / size combinations to test packed import performance
PACKED_SCENARIOS = {
    # Many small files - typical AiiDA outputs (stdout, stderr, input files)
    # This is where packed import helps most (fewer fsyncs)
    'many-small': (2500, 100),
    # Moderate number of medium files - balanced workload
    'mixed': (250, 1_000),
    # Few large files - data-heavy calculations
    # Packed import helps less here (fewer files = fewer fsyncs saved)
    'few-large': (25, 10_000),
}


@pytest.fixture
def archive_for_scenario(tmp_path, aiida_profile, request):
    """Create an archive for the given scenario."""
    scenario_name = request.param
    num_files, file_size = PACKED_SCENARIOS[scenario_name]

    # Apply global multiplier
    num_files *= SIZE_MULTIPLIER
    file_size *= SIZE_MULTIPLIER

    aiida_profile.reset_storage()

    node, num_objects = _create_folder_node_with_objects(num_files, file_size)
    node_uuid = node.uuid

    archive_path = tmp_path / 'test.aiida'
    create_archive(
        [node],
        filename=str(archive_path),
        overwrite=True,
        include_comments=False,
        include_logs=False,
    )

    return archive_path, node_uuid, num_objects, file_size, scenario_name


@pytest.mark.parametrize('archive_for_scenario', PACKED_SCENARIOS.keys(), indirect=True)
@pytest.mark.parametrize('packed', [pytest.param(False, id='loose'), pytest.param(True, id='packed')])
@pytest.mark.benchmark(group='packed-import')
def test_packed_import_scenarios(aiida_profile, benchmark, archive_for_scenario, packed):
    """Benchmark importing archive to loose or packed storage with different file size distributions."""
    archive_path, node_uuid, num_objects, file_size, scenario = archive_for_scenario

    def _setup():
        aiida_profile.reset_storage()

    def _run():
        import_archive(str(archive_path), packed=packed)

    benchmark.pedantic(_run, setup=_setup, iterations=1, rounds=3, warmup_rounds=1)

    # Verify import succeeded
    imported_node = load_node(node_uuid)
    assert len(list(imported_node.base.repository.list_object_names())) == num_objects

    # Verify storage type
    repo = get_manager().get_profile_storage().get_repository()
    with repo._container as container:
        counts = container.count_objects()
        if packed:
            assert counts.packed == num_objects
        else:
            assert counts.loose == num_objects

    benchmark.extra_info['scenario'] = scenario
    benchmark.extra_info['packed'] = packed
    benchmark.extra_info['num_files'] = num_objects
    benchmark.extra_info['file_size_bytes'] = file_size
