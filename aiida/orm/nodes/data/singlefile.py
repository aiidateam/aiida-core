# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Data class that can be used to store a single file in its repository."""
import inspect
import os
import warnings

from aiida.common import exceptions
from aiida.common.warnings import AiidaDeprecationWarning
from .data import Data

__all__ = ('SinglefileData',)


class SinglefileData(Data):
    """Data class that can be used to store a single file in its repository."""

    DEFAULT_FILENAME = 'file.txt'

    def __init__(self, file, filename=None, **kwargs):
        """Construct a new instance and set the contents to that of the file.

        :param file: an absolute filepath or filelike object whose contents to copy.
            Hint: Pass io.BytesIO(b"my string") to construct the SinglefileData directly from a string.
        :param filename: specify filename to use (defaults to name of provided file).
        """
        # pylint: disable=redefined-builtin
        super().__init__(**kwargs)

        # 'filename' argument was added to 'set_file' after 1.0.0.
        if 'filename' not in inspect.getfullargspec(self.set_file)[0]:
            warnings.warn(  # pylint: disable=no-member
                "Method '{}.set_file' does not support the 'filename' argument. ".format(type(self).__name__) +
                'This will raise an exception in AiiDA 2.0.', AiidaDeprecationWarning
            )

        if file is not None:
            if filename is None:
                # don't assume that set_file has a 'filename' argument (remove guard in 2.0.0)
                self.set_file(file)
            else:
                self.set_file(file, filename=filename)

    @property
    def filename(self):
        """Return the name of the file stored.

        :return: the filename under which the file is stored in the repository
        """
        return self.get_attribute('filename')

    def open(self, key=None, mode='r'):
        """Return an open file handle to the content of this data node.

        :param key: optional key within the repository, by default is the `filename` set in the attributes
        :param mode: the mode with which to open the file handle (default: read mode)
        :return: a file handle
        """
        if key is None:
            key = self.filename

        return self._repository.open(key, mode=mode)

    def get_content(self):
        """Return the content of the single file stored for this data node.

        :return: the content of the file as a string
        """
        with self.open() as handle:
            return handle.read()

    def set_file(self, file, filename=None):
        """Store the content of the file in the node's repository, deleting any other existing objects.

        :param file: an absolute filepath or filelike object whose contents to copy
            Hint: Pass io.BytesIO(b"my string") to construct the file directly from a string.
        :param filename: specify filename to use (defaults to name of provided file).
        """
        # pylint: disable=redefined-builtin

        if isinstance(file, str):
            is_filelike = False

            key = os.path.basename(file)
            if not os.path.isabs(file):
                raise ValueError('path `{}` is not absolute'.format(file))

            if not os.path.isfile(file):
                raise ValueError('path `{}` does not correspond to an existing file'.format(file))
        else:
            is_filelike = True
            try:
                key = os.path.basename(file.name)
            except AttributeError:
                key = self.DEFAULT_FILENAME

        key = filename or key

        existing_object_names = self.list_object_names()

        try:
            # Remove the 'key' from the list of currently existing objects such that it is not deleted after storing
            existing_object_names.remove(key)
        except ValueError:
            pass

        if is_filelike:
            self.put_object_from_filelike(file, key, mode='wb')
        else:
            self.put_object_from_file(file, key)

        # Delete any other existing objects (minus the current `key` which was already removed from the list)
        for existing_key in existing_object_names:
            self.delete_object(existing_key)

        self.set_attribute('filename', key)

    def _validate(self):
        """Ensure that there is one object stored in the repository, whose key matches value set for `filename` attr."""
        super()._validate()

        try:
            filename = self.filename
        except AttributeError:
            raise exceptions.ValidationError('the `filename` attribute is not set.')

        objects = self.list_object_names()

        if [filename] != objects:
            raise exceptions.ValidationError(
                'respository files {} do not match the `filename` attribute {}.'.format(objects, filename)
            )
