# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=global-statement
"""Definition of AiiDA's process persister and the necessary object loaders."""

import importlib
import logging
import traceback
from typing import TYPE_CHECKING, Any, Hashable, Optional

from plumpy.exceptions import PersistenceError
import plumpy.loaders
import plumpy.persistence

from aiida.orm.utils import serialize

if TYPE_CHECKING:
    from aiida.engine.processes.process import Process

__all__ = ('AiiDAPersister', 'ObjectLoader', 'get_object_loader')

LOGGER = logging.getLogger(__name__)
OBJECT_LOADER = None


class ObjectLoader(plumpy.loaders.DefaultObjectLoader):
    """Custom object loader for `aiida-core`."""

    def load_object(self, identifier: str) -> Any:  # pylint: disable=no-self-use
        """Attempt to load the object identified by the given `identifier`.

        .. note:: We override the `plumpy.DefaultObjectLoader` to be able to throw an `ImportError` instead of a
            `ValueError` which in the context of `aiida-core` is not as apt, since we are loading classes.

        :param identifier: concatenation of module and resource name
        :return: loaded object
        :raises ImportError: if the object cannot be loaded
        """
        module_name, name = identifier.split(':')
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            raise ImportError(f"module '{module_name}' from identifier '{identifier}' could not be loaded")

        try:
            return getattr(module, name)
        except AttributeError:
            raise ImportError(f"object '{name}' from identifier '{identifier}' could not be loaded")


def get_object_loader() -> ObjectLoader:
    """Return the global AiiDA object loader.

    :return: The global object loader

    """
    global OBJECT_LOADER
    if OBJECT_LOADER is None:
        OBJECT_LOADER = ObjectLoader()
    return OBJECT_LOADER


class AiiDAPersister(plumpy.persistence.Persister):
    """Persister to take saved process instance states and persisting them to the database."""

    def save_checkpoint(self, process: 'Process', tag: Optional[str] = None):  # type: ignore[override] # pylint: disable=no-self-use
        """Persist a Process instance.

        :param process: :class:`aiida.engine.Process`
        :param tag: optional checkpoint identifier to allow distinguishing multiple checkpoints for the same process
        :raises: :class:`PersistenceError` Raised if there was a problem saving the checkpoint
        """
        LOGGER.debug('Persisting process<%d>', process.pid)

        if tag is not None:
            raise NotImplementedError('Checkpoint tags not supported yet')

        try:
            bundle = plumpy.persistence.Bundle(process, plumpy.persistence.LoadSaveContext(loader=get_object_loader()))
        except ImportError:
            # Couldn't create the bundle
            raise PersistenceError(f"Failed to create a bundle for '{process}': {traceback.format_exc()}")

        try:
            process.node.set_checkpoint(serialize.serialize(bundle))
        except Exception:
            raise PersistenceError(f"Failed to store a checkpoint for '{process}': {traceback.format_exc()}")

        return bundle

    def load_checkpoint(self, pid: Hashable, tag: Optional[str] = None) -> plumpy.persistence.Bundle:  # pylint: disable=no-self-use
        """Load a process from a persisted checkpoint by its process id.

        :param pid: the process id of the :class:`plumpy.Process`
        :param tag: optional checkpoint identifier to allow retrieving a specific sub checkpoint
        :return: a bundle with the process state
        :rtype: :class:`plumpy.Bundle`
        :raises: :class:`PersistenceError` Raised if there was a problem loading the checkpoint
        """
        from aiida.common.exceptions import MultipleObjectsError, NotExistent
        from aiida.orm import load_node

        if tag is not None:
            raise NotImplementedError('Checkpoint tags not supported yet')

        try:
            calculation = load_node(pid)
        except (MultipleObjectsError, NotExistent):
            raise PersistenceError(f'Failed to load the node for process<{pid}>: {traceback.format_exc()}')

        checkpoint = calculation.checkpoint

        if checkpoint is None:
            raise PersistenceError(f'Calculation<{calculation.pk}> does not have a saved checkpoint')

        try:
            bundle = serialize.deserialize_unsafe(checkpoint)
        except Exception:
            raise PersistenceError(f'Failed to load the checkpoint for process<{pid}>: {traceback.format_exc()}')

        return bundle

    def get_checkpoints(self):
        """Return a list of all the current persisted process checkpoints

        :return: list of PersistedCheckpoint tuples with element containing the process id and optional checkpoint tag.
        """

    def get_process_checkpoints(self, pid: Hashable):
        """Return a list of all the current persisted process checkpoints for the specified process.

        :param pid: the process pid
        :return: list of PersistedCheckpoint tuples with element containing the process id and optional checkpoint tag.
        """

    def delete_checkpoint(self, pid: Hashable, tag: Optional[str] = None) -> None:  # pylint: disable=no-self-use,unused-argument
        """Delete a persisted process checkpoint, where no error will be raised if the checkpoint does not exist.

        :param pid: the process id of the :class:`plumpy.Process`
        :param tag: optional checkpoint identifier to allow retrieving a specific sub checkpoint
        """
        from aiida.orm import load_node

        calc = load_node(pid)
        calc.delete_checkpoint()

    def delete_process_checkpoints(self, pid: Hashable):
        """Delete all persisted checkpoints related to the given process id.

        :param pid: the process id of the :class:`aiida.engine.processes.process.Process`
        """
