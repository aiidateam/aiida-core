from pathlib import Path

import pytest

from aiida.tools.dumping.config import DumpConfig
from aiida.tools.dumping.logger import DumpLogger, DumpLogStoreCollection
from aiida.tools.dumping.managers.process import ProcessDumpManager
from aiida.tools.dumping.utils.helpers import DumpTimes
from aiida.tools.dumping.utils.paths import DumpPaths


@pytest.fixture
def mock_dump_logger(tmp_path):
    """Fixture providing a DumpLogger instance without loading from file."""
    # Use a dummy path for the logger, actual file interaction is bypassed
    dump_paths = DumpPaths(parent=tmp_path, child=Path('mock_dump'))
    stores = DumpLogStoreCollection()
    return DumpLogger(dump_paths=dump_paths, stores=stores, last_dump_time_str=None)


@pytest.fixture
def process_dump_manager(mock_dump_logger, tmp_path):
    """Fixture providing an initialized ProcessDumpManager."""
    config = DumpConfig()  # Default config
    dump_paths = DumpPaths(parent=tmp_path, child=Path('manager_test_dump'))
    dump_times = DumpTimes()
    manager = ProcessDumpManager(
        config=config, dump_paths=dump_paths, dump_logger=mock_dump_logger, dump_times=dump_times
    )
    return manager
