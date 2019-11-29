# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `OrbitalData` class."""

import copy
from aiida.backends.testbase import AiidaTestCase
from aiida.common import ValidationError
from aiida.orm import OrbitalData
from aiida.plugins import OrbitalFactory


class TestOrbitalData(AiidaTestCase):
    """Test for the `OrbitalData` class."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)

        cls.my_real_hydrogen_dict = {
            'angular_momentum': -3,
            'diffusivity': None,
            'kind_name': 'As',
            'magnetic_number': 0,
            'position': [-1.420047044832945, 1.420047044832945, 1.420047044832945],
            'radial_nodes': 0,
            'spin': 0,
            'spin_orientation': None,
            'x_orientation': None,
            'z_orientation': None
        }

    def test_real_hydrogen(self):
        """Tests storage of the RealHydrogen oribtal"""
        RealHydrogen = OrbitalFactory('realhydrogen')  # pylint: disable=invalid-name
        orbital = RealHydrogen(**self.my_real_hydrogen_dict)
        orbitaldata = OrbitalData()

        #Check that there is a failure if get_orbital is called for setting orbitals
        self.assertRaises(AttributeError, orbitaldata.get_orbitals)

        #Check that only one orbital has been assiigned
        orbitaldata.set_orbitals(orbitals=orbital)
        self.assertEqual(len(orbitaldata.get_orbitals()), 1)

        #Check the orbital dict has been assigned correctly
        retrieved_real_hydrogen_dict = orbitaldata.get_orbitals()[0].get_orbital_dict()
        self.assertEqual(retrieved_real_hydrogen_dict.pop('_orbital_type'), 'realhydrogen')
        self.assertDictEqual(retrieved_real_hydrogen_dict, self.my_real_hydrogen_dict)

        #Check that a corrupted OribtalData fails on get_orbitals
        corrupted_orbitaldata = copy.deepcopy(orbitaldata)
        del corrupted_orbitaldata.get_attribute('orbital_dicts')[0]['_orbital_type']
        self.assertRaises(ValidationError, corrupted_orbitaldata.get_orbitals)

        #Check that clear_orbitals empties the data of orbitals
        orbitaldata.clear_orbitals()
        self.assertEqual(len(orbitaldata.get_orbitals()), 0)


# verdi -p test_aiida devel tests db.orm.data.orbital
# coverage run `which verdi` -p test_aiida devel tests db.orm.data.orbital && coverage html
