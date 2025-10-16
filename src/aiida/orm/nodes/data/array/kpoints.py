###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module of the KpointsData class, defining the AiiDA data type for storing
lists and meshes of k-points (i.e., points in the reciprocal space of a
periodic crystal structure).
"""

import typing as t

import numpy

from aiida.common.pydantic import MetadataField

from .array import ArrayData

__all__ = ('KpointsData',)

_DEFAULT_EPSILON_LENGTH = 1e-5
_DEFAULT_EPSILON_ANGLE = 1e-5


class KpointsData(ArrayData):
    """Class to handle array of kpoints in the Brillouin zone. Provide methods to
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

    class Model(ArrayData.Model):
        labels: t.List[str] = MetadataField(description='Labels associated with the list of kpoints')
        label_numbers: t.List[int] = MetadataField(description='Index of the labels in the list of kpoints')
        mesh: t.List[int] = MetadataField(description='Mesh of kpoints')
        offset: t.List[float] = MetadataField(description='Offset of kpoints')
        cell: t.List[t.List[float]] = MetadataField(description='Unit cell of the crystal, in Angstroms')
        pbc1: bool = MetadataField(description='True if the first lattice vector is periodic')
        pbc2: bool = MetadataField(description='True if the second lattice vector is periodic')
        pbc3: bool = MetadataField(description='True if the third lattice vector is periodic')

    def get_description(self):
        """Returns a string with infos retrieved from  kpoints node's properties.
        :param node:
        :return: retstr
        """
        try:
            mesh = self.get_kpoints_mesh()
            return 'Kpoints mesh: {}x{}x{} (+{:.1f},{:.1f},{:.1f})'.format(
                mesh[0][0], mesh[0][1], mesh[0][2], mesh[1][0], mesh[1][1], mesh[1][2]
            )
        except AttributeError:
            try:
                return f'(Path of {len(self.get_kpoints())} kpts)'
            except OSError:
                return self.node_type

    @property
    def cell(self):
        """The crystal unit cell. Rows are the crystal vectors in Angstroms.
        :return: a 3x3 numpy.array
        """
        return numpy.array(self.base.attributes.get('cell'))

    @cell.setter
    def cell(self, value):
        """Set the crystal unit cell
        :param value: a 3x3 list/tuple/array of numbers (units = Angstroms).
        """
        self._set_cell(value)

    def _set_cell(self, value):
        """Validate if 'value' is a allowed crystal unit cell
        :param value: something compatible with a 3x3 tuple of floats
        """
        from aiida.common.exceptions import ModificationNotAllowed
        from aiida.orm.nodes.data.structure import _get_valid_cell

        if self.is_stored:
            raise ModificationNotAllowed('KpointsData cannot be modified, it has already been stored')

        the_cell = _get_valid_cell(value)

        self.base.attributes.set('cell', the_cell)

    @property
    def pbc(self):
        """The periodic boundary conditions along the vectors a1,a2,a3.

        :return: a tuple of three booleans, each one tells if there are periodic
            boundary conditions for the i-th real-space direction (i=1,2,3)
        """
        # return copy.deepcopy(self._pbc)
        return (self.base.attributes.get('pbc1'), self.base.attributes.get('pbc2'), self.base.attributes.get('pbc3'))

    @pbc.setter
    def pbc(self, value):
        """Set the value of pbc, i.e. a tuple of three booleans, indicating if the
        cell is periodic in the 1,2,3 crystal direction
        """
        self._set_pbc(value)

    def _set_pbc(self, value):
        """Validate the pbc, then store them"""
        from aiida.common.exceptions import ModificationNotAllowed
        from aiida.orm.nodes.data.structure import get_valid_pbc

        if self.is_stored:
            raise ModificationNotAllowed('The KpointsData object cannot be modified, it has already been stored')
        the_pbc = get_valid_pbc(value)
        self.base.attributes.set('pbc1', the_pbc[0])
        self.base.attributes.set('pbc2', the_pbc[1])
        self.base.attributes.set('pbc3', the_pbc[2])

    @property
    def labels(self):
        """Labels associated with the list of kpoints.
        List of tuples with kpoint index and kpoint name: ``[(0,'G'),(13,'M'),...]``
        """
        label_numbers = self.base.attributes.get('label_numbers', None)
        labels = self.base.attributes.get('labels', None)
        if labels is None or label_numbers is None:
            return None
        return list(zip(label_numbers, labels))

    @labels.setter
    def labels(self, value):
        self._set_labels(value)

    def _set_labels(self, value):
        """Set label names. Must pass in input a list like: ``[[0,'X'],[34,'L'],... ]``"""
        # check if kpoints were set
        try:
            self.get_kpoints()
        except AttributeError:
            raise AttributeError('Kpoints must be set before the labels')

        if value is None:
            value = []

        try:
            label_numbers = [int(i[0]) for i in value]
        except ValueError:
            raise ValueError('The input must contain an integer index, to map the labels into the kpoint list')
        labels = [str(i[1]) for i in value]

        if any(i > len(self.get_kpoints()) - 1 for i in label_numbers):
            raise ValueError('Index of label exceeding the list of kpoints')

        self.base.attributes.set('label_numbers', label_numbers)
        self.base.attributes.set('labels', labels)

    def _change_reference(self, kpoints, to_cartesian=True):
        """Change reference system, from cartesian to crystal coordinates (units of b1,b2,b3) or viceversa.
        :param kpoints: a list of (3) point coordinates
        :return kpoints: a list of (3) point coordinates in the new reference
        """
        if not isinstance(kpoints, numpy.ndarray):
            raise ValueError('kpoints must be a numpy.array for method change_reference()')

        try:
            rec_cell = self.reciprocal_cell
        except AttributeError:
            # rec_cell = numpy.eye(3)
            raise AttributeError('Cannot use cartesian coordinates without having defined a cell')

        trec_cell = numpy.transpose(numpy.array(rec_cell))
        if to_cartesian:
            matrix = trec_cell
        else:
            matrix = numpy.linalg.inv(trec_cell)

        # note: kpoints is a list Nx3, matrix is 3x3.
        # hence, first transpose kpoints, then multiply, finally transpose it back
        return numpy.transpose(numpy.dot(matrix, numpy.transpose(kpoints)))

    def set_cell_from_structure(self, structuredata):
        """Set a cell to be used for symmetry analysis from an AiiDA structure.
        Inherits both the cell and the pbc's.
        To set manually a cell, use "set_cell"

        :param structuredata: an instance of StructureData
        """
        from aiida.orm import StructureData

        if not isinstance(structuredata, StructureData):
            raise ValueError(
                'An instance of StructureData should be passed to ' 'the KpointsData, found instead {}'.format(
                    structuredata.__class__
                )
            )
        cell = structuredata.cell
        self.set_cell(cell, structuredata.pbc)

    def set_cell(self, cell, pbc=None):
        """Set a cell to be used for symmetry analysis.
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

    @property
    def reciprocal_cell(self):
        """Compute reciprocal cell from the internally set cell.

        :returns: reciprocal cell in units of 1/Angstrom with cell vectors stored as rows.
            Use e.g. reciprocal_cell[0] to access the first reciprocal cell vector.
        """
        the_cell = numpy.array(self.cell)
        reciprocal_cell = 2.0 * numpy.pi * numpy.linalg.inv(the_cell).transpose()
        return reciprocal_cell

    def set_kpoints_mesh(self, mesh, offset=None):
        """Set KpointsData to represent a uniformily spaced mesh of kpoints in the
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
            the_mesh = [int(i) for i in mesh]
            if len(the_mesh) != 3:
                raise ValueError
        except (IndexError, ValueError, TypeError):
            raise ValueError('The kpoint mesh must be a list of three integers')
        if offset is None:
            offset = [0.0, 0.0, 0.0]
        try:
            the_offset = [float(i) for i in offset]
            if len(the_offset) != 3:
                raise ValueError
        except (IndexError, ValueError, TypeError):
            raise ValueError('The offset must be a list of three floats')
        # check that there is no list of kpoints saved already
        # I cannot have both of them at the same time
        try:
            _ = self.get_array('kpoints')
            raise ModificationNotAllowed('KpointsData has already a kpoint-list stored')
        except KeyError:
            pass

        # store
        self.base.attributes.set('mesh', the_mesh)
        self.base.attributes.set('offset', the_offset)

    def get_kpoints_mesh(self, print_list=False):
        """Get the mesh of kpoints.

        :param print_list: default=False. If True, prints the mesh of kpoints as a list

        :raise AttributeError: if no mesh has been set
        :return mesh,offset: (if print_list=False) a list of 3 integers and a list of three
                floats 0<x<1, representing the mesh and the offset of kpoints
        :return kpoints: (if print_list = True) an explicit list of kpoints coordinates,
                similar to what returned by get_kpoints()
        """
        mesh = self.base.attributes.get('mesh')
        offset = self.base.attributes.get('offset')

        if not print_list:
            return mesh, offset

        kpoints = numpy.mgrid[0 : mesh[0], 0 : mesh[1], 0 : mesh[2]]
        kpoints = kpoints.reshape(3, -1).T
        offset_kpoints = kpoints + numpy.array(offset)
        offset_kpoints[:, 0] /= mesh[0]
        offset_kpoints[:, 1] /= mesh[1]
        offset_kpoints[:, 2] /= mesh[2]
        return offset_kpoints

    def set_kpoints_mesh_from_density(self, distance, offset=None, force_parity=False):
        """Set a kpoints mesh using a kpoints density, expressed as the maximum
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
        if offset is None:
            offset = [0.0, 0.0, 0.0]

        try:
            rec_cell = self.reciprocal_cell
        except AttributeError:
            # rec_cell = numpy.eye(3)
            raise AttributeError('Cannot define a mesh from a density without having defined a cell')
        # I first round to the fifth digit |b|/distance (to avoid that e.g.
        # 3.00000001 becomes 4)
        kpointsmesh = [
            max(int(numpy.ceil(round(numpy.linalg.norm(b) / distance, 5))), 1) if pbc else 1
            for pbc, b in zip(self.pbc, rec_cell)
        ]
        if force_parity:
            kpointsmesh = [k + (k % 2) if pbc else 1 for pbc, k in zip(self.pbc, kpointsmesh)]
        self.set_kpoints_mesh(kpointsmesh, offset=offset)

    @property
    def _dimension(self):
        """Dimensionality of the structure, found from its pbc (i.e. 1 if it's a 1D
        structure, 2 if its 2D, 3 if it's 3D ...).
        :return dimensionality: 0, 1, 2 or 3
        :note: will return 3 if pbc has not been set beforehand
        """
        try:
            return sum(self.pbc)
        except AttributeError:
            return 3

    def _validate_kpoints_weights(self, kpoints, weights):
        """Validate the list of kpoints and of weights before storage.
        Kpoints and weights must be convertible respectively to an array of
        N x dimension and N floats
        """
        kpoints = numpy.array(kpoints)

        # I cannot just use `if not kpoints` because it's a numpy array and
        # `not` of a numpy array does not work
        if len(kpoints) == 0:
            if self._dimension == 0:
                # replace empty list by Gamma point
                kpoints = numpy.array([[0.0, 0.0, 0.0]])
            else:
                raise ValueError(
                    'empty kpoints list is valid only in zero dimension'
                    '; instead here with have {} dimensions'
                    ''.format(self._dimension)
                )

        if len(kpoints.shape) <= 1:
            # list of scalars is accepted only in the 0D and 1D cases
            if self._dimension <= 1:
                # replace by singletons
                kpoints = kpoints.reshape(kpoints.shape[0], 1)
            else:
                raise ValueError(f'kpoints must be a list of lists in {self._dimension}D case')

        if kpoints.dtype != numpy.dtype(float):
            raise ValueError(f'kpoints must be an array of type floats. Found instead {kpoints.dtype}')

        if kpoints.shape[1] < self._dimension:
            raise ValueError(
                'In a system which has {0} dimensions, kpoint need'
                'more than {0} coordinates (found instead {1})'.format(self._dimension, kpoints.shape[1])
            )

        if weights is not None:
            weights = numpy.array(weights)
            if weights.shape[0] != kpoints.shape[0]:
                raise ValueError(f'Found {weights.shape[0]} weights but {kpoints.shape[0]} kpoints')
            if weights.dtype != numpy.dtype(float):
                raise ValueError(f'weights must be an array of type floats. Found instead {weights.dtype}')

        return kpoints, weights

    def set_kpoints(self, kpoints, cartesian=False, labels=None, weights=None, fill_values=0):
        """Set the list of kpoints. If a mesh has already been stored, raise a ModificationNotAllowed

        :param kpoints: a list of kpoints, each kpoint being a list of one, two
            or three coordinates, depending on self.pbc: if structure is 1D
            (only one True in self.pbc) one allows singletons or scalars for
            each k-point, if it's 2D it can be a length-2 list, and in all
            cases it can be a length-3 list.

        Examples
        --------

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
        the_kpoints, the_weights = self._validate_kpoints_weights(kpoints, weights)

        # if k-points have less than 3 coordinates (low dimensionality), fill
        # with constant values the non-periodic dimensions
        if the_kpoints.shape[1] < 3:
            if numpy.isscalar(fill_values):
                # replace scalar by a list of 3-the_kpoints.shape[1] identical
                # elements
                fill_values = [fill_values] * (3 - the_kpoints.shape[1])

            if len(fill_values) < 3 - the_kpoints.shape[1]:
                raise ValueError(f'fill_values should be either a scalar or a length-{3 - the_kpoints.shape[1]} list')
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
                            (tmp_kpoints, the_kpoints[:, i_kpts].reshape((the_kpoints.shape[0], 1)))
                        )
                        i_kpts += 1
                    else:
                        tmp_kpoints = numpy.hstack(
                            (tmp_kpoints, numpy.ones((the_kpoints.shape[0], 1)) * fill_values[i_fill])
                        )
                        i_fill += 1
                the_kpoints = tmp_kpoints

        # change reference and always store in crystal coords
        if cartesian:
            the_kpoints = self._change_reference(the_kpoints, to_cartesian=False)

        # check that we did not saved a mesh already
        if self.base.attributes.get('mesh', None) is not None:
            raise ModificationNotAllowed('KpointsData has already a mesh stored')

        # store
        self.set_array('kpoints', the_kpoints)
        if the_weights is not None:
            self.set_array('weights', the_weights)
        if labels is not None:
            self.labels = labels

    def get_kpoints(self, also_weights=False, cartesian=False):
        """Return the list of kpoints

        :param also_weights: if True, returns also the list of weights.
            Default = False
        :param cartesian: if True, returns points in cartesian coordinates,
            otherwise, returns in crystal coordinates. Default = False.
        """
        try:
            kpoints = numpy.array(self.get_array('kpoints'))
        except KeyError:
            raise AttributeError('Before the get, first set a list of kpoints')

        if cartesian:
            kpoints = self._change_reference(kpoints, to_cartesian=True)

        if also_weights:
            try:
                the_weights = self.get_array('weights')
            except KeyError:
                raise AttributeError('No weights were set')

            weights = numpy.array(the_weights)
            return kpoints, weights

        return kpoints
