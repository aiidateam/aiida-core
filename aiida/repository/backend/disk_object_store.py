# -*- coding: utf-8 -*-
"""Implementation of the ``AbstractRepositoryBackend`` using the ``disk-objectstore`` as the backend."""
import contextlib
import shutil
from typing import BinaryIO, Iterable, Iterator, List, Optional, Tuple

from disk_objectstore import Container

from aiida.common.lang import type_check

from .abstract import AbstractRepositoryBackend

__all__ = ('DiskObjectStoreRepositoryBackend',)

BYTES_TO_MB = 1 / 1024**2


class DiskObjectStoreRepositoryBackend(AbstractRepositoryBackend):
    """Implementation of the ``AbstractRepositoryBackend`` using the ``disk-object-store`` as the backend."""

    def __init__(self, container):
        type_check(container, Container)
        self._container = container

    def __str__(self) -> str:
        """Return the string representation of this repository."""
        if self.is_initialised:
            return f'DiskObjectStoreRepository: {self.container.container_id} | {self.container.get_folder()}'
        return 'DiskObjectStoreRepository: <uninitialised>'

    @property
    def uuid(self) -> Optional[str]:
        """Return the unique identifier of the repository."""
        if not self.is_initialised:
            return None
        return self.container.container_id

    @property
    def key_format(self) -> Optional[str]:
        return self.container.hash_type

    def initialise(self, **kwargs) -> None:
        """Initialise the repository if it hasn't already been initialised.

        :param kwargs: parameters for the initialisation.
        """
        with self.container as container:
            container.init_container(**kwargs)

    @property
    def is_initialised(self) -> bool:
        """Return whether the repository has been initialised."""
        return self.container.is_initialised

    @property
    def container(self) -> Container:
        return self._container

    def erase(self):
        """Delete the repository itself and all its contents."""
        try:
            shutil.rmtree(self.container.get_folder())
        except FileNotFoundError:
            pass

    def _put_object_from_filelike(self, handle: BinaryIO) -> str:
        """Store the byte contents of a file in the repository.

        :param handle: filelike object with the byte content to be stored.
        :return: the generated fully qualified identifier for the object within the repository.
        :raises TypeError: if the handle is not a byte stream.
        """
        with self.container as container:
            return container.add_streamed_object(handle)

    def has_objects(self, keys: List[str]) -> List[bool]:
        return self.container.has_objects(keys)

    def has_object(self, key: str) -> bool:
        """Return whether the repository has an object with the given key.

        :param key: fully qualified identifier for the object within the repository.
        :return: True if the object exists, False otherwise.
        """
        with self.container as container:
            return container.has_object(key)

    @contextlib.contextmanager
    def open(self, key: str) -> Iterator[BinaryIO]:
        """Open a file handle to an object stored under the given key.

        .. note:: this should only be used to open a handle to read an existing file. To write a new file use the method
            ``put_object_from_filelike`` instead.

        :param key: fully qualified identifier for the object within the repository.
        :return: yield a byte stream object.
        :raise FileNotFoundError: if the file does not exist.
        :raise OSError: if the file could not be opened.
        """
        super().open(key)

        with self.container as container:
            with container.get_object_stream(key) as handle:
                yield handle  # type: ignore[misc]

    def iter_object_streams(self, keys: List[str]) -> Iterator[Tuple[str, BinaryIO]]:
        with self.container.get_objects_stream_and_meta(keys) as triplets:
            for key, stream, _ in triplets:
                assert stream is not None
                yield key, stream  # type: ignore[misc]

    def delete_objects(self, keys: List[str]) -> None:
        super().delete_objects(keys)
        with self.container as container:
            self.container.delete_objects(keys)

    def list_objects(self) -> Iterable[str]:
        return self.container.list_all_objects()

    def get_object_hash(self, key: str) -> str:
        """Return the SHA-256 hash of an object stored under the given key.

        .. important::
            A SHA-256 hash should always be returned,
            to ensure consistency across different repository implementations.

        :param key: fully qualified identifier for the object within the repository.
        :raise FileNotFoundError: if the file does not exist.

        """
        if not self.has_object(key):
            raise FileNotFoundError(key)
        if self.container.hash_type != 'sha256':
            return super().get_object_hash(key)
        return key

    def maintain(  # type: ignore # pylint: disable=arguments-differ,too-many-branches
        self,
        dry_run: bool = False,
        live: bool = True,
        pack_loose: bool = None,
        do_repack: bool = None,
        clean_storage: bool = None,
        do_vacuum: bool = None,
    ) -> dict:
        """Performs maintenance operations.

        :param live:
            if True, will only perform operations that are safe to do while the repository is in use.
        :param pack_loose:
            flag for forcing the packing of loose files.
        :param do_repack:
            flag for forcing the re-packing of already packed files.
        :param clean_storage:
            flag for forcing the cleaning of soft-deleted files from the repository.
        :param do_vacuum:
            flag for forcing the vacuuming of the internal database when cleaning the repository.
        :return:
            a dictionary with information on the operations performed.
        """
        from aiida.backends.control import MAINTAIN_LOGGER
        DOSTORE_LOGGER = MAINTAIN_LOGGER.getChild('disk_object_store')  # pylint: disable=invalid-name

        if live and (do_repack or clean_storage or do_vacuum):
            overrides = {'do_repack': do_repack, 'clean_storage': clean_storage, 'do_vacuum': do_vacuum}
            keys = ', '.join([key for key, override in overrides if override is True])  # type: ignore
            raise ValueError(f'The following overrides were enabled but cannot be if `live=True`: {keys}')

        pack_loose = True if pack_loose is None else pack_loose

        if live:
            do_repack = False
            clean_storage = False
            do_vacuum = False
        else:
            do_repack = True if do_repack is None else do_repack
            clean_storage = True if clean_storage is None else clean_storage
            do_vacuum = True if do_vacuum is None else do_vacuum

        if pack_loose:
            files_numb = self.container.count_objects()['loose']
            files_size = self.container.get_total_size()['total_size_loose'] * BYTES_TO_MB
            DOSTORE_LOGGER.report(f'Packing all loose files ({files_numb} files occupying {files_size} MB) ...')
            if not dry_run:
                self.container.pack_all_loose()

        if do_repack:
            files_numb = self.container.count_objects()['packed']
            files_size = self.container.get_total_size()['total_size_packfiles_on_disk'] * BYTES_TO_MB
            DOSTORE_LOGGER.report(
                f'Re-packing all pack files ({files_numb} files in packs, occupying {files_size} MB) ...'
            )
            if not dry_run:
                self.container.repack()

        if clean_storage:
            DOSTORE_LOGGER.report(f'Cleaning the repository database (with `vacuum={do_vacuum}`) ...')
            if not dry_run:
                self.container.clean_storage(vacuum=do_vacuum)


    def get_info(  # type: ignore # pylint: disable=arguments-differ
        self,
        statistics=False,
        ) -> dict:

        output_info = {}
        output_info['SHA-hash algorithm'] = self.container.hash_type
        output_info['Compression algorithm'] = self.container.compression_algorithm

        if not statistics:
            return output_info

        files_data = self.container.count_objects()
        size_data = self.container.get_total_size()

        output_info['Packs'] = files_data['pack_files']  # type: ignore

        output_info['Objects'] = {  # type: ignore
            'unpacked': files_data['loose'],
            'packed': files_data['packed'],
        }
        output_info['Size (MB)'] = {  # type: ignore
            'unpacked': size_data['total_size_loose'] * BYTES_TO_MB,
            'packed': size_data['total_size_packfiles_on_disk'] * BYTES_TO_MB,
            'other': size_data['total_size_packindexes_on_disk'] * BYTES_TO_MB,
        }
        return output_info
