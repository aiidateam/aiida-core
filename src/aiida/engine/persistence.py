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
from uuid import uuid4

from aiida.common.loaders import DefaultObjectLoader as ObjectLoader
from aiida.common.loaders import get_object_loader
from aiida.engine.processes import persistence as process_persistence
from aiida.engine.processes.exceptions import PersistenceError
from aiida.orm.nodes.process.process import ProcessNode
from aiida.orm.utils import serialize

if t.TYPE_CHECKING:
    from aiida.engine.processes.process import Process

__all__ = ('AiidaCheckpointPersister', 'ObjectLoader', 'get_object_loader')

LOGGER = logging.getLogger(__name__)


def _checkpoint_classes_dirpath() -> Path:
    """Return the directory this profile keeps carried process class bytes in."""
    from aiida.manage import get_manager

    return get_manager().get_profile_storage().get_checkpoint_classes_dirpath()


@dataclasses.dataclass(frozen=True)
class _ProcessClassBytes:
    """The bytes of a process class together with the digest derived from them.

    The digest is derived here rather than passed alongside, so no caller can write a file whose name does not
    hold, and whoever computes it before the write and whoever needs it after get the same value.
    """

    content: bytes

    @functools.cached_property
    def digest(self) -> str:
        return hashlib.sha256(self.content).hexdigest()


@dataclasses.dataclass(frozen=True)
class _CheckpointClassFiles:
    """One node's files of carried process class bytes, holding what its checkpoint could not keep inline.

    Nothing here refers to a checkpoint. A caller hands over bytes and gets them back from any worker of the
    profile, because this lives in storage they all reach. The node's uuid keeps one process's files clear of
    another's, and the digest distinguishes each one, so a write never lands on the file a checkpoint refers to.
    """

    node_uuid: str

    def _path(self, digest: str) -> Path:
        return _checkpoint_classes_dirpath() / f'{self.node_uuid}-{digest}.pkl'

    def read(self, *, digest: str) -> bytes:
        """Return the bytes stored under ``digest``."""
        return self._path(digest).read_bytes()

    def write(self, class_bytes: _ProcessClassBytes) -> None:
        """Store ``class_bytes``, so that whatever opens them sees either all of them or no file at all.

        A rename is atomic within a filesystem, and the two ``fsync`` calls are what put the file and then the
        rename on disk, so a checkpoint that refers to the file finds it again after a crash.
        """
        destination: Path = self._path(class_bytes.digest)
        destination.parent.mkdir(parents=True, exist_ok=True)
        staged: Path = destination.parent / f'.{uuid4().hex}'

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
        """Delete the file for ``digest``, and only that one.

        A writer between its own file write and its attribute write would otherwise lose its file to another
        writer's cleanup, and be left referring to one that is gone.
        """
        self._path(digest).unlink(missing_ok=True)

    def discard_all(self) -> None:
        """Delete every file of this node, which is what a process leaves behind when it terminates."""
        try:
            dirpath: Path = _checkpoint_classes_dirpath()
        except NotImplementedError:
            # A storage that keeps no such files has none of this node's to delete, and the checkpoint itself
            # still has to go: this runs before the attribute is deleted.
            return

        if not dirpath.exists():
            return

        for path in dirpath.glob(f'{self.node_uuid}-*'):
            path.unlink(missing_ok=True)


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
        """Return the digest the bundle ``checkpoint`` refers to, or ``None`` where it refers to none."""
        if checkpoint is None:
            return None

        match: re.Match[str] | None = re.search(f'{ProcessNode.CLASS_BYTES_PREFIX}([0-9a-f]{{64}})', checkpoint)

        return match.group(1) if match else None


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
            # The class travels as bytes, which is the one thing the attribute should never hold, so it goes to a
            # file and the bundle keeps its digest. Everything else the bundle holds is text.
            carried: _ProcessClassBytes | None = _CarriedClass.detach(payload=payload)
            stored: str = serialize.serialize(data=payload)

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
        _CheckpointClassFiles(node_uuid=calc.uuid).discard_all()
        calc.delete_checkpoint()

    def delete_process_checkpoints(self, pid: Hashable):
        """Delete all persisted checkpoints related to the given process id.

        :param pid: the process id of the :class:`aiida.engine.processes.process.Process`
        """
