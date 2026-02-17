###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Benchmark tests comparing import to loose vs packed storage.

These tests measure the performance difference between importing archive files
to loose storage (default) versus directly to packed storage.

Different scenarios are tested:
- many-small: Many small files (where packed import helps most)
- mixed: Mix of small, medium, and large files (typical use case)
- few-large: Few large files (where the difference is smaller)

To scale all scenarios for local testing, edit SIZE_MULTIPLIER below.

Running benchmarks (do NOT use -n, it's incompatible with pytest-benchmark):
    uv run pytest tests/benchmark/test_packed_import.py --benchmark-only
"""

import io

import pytest

from aiida.manage import get_manager
from aiida.orm import FolderData, load_node
from aiida.tools.archive import create_archive, import_archive

GROUP_NAME = 'packed-import'

# =============================================================================
# SIZE MULTIPLIER - Adjust this for local testing with larger sizes
# =============================================================================
# Default: 1 (CI-friendly). For realistic benchmarks, try 10-100.
SIZE_MULTIPLIER = 1
# =============================================================================


def add_file_to_node(node: FolderData, file_index: int, size: int, category: str) -> int:
    """Add a file to the node and return its actual size."""
    header = f'{category}_{file_index:010d}_'.encode()
    padding_size = max(0, size - len(header))
    content = header + (b'x' * padding_size)
    node.base.repository.put_object_from_filelike(io.BytesIO(content), f'{category}_{file_index:06d}.dat')
    return len(content)


def create_folder_node_with_objects(
    total_size: int,
    small_size: int,
    medium_size: int,
    large_size: int,
) -> tuple[FolderData, int]:
    """Create a FolderData node with mixed-size objects."""
    node = FolderData()
    file_index = 0

    # Distribution: 50% small, 30% medium, 20% large
    target_small = int(total_size * 0.5)
    target_medium = int(total_size * 0.3)
    target_large = int(total_size * 0.2)

    small_accumulated = 0
    while small_accumulated < target_small and small_size > 0:
        small_accumulated += add_file_to_node(node, file_index, small_size, 'small')
        file_index += 1

    medium_accumulated = 0
    while medium_accumulated < target_medium and medium_size > 0:
        medium_accumulated += add_file_to_node(node, file_index, medium_size, 'medium')
        file_index += 1

    large_accumulated = 0
    while large_accumulated < target_large and large_size > 0:
        large_accumulated += add_file_to_node(node, file_index, large_size, 'large')
        file_index += 1

    node.store()
    return node, file_index


# Scenarios: (total_size, small_size, medium_size, large_size)
# These represent different real-world use cases
SCENARIOS = {
    # Many small files - typical AiiDA calculation outputs (stdout, stderr, input files)
    'many-small': (500_000, 100, 1_000, 10_000),
    # Mixed sizes - balanced workload
    'mixed': (1_000_000, 1_000, 10_000, 100_000),
    # Few large files - data-heavy calculations
    'few-large': (1_000_000, 10_000, 100_000, 500_000),
}


@pytest.fixture
def archive_for_scenario(tmp_path, aiida_profile, request):
    """Create an archive for the given scenario."""
    scenario_name = request.param
    total_size, small_size, medium_size, large_size = SCENARIOS[scenario_name]

    # Apply global multiplier
    total_size *= SIZE_MULTIPLIER
    small_size *= SIZE_MULTIPLIER
    medium_size *= SIZE_MULTIPLIER
    large_size *= SIZE_MULTIPLIER

    aiida_profile.reset_storage()

    node, num_objects = create_folder_node_with_objects(total_size, small_size, medium_size, large_size)
    node_uuid = node.uuid

    archive_path = tmp_path / 'test.aiida'
    create_archive(
        [node],
        filename=str(archive_path),
        overwrite=True,
        include_comments=False,
        include_logs=False,
    )

    return archive_path, node_uuid, num_objects, total_size, scenario_name


@pytest.mark.parametrize('archive_for_scenario', SCENARIOS.keys(), indirect=True)
@pytest.mark.parametrize('packed', [pytest.param(False, id='loose'), pytest.param(True, id='packed')])
@pytest.mark.benchmark(group=GROUP_NAME)
def test_import(aiida_profile, benchmark, archive_for_scenario, packed):
    """Benchmark importing archive to loose or packed storage."""
    archive_path, node_uuid, num_objects, total_size, scenario = archive_for_scenario

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
    benchmark.extra_info['num_objects'] = num_objects
    benchmark.extra_info['total_size_bytes'] = total_size
