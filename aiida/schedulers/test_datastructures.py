# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Datastructures test
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import unittest


class TestNodeNumberJobResource(unittest.TestCase):
    """Unit tests for the NodeNumberJobResource class."""

    def test_init(self):
        """
        Test the __init__ of the NodeNumberJobResource class
        """
        from aiida.schedulers.datastructures import NodeNumberJobResource

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
        job_resource = NodeNumberJobResource(num_machines=2, num_mpiprocs_per_machine=8)
        self.assertEqual(job_resource.num_machines, 2)
        self.assertEqual(job_resource.num_mpiprocs_per_machine, 8)
        self.assertEqual(job_resource.get_tot_num_mpiprocs(), 16)
        # redundant but consistent information
        job_resource = NodeNumberJobResource(num_machines=2, num_mpiprocs_per_machine=8, tot_num_mpiprocs=16)
        self.assertEqual(job_resource.num_machines, 2)
        self.assertEqual(job_resource.num_mpiprocs_per_machine, 8)
        self.assertEqual(job_resource.get_tot_num_mpiprocs(), 16)
        # other equivalent ways of specifying the information
        job_resource = NodeNumberJobResource(num_mpiprocs_per_machine=8, tot_num_mpiprocs=16)
        self.assertEqual(job_resource.num_machines, 2)
        self.assertEqual(job_resource.num_mpiprocs_per_machine, 8)
        self.assertEqual(job_resource.get_tot_num_mpiprocs(), 16)
        # other equivalent ways of specifying the information
        job_resource = NodeNumberJobResource(num_machines=2, tot_num_mpiprocs=16)
        self.assertEqual(job_resource.num_machines, 2)
        self.assertEqual(job_resource.num_mpiprocs_per_machine, 8)
        self.assertEqual(job_resource.get_tot_num_mpiprocs(), 16)

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
