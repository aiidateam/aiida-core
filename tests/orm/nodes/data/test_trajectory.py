# -*- coding: utf-8 -*-
"""Tests for the `TrajectoryData` class."""

import numpy as np

from aiida.orm import TrajectoryData, load_node
from aiida.storage.testbase import AiidaTestCase


class TestTrajectory(AiidaTestCase):
    """Test for the `TrajectoryData` class."""

    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)

        n_atoms = 5
        n_steps = 30

        cls.symbols = [chr(_) for _ in range(ord('A'), ord('A') + n_atoms)]
        cls.positions = np.array(np.arange(n_steps * n_atoms * 3).reshape(n_steps, n_atoms, 3), dtype=float)

    def test_get_attribute_tryexcept_default(self):
        """
        Test whether the try_except statement on the get_attribute calls for units in
        the `show_mpl_*` functions except the correct exception type (for setting defaults).

        Added for PR #5015 (behavior of BackendEntityAttributesMixin.get_attribute changed
        to raise AttributeError instead of KeyError)
        """
        tjd = TrajectoryData()

        try:
            positions_unit = tjd.get_attribute('units|positions')
        except AttributeError:
            positions_unit = 'A'
        except KeyError:
            times_unit = 'FAILED_tryexc'
        self.assertEqual(positions_unit, 'A')

        try:
            times_unit = tjd.get_attribute('units|times')
        except AttributeError:
            times_unit = 'ps'
        except KeyError:
            times_unit = 'FAILED_tryexc'
        self.assertEqual(times_unit, 'ps')

        positions = 1
        try:
            if self.get_attribute('units|positions') in ('bohr', 'atomic'):
                bohr_to_ang = 0.52917720859
                positions *= bohr_to_ang
        except AttributeError:
            pass
        except KeyError:
            positions = 'FAILED_tryexc'
        self.assertEqual(positions, 1)

    def test_units(self):
        """Test the setting of units attributes."""
        tjd = TrajectoryData()

        tjd.set_attribute('units|positions', 'some_random_pos_unit')
        self.assertEqual(tjd.get_attribute('units|positions'), 'some_random_pos_unit')

        tjd.set_attribute('units|times', 'some_random_time_unit')
        self.assertEqual(tjd.get_attribute('units|times'), 'some_random_time_unit')

        # Test after storing
        tjd.set_trajectory(self.symbols, self.positions)
        tjd.store()
        tjd2 = load_node(tjd.pk)
        self.assertEqual(tjd2.get_attribute('units|positions'), 'some_random_pos_unit')
        self.assertEqual(tjd2.get_attribute('units|times'), 'some_random_time_unit')
