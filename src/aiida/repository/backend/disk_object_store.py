"""Implementation of the ``AbstractRepositoryBackend`` using the ``disk-objectstore`` as the backend."""

import contextlib
import dataclasses
import shutil
import typing as t

from aiida.common.lang import type_check
from aiida.storage.log import STORAGE_LOGGER

from .abstract import AbstractRepositoryBackend, InfoDictType

if t.TYPE_CHECKING:
    from disk_objectstore import Container

__all__ = ('DiskObjectStoreRepositoryBackend',)

BYTES_TO_MB = 1 / 1024**2

logger = STORAGE_LOGGER.getChild('disk_object_store')


class DiskObjectStoreRepositoryBackend(AbstractRepositoryBackend):
    """Implementation of the ``AbstractRepositoryBackend`` using the ``disk-object-store`` as the backend.

    .. note:: For certain methods, the container may create a sessions which should be closed after the operation is
        done to make sure the connection to the underlying sqlite database is closed. The best way is to accomplish this
        is by using the container as a context manager, which will automatically call the ``close`` method when it exits
        which ensures the session being closed. Note that not all methods may open the session and so need closing it,
        but to be on the safe side, we put every use of the container in a context manager. If no session is created,
        the ``close`` method is essentially a no-op.

    """

    def __init__(self, container: 'Container'):
        from disk_objectstore import Container

        type_check(container, Container)
        self._container = container

    def __str__(self) -> str:
        """Return the string representation of this repository."""
        if self.is_initialised:
            with self._container as container:
                return f'DiskObjectStoreRepository: {container.container_id} | {container.get_folder()}'
        return 'DiskObjectStoreRepository: <uninitialised>'

    @property
    def uuid(self) -> t.Optional[str]:
        """Return the unique identifier of the repository."""
        if not self.is_initialised:
            return None
        with self._container as container:
            return container.container_id

    @property
    def key_format(self) -> t.Optional[str]:
        with self._container as container:
            return container.hash_type

    def initialise(self, **kwargs: t.Any) -> None:
        """Initialise the repository if it hasn't already been initialised.

        :param kwargs: parameters for the initialisation.
        """
        with self._container as container:
            container.init_container(**kwargs)

    @property
    def is_initialised(self) -> bool:
        """Return whether the repository has been initialised."""
        with self._container as container:
            return container.is_initialised

    def erase(self) -> None:
        """Delete the repository itself and all its contents."""
        try:
            with self._container as container:
                shutil.rmtree(container.get_folder())
        except FileNotFoundError:
            pass

    def _put_object_from_filelike(self, handle: t.BinaryIO) -> str:
        """Store the byte contents of a file in the repository.

        :param handle: filelike object with the byte content to be stored.
        :return: the generated fully qualified identifier for the object within the repository.
        :raises TypeError: if the handle is not a byte stream.
        """
        with self._container as container:
            return container.add_streamed_object(handle)

    def has_objects(self, keys: t.List[str]) -> t.List[bool]:
        with self._container as container:
            return container.has_objects(keys)

    @contextlib.contextmanager
    def open(self, key: str) -> t.Iterator[t.BinaryIO]:
        """Open a file handle to an object stored under the given key.

        .. note:: this should only be used to open a handle to read an existing file. To write a new file use the method
            ``put_object_from_filelike`` instead.

        :param key: fully qualified identifier for the object within the repository.
        :return: yield a byte stream object.
        :raise FileNotFoundError: if the file does not exist.
        :raise OSError: if the file could not be opened.
        """
        from disk_objectstore.exceptions import NotExistent

        # enforce abstract contract
        if not isinstance(key, str):
            raise TypeError('key must be a string')

        with self._container as container:
            try:
                with container.get_object_stream(key) as handle:
                    yield t.cast(t.BinaryIO, handle)
            except NotExistent:
                raise FileNotFoundError(f'object with key `{key}` does not exist.')

    def iter_object_streams(self, keys: t.Iterable[str]) -> t.Iterator[t.Tuple[str, t.BinaryIO]]:
        with self._container.get_objects_stream_and_meta(keys) as triplets:  # type: ignore[arg-type]
            for key, stream, _ in triplets:
                assert stream is not None
                yield key, stream  # type: ignore[misc]

    def delete_objects(self, keys: t.List[str]) -> None:
        super().delete_objects(keys)
        with self._container as container:
            container.delete_objects(keys)

    def list_objects(self) -> t.Iterable[str]:
        with self._container as container:
            return container.list_all_objects()

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
        with self._container as container:
            if container.hash_type != 'sha256':
                return super().get_object_hash(key)
        return key

    def maintain(
        self,
        dry_run: bool = False,
        live: bool = True,
        pack_loose: t.Optional[bool] = None,
        do_repack: t.Optional[bool] = None,
        clean_storage: t.Optional[bool] = None,
        do_vacuum: t.Optional[bool] = None,
        compress: bool = False,
    ) -> None:
        """Performs maintenance operations.

        :param live: if True, will only perform operations that are safe to do while the repository is in use.
        :param pack_loose: flag for forcing the packing of loose files.
        :param do_repack: flag for forcing the re-packing of already packed files.
        :param clean_storage: flag for forcing the cleaning of soft-deleted files from the repository.
        :param do_vacuum: flag for forcing the vacuuming of the internal database when cleaning the repository.
        :param compress: flag for compressing the data when packing loose files.
                         Set to ``CompressMode.AUTO`` if ``True``.
        :return: a dictionary with information on the operations performed.
        """
        from disk_objectstore import CompressMode

        from aiida.common.progress_reporter import create_callback, get_progress_reporter

        if live and (do_repack or clean_storage or do_vacuum):
            overrides = {'do_repack': do_repack, 'clean_storage': clean_storage, 'do_vacuum': do_vacuum}
            keys = ', '.join([key for key, override in overrides.items() if override is True])
            raise ValueError(f'The following overrides were enabled but cannot be if `live=True`: {keys}')

        pack_loose = True if pack_loose is None else pack_loose

        compress_mode = CompressMode.NO
        if compress is True:
            compress_mode = CompressMode.AUTO

        if live:
            do_repack = False
            clean_storage = True if clean_storage is None else clean_storage
            do_vacuum = False
        else:
            do_repack = True if do_repack is None else do_repack
            clean_storage = True if clean_storage is None else clean_storage
            do_vacuum = True if do_vacuum is None else do_vacuum

        with self._container as container:
            if pack_loose:
                files_numb = container.count_objects().loose
                files_size = container.get_total_size().total_size_loose * BYTES_TO_MB
                logger.report(f'Packing all loose files ({files_numb} files occupying {files_size} MB) ...')
                if not dry_run:
                    with get_progress_reporter()(total=1) as progress:
                        callback = create_callback(progress)
                        container.pack_all_loose(compress=compress_mode, callback=callback)  # type: ignore[arg-type]

            if do_repack:
                files_numb = container.count_objects().packed
                files_size = container.get_total_size().total_size_packfiles_on_disk * BYTES_TO_MB
                logger.report(f'Re-packing all pack files ({files_numb} files in packs, occupying {files_size} MB) ...')
                if not dry_run:
                    with get_progress_reporter()(total=1) as progress:
                        callback = create_callback(progress)
                        container.repack(callback=callback)  # type: ignore[arg-type]

            if clean_storage:
                logger.report(f'Cleaning the repository database (with `vacuum={do_vacuum}`) ...')
                if not dry_run:
                    container.clean_storage(vacuum=do_vacuum)

    def get_info(
        self,
        detailed: bool = False,
    ) -> InfoDictType:
        """Return information on configuration and content of the repository."""
        output_info: InfoDictType = {}

        with self._container as container:
            output_info['SHA-hash algorithm'] = container.hash_type
            output_info['Compression algorithm'] = container.compression_algorithm
            output_info['Objects'] = dataclasses.asdict(container.count_objects())

            if not detailed:
                return output_info

            output_info['Size (MB)'] = {
                k: float(f'{v * BYTES_TO_MB:.2f}') for k, v in dataclasses.asdict(container.get_total_size()).items()
            }

        return output_info
