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

from aiida.common.loaders import DefaultObjectLoader as ObjectLoader
from aiida.common.loaders import get_object_loader
from aiida.engine import _checkpoint_pickle
from aiida.engine.processes import persistence as process_persistence
from aiida.engine.processes.exceptions import PersistenceError
from aiida.orm.implementation.checkpoint_store import CheckpointBytes

if t.TYPE_CHECKING:
    from aiida.engine.processes.process import Process

__all__ = ('AiidaCheckpointPersister', 'ObjectLoader', 'get_object_loader')

LOGGER = logging.getLogger(__name__)


_PICKLE_PREFIX: t.Final[str] = 'checkpoint-pickle-v1:'


def _checkpoint_digest(*, checkpoint: str | None) -> str | None:
    """Return the digest of a supported checkpoint reference, or `None`."""
    if checkpoint is None or not checkpoint.startswith(_PICKLE_PREFIX):
        return None
    digest: str = checkpoint.removeprefix(_PICKLE_PREFIX)
    return digest if re.fullmatch(r'[0-9a-f]{64}', digest) else None


class AiidaCheckpointPersister(process_persistence.CheckpointPersister):
    """Store checkpoints in profile files with references on process nodes."""

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
            node = process.node
            store = node.backend.checkpoint_store
            previous = node.checkpoint
            data = CheckpointBytes(content=_checkpoint_pickle.dumps(payload))
            reference = f'{_PICKLE_PREFIX}{data.digest}'

            # A missing file (external deletion, partial restore) must be rewritten even when the
            # reference is unchanged, otherwise the node keeps a permanently dangling reference. A present
            # file is revalidated since mere existence cannot prove readability or digest integrity.
            needs_write = reference != previous
            if not needs_write:
                try:
                    store.read(node_uuid=node.uuid, digest=data.digest)
                except (ValueError, OSError):
                    needs_write = True
            if needs_write:
                store.write(node_uuid=node.uuid, data=data)
                node.set_checkpoint(checkpoint=reference)
                previous_digest = _checkpoint_digest(checkpoint=previous)
                if previous_digest is not None and previous_digest != data.digest:
                    store.discard_one(node_uuid=node.uuid, digest=previous_digest)
        except Exception as exception:
            msg = f"Failed to store a checkpoint for '{process}': {traceback.format_exc()}"
            raise PersistenceError(msg) from exception

        return payload

    def load_checkpoint(self, pid: Hashable, tag: str | None = None) -> process_persistence.CheckpointPayload:
        """Load a process from a persisted checkpoint by its process id.

        Checkpoints can execute Python code during deserialization. Only load from trusted profiles.

        :param pid: the process id of the :class:`aiida.engine.processes.generic.process.Process`
        :param tag: optional checkpoint identifier to allow retrieving a specific sub checkpoint
        :return: a checkpoint payload with the process state
        :rtype: :class:`aiida.engine.processes.persistence.CheckpointPayload`
        :raises: :class:`PersistenceError` Raised if there was a problem loading the checkpoint
        """
        from aiida.manage import get_manager
        from aiida.orm import load_node

        if tag is not None:
            raise NotImplementedError('Checkpoint tags not supported yet')

        try:
            store = get_manager().get_profile_storage().checkpoint_store
            if store.storage.in_transaction:
                msg = (
                    f'Process<{pid}> cannot be loaded inside an open storage transaction, such as a '
                    '`QueryBuilder.iterall()` or `iterdict()` loop. Collect the query results first, for '
                    'example with `QueryBuilder.all()`.'
                )
                raise PersistenceError(msg)
            node = load_node(pid)
            checkpoint = node.checkpoint
            if checkpoint is None:
                msg = f'Process<{pid}> does not have a saved checkpoint'
                raise PersistenceError(msg)
            if not checkpoint.startswith(_PICKLE_PREFIX):
                msg = f'Process<{pid}> has an unsupported checkpoint format.'
                raise PersistenceError(msg)
            data = store.read(node_uuid=node.uuid, digest=checkpoint.removeprefix(_PICKLE_PREFIX))

            return _checkpoint_pickle.loads_unsafe(data)
        except PersistenceError:
            raise
        except Exception as exception:
            msg = f'Failed to load the checkpoint for process<{pid}>: {exception}'
            raise PersistenceError(msg) from exception

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
        # Attribute first, matching the write: a kill leaves an unreferenced file, never a dangling reference.
        calc.delete_checkpoint()
        calc.backend.checkpoint_store.discard_all(node_uuid=calc.uuid)

    def delete_process_checkpoints(self, pid: Hashable):
        """Delete all persisted checkpoints related to the given process id.

        :param pid: the process id of the :class:`aiida.engine.processes.process.Process`
        """
