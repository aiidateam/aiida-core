# -*- coding: utf-8 -*-
# pylint: disable=redefined-outer-name
"""Tests for the :mod:`~aiida.orm.node.data.array.bands.electronic.ElectronicBandsData`."""
import numpy
import pytest

from aiida.common.exceptions import ModificationNotAllowed
from aiida.orm.nodes.data.array.kpoints import KpointsData
from aiida.orm.nodes.data.array.bands.electronic import ElectronicBandsData


@pytest.fixture
def bands():
    """Return a numpy array with arbitrary bands data."""
    return numpy.array([[0, 1], [1, 1]])


@pytest.fixture
def kpoints():
    """Return a numpy array with arbitrary bands data."""
    kpoints = KpointsData()
    kpoints.set_kpoints([[0., 0., 0.], [0.1, 0.1, 0.1]])
    return kpoints


@pytest.mark.usefixtures('clear_database_before_test')
def test_constructor(kpoints, bands):
    """Test the constructor."""
    node = ElectronicBandsData(kpoints, bands)
    assert isinstance(node, ElectronicBandsData)
    assert not node.is_stored

    fermi_level = 2.3
    node = ElectronicBandsData(kpoints, bands, fermi_level)
    assert isinstance(node, ElectronicBandsData)
    assert not node.is_stored
    assert node.fermi_level == fermi_level


@pytest.mark.usefixtures('clear_database_before_test')
def test_store(kpoints, bands):
    """Test storing an instance."""
    node = ElectronicBandsData(kpoints, bands)
    node.store()
    assert isinstance(node, ElectronicBandsData)
    assert node.is_stored


@pytest.mark.usefixtures('clear_database_before_test')
def test_fermi_level(kpoints, bands):
    """Test the ``fermi_level`` property."""
    node = ElectronicBandsData(kpoints, bands)
    assert node.fermi_level is None

    fermi_level = 2.3
    node.fermi_level = fermi_level
    assert node.fermi_level == fermi_level

    node.store()
    assert node.is_stored

    with pytest.raises(ModificationNotAllowed):
        node.fermi_level = 1.0
