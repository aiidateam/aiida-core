# -*- coding: utf-8 -*-
from aiida.orm.data.array import ArrayData
from aiida.orm.calculation.inline import optional_inline

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0.1"
__authors__ = "The AiiDA team."


@optional_inline
def _get_aiida_structure_inline(trajectory=None, parameters=None):
    """
    Creates :py:class:`aiida.orm.data.structure.StructureData` using ASE.

    .. note:: requires ASE module.
    """
    from aiida.orm.data.structure import StructureData

    kwargs = {}
    if parameters is not None:
        kwargs = parameters.get_dict()
    if 'index' not in kwargs.keys() or kwargs['index'] is None:
        raise ValueError("Step index is not supplied for TrajectoryData")
    return {'structure': trajectory.step_to_structure(**kwargs)}


class TrajectoryData(ArrayData):
    """
    Stores a trajectory (a sequence of crystal structures with timestamps, and
    possibly with velocities).
    """

    def _internal_validate(self, steps, cells, symbols, positions, times, velocities):
        """
        Internal function to validate the type and shape of the arrays. See
        the documentation of py:meth:`.set_trajectory` for a description of the
        valid shape and type of the parameters.
        """
        import numpy

        if not isinstance(steps, numpy.ndarray) or steps.dtype != int:
            raise TypeError("TrajectoryData.steps must be a numpy array of integers")
        if not isinstance(cells, numpy.ndarray) or cells.dtype != float:
            raise TypeError("TrajectoryData.cells must be a numpy array of floats")
        if not isinstance(symbols, numpy.ndarray):
            raise TypeError("TrajectoryData.symbols must be a numpy array")
        if any([not isinstance(i, basestring) for i in symbols]):
            raise TypeError("TrajectoryData.symbols must be a numpy array of strings")
        if not isinstance(positions, numpy.ndarray) or positions.dtype != float:
            raise TypeError("TrajectoryData.positions must be a numpy array of floats")
        if times is not None:
            if not isinstance(times, numpy.ndarray) or times.dtype != float:
                raise TypeError("TrajectoryData.times must be a numpy array of floats")
        if velocities is not None:
            if not isinstance(velocities, numpy.ndarray) or velocities.dtype != float:
                raise TypeError("TrajectoryData.velocities must be a numpy array of floats, or None")

        numsteps = steps.size
        if steps.shape != (numsteps,):
            raise ValueError("TrajectoryData.steps must be a 1d array")
        if cells.shape != (numsteps, 3, 3):
            raise ValueError("TrajectoryData.cells must have shape (s,3,3), "
                             "with s=number of steps")
        numatoms = symbols.size
        if symbols.shape != (numatoms,):
            raise ValueError("TrajectoryData.symbols must be a 1d array")
        if positions.shape != (numsteps, numatoms, 3):
            raise ValueError("TrajectoryData.positions must have shape (s,n,3), "
                             "with s=number of steps and n=number of symbols")
        if times is not None:
            if times.shape != (numsteps,):
                raise ValueError("TrajectoryData.times must have shape (s,), "
                                 "with s=number of steps")
        if velocities is not None:
            if velocities.shape != (numsteps, numatoms, 3):
                raise ValueError("TrajectoryData.velocities, if not None, must "
                                 "have shape (s,n,3), "
                                 "with s=number of steps and n=number of symbols")

    def set_trajectory(self, steps, cells, symbols, positions, times=None, velocities=None):
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
        :param positions: float array with dimension :math:`s \times n \times 3`,
                      where ``s`` is the
                      length of the ``steps`` array and ``n`` is the length
                      of the ``symbols`` array. Units are angstrom.
                      In particular,
                      ``positions[i,j,k]`` is the ``k``-th component of the
                      ``j``-th atom (or site) in the structure at the time step
                      with index ``i`` (identified
                      by step number ``step[i]`` and with timestamp ``times[i]``).
        :param times: if specified, float array with dimension ``s``, where 
                      ``s`` is the length of the ``steps`` array. Contains the 
                      timestamp of each step in picoseconds (ps).
        :param velocities: if specified, must be a float array with the same
                      dimensions of the ``positions`` array.
                      The array contains the velocities in the atoms.
                      
        .. todo :: Choose suitable units for velocities
        """
        self._internal_validate(steps, cells, symbols, positions, times, velocities)
        self.set_array('steps', steps)
        self.set_array('cells', cells)
        self.set_array('symbols', symbols)
        self.set_array('positions', positions)
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
        """
        Create trajectory from the list of
        :py:class:`aiida.orm.data.structure.StructureData` instances.

        :param structurelist: a list of
            :py:class:`aiida.orm.data.structure.StructureData` instances.

        :raises ValueError: if symbol lists of supplied structures are
            different
        """
        import numpy

        steps = numpy.array(range(0, len(structurelist)))
        cells = numpy.array([x.cell for x in structurelist])
        symbols_first = [str(s.kind_name) for s in structurelist[0].sites]
        for symbols_now in [[str(s.kind_name) for s in structurelist[i].sites]
                            for i in steps]:
            if symbols_first != symbols_now:
                raise ValueError("Symbol lists have to be the same for "
                                 "all of the supplied structures")
        symbols = numpy.array(symbols_first)
        positions = numpy.array([[list(s.position) for s in x.sites] for x in structurelist])
        self.set_trajectory(steps, cells, symbols, positions)

    def _validate(self):
        """
        Verify that the required arrays are present and that their type and
        dimension are correct.
        """
        # check dimensions, types
        from aiida.common.exceptions import ValidationError

        try:
            self._internal_validate(self.get_steps(),
                                    self.get_cells(),
                                    self.get_symbols(), self.get_positions(),
                                    self.get_times(),
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
        
        :raises KeyError: if the trajectory has not been set yet.
        """
        return self.get_array('steps')

    def get_times(self):
        """
        Return the array of times (in ps), if it has already been set.
        
        :raises KeyError: if the trajectory has not been set yet.
        """
        try:
            return self.get_array('times')
        except (AttributeError, KeyError):
            return None

    def get_cells(self):
        """
        Return the array of cells, if it has already been set.
        
        :raises KeyError: if the trajectory has not been set yet.
        """
        return self.get_array('cells')

    def get_symbols(self):
        """
        Return the array of symbols, if it has already been set.
        
        :raises KeyError: if the trajectory has not been set yet.
        """
        return self.get_array('symbols')

    def get_positions(self):
        """
        Return the array of positions, if it has already been set.
        
        :raises KeyError: if the trajectory has not been set yet.
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

        .. note:: Note that this function returns the first index found
            (i.e. if multiple steps are present with the same value,
            only the index of the first one is returned).
        
        :raises ValueError: if no step with the given value is found.
        """
        import numpy

        try:
            return numpy.where(self.get_steps() == step)[0][0]
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
        :raises IndexError: if you require an index beyond the limits.
        :raises KeyError: if you did not store the trajectory yet.
        """
        if index >= self.numsteps:
            raise IndexError("You have only {} steps, but you are looking beyond"
                             " (index={})".format(self.numsteps, index))

        vel = self.get_velocities()
        if vel is not None:
            vel = vel[index, :, :]
        time = self.get_times()
        if time is not None:
            time = time[index]
        return (self.get_steps()[index], time, self.get_cells()[index, :, :],
                self.get_symbols(), self.get_positions()[index, :, :], vel)

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
            for s, p in zip(symbols, positions):
                # Automatic species generation
                struc.append_atom(symbols=s, position=p)

        return struc

    def _prepare_xsf(self,step=None):
        """
        Write the given trajectory to a string of format XSF (for XCrySDen). 
        """
        from aiida.common.constants import elements
        _atomic_numbers = {data['symbol']: num for num, data in elements.iteritems()}
        
        steps = self.get_steps()
        if step is not None:
            steps = [step]
        return_string = "ANIMSTEPS {}\nCRYSTAL\n".format(len(steps))
        for idx, step in enumerate(steps):
            return_string += "PRIMVEC {}\n".format(idx+1)
            structure = self.step_to_structure(step)
            sites = structure.sites
            if structure.is_alloy() or structure.has_vacancies():
                raise NotImplementedError("XSF for alloys or systems with "
                                          "vacancies not implemented.")
            for cell_vector in structure.cell:
                return_string += " ".join(["%18.5f" % i for i in cell_vector])
                return_string += "\n"
            return_string += "PRIMCOORD {}\n".format(idx+1)
            return_string += "%d 1\n" % len(sites)
            for site in sites:
                # I checked above that it is not an alloy, therefore I take the
                # first symbol
                return_string += "%s " % _atomic_numbers[
                                                         structure.get_kind(site.kind_name).symbols[0]]
                return_string += "%18.10f %18.10f %18.10f\n" % tuple(site.position)
        return return_string

    def _prepare_cif(self, step=None):
        """
        Write the given trajectory to a string of format CIF.
        """
        import CifFile
        from aiida.orm.data.cif \
            import ase_loops, cif_from_ase, pycifrw_from_cif

        cif = ""
        steps = self.get_steps()
        if step is not None:
            steps = [step]
        for i in steps:
            structure = self.step_to_structure(i - 1)
            ciffile = pycifrw_from_cif(cif_from_ase(structure.get_ase()),
                                       ase_loops)
            cif = cif + ciffile.WriteOut()
        return cif

    def _prepare_tcod(self, **kwargs):
        """
        Write the given trajectory to a string of format TCOD CIF.
        """
        from aiida.tools.dbexporters.tcod import export_cif
        return export_cif(self,**kwargs)

    def _get_aiida_structure(self, store=False, **kwargs):
        """
        Creates :py:class:`aiida.orm.data.structure.StructureData`.

        :param converter: specify the converter. Default 'ase'.
        :param store: If True, intermediate calculation gets stored in the
            AiiDA database for record. Default False.
        :return: :py:class:`aiida.orm.data.structure.StructureData` node.
        """
        from aiida.orm.data.parameter import ParameterData
        import trajectory  # This same module

        param = ParameterData(dict=kwargs)
        conv_f = getattr(trajectory, '_get_aiida_structure_inline')
        ret_dict = conv_f(trajectory=self, parameters=param, store=store)
        return ret_dict['structure']

    def _get_cif(self, index=None, **kwargs):
        """
        Creates :py:class:`aiida.orm.data.cif.CifData`
        """
        struct = self._get_aiida_structure(index=index, **kwargs)
        cif = struct._get_cif(**kwargs)
        return cif

    def _parse_xyz_pos(self, inputstring):
        """
        Load positions from a XYZ file.

        .. note:: The steps and symbols must be set manually before calling this
            import function as a consistency measure. Even though the symbols
            and steps could be extracted from the XYZ file, the data present in
            the XYZ file may or may not be correct and the same logic would have
            to be present in the XYZ-velocities function. It was therefore
            decided not to implement it at all but require it to be set
            explicitly.

        .. usage::

            from aiida.orm.data.array.trajectory import TrajectoryData

            t = TrajectoryData()
            # get sites and number of timesteps
            t.set_array('steps', arange(ntimesteps))
            t.set_array('symbols', array([site.kind for site in s.sites]))
            t.importfile('some-calc/AIIDA-PROJECT-pos-1.xyz', 'xyz_pos')
        """

        from aiida.common.exceptions import ValidationError
        from aiida.common.utils import xyz_parser_iterator
        from numpy import array

        try:
            numsteps = self.get_array('steps').size
        except:
            raise ValidationError("steps must be set before importing positional data")

        try:
            numatoms = self.get_array('symbols').size
        except:
            raise ValidationError("symbols must be set before importing positional data")

        positions = array([
            [list(position) for _, position in atoms]
                    for _, _, atoms in xyz_parser_iterator(inputstring)])

        if positions.shape != (numsteps, numatoms, 3):
            raise ValueError("TrajectoryData.positions must have shape (s,n,3), "
                             "with s=number of steps and n=number of symbols")

        self.set_array('positions', positions)

    def _parse_xyz_vel(self, inputstring):
        """
        Load velocities from a XYZ file.

        .. note:: The steps and symbols must be set manually before calling this
            import function as a consistency measure. See also comment for
            :py:meth:`._import_xy_pos`
        """

        from aiida.common.exceptions import ValidationError
        from aiida.common.utils import xyz_parser_iterator
        from numpy import array

        try:
            numsteps = self.get_array('steps').size
        except:
            raise ValidationError("steps must be set before importing positional data")

        try:
            numatoms = self.get_array('symbols').size
        except:
            raise ValidationError("symbols must be set before importing positional data")

        velocities = array([
            [list(velocity) for _, velocity in atoms]
                    for _, _, atoms in xyz_parser_iterator(inputstring)])

        if velocities.shape != (numsteps, numatoms, 3):
            raise ValueError("TrajectoryData.velocities must have shape (s,n,3), "
                             "with s=number of steps and n=number of symbols")

        self.set_array('velocities', velocities)
