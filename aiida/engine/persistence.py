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

import plumpy

from aiida.orm.utils import serialize

__all__ = ('AiiDAPersister', 'ObjectLoader', 'get_object_loader')

LOGGER = logging.getLogger(__name__)
OBJECT_LOADER = None


class ObjectLoader(plumpy.DefaultObjectLoader):
    """Custom object loader for `aiida-core`."""

    def load_object(self, identifier):
        """Attempt to load the object identified by the given `identifier`.

        .. note:: We override the `plumpy.DefaultObjectLoader` to be able to throw an `ImportError` instead of a
            `ValueError` which in the context of `aiida-core` is not as apt, since we are loading classes.

        :param identifier: concatenation of module and resource name
        :return: loaded object
        :raises ImportError: if the object cannot be loaded
        """
        module, name = identifier.split(':')
        try:
            module = importlib.import_module(module)
        except ImportError:
            raise ImportError(f"module '{module}' from identifier '{identifier}' could not be loaded")

        try:
            return getattr(module, name)
        except AttributeError:
            raise ImportError(f"object '{name}' from identifier '{identifier}' could not be loaded")


def get_object_loader():
    """Return the global AiiDA object loader.

    :return: The global object loader
    :rtype: :class:`plumpy.ObjectLoader`
    """
    global OBJECT_LOADER
    if OBJECT_LOADER is None:
        OBJECT_LOADER = ObjectLoader()
    return OBJECT_LOADER


class AiiDAPersister(plumpy.Persister):
    """Persister to take saved process instance states and persisting them to the database."""

    def save_checkpoint(self, process, tag=None):
        """Persist a Process instance.

        :param process: :class:`aiida.engine.Process`
        :param tag: optional checkpoint identifier to allow distinguishing multiple checkpoints for the same process
        :raises: :class:`plumpy.PersistenceError` Raised if there was a problem saving the checkpoint
        """
        LOGGER.debug('Persisting process<%d>', process.pid)

        if tag is not None:
            raise NotImplementedError('Checkpoint tags not supported yet')

        try:
            bundle = plumpy.Bundle(process, plumpy.LoadSaveContext(loader=get_object_loader()))
        except ImportError:
            # Couldn't create the bundle
            raise plumpy.PersistenceError(f"Failed to create a bundle for '{process}': {traceback.format_exc()}")

        try:
            process.node.set_checkpoint(serialize.serialize(bundle))
        except Exception:
            raise plumpy.PersistenceError(f"Failed to store a checkpoint for '{process}': {traceback.format_exc()}")

        return bundle

    def load_checkpoint(self, pid, tag=None):
        """Load a process from a persisted checkpoint by its process id.

        :param pid: the process id of the :class:`plumpy.Process`
        :param tag: optional checkpoint identifier to allow retrieving a specific sub checkpoint
        :return: a bundle with the process state
        :rtype: :class:`plumpy.Bundle`
        :raises: :class:`plumpy.PersistenceError` Raised if there was a problem loading the checkpoint
        """
        from aiida.common.exceptions import MultipleObjectsError, NotExistent
        from aiida.orm import load_node

        if tag is not None:
            raise NotImplementedError('Checkpoint tags not supported yet')

        try:
            calculation = load_node(pid)
        except (MultipleObjectsError, NotExistent):
            raise plumpy.PersistenceError(f'Failed to load the node for process<{pid}>: {traceback.format_exc()}')

        checkpoint = calculation.checkpoint

        if checkpoint is None:
            raise plumpy.PersistenceError(f'Calculation<{calculation.pk}> does not have a saved checkpoint')

        try:
            bundle = serialize.deserialize(checkpoint)
        except Exception:
            raise plumpy.PersistenceError(f'Failed to load the checkpoint for process<{pid}>: {traceback.format_exc()}')

        return bundle

    def get_checkpoints(self):
        """Return a list of all the current persisted process checkpoints

        :return: list of PersistedCheckpoint tuples with element containing the process id and optional checkpoint tag.
        """

    def get_process_checkpoints(self, pid):
        """Return a list of all the current persisted process checkpoints for the specified process.

        :param pid: the process pid
        :return: list of PersistedCheckpoint tuples with element containing the process id and optional checkpoint tag.
        """

    def delete_checkpoint(self, pid, tag=None):
        """Delete a persisted process checkpoint, where no error will be raised if the checkpoint does not exist.

        :param pid: the process id of the :class:`plumpy.Process`
        :param tag: optional checkpoint identifier to allow retrieving a specific sub checkpoint
        """
        from aiida.orm import load_node

        calc = load_node(pid)
        calc.delete_checkpoint()

    def delete_process_checkpoints(self, pid):
        """Delete all persisted checkpoints related to the given process id.

        :param pid: the process id of the :class:`aiida.engine.processes.process.Process`
        """
