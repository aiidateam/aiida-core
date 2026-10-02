###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Definition of AiiDA's checkpoint repository and object loader helpers."""

import logging
import re
import traceback
import typing as t
from collections.abc import Hashable

import yaml

from aiida.common.loaders import DefaultObjectLoader as ObjectLoader
from aiida.common.loaders import get_object_loader
from aiida.engine.processes import persistence as process_persistence
from aiida.engine.processes.exceptions import PersistenceError
from aiida.orm.implementation.checkpoint_class_store import CheckpointClassStore, ProcessClassBytes
from aiida.orm.utils import serialize

if t.TYPE_CHECKING:
    from aiida.engine.processes.process import Process

__all__ = ('AiidaCheckpointPersister', 'ObjectLoader', 'get_object_loader')

LOGGER = logging.getLogger(__name__)


_CLASS_BYTES_PREFIX: t.Final[str] = 'sha256:'


def _class_store() -> CheckpointClassStore:
    from aiida.manage import get_manager

    return get_manager().get_profile_storage().checkpoint_class_store


def _detach_carried_class(*, payload: process_persistence.CheckpointPayload) -> ProcessClassBytes | None:
    """Replace carried bytes in `payload` with a digest reference and return `ProcessClassBytes`, or `None`."""
    metadata: dict[str, t.Any] = payload.get(process_persistence.META, {})
    content: bytes | None = metadata.get(process_persistence.META__CLASS_BYTES)

    if content is None:
        return None

    carried: ProcessClassBytes = ProcessClassBytes(content=content)
    metadata[process_persistence.META__CLASS_BYTES] = f'{_CLASS_BYTES_PREFIX}{carried.digest}'

    return carried


def _attach_carried_class(*, payload: process_persistence.CheckpointPayload, uuid: str) -> None:
    """Restore carried class bytes in `payload` from their digest reference."""
    metadata: dict[str, t.Any] = payload.get(process_persistence.META, {})
    reference: t.Any = metadata.get(process_persistence.META__CLASS_BYTES)

    if not isinstance(reference, str) or not reference.startswith(_CLASS_BYTES_PREFIX):
        return

    digest: str = reference[len(_CLASS_BYTES_PREFIX) :]
    metadata[process_persistence.META__CLASS_BYTES] = _class_store().read(node_uuid=uuid, digest=digest)


def _carried_digest_in(*, checkpoint: str | None) -> str | None:
    """Return the unique metadata class digest, or `None`, without constructing YAML objects.

    Malformed or ambiguous metadata defers cleanup.
    """
    if checkpoint is None:
        return None
    try:
        root: yaml.Node | None = yaml.compose(checkpoint, Loader=yaml.SafeLoader)
    except yaml.YAMLError:
        LOGGER.warning('Cannot parse checkpoint metadata; class-file cleanup is deferred.')
        return None
    if not isinstance(root, yaml.MappingNode):
        return None
    metadata: list[yaml.Node] = [
        value for key, value in root.value if isinstance(key, yaml.ScalarNode) and key.value == process_persistence.META
    ]
    if len(metadata) != 1 or not isinstance(metadata[0], yaml.MappingNode):
        return None
    references: list[yaml.Node] = [
        value
        for key, value in metadata[0].value
        if isinstance(key, yaml.ScalarNode) and key.value == process_persistence.META__CLASS_BYTES
    ]
    if len(references) != 1:
        if references:
            LOGGER.warning('Ambiguous checkpoint class references; class-file cleanup is deferred.')
        return None
    reference: yaml.Node = references[0]
    if not isinstance(reference, yaml.ScalarNode):
        return None
    match: re.Match[str] | None = re.fullmatch(rf'{re.escape(_CLASS_BYTES_PREFIX)}([0-9a-f]{{64}})', reference.value)
    return None if match is None else match.group(1)


class AiidaCheckpointPersister(process_persistence.CheckpointPersister):
    """Store checkpoints on process nodes and carried class bytes in profile files."""

    def save_checkpoint(self, process: 'Process', tag: str | None = None):  # type: ignore[override]
        """Persist the process checkpoint and return its payload with carried bytes intact.

        :raises NotImplementedError: If `tag` is supplied.
        :raises PersistenceError: If checkpoint creation or storage fails.
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
            carried: ProcessClassBytes | None = _detach_carried_class(payload=stored_payload)
            stored: str = serialize.serialize(data=stored_payload)

            if stored == superseded:
                LOGGER.debug('checkpoint of process<%d> is unchanged, so nothing is written', process.pid)
            else:
                byte_files: CheckpointClassStore = _class_store()
                current: str | None = None

                if carried is not None:
                    current = carried.digest
                    # The bytes go in first, so the attribute never refers to a file that was not written.
                    byte_files.write(node_uuid=process.node.uuid, class_bytes=carried)

                process.node.set_checkpoint(checkpoint=stored)
                superseded_digest: str | None = _carried_digest_in(checkpoint=superseded)

                # A bundle changes far more often than the class it carries, and then both refer to one file.
                # The first checkpoint of a process supersedes nothing, and one carrying no class refers to none.
                if superseded_digest is not None and superseded_digest != current:
                    # Only now, since until the attribute refers to the new file the old one is what revives it.
                    byte_files.discard_one(node_uuid=process.node.uuid, digest=superseded_digest)
        except Exception:
            msg = f"Failed to store a checkpoint for '{process}': {traceback.format_exc()}"
            raise PersistenceError(msg)

        return payload

    def load_checkpoint(self, pid: Hashable, tag: str | None = None) -> process_persistence.CheckpointPayload:
        """Load the checkpoint payload, restoring carried bytes after digest validation.

        :raises NotImplementedError: If `tag` is supplied.
        :raises PersistenceError: If the node, checkpoint or carried bytes cannot be loaded.
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
            _attach_carried_class(payload=payload, uuid=calculation.uuid)
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
        """Remove the checkpoint if present, then attempt class-file cleanup.

        Transactions and active backups defer file deletion; `tag` is ignored.
        """
        from aiida.orm import load_node

        calc = load_node(pid)
        # The attribute goes first, matching the write: a kill between the two then leaves a file nothing refers to,
        # which maintenance collects, where the other order leaves a checkpoint referring to bytes that are gone.
        calc.delete_checkpoint()
        _class_store().discard_all(node_uuid=calc.uuid)

    def delete_process_checkpoints(self, pid: Hashable):
        """Delete all persisted checkpoints related to the given process id.

        :param pid: the process id of the :class:`aiida.engine.processes.process.Process`
        """
