# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `Data` base class."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import numpy

from aiida import orm
from aiida.backends.testbase import AiidaTestCase


class TestData(AiidaTestCase):
    """Test for the `Data` base class."""

    @staticmethod
    def generate_class_instance(data_class):
        """Generate a dummy `Data` instance for the given sub class."""
        dirpath_fixtures = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'fixtures'))
        if data_class is orm.CifData:
            instance = data_class(file=os.path.join(dirpath_fixtures, 'data', 'Si.cif'))
            return instance

        if data_class is orm.StructureData:
            instance = orm.CifData(file=os.path.join(dirpath_fixtures, 'data', 'Si.cif')).get_structure()
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

        raise RuntimeError(
            'no instance generator implemented for class `{}`. If you have added a `_prepare_*` method '
            'for this data class, add a generator of a dummy instance here'.format(data_class)
        )

    def test_data_exporters(self):
        """Verify that the return value of the export methods of all `Data` sub classes have the correct type.

        It should be a tuple where the first should be a byte string and the second a dictionary.
        """
        from aiida.plugins.entry_point import get_entry_points

        for entry_point in get_entry_points('aiida.data'):

            data_class = entry_point.load()
            export_formats = data_class.get_export_formats()

            if not export_formats:
                continue

            instance = self.generate_class_instance(data_class)

            for fileformat in export_formats:
                content, dictionary = instance._exportcontent(fileformat)  # pylint: disable=protected-access
                self.assertIsInstance(content, bytes)
                self.assertIsInstance(dictionary, dict)
