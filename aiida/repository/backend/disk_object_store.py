# -*- coding: utf-8 -*-
"""Implementation of the ``AbstractRepositoryBackend`` using the ``disk-objectstore`` as the backend."""
import contextlib
import shutil
from typing import BinaryIO, Iterable, Iterator, List, Optional, Tuple

from disk_objectstore import Container

from aiida.common.lang import type_check

from .abstract import AbstractRepositoryBackend

__all__ = ('DiskObjectStoreRepositoryBackend',)


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
        self.container.init_container(**kwargs)

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
        return self.container.add_streamed_object(handle)

    def has_objects(self, keys: List[str]) -> List[bool]:
        return self.container.has_objects(keys)

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

        with self.container.get_object_stream(key) as handle:
            yield handle  # type: ignore[misc]

    def iter_object_streams(self, keys: List[str]) -> Iterator[Tuple[str, BinaryIO]]:
        with self.container.get_objects_stream_and_meta(keys) as triplets:
            for key, stream, _ in triplets:
                assert stream is not None
                yield key, stream  # type: ignore[misc]

    def delete_objects(self, keys: List[str]) -> None:
        super().delete_objects(keys)
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

    def maintain(  # pylint: disable=arguments-differ
        self,
        full: bool = False,
        override_pack_loose: bool = None,
        override_do_repack: bool = None,
        override_clean_storage: bool = None,
        override_do_vacuum: bool = None,
    ) -> dict:
        """Performs maintenance operations.

        :param full:
            a flag to perform operations that require to stop using the maintained profile.
        :param override_pack_loose:
            override flag for forcing the packing of loose files.
        :param override_do_repack:
            override flag for forcing the re-packing of already packed files.
        :param override_clean_storage:
            override flag for forcing the cleaning of soft-deleted files from the repository.
        :param override_do_vacuum:
            override flag for forcing the vacuuming of the internal database when cleaning the repository.
        :return:
            a dictionary with information on the operations performed.
        """
        from aiida.backends.control import MAINTAIN_LOGGER
        DOSTORE_LOGGER = MAINTAIN_LOGGER.getChild('disk_object_store')  # pylint: disable=invalid-name

        pack_loose = True
        do_repack = full
        clean_storage = full
        do_vacuum = full

        if override_pack_loose is not None:
            pack_loose = override_pack_loose

        if override_do_repack is not None:
            do_repack = override_do_repack

        if override_clean_storage is not None:
            clean_storage = override_clean_storage

        if override_do_vacuum is not None:
            do_vacuum = override_do_vacuum

        operation_results = {}

        if pack_loose:
            DOSTORE_LOGGER.info('Packing all loose files ...')
            self.container.pack_all_loose()
            operation_results['packing'] = 'All loose files have been packed.'

        if do_repack:
            DOSTORE_LOGGER.info('Re-packing all pack files ...')
            self.container.repack()
            operation_results['repacking'] = 'All pack files have been re-packed.'

        if clean_storage:
            DOSTORE_LOGGER.info(f'Cleaning the repository database (with `vacuum={do_vacuum}`) ...')
            self.container.clean_storage(vacuum=do_vacuum)
            operation_results['cleaning'] = f'The repository database has been cleaned (with `vacuum={do_vacuum}`).'

        return operation_results

    def get_info(  # pylint: disable=arguments-differ
        self,
        statistics=False,
        ) -> dict:
        bytes_to_mb = 9.53674316E-7

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
            'unpacked': size_data['total_size_loose'] * bytes_to_mb,
            'packed': size_data['total_size_packfiles_on_disk'] * bytes_to_mb,
            'other': size_data['total_size_packindexes_on_disk'] * bytes_to_mb,
        }
        return output_info
