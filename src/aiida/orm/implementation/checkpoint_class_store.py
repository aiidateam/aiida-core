###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Checkpoint class-file storage, cleanup and backup coordination."""

import dataclasses
import functools
import hashlib
import os
import re
import typing as t
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

if t.TYPE_CHECKING:
    from aiida.orm.implementation.storage_backend import StorageBackend

_CHECKPOINT_CLASS_FILE_OWNER: t.Final[re.Pattern[str]] = re.compile(
    r'(?P<staged>\.)?(?P<owner>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})-'
    r'(?(staged)[0-9a-f]{32}|[0-9a-f]{64}\.pkl)'
)


@dataclasses.dataclass(frozen=True)
class ProcessClassBytes:
    """Process class bytes with their SHA-256 digest."""

    content: bytes

    @functools.cached_property
    def digest(self) -> str:
        return hashlib.sha256(self.content).hexdigest()


@dataclasses.dataclass(frozen=True)
class CheckpointClassStore:
    """Class files belonging to one storage backend."""

    storage: 'StorageBackend'

    def _path(self, *, node_uuid: str, digest: str) -> Path:
        return self.storage.get_checkpoint_classes_dirpath() / f'{node_uuid}-{digest}.pkl'

    def read(self, *, node_uuid: str, digest: str) -> bytes:
        """Return class bytes after validating the reference and content digest."""
        if re.fullmatch(r'[0-9a-f]{64}', digest) is None:
            msg: str = f'Invalid checkpoint class digest {digest!r} for node {node_uuid}.'
            raise ValueError(msg)
        path: Path = self._path(node_uuid=node_uuid, digest=digest)
        content: bytes = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != digest:
            msg = f'Checkpoint class digest mismatch for node {node_uuid} at {path.resolve()}.'
            raise ValueError(msg)
        return content

    def write(self, *, node_uuid: str, class_bytes: ProcessClassBytes) -> None:
        """Atomically publish `class_bytes` and synchronize the file and both directory levels."""
        destination: Path = self._path(node_uuid=node_uuid, digest=class_bytes.digest)
        destination.parent.mkdir(parents=True, exist_ok=True)
        parent_descriptor: int = os.open(destination.parent.parent, os.O_RDONLY)
        try:
            os.fsync(parent_descriptor)
        finally:
            os.close(parent_descriptor)
        staged: Path = destination.parent / f'.{node_uuid}-{uuid4().hex}'

        try:
            with open(staged, 'wb') as handle:
                handle.write(class_bytes.content)
                handle.flush()
                os.fsync(handle.fileno())

            os.replace(staged, destination)
        finally:
            staged.unlink(missing_ok=True)

        descriptor: int = os.open(destination.parent, os.O_RDONLY)

        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    def discard_one(self, *, node_uuid: str, digest: str) -> None:
        """Delete an obsolete class file after its checkpoint update has committed."""
        storage: StorageBackend = self.storage
        # Rollback can restore the old reference. Retained files are collected after the node seals.
        if storage.in_transaction:
            return
        try:
            with self.lock():
                self._path(node_uuid=node_uuid, digest=digest).unlink(missing_ok=True)
        except BlockingIOError:
            return

    def discard_all(self, *, node_uuid: str) -> None:
        """Delete this node's finished and staged class files after checkpoint deletion commits."""
        storage: StorageBackend = self.storage
        if storage.in_transaction:
            return
        owned: list[tuple[Path, str]] = list(self.iter_files(node_uuid=node_uuid))
        if not owned:
            return
        try:
            with self.lock():
                for path, _ in owned:
                    path.unlink(missing_ok=True)
        except BlockingIOError:
            return

    @contextmanager
    def lock(self, *, exclusive: bool = False) -> Iterator[None]:
        """Protect database and class-file backup snapshots from concurrent deletion.

        :param exclusive: Wait for the backup lock; otherwise attempt a nonblocking shared deletion lock.
        :raises BlockingIOError: If a backup blocks the deletion lock.
        """
        import fcntl

        try:
            directory: Path = self.storage.get_checkpoint_classes_dirpath()
        except NotImplementedError:
            yield
            return

        directory.mkdir(parents=True, exist_ok=True)
        parent_descriptor: int = os.open(directory.parent, os.O_RDONLY)
        try:
            os.fsync(parent_descriptor)
        finally:
            os.close(parent_descriptor)

        # A writable regular file supports flock emulation on shared NFS filesystems.
        lock_path: Path = directory.with_name(f'.{directory.name}.lock')
        with lock_path.open('a+b') as handle:
            operation: int = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH | fcntl.LOCK_NB
            fcntl.flock(handle.fileno(), operation)
            yield

    def iter_files(self, *, node_uuid: str | None = None) -> Iterator[tuple[Path, str]]:
        """Yield finished and staged class-file paths with their owner UUIDs.

        Unsupported storage yields nothing; unrecognized names, symlinks and non-files are skipped.

        :param node_uuid: Restrict results to this owner.
        """
        try:
            dirpath: Path = self.storage.get_checkpoint_classes_dirpath()
        except NotImplementedError:
            return

        if not dirpath.exists():
            return

        for path in sorted(dirpath.iterdir()):
            match: re.Match[str] | None = _CHECKPOINT_CLASS_FILE_OWNER.fullmatch(path.name)

            if match is None or path.is_symlink() or not path.is_file():
                continue

            owner: str = match.group('owner')
            if node_uuid is None or owner == node_uuid:
                yield path, owner
