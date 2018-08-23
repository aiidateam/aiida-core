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
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Definition of AiiDA's process persister and the necessary object loaders."""
from __future__ import absolute_import
import logging
import traceback
import yaml

import plumpy

__all__ = ['ObjectLoader', 'get_object_loader']

LOGGER = logging.getLogger(__name__)
OBJECT_LOADER = None


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

        :param process: :class:`aiida.work.Process`
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
            raise plumpy.PersistenceError("Failed to create a bundle for '{}':{}".format(
                process, traceback.format_exc()))
        else:
            calc = process.calc
            calc.set_checkpoint(yaml.dump(bundle))

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
        from aiida.orm import load_node

        if tag is not None:
            raise NotImplementedError('Checkpoint tags not supported yet')

        calculation = load_node(pid)
        checkpoint = calculation.checkpoint

        if checkpoint is None:
            raise plumpy.PersistenceError('Calculation<{}> does not have a saved checkpoint'.format(calculation.pk))

        bundle = yaml.load(checkpoint)
        return bundle

    def get_checkpoints(self):
        """
        Return a list of all the current persisted process checkpoints
        with each element containing the process id and optional checkpoint tag

        :return: list of PersistedCheckpoint tuples
        """
        pass

    def get_process_checkpoints(self, pid):
        """
        Return a list of all the current persisted process checkpoints for the
        specified process with each element containing the process id and
        optional checkpoint tag

        :param pid: the process pid
        :return: list of PersistedCheckpoint tuples
        """
        pass

    def delete_checkpoint(self, pid, tag=None):
        """
        Delete a persisted process checkpoint, where no error will be raised if the checkpoint does not exist

        :param pid: the process id of the :class:`plumpy.Process`
        :param tag: optional checkpoint identifier to allow retrieving a specific sub checkpoint
        """
        from aiida.orm import load_node

        calc = load_node(pid)
        calc.del_checkpoint()

    def delete_process_checkpoints(self, pid):
        """
        Delete all persisted checkpoints related to the given process id

        :param pid: the process id of the :class:`aiida.work.processes.Process`
        """
        pass


class ObjectLoader(plumpy.DefaultObjectLoader):
    """
    The AiiDA specific object loader.
    """

    @staticmethod
    def is_wrapped_job_calculation(name):
        from aiida.work.job_processes import JobProcess
        return name.find(JobProcess.__name__) != -1

    def load_object(self, identifier):
        """
        Given an identifier load an object.

        :param identifier: The identifier
        :return: The loaded object
        :raises: ValueError if the object cannot be loaded
        """
        from aiida.work.job_processes import JobProcess

        if self.is_wrapped_job_calculation(identifier):
            idx = identifier.find(JobProcess.__name__)
            wrapped_class = identifier[idx + len(JobProcess.__name__) + 1:]
            # Recreate the class
            return JobProcess.build(super(ObjectLoader, self).load_object(wrapped_class))

        return super(ObjectLoader, self).load_object(identifier)
