###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Storage for immutable checkpoint files, with rollback- and backup-safe cleanup."""

import dataclasses
import functools
import hashlib
import os
import re
import typing as t
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

if t.TYPE_CHECKING:
    from aiida.orm.implementation.storage_backend import StorageBackend

_CHECKPOINT_FILE_OWNER: t.Final[re.Pattern[str]] = re.compile(
    r'(?P<staged>\.)?(?P<owner>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})-'
    r'(?(staged)[0-9a-f]{32}|[0-9a-f]{64}\.pkl)'
)


@dataclasses.dataclass(frozen=True)
class CheckpointBytes:
    """Serialized checkpoint data with its SHA-256 digest."""

    content: bytes

    @functools.cached_property
    def digest(self) -> str:
        return hashlib.sha256(self.content).hexdigest()


def _discard_file(*, path: Path) -> bool:
    """Delete `path`, returning whether it is gone, and warning instead of raising."""
    from aiida.storage.log import STORAGE_LOGGER

    try:
        path.unlink(missing_ok=True)
    except OSError as exception:
        STORAGE_LOGGER.warning('could not delete the orphaned checkpoint file `%s`: %s', path, exception)
        return False
    return True


def _fsync_dir(path: Path) -> None:
    """Synchronize `path` so a newly created entry survives a crash."""
    descriptor: int = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


@dataclasses.dataclass(frozen=True)
class CheckpointStore:
    """Checkpoint files belonging to one storage backend."""

    storage: 'StorageBackend'

    def _path_of(self, *, node_uuid: str, digest: str) -> Path:
        """Return the finished checkpoint-file path for `node_uuid` and `digest`."""
        return self.storage.get_checkpoint_classes_dirpath() / f'{node_uuid}-{digest}.pkl'

    def read(self, *, node_uuid: str, digest: str) -> bytes:
        """Return the bytes after validating the reference and content digest."""
        if re.fullmatch(r'[0-9a-f]{64}', digest) is None:
            msg: str = f'Invalid checkpoint digest {digest!r} for node {node_uuid}.'
            raise ValueError(msg)
        path: Path = self._path_of(node_uuid=node_uuid, digest=digest)
        content: bytes = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != digest:
            msg = f'Checkpoint digest mismatch for node {node_uuid} at {path.resolve()}.'
            raise ValueError(msg)
        return content

    def write(self, *, node_uuid: str, data: CheckpointBytes) -> None:
        """Durably publish the file before the database can reference it."""
        destination = self._path_of(node_uuid=node_uuid, digest=data.digest)
        destination.parent.mkdir(exist_ok=True)
        _fsync_dir(destination.parent.parent)
        staged: Path = destination.parent / f'.{node_uuid}-{uuid4().hex}'

        try:
            with open(staged, 'wb') as handle:
                handle.write(data.content)
                handle.flush()
                os.fsync(handle.fileno())

            # Module attribute, not `Path.replace`: tests intercept it, which a bound reference would bypass.
            os.replace(staged, destination)
        finally:
            staged.unlink(missing_ok=True)

        _fsync_dir(destination.parent)

    def discard_one(self, *, node_uuid: str, digest: str) -> None:
        """Delete an obsolete file after its checkpoint update has committed."""
        # Rollback can restore the old reference. Retained files are collected after the node seals.
        self.discard_files(paths=[self._path_of(node_uuid=node_uuid, digest=digest)])

    def discard_all(self, *, node_uuid: str) -> None:
        """Delete this node's finished and staged files after checkpoint deletion commits."""
        self.discard_files(paths=[path for path, _ in self.iter_files(node_uuid=node_uuid)])

    @contextmanager
    def retain_files(self) -> Iterator[None]:
        """Prevent deletion while reading a checkpoint or copying a storage snapshot."""
        import fcntl

        try:
            path = self._lock_path()
        except NotImplementedError:
            yield
            return

        with path.open('ab') as lock:
            fcntl.flock(lock, fcntl.LOCK_SH)
            yield

    def _lock_path(self) -> Path:
        return self.storage.get_checkpoint_classes_dirpath().with_name('.checkpoint-files.lock')

    def discard_files(self, *, paths: Iterable[Path]) -> list[Path]:
        """Delete obsolete files unless a transaction, reader or backup may need them."""
        import fcntl

        pending = list(paths)
        if not pending or self.storage.in_transaction:
            return []

        try:
            with self._lock_path().open('ab') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return [path for path in pending if _discard_file(path=path)]
        except BlockingIOError:
            # A reader or backup may need the previous file. Leave it for later cleanup.
            return []
        except OSError as exception:
            from aiida.storage.log import STORAGE_LOGGER

            STORAGE_LOGGER.warning('could not lock checkpoint files for cleanup: %s', exception)
            return []

    def iter_files(self, *, node_uuid: str | None = None) -> Iterator[tuple[Path, str]]:
        """Yield finished and staged checkpoint files with their owner UUIDs.

        Unsupported storage yields nothing; unrecognized names, symlinks and non-files are skipped.

        :param node_uuid: Restrict results to this owner.
        """
        try:
            dirpath: Path = self.storage.get_checkpoint_classes_dirpath()
        except NotImplementedError:
            return

        if not dirpath.exists():
            return

        paths = dirpath.iterdir() if node_uuid is None else dirpath.glob(f'*{node_uuid}-*')
        for path in sorted(paths):
            match = _CHECKPOINT_FILE_OWNER.fullmatch(path.name)

            if match is None or path.is_symlink() or not path.is_file():
                continue

            owner: str = match.group('owner')
            if node_uuid is None or owner == node_uuid:
                yield path, owner
