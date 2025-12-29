"""Implementation of the ``AbstractRepositoryBackend`` using Git's object database.

This implementation uses pygit2 library for Git operations.
"""

import contextlib
import hashlib
import io
import json
import shutil
import subprocess
import uuid as uuid_module
from pathlib import Path
from typing import Any, BinaryIO, Iterable, Iterator, List, Optional, Tuple, Union

import pygit2

from aiida.common.hashing import chunked_file_hash

from .abstract import AbstractRepositoryBackend, InfoDictType

__all__ = ('GitRepositoryBackend',)


class GitRepositoryBackend(AbstractRepositoryBackend):
    """Implementation of the ``AbstractRepositoryBackend`` using Git's object database.

    This backend uses a bare Git repository to store file contents as Git blobs. Objects are content-addressable using
    Git's native SHA-1 hashing algorithm, with OIDs (Object IDs) serving as keys.

    Key features:
    - Uses pygit2 library for Git operations
    - Stores objects as Git blobs in a bare repository
    - Returns SHA-1 OIDs (40 hex characters) as keys
    - Leverages Git's built-in compression and deduplication
    - No soft-delete support (Git limitation)

    Note:
        This implementation requires pygit2 and libgit2 to be installed.
    """

    _CONFIG_FILE = 'aiida_config.json'

    def __init__(self, folder: Union[str, Path]):
        """Initialize the Git repository backend.

        :param folder: Path to the folder that will contain the bare Git repository
        """
        self._folder = Path(folder).resolve()
        self._repo: Optional[pygit2.Repository] = None
        self._config_cache: Optional[dict] = None

    def __str__(self) -> str:
        """Return the string representation of this repository."""
        if self.is_initialised:
            return f'GitRepository: {self.uuid} | {self._folder}'
        return 'GitRepository: <uninitialised>'

    def _get_repo(self) -> pygit2.Repository:
        """Get or create the pygit2 Repository object.

        :return: The pygit2 Repository instance
        :raises: RuntimeError if the repository is not initialised
        """
        if self._repo is None:
            if not self.is_initialised:
                raise RuntimeError('Repository is not initialised')
            self._repo = pygit2.Repository(str(self._folder))
        return self._repo

    def _get_config_path(self) -> Path:
        """Return path to the AiiDA configuration file."""
        return self._folder / self._CONFIG_FILE

    def _load_config(self) -> dict:
        """Load the configuration file."""
        if self._config_cache is None:
            config_path = self._get_config_path()
            if config_path.exists():
                with open(config_path, 'r') as f:
                    self._config_cache = json.load(f)
            else:
                self._config_cache = {}
        return self._config_cache

    def _save_config(self, config: dict) -> None:
        """Save the configuration file."""
        with open(self._get_config_path(), 'w') as f:
            json.dump(config, f, indent=2)
        self._config_cache = config

    @property
    def uuid(self) -> Optional[str]:
        """Return the unique identifier of the repository.

        The UUID is stored in a config file.

        :return: The repository UUID or None if not initialised
        """
        if not self.is_initialised:
            return None
        config = self._load_config()
        return config.get('uuid')

    @property
    def key_format(self) -> Optional[str]:
        """Return the format for the keys of the repository.

        :return: 'sha1' to indicate Git's native SHA-1 OID format, or None if not initialised
        """
        if not self.is_initialised:
            return None
        return 'sha1'

    def initialise(self, **kwargs: Any) -> None:
        """Initialise the repository if it hasn't already been initialised.

        Creates a bare Git repository and stores a UUID in a config file.

        :param kwargs: Additional keyword arguments (currently unused)
        """
        if self.is_initialised:
            return

        # Create the folder
        self._folder.mkdir(parents=True, exist_ok=True)

        # Initialize a bare Git repository using pygit2
        pygit2.init_repository(str(self._folder), bare=True)

        # Generate and save UUID
        config = {
            'uuid': str(uuid_module.uuid4()),
            'version': '1.0',
            'backend': 'git'
        }
        self._save_config(config)

        # Reset the cached repository object
        self._repo = None

    @property
    def is_initialised(self) -> bool:
        """Return whether the repository has been initialised.

        :return: True if the repository exists and is a valid Git repository
        """
        if not self._folder.exists():
            return False

        git_dir = self._folder / 'objects'
        config_file = self._get_config_path()

        return git_dir.exists() and config_file.exists()

    def erase(self) -> None:
        """Delete the repository itself and all its contents.

        This removes the entire repository folder from disk.
        """
        # Close the repository first
        if self._repo is not None:
            self._repo = None

        # Delete the entire folder
        if self._folder.exists():
            shutil.rmtree(self._folder)

        # Clear cache
        self._config_cache = None

    def _put_object_from_filelike(self, handle: BinaryIO) -> str:
        """Store the byte contents of a file in the repository.

        :param handle: Filelike object with the byte content to be stored
        :return: The Git OID (SHA-1 hash) as a string
        """
        # Read the data
        data = handle.read()

        # Get the repository
        repo = self._get_repo()

        # Use pygit2 to create a blob
        oid = repo.create_blob(data)

        # Return as hex string
        return str(oid)

    def has_objects(self, keys: List[str]) -> List[bool]:
        """Return whether the repository has objects with the given keys.

        :param keys: List of Git OIDs to check
        :return: List of booleans indicating existence for each key
        """
        repo = self._get_repo()
        result = []

        for key in keys:
            try:
                # Try to create an Oid and check if it exists in the ODB
                oid = pygit2.Oid(hex=key)
                result.append(oid in repo.odb)
            except (ValueError, KeyError):
                result.append(False)

        return result

    @contextlib.contextmanager
    def open(self, key: str) -> Iterator[BinaryIO]:
        """Open a file handle to an object stored under the given key.

        :param key: Git OID as string
        :return: Yield a byte stream object
        :raise FileNotFoundError: If the object does not exist
        :raise OSError: If the object could not be opened
        """
        # Call parent to check existence
        super().open(key)

        try:
            repo = self._get_repo()
            oid = pygit2.Oid(hex=key)

            # Read the blob
            # Note: This backend only creates blobs, so no need to check type
            blob = repo[oid]

            # Return the data as a BytesIO stream
            stream = io.BytesIO(blob.data)
            yield stream
        except (ValueError, KeyError) as exc:
            raise FileNotFoundError(f'object with key `{key}` does not exist.') from exc

    def iter_object_streams(self, keys: Iterable[str]) -> Iterator[Tuple[str, BinaryIO]]:
        """Return an iterator over the byte streams of objects identified by key.

        :param keys: Git OIDs of objects to iterate
        :return: Iterator of (oid, stream) tuples
        :raise FileNotFoundError: If any object does not exist
        :raise OSError: If any object could not be opened
        """
        for key in keys:
            with self.open(key) as stream:
                # Read the data and create a new stream since the context manager will close the original
                data = stream.read()
                yield key, io.BytesIO(data)

    def list_objects(self) -> Iterable[str]:
        """Return iterable that yields all available objects by key.

        :return: Iterator over all Git OIDs in the repository
        """
        repo = self._get_repo()

        # Iterate through all objects in the object database
        # Note: This backend only creates blobs, so all OIDs should be blobs
        # No need to check type, which would require loading each object
        for oid in repo.odb:
            yield str(oid)

    def get_object_hash(self, key: str) -> str:
        """Return the SHA-256 hash of an object stored under the given key.

        Note:
            This computes the SHA-256 hash on-the-fly from the blob data, as Git uses SHA-1
            for object IDs. This is required for AiiDA's consistency checks across different
            repository backends.

        :param key: Git OID
        :return: SHA-256 hash of the object content
        :raise FileNotFoundError: If the object does not exist
        """
        if not self.has_object(key):
            raise FileNotFoundError(key)

        # Compute SHA-256 hash from the blob data
        with self.open(key) as handle:
            return chunked_file_hash(handle, hashlib.sha256)

    def delete_objects(self, keys: List[str]) -> None:
        """Delete the objects from the repository.

        Note:
            Git does not support direct deletion of specific objects. This method validates
            that the objects exist, then runs garbage collection to remove all unreferenced
            objects from the repository.

        :param keys: List of Git OIDs to delete
        :raise FileNotFoundError: If any of the objects does not exist
        """
        # Call parent to validate existence
        super().delete_objects(keys)

        # Run git garbage collection to remove unreferenced objects
        # Note: This removes ALL unreferenced objects, not just the ones in `keys`
        subprocess.run(
            ['git', '--git-dir', str(self._folder), 'gc', '--prune=now', '--quiet'],
            check=True,
            capture_output=True
        )

    def get_info(self, detailed: bool = False) -> InfoDictType:
        """Return information on configuration and content of the repository.

        :param detailed: Flag to enable extra information (currently unused)
        :return: Dictionary with repository information
        """
        info: InfoDictType = {}

        if not self.is_initialised:
            return info

        try:
            repo = self._get_repo()

            # Count blobs in the repository
            blob_count = sum(1 for _ in self.list_objects())

            info['Objects'] = {'total': blob_count}
            info['Backend'] = 'git'
            info['Hash algorithm (keys)'] = 'sha1'
            info['Hash algorithm (content)'] = 'sha256'

        except Exception:
            # Fallback to minimal info
            info['Backend'] = 'git'
            info['Hash algorithm (keys)'] = 'sha1'
            info['Hash algorithm (content)'] = 'sha256'

        return info
