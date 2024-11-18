"""Fixtures that provide access to global singletons."""

import typing as t

import pytest

if t.TYPE_CHECKING:
    from aiida.manage.manager import Manager


@pytest.fixture(scope='session')
def aiida_manager() -> 'Manager':
    """Return the global :class:`~aiida.manage.manager.Manager` instance.

    :returns :class:`~aiida.manage.manager.Manager`: The global manager instance.
    """
    from aiida.manage import get_manager

    return get_manager()
