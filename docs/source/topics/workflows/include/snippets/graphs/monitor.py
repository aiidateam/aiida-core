from pathlib import Path

from aiida.engine import graph_execution as graph
from aiida.engine import monitor
from aiida.engine import task_execution as task


@monitor
def file_is_there(path: str) -> bool:
    """Say whether the condition is met; it is looked at again until it is."""
    return Path(path).exists()


@task(outputs=['size'])
def size_of(path: str) -> int:
    return len(Path(path).read_text())


@graph
def read_once_written(path) -> int:
    written = file_is_there(path=path, interval=5)
    return size_of(path=path).after(written).size
