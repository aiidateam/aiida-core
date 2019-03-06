# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Data class that can be used to store a single file in its repository."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os

from aiida.common import exceptions
from .data import Data

__all__ = ('SinglefileData',)


class SinglefileData(Data):
    """Data class that can be used to store a single file in its repository."""

    def __init__(self, filepath, **kwargs):
        super(SinglefileData, self).__init__(**kwargs)
        if filepath is not None:
            self.put_object_from_file(filepath)

    @property
    def filename(self):
        """Return the name of the file stored.

        :return: the filename under which the file is stored in the repository
        """
        return self.get_attribute('filename')

    def open(self, key=None, mode='r'):
        """Return an open file handle to the content of this data node.

        :param key: optional key within the repository, by default is the `filename` set in the attributes
        :param mode: the mode with which to open the file handle
        :return: a file handle in read mode
        """
        if key is None:
            key = self.filename

        return self._repository.open(key, mode=mode)

    def get_content(self):
        """Return the content of the single file stored for this data node.

        :return: the string content of the file
        """
        with self.open() as handle:
            return handle.read()

    def set_file(self, filepath):
        """Add the file located at `path` on file system to repository, deleting any other existing objects."""
        self.put_object_from_file(filepath)

    def put_object_from_file(self, path, key=None, mode='w', encoding='utf8', force=False):
        """Add the file located at `path` on file system to repository, deleting any other existing objects."""
        if not os.path.isabs(path):
            raise ValueError('path `{}` is not absolute'.format(path))

        if not os.path.isfile(path):
            raise ValueError('path `{}` does not correspond to an existing file'.format(path))

        if key is None:
            key = os.path.split(path)[1]

        existing_object_names = self.list_object_names()

        try:
            # Remove the 'key' from the list of currently existing objects such that it is not deleted after storing
            existing_object_names.remove(key)
        except ValueError:
            pass

        super(SinglefileData, self).put_object_from_file(path, key, mode, encoding, force)

        # Delete any other existing objects (minus the current `key` which was already removed from the list)
        for existing_key in existing_object_names:
            self.delete_object(existing_key)

        self.set_attribute('filename', key)

    def _validate(self):
        """Ensure that there is one object stored in the repository, whose key matches value set for `filename` attr."""
        super(SinglefileData, self)._validate()

        try:
            filename = self.filename
        except AttributeError:
            raise exceptions.ValidationError('the `filename` attribute is not set.')

        objects = self.list_object_names()

        if [filename] != objects:
            raise exceptions.ValidationError('respository files {} do not match the `filename` attribute {}.'.format(
                objects, filename))
