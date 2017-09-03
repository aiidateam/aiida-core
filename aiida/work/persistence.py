# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import traceback
import collections
import uritools
import os.path

import plum.persistence.pickle_persistence
from plum.process import Process
from aiida.common.lang import override
from aiida.work.defaults import class_loader

import glob
import os
import os.path as path
import portalocker
import portalocker.utils
from shutil import copyfile
import tempfile
import pickle
from plum.persistence.bundle import Bundle
from plum.process_listener import ProcessListener
from plum.process_monitor import MONITOR, ProcessMonitorListener
from plum.util import override, protected
from plum.persistence._base import LOGGER

_RUNNING_DIRECTORY = path.join(tempfile.gettempdir(), "running")
_FINISHED_DIRECTORY = path.join(_RUNNING_DIRECTORY, "finished")
_FAILED_DIRECTORY = path.join(_RUNNING_DIRECTORY, "failed")


# If portalocker accepts my pull request to have this incorporated into the
# library then this can be removed. https://github.com/WoLpH/portalocker/pull/34
class RLock(portalocker.Lock):
    """
    A reentrant lock, functions in a similar way to threading.RLock in that it
    can be acquired multiple times.  When the corresponding number of release()
    calls are made the lock will finally release the underlying file lock.
    """

    def __init__(
            self, filename, mode='a', timeout=portalocker.utils.DEFAULT_TIMEOUT,
            check_interval=portalocker.utils.DEFAULT_CHECK_INTERVAL, fail_when_locked=False,
            flags=portalocker.utils.LOCK_METHOD):
        super(RLock, self).__init__(filename, mode, timeout, check_interval,
                                    fail_when_locked, flags)
        self._acquire_count = 0

    def acquire(
            self, timeout=None, check_interval=None, fail_when_locked=None):
        if self._acquire_count >= 1:
            fh = self.fh
        else:
            fh = super(RLock, self).acquire(timeout, check_interval,
                                            fail_when_locked)
        self._acquire_count += 1
        return fh

    def release(self):
        if self._acquire_count == 0:
            raise portalocker.LockException(
                "Cannot release more times than acquired")

        if self._acquire_count == 1:
            super(RLock, self).release()
        self._acquire_count -= 1


class Persistence(plum.persistence.pickle_persistence.PicklePersistence):
    @override
    def load_checkpoint_from_file(self, filepath):
        cp = super(Persistence, self).load_checkpoint_from_file(filepath)

        inputs = cp.get(Process.BundleKeys.INPUTS.value, None)
        if inputs:
            cp[Process.BundleKeys.INPUTS.value] = self._load_nodes_from(inputs)
        outputs = cp.get(Process.BundleKeys.OUTPUTS.value, None)
        if outputs:
            cp[Process.BundleKeys.OUTPUTS.value] = self._load_nodes_from(outputs)

        cp.set_class_loader(class_loader)
        return cp

    @override
    def create_bundle(self, process):
        b = super(Persistence, self).create_bundle(process)

        inputs = b.get(Process.BundleKeys.INPUTS.value, None)
        if inputs:
            b[Process.BundleKeys.INPUTS.value] = self._convert_to_ids(inputs)
        outputs = b.get(Process.BundleKeys.OUTPUTS.value, None)
        if outputs:
            b[Process.BundleKeys.OUTPUTS.value] = self._convert_to_ids(outputs)

        return b

    def _convert_to_ids(self, nodes):
        from aiida.orm import Node

        input_ids = apricotpy.Bundle()
        for label, node in nodes.iteritems():
            if node is None:
                continue
            elif isinstance(node, Node):
                if node.is_stored:
                    input_ids[label] = node.pk
                else:
                    # Try using the UUID, but there's probably no chance of
                    # being abel to recover the node from this if not stored
                    # (for the time being)
                    input_ids[label] = node.uuid
            elif isinstance(node, collections.Mapping):
                input_ids[label] = self._convert_to_ids(node)

        return input_ids

    def _load_nodes_from(self, pks_mapping):
        """
        Take a dictionary of of {label: pk} or nested dictionary i.e.
        {label: {label: pk}} and convert to the equivalent Bundle but
        with nodes instead of the ids.

        :param pks_mapping: The dictionary of node pks.
        :return: A dictionary with the loaded nodes.
        :rtype: dict
        """
        from aiida.orm import load_node

        nodes = apricotpy.Bundle()
        for label, pk in pks_mapping.iteritems():
            if isinstance(pk, collections.Mapping):
                nodes[label] = self._load_nodes_from(pk)
            else:
                nodes[label] = load_node(pk=pk)
        return nodes


_GLOBAL_PERSISTENCE = None


def get_global_persistence():
    global _GLOBAL_PERSISTENCE

    if _GLOBAL_PERSISTENCE is None:
        _create_storage()

    return _GLOBAL_PERSISTENCE


def _create_storage():
    import aiida.common.setup as setup
    import aiida.settings as settings
    global _GLOBAL_PERSISTENCE

    parts = uritools.urisplit(settings.REPOSITORY_URI)
    if parts.scheme == u'file':
        WORKFLOWS_DIR = os.path.expanduser(
            os.path.join(parts.path, setup.WORKFLOWS_SUBDIR))

        _GLOBAL_PERSISTENCE = Persistence(
            running_directory=os.path.join(WORKFLOWS_DIR, 'running'),
            finished_directory=os.path.join(WORKFLOWS_DIR, 'finished'),
            failed_directory=os.path.join(WORKFLOWS_DIR, 'failed'))
