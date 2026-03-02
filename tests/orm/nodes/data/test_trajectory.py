"""Tests for the `TrajectoryData` class."""

import numpy as np
import pytest

from aiida.common.warnings import AiidaDeprecationWarning
from aiida.orm import StructureData, TrajectoryData, load_node


@pytest.fixture
def trajectory_data():
    """Return a dictionary of data to create a ``TrajectoryData``."""
    symbols = ['H'] * 5 + ['Cl'] * 5
    pbc = [True, True, True]
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
        'pbc': pbc,
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
        assert np.array_equal(cell, trajectory_data['cells'][-2, :, :])
        assert np.array_equal(symbols, trajectory_data['symbols'])
        assert np.array_equal(trajectory.pbc, trajectory_data['pbc'])
        assert np.array_equal(positions, trajectory_data['positions'][-2, :, :])
        assert np.array_equal(velocities, trajectory_data['velocities'][-2, :, :])

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
        assert trajectory.pbc == (False, False, False), 'Trajectory without a cell should not have PBC set'

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

    def test_trajectory_pbc_structures(self, trajectory_data):
        """Test the `pbc` for the `TrajectoryData` using structure inputs."""
        # Test non-pbc structure with no cell
        structure = StructureData(cell=None, pbc=[False, False, False])
        structure.append_atom(position=[0.0, 0.0, 0.0], symbols='H')

        trajectory = TrajectoryData(structurelist=(structure,))

        trajectory.get_step_structure(0).store()  # Verify that the `StructureData` can be stored
        assert trajectory.get_step_structure(0).pbc == structure.pbc

        # Test failure for incorrect pbc
        trajectory_data_incorrect = trajectory_data.copy()
        trajectory_data_incorrect['pbc'] = [0, 0, 0]
        with pytest.raises(ValueError, match='`pbc` must be a list/tuple of length three with boolean values'):
            trajectory = TrajectoryData()
            trajectory.set_trajectory(**trajectory_data_incorrect)

        # Test failure when structures have different pbc
        cell = [[3.0, 0.1, 0.3], [-0.05, 3.0, -0.2], [0.02, -0.08, 3.0]]
        structure_periodic = StructureData(cell=cell)
        structure_periodic.append_atom(position=[0.0, 0.0, 0.0], symbols='H')
        structure_non_periodic = StructureData(cell=cell, pbc=[False, False, False])
        structure_non_periodic.append_atom(position=[0.0, 0.0, 0.0], symbols='H')

        with pytest.raises(ValueError, match='All structures should have the same `pbc`'):
            TrajectoryData(structurelist=(structure_periodic, structure_non_periodic))

    def test_trajectory_pbc_set_trajectory(self):
        """Test the `pbc` for the `TrajectoryData` using `set_trajectory`."""
        data = {
            'symbols': ['H'],
            'positions': np.array(
                [
                    [
                        [0.0, 0.0, 0.0],
                    ]
                ]
            ),
        }
        trajectory = TrajectoryData()

        data.update(
            {
                'cells': None,
                'pbc': None,
            }
        )
        trajectory.set_trajectory(**data)
        assert trajectory.get_step_structure(0).pbc == (False, False, False)

        data.update(
            {
                'cells': None,
                'pbc': [False, False, False],
            }
        )
        trajectory.set_trajectory(**data)
        assert trajectory.get_step_structure(0).pbc == (False, False, False)

        data.update(
            {
                'cells': None,
                'pbc': [True, False, False],
            }
        )
        with pytest.raises(ValueError, match='Periodic boundary conditions are only possible when a cell is defined'):
            trajectory.set_trajectory(**data)

        data.update(
            {
                'cells': np.array([[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]]),
                'pbc': None,
            }
        )
        with pytest.warns(AiidaDeprecationWarning, match="When 'cells' is not None, the periodic"):
            trajectory.set_trajectory(**data)

        data.update(
            {
                'cells': np.array([[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]]),
                'pbc': (True, False, False),
            }
        )
        trajectory.set_trajectory(**data)
        assert trajectory.get_step_structure(0).pbc == (True, False, False)

    def test_trajectory_without_pbc(self, trajectory_data):
        """Test old `TrajectoryData` that do not have the `pbc` attribute."""
        trajectory = TrajectoryData()
        trajectory.set_trajectory(**trajectory_data)
        trajectory.base.attributes.delete('pbc')  # Emulate an old TrajectoryData without pbc

        assert trajectory.pbc is None
        structure = trajectory.get_step_structure(0)
        assert structure.pbc == (True, True, True)
