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
parts of the database.
"""

from io import StringIO

import pytest

from aiida.common.links import LinkType
from aiida.engine import ProcessState
from aiida.orm import CalcFunctionNode, Dict, Node, QueryBuilder, load_node
from aiida.tools.archive import create_archive, import_archive

GROUP_NAME = 'import-export'


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


TREE = {'no-objects': (4, 3, 0), 'with-objects': (4, 3, 2)}


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


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.benchmark(group='large-archive')
def test_large_archive_import_benchmark(tmp_path, benchmark, aiida_profile_clean):
    """Benchmark import performance with different filter_size values using 10k nodes."""
    from tests.utils.nodes import create_int_nodes

    num_nodes = 10_000

    def setup():
        """Create archive for import benchmarking (setup phase, not timed)."""
        # Create nodes and export to archive
        export_file = tmp_path / 'import_benchmark.aiida'
        # archive is being created in the multiple runs of the benchmark
        # archive creation is not timed, so we can re-use if it already exists
        if export_file.exists():
            return (export_file,), {}
        else:
            _ = create_int_nodes(num_nodes)
            _ = create_archive(entities=None, filename=export_file, overwrite=False)
        return (export_file,), {}

    def import_operation(export_file):
        """The actual import operation to benchmark."""
        aiida_profile_clean.reset_storage()
        import_archive(export_file)

    # Use benchmark.pedantic with setup function
    benchmark.pedantic(import_operation, setup=setup, rounds=3, iterations=1)

    # Verify correctness after benchmark
    all_nodes = QueryBuilder().append(Node).all(flat=True)
    assert len(all_nodes) == num_nodes
