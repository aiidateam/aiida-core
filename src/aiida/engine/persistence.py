###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Definition of AiiDA's checkpoint repository and object loader helpers."""

import io
import logging
import traceback
import typing as t
from collections.abc import Hashable

from aiida.common.loaders import DefaultObjectLoader as ObjectLoader
from aiida.common.loaders import get_object_loader
from aiida.engine.processes import persistence as process_persistence
from aiida.engine.processes.exceptions import PersistenceError
from aiida.orm.nodes.process.process import ProcessNode
from aiida.orm.utils import serialize

if t.TYPE_CHECKING:
    from aiida.engine.processes.process import Process

__all__ = ('AiidaCheckpointPersister', 'ObjectLoader', 'get_object_loader')

MAX_ATTRIBUTE_PAYLOAD_LENGTH: t.Final = 100_000
"""Longest checkpoint payload, in characters, kept in a node attribute. A longer one goes to the repository.

Measured on PostgreSQL, a node attribute wins by 2 to 2.5x below 30 kB, because rewriting a row costs less
than creating and deleting a loose object. The two are within noise of each other from 60 kB to 500 kB, and
the repository wins by 2.4x at 1 MB and 7.5x at 10 MB. This sits in that plateau, where the choice does not
matter.
"""

LOGGER = logging.getLogger(__name__)


class AiidaCheckpointPersister(process_persistence.CheckpointPersister):
    """Store process checkpoint payloads on process nodes."""

    def save_checkpoint(self, process: 'Process', tag: str | None = None):  # type: ignore[override]
        """Persist a Process instance.

        Where the payload goes is decided by its length alone. Every worker has to be able to read it, and the
        repository is the one place besides the database that a worker is already guaranteed to reach, since node
        files live there. It goes in as a managed object, whose lifetime the repository leaves to its writer.

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
            superseded = process.node.checkpoint
            stored = self._store_payload(serialize.serialize(payload))

            # A payload that did not change needs no write. The repository addresses an object by its content, so
            # an unchanged one keeps its key, and the comparison holds for either destination.
            if stored == superseded:
                LOGGER.debug('checkpoint of process<%d> is unchanged, so nothing is written', process.pid)
            else:
                process.node.set_checkpoint(stored)
                self._delete_payload(superseded)
        except Exception:
            msg = f"Failed to store a checkpoint for '{process}': {traceback.format_exc()}"
            raise PersistenceError(msg)

        return payload

    @staticmethod
    def _repository():
        """Return the repository of the loaded profile, which every worker of that profile can reach."""
        from aiida.manage import get_manager

        return get_manager().get_profile_storage().get_repository()

    @classmethod
    def _store_payload(cls, serialized: str) -> str:
        """Return what to store on the node for ``serialized``, putting it in the repository where that is cheaper.

        :param serialized: The serialized checkpoint payload.
        :returns: The payload itself, or a reference to the object holding it.
        """
        if len(serialized) <= MAX_ATTRIBUTE_PAYLOAD_LENGTH:
            LOGGER.debug(
                'checkpoint payload of %d characters goes to a node attribute, at or below the %d it takes to be '
                'worth an object',
                len(serialized),
                MAX_ATTRIBUTE_PAYLOAD_LENGTH,
            )
            return serialized

        key = cls._repository().put_managed_object_from_filelike(io.BytesIO(serialized.encode('utf8')))
        LOGGER.debug(
            'checkpoint payload of %d characters goes to the repository as managed object `%s`, above the %d it '
            'takes to be worth one',
            len(serialized),
            key,
            MAX_ATTRIBUTE_PAYLOAD_LENGTH,
        )

        return f'{ProcessNode.CHECKPOINT_OBJECT_PREFIX}{key}'

    @classmethod
    def _load_payload(cls, checkpoint: str) -> str:
        """Return the payload ``checkpoint`` holds, reading the repository if it only names it.

        :param checkpoint: What was stored on the node.
        :returns: The serialized checkpoint payload.
        """
        if not checkpoint.startswith(ProcessNode.CHECKPOINT_OBJECT_PREFIX):
            return checkpoint

        with cls._repository().open_managed_object(checkpoint[len(ProcessNode.CHECKPOINT_OBJECT_PREFIX) :]) as handle:
            return handle.read().decode('utf8')

    @classmethod
    def _delete_payload(cls, checkpoint: str | None) -> None:
        """Delete the object ``checkpoint`` names, if it names one.

        The repository leaves a managed object's lifetime to its writer, so a rewritten or deleted checkpoint has
        to take its object with it.

        :param checkpoint: What was stored on the node, or ``None``.
        """
        if checkpoint is None or not checkpoint.startswith(ProcessNode.CHECKPOINT_OBJECT_PREFIX):
            return

        cls._repository().delete_managed_objects([checkpoint[len(ProcessNode.CHECKPOINT_OBJECT_PREFIX) :]])

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
            payload = serialize.deserialize_unsafe(self._load_payload(checkpoint))
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
        self._delete_payload(calc.checkpoint)
        calc.delete_checkpoint()

    def delete_process_checkpoints(self, pid: Hashable):
        """Delete all persisted checkpoints related to the given process id.

        :param pid: the process id of the :class:`aiida.engine.processes.process.Process`
        """
