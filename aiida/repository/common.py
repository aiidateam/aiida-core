# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module with resources common to the repository."""
import enum
import typing

__all__ = ('FileType', 'File')


class FileType(enum.Enum):
    """Enumeration to represent the type of a file object."""

    DIRECTORY = 0
    FILE = 1


class File():
    """Data class representing a file object."""

    def __init__(
        self,
        name: str = '',
        file_type: FileType = FileType.DIRECTORY,
        key: typing.Union[str, None] = None,
        objects: typing.Dict[str, 'File'] = None
    ):
        if not isinstance(name, str):
            raise TypeError('name should be a string.')

        if not isinstance(file_type, FileType):
            raise TypeError('file_type should be an instance of `FileType`.')

        if key is not None and not isinstance(key, str):
            raise TypeError('key should be `None` or a string.')

        if objects is not None and any([not isinstance(obj, self.__class__) for obj in objects.values()]):
            raise TypeError('objects should be `None` or a dictionary of `File` instances.')

        self._name = name
        self._file_type = file_type
        self._key = key
        self._objects = objects or {}

    @classmethod
    def from_serialized(cls, serialized: dict) -> 'File':
        """Construct a new instance from a serialized instance.

        :param serialized: the serialized instance.
        :return: the reconstructed file object.
        """
        objects = {name: File.from_serialized(obj) for name, obj in serialized['objects'].items()}
        instance = cls.__new__(cls)
        instance.__init__(serialized['name'], FileType(serialized['file_type']), serialized['key'], objects)
        return instance

    def serialize(self) -> dict:
        """Serialize the metadata into a JSON-serializable format.

        :return: dictionary with the content metadata.
        """
        return {
            'name': self.name,
            'file_type': self.file_type.value,
            'key': self.key,
            'objects': {key: obj.serialize() for key, obj in self.objects.items()},
        }

    @property
    def name(self) -> str:
        """Return the name of the file object."""
        return self._name

    @property
    def file_type(self) -> FileType:
        """Return the file type of the file object."""
        return self._file_type

    @property
    def key(self) -> typing.Union[str, None]:
        """Return the key of the file object."""
        return self._key

    @property
    def objects(self) -> typing.Dict[str, 'File']:
        """Return the objects of the file object."""
        return self._objects

    def __eq__(self, other) -> bool:
        """Return whether this instance is equal to another file object instance."""
        if not isinstance(other, self.__class__):
            return False

        equal_attributes = all([getattr(self, key) == getattr(other, key) for key in ['name', 'file_type', 'key']])
        equal_object_keys = list(self.objects) == list(other.objects)
        equal_objects = equal_object_keys and all([obj == other.objects[key] for key, obj in self.objects.items()])

        return equal_attributes and equal_objects

    def __repr__(self):
        args = (self.name, self.file_type.value, self.key, list(self.objects.keys()))
        return 'File<name={}, file_type={}, key={}, objects={}>'.format(*args)
