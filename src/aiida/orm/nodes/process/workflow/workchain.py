###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module with `Node` sub class for workchain processes."""

from typing import Optional, Tuple

from aiida.common.lang import classproperty

from .workflow import WorkflowNode

__all__ = ('WorkChainNode',)


class WorkChainNode(WorkflowNode):
    """ORM class for all nodes representing the execution of a WorkChain."""

    STEPPER_STATE_INFO_KEY = 'stepper_state_info'

    @classproperty
    def _updatable_attributes(cls) -> Tuple[str, ...]:  # noqa: N805
        return super()._updatable_attributes + (cls.STEPPER_STATE_INFO_KEY,)

    @property
    def stepper_state_info(self) -> Optional[str]:
        """Return the stepper state info

        :returns: string representation of the stepper state info
        """
        return self.base.attributes.get(self.STEPPER_STATE_INFO_KEY, None)

    def set_stepper_state_info(self, stepper_state_info: str) -> None:
        """Set the stepper state info

        :param state: string representation of the stepper state info
        """
        return self.base.attributes.set(self.STEPPER_STATE_INFO_KEY, stepper_state_info)
