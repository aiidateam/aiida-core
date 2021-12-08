# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=redefined-outer-name
"""Tests for the :class:`aiida.orm.nodes.data.data:Data` class."""
import os

import numpy
import pytest

from aiida import orm, plugins
from tests.static import STATIC_DIR


@pytest.fixture
@pytest.mark.usefixtures('clear_database_before_test')
def generate_class_instance():
    """Generate a dummy `Data` instance for the given sub class."""

    def _generate_class_instance(data_class):
        if data_class is orm.CifData:
            instance = data_class(file=os.path.join(STATIC_DIR, 'data', 'Si.cif'))
            return instance

        if data_class is orm.UpfData:
            filename = os.path.join(STATIC_DIR, 'pseudos', 'Ba.pbesol-spn-rrkjus_psl.0.2.3-tot-pslib030.UPF')
            instance = data_class(file=filename)
            return instance

        if data_class is orm.StructureData:
            instance = orm.CifData(file=os.path.join(STATIC_DIR, 'data', 'Si.cif')).get_structure()
            return instance

        if data_class is orm.BandsData:
            kpoints = orm.KpointsData()
            kpoints.set_cell([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
            kpoints.set_kpoints([[0., 0., 0.], [0.1, 0.1, 0.1]])
            instance = data_class()
            instance.set_kpointsdata(kpoints)
            instance.set_bands([[1.0, 2.0], [3.0, 4.0]])
            return instance

        if data_class is orm.TrajectoryData:
            instance = data_class()
            stepids = numpy.array([60])
            times = stepids * 0.01
            cells = numpy.array([[[3., 0., 0.], [0., 3., 0.], [0., 0., 3.]]])
            positions = numpy.array([[[0., 0., 0.]]])
            instance.set_trajectory(stepids=stepids, cells=cells, symbols=['H'], positions=positions, times=times)
            return instance

        if data_class is orm.UpfData:
            filepath_base = os.path.abspath(os.path.join(STATIC_DIR, 'pseudos'))
            filepath_carbon = os.path.join(filepath_base, 'C_pbe_v1.2.uspp.F.UPF')
            instance = data_class(file=filepath_carbon)
            return instance

        raise RuntimeError(
            'no instance generator implemented for class `{}`. If you have added a `_prepare_*` method '
            'for this data class, add a generator of a dummy instance here'.format(data_class)
        )

    return _generate_class_instance


@pytest.fixture(scope='function', params=plugins.get_entry_points('aiida.data'))
def data_plugin(request):
    """Fixture that parametrizes over all the registered entry points of the ``aiida.data`` entry point group."""
    return request.param.load()


@pytest.mark.usefixtures('clear_database_before_test')
def test_constructor():
    """Test the constructor.

    Specifically, verify that the ``source`` attribute can be set through a keyword argument.
    """
    source = {'id': 1}
    node = orm.Data(source=source)
    assert isinstance(node, orm.Data)
    assert node.source == source


@pytest.mark.usefixtures('clear_database_before_test')
def test_data_exporters(data_plugin, generate_class_instance):
    """Verify that the return value of the export methods of all `Data` sub classes have the correct type.

    It should be a tuple where the first should be a byte string and the second a dictionary.
    """
    export_formats = data_plugin.get_export_formats()

    if not export_formats:
        return

    instance = generate_class_instance(data_plugin)

    for fileformat in export_formats:
        content, dictionary = instance._exportcontent(fileformat)  # pylint: disable=protected-access
        assert isinstance(content, bytes)
        assert isinstance(dictionary, dict)
