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
        objects: typing.Optional[typing.Dict[str, 'File']] = None
    ) -> None:
        """Construct a new instance.

        :param name: The final element of the file path
        :param file_type: Identifies whether the File is a file or a directory
        :param key: A key to map the file to its contents in the backend repository (file only)
        :param objects: Mapping of child names to child Files (directory only)

        :raises ValueError: If a key is defined for a directory,
            or objects are defined for a file
        """
        if not isinstance(name, str):
            raise TypeError('name should be a string.')

        if not isinstance(file_type, FileType):
            raise TypeError('file_type should be an instance of `FileType`.')

        if key is not None and not isinstance(key, str):
            raise TypeError('key should be `None` or a string.')

        if objects is not None and any(not isinstance(obj, self.__class__) for obj in objects.values()):
            raise TypeError('objects should be `None` or a dictionary of `File` instances.')

        if file_type == FileType.DIRECTORY and key is not None:
            raise ValueError('an object of type `FileType.DIRECTORY` cannot define a key.')

        if file_type == FileType.FILE and objects is not None:
            raise ValueError('an object of type `FileType.FILE` cannot define any objects.')

        self._name = name
        self._file_type = file_type
        self._key = key
        self._objects = objects or {}

    @classmethod
    def from_serialized(cls, serialized: dict, name='') -> 'File':
        """Construct a new instance from a serialized instance.

        :param serialized: the serialized instance.
        :return: the reconstructed file object.
        """
        if 'k' in serialized:
            file_type = FileType.FILE
            key = serialized['k']
            objects = None
        else:
            file_type = FileType.DIRECTORY
            key = None
            objects = {name: File.from_serialized(obj, name) for name, obj in serialized.get('o', {}).items()}

        instance = cls.__new__(cls)
        instance.__init__(name, file_type, key, objects)  # type: ignore[misc]
        return instance

    def serialize(self) -> dict:
        """Serialize the metadata into a JSON-serializable format.

        .. note:: the serialization format is optimized to reduce the size in bytes.

        :return: dictionary with the content metadata.
        """
        if self.file_type == FileType.DIRECTORY:
            if self.objects:
                return {'o': {key: obj.serialize() for key, obj in self.objects.items()}}
            return {}
        return {'k': self.key}

    @property
    def name(self) -> str:
        """Return the name of the file object."""
        return self._name

    @property
    def file_type(self) -> FileType:
        """Return the file type of the file object."""
        return self._file_type

    def is_file(self) -> bool:
        """Return whether this instance is a file object."""
        return self.file_type == FileType.FILE

    def is_dir(self) -> bool:
        """Return whether this instance is a directory object."""
        return self.file_type == FileType.DIRECTORY

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

        equal_attributes = all(getattr(self, key) == getattr(other, key) for key in ['name', 'file_type', 'key'])
        equal_object_keys = sorted(self.objects) == sorted(other.objects)
        equal_objects = equal_object_keys and all(obj == other.objects[key] for key, obj in self.objects.items())

        return equal_attributes and equal_objects

    def __repr__(self):
        args = (self.name, self.file_type.value, self.key, self.objects.items())
        return 'File<name={}, file_type={}, key={}, objects={}>'.format(*args)
