###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Abstraction for an archive file format."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO, Dict, List, Literal, Optional, Type, TypeVar, Union, overload

from typing_extensions import Self

if TYPE_CHECKING:
    from aiida.orm import QueryBuilder
    from aiida.orm.entities import Entity, EntityTypes
    from aiida.orm.implementation import StorageBackend
    from aiida.tools.visualization.graph import Graph

EntityType = TypeVar('EntityType', bound='Entity')

__all__ = ('ArchiveFormatAbstract', 'ArchiveReaderAbstract', 'ArchiveWriterAbstract', 'get_format')


class ArchiveWriterAbstract(ABC):
    """Writer of an archive, that will be used as a context manager."""

    def __init__(
        self,
        path: Union[str, Path],
        fmt: 'ArchiveFormatAbstract',
        *,
        mode: Literal['x', 'w', 'a'] = 'x',
        compression: int = 6,
        **kwargs: Any,
    ):
        """Initialise the writer.

        :param path: archive path
        :param mode: mode to open the archive in: 'x' (exclusive), 'w' (write) or 'a' (append)
        :param compression: default level of compression to use (integer from 0 to 9)
        """
        self._path = Path(path)
        if mode not in ('x', 'w', 'a'):
            raise ValueError(f'mode not in x, w, a: {mode}')
        self._mode = mode
        if compression not in range(10):
            raise ValueError(f'compression not in range 0-9: {compression}')
        self._compression = compression
        self._format = fmt
        self._kwargs = kwargs

    @property
    def path(self) -> Path:
        """Return the path to the archive."""
        return self._path

    @property
    def mode(self) -> Literal['x', 'w', 'a']:
        """Return the mode of the archive."""
        return self._mode

    @property
    def compression(self) -> int:
        """Return the compression level."""
        return self._compression

    def __enter__(self) -> Self:
        """Start writing to the archive."""
        return self

    def __exit__(self, *args, **kwargs) -> None:
        """Finalise the archive."""

    @abstractmethod
    def update_metadata(self, data: Dict[str, Any], overwrite: bool = False) -> None:
        """Add key, values to the top-level metadata."""

    @abstractmethod
    def bulk_insert(
        self,
        entity_type: 'EntityTypes',
        rows: List[Dict[str, Any]],
        allow_defaults: bool = False,
    ) -> None:
        """Add multiple rows of entity data to the archive.

        :param entity_type: The type of the entity
        :param data: A list of dictionaries, containing all fields of the backend model,
            except the `id` field (a.k.a primary key), which will be generated dynamically
        :param allow_defaults: If ``False``, assert that each row contains all fields,
            otherwise, allow default values for missing fields.

        :raises: ``IntegrityError`` if the keys in a row are not a subset of the columns in the table
        """

    @abstractmethod
    def put_object(self, stream: BinaryIO, *, buffer_size: Optional[int] = None, key: Optional[str] = None) -> str:
        """Add an object to the archive.

        :param stream: byte stream to read the object from
        :param buffer_size: Number of bytes to buffer when read/writing
        :param key: key to use for the object (if None will be auto-generated)
        :return: the key of the object
        """

    @abstractmethod
    def delete_object(self, key: str) -> None:
        """Delete the object from the archive.

        :param key: fully qualified identifier for the object within the repository.
        :raise OSError: if the file could not be deleted.
        """


class ArchiveReaderAbstract(ABC):
    """Reader of an archive, that will be used as a context manager."""

    def __init__(self, path: Union[str, Path], **kwargs: Any):
        """Initialise the reader.

        :param path: archive path
        """
        self._path = Path(path)

    @property
    def path(self):
        """Return the path to the archive."""
        return self._path

    def __enter__(self) -> Self:
        """Start reading from the archive."""
        return self

    def __exit__(self, *args, **kwargs) -> None:
        """Finalise the archive."""

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Return the top-level metadata.

        :raises: ``CorruptStorage`` if the top-level metadata cannot be read from the archive
        """

    @abstractmethod
    def get_backend(self) -> 'StorageBackend':
        """Return a 'read-only' backend for the archive."""

    # below are convenience methods for some common use cases

    def querybuilder(self, **kwargs: Any) -> 'QueryBuilder':
        """Return a ``QueryBuilder`` instance, initialised with the archive backend."""
        from aiida.orm import QueryBuilder

        return QueryBuilder(backend=self.get_backend(), **kwargs)

    def get(self, entity_cls: Type[EntityType], **filters: Any) -> EntityType:
        """Return the entity for the given filters.

        Example::

            reader.get(orm.Node, pk=1)

        :param entity_cls: The type of the front-end entity
        :param filters: the filters identifying the object to get
        """
        if 'pk' in filters:
            filters['id'] = filters.pop('pk')
        return self.querybuilder().append(entity_cls, filters=filters).one()[0]

    def graph(self, **kwargs: Any) -> 'Graph':
        """Return a provenance graph generator for the archive."""
        from aiida.tools.visualization.graph import Graph

        return Graph(backend=self.get_backend(), **kwargs)


class ArchiveFormatAbstract(ABC):
    """Abstract class for an archive format."""

    @property
    @abstractmethod
    def latest_version(self) -> str:
        """Return the latest schema version of the archive format."""

    @property
    @abstractmethod
    def key_format(self) -> str:
        """Return the format of repository keys."""

    @abstractmethod
    def read_version(self, path: Union[str, Path]) -> str:
        """Read the version of the archive from a file.

        This method should account for reading all versions of the archive format.

        :param path: archive path

        :raises: ``UnreachableStorage`` if the file does not exist
        :raises: ``CorruptStorage`` if a version cannot be read from the archive
        """

    @overload
    @abstractmethod
    def open(
        self, path: Union[str, Path], mode: Literal['r'], *, compression: int = 6, **kwargs: Any
    ) -> ArchiveReaderAbstract: ...

    @overload
    @abstractmethod
    def open(
        self, path: Union[str, Path], mode: Literal['x', 'w'], *, compression: int = 6, **kwargs: Any
    ) -> ArchiveWriterAbstract: ...

    @overload
    @abstractmethod
    def open(
        self, path: Union[str, Path], mode: Literal['a'], *, compression: int = 6, **kwargs: Any
    ) -> ArchiveWriterAbstract: ...

    @abstractmethod
    def open(
        self, path: Union[str, Path], mode: Literal['r', 'x', 'w', 'a'] = 'r', *, compression: int = 6, **kwargs: Any
    ) -> Union[ArchiveReaderAbstract, ArchiveWriterAbstract]:
        """Open an archive (latest version only).

        :param path: archive path
        :param mode: open mode: 'r' (read), 'x' (exclusive write), 'w' (write) or 'a' (append)
        :param compression: default level of compression to use for writing (integer from 0 to 9)

        Note, in write mode, the writer is responsible for writing the format version.
        """

    @abstractmethod
    def migrate(
        self,
        inpath: Union[str, Path],
        outpath: Union[str, Path],
        version: str,
        *,
        force: bool = False,
        compression: int = 6,
    ) -> None:
        """Migrate an archive to a specific version.

        :param inpath: input archive path
        :param outpath: output archive path
        :param version: version to migrate to
        :param force: allow overwrite of existing output archive path
        :param compression: default level of compression to use for writing (integer from 0 to 9)
        """


def get_format(name: str = 'sqlite_zip') -> ArchiveFormatAbstract:
    """Get the archive format instance.

    :param name: name of the archive format
    :return: archive format instance
    """
    # to-do entry point for archive formats?
    assert name == 'sqlite_zip'
    from aiida.tools.archive.implementations.sqlite_zip.main import ArchiveFormatSqlZip

    return ArchiveFormatSqlZip()
