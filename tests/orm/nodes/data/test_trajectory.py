"""Tests for the `TrajectoryData` class."""

import numpy as np
import pytest

from aiida.orm import StructureData, TrajectoryData, load_node


@pytest.fixture
def trajectory_data():
    """Return a dictionary of data to create a ``TrajectoryData``."""
    symbols = ['H'] * 5 + ['Cl'] * 5
    stepids = np.arange(1000, 3000, 10)
    times = stepids * 0.01
    positions = np.arange(6000, dtype=float).reshape((200, 10, 3))
    velocities = -np.arange(6000, dtype=float).reshape((200, 10, 3))
    cell = [[[3.0, 0.1, 0.3], [-0.05, 3.0, -0.2], [0.02, -0.08, 3.0]]]
    cells = np.array(cell * 200) + np.arange(0, 0.2, 0.001)[:, np.newaxis, np.newaxis]
    return {
        'symbols': symbols,
        'positions': positions,
        'stepids': stepids,
        'cells': cells,
        'times': times,
        'velocities': velocities,
    }


class TestTrajectory:
    """Test for the `TrajectoryData` class."""

    @pytest.fixture(autouse=True)
    def init_profile(self):
        """Initialize the profile."""
        n_atoms = 5
        n_steps = 30

        self.symbols = [chr(_) for _ in range(ord('A'), ord('A') + n_atoms)]
        self.positions = np.array(np.arange(n_steps * n_atoms * 3).reshape(n_steps, n_atoms, 3), dtype=float)

    def test_get_attribute_tryexcept_default(self):
        """Test whether the try_except statement on the get_attribute calls for units in
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

    def test_trajectory_get_index_from_stepid(self, trajectory_data):
        """Test the ``get_index_from_stepid`` method."""
        trajectory = TrajectoryData()
        trajectory.set_trajectory(**trajectory_data)
        assert trajectory.get_index_from_stepid(1050) == 5

        with pytest.raises(ValueError):
            trajectory.get_index_from_stepid(2333)

    def test_trajectory_get_step_data(self, trajectory_data):
        """Test the ``get_step_data`` method."""
        trajectory = TrajectoryData()
        trajectory.set_trajectory(**trajectory_data)
        stepid, time, cell, symbols, positions, velocities = trajectory.get_step_data(-2)
        assert stepid == trajectory_data['stepids'][-2]
        assert time == trajectory_data['times'][-2]
        np.array_equal(cell, trajectory_data['cells'][-2, :, :])
        np.array_equal(symbols, trajectory_data['symbols'])
        np.array_equal(positions, trajectory_data['positions'][-2, :, :])
        np.array_equal(velocities, trajectory_data['velocities'][-2, :, :])

    def test_trajectory_get_step_data_empty(self, trajectory_data):
        """Test the `get_step_data` method when some arrays are not defined."""
        trajectory = TrajectoryData()
        trajectory.set_trajectory(symbols=trajectory_data['symbols'], positions=trajectory_data['positions'])
        stepid, time, cell, symbols, positions, velocities = trajectory.get_step_data(3)
        assert stepid == 3
        assert time is None
        assert cell is None
        assert np.array_equal(symbols, trajectory_data['symbols'])
        assert np.array_equal(positions, trajectory_data['positions'][3, :, :])
        assert velocities is None

    def test_trajectory_get_step_structure(self, trajectory_data):
        """Test the `get_step_structure` method."""
        trajectory = TrajectoryData()
        trajectory.set_trajectory(**trajectory_data)
        structure = trajectory.get_step_structure(50)

        expected = StructureData()
        expected.cell = trajectory_data['cells'][50]
        for symbol, position in zip(trajectory_data['symbols'], trajectory_data['positions'][50, :, :]):
            expected.append_atom(symbols=symbol, position=position)

        structure.store()
        expected.store()
        assert structure.base.caching.get_hash() == expected.base.caching.get_hash()

        with pytest.raises(IndexError):
            trajectory.get_step_structure(500)
