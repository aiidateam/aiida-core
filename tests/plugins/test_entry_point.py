###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the :mod:`~aiida.plugins.entry_point` module."""

import pytest
from importlib_metadata import EntryPoint as EP  # noqa: N817
from importlib_metadata import EntryPoints

from aiida.common.exceptions import MissingEntryPointError, MultipleEntryPointError
from aiida.common.warnings import AiidaDeprecationWarning
from aiida.plugins import entry_point
from aiida.plugins.entry_point import get_entry_point, validate_registered_entry_points


def test_validate_registered_entry_points():
    """Test the ``validate_registered_entry_points`` function."""
    validate_registered_entry_points()


@pytest.mark.parametrize(
    'group, name',
    (
        ('aiida.calculations', 'arithmetic.add'),
        ('aiida.data', 'array'),
        ('aiida.tools.dbimporters', 'cod'),
        ('aiida.tools.data.orbitals', 'orbital'),
        ('aiida.parsers', 'arithmetic.add'),
        ('aiida.schedulers', 'direct'),
        ('aiida.transports', 'local'),
        ('aiida.workflows', 'arithmetic.multiply_add'),
    ),
)
def test_get_entry_point_deprecated(group, name):
    """Test the ``get_entry_point`` method for a deprecated entry point.

    The entry points in the parametrization were deprecated in ``aiida-core==2.0``. To provide a deprecation pathway,
    the ``get_entry_point`` method was patched to go through the factories, which would automatically load the new entry
    point and issue a deprecation warning. This is what we are testing here. This test can be removed once the
    deprecated entry points are removed in ``aiida-core==3.0``.
    """
    warning = f'The entry point `{name}` is deprecated. Please replace it with `core.{name}`.'

    with pytest.warns(AiidaDeprecationWarning, match=warning):
        get_entry_point(group, name)


@pytest.fixture
def eps(request):
    """Mocked version of :func:`aiida.plugins.entry_point.eps`.

    The mocked function returns a dummy class whose ``select`` method returns a fixed list of entry points that are
    passed in via the ``request`` parameter with which ``pytest`` invokes the fixture.
    """

    class MockEntryPoints:
        @staticmethod
        def select(group, name):
            return EntryPoints(request.param)

    return MockEntryPoints


@pytest.mark.parametrize(
    'eps, name, exception',
    (
        ((EP(name='ep', group='gr', value='x'),), 'ep', None),
        ((EP(name='ep', group='gr', value='x'),), 'non-existing', MissingEntryPointError),
        ((EP(name='ep', group='gr', value='x'), EP(name='ep', group='gr', value='y')), 'ep', MultipleEntryPointError),
        ((EP(name='ep', group='gr', value='x'), EP(name='ep', group='gr', value='x')), 'ep', None),
    ),
    indirect=['eps'],
)
def test_get_entry_point(eps, name, exception, monkeypatch):
    """Test the ``get_entry_point`` method.

    Test four different cases:

     * Requested entry point exists and no duplicates -> no exception
     * Requested entry points does not exist -> MissingEntryPointError
     * Requested entry point has two matches by name but hits have different values -> MultipleEntryPointError
     * Requested entry point has two matches by name but hits have same values -> no exception

    """
    monkeypatch.setattr(entry_point, 'eps', eps)
    entry_point.eps_select.cache_clear()

    if exception:
        with pytest.raises(exception):
            get_entry_point(group='gr', name=name)
    else:
        get_entry_point(group='gr', name=name)
