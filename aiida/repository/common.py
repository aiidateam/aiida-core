# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=redefined-builtin
"""Module with resources common to the repository."""
import enum
import warnings

from aiida.common.warnings import AiidaDeprecationWarning

__all__ = ('File', 'FileType')


class FileType(enum.Enum):
    """Enumeration to represent the type of a file object."""

    DIRECTORY = 0
    FILE = 1


class File:
    """Data class representing a file object."""

    def __init__(self, name: str = '', file_type: FileType = FileType.DIRECTORY, type=None):
        """

            .. deprecated:: 1.4.0
                The argument `type` has been deprecated and will be removed in `v2.0.0`, use `file_type` instead.
        """
        if type is not None:
            warnings.warn(
                'argument `type` is deprecated and will be removed in `v2.0.0`. Use `file_type` instead.',
                AiidaDeprecationWarning
            )  # pylint: disable=no-member"""
            file_type = type

        if not isinstance(name, str):
            raise TypeError('name should be a string.')

        if not isinstance(file_type, FileType):
            raise TypeError('file_type should be an instance of `FileType`.')

        self._name = name
        self._file_type = file_type

    @property
    def name(self) -> str:
        """Return the name of the file object."""
        return self._name

    @property
    def type(self) -> FileType:
        """Return the file type of the file object.

        .. deprecated:: 1.4.0
            Will be removed in `v2.0.0`, use `file_type` instead.
        """
        warnings.warn('property is deprecated, use `file_type` instead', AiidaDeprecationWarning)  # pylint: disable=no-member"""
        return self.file_type

    @property
    def file_type(self) -> FileType:
        """Return the file type of the file object."""
        return self._file_type

    def __iter__(self):
        """Iterate over the properties."""
        warnings.warn(
            '`File` has changed from named tuple into class and from `v2.0.0` will no longer be iterable',
            AiidaDeprecationWarning
        )
        yield self.name
        yield self.file_type

    def __eq__(self, other):
        return self.file_type == other.file_type and self.name == other.name
