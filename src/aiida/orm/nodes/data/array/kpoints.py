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

from __future__ import annotations

import typing as t

import numpy as np
import pydantic as pdt

from aiida.common import exceptions
from aiida.orm.decorators import attribute
from aiida.orm.models.adapters import NumpyArrayListAdapter
from aiida.orm.nodes.data.array.array import ArrayData

__all__ = ('KpointsData',)

_DEFAULT_EPSILON_LENGTH = 1e-5
_DEFAULT_EPSILON_ANGLE = 1e-5


class KpointsData(ArrayData):
    """Class to handle array of kpoints in the Brillouin zone.

    The class provides methods to generate either user-defined k-points or path
    of k-points along symmetry lines. Internally, all k-points are defined in
    terms of crystal (fractional) coordinates. Cell andlattice vector coordinates
    are in Angstroms, reciprocal lattice vectors in Angstrom^-1.

    :note: The methods setting and using the Bravais lattice info assume the
    PRIMITIVE unit cell is provided in input to the set_cell or
    ``set_cell_from_structure`` methods.
    """

    _attributes_model_config = ArrayData._attributes_model_config

    _requires_array = False

    @attribute(
        model_adapter=NumpyArrayListAdapter(),
        model_field_info=pdt.fields.FieldInfo(annotation=list[list[float]]),
    )
    def cell(self) -> np.ndarray | None:
        """The crystal unit cell, with rows representing crystal vectors in Angstroms."""
        cell = self.base.attributes.get('cell', None)
        return None if cell is None else np.array(cell)

    @cell.setter
    def cell(self, value: np.ndarray | None) -> None:
        raise AttributeError("cannot set 'cell' directly; use 'set_cell' instead")

    @attribute
    def pbc1(self) -> bool | None:
        """Periodicity in the first lattice vector direction."""
        return self.base.attributes.get('pbc1', None)

    @pbc1.setter
    def pbc1(self, value: bool) -> None:
        self.base.attributes.set('pbc1', value)

    @attribute
    def pbc2(self) -> bool | None:
        """Periodicity in the second lattice vector direction."""
        return self.base.attributes.get('pbc2', None)

    @pbc2.setter
    def pbc2(self, value: bool) -> None:
        self.base.attributes.set('pbc2', value)

    @attribute
    def pbc3(self) -> bool | None:
        """Periodicity in the third lattice vector direction."""
        return self.base.attributes.get('pbc3', None)

    @pbc3.setter
    def pbc3(self, value: bool) -> None:
        self.base.attributes.set('pbc3', value)

    @attribute
    def mesh(self) -> list[int] | None:
        """The mesh of kpoints."""
        return self.base.attributes.get('mesh', None)

    @mesh.setter
    def mesh(self, value: list[int] | None) -> None:
        raise AttributeError("cannot set 'mesh' directly; use 'set_kpoints_mesh' instead")

    @attribute
    def offset(self) -> list[float] | None:
        """The offset of the kpoints mesh."""
        return self.base.attributes.get('offset', None)

    @offset.setter
    def offset(self, value: list[float] | None) -> None:
        raise AttributeError("cannot set 'offset' directly; use 'set_kpoints_mesh' instead")

    @attribute
    def labels(self) -> list[str] | None:
        """The labels associated with the list of kpoints."""
        return self.base.attributes.get('labels', None)

    @labels.setter
    def labels(self, value: list[str] | None) -> None:
        raise AttributeError("cannot set 'labels' directly; use 'set_labels' instead")

    @attribute
    def label_numbers(self) -> list[int] | None:
        """The indices of the labels in the list of kpoints."""
        return self.base.attributes.get('label_numbers', None)

    @label_numbers.setter
    def label_numbers(self, value: list[int] | None) -> None:
        raise AttributeError("cannot set 'label_numbers' directly; use 'set_labels' instead")

    @property
    def pbc(self) -> tuple[bool, bool, bool]:
        """The periodic boundary conditions along the vectors a1,a2,a3.

        :return: a tuple of three booleans, each one tells if there are periodic
            boundary conditions for the i-th real-space direction (i=1,2,3)
        """
        return self.pbc1 or False, self.pbc2 or False, self.pbc3 or False

    @pbc.setter
    def pbc(self, value: t.Sequence[bool]) -> None:
        raise AttributeError("cannot set 'pbc' directly; use 'set_pbc' instead")

    @property
    def reciprocal_cell(self) -> np.ndarray:
        """Compute reciprocal cell from the internally set cell.

        :returns: reciprocal cell in units of 1/Angstrom with cell vectors stored as rows.
            Use e.g. reciprocal_cell[0] to access the first reciprocal cell vector.
        """
        if self.cell is None:
            raise AttributeError('Cannot compute the reciprocal cell without having defined a cell')

        return 2.0 * np.pi * np.linalg.inv(self.cell).transpose()

    def get_description(self):
        """Returns a string with infos retrieved from  kpoints node's properties.
        :param node:
        :return: retstr
        """
        try:
            mesh = self.get_kpoints_mesh()
            return (
                f'Kpoints mesh: {mesh[0][0]}x{mesh[0][1]}x{mesh[0][2]} '
                f'(+{mesh[1][0]:.1f},{mesh[1][1]:.1f},{mesh[1][2]:.1f})'
            )
        except AttributeError:
            try:
                return f'(Path of {len(self.get_kpoints())} kpts)'
            except OSError:
                return self.node_type

    def get_labels(self) -> list[tuple[int, str]] | None:
        """Return the list of (number, label) tuples associated with the kpoints."""
        if self.labels is None or self.label_numbers is None:
            return None

        return list(zip(self.label_numbers, self.labels))

    def set_labels(self, value: t.Sequence[t.Sequence[t.Any]] | None) -> None:
        """Set label names. Must pass in input a list like: ``[[0,'X'],[34,'L'],... ]``"""
        try:
            kpoints = self.get_kpoints()
        except AttributeError:
            raise AttributeError('Kpoints must be set before the labels')

        if value is None:
            value = []

        try:
            label_numbers = [int(item[0]) for item in value]
        except ValueError:
            raise ValueError('The input must contain an integer index, to map the labels into the kpoint list')

        labels = [str(item[1]) for item in value]

        if any(index > len(kpoints) - 1 for index in label_numbers):
            raise ValueError('Index of label exceeding the list of kpoints')

        self.base.attributes.set('label_numbers', label_numbers)
        self.base.attributes.set('labels', labels)

    def set_cell_from_structure(self, structuredata):
        """Set a cell to be used for symmetry analysis from an AiiDA structure.
        Inherits both the cell and the pbc's.
        To set manually a cell, use "set_cell"

        :param structuredata: an instance of StructureData
        """
        from aiida.orm import StructureData

        if not isinstance(structuredata, StructureData):
            msg = (
                'An instance of StructureData should be passed to the KpointsData, '
                f'found instead {structuredata.__class__}'
            )
            raise ValueError(msg)

        self.set_cell(structuredata.cell, structuredata.pbc)

    def set_cell(self, cell, pbc=None):
        """Set a cell to be used for symmetry analysis.
        To set a cell from an AiiDA structure, use "set_cell_from_structure".

        :param cell: 3x3 matrix of cell vectors. Orientation: each row
                     represent a lattice vector. Units are Angstroms.
        :param pbc: list of 3 booleans, True if in the nth crystal direction the
                    structure is periodic. Default = [True,True,True]
        """
        from aiida.orm.nodes.data.structure import _get_valid_cell

        the_cell = _get_valid_cell(cell)
        self.base.attributes.set('cell', the_cell)

        self.set_pbc([True, True, True] if pbc is None else pbc)

    def set_pbc(self, value: t.Sequence[bool]) -> None:
        """Set the periodic boundary conditions."""
        from aiida.orm.nodes.data.structure import get_valid_pbc

        if self.is_stored:
            msg = f'{self.__class__.__name__} cannot be modified once stored'
            raise exceptions.ModificationNotAllowed(msg)

        pbc = get_valid_pbc(value)
        self.base.attributes.set_many(
            {
                'pbc1': pbc[0],
                'pbc2': pbc[1],
                'pbc3': pbc[2],
            }
        )

    def set_kpoints_mesh(self, mesh, offset=None):
        """Set KpointsData to represent a uniformly spaced mesh of kpoints in the
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

        try:
            the_mesh = [int(item) for item in mesh]
            if len(the_mesh) != 3:
                raise ValueError
        except (IndexError, ValueError, TypeError):
            raise ValueError('The kpoint mesh must be a list of three integers')

        if offset is None:
            offset = [0.0, 0.0, 0.0]

        try:
            the_offset = [float(item) for item in offset]
            if len(the_offset) != 3:
                raise ValueError
        except (IndexError, ValueError, TypeError):
            raise ValueError('The offset must be a list of three floats')

        try:
            self.get_array('kpoints')
            raise ModificationNotAllowed('KpointsData has already a kpoint-list stored')
        except KeyError:
            pass

        self.base.attributes.set_many(
            {
                'mesh': the_mesh,
                'offset': the_offset,
            }
        )

    def get_kpoints_mesh(self, print_list=False):
        """Get the mesh of kpoints.

        :param print_list: default=False. If True, prints the mesh of kpoints as a list

        :raise AttributeError: if no mesh has been set
        :return mesh,offset: (if print_list=False) a list of 3 integers and a list of three
                floats 0<x<1, representing the mesh and the offset of kpoints
        :return kpoints: (if print_list = True) an explicit list of kpoints coordinates,
                similar to what returned by get_kpoints()
        """
        mesh = self.mesh
        offset = self.offset

        if mesh is None or offset is None:
            raise AttributeError('No kpoints mesh has been set')

        if not print_list:
            return mesh, offset

        kpoints = np.mgrid[0 : mesh[0], 0 : mesh[1], 0 : mesh[2]]
        kpoints = kpoints.reshape(3, -1).T
        offset_kpoints = kpoints + np.array(offset)
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
            raise AttributeError('Cannot define a mesh from a density without having defined a cell')

        kpointsmesh = [
            max(int(np.ceil(round(np.linalg.norm(b) / distance, 5))), 1) if pbc else 1
            for pbc, b in zip(self.pbc, rec_cell)
        ]

        if force_parity:
            kpointsmesh = [k + (k % 2) if pbc else 1 for pbc, k in zip(self.pbc, kpointsmesh)]

        self.set_kpoints_mesh(kpointsmesh, offset=offset)

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

        the_kpoints, the_weights = self._validate_kpoints_weights(kpoints, weights)

        if the_kpoints.shape[1] < 3:
            if np.isscalar(fill_values):
                fill_values = [fill_values] * (3 - the_kpoints.shape[1])

            if len(fill_values) < 3 - the_kpoints.shape[1]:
                msg = f'fill_values should be either a scalar or a length-{3 - the_kpoints.shape[1]} list'
                raise ValueError(msg)

            tmp_kpoints = np.zeros((the_kpoints.shape[0], 0))
            i_kpts = 0
            i_fill = 0

            for idim in range(3):
                if self.pbc[idim]:
                    tmp_kpoints = np.hstack((tmp_kpoints, the_kpoints[:, i_kpts].reshape((the_kpoints.shape[0], 1))))
                    i_kpts += 1
                else:
                    tmp_kpoints = np.hstack((tmp_kpoints, np.ones((the_kpoints.shape[0], 1)) * fill_values[i_fill]))
                    i_fill += 1

            the_kpoints = tmp_kpoints

        if cartesian:
            the_kpoints = self._change_reference(the_kpoints, to_cartesian=False)

        if self.mesh is not None:
            raise ModificationNotAllowed('KpointsData has already a mesh stored')

        self.set_array('kpoints', the_kpoints)

        if the_weights is not None:
            self.set_array('weights', the_weights)

        if labels is not None:
            self.set_labels(labels)

    def get_kpoints(self, also_weights=False, cartesian=False):
        """Return the list of kpoints

        :param also_weights: if True, returns also the list of weights.
            Default = False
        :param cartesian: if True, returns points in cartesian coordinates,
            otherwise, returns in crystal coordinates. Default = False.
        """
        try:
            kpoints = np.array(self.get_array('kpoints'))
        except KeyError:
            raise AttributeError('Before the get, first set a list of kpoints')

        if cartesian:
            kpoints = self._change_reference(kpoints, to_cartesian=True)

        if also_weights:
            try:
                the_weights = self.get_array('weights')
            except KeyError:
                raise AttributeError('No weights were set')

            return kpoints, np.array(the_weights)

        return kpoints

    @property
    def _dimension(self):
        """Dimensionality of the structure, found from its pbc (i.e. 1 if it's a 1D
        structure, 2 if its 2D, 3 if it's 3D ...).
        :return dimensionality: 0, 1, 2 or 3
        """
        return sum(self.pbc)

    def _change_reference(self, kpoints, to_cartesian=True):
        """Change reference system, from cartesian to crystal coordinates (units of b1,b2,b3) or viceversa.
        :param kpoints: a list of (3) point coordinates
        :return kpoints: a list of (3) point coordinates in the new reference
        """
        if not isinstance(kpoints, np.ndarray):
            raise ValueError('kpoints must be a np.array for method change_reference()')

        try:
            rec_cell = self.reciprocal_cell
        except AttributeError:
            raise AttributeError('Cannot use cartesian coordinates without having defined a cell')

        trec_cell = np.transpose(np.array(rec_cell))
        matrix = trec_cell if to_cartesian else np.linalg.inv(trec_cell)

        return np.transpose(np.dot(matrix, np.transpose(kpoints)))

    def _validate_kpoints_weights(self, kpoints, weights):
        """Validate the list of kpoints and of weights before storage.
        Kpoints and weights must be convertible respectively to an array of
        N x dimension and N floats
        """
        kpoints = np.array(kpoints)

        if len(kpoints) == 0:
            if self._dimension == 0:
                kpoints = np.array([[0.0, 0.0, 0.0]])
            else:
                msg = (
                    'empty kpoints list is valid only in zero dimension; '
                    f'instead here with have {self._dimension} dimensions'
                )
                raise ValueError(msg)

        if len(kpoints.shape) <= 1:
            if self._dimension <= 1:
                kpoints = kpoints.reshape(kpoints.shape[0], 1)
            else:
                msg = f'kpoints must be a list of lists in {self._dimension}D case'
                raise ValueError(msg)

        if kpoints.dtype != np.dtype(float):
            msg = f'kpoints must be an array of type floats. Found instead {kpoints.dtype}'
            raise ValueError(msg)

        if kpoints.shape[1] < self._dimension:
            msg = (
                f'In a system which has {self._dimension} dimensions, '
                f'kpoint need more than {self._dimension} coordinates (found instead {kpoints.shape[1]})'
            )
            raise ValueError(msg)

        if weights is not None:
            weights = np.array(weights)

            if weights.shape[0] != kpoints.shape[0]:
                msg = f'Found {weights.shape[0]} weights but {kpoints.shape[0]} kpoints'
                raise ValueError(msg)

            if weights.dtype != np.dtype(float):
                msg = f'weights must be an array of type floats. Found instead {weights.dtype}'
                raise ValueError(msg)

        return kpoints, weights

    def _validate(self) -> None:
        """Validate the kpoints representation."""
        super()._validate()

        has_kpoints = 'kpoints' in self.get_arraynames()
        has_mesh = self.mesh is not None

        if has_kpoints and has_mesh:
            raise exceptions.ValidationError('KpointsData cannot contain both a mesh and an explicit kpoints list.')

        if not has_kpoints and not has_mesh:
            raise exceptions.ValidationError('KpointsData must contain either a mesh or an explicit kpoints list.')

        if has_mesh and self.offset is None:
            raise exceptions.ValidationError('A kpoints mesh must define an offset.')

        if self.labels is not None or self.label_numbers is not None:
            if not has_kpoints:
                raise exceptions.ValidationError('Kpoint labels can only be defined for an explicit kpoints list.')

            if self.labels is None or self.label_numbers is None:
                raise exceptions.ValidationError(
                    'Kpoint labels and label numbers must either both be defined or both absent.'
                )

            if len(self.labels) != len(self.label_numbers):
                raise exceptions.ValidationError('Kpoint labels and label numbers must have the same length.')
