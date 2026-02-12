"""Tests execution of Jupyter notebooks in a real kernel and verify outcomes."""

from pathlib import Path

import nbformat
import pytest
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

NOTEBOOK_DIR = Path(__file__).parent


def _execute_notebook(notebook_name, timeout=120):
    """Execute a notebook and return the executed notebook object."""
    path = NOTEBOOK_DIR / notebook_name
    nb = nbformat.read(path, as_version=4)
    client = NotebookClient(nb, timeout=timeout, kernel_name='python3')
    client.execute()
    return nb


def _get_cell_outputs(cell, output_type='stream', name='stdout'):
    """Extract text from cell outputs of a given type."""
    texts = []
    for output in cell.outputs:
        if output.output_type == output_type and output.get('name') == name:
            texts.append(output.text)
    return ''.join(texts)


@pytest.mark.timeout(180)
def test_same_cell_fails_with_expected_error():
    """Test that load_profile + engine call in the same cell fails with a clear error."""
    path = NOTEBOOK_DIR / 'test_same_cell.ipynb'
    nb = nbformat.read(path, as_version=4)
    client = NotebookClient(nb, timeout=120, kernel_name='python3')

    with pytest.raises(CellExecutionError) as exc_info:
        client.execute()

    code_cell = nb.cells[1]  # Cell index 1, after the markdown cell
    stdout = _get_cell_outputs(code_cell)
    assert 'Profile loaded' in stdout
    assert 'Synchronous process execution is available only from the next cell' in stdout
    assert 'All aiida engine methods is only availabe from the next cell' in stdout

    error_message = str(exc_info.value)
    # Note: this error message is from plumpy and is not ideal,
    # but we have to ensure it contains the key information about the nature of the error and how to fix it.
    assert 'RuntimeError' in error_message
    assert 'Cannot synchronously execute a process while the event loop is running' in error_message
    assert 'call load_profile() in a prior cell' in error_message


@pytest.mark.timeout(180)
def test_separate_cell_passes():
    """Test that load_profile in one cell and engine call in the next cell works."""
    _execute_notebook('test_separate_cell.ipynb')


@pytest.mark.timeout(180)
def test_magic_cells_passes():
    """Test that magic commands work correctly after greenback portal is installed."""
    _execute_notebook('test_magic_cells.ipynb')
