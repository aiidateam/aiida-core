###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module with `Node` sub class for workchain processes."""

from typing import TYPE_CHECKING, Optional, Tuple

from aiida.common import exceptions
from aiida.common.lang import classproperty

from .workflow import WorkflowNode

if TYPE_CHECKING:
    from aiida.tools.workflows import WorkflowTools

__all__ = ('WorkChainNode',)


class WorkChainNode(WorkflowNode):
    """ORM class for all nodes representing the execution of a WorkChain."""

    STEPPER_STATE_INFO_KEY = 'stepper_state_info'

    # An optional entry point for a WorkflowTools instance
    _tools = None

    @property
    def tools(self) -> Optional['WorkflowTools']:
        """Return the workflow tools that are registered for the process type associated with this workflow.

        If the entry point name stored in the `process_type` of the WorkChainNode has an accompanying entry point in the
        `aiida.tools.workflows` entry point category, it will attempt to load the entry point and instantiate it
        passing the node to the constructor. If the entry point does not exist, cannot be resolved or loaded, a warning
        will be logged and the base WorkflowTools class will be instantiated and returned.

        :return: WorkflowsTools instance
        """
        from aiida.plugins.entry_point import get_entry_point_from_string, is_valid_entry_point_string, load_entry_point
        from aiida.tools.workflows import WorkflowTools

        if self._tools is None:
            entry_point_string = self.process_type

            if entry_point_string and is_valid_entry_point_string(entry_point_string):
                entry_point = get_entry_point_from_string(entry_point_string)

                try:
                    tools_class = load_entry_point('aiida.tools.workflows', entry_point.name)
                    self._tools = tools_class(self)
                except exceptions.EntryPointError as exception:
                    self._tools = WorkflowTools(self)
                    self.logger.warning(
                        f'could not load the workflow tools entry point {entry_point.name}: {exception}'
                    )

        return self._tools

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
