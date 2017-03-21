# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

import plum.process
import plum.knowledge_provider
import plum.in_memory_database
import plum.process_monitor
import aiida.common.exceptions as exceptions
from aiida.common.lang import override
from aiida.work.util import ProcessStack


class ProcessRegistry(plum.knowledge_provider.KnowledgeProvider):
    """
    This class is a knowledge provider that uses the AiiDA database to answer
    questions related to processes.
    """
    @property
    def current_pid(self):
        return ProcessStack.top().pid

    @property
    def current_calc_node(self):
        return ProcessStack.top().calc

    @override
    def has_finished(self, pid):
        from aiida.orm.calculation.job import JobCalculation
        from aiida.orm.calculation.work import WorkCalculation

        import aiida.orm

        try:
            node = aiida.orm.load_node(pid)
        except exceptions.NotExistent:
            raise plum.knowledge_provider.NotKnown(
                "Can't find node with pk '{}'".format(pid))
        else:
            if isinstance(node, JobCalculation):
                return node.has_finished()
            elif isinstance(node, WorkCalculation):
                return node.is_sealed
            else:
                raise plum.knowledge_provider.NotKnown(
                    "The node is of an unexpected type.")

    @override
    def get_inputs(self, pid):
        from aiida.orm import load_node

        try:
            return load_node(pid).get_inputs_dict()
        except exceptions.NotExistent:
            raise plum.knowledge_provider.NotKnown(
                "Can't find node with pk '{}'".format(pid))

    @override
    def get_outputs(self, pid):
        from aiida.orm import load_node

        try:
            return {e[0]: e[1]
                    for e in load_node(pid).get_outputs(also_labels=True)}
        except exceptions.NotExistent:
            raise plum.knowledge_provider.NotKnown(
                "Can't find node with pk '{}'".format(pid))
