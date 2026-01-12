###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""This module defines the classes related to Xy data. That is data that contains
collections of y-arrays bound to a single x-array, and the methods to operate
on them.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Sequence

import numpy as np

from aiida.common.exceptions import NotExistent

from .array import ArrayData

if TYPE_CHECKING:
    from numpy import ndarray

__all__ = ('XyData',)


def check_convert_single_to_tuple(item: Any | Sequence[Any]) -> Sequence[Any]:
    """Checks if the item is a list or tuple, and converts it to a list if it is
    not already a list or tuple

    :param item: an object which may or may not be a list or tuple
    :return: item_list: the input item unchanged if list or tuple and [item]
                        otherwise
    """
    if isinstance(item, (list, tuple)):
        return item

    return [item]


class XyData(ArrayData):
    """A subclass designed to handle arrays that have an "XY" relationship to
    each other. That is there is one array, the X array, and there are several
    Y arrays, which can be considered functions of X.

    The X array must be set first using :meth:`set_x`, followed by one or more Y arrays
    using :meth:`set_y`. Each Y array must have the same shape as the X array. All arrays
    are stored as 1D numpy arrays with shape ``(n,)`` where ``n`` is the number of data points::

        xy = XyData()
        xy.set_x(np.array([1, 2, 3]), 'position', 'm')  # shape: (3,)
        xy.set_y(np.array([10, 20, 30]), 'temperature', 'K')  # shape: (3,)

    Multiple Y arrays can be set at once by passing lists. Each Y array is stored
    separately and must match the X array shape::

        xy.set_y(
            [np.array([10, 20, 30]), np.array([5, 6, 7])],  # Two 1D arrays, each shape (3,)
            ['temperature', 'pressure'],
            ['K', 'Pa']
        )

    To retrieve data, use :meth:`get_x` to get the X array with its metadata, and :meth:`get_y`
    to get a list of tuples containing (name, array, units) for each Y array.

    .. note:: The :meth:`~aiida.orm.nodes.data.array.array.ArrayData.get_arraynames` method
        inherited from :class:`~aiida.orm.nodes.data.array.array.ArrayData` returns the internal
        storage names (e.g. ``['x_array', 'y_array_0', 'y_array_1']``), not the user-provided names.
        To get the user-provided names, use :meth:`get_y` and extract the names from the returned tuples.
    """

    def __init__(
        self,
        x_array: 'ndarray' | None = None,
        y_arrays: 'ndarray' | list['ndarray'] | None = None,
        *,
        x_name: str | None = None,
        x_units: str | None = None,
        y_names: str | list[str] | None = None,
        y_units: str | list[str] | None = None,
        **kwargs,
    ):
        """Construct a new instance, optionally setting the x and y arrays.

        .. note:: If the ``x_array`` is specified, all other keywords need to be specified as well.

        :param x_array: The x array.
        :param y_arrays: The y arrays.
        :param x_name: The name of the x array.
        :param x_units: The unit of the x array.
        :param y_names: The names of the y arrays.
        :param y_units: The units of the y arrays.
        """
        super().__init__(**kwargs)

        if x_array is not None:
            self.set_x(x_array, x_name, x_units)  # type: ignore[arg-type]
            self.set_y(y_arrays, y_names, y_units)  # type: ignore[arg-type]

    @staticmethod
    def _arrayandname_validator(array: 'ndarray', name: str, units: str) -> None:
        """Validates that the array is an numpy.ndarray and that the name is
        of type str. Raises TypeError or ValueError if this not the case.
        """
        if not isinstance(name, str):
            raise TypeError('The name must always be a str.')

        if not isinstance(array, np.ndarray):
            raise TypeError('The input array must always be a numpy array')
        try:
            array.astype(float)
        except ValueError as exc:
            raise TypeError('The input array must only contain floats') from exc
        if not isinstance(units, str):
            raise TypeError('The units must always be a str.')

    def set_x(self, x_array: 'ndarray', x_name: str, x_units: str) -> None:
        """Sets the array and the name for the x values.

        :param x_array: A numpy.ndarray, containing only floats
        :param x_name: a string for the x array name
        :param x_units: the units of x
        """
        self._arrayandname_validator(x_array, x_name, x_units)
        self.base.attributes.set('x_name', x_name)
        self.base.attributes.set('x_units', x_units)
        self.set_array('x_array', x_array)

    def set_y(
        self, y_arrays: 'ndarray' | Sequence['ndarray'], y_names: str | Sequence[str], y_units: str | Sequence[str]
    ) -> None:
        """Set array(s) for the y part of the dataset. Also checks if the
        x_array has already been set, and that, the shape of the y_arrays
        agree with the x_array.
        :param y_arrays: A list of y_arrays, numpy.ndarray
        :param y_names: A list of strings giving the names of the y_arrays
        :param y_units: A list of strings giving the units of the y_arrays
        """
        # for the case of single name, array, tag input converts to a list
        y_arrays = check_convert_single_to_tuple(y_arrays)
        y_names = check_convert_single_to_tuple(y_names)
        y_units = check_convert_single_to_tuple(y_units)

        # checks that the input lengths match
        if len(y_arrays) != len(y_names):
            raise ValueError('Length of arrays and names do not match!')
        if len(y_units) != len(y_names):
            raise ValueError('Length of units does not match!')

        # Try to get the x_array
        try:
            x_array = self.get_x()[1]
        except NotExistent as exc:
            raise ValueError('X array has not been set yet') from exc
        # validate each of the y_arrays
        for num, (y_array, y_name, y_unit) in enumerate(zip(y_arrays, y_names, y_units)):
            self._arrayandname_validator(y_array, y_name, y_unit)
            if np.shape(y_array) != np.shape(x_array):
                raise ValueError(f'y_array {y_name} does not have the same shape as x_array!')
            self.set_array(f'y_array_{num}', y_array)

        # if the y_arrays pass the initial validation, sets each
        self.base.attributes.set('y_names', y_names)
        self.base.attributes.set('y_units', y_units)

    def get_x(self) -> tuple[str, 'ndarray', str]:
        """Tries to retrieve the x array and x name raises a NotExistent
        exception if no x array has been set yet.
        :return x_name: the name set for the x_array
        :return x_array: the x array set earlier
        :return x_units: the x units set earlier
        """
        try:
            x_name = self.base.attributes.get('x_name')
            x_array = self.get_array('x_array')
            x_units = self.base.attributes.get('x_units')
        except (KeyError, AttributeError):
            raise NotExistent('No x array has been set yet!')
        return x_name, x_array, x_units

    def get_y(self) -> list[tuple[str, 'ndarray', str]]:
        """Tries to retrieve the y arrays and the y names, raises a
        NotExistent exception if they have not been set yet, or cannot be
        retrieved
        :return y_names: list of strings naming the y_arrays
        :return y_arrays: list of y_arrays
        :return y_units: list of strings giving the units for the y_arrays
        """
        try:
            y_names = self.base.attributes.get('y_names')
        except (KeyError, AttributeError):
            raise NotExistent('No y names has been set yet!')
        try:
            y_units = self.base.attributes.get('y_units')
        except (KeyError, AttributeError):
            raise NotExistent('No y units has been set yet!')
        y_arrays = []
        try:
            for i in range(len(y_names)):
                y_arrays += [self.get_array(f'y_array_{i}')]
        except (KeyError, AttributeError):
            raise NotExistent(f'Could not retrieve array associated with y array {y_names[i]}')
        return list(zip(y_names, y_arrays, y_units))
