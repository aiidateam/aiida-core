###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""AiiDA class to deal with crystal structure trajectories."""

from __future__ import annotations

import collections.abc
from typing import TYPE_CHECKING, List, Optional

import numpy as np

from aiida.common.pydantic import MetadataField

from .array import ArrayData

if TYPE_CHECKING:
    from aiida import orm

__all__ = ('TrajectoryData',)


class TrajectoryData(ArrayData):
    """Stores a trajectory (a sequence of crystal structures with timestamps, and
    possibly with velocities).
    """

    class Model(ArrayData.Model):
        units_positions: Optional[str] = MetadataField(
            None,
            serialization_alias='units|positions',
            description='Unit of positions',
        )
        units_times: Optional[str] = MetadataField(
            None,
            serialization_alias='units|times',
            description='Unit of time',
        )
        symbols: List[str] = MetadataField(description='List of symbols')

    def __init__(
        self,
        structurelist: list[orm.StructureData] | None = None,
        units_positions: str | None = None,
        units_times: str | None = None,
        symbols: list[str] | None = None,
        arrays: np.ndarray | dict[str, np.ndarray] | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.unit_positions = units_positions
        self.unit_times = units_times
        if structurelist is not None:
            self.set_structurelist(structurelist)
        elif arrays is not None:
            self.set_trajectory(
                symbols=symbols,
                positions=arrays['positions'],
                stepids=arrays.get('steps'),
                cells=arrays.get('cells'),
                times=arrays.get('times'),
                velocities=arrays.get('velocities'),
            )

    def _internal_validate(self, stepids, cells, symbols, positions, times, velocities):
        """Internal function to validate the type and shape of the arrays. See
        the documentation of py:meth:`.set_trajectory` for a description of the
        valid shape and type of the parameters.
        """
        import numpy

        if not isinstance(symbols, collections.abc.Iterable):
            raise TypeError('TrajectoryData.symbols must be of type list')
        if any(not isinstance(i, str) for i in symbols):
            raise TypeError('TrajectoryData.symbols must be a 1d list of strings')
        if not isinstance(positions, numpy.ndarray) or positions.dtype != float:
            raise TypeError('TrajectoryData.positions must be a numpy array of floats')
        if stepids is not None:
            if not isinstance(stepids, numpy.ndarray) or stepids.dtype != int:
                raise TypeError('TrajectoryData.stepids must be a numpy array of integers')
        if cells is not None:
            if not isinstance(cells, numpy.ndarray) or cells.dtype != float:
                raise TypeError('TrajectoryData.cells must be a numpy array of floats')
        if times is not None:
            if not isinstance(times, numpy.ndarray) or times.dtype != float:
                raise TypeError('TrajectoryData.times must be a numpy array of floats')
        if velocities is not None:
            if not isinstance(velocities, numpy.ndarray) or velocities.dtype != float:
                raise TypeError('TrajectoryData.velocities must be a numpy array of floats, or None')
        if stepids is not None:
            numsteps = stepids.size
            if stepids.shape != (numsteps,):
                raise ValueError('TrajectoryData.stepids must be a 1d array')
        else:
            numsteps = positions.shape[0]
        if cells is not None:
            if cells.shape != (numsteps, 3, 3):
                raise ValueError('TrajectoryData.cells must have shape (s,3,3), with s=number of steps')
        numatoms = len(symbols)
        if positions.shape != (numsteps, numatoms, 3):
            raise ValueError(
                'TrajectoryData.positions must have shape (s,n,3), ' 'with s=number of steps and n=number of symbols'
            )
        if times is not None:
            if times.shape != (numsteps,):
                raise ValueError('TrajectoryData.times must have shape (s,), with s=number of steps')
        if velocities is not None:
            if velocities.shape != (numsteps, numatoms, 3):
                raise ValueError(
                    'TrajectoryData.velocities, if not None, must '
                    'have shape (s,n,3), '
                    'with s=number of steps and n=number of symbols'
                )

    def set_trajectory(self, symbols, positions, stepids=None, cells=None, times=None, velocities=None):
        r"""Store the whole trajectory, after checking that types and dimensions
        are correct.

        Parameters ``stepids``, ``cells`` and ``velocities`` are optional
        variables. If nothing is passed for ``cells`` or ``velocities``
        nothing will be stored. However, if no input is given for ``stepids``
        a consecutive sequence [0,1,2,...,len(positions)-1] will be assumed.


        :param symbols: string list with dimension ``n``, where ``n`` is the
                      number of atoms (i.e., sites) in the structure.
                      The same list is used for each step. Normally, the string
                      should be a valid chemical symbol, but actually any unique
                      string works and can be used as the name of the atomic kind
                      (see also the :py:meth:`.get_step_structure()` method).
        :param positions: float array with dimension :math:`s \times n \times 3`,
                      where ``s`` is the
                      length of the ``stepids`` array and ``n`` is the length
                      of the ``symbols`` array. Units are angstrom.
                      In particular,
                      ``positions[i,j,k]`` is the ``k``-th component of the
                      ``j``-th atom (or site) in the structure at the time step
                      with index ``i`` (identified
                      by step number ``step[i]`` and with timestamp ``times[i]``).
        :param stepids: integer array with dimension ``s``, where ``s`` is the
                      number of steps. Typically represents an internal counter
                      within the code. For instance, if you want to store a
                      trajectory with one step every 10, starting from step 65,
                      the array will be ``[65,75,85,...]``.
                      No checks are done on duplicate elements
                      or on the ordering, but anyway this array should be
                      sorted in ascending order, without duplicate elements.
                      (If not specified, stepids will be set to ``numpy.arange(s)``
                      by default) It is internally stored as an array named 'steps'.
        :param cells: if specified float array with dimension
                      :math:`s \times 3 \times 3`, where ``s`` is the
                      length of the ``stepids`` array. Units are angstrom.
                      In particular, ``cells[i,j,k]`` is the ``k``-th component
                      of the ``j``-th cell vector at the time step with index
                      ``i`` (identified by step number ``stepid[i]`` and with
                      timestamp ``times[i]``).
        :param times: if specified, float array with dimension ``s``, where
                      ``s`` is the length of the ``stepids`` array. Contains the
                      timestamp of each step in picoseconds (ps).
        :param velocities: if specified, must be a float array with the same
                      dimensions of the ``positions`` array.
                      The array contains the velocities in the atoms.

        .. todo :: Choose suitable units for velocities
        """
        import numpy

        self._internal_validate(stepids, cells, symbols, positions, times, velocities)
        # set symbols as attribute for easier querying
        self.base.attributes.set('symbols', list(symbols))
        self.set_array('positions', positions)
        if stepids is not None:  # use input stepids
            self.set_array('steps', stepids)
        else:  # use consecutive sequence if not given
            self.set_array('steps', numpy.arange(positions.shape[0]))
        if cells is not None:
            self.set_array('cells', cells)
        else:
            # Delete cells array, if it was present
            try:
                self.delete_array('cells')
            except KeyError:
                pass
        if times is not None:
            self.set_array('times', times)
        else:
            # Delete times array, if it was present
            try:
                self.delete_array('times')
            except KeyError:
                pass
        if velocities is not None:
            self.set_array('velocities', velocities)
        else:
            # Delete velocities array, if it was present
            try:
                self.delete_array('velocities')
            except KeyError:
                pass

    def set_structurelist(self, structurelist):
        """Create trajectory from the list of
        :py:class:`aiida.orm.nodes.data.structure.StructureData` instances.

        :param structurelist: a list of
            :py:class:`aiida.orm.nodes.data.structure.StructureData` instances.

        :raises ValueError: if symbol lists of supplied structures are
            different
        """
        import numpy

        stepids = numpy.arange(len(structurelist))
        cells = numpy.array([x.cell for x in structurelist])
        symbols_first = [str(s.kind_name) for s in structurelist[0].sites]
        for symbols_now in [[str(s.kind_name) for s in structurelist[i].sites] for i in stepids]:
            if symbols_first != symbols_now:
                raise ValueError('Symbol lists have to be the same for all of the supplied structures')
        symbols = list(symbols_first)
        positions = numpy.array([[list(s.position) for s in x.sites] for x in structurelist])
        self.set_trajectory(stepids=stepids, cells=cells, symbols=symbols, positions=positions)

    def _validate(self):
        """Verify that the required arrays are present and that their type and
        dimension are correct.
        """
        # check dimensions, types
        from aiida.common.exceptions import ValidationError

        try:
            self._internal_validate(
                self.get_stepids(),
                self.get_cells(),
                self.symbols,
                self.get_positions(),
                self.get_times(),
                self.get_velocities(),
            )
        # Should catch TypeErrors, ValueErrors, and KeyErrors for missing arrays
        except Exception as exception:
            raise ValidationError(
                f'The TrajectoryData did not validate. Error: {type(exception).__name__} with message {exception}'
            )

    @property
    def numsteps(self):
        """Return the number of stored steps, or zero if nothing has been stored yet."""
        try:
            return self.get_shape('steps')[0]
        except (AttributeError, KeyError, IndexError):
            return 0

    @property
    def numsites(self):
        """Return the number of stored sites, or zero if nothing has been stored yet."""
        try:
            return len(self.symbols)
        except (AttributeError, KeyError, IndexError):
            return 0

    def get_stepids(self):
        """Return the array of steps, if it has already been set.

        :raises KeyError: if the trajectory has not been set yet.
        """
        return self.get_array('steps')

    def get_times(self):
        """Return the array of times (in ps), if it has already been set.

        :raises KeyError: if the trajectory has not been set yet.
        """
        try:
            return self.get_array('times')
        except (AttributeError, KeyError):
            return None

    def get_cells(self):
        """Return the array of cells, if it has already been set.

        :raises KeyError: if the trajectory has not been set yet.
        """
        try:
            return self.get_array('cells')
        except (AttributeError, KeyError):
            return None

    @property
    def units_positions(self) -> str | None:
        """Units for the positions array."""
        return self.base.attributes.get('units|positions', None)

    @units_positions.setter
    def units_positions(self, units: str) -> None:
        """Set units for the positions array."""
        self.base.attributes.set('units|positions', units)

    @property
    def units_times(self) -> str | None:
        """Units for the times array."""
        return self.base.attributes.get('units|times', None)

    @units_times.setter
    def units_times(self, units: str) -> None:
        """Set units for the times array."""
        self.base.attributes.set('units|times', units)

    @property
    def symbols(self) -> List[str]:
        """Return the array of symbols, if it has already been set.

        :raises KeyError: if the trajectory has not been set yet.
        """
        return self.base.attributes.get('symbols')

    def get_positions(self):
        """Return the array of positions, if it has already been set.

        :raises KeyError: if the trajectory has not been set yet.
        """
        return self.get_array('positions')

    def get_velocities(self):
        """Return the array of velocities, if it has already been set.

        .. note :: This function (differently from all other ``get_*``
          functions, will not raise an exception if the velocities are not
          set, but rather return ``None`` (both if no trajectory was not set yet,
          and if it the trajectory was set but no velocities were specified).
        """
        try:
            return self.get_array('velocities')
        except (AttributeError, KeyError):
            return None

    def get_index_from_stepid(self, stepid):
        """Given a value for the stepid (i.e., a value among those of the ``steps``
        array), return the array index of that stepid, that can be used in other
        methods such as :py:meth:`.get_step_data` or
        :py:meth:`.get_step_structure`.

        .. note:: Note that this function returns the first index found
            (i.e. if multiple steps are present with the same value,
            only the index of the first one is returned).

        :raises ValueError: if no step with the given value is found.
        """
        import numpy

        try:
            return numpy.where(self.get_stepids() == stepid)[0][0]
        except IndexError:
            raise ValueError(f'{stepid} not among the stepids')

    def get_step_data(self, index):
        """Return a tuple with all information concerning the stepid with given
        index (0 is the first step, 1 the second step and so on). If you know
        only the step value, use the :py:meth:`.get_index_from_stepid` method
        to get the corresponding index.

        If no velocities, cells, or times were specified, None is returned as
        the corresponding element.

        :return: A tuple in the format
          ``(stepid, time, cell, symbols, positions, velocities)``,
          where ``stepid`` is an integer, ``time`` is a float, ``cell`` is a
          :math:`3 \times 3` matrix, ``symbols`` is an array of length ``n``,
          positions is a :math:`n \times 3` array, and velocities is either
          ``None`` or a :math:`n \times 3` array

        :param index: The index of the step that you want to retrieve, from
           0 to ``self.numsteps - 1``.
        :raises IndexError: if you require an index beyond the limits.
        :raises KeyError: if you did not store the trajectory yet.
        """
        if index >= self.numsteps:
            raise IndexError(f'You have only {self.numsteps} steps, but you are looking beyond (index={index})')

        vel = self.get_velocities()
        if vel is not None:
            vel = vel[index, :, :]
        time = self.get_times()
        if time is not None:
            time = time[index]
        cells = self.get_cells()
        if cells is not None:
            cell = cells[index, :, :]
        else:
            cell = None
        return (self.get_stepids()[index], time, cell, self.symbols, self.get_positions()[index, :, :], vel)

    def get_step_structure(self, index, custom_kinds=None):
        """Return an AiiDA :py:class:`aiida.orm.nodes.data.structure.StructureData` node
        (not stored yet!) with the coordinates of the given step, identified by
        its index. If you know only the step value, use the
        :py:meth:`.get_index_from_stepid` method to get the corresponding index.

        .. note:: The periodic boundary conditions are always set to True.

        :param index: The index of the step that you want to retrieve, from
           0 to ``self.numsteps- 1``.
        :param custom_kinds: (Optional) If passed must be a list of
          :py:class:`aiida.orm.nodes.data.structure.Kind` objects. There must be one
          kind object for each different string in the ``symbols`` array, with
          ``kind.name`` set to this string.
          If this parameter is omitted, the automatic kind generation of AiiDA
          :py:class:`aiida.orm.nodes.data.structure.StructureData` nodes is used,
          meaning that the strings in the ``symbols`` array must be valid
          chemical symbols.

        :return: :py:class:`aiida.orm.nodes.data.structure.StructureData` node.
        """
        from aiida.orm.nodes.data.structure import Kind, Site, StructureData

        # ignore step, time, and velocities
        _, _, cell, symbols, positions, _ = self.get_step_data(index)

        if custom_kinds is not None:
            kind_names = []
            for k in custom_kinds:
                if not isinstance(k, Kind):
                    raise TypeError(
                        'Each element of the custom_kinds list must ' 'be a aiida.orm.nodes.data.structure.Kind object'
                    )
                kind_names.append(k.name)
            if len(kind_names) != len(set(kind_names)):
                raise ValueError('Multiple kinds with the same name passed as custom_kinds')
            if set(kind_names) != set(symbols):
                raise ValueError(
                    'If you pass custom_kinds, you have to '
                    'pass one Kind object for each symbol '
                    'that is present in the trajectory. You '
                    'passed {}, but the symbols are {}'.format(sorted(kind_names), sorted(symbols))
                )

        struc = StructureData(cell=cell)
        if custom_kinds is not None:
            for _k in custom_kinds:
                struc.append_kind(_k)
            for _s, _p in zip(symbols, positions):
                struc.append_site(Site(kind_name=_s, position=_p))
        else:
            for _s, _p in zip(symbols, positions):
                # Automatic species generation
                struc.append_atom(symbols=_s, position=_p)

        return struc

    def _prepare_xsf(self, index=None, main_file_name=''):
        """Write the given trajectory to a string of format XSF (for XCrySDen)."""
        from aiida.common.constants import elements

        _atomic_numbers = {data['symbol']: num for num, data in elements.items()}

        indices = list(range(self.numsteps))
        if index is not None:
            indices = [index]
        return_string = f'ANIMSTEPS {len(indices)}\nCRYSTAL\n'
        # Do the checks once and for all here:
        structure = self.get_step_structure(index=0)
        if structure.is_alloy or structure.has_vacancies:
            raise NotImplementedError('XSF for alloys or systems with vacancies not implemented.')
        cells = self.get_cells()
        if cells is None:
            raise ValueError('No cell parameters have been supplied for TrajectoryData')
        positions = self.get_positions()
        symbols = self.symbols
        atomic_numbers_list = [_atomic_numbers[s] for s in symbols]
        nat = len(symbols)

        for idx in indices:
            return_string += f'PRIMVEC {idx + 1}\n'
            for cell_vector in cells[idx]:
                return_string += ' '.join([f'{i:18.5f}' for i in cell_vector])
                return_string += '\n'
            return_string += f'PRIMCOORD {idx + 1}\n'
            return_string += f'{nat} 1\n'
            for atn, pos in zip(atomic_numbers_list, positions[idx]):
                try:
                    return_string += f'{atn} {pos[0]:18.10f} {pos[1]:18.10f} {pos[2]:18.10f}\n'
                except:
                    print(atn, pos)
                    raise
        return return_string.encode('utf-8'), {}

    def _prepare_cif(self, trajectory_index=None, main_file_name=''):
        """Write the given trajectory to a string of format CIF."""
        from aiida.common.utils import Capturing
        from aiida.orm.nodes.data.cif import ase_loops, cif_from_ase, pycifrw_from_cif

        cif = ''
        indices = list(range(self.numsteps))
        if trajectory_index is not None:
            indices = [trajectory_index]
        for idx in indices:
            structure = self.get_step_structure(idx)
            ciffile = pycifrw_from_cif(cif_from_ase(structure.get_ase()), ase_loops)
            with Capturing():
                cif = cif + ciffile.WriteOut()
        return cif.encode('utf-8'), {}

    def get_structure(self, store=False, **kwargs):
        """Creates :py:class:`aiida.orm.nodes.data.structure.StructureData`.

        :param store: If True, intermediate calculation gets stored in the
            AiiDA database for record. Default False.
        :param index: The index of the step that you want to retrieve, from
           0 to ``self.numsteps- 1``.
        :param custom_kinds: (Optional) If passed must be a list of
          :py:class:`aiida.orm.nodes.data.structure.Kind` objects. There must be one
          kind object for each different string in the ``symbols`` array, with
          ``kind.name`` set to this string.
          If this parameter is omitted, the automatic kind generation of AiiDA
          :py:class:`aiida.orm.nodes.data.structure.StructureData` nodes is used,
          meaning that the strings in the ``symbols`` array must be valid
          chemical symbols.
        :param custom_cell: (Optional) The cell matrix of the structure.
          If omitted, the cell will be read from the trajectory, if present,
          otherwise the default cell of
          :py:class:`aiida.orm.nodes.data.structure.StructureData` will be used.

        :return: :py:class:`aiida.orm.nodes.data.structure.StructureData` node.
        """
        from aiida.orm.nodes.data.dict import Dict
        from aiida.tools.data.array.trajectory import _get_aiida_structure_inline

        param = Dict(kwargs)

        ret_dict = _get_aiida_structure_inline(trajectory=self, parameters=param, metadata={'store_provenance': store})
        return ret_dict['structure']

    def get_cif(self, index=None, **kwargs):
        """Creates :py:class:`aiida.orm.nodes.data.cif.CifData`"""
        struct = self.get_structure(index=index, **kwargs)
        cif = struct.get_cif(**kwargs)
        return cif

    def _parse_xyz_pos(self, inputstring):
        """Load positions from a XYZ file.

        .. note:: The steps and symbols must be set manually before calling this
            import function as a consistency measure. Even though the symbols
            and steps could be extracted from the XYZ file, the data present in
            the XYZ file may or may not be correct and the same logic would have
            to be present in the XYZ-velocities function. It was therefore
            decided not to implement it at all but require it to be set
            explicitly.

        Usage::

            from aiida.orm.nodes.data.array.trajectory import TrajectoryData

            t = TrajectoryData()
            # get sites and number of timesteps
            t.set_array('steps', arange(ntimesteps))
            t.set_array('symbols', array([site.kind for site in s.sites]))
            t.importfile('some-calc/AIIDA-PROJECT-pos-1.xyz', 'xyz_pos')
        """
        from numpy import array

        from aiida.common.exceptions import ValidationError
        from aiida.tools.data.structure import xyz_parser_iterator

        numsteps = self.numsteps
        if numsteps == 0:
            raise ValidationError('steps must be set before importing positional data')

        numsites = self.numsites
        if numsites == 0:
            raise ValidationError('symbols must be set before importing positional data')

        positions = array(
            [[list(position) for _, position in atoms] for _, _, atoms in xyz_parser_iterator(inputstring)]
        )

        if positions.shape != (numsteps, numsites, 3):
            raise ValueError(
                'TrajectoryData.positions must have shape (s,n,3), '
                'with s=number of steps={} and '
                'n=number of symbols={}'.format(numsteps, numsites)
            )

        self.set_array('positions', positions)

    def _parse_xyz_vel(self, inputstring):
        """Load velocities from a XYZ file.

        .. note:: The steps and symbols must be set manually before calling this
            import function as a consistency measure. See also comment for
            :py:meth:`._parse_xyz_pos`
        """
        from numpy import array

        from aiida.common.exceptions import ValidationError
        from aiida.tools.data.structure import xyz_parser_iterator

        numsteps = self.numsteps
        if numsteps == 0:
            raise ValidationError('steps must be set before importing positional data')

        numsites = self.numsites
        if numsites == 0:
            raise ValidationError('symbols must be set before importing positional data')

        velocities = array(
            [[list(velocity) for _, velocity in atoms] for _, _, atoms in xyz_parser_iterator(inputstring)]
        )

        if velocities.shape != (numsteps, numsites, 3):
            raise ValueError(
                'TrajectoryData.positions must have shape (s,n,3), '
                'with s=number of steps={} and '
                'n=number of symbols={}'.format(numsteps, numsites)
            )

        self.set_array('velocities', velocities)

    def show_mpl_pos(self, **kwargs):
        """Shows the positions as a function of time, separate for XYZ coordinates

        :param int stepsize: The stepsize for the trajectory, set higher than 1 to
            reduce number of points
        :param int mintime: Time to start from
        :param int maxtime: Maximum time
        :param list elements:
            A list of atomic symbols that should be displayed.
            If not specified, all atoms are displayed.
        :param list indices:
            A list of indices of that atoms that can be displayed.
            If not specified, all atoms of the correct species are displayed.
        :param bool dont_block: If True, interpreter is not blocked when figure is displayed.
        """
        from ase.data import atomic_numbers

        # Reading the arrays I need:
        positions = self.get_positions()
        times = self.get_times()
        symbols = self.symbols

        # Try to get the units.
        try:
            positions_unit = self.base.attributes.get('units|positions')
        except AttributeError:
            positions_unit = 'A'
        try:
            times_unit = self.base.attributes.get('units|times')
        except AttributeError:
            times_unit = 'ps'

        # Getting the keyword input
        stepsize = kwargs.pop('stepsize', 1)
        maxtime = kwargs.pop('maxtime', times[-1])
        mintime = kwargs.pop('mintime', times[0])
        element_list = kwargs.pop('elements', None)
        index_list = kwargs.pop('indices', None)
        dont_block = kwargs.pop('dont_block', False)
        label = kwargs.pop('label', None) or self.label or self.__repr__()
        # Choosing the color scheme

        colors = kwargs.pop('colors', 'jmol')
        if colors == 'jmol':
            from ase.data.colors import jmol_colors as colors
        elif colors == 'cpk':
            from ase.data.colors import cpk_colors as colors
        else:
            raise ValueError(f'Unknown color spec {colors}')

        if element_list is None:
            # If not all elements are allowed
            allowed_elements = set(symbols)
        else:
            # A subset of elements are allowed
            allowed_elements = set(element_list)
        color_dict = {s: colors[atomic_numbers[s]] for s in set(symbols)}
        # Here I am trying to find out the atoms to show
        if index_list is None:
            # If not index_list was provided, I will see if an element_list
            # was given to me
            indices_to_show = [i for i, sym in enumerate(symbols) if sym in allowed_elements]
        else:
            indices_to_show = index_list
            # I refrain from checking if indices are ok, will crash if not...

        # The color_list is a list of colors (RGB) that I will
        # pass, so the different species give different colors in the plot
        color_list = [color_dict[s] for s in symbols]

        # Reducing array size based on stepsize variable
        _times = times[::stepsize]
        _positions = positions[::stepsize]

        # Calling
        plot_positions_XYZ(
            _times,
            _positions,
            indices_to_show,
            color_list,
            label,
            positions_unit,
            times_unit,
            dont_block,
            mintime,
            maxtime,
        )

    def show_mpl_heatmap(self, **kwargs):
        """Show a heatmap of the trajectory with matplotlib."""
        import numpy as np
        from scipy import stats

        try:
            from mayavi import mlab
        except ImportError:
            raise ImportError(
                'The plotting feature you requested requires the mayavi package.'
                'Try `pip install mayavi` or consult the documentation.'
            )
        from ase.data import atomic_numbers
        from ase.data.colors import jmol_colors

        def collapse_into_unit_cell(point, cell):
            """Applies linear transformation to coordinate system based on crystal
            lattice, vectors. The inverse of that inverse transformation matrix with the
            point given results in the point being given as a multiples of lattice vectors
            Than take the integer of the rows to find how many times you have to shift
            the point back
            """
            invcell = np.matrix(cell).T.I
            # point in crystal coordinates
            points_in_crystal = np.dot(invcell, point).tolist()[0]
            # point collapsed into unit cell
            points_in_unit_cell = [i % 1 for i in points_in_crystal]
            return np.dot(cell.T, points_in_unit_cell).tolist()

        elements = kwargs.pop('elements', None)
        mintime = kwargs.pop('mintime', None)
        maxtime = kwargs.pop('maxtime', None)
        stepsize = kwargs.pop('stepsize', None) or 1
        contours = np.array(kwargs.pop('contours', None) or (0.1, 0.5))
        sampling_stepsize = int(kwargs.pop('sampling_stepsize', None) or 0)

        times = self.get_times()
        if mintime is None:
            minindex = 0
        else:
            minindex = np.argmax(times > mintime)
        if maxtime is None:
            maxindex = len(times)
        else:
            maxindex = np.argmin(times < maxtime)
        positions = self.get_positions()[minindex:maxindex:stepsize]

        try:
            if self.base.attributes.get('units|positions') in ('bohr', 'atomic'):
                bohr_to_ang = 0.52917720859
                positions *= bohr_to_ang
        except AttributeError:
            pass

        symbols = self.symbols
        if elements is None:
            elements = set(symbols)

        cells = self.get_cells()
        if cells is None:
            raise ValueError('No cell parameters have been supplied for TrajectoryData')
        else:
            cell = np.array(cells[0])
        storage_dict = {s: {} for s in elements}
        for ele in elements:
            storage_dict[ele] = [np.array([]), np.array([]), np.array([])]
        for iat, ele in enumerate(symbols):
            if ele in elements:
                for idim in range(3):
                    storage_dict[ele][idim] = np.concatenate(
                        (storage_dict[ele][idim], positions[:, iat, idim].flatten())
                    )

        for ele in elements:
            storage_dict[ele] = np.array(storage_dict[ele]).T
            storage_dict[ele] = np.array([collapse_into_unit_cell(pos, cell) for pos in storage_dict[ele]]).T

        white = (1, 1, 1)
        mlab.figure(bgcolor=white, size=(1080, 720))

        for i1, a in enumerate(cell):
            i2 = (i1 + 1) % 3
            i3 = (i1 + 2) % 3
            for b in [np.zeros(3), cell[i2]]:
                for c in [np.zeros(3), cell[i3]]:
                    p1 = b + c
                    p2 = p1 + a
                    mlab.plot3d([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]], tube_radius=0.1)

        for ele, data in storage_dict.items():
            kde = stats.gaussian_kde(data, bw_method=0.15)

            _x = data[0, :]
            _y = data[1, :]
            _z = data[2, :]
            xmin, ymin, zmin = _x.min(), _y.min(), _z.min()
            xmax, ymax, zmax = _x.max(), _y.max(), _z.max()

            _xi, _yi, _zi = np.mgrid[xmin:xmax:60j, ymin:ymax:30j, zmin:zmax:30j]
            coords = np.vstack([item.ravel() for item in [_xi, _yi, _zi]])
            density = kde(coords).reshape(_xi.shape)

            # Plot scatter with mayavi
            # ~ figure = mlab.figure('DensityPlot')
            grid = mlab.pipeline.scalar_field(_xi, _yi, _zi, density)
            # ~ min = density.min()
            maxdens = density.max()
            # ~ mlab.pipeline.volume(grid, vmin=min, vmax=min + .5*(max-min))
            surf = mlab.pipeline.iso_surface(grid, opacity=0.5, colormap='cool', contours=(maxdens * contours).tolist())
            lut = surf.module_manager.scalar_lut_manager.lut.table.to_array()

            # The lut is a 255x4 array, with the columns representing RGBA
            # (red, green, blue, alpha) coded with integers going from 0 to 255.

            # We modify the alpha channel to add a transparency gradient
            lut[:, -1] = np.linspace(100, 255, 256)
            lut[:, 0:3] = 255 * jmol_colors[atomic_numbers[ele]]
            # and finally we put this LUT back in the surface object. We could have
            # added any 255*4 array rather than modifying an existing LUT.
            surf.module_manager.scalar_lut_manager.lut.table = lut

            if sampling_stepsize > 0:
                mlab.points3d(
                    _x[::sampling_stepsize],
                    _y[::sampling_stepsize],
                    _z[::sampling_stepsize],
                    color=tuple(jmol_colors[atomic_numbers[ele]].tolist()),
                    scale_mode='none',
                    scale_factor=0.3,
                    opacity=0.3,
                )

        mlab.view(azimuth=155, elevation=70, distance='auto')
        mlab.show()


def plot_positions_XYZ(  # noqa: N802
    times,
    positions,
    indices_to_show,
    color_list,
    label,
    positions_unit='A',
    times_unit='ps',
    dont_block=False,
    mintime=None,
    maxtime=None,
    n_labels=10,
):
    """Plot with matplotlib the positions of the coordinates of the atoms
    over time for a trajectory

    :param times: array of times
    :param positions: array of positions
    :param indices_to_show: list of indices of to show (0, 1, 2 for X, Y, Z)
    :param color_list: list of valid color specifications for matplotlib
    :param label: label for this plot to put in the title
    :param positions_unit: label for the units of positions (for the x label)
    :param times_unit: label for the units of times (for the y label)
    :param dont_block: passed to plt.show() as ``block=not dont_block``
    :param mintime: if specified, cut the time axis at the specified min value
    :param maxtime: if specified, cut the time axis at the specified max value
    :param n_labels: how many labels (t, coord) to put
    """
    import numpy as np
    from matplotlib import pyplot as plt
    from matplotlib.gridspec import GridSpec

    tlim = [times[0], times[-1]]
    index_range = [0, len(times) - 1]
    if mintime is not None:
        tlim[0] = mintime
        index_range[0] = np.argmax(times > mintime)
    if maxtime is not None:
        tlim[1] = maxtime
        index_range[1] = np.argmin(times < maxtime)

    trajectories = zip(*positions.tolist())  # only used in enumerate() below
    fig = plt.figure(figsize=(12, 7))

    plt.suptitle(r'Trajectory of {}'.format(label), fontsize=16)
    nr_of_axes = 3
    gridspec = GridSpec(nr_of_axes, 1, hspace=0.0)

    ax1 = fig.add_subplot(gridspec[0])
    plt.ylabel(r'X Position $\left[{}\right]$'.format(positions_unit))
    plt.xticks([])
    plt.xlim(*tlim)
    ax2 = fig.add_subplot(gridspec[1])
    plt.ylabel(r'Y Position $\left[{}\right]$'.format(positions_unit))
    plt.xticks([])
    plt.xlim(*tlim)
    ax3 = fig.add_subplot(gridspec[2])
    plt.ylabel(r'Z Position $\left[{}\right]$'.format(positions_unit))
    plt.xlabel(f'Time [{times_unit}]')
    plt.xlim(*tlim)
    n_labels = np.minimum(n_labels, len(times))  # don't need more labels than times
    sparse_indices = np.linspace(*index_range, num=n_labels, dtype=int)

    for index, traj in enumerate(trajectories):
        if index not in indices_to_show:
            continue
        color = color_list[index]
        _x, _y, _z = list(zip(*traj))
        ax1.plot(times, _x, color=color)
        ax2.plot(times, _y, color=color)
        ax3.plot(times, _z, color=color)
        for i in sparse_indices:
            ax1.text(times[i], _x[i], str(index), color=color, fontsize=5)
            ax2.text(times[i], _x[i], str(index), color=color, fontsize=5)
            ax3.text(times[i], _x[i], str(index), color=color, fontsize=5)
    for axes in ax1, ax2, ax3:
        yticks = axes.yaxis.get_major_ticks()
        yticks[0].label1.set_visible(False)

    plt.show(block=not dont_block)
