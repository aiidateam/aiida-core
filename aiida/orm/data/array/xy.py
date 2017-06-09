# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
This module defines the classes related to Xy data. That is data that contains
collections of y-arrays bound to a single x-array, and the methods to operate
on them.
"""

from aiida.orm.data.array import ArrayData
import numpy as np
from aiida.common.exceptions import InputValidationError, NotExistent


def check_convert_single_to_tuple(item):
    """
    Checks if the item is a list or tuple, and converts it to a list if it is
    not already a list or tuple

    :param item: an object which may or may not be a list or tuple
    :return: item_list: the input item unchanged if list or tuple and [item]
                        otherwise
    """
    if isinstance(item, (list, tuple)):
        return item
    else:
        return [item]

class XyData(ArrayData):
    """
    A subclass designed to handle arrays that have an "XY" relationship to
    each other. That is there is one array, the X array, and there are several
    Y arrays, which can be considered functions of X.
    """
    def _arrayandname_validator(self, array, name, units):
        """
        Validates that the array is an numpy.ndarray and that the name is
        of type basestring. Raises InputValidationError if this not the case.
        """
        if not isinstance(name, basestring):
            raise InputValidationError("The name must always be an instance "
                                       "of basestring.")

        if not isinstance(array, np.ndarray):
            raise InputValidationError("The input array must always be a "
                                       "numpy array")
        try:
            array.astype(float)
        except ValueError:
            raise InputValidationError("The input array must only contain "
                                       "floats")
        if not isinstance(units, basestring):
            raise InputValidationError("The units must always be an instance"
                                           " of basestring.")

        
    def set_x(self, x_array, x_name, x_units):
        """
        Sets the array and the name for the x values.

        :param x_array: A numpy.ndarray, containing only floats
        :param x_name: a string for the x array name
        :param x_units: the units of x
        """
        self._arrayandname_validator(x_array, x_name, x_units)
        self._set_attr("x_name", x_name)
        self._set_attr("x_units", x_units)
        self.set_array("x_array", x_array)

        
    def set_y(self, y_arrays, y_names, y_units):
        """
        Set array(s) for the y part of the dataset. Also checks if the
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
            raise InputValidationError("Length of arrays and names do not "
                                       "match!")
        if len(y_units) != len(y_names):
            raise InputValidationError("Length of units does not match!")

        # Try to get the x_array
        try:
            x_array = self.get_x()[1]
        except NotExistent:
            raise InputValidationError("X array has not been set yet")
        # validate each of the y_arrays
        for num, (y_array, y_name, y_unit) in enumerate(
                                            zip(y_arrays, y_names, y_units)):
            self._arrayandname_validator(y_array,y_name,y_unit)
            if np.shape(y_array) != np.shape(x_array):
                raise InputValidationError("y_array {} did not have the "
                                           "same shape has the x_array!"
                                           "".format(y_name))
            self.set_array("y_array_{}".format(num), y_array)

        # if the y_arrays pass the initial validation, sets each
        self._set_attr("y_names", y_names)
        self._set_attr("y_units", y_units)

    def get_x(self):
        """
        Tries to retrieve the x array and x name raises a NotExistent
        exception if no x array has been set yet.
        :return x_name: the name set for the x_array
        :return x_array: the x array set earlier
        :return x_units: the x units set earlier
        """
        try:
            x_name = self.get_attr("x_name")
            x_array = self.get_array("x_array")
            x_units = self.get_attr("x_units")
        except (KeyError, AttributeError):
            raise NotExistent("No x array has been set yet!")
        return x_name, x_array, x_units
    
    def get_y(self):
        """
        Tries to retrieve the y arrays and the y names, raises a
        NotExistent exception if they have not been set yet, or cannot be
        retrieved
        :return y_names: list of strings naming the y_arrays
        :return y_arrays: list of y_arrays
        :return y_units: list of strings giving the units for the y_arrays
        """
        try:
            y_names = self.get_attr("y_names")
        except (KeyError, AttributeError):
            raise NotExistent("No y names has been set yet!")
        try:
            y_units = self.get_attr("y_units")
        except (KeyError, AttributeError):
            raise NotExistent("No y units has been set yet!")
        y_arrays = []
        try:
            for i in range(len(y_names)):
                y_arrays += [self.get_array("y_array_{}".format(i))]
        except (KeyError, AttributeError):
            raise NotExistent("Could not retrieve array associated with y array"
                              " {}".format(y_names[i]))
        return zip(y_names,y_arrays,y_units)

    # def plot_dosdata(self, dosdata_type, spin='',path='', fmt='pdf'):
    #     """
    #     Creates a plot of any of the dosdata_type that is dos of a given spin,
    #     or the integrated dos array.
    #
    #     :param dosdata_type: str, descriptor of dosdata array
    #     :param spin: optional parameter, to be passed to get_dos
    #     :param path: str, if specified will save figure to path
    #     :param fmt: str, specifies format to save figure, default pdf
    #     """
    #     plt.close()
    #     dosdata_array = getattr(self, 'get_'+dosdata_type)(spin)
    #     dosenergy_array = self.get_dos_energy()
    #     dosdata_units = getattr(self, dosdata_type+'_units')
    #     dosenergy_units = self.energy_units
    #     plt.plot(dosenergy_array, dosdata_array)
    #     plt.title(dosdata_type+' vs energy')
    #     plt.xlabel('Energy in ('+dosenergy_units+')')
    #     plt.ylabel(dosdata_type+' in ('+dosdata_units+')')
    #     if path != '':
    #         plt.savefig(path, format=fmt)
