# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the `TrajectoryData` class."""

import numpy as np
import pytest

from aiida.backends.testbase import AiidaTestCase
from aiida.orm import TrajectoryData, StructureData


class TestTrajectoryData(AiidaTestCase):
    """Test for the `TrajectoryData` class."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.symbols = ['H'] * 5 + ['Cl'] * 5
        cls.stepids = np.arange(1000, 3000, 10)
        cls.times = cls.stepids * 0.01
        cls.positions = np.arange(6000, dtype=float).reshape((200, 10, 3))
        cls.velocities = -np.arange(6000, dtype=float).reshape((200, 10, 3))
        cls.cells = np.array([[[3., 0.1, 0.3], [-0.05, 3., -0.2], [0.02, -0.08, 3.]]] * 200
                             ) + np.arange(0, 0.2, 0.001)[:, np.newaxis, np.newaxis]

    def test_trajectory_get_index_from_stepid(self):
        """Test the `get_index_from_stepid` method."""
        traj = TrajectoryData()
        traj.set_trajectory(
            symbols=self.symbols,
            positions=self.positions,
            stepids=self.stepids,
            cells=self.cells,
            times=self.times,
            velocities=self.velocities
        )

        index = traj.get_index_from_stepid(1050)
        self.assertEqual(index, 5)

        with pytest.raises(ValueError):
            index = traj.get_index_from_stepid(2333)

    def test_trajectory_get_step_data(self):
        """Test the `get_step_data` method."""
        traj = TrajectoryData()
        traj.set_trajectory(
            symbols=self.symbols,
            positions=self.positions,
            stepids=self.stepids,
            cells=self.cells,
            times=self.times,
            velocities=self.velocities
        )

        stepid, time, cell, symbols, positions, velocities = traj.get_step_data(-2)
        self.assertEqual(stepid, self.stepids[-2])
        self.assertEqual(time, self.times[-2])
        self.assertListEqual(cell.tolist(), self.cells[-2, :, :].tolist())
        self.assertListEqual(symbols, self.symbols)
        self.assertListEqual(positions.tolist(), self.positions[-2, :, :].tolist())
        self.assertListEqual(velocities.tolist(), self.velocities[-2, :, :].tolist())

    def test_trajectory_get_step_data_empty(self):
        """Test the `get_step_data` method when some arrays are not defined."""
        traj = TrajectoryData()
        traj.set_trajectory(symbols=self.symbols, positions=self.positions)

        stepid, time, cell, symbols, positions, velocities = traj.get_step_data(3)
        self.assertEqual(stepid, 3)
        self.assertEqual(time, None)
        self.assertEqual(cell, None)
        self.assertListEqual(symbols, self.symbols)
        self.assertListEqual(positions.tolist(), self.positions[3, :, :].tolist())
        self.assertEqual(velocities, None)

    def test_trajectory_get_step_structure(self):
        """Test the `get_step_structure` method."""
        traj = TrajectoryData()
        traj.set_trajectory(
            symbols=self.symbols,
            positions=self.positions,
            stepids=self.stepids,
            cells=self.cells,
            times=self.times,
            velocities=self.velocities
        )

        structure = traj.get_step_structure(50)
        # is there a better way to compare StructureData nodes?
        self.assertIsInstance(structure, StructureData)
        self.assertListEqual(structure.cell, self.cells[50, :, :].tolist())
        for site, kind, pos in zip(structure.sites, self.symbols, self.positions[50, :, :]):
            # note: this may depend on the ordering of the sites
            self.assertEqual(site.kind_name, kind)
            self.assertListEqual(list(site.position), pos.tolist())

        with pytest.raises(IndexError):
            structure = traj.get_step_structure(500)

    def test_trajectory_get_step_structure_nocell(self):
        """Test the `get_step_structure` method when custom_cell is specified."""
        traj = TrajectoryData()
        traj.set_trajectory(
            symbols=self.symbols,
            positions=self.positions,
            stepids=self.stepids,
            times=self.times,
            velocities=self.velocities
        )

        custom_cell = np.array([[5., 0., 0.], [0., 5., 0.], [0., 0., 5.]])
        structure = traj.get_step_structure(50, custom_cell=custom_cell)
        # is there a better way to compare StructureData nodes?
        self.assertIsInstance(structure, StructureData)
        self.assertListEqual(structure.cell, custom_cell.tolist())
        for site, kind, pos in zip(structure.sites, self.symbols, self.positions[50, :, :]):
            # note: this may depend on the ordering of the sites
            self.assertEqual(site.kind_name, kind)
            self.assertListEqual(list(site.position), pos.tolist())

        with pytest.raises(IndexError):
            structure = traj.get_step_structure(500)

        # check that cell is overridden even if present in the trajectory
        traj = TrajectoryData()
        traj.set_trajectory(
            symbols=self.symbols,
            positions=self.positions,
            cells=self.cells,
            stepids=self.stepids,
            times=self.times,
            velocities=self.velocities
        )

        custom_cell = np.array([[5., 0., 0.], [0., 5., 0.], [0., 0., 5.]])
        structure = traj.get_step_structure(50, custom_cell=custom_cell)
        self.assertListEqual(structure.cell, custom_cell.tolist())
