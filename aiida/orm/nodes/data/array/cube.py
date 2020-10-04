# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Module of the GaussianCubeData class, defining the AiiDA data type for storing
Gaussian cube files.
"""
import os
import sys
import numpy as np

from .array import ArrayData


class GaussianCubeData(ArrayData):
    """Class that allows managing gaussian cube files."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        comment=None,
        voxel=None,
        origin=None,
        atomic_numbers=None,
        atomic_charges=None,
        atomic_coordinates=None,
        data=None,
        data_units=None,
        **kwargs
    ):
        super().__init__(**kwargs)
        if comment is not None:
            self.comment = comment
        if voxel is not None:
            self.voxel = voxel
        if origin is not None:
            self.origin = origin
        if atomic_numbers is not None:
            self.atomic_numbers = atomic_numbers
        if atomic_charges is not None:
            self.atomic_charges = atomic_charges
        if atomic_coordinates is not None:
            self.atomic_coordinates = atomic_coordinates
        if data is not None:
            self.data = data
        if data_units is not None:
            self.data_units = data_units

    @property
    def comment(self):
        """First two lines of the cube file that contain the comment"""
        return self.get_attribute('comment')

    @comment.setter
    def comment(self, comment):
        if isinstance(comment, (list, tuple)) and len(comment) == 2:
            if isinstance(comment[0], str) and isinstance(comment[1], str):
                self.set_attribute('comment', comment)
                return
        raise ValueError(f'The attibue `comment` must be a list or a tuple containing two strings, got: {comment}')

    @property
    def voxel(self):
        """Three vectors defining a voxel  (bohr)"""
        return self.get_array('voxel')

    @voxel.setter
    def voxel(self, voxel):
        self.set_array('voxel', voxel)

    @property
    def origin(self):
        """Position of the origin of the volumeric data (bohr)."""
        return self.get_array('origin')

    @origin.setter
    def origin(self, origin):
        self.set_array('origin', origin)

    @property
    def atomic_numbers(self):
        """Atomic numbers in the structure."""
        return self.get_array('atomic_numbers')

    @atomic_numbers.setter
    def atomic_numbers(self, atomic_numbers):
        self.set_array('atomic_numbers', atomic_numbers)

    @property
    def atomic_charges(self):
        """Atomic charges in the structure."""
        return self.get_array('atomic_charges')

    @atomic_charges.setter
    def atomic_charges(self, atomic_charges):
        self.set_array('atomic_charges', atomic_charges)

    @property
    def atomic_coordinates(self):
        """Atomic coordinates in the structure."""
        return self.get_array('atomic_coordinates')

    @atomic_coordinates.setter
    def atomic_coordinates(self, atomic_coordinates):
        self.set_array('atomic_coordinates', atomic_coordinates)

    @property
    def data(self):
        """3D array containing the mesh data."""
        return self.get_array('data')

    @data.setter
    def data(self, data):
        self.set_array('data', data)

    @property
    def data_units(self):
        """Units of the mesh data."""
        return self.get_attribute('data_units')

    @data_units.setter
    def data_units(self, data_units):
        self.set_attribute('data_units', data_units)

    def read(self, file, data_units=None, encoding='utf-8'):
        """Parse cube file."""

        # It should be either a string pointing to a file, or a file object.
        if isinstance(file, str):
            with open(file, mode='r', encoding=encoding) as fobj:
                fiter = iter(fobj.readlines())
        else:
            fiter = iter(file.readlines())

        # Comment.
        self.comment = [next(fiter).rstrip(), next(fiter).rstrip()]

        # Number of atoms and origin.
        line = next(fiter).split()
        natoms = int(line[0])
        self.origin = np.array(line[1:], dtype=float)

        # Data shape and voxel.
        shape = np.empty(3, dtype=int)
        voxel = np.empty((3, 3))
        for i in range(3):
            nmb, x, y, z = [float(s) for s in next(fiter).split()]
            shape[i] = int(nmb)
            voxel[i] = np.array([x, y, z])

        self.voxel = voxel

        # Atomic numbers, charges and positions.
        numbers = np.empty(natoms, int)
        charges = np.empty(natoms, int)
        positions = np.empty((natoms, 3))
        for i in range(natoms):
            line = next(fiter).split()
            numbers[i] = int(line[0])
            charges[i] = float(line[1])
            positions[i] = [float(s) for s in line[2:]]
        self.atomic_numbers = numbers
        self.atomic_charges = charges
        self.atomic_coordinates = positions

        # Data mesh.
        data = np.empty(shape[0] * shape[1] * shape[2], dtype=float)
        cursor = 0
        for i, line in enumerate(fiter):
            l_split = line.split()
            data[cursor:cursor + len(l_split)] = l_split
            cursor += len(l_split)
        self.data = data.reshape(shape)

        if data_units:
            self.data_units = data_units

    def _validate(self):
        """Check if the object contains all the data to construct a valid cube file."""
        all_good = True
        return_msg = ''
        for attr in ['comment', 'voxel', 'origin', 'atomic_numbers', 'atomic_charges', 'atomic_coordinates', 'data']:
            try:
                getattr(self, attr)
            except (AttributeError, KeyError):
                all_good = False
                return_msg += f'The attribute `{attr}` is not set.\n'

        return all_good and super()._validate(), return_msg

    def export(self, path, fileformat='cube', encoding='utf-8', overwrite=False, **kwargs):
        """Export data to the selected file."""

        if not self._validate():
            raise ValueError("Can't export the cube file.")

        if fileformat == 'cube':
            content = self._write_gaussian_cube()

        if path:
            if overwrite or not os.path.isfile(path):
                with open(path, mode='w', encoding=encoding) as fobj:
                    fobj.write(content)
            else:
                raise FileExistsError(
                    "Can't write to an existing file, please set `overwrite=True` to avoid this exception."
                )
        else:
            sys.stdout.write(content)

    def _write_gaussian_cube(self):
        """Write gaussian cube data into a string."""

        # Comment.
        filecontent = '\n'.join(self.comment) + '\n'
        natoms = self.atomic_numbers.shape[0]

        # Number of atoms and origin.
        filecontent += '{:5d} {:12.6f} {:12.6f} {:12.6f}\n'.format(
            natoms, self.origin[0], self.origin[1], self.origin[2]
        )

        # Data shape and voxel.
        for i in range(3):
            filecontent += '{:5d} {:12.6f} {:12.6f} {:12.6f}\n'.format(
                self.data.shape[i], self.voxel[i][0], self.voxel[i][1], self.voxel[i][2]
            )

        # Atomic numbers, charges and coordinates.
        for i in range(natoms):
            at_x, at_y, at_z = self.atomic_coordinates[i]
            filecontent += '{:5d} {:12.6f} {:12.6f} {:12.6f} {:12.6f}\n'.format(
                self.atomic_numbers[i], self.atomic_charges[i], at_x, at_y, at_z
            )

        # Data mesh.
        fmt = ' {:11.4e}'
        flat_data = self.data.ravel()
        for line in range(flat_data.shape[0] // 6):
            filecontent += (' {:11.4e}' * 6 + '\n').format(*flat_data[line * 6:(line + 1) * 6])
        left = flat_data.shape[0] % 6
        filecontent += (fmt * left + '\n').format(*flat_data[-left:])

        return filecontent
