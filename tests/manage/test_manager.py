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
    demonstrate the problematic behavior. Getting the communicator and then disconnecting it (through calling
    :meth:`aiida.manage.manager.Manager.reset_profile`) works fine. However, if a process is a run before closing it,
    for example running a calcfunction, the closing of the communicator will raise a ``TimeoutError``.
    """
    from aiida.manage import get_manager

    manager = get_manager()
    manager.get_communicator()
    manager.reset_profile()  # This returns just fine

    result, node = add_calcfunction.run_get_node(1)
    assert node.is_finished_ok
    assert result == 2
    manager.reset_profile()  # This hangs before timing out


def test_kernel_patch_not_applied_outside_notebook():
    """Test that ``_install_portal`` does not patch when no event loop is running."""
    from ipykernel.ipkernel import IPythonKernel

    from aiida.manage.manager import Manager

    manager = Manager()
    manager._install_portal()

    assert not getattr(IPythonKernel, '_aiida_portal_patched', False)
