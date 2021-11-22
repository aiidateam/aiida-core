# -*- coding: utf-8 -*-
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

from aiida.common.warnings import AiidaDeprecationWarning
from aiida.plugins.entry_point import EntryPoint, get_entry_point, validate_registered_entry_points


def test_validate_registered_entry_points():
    """Test the ``validate_registered_entry_points`` function."""
    validate_registered_entry_points()


@pytest.mark.parametrize(
    'group, name', (
        ('aiida.calculations', 'arithmetic.add'),
        ('aiida.data', 'array'),
        ('aiida.tools.dbimporters', 'cod'),
        ('aiida.tools.data.orbitals', 'orbital'),
        ('aiida.parsers', 'arithmetic.add'),
        ('aiida.schedulers', 'direct'),
        ('aiida.transports', 'local'),
        ('aiida.workflows', 'arithmetic.multiply_add'),
    )
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
        entry_point = get_entry_point(group, name)

    assert isinstance(entry_point, EntryPoint)
