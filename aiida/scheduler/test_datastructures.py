# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import unittest



class TestNodeNumberJobResource(unittest.TestCase):
    def test_init(self):
        """
        Test the __init__ of the NodeNumberJobResource class
        """
        from aiida.scheduler.datastructures import NodeNumberJobResource

        # No empty initialization
        with self.assertRaises(TypeError):
            _ = NodeNumberJobResource()

        # Missing required field
        with self.assertRaises(TypeError):
            _ = NodeNumberJobResource(num_machines=1)
        with self.assertRaises(TypeError):
            _ = NodeNumberJobResource(num_mpiprocs_per_machine=1)
        with self.assertRaises(TypeError):
            _ = NodeNumberJobResource(tot_num_mpiprocs=1)

        # Standard info
        jr = NodeNumberJobResource(num_machines=2, num_mpiprocs_per_machine=8)
        self.assertEquals(jr.num_machines, 2)
        self.assertEquals(jr.num_mpiprocs_per_machine, 8)
        self.assertEquals(jr.get_tot_num_mpiprocs(), 16)
        # redundant but consistent information
        jr = NodeNumberJobResource(num_machines=2, num_mpiprocs_per_machine=8, tot_num_mpiprocs=16)
        self.assertEquals(jr.num_machines, 2)
        self.assertEquals(jr.num_mpiprocs_per_machine, 8)
        self.assertEquals(jr.get_tot_num_mpiprocs(), 16)
        # other equivalent ways of specifying the information
        jr = NodeNumberJobResource(num_mpiprocs_per_machine=8, tot_num_mpiprocs=16)
        self.assertEquals(jr.num_machines, 2)
        self.assertEquals(jr.num_mpiprocs_per_machine, 8)
        self.assertEquals(jr.get_tot_num_mpiprocs(), 16)
        # other equivalent ways of specifying the information
        jr = NodeNumberJobResource(num_machines=2, tot_num_mpiprocs=16)
        self.assertEquals(jr.num_machines, 2)
        self.assertEquals(jr.num_mpiprocs_per_machine, 8)
        self.assertEquals(jr.get_tot_num_mpiprocs(), 16)

        # wrong field name
        with self.assertRaises(TypeError):
            _ = NodeNumberJobResource(num_machines=2, num_mpiprocs_per_machine=8, wrong_name=16)

        # Examples of wrong informaton (e.g., number of machines or of nodes < 0
        with self.assertRaises(ValueError):
            _ = NodeNumberJobResource(num_machines=0, num_mpiprocs_per_machine=8)
        with self.assertRaises(ValueError):
            _ = NodeNumberJobResource(num_machines=1, num_mpiprocs_per_machine=0)
        with self.assertRaises(ValueError):
            _ = NodeNumberJobResource(num_machines=1, tot_num_mpiprocs=0)
        with self.assertRaises(ValueError):
            _ = NodeNumberJobResource(num_mpiprocs_per_machine=1, tot_num_mpiprocs=0)

        # Examples of inconsistent information
        with self.assertRaises(ValueError):
            _ = NodeNumberJobResource(num_mpiprocs_per_machine=8, num_machines=2, tot_num_mpiprocs=32)

        with self.assertRaises(ValueError):
            _ = NodeNumberJobResource(num_mpiprocs_per_machine=8, tot_num_mpiprocs=15)
        
        