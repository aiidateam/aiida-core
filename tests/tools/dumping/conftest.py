import pytest

from aiida.tools.dumping.config import DumpConfig
from aiida.tools.dumping.executors.process import ProcessDumpExecutor
from aiida.tools.dumping.tracking import DumpTracker
from aiida.tools.dumping.utils.helpers import DumpTimes
from aiida.tools.dumping.utils.paths import DumpPaths


@pytest.fixture
def mock_dump_tracker(tmp_path):
    """Fixture providing a DumpTracker instance without loading from file."""
    # Use a dummy path for the logger, actual file interaction is bypassed
    config = DumpConfig()
    dump_paths = DumpPaths(base_output_path=tmp_path / 'mock_dump', config=config)
    return DumpTracker(dump_paths=dump_paths, last_dump_time_str=None)


@pytest.fixture
def process_dump_manager(mock_dump_tracker, tmp_path):
    """Fixture providing an initialized ProcessDumpExecutor."""
    config = DumpConfig()
    dump_paths = DumpPaths(base_output_path=tmp_path / 'manager_test_dump', config=config)
    dump_times = DumpTimes()
    manager = ProcessDumpExecutor(
        config=config, dump_paths=dump_paths, dump_tracker=mock_dump_tracker, dump_times=dump_times
    )
    return manager
