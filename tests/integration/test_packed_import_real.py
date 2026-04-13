"""Benchmark tests for importing real archives to loose vs packed storage.

These tests allow benchmarking with real-world archives by setting an environment
variable. Results are captured by pytest-benchmark with statistical analysis.

Usage:
    AIIDA_TEST_ARCHIVE=<archive-path.aiida> uv run pytest tests/integration/test_packed_import_real.py --benchmark-only
"""

import os

import pytest

from aiida.tools.archive import import_archive

ARCHIVE_PATH = os.environ.get('AIIDA_TEST_ARCHIVE')


@pytest.mark.skipif(not ARCHIVE_PATH, reason='Set AIIDA_TEST_ARCHIVE env var to run')
@pytest.mark.timeout(14400)  # 4 hours - real archives can be large
@pytest.mark.parametrize(
    'packed',
    [
        pytest.param(False, id='loose'),
        pytest.param(True, id='packed'),
    ],
)
@pytest.mark.benchmark(group='real-archive-import')
def test_import_real_archive(aiida_profile, benchmark, packed):
    """Benchmark importing a real archive to loose or packed storage.

    Set AIIDA_TEST_ARCHIVE environment variable to the path of the archive to test.
    """

    def _setup():
        aiida_profile.reset_storage()

    def _run():
        import_archive(ARCHIVE_PATH, packed=packed)

    benchmark.pedantic(_run, setup=_setup, iterations=1, rounds=3, warmup_rounds=0)
    benchmark.extra_info['archive'] = ARCHIVE_PATH
    benchmark.extra_info['packed'] = packed
