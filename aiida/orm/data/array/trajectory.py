# -*- coding: utf-8 -*-
from aiida.orm.data.array import ArrayData

__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = "Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

class TrajectoryData(ArrayData):
    """
    Stores a trajectory (a sequence of crystal structures with timestamps, and
    possibly with velocities).
    """

    def _internal_validate(self, steps, times, cells, symbols, positions, velocities):
        """
        Internal function to validate the type and shape of the arrays. See
        the documentation of py:meth:`.set_trajectory` for a description of the
        valid shape and type of the parameters.
        """
        import numpy
        
        if not isinstance(steps, numpy.ndarray) or steps.dtype != int:
            raise TypeError("TrajectoryData.steps must be a numpy array of integers")
        if not isinstance(times, numpy.ndarray) or times.dtype != float:
            raise TypeError("TrajectoryData.times must be a numpy array of floats")
        if not isinstance(cells, numpy.ndarray) or cells.dtype != float:
            raise TypeError("TrajectoryData.cells must be a numpy array of floats")
        if not isinstance(symbols, numpy.ndarray):
            raise TypeError("TrajectoryData.symbols must be a numpy array")
        if not isinstance(positions, numpy.ndarray) or positions.dtype != float:
            raise TypeError("TrajectoryData.positions must be a numpy array of floats")
        if velocities is not None:
            if not isinstance(velocities, numpy.ndarray) or velocities.dtype != float:
                raise TypeError("TrajectoryData.velocities must be a numpy array of floats, or None")
        
        numsteps = steps.size
        if steps.shape != (numsteps,):
            raise ValueError("TrajectoryData.steps must be a 1d array")
        if times.shape != (numsteps,):
            raise ValueError("TrajectoryData.times must have shape (s,), "
                             "with s=number of steps")
        if cells.shape != (numsteps,3,3):
            raise ValueError("TrajectoryData.cells must have shape (s,3,3), "
                             "with s=number of steps")
        numatoms = symbols.size
        if symbols.shape != (numatoms,):
            raise ValueError("TrajectoryData.symbols must be a 1d array")
        if positions.shape != (numsteps,numatoms,3):
            raise ValueError("TrajectoryData.positions must have shape (s,n,3), "
                             "with s=number of steps and n=number of symbols")
        if velocities is not None:
            if velocities.shape != (numsteps,numatoms,3):
                raise ValueError("TrajectoryData.velocities, if not None, must "
                                 "have shape (s,n,3), "
                                 "with s=number of steps and n=number of symbols")


        
    def set_trajectory(self, steps, times,  cells, symbols, positions, velocities=None):
        r"""
        Store the whole trajectory, after checking that types and dimensions
        are correct.
        Velocities are optional, if they are not passed, nothing is stored.
        
        :param steps: integer array with dimension ``s``, where ``s`` is the
                      number of steps. Typically represents an internal counter
                      within the code. For instance, if you want to store a
                      trajectory with one step every 10, starting from step 65,
                      the array will be ``[65,75,85,...]``.
                      No checks are done on duplicate elements
                      or on the ordering, but anyway this array should be
                      sorted in ascending order, without duplicate elements.
                      If your code does not provide an internal counter, just
                      provide for instance ``arange(s)``.
        :param times: float array with dimension ``s``, where ``s`` is the
                      length of the ``steps`` array. Contains the timestamp
                      of each step in picoseconds (ps).
        :param cells: float array with dimension :math:`s \times 3 \times 3`,
                      where ``s`` is the
                      length of the ``steps`` array. Units are angstrom.
                      In particular,
                      ``cells[i,j,k]`` is the ``k``-th component of the ``j``-th
                      cell vector at the time step with index ``i`` (identified
                      by step number ``step[i]`` and with timestamp ``times[i]``).
        :param symbols: string array with dimension ``n``, where ``n`` is the 
                      number of atoms (i.e., sites) in the structure.
                      The same array is used for each step. Normally, the string
                      should be a valid chemical symbol, but actually any unique
                      string works and can be used as the name of the atomic kind
                      (see also the :py:meth:`.step_to_structure()` method). 
        :param positions: float array with dimension :math:`s \times 3 \times 3`,
                      where ``s`` is the
                      length of the ``steps`` array and ``n`` is the length
                      of the ``symbols`` array. Units are angstrom.
                      In particular,
                      ``positions[i,j,k]`` is the ``k``-th component of the
                      ``j``-th atom (or site) in the structure at the time step
                      with index ``i`` (identified
                      by step number ``step[i]`` and with timestamp ``times[i]``).
        :param velocities: if specified, must be a float array with the same
                      dimensions of the ``positions`` array.
                      The array contains the velocities in the atoms.
                      
        .. todo :: Choose suitable units for velocities
        """
        self._internal_validate(steps,times,cells,symbols,positions,velocities)
        self.set_array('steps', steps)
        self.set_array('times', times)
        self.set_array('cells', cells)
        self.set_array('symbols', symbols)
        self.set_array('positions', positions)
        if velocities is not None:
            self.set_array('velocities', velocities)
        else:
            # Delete velocities array, if it was present
            try:
                self.delete_array('velocities')
            except KeyError:
                pass
        

    def validate(self):
        """
        Verify that the required arrays are present and that their type and
        dimension are correct.
        """
        #check dimensions, types 
        from aiida.common.exceptions import ValidationError
        try:
            self._internal_validate(self.get_steps(),self.get_times(),
                                    self.get_cells(),
                                    self.get_symbols(),self.get_positions(),
                                    self.get_velocities())
        # Should catch TypeErrors, ValueErrors, and KeyErrors for missing arrays
        except Exception as e:
            raise ValidationError("The TrajectoryData did not validate. "
                                  "Error: {} with message {}".format(
                                     type(e).__name__, e.message))

    @property
    def numsteps(self):
        """
        Return the number of stored steps, or zero if nothing has been stored yet.
        """
        try:
            return self.get_shape('steps')[0]
        except (AttributeError, KeyError, IndexError):
            return 0

    @property
    def numsites(self):
        """
        Return the number of stored sites, or zero if nothing has been stored yet.
        """
        try:
            return self.get_shape('symbols')[0]
        except (AttributeError, KeyError, IndexError):
            return 0

    def get_steps(self):
        """
        Return the array of steps, if it has already been set.
        
        :raises: KeyError if the trajectory has not been set yet.
        """
        return self.get_array('steps')
    
    def get_times(self):
        """
        Return the array of times (in ps), if it has already been set.
        
        :raises: KeyError if the trajectory has not been set yet.
        """
        return self.get_array('times')

    def get_cells(self):
        """
        Return the array of cells, if it has already been set.
        
        :raises: KeyError if the trajectory has not been set yet.
        """
        return self.get_array('cells')

    def get_symbols(self):
        """
        Return the array of symbols, if it has already been set.
        
        :raises: KeyError if the trajectory has not been set yet.
        """
        return self.get_array('symbols')

    def get_positions(self):
        """
        Return the array of positions, if it has already been set.
        
        :raises: KeyError if the trajectory has not been set yet.
        """
        return self.get_array('positions')

    def get_velocities(self):
        """
        Return the array of velocities, if it has already been set.

        .. note :: This function (differently from all other ``get_*``
          functions, will not raise an exception if the velocities are not
          set, but rather return ``None`` (both if no trajectory was not set yet,
          and if it the trajectory was set but no velocities were specified).
        """
        try:
            return self.get_array('velocities')
        except (AttributeError, KeyError):
            return None
    
    def get_step_index(self, step):
        """
        Given a value for the step (i.e., a value among those of the ``steps``
        array), return the array index of that step, that can be used in other
        methods such as :py:meth:`.get_step_data` or
        :py:meth:`.step_to_structure`.

        Note that this function returns the first index found (i.e. if multiple
        steps are present with the same value,
        only the index of the first one is returned).
        
        :raise: ValueError if no step with the given value is found.
        """
        import numpy
        
        try:
            return numpy.where(self.get_steps()==step)[0][0]
        except IndexError:
            raise ValueError("{} not among the steps".format(step))

    def get_step_data(self, index):
        r"""
        Return a tuple with all information concerning 
        the step with given index (0 is the first step, 1 the second step
        and so on). If you know only the step value, use the :py:meth:`.get_step_index`
        method to get the corresponding index.
        
        If no velocities were specified, None is returned as the last element.
        
        :return: A tuple in the format
          ``(step, time, cell, symbols, positions, velocities)``,
          where ``step`` is an integer, ``time`` is a float, ``cell`` is a
          :math:`3 \times 3` matrix, ``symbols`` is an array of length ``n``,
          positions is a :math:`n \times 3` array, and velocities is either
          ``None`` or a :math:`n \times 3` array
        
        :param index: The index of the step that you want to retrieve, from 
           0 to ``self.numsteps - 1``.
        :raise: IndexError if you require an index beyond the limits.
        :raise: KeyError if you did not store the trajectory yet.
        """
        if index >= self.numsteps:
            raise IndexError("You have only {} steps, but you are looking beyond"
                             " (index={})".format(self.numsteps,index))
            
        vel = self.get_velocities()
        if vel is not None:
            vel = vel[index,:,:]
        return (self.get_steps()[index], self.get_times()[index],
                self.get_cells()[index,:,:], self.get_symbols(), 
                self.get_positions()[index,:,:], vel)

    def step_to_structure(self, index, custom_kinds=None):   
        """
        Return an AiiDA :py:class:`aiida.orm.data.structure.StructureData` node
        (not stored yet!) with the coordinates of the given step, identified by
        its index. If you know only the step value, use the :py:meth:`.get_step_index`
        method to get the corresponding index.
        
        .. note:: The periodic boundary conditions are always set to True.
    
        :param index: The index of the step that you want to retrieve, from 
           0 to ``self.numsteps- 1``.
        :param custom_kinds: (Optional) If passed must be a list of
          :py:class:`aiida.orm.data.structure.Kind` objects. There must be one
          kind object for each different string in the ``symbols`` array, with
          ``kind.name`` set to this string.
          If this parameter is omitted, the automatic kind generation of AiiDA
          :py:class:`aiida.orm.data.structure.StructureData` nodes is used,
          meaning that the strings in the ``symbols`` array must be valid 
          chemical symbols.
        """
        from aiida.orm.data.structure import StructureData, Kind, Site

        # ignore step, time, and velocities
        _, _, cell, symbols, positions, _ = self.get_step_data(index)
        
        if custom_kinds is not None:
            kind_names = []
            for k in custom_kinds:
                if not isinstance(k, Kind):
                    raise TypeError("Each element of the custom_kinds list must "
                                   "be a aiida.orm.data.structure.Kind object")
                kind_names.append(k.name)
            if len(kind_names) != len(set(kind_names)):
                raise ValueError("Multiple kinds with the same name passed "
                                 "as custom_kinds")
            if set(kind_names) != set(symbols):
                raise ValueError("If you pass custom_kinds, you have to "
                                 "pass one Kind object for each symbol "
                                 "that is present in the trajectory. You "
                                 "passed {}, but the symbols are {}".format(
                                     sorted(kind_names), sorted(symbols)))
                
        
        struc = StructureData(cell=cell)
        if custom_kinds is not None:
            for k in custom_kinds:
                struc.append_kind(k)
            for s, p in zip(symbols, positions): 
                struc.append_site(Site(kind_name=s, position=p))
        else:
            for s,p in zip(symbols,positions):
                # Automatic species generation
                struc.append_atom(symbols=s, position=p)
                
        return struc