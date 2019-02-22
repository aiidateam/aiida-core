# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import six
from six.moves import range, zip
import numpy

from .array import ArrayData


DEPRECATION_DOCS_URL = 'http://aiida-core.readthedocs.io/en/latest/datatypes/kpoints.html#deprecated-methods'

_default_epsilon_length = 1e-5
_default_epsilon_angle = 1e-5


class KpointsData(ArrayData):
    """
    Class to handle array of kpoints in the Brillouin zone. Provide methods to
    generate either user-defined k-points or path of k-points along symmetry
    lines.
    Internally, all k-points are defined in terms of crystal (fractional)
    coordinates.
    Cell and lattice vector coordinates are in Angstroms, reciprocal lattice
    vectors in Angstrom^-1 .
    :note: The methods setting and using the Bravais lattice info assume the
    PRIMITIVE unit cell is provided in input to the set_cell or
    set_cell_from_structure methods.
    """

    def __init__(self, *args, **kwargs):
        super(KpointsData, self).__init__(*args, **kwargs)
        try:
            self._set_reciprocal_cell()
        except AttributeError:
            pass

    def get_description(self):
        """
        Returns a string with infos retrieved from  kpoints node's properties.
        :param node:
        :return: retstr
        """
        try:
            mesh = self.get_kpoints_mesh()
            return "Kpoints mesh: {}x{}x{} (+{:.1f},{:.1f},{:.1f})".format(
                mesh[0][0], mesh[0][1], mesh[0][2],
                mesh[1][0], mesh[1][1], mesh[1][2])
        except AttributeError:
            try:
                return '(Path of {} kpts)'.format(len(self.get_kpoints()))
            except OSError:
                return self.node_type

    @property
    def cell(self):
        """
        The crystal unit cell. Rows are the crystal vectors in Angstroms.
        :return: a 3x3 numpy.array
        """
        return numpy.array(self.get_attribute('cell'))

    @cell.setter
    def cell(self, value):
        """
        Set the crystal unit cell
        :param value: a 3x3 list/tuple/array of numbers (units = Angstroms).
        """
        self._set_cell(value)

    def _set_cell(self, value):
        """
        Validate if 'value' is a allowed crystal unit cell
        :param value: something compatible with a 3x3 tuple of floats
        """
        from aiida.common.exceptions import ModificationNotAllowed
        from aiida.orm.nodes.data.structure import _get_valid_cell

        if self.is_stored:
            raise ModificationNotAllowed(
                "KpointsData cannot be modified, it has already been stored")

        the_cell = _get_valid_cell(value)

        self.set_attribute('cell', the_cell)

    @property
    def pbc(self):
        """
        The periodic boundary conditions along the vectors a1,a2,a3.

        :return: a tuple of three booleans, each one tells if there are periodic
            boundary conditions for the i-th real-space direction (i=1,2,3)
        """
        # return copy.deepcopy(self._pbc)
        return (
        self.get_attribute('pbc1'), self.get_attribute('pbc2'), self.get_attribute('pbc3'))

    @pbc.setter
    def pbc(self, value):
        """
        Set the value of pbc, i.e. a tuple of three booleans, indicating if the
        cell is periodic in the 1,2,3 crystal direction
        """
        self._set_pbc(value)

    def _set_pbc(self, value):
        """
        validate the pbc, then store them
        """
        from aiida.common.exceptions import ModificationNotAllowed
        from aiida.orm.nodes.data.structure import get_valid_pbc

        if self.is_stored:
            raise ModificationNotAllowed(
                "The KpointsData object cannot be modified, it has already been stored")
        the_pbc = get_valid_pbc(value)
        self.set_attribute('pbc1', the_pbc[0])
        self.set_attribute('pbc2', the_pbc[1])
        self.set_attribute('pbc3', the_pbc[2])

    @property
    def labels(self):
        """
        Labels associated with the list of kpoints.
        List of tuples with kpoint index and kpoint name: ``[(0,'G'),(13,'M'),...]``
        """
        label_numbers = self.get_attribute('label_numbers', None)
        labels = self.get_attribute('labels', None)
        if labels is None or label_numbers is None:
            return None
        return list(zip(label_numbers, labels))

    @labels.setter
    def labels(self, value):
        self._set_labels(value)

    def _set_labels(self, value):
        """
        set label names. Must pass in input a list like: ``[[0,'X'],[34,'L'],... ]``
        """
        # check if kpoints were set
        try:
            self.get_kpoints()
        except AttributeError:
            raise AttributeError("Kpoints must be set before the labels")

        if value is None:
            value = []

        try:
            label_numbers = [int(i[0]) for i in value]
        except ValueError:
            raise ValueError("The input must contain an integer index, to map"
                             " the labels into the kpoint list")
        labels = [str(i[1]) for i in value]

        if any([i > len(self.get_kpoints()) - 1 for i in label_numbers]):
            raise ValueError("Index of label exceeding the list of kpoints")

        self.set_attribute('label_numbers', label_numbers)
        self.set_attribute('labels', labels)

    def _change_reference(self, kpoints, to_cartesian=True):
        """
        Change reference system, from cartesian to crystal coordinates (units of b1,b2,b3) or viceversa.
        :param kpoints: a list of (3) point coordinates
        :return kpoints: a list of (3) point coordinates in the new reference
        """
        if not isinstance(kpoints, numpy.ndarray):
            raise ValueError("kpoints must be a numpy.array for method change_reference()")

        try:
            rec_cell = self.reciprocal_cell
        except AttributeError:
            # rec_cell = numpy.eye(3)
            raise AttributeError(
                "Cannot use cartesian coordinates without having defined a cell")

        trec_cell = numpy.transpose(numpy.array(rec_cell))
        if to_cartesian:
            matrix = trec_cell
        else:
            matrix = numpy.linalg.inv(trec_cell)

        # note: kpoints is a list Nx3, matrix is 3x3.
        # hence, first transpose kpoints, then multiply, finally transpose it back
        return numpy.transpose(numpy.dot(matrix, numpy.transpose(kpoints)))

    def set_cell_from_structure(self, structuredata):
        """
        Set a cell to be used for symmetry analysis from an AiiDA structure.
        Inherits both the cell and the pbc's.
        To set manually a cell, use "set_cell"

        :param structuredata: an instance of StructureData
        """
        from aiida.orm import StructureData

        if not isinstance(structuredata, StructureData):
            raise ValueError("An instance of StructureData should be passed to "
                             "the KpointsData, found instead {}"
                             .format(structuredata.__class__))
        cell = structuredata.cell
        self.set_cell(cell, structuredata.pbc)

    def set_cell(self, cell, pbc=None):
        """
        Set a cell to be used for symmetry analysis.
        To set a cell from an AiiDA structure, use "set_cell_from_structure".

        :param cell: 3x3 matrix of cell vectors. Orientation: each row
                     represent a lattice vector. Units are Angstroms.
        :param pbc: list of 3 booleans, True if in the nth crystal direction the
                    structure is periodic. Default = [True,True,True]
        """
        self.cell = cell
        if pbc is None:
            pbc = [True, True, True]
        self.pbc = pbc
        self._set_reciprocal_cell()

    def _set_reciprocal_cell(self):
        """
        Sets the reciprocal cell in units of 1/Angstrom from the internally set cell
        """
        the_cell = numpy.array(self.cell)
        self.reciprocal_cell = 2. * numpy.pi * numpy.linalg.inv(the_cell).transpose()

    def set_kpoints_mesh(self, mesh, offset=[0., 0., 0.]):
        """
        Set KpointsData to represent a uniformily spaced mesh of kpoints in the
        Brillouin zone. This excludes the possibility of set/get kpoints

        :param mesh: a list of three integers, representing the size of the
            kpoint mesh along b1,b2,b3.
        :param offset: (optional) a list of three floats between 0 and 1.
            [0.,0.,0.] is Gamma centered mesh
            [0.5,0.5,0.5] is half shifted
            [1.,1.,1.] by periodicity should be equivalent to [0.,0.,0.]
            Default = [0.,0.,0.].
        """
        from aiida.common.exceptions import ModificationNotAllowed
        # validate
        try:
            the_mesh = tuple(int(i) for i in mesh)
            if len(the_mesh) != 3:
                raise ValueError
        except (IndexError, ValueError, TypeError):
            raise ValueError("The kpoint mesh must be a list of three integers")
        try:
            the_offset = tuple(float(i) for i in offset)
            if len(the_offset) != 3:
                raise ValueError
        except (IndexError, ValueError, TypeError):
            raise ValueError("The offset must be a list of three floats")
        # check that there is no list of kpoints saved already
        # I cannot have both of them at the same time
        try:
            _ = self.get_array('kpoints')
            raise ModificationNotAllowed("KpointsData has already a kpoint-"
                                         "list stored")
        except KeyError:
            pass

        # store
        self.set_attribute('mesh', the_mesh)
        self.set_attribute('offset', the_offset)

    def get_kpoints_mesh(self, print_list=False):
        """
        Get the mesh of kpoints.

        :param print_list: default=False. If True, prints the mesh of kpoints as a list

        :raise AttributeError: if no mesh has been set
        :return mesh,offset: (if print_list=False) a list of 3 integers and a list of three
                floats 0<x<1, representing the mesh and the offset of kpoints
        :return kpoints: (if print_list = True) an explicit list of kpoints coordinates,
                similar to what returned by get_kpoints()
        """
        mesh = self.get_attribute('mesh')
        offset = self.get_attribute('offset')
        if not print_list:
            return mesh, offset
        else:
            kpoints = numpy.mgrid[0:mesh[0], 0:mesh[1], 0:mesh[2]]
            kpoints = kpoints.reshape(3, -1).T
            offset_kpoints = kpoints + numpy.array(offset)
            offset_kpoints[:, 0] /= mesh[0]
            offset_kpoints[:, 1] /= mesh[1]
            offset_kpoints[:, 2] /= mesh[2]
            return offset_kpoints

    def set_kpoints_mesh_from_density(self, distance, offset=[0., 0., 0.],
                                      force_parity=False):
        """
        Set a kpoints mesh using a kpoints density, expressed as the maximum
        distance between adjacent points along a reciprocal axis

        :param distance: distance (in 1/Angstrom) between adjacent 
            kpoints, i.e. the number of kpoints along each reciprocal
            axis i is :math:`|b_i|/distance`
            where :math:`|b_i|` is the norm of the reciprocal cell vector.
        :param offset: (optional) a list of three floats between 0 and 1.
            [0.,0.,0.] is Gamma centered mesh
            [0.5,0.5,0.5] is half shifted
            Default = [0.,0.,0.].
        :param force_parity: (optional) if True, force each integer in the mesh
            to be even (except for the non-periodic directions). 

        :note: a cell should be defined first.
        :note: the number of kpoints along non-periodic axes is always 1.
        """
        try:
            rec_cell = self.reciprocal_cell
        except AttributeError:
            # rec_cell = numpy.eye(3)
            raise AttributeError("Cannot define a mesh from a density without "
                                 "having defined a cell")
        # I first round to the fifth digit |b|/distance (to avoid that e.g.
        # 3.00000001 becomes 4)
        kpointsmesh = [
            max(int(numpy.ceil(round(numpy.linalg.norm(b) / distance, 5))), 1)
            if pbc else 1 for pbc, b in zip(self.pbc, rec_cell)]
        if force_parity:
            kpointsmesh = [k + (k % 2) if pbc else 1
                           for pbc, k in zip(self.pbc, kpointsmesh)]
        self.set_kpoints_mesh(kpointsmesh, offset=offset)

    @property
    def _dimension(self):
        """
        Dimensionality of the structure, found from its pbc (i.e. 1 if it's a 1D
        structure, 2 if its 2D, 3 if it's 3D ...).
        :return dimensionality: 0, 1, 2 or 3
        :note: will return 3 if pbc has not been set beforehand
        """
        try:
            return sum(self.pbc)
        except AttributeError:
            return 3

    def _validate_kpoints_weights(self, kpoints, weights):
        """
        Validate the list of kpoints and of weights before storage.
        Kpoints and weights must be convertible respectively to an array of
        N x dimension and N floats
        """
        kpoints = numpy.array(kpoints)

        if len(kpoints) == 0:
            if self._dimension == 0:
                # replace empty list by Gamma point
                kpoints = numpy.array([[0., 0., 0.]])
            else:
                raise ValueError(
                    "empty kpoints list is valid only in zero dimension"
                    "; instead here with have {} dimensions"
                    "".format(self._dimension))

        if len(kpoints.shape) <= 1:
            # list of scalars is accepted only in the 0D and 1D cases
            if self._dimension <= 1:
                # replace by singletons
                kpoints = kpoints.reshape(kpoints.shape[0], 1)
            else:
                raise ValueError("kpoints must be a list of lists in {}D case"
                                 "".format(self._dimension))

        if kpoints.dtype != numpy.dtype(numpy.float):
            raise ValueError("kpoints must be an array of type floats. "
                             "Found instead {}".format(kpoints.dtype))

        if kpoints.shape[1] < self._dimension:
            raise ValueError("In a system which has {0} dimensions, kpoint need"
                             "more than {0} coordinates (found instead {1})"
                             .format(self._dimension, kpoints.shape[1]))

        if weights is not None:
            weights = numpy.array(weights)
            if weights.shape[0] != kpoints.shape[0]:
                raise ValueError("Found {} weights but {} kpoints"
                                 .format(weights.shape[0], kpoints.shape[0]))
            if weights.dtype != numpy.dtype(numpy.float):
                raise ValueError("weights must be an array of type floats. "
                                 "Found instead {}".format(weights.dtype))

        return kpoints, weights

    def set_kpoints(self, kpoints, cartesian=False, labels=None, weights=None,
                    fill_values=0):
        """
        Set the list of kpoints. If a mesh has already been stored, raise a
        ModificationNotAllowed

        :param kpoints: a list of kpoints, each kpoint being a list of one, two
            or three coordinates, depending on self.pbc: if structure is 1D
            (only one True in self.pbc) one allows singletons or scalars for
            each k-point, if it's 2D it can be a length-2 list, and in all
            cases it can be a length-3 list.
            Examples:

                * [[0.,0.,0.],[0.1,0.1,0.1],...] for 1D, 2D or 3D
                * [[0.,0.],[0.1,0.1,],...] for 1D or 2D
                * [[0.],[0.1],...] for 1D
                * [0., 0.1, ...] for 1D (list of scalars)

            For 0D (all pbc are False), the list can be any of the above
            or empty - then only Gamma point is set.
            The value of k for the non-periodic dimension(s) is set by
            fill_values
        :param cartesian: if True, the coordinates given in input are treated
            as in cartesian units. If False, the coordinates are crystal,
            i.e. in units of b1,b2,b3. Default = False
        :param labels: optional, the list of labels to be set for some of the
            kpoints. See labels for more info
        :param weights: optional, a list of floats with the weight associated
            to the kpoint list
        :param fill_values: scalar to be set to all
            non-periodic dimensions (indicated by False in self.pbc), or list of
            values for each of the non-periodic dimensions.
        """
        from aiida.common.exceptions import ModificationNotAllowed

        # check that it is a 'dim'x #kpoints dimensional array
        the_kpoints, the_weights = self._validate_kpoints_weights(kpoints,
                                                                  weights)

        # if k-points have less than 3 coordinates (low dimensionality), fill
        # with constant values the non-periodic dimensions
        if the_kpoints.shape[1] < 3:
            if numpy.isscalar(fill_values):
                # replace scalar by a list of 3-the_kpoints.shape[1] identical
                # elements
                fill_values = [fill_values] * (3 - the_kpoints.shape[1])

            if len(fill_values) < 3 - the_kpoints.shape[1]:
                raise ValueError("fill_values should be either a scalar or a "
                                 "length-{} list".format(
                    3 - the_kpoints.shape[1]))
            else:
                tmp_kpoints = numpy.zeros((the_kpoints.shape[0], 0))
                i_kpts = 0
                i_fill = 0
                for idim in range(3):
                    # check periodic boundary condition of each of the 3 dimensions:
                    # - if it's a periodic one, fill with the k-points values
                    # defined in input
                    # - if it's non-periodic, fill with one of the values in
                    # fill_values
                    if self.pbc[idim]:
                        tmp_kpoints = numpy.hstack(
                            (tmp_kpoints, the_kpoints[:, i_kpts].reshape((
                                the_kpoints.shape[0], 1))))
                        i_kpts += 1
                    else:
                        tmp_kpoints = numpy.hstack(
                            (tmp_kpoints,numpy.ones(
                                (the_kpoints.shape[0], 1)
                            ) * fill_values[i_fill]))
                        i_fill += 1
                the_kpoints = tmp_kpoints

        # change reference and always store in crystal coords
        if cartesian:
            the_kpoints = self._change_reference(the_kpoints, to_cartesian=False)

        # check that we did not saved a mesh already
        if self.get_attribute('mesh', None) is not None:
            raise ModificationNotAllowed(
                "KpointsData has already a mesh stored")

        # store
        self.set_array('kpoints', the_kpoints)
        if the_weights is not None:
            self.set_array('weights', the_weights)
        if labels is not None:
            self.labels = labels

    def get_kpoints(self, also_weights=False, cartesian=False):
        """
        Return the list of kpoints

        :param also_weights: if True, returns also the list of weights.
            Default = False
        :param cartesian: if True, returns points in cartesian coordinates,
            otherwise, returns in crystal coordinates. Default = False.
        """
        try:
            kpoints = numpy.array(self.get_array('kpoints'))
        except KeyError:
            raise AttributeError("Before the get, first set a list of kpoints")

        if cartesian:
            kpoints = self._change_reference(kpoints, to_cartesian=True)

        if also_weights:
            try:
                the_weights = self.get_array('weights')
            except KeyError:
                raise AttributeError('No weights were set')

            weights = numpy.array(the_weights)
            return kpoints, weights
        else:
            return kpoints


# All functions below are deprecated and have been moved to aiida.tools.data.array.kpoints.legacy

    @property
    def bravais_lattice(self):
        """
        The dictionary containing informations about the cell symmetry

        .. deprecated:: 0.11
        """
        import warnings
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('the bravais_lattice method has been deprecated, see {}'.format(DEPRECATION_DOCS_URL), DeprecationWarning)
        return self.get_attribute('bravais_lattice')

    @bravais_lattice.setter
    def bravais_lattice(self, value):
        """
        Set the bravais lattice dictionary

        .. deprecated:: 0.11
        """
        import warnings
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('the bravais_lattice method has been deprecated, see {}'.format(DEPRECATION_DOCS_URL), DeprecationWarning)
        self._set_bravais_lattice(value)

    def _set_bravais_lattice(self, value):
        """
        Validating function to set the bravais_lattice dictionary

        .. deprecated:: 0.11
        """
        import warnings
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('the _set_bravais_lattice method has been deprecated, see {}'.format(DEPRECATION_DOCS_URL), DeprecationWarning)

        import copy
        if not isinstance(value, dict):
            raise ValueError("bravais_lattice is not a dict")
        if not all([i in value for i in ["short_name", "extended_name", "index", "permutation"]]):
            raise ValueError()

        bravais_lattice = copy.copy(value)
        bravais_lattice['permutation'] = [int(i) for i in value['permutation']]

        try:
            if not isinstance(bravais_lattice['variation'], six.string_types):
                raise ValueError()
        except KeyError:
            pass
        try:
            if not isinstance(bravais_lattice['extra'], dict):
                raise ValueError()
            if not all([isinstance(i, float) for i in bravais_lattice['extra'].values()]):
                raise ValueError()
        except KeyError:
            pass

        self.set_attribute('bravais_lattice', bravais_lattice)

    def _get_or_create_bravais_lattice(self,
                                       epsilon_length=_default_epsilon_length,
                                       epsilon_angle=_default_epsilon_angle):
        """
        Try to get the bravais_lattice info if stored already, otherwise analyze
        the cell with the default settings and save this in the attribute.

        .. deprecated:: 0.11
           Use the methods inside the :ref:`aiida.tools.data.array.kpoints<AutomaticKpoints>` module instead.

        :param epsilon_length: threshold on lengths comparison, used
             to get the bravais lattice info
        :param epsilon_angle: threshold on angles comparison, used
             to get the bravais lattice info

        :return bravais_lattice: the dictionary containing the symmetry info
        """
        import warnings
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('the _get_or_create_bravais_lattice method has been deprecated, see {}'.format(DEPRECATION_DOCS_URL), DeprecationWarning)

        try:
            bravais_lattice = self.bravais_lattice
        except AttributeError:
            bravais_lattice = self._find_bravais_info(epsilon_length=epsilon_length,
                                                      epsilon_angle=epsilon_angle)
            self.bravais_lattice = bravais_lattice
        return bravais_lattice

    def set_kpoints_path(self, value=None, kpoint_distance=None, cartesian=False,
                         epsilon_length=_default_epsilon_length,
                         epsilon_angle=_default_epsilon_angle):
        """
        Set a path of kpoints in the Brillouin zone.

        .. deprecated:: 0.11
           Use the methods inside the :ref:`aiida.tools.data.array.kpoints<AutomaticKpoints>` module instead.

        :param value: description of the path, in various possible formats.

            None: automatically sets all irreducible high symmetry paths.
            Requires that a cell was set

            or

            [('G','M'), (...), ...]
            [('G','M',30), (...), ...]
            [('G',(0,0,0),'M',(1,1,1)), (...), ...]
            [('G',(0,0,0),'M',(1,1,1),30), (...), ...]

        :param bool cartesian: if set to true, reads the coordinates eventually
            passed in value as cartesian coordinates. Default: False.
        :param float kpoint_distance: parameter controlling the distance between
            kpoints. Distance is given in crystal coordinates, i.e. the distance
            is computed in the space of b1,b2,b3. The distance set will be the
            closest possible to this value, compatible with the requirement of
            putting equispaced points between two special points (since extrema
            are included).
        :param float epsilon_length: threshold on lengths comparison, used
            to get the bravais lattice info. It has to be used if the
            user wants to be sure the right symmetries are recognized.
        :param float epsilon_angle: threshold on angles comparison, used
            to get the bravais lattice info. It has to be used if the
            user wants to be sure the right symmetries are recognized.

        """
        import warnings
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('the set_kpoints_path method has been deprecated, see {}'.format(DEPRECATION_DOCS_URL), DeprecationWarning)

        from aiida.tools.data.array.kpoints.legacy import get_explicit_kpoints_path

        try:
            cell = self.cell
        except AttributeError:
            cell = None

        try:
            pbc = self.pbc
        except AttributeError:
            pbc = None

        point_coords, path, bravais_info, explicit_kpoints, labels = get_explicit_kpoints_path(
            value=value, cell=cell, pbc=pbc, kpoint_distance=kpoint_distance, cartesian=cartesian,
            epsilon_length=epsilon_length,
            epsilon_angle=epsilon_angle
        )

        self.set_kpoints(explicit_kpoints)
        self.labels = labels


    def _find_bravais_info(self, epsilon_length=_default_epsilon_length,
                           epsilon_angle=_default_epsilon_angle):
        """
        Finds the Bravais lattice of the cell passed in input to the Kpoint class
        :note: We assume that the cell given by the cell property is the
        primitive unit cell.

        .. deprecated:: 0.11
           Use the methods inside the :ref:`aiida.tools.data.array.kpoints<AutomaticKpoints>` module instead.

        :return: a dictionary, with keys short_name, extended_name, index
                (index of the Bravais lattice), and sometimes variation (name of
                the variation of the Bravais lattice) and extra (a dictionary
                with extra parameters used by the get_special_points method)
        """
        import warnings
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('the _find_bravais_info method has been deprecated, see {}'.format(DEPRECATION_DOCS_URL), DeprecationWarning)

        from aiida.tools.data.array.kpoints.legacy import find_bravais_info
        return find_bravais_info(
            cell=self.cell, pbc=self.pbc,
            epsilon_length=epsilon_length,
            epsilon_angle=epsilon_angle
        )


    def find_bravais_lattice(self, epsilon_length=_default_epsilon_length,
                             epsilon_angle=_default_epsilon_angle):
        """
        Analyze the symmetry of the cell. Allows to relax or tighten the
        thresholds used to compare angles and lengths of the cell. Save the
        information of the cell used for later use (like getting special
        points). It has to be used if the user wants to be sure the right
        symmetries are recognized. Otherwise, this function is automatically
        called with the default values.

        If the right symmetry is not found, be sure also you are providing cells
        with enough digits.

        If node is already stored, just returns the symmetry found before
        storing (if any).

        .. deprecated:: 0.11
           Use the methods inside the :ref:`aiida.tools.data.array.kpoints<AutomaticKpoints>` module instead.

        :return (str) lattice_name: the name of the bravais lattice and its
             eventual variation
        """
        import warnings
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('the find_bravais_lattice method has been deprecated, see {}'.format(DEPRECATION_DOCS_URL), DeprecationWarning)

        if not self.is_stored:
            bravais_lattice = self._find_bravais_info(epsilon_length=epsilon_length,
                                                      epsilon_angle=epsilon_angle)
            self.bravais_lattice = bravais_lattice
        else:
            bravais_info = self.bravais_lattice

        try:
            variation = ", variation: {}".format(bravais_info['variation'])
        except KeyError:
            variation = ""

        return bravais_info['extended_name'] + variation

    def get_special_points(self, cartesian=False,
                           epsilon_length=_default_epsilon_length,
                           epsilon_angle=_default_epsilon_angle):
        """
        Get the special point and path of a given structure.

        References:

        - In 2D, coordinates are based on the paper:
          R. Ramirez and M. C. Bohm,  Int. J. Quant. Chem., XXX, pp. 391-411 (1986)

        - In 3D, coordinates are based on the paper:
          W. Setyawan, S. Curtarolo, Comp. Mat. Sci. 49, 299 (2010)

        .. deprecated:: 0.11
           Use the methods inside the :ref:`aiida.tools.data.array.kpoints<AutomaticKpoints>` module instead.

        :param cartesian: If true, returns points in cartesian coordinates.
            Crystal coordinates otherwise. Default=False
        :param epsilon_length: threshold on lengths comparison, used to get the bravais lattice info
        :param epsilon_angle: threshold on angles comparison, used to get the bravais lattice info
        :returns point_coords: a dictionary of point_name:point_coords key,values.
        :returns path: the suggested path which goes through all high symmetry lines.
            A list of lists for all path segments. e.g. [('G','X'),('X','M'),...]
            It's not necessarily a continuous line.
        :note: We assume that the cell given by the cell property is the primitive unit cell
        """
        import warnings
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn('the get_special_points method has been deprecated, see {}'.format(DEPRECATION_DOCS_URL), DeprecationWarning)

        from aiida.tools.data.array.kpoints.legacy import get_kpoints_path
        point_coords, path, bravais_info = get_kpoints_path(
            cell=self.cell, pbc=self.pbc, cartesian=cartesian,
            epsilon_length=epsilon_length,
            epsilon_angle=epsilon_angle
        )

        return point_coords, path
