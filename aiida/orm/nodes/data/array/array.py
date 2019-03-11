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
AiiDA ORM data class storing (numpy) arrays
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from ..data import Data


class ArrayData(Data):
    """
    Store a set of arrays on disk (rather than on the database) in an efficient
    way using numpy.save() (therefore, this class requires numpy to be
    installed).

    Each array is stored within the Node folder as a different .npy file.

    :note: Before storing, no caching is done: if you perform a
      :py:meth:`.get_array` call, the array will be re-read from disk.
      If instead the ArrayData node has already been stored,
      the array is cached in memory after the first read, and the cached array
      is used thereafter.
      If too much RAM memory is used, you can clear the
      cache with the :py:meth:`.clear_internal_cache` method.
    """
    array_prefix = "array|"
    _cached_arrays = None

    def initialize(self):
        super(ArrayData, self).initialize()
        self._cached_arrays = {}

    def delete_array(self, name):
        """
        Delete an array from the node. Can only be called before storing.

        :param name: The name of the array to delete from the node.
        """
        fname = '{}.npy'.format(name)
        if fname not in self.list_object_names():
            raise KeyError("Array with name '{}' not found in node pk= {}".format(name, self.pk))

        # remove both file and attribute
        self.delete_object(fname)
        try:
            self.delete_attribute("{}{}".format(self.array_prefix, name))
        except (KeyError, AttributeError):
            # Should not happen, but do not crash if for some reason the property was not set.
            pass

    def get_arraynames(self):
        """
        Return a list of all arrays stored in the node, listing the files (and
        not relying on the properties).

        .. versionadded:: 0.7
           Renamed from arraynames
        """
        return self._arraynames_from_properties()

    def _arraynames_from_files(self):
        """
        Return a list of all arrays stored in the node, listing the files (and
        not relying on the properties).
        """
        return [i[:-4] for i in self.list_object_names() if i.endswith('.npy')]

    def _arraynames_from_properties(self):
        """
        Return a list of all arrays stored in the node, listing the attributes
        starting with the correct prefix.
        """
        return [i[len(self.array_prefix):] for i in self.attributes.keys() if i.startswith(self.array_prefix)]

    def get_shape(self, name):
        """
        Return the shape of an array (read from the value cached in the
        properties for efficiency reasons).

        :param name: The name of the array.
        """
        return tuple(self.get_attribute("{}{}".format(self.array_prefix, name)))

    def iterarrays(self):
        """
        Iterator that returns tuples (name, array) for each array stored in the
        node.
        """
        import warnings
        from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
        warnings.warn(  # pylint: disable=no-member
            'This method has been deprecated and will be renamed to get_iterarrays() in AiiDA v1.0', DeprecationWarning)
        return self.get_iterarrays()

    def get_iterarrays(self):
        """
        Iterator that returns tuples (name, array) for each array stored in the
        node.

        .. versionadded:: 1.0
           Renamed from iterarrays
        """
        for name in self.get_arraynames():
            yield (name, self.get_array(name))

    def get_array(self, name):
        """
        Return an array stored in the node

        :param name: The name of the array to return.
        """
        import numpy

        def get_array_from_file(self, name):
            """Return the array stored in a .npy file"""
            filename = '{}.npy'.format(name)

            if filename not in self.list_object_names():
                raise KeyError('Array with name `{}` not found in ArrayData<{}>'.format(name, self.pk))

            # Open a handle in binary read mode as the arrays are written as binary files as well
            with self.open(filename, mode='rb') as handle:
                return numpy.load(handle)

        # Return with proper caching if the node is stored, otherwise always re-read from disk
        if not self.is_stored:
            return get_array_from_file(self, name)

        if name not in self._cached_arrays:
            self._cached_arrays[name] = get_array_from_file(self, name)

        return self._cached_arrays[name]

    def clear_internal_cache(self):
        """
        Clear the internal memory cache where the arrays are stored after being
        read from disk (used in order to reduce at minimum the readings from
        disk).
        This function is useful if you want to keep the node in memory, but you
        do not want to waste memory to cache the arrays in RAM.
        """
        self._cached_arrays = {}

    def set_array(self, name, array):
        """
        Store a new numpy array inside the node. Possibly overwrite the array
        if it already existed.

        Internally, it stores a name.npy file in numpy format.

        :param name: The name of the array.
        :param array: The numpy array to store.
        """
        import re
        import tempfile
        import numpy

        if not isinstance(array, numpy.ndarray):
            raise TypeError('ArrayData can only store numpy arrays. Convert the object to an array first')

        # Check if the name is valid
        if not name or re.sub('[0-9a-zA-Z_]', '', name):
            raise ValueError("The name assigned to the array ({}) is not valid,"
                             "it can only contain digits, letters and underscores")

        # Write the array to a temporary file, and then add it to the repository of the node
        with tempfile.NamedTemporaryFile() as handle:
            numpy.save(handle, array)

            # Flush and rewind the handle, otherwise the command to store it in the repo will write an empty file
            handle.flush()
            handle.seek(0)

            # Write the numpy array to the repository, keeping the byte representation
            self.put_object_from_filelike(handle, '{}.npy'.format(name), mode='wb', encoding=None)

        # Store the array name and shape for querying purposes
        self.set_attribute('{}{}'.format(self.array_prefix, name), list(array.shape))

    def _validate(self):
        """
        Check if the list of .npy files stored inside the node and the
        list of properties match. Just a name check, no check on the size
        since this would require to reload all arrays and this may take time
        and memory.
        """
        from aiida.common.exceptions import ValidationError

        files = self._arraynames_from_files()
        properties = self._arraynames_from_properties()

        if set(files) != set(properties):
            raise ValidationError("Mismatch of files and properties for ArrayData"
                                  " node (pk= {}): {} vs. {}".format(self.pk, files, properties))
        super(ArrayData, self)._validate()
