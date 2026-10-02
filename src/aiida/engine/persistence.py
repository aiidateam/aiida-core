###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Definition of AiiDA's checkpoint repository and object loader helpers."""

import dataclasses
import functools
import hashlib
import logging
import os
import re
import traceback
import typing as t
from collections.abc import Hashable
from pathlib import Path

from aiida.common.loaders import DefaultObjectLoader as ObjectLoader
from aiida.common.loaders import get_object_loader
from aiida.engine.processes import persistence as process_persistence
from aiida.engine.processes.exceptions import PersistenceError
from aiida.orm.nodes.process.process import ProcessNode
from aiida.orm.utils import serialize

if t.TYPE_CHECKING:
    from aiida.engine.processes.process import Process
    from aiida.orm.implementation import StorageBackend

__all__ = ('AiidaCheckpointPersister', 'ObjectLoader', 'get_object_loader')

LOGGER = logging.getLogger(__name__)

CARRIED_CLASS_REFERENCE: t.Final[re.Pattern[str]] = re.compile(
    rf'^\s*{re.escape(process_persistence.META__CLASS_BYTES)}:\s*'
    rf'{re.escape(ProcessNode.CLASS_BYTES_PREFIX)}([0-9a-f]{{64}})\s*$',
    re.MULTILINE,
)
"""The class file a serialized bundle refers to, as its own line, so no other value of the same shape matches."""


@dataclasses.dataclass(frozen=True)
class _ProcessClassBytes:
    """Process class bytes with their SHA-256 digest."""

    content: bytes

    @functools.cached_property
    def digest(self) -> str:
        return hashlib.sha256(self.content).hexdigest()


@dataclasses.dataclass(frozen=True)
class _CheckpointClassFiles:
    """One node's class files, addressed by content digest in shared profile storage."""

    node_uuid: str

    @staticmethod
    def _storage() -> 'StorageBackend':
        from aiida.manage import get_manager

        return get_manager().get_profile_storage()

    def _path(self, digest: str) -> Path:
        return self._storage()._get_checkpoint_class_filepath(node_uuid=self.node_uuid, digest=digest)

    def read(self, *, digest: str) -> bytes:
        """Return class bytes after validating the reference and content digest."""
        if re.fullmatch(r'[0-9a-f]{64}', digest) is None:
            msg: str = f'Invalid checkpoint class digest {digest!r} for node {self.node_uuid}.'
            raise ValueError(msg)
        path: Path = self._path(digest)
        content: bytes = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != digest:
            msg = f'Checkpoint class digest mismatch for node {self.node_uuid} at {path.resolve()}.'
            raise ValueError(msg)
        return content

    def write(self, class_bytes: _ProcessClassBytes) -> None:
        """Store ``class_bytes``, so that whatever opens them reads either all of them or no file at all.

        Synchronizing the file and both directory levels preserves the reference across a filesystem crash.
        """
        destination: Path = self._path(class_bytes.digest)
        destination.parent.mkdir(parents=True, exist_ok=True)
        parent_descriptor: int = os.open(destination.parent.parent, os.O_RDONLY)
        try:
            os.fsync(parent_descriptor)
        finally:
            os.close(parent_descriptor)
        staged: Path = self._storage()._get_checkpoint_class_staging_filepath(node_uuid=self.node_uuid)

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

    def discard_one(self, *, digest: str) -> None:
        """Delete an obsolete class file after its checkpoint update has committed."""
        storage: StorageBackend = self._storage()
        # Rollback can restore the old reference. Retained files are collected after the node seals.
        if storage.in_transaction:
            return
        try:
            with storage.checkpoint_class_files_lock():
                self._path(digest).unlink(missing_ok=True)
        except BlockingIOError:
            return

    def discard_all(self) -> None:
        """Delete this node's finished and staged class files after checkpoint deletion commits."""
        storage: StorageBackend = self._storage()
        if storage.in_transaction:
            return
        owned: list[tuple[Path, str]] = list(storage._iter_checkpoint_class_files(node_uuid=self.node_uuid))
        if not owned:
            return
        try:
            with storage.checkpoint_class_files_lock():
                for path, _ in owned:
                    path.unlink(missing_ok=True)
        except BlockingIOError:
            return


class _CarriedClass:
    """The process class a checkpoint carries, in its two forms.

    In memory the bundle holds the class as bytes; stored, it holds the digest of the file those bytes went to.
    This is the only place that touches both the bundle's shape and that reference form, so neither the store
    nor the vendored checkpoint format has to.
    """

    @staticmethod
    def detach(*, payload: process_persistence.CheckpointPayload) -> _ProcessClassBytes | None:
        """Take the carried class out of ``payload``, leaving its digest behind, and return it.

        The bundle stays in the node attribute, where the database keeps it consistent with the rest of the row.
        Only the bytes leave, since raw bytes are what the ``attributes`` column should never hold. Nothing is
        written here, so an unchanged checkpoint costs no file write at all.

        :param payload: The checkpoint payload, modified in place.
        :returns: What was taken out, or ``None`` where the bundle carried none.
        """
        metadata: dict[str, t.Any] = payload.get(process_persistence.META, {})
        content: bytes | None = metadata.get(process_persistence.META__CLASS_BYTES)

        if content is None:
            return None

        carried: _ProcessClassBytes = _ProcessClassBytes(content=content)
        metadata[process_persistence.META__CLASS_BYTES] = f'{ProcessNode.CLASS_BYTES_PREFIX}{carried.digest}'

        return carried

    @staticmethod
    def attach(*, payload: process_persistence.CheckpointPayload, uuid: str) -> None:
        """Read the carried class back into ``payload`` from the file its digest refers to."""
        metadata: dict[str, t.Any] = payload.get(process_persistence.META, {})
        reference: t.Any = metadata.get(process_persistence.META__CLASS_BYTES)

        if not isinstance(reference, str) or not reference.startswith(ProcessNode.CLASS_BYTES_PREFIX):
            return

        digest: str = reference[len(ProcessNode.CLASS_BYTES_PREFIX) :]
        metadata[process_persistence.META__CLASS_BYTES] = _CheckpointClassFiles(node_uuid=uuid).read(digest=digest)

    @staticmethod
    def digest_in(*, checkpoint: str | None) -> str | None:
        """Return the digest the bundle ``checkpoint`` refers to, or ``None`` where it refers to none.

        A bundle holds whatever a process kept in its context, a file checksum among the ordinary things, so the
        digest is read from the line the metadata key owns. More than one such line leaves the file to
        :meth:`~aiida.orm.implementation.storage_backend.StorageBackend.delete_orphaned_checkpoint_class_files`,
        since dropping the wrong one would take the file a checkpoint still refers to.
        """
        if checkpoint is None:
            return None

        found: list[str] = CARRIED_CLASS_REFERENCE.findall(checkpoint)

        if len(found) == 1:
            return found[0]

        if found:
            LOGGER.warning('a checkpoint refers to %d carried classes, so none of their files is dropped', len(found))

        return None


class AiidaCheckpointPersister(process_persistence.CheckpointPersister):
    """Store process checkpoints on process nodes, with any carried process class bytes beside them."""

    def save_checkpoint(self, process: 'Process', tag: str | None = None):  # type: ignore[override]
        """Persist a Process instance.

        :param process: :class:`aiida.engine.Process`
        :param tag: optional checkpoint identifier to allow distinguishing multiple checkpoints for the same process
        :raises: :class:`PersistenceError` Raised if there was a problem saving the checkpoint
        """
        LOGGER.debug('Persisting process<%d>', process.pid)

        if tag is not None:
            raise NotImplementedError('Checkpoint tags not supported yet')

        try:
            payload = process_persistence.CheckpointPayload.from_object(
                process, process_persistence.CheckpointContext(loader=get_object_loader())
            )
        except ImportError:
            msg = f"Failed to create a checkpoint payload for '{process}': {traceback.format_exc()}"
            raise PersistenceError(msg)

        try:
            superseded: str | None = process.node.checkpoint
            stored_payload: process_persistence.CheckpointPayload = process_persistence.CheckpointPayload(payload)
            stored_payload[process_persistence.META] = dict(payload.get(process_persistence.META, {}))
            carried: _ProcessClassBytes | None = _CarriedClass.detach(payload=stored_payload)
            stored: str = serialize.serialize(data=stored_payload)

            if stored == superseded:
                LOGGER.debug('checkpoint of process<%d> is unchanged, so nothing is written', process.pid)
            else:
                byte_files: _CheckpointClassFiles = _CheckpointClassFiles(node_uuid=process.node.uuid)
                current: str | None = None

                if carried is not None:
                    current = carried.digest
                    # The bytes go in first, so the attribute never refers to a file that was not written.
                    byte_files.write(class_bytes=carried)

                process.node.set_checkpoint(checkpoint=stored)
                superseded_digest: str | None = _CarriedClass.digest_in(checkpoint=superseded)

                # A bundle changes far more often than the class it carries, and then both refer to one file.
                # The first checkpoint of a process supersedes nothing, and one carrying no class refers to none.
                if superseded_digest is not None and superseded_digest != current:
                    # Only now, since until the attribute refers to the new file the old one is what revives it.
                    byte_files.discard_one(digest=superseded_digest)
        except Exception:
            msg = f"Failed to store a checkpoint for '{process}': {traceback.format_exc()}"
            raise PersistenceError(msg)

        return payload

    def load_checkpoint(self, pid: Hashable, tag: str | None = None) -> process_persistence.CheckpointPayload:
        """Load a process from a persisted checkpoint by its process id.

        :param pid: the process id of the :class:`aiida.engine.processes.generic.process.Process`
        :param tag: optional checkpoint identifier to allow retrieving a specific sub checkpoint
        :return: a checkpoint payload with the process state
        :rtype: :class:`aiida.engine.processes.persistence.CheckpointPayload`
        :raises: :class:`PersistenceError` Raised if there was a problem loading the checkpoint
        """
        from aiida.common.exceptions import MultipleObjectsError, NotExistent
        from aiida.orm import load_node

        if tag is not None:
            raise NotImplementedError('Checkpoint tags not supported yet')

        try:
            calculation = load_node(pid)
        except (MultipleObjectsError, NotExistent):
            msg = f'Failed to load the node for process<{pid}>: {traceback.format_exc()}'
            raise PersistenceError(msg)

        checkpoint = calculation.checkpoint

        if checkpoint is None:
            msg = f'Calculation<{calculation.pk}> does not have a saved checkpoint'
            raise PersistenceError(msg)

        try:
            payload = serialize.deserialize_unsafe(checkpoint)
            _CarriedClass.attach(payload=payload, uuid=calculation.uuid)
        except Exception:
            msg = f'Failed to load the checkpoint for process<{pid}>: {traceback.format_exc()}'
            raise PersistenceError(msg)

        return payload

    def get_checkpoints(self):
        """Return a list of all the current persisted process checkpoints

        :return: list of PersistedCheckpoint tuples with element containing the process id and optional checkpoint tag.
        """

    def get_process_checkpoints(self, pid: Hashable):
        """Return a list of all the current persisted process checkpoints for the specified process.

        :param pid: the process pid
        :return: list of PersistedCheckpoint tuples with element containing the process id and optional checkpoint tag.
        """

    def delete_checkpoint(self, pid: Hashable, tag: str | None = None) -> None:
        """Delete a persisted process checkpoint, where no error will be raised if the checkpoint does not exist.

        :param pid: the process id of the :class:`aiida.engine.processes.generic.process.Process`
        :param tag: optional checkpoint identifier to allow retrieving a specific sub checkpoint
        """
        from aiida.orm import load_node

        calc = load_node(pid)
        # The attribute goes first, matching the write: a kill between the two then leaves a file nothing refers to,
        # which maintenance collects, where the other order leaves a checkpoint referring to bytes that are gone.
        calc.delete_checkpoint()
        _CheckpointClassFiles(node_uuid=calc.uuid).discard_all()

    def delete_process_checkpoints(self, pid: Hashable):
        """Delete all persisted checkpoints related to the given process id.

        :param pid: the process id of the :class:`aiida.engine.processes.process.Process`
        """
