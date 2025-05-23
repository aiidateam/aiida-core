from pathlib import Path

import pytest

from aiida.tools.dumping.config import DumpConfig
from aiida.tools.dumping.managers.process import ProcessDumpManager
from aiida.tools.dumping.tracking import DumpRegistryCollection, DumpTracker
from aiida.tools.dumping.utils.helpers import DumpTimes
from aiida.tools.dumping.utils.paths import DumpPaths


@pytest.fixture
def mock_dump_tracker(tmp_path):
    """Fixture providing a DumpTracker instance without loading from file."""
    # Use a dummy path for the logger, actual file interaction is bypassed
    dump_paths = DumpPaths(parent=tmp_path, child=Path('mock_dump'))
    stores = DumpRegistryCollection()
    return DumpTracker(dump_paths=dump_paths, stores=stores, last_dump_time_str=None)


@pytest.fixture
def process_dump_manager(mock_dump_tracker, tmp_path):
    """Fixture providing an initialized ProcessDumpManager."""
    config = DumpConfig()  # Default config
    dump_paths = DumpPaths(parent=tmp_path, child=Path('manager_test_dump'))
    dump_times = DumpTimes()
    manager = ProcessDumpManager(
        config=config, dump_paths=dump_paths, dump_tracker=mock_dump_tracker, dump_times=dump_times
    )
    return manager
