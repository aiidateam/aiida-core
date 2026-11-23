###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""ORM node for a function-backed task."""

import typing as t

from aiida.common.lang import override
from aiida.common.links import LinkType
from aiida.orm.nodes.process.calculation.calculation import CalculationNode
from aiida.orm.nodes.process.process import ProcessNodeLinks
from aiida.orm.utils.mixins import FunctionCalculationMixin

if t.TYPE_CHECKING:
    from aiida.orm import Node

__all__ = ('TaskNode',)


class TaskNodeLinks(ProcessNodeLinks):
    """Link constraints for function-backed tasks."""

    @override
    def validate_outgoing(self, target: 'Node', link_type: LinkType, link_label: str) -> None:
        """Reject claiming creation of an already stored output."""
        super().validate_outgoing(target, link_type, link_label)
        if link_type is LinkType.CREATE and target.is_stored:
            msg = (
                'a task cannot create an already stored node; '
                'return a new node or mark the input mutable to edit a copy.'
            )
            raise ValueError(msg)


class TaskNode(FunctionCalculationMixin, CalculationNode):
    """Record the execution of a function-backed task."""

    _CLS_NODE_LINKS = TaskNodeLinks
    CHECKPOINT_OUTPUT_DIGEST = 'checkpoint_output_digest'
    _updatable_attributes = (*CalculationNode._updatable_attributes, CHECKPOINT_OUTPUT_DIGEST)
