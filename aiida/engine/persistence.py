# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=global-statement
"""Definition of AiiDA's process persister and the necessary object loaders."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import logging
import traceback

import plumpy

from aiida.orm.utils import serialize

__all__ = ('AiiDAPersister', 'ObjectLoader', 'get_object_loader')

LOGGER = logging.getLogger(__name__)
OBJECT_LOADER = None

ObjectLoader = plumpy.DefaultObjectLoader


def get_object_loader():
    """
    Get the global AiiDA object loader

    :return: The global object loader
    :rtype: :class:`plumpy.ObjectLoader`
    """
    global OBJECT_LOADER
    if OBJECT_LOADER is None:
        OBJECT_LOADER = ObjectLoader()
    return OBJECT_LOADER


class AiiDAPersister(plumpy.Persister):
    """
    This node is responsible to taking saved process instance states and
    persisting them to the database.
    """

    def save_checkpoint(self, process, tag=None):
        """
        Persist a Process instance

        :param process: :class:`aiida.engine.Process`
        :param tag: optional checkpoint identifier to allow distinguishing multiple checkpoints for the same process
        :raises: :class:`plumpy.PersistenceError` Raised if there was a problem saving the checkpoint
        """
        LOGGER.debug('Persisting process<%d>', process.pid)

        if tag is not None:
            raise NotImplementedError('Checkpoint tags not supported yet')

        try:
            bundle = plumpy.Bundle(process, plumpy.LoadSaveContext(loader=get_object_loader()))
        except ValueError:
            # Couldn't create the bundle
            raise plumpy.PersistenceError("Failed to create a bundle for '{}': {}".format(
                process, traceback.format_exc()))

        try:
            process.node.set_checkpoint(serialize.serialize(bundle))
        except Exception:
            raise plumpy.PersistenceError("Failed to store a checkpoint for '{}': {}".format(
                process, traceback.format_exc()))

        return bundle

    def load_checkpoint(self, pid, tag=None):
        """
        Load a process from a persisted checkpoint by its process id

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
            raise plumpy.PersistenceError("Failed to load the node for process<{}>: {}".format(
                pid, traceback.format_exc()))

        checkpoint = calculation.checkpoint

        if checkpoint is None:
            raise plumpy.PersistenceError('Calculation<{}> does not have a saved checkpoint'.format(calculation.pk))

        try:
            bundle = serialize.deserialize(checkpoint)
        except Exception:
            raise plumpy.PersistenceError("Failed to load the checkpoint for process<{}>: {}".format(
                pid, traceback.format_exc()))

        return bundle

    def get_checkpoints(self):
        """
        Return a list of all the current persisted process checkpoints
        with each element containing the process id and optional checkpoint tag

        :return: list of PersistedCheckpoint tuples
        """

    def get_process_checkpoints(self, pid):
        """
        Return a list of all the current persisted process checkpoints for the
        specified process with each element containing the process id and
        optional checkpoint tag

        :param pid: the process pid
        :return: list of PersistedCheckpoint tuples
        """

    def delete_checkpoint(self, pid, tag=None):
        """
        Delete a persisted process checkpoint, where no error will be raised if the checkpoint does not exist

        :param pid: the process id of the :class:`plumpy.Process`
        :param tag: optional checkpoint identifier to allow retrieving a specific sub checkpoint
        """
        from aiida.orm import load_node

        calc = load_node(pid)
        calc.delete_checkpoint()

    def delete_process_checkpoints(self, pid):
        """
        Delete all persisted checkpoints related to the given process id

        :param pid: the process id of the :class:`aiida.engine.processes.process.Process`
        """
