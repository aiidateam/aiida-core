# -*- coding: utf-8 -*-
# pylint: disable=no-self-use
"""Tests for the `TrajectoryData` class."""
import numpy as np
import pytest

from aiida.orm import TrajectoryData, load_node


class TestTrajectory:
    """Test for the `TrajectoryData` class."""

    @pytest.fixture(autouse=True)
    def init_profile(self, aiida_profile_clean, aiida_localhost):  # pylint: disable=unused-argument
        """Initialize the profile."""
        # pylint: disable=attribute-defined-outside-init

        n_atoms = 5
        n_steps = 30

        self.symbols = [chr(_) for _ in range(ord('A'), ord('A') + n_atoms)]
        self.positions = np.array(np.arange(n_steps * n_atoms * 3).reshape(n_steps, n_atoms, 3), dtype=float)

    def test_get_attribute_tryexcept_default(self):
        """
        Test whether the try_except statement on the get_attribute calls for units in
        the `show_mpl_*` functions except the correct exception type (for setting defaults).

        Added for PR #5015 (behavior of BackendEntityAttributes.get changed
        to raise AttributeError instead of KeyError)
        """
        tjd = TrajectoryData()

        try:
            positions_unit = tjd.base.attributes.get('units|positions')
        except AttributeError:
            positions_unit = 'A'
        except KeyError:
            times_unit = 'FAILED_tryexc'
        assert positions_unit == 'A'

        try:
            times_unit = tjd.base.attributes.get('units|times')
        except AttributeError:
            times_unit = 'ps'
        except KeyError:
            times_unit = 'FAILED_tryexc'
        assert times_unit == 'ps'

        positions = 1
        try:
            if self.base.attributes.get('units|positions') in ('bohr', 'atomic'):
                bohr_to_ang = 0.52917720859
                positions *= bohr_to_ang
        except AttributeError:
            pass
        except KeyError:
            positions = 'FAILED_tryexc'
        assert positions == 1

    def test_units(self):
        """Test the setting of units attributes."""
        tjd = TrajectoryData()

        tjd.base.attributes.set('units|positions', 'some_random_pos_unit')
        assert tjd.base.attributes.get('units|positions') == 'some_random_pos_unit'

        tjd.base.attributes.set('units|times', 'some_random_time_unit')
        assert tjd.base.attributes.get('units|times') == 'some_random_time_unit'

        # Test after storing
        tjd.set_trajectory(self.symbols, self.positions)
        tjd.store()
        tjd2 = load_node(tjd.pk)
        assert tjd2.base.attributes.get('units|positions') == 'some_random_pos_unit'
        assert tjd2.base.attributes.get('units|times') == 'some_random_time_unit'
