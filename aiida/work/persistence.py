# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import collections
import uritools
import os.path

import plum.persistence.pickle_persistence
from plum.process import Process
from aiida.common.lang import override
from aiida.work.defaults import class_loader


class Persistence(plum.persistence.pickle_persistence.PicklePersistence):
    @override
    def load_checkpoint_from_file(self, filepath):
        cp = super(Persistence, self).load_checkpoint_from_file(filepath)

        inputs = cp[Process.BundleKeys.INPUTS.value]
        if inputs:
            cp[Process.BundleKeys.INPUTS.value] = self._load_nodes_from(inputs)

        cp.set_class_loader(class_loader)
        return cp

    @override
    def create_bundle(self, process):
        b = super(Persistence, self).create_bundle(process)

        inputs = b[Process.BundleKeys.INPUTS.value]
        if inputs:
            b[Process.BundleKeys.INPUTS.value] = self._convert_to_ids(inputs)

        return b

    def _convert_to_ids(self, nodes):
        from aiida.orm import Node

        input_ids = {}
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
        {label: {label: pk}} and convert to the equivalent dictionary but
        with nodes instead of the ids.

        :param pks_mapping: The dictionary of node pks.
        :return: A dictionary with the loaded nodes.
        :rtype: dict
        """
        from aiida.orm import load_node

        nodes = {}
        for label, pk in pks_mapping.iteritems():
            if isinstance(pk, collections.Mapping):
                nodes[label] = self._load_nodes_from(pk)
            else:
                nodes[label] = load_node(pk=pk)
        return nodes


_DEFAULT_STORAGE = None


def get_default():
    global _DEFAULT_STORAGE

    if _DEFAULT_STORAGE is None:
        _create_storage()

    return _DEFAULT_STORAGE


def _create_storage():
    import aiida.common.setup as setup
    import aiida.settings as settings
    global _DEFAULT_STORAGE

    parts = uritools.urisplit(settings.REPOSITORY_URI)
    if parts.scheme == u'file':
        WORKFLOWS_DIR = os.path.expanduser(
            os.path.join(parts.path, setup.WORKFLOWS_SUBDIR))

        _DEFAULT_STORAGE = Persistence(
            auto_persist=False,
            running_directory=os.path.join(WORKFLOWS_DIR, 'running'),
            finished_directory=os.path.join(WORKFLOWS_DIR, 'finished'),
            failed_directory=os.path.join(WORKFLOWS_DIR, 'failed'))
