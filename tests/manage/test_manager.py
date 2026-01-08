"""Tests for :mod:`aiida.manage.manager`."""

import pytest

from aiida import engine, orm


@engine.calcfunction
def add_calcfunction(data):
    return orm.Int(data.value + 1)


@pytest.mark.requires_rmq
def test_disconnect():
    """Test the communicator disconnect.

    When the dependency ``kiwipy`` was updated to v0.8, it introduced a problem with shutting down the communicator.
    After at least one process would have been run, trying to disconnect the communcitor would time out. The problem
    is related to the update of the lower lying libraries ``aio-pika`` and ``aiormq`` to v9.4 and v6.8, respectively.
    After much painstaking debugging the cause could not be determined, nor a solution. This test is added to
    demonstrate the problematic behavior.
    """
    from aiida.manage import get_manager

    manager = get_manager()
    manager.get_communicator()
    manager.reset_profile()  # This returns just fine

    result, node = add_calcfunction.run_get_node(1)
    assert node.is_finished_ok
    assert result == 2
    manager.reset_profile()
