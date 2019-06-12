# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module with `Node` sub class for workchain processes."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.common.lang import classproperty

from .workflow import WorkflowNode

__all__ = ('WorkChainNode',)


class WorkChainNode(WorkflowNode):
    """ORM class for all nodes representing the execution of a WorkChain."""

    _cachable = False

    STEPPER_STATE_INFO_KEY = 'stepper_state_info'
    ERRORS_HANDLED_KEY = 'errors_handled'

    @classproperty
    def _updatable_attributes(cls):
        # pylint: disable=no-self-argument
        return super(WorkChainNode, cls)._updatable_attributes + (cls.STEPPER_STATE_INFO_KEY, cls.ERRORS_HANDLED_KEY)

    @property
    def stepper_state_info(self):
        """Return the stepper state info

        :returns: string representation of the stepper state info
        """
        return self.get_attribute(self.STEPPER_STATE_INFO_KEY, None)

    def set_stepper_state_info(self, stepper_state_info):
        """Set the stepper state info

        :param state: string representation of the stepper state info
        """
        return self.set_attribute(self.STEPPER_STATE_INFO_KEY, stepper_state_info)

    @property
    def errors_handled(self):
        """Return the errors handled during execution of this work chain.

        When an error is handled through an error handler, it can be added through `add_error_handled`.

        :return: a list of error handler method names
        """
        return self.get_attribute(self.ERRORS_HANDLED_KEY, None)

    def add_error_handled(self, error_handled):
        """Return the names of the error handlers that were triggered during execution

        :param state: string representation of the stepper state info
        """
        errors_handled = self.errors_handled or []
        errors_handled.append(error_handled)
        return self.set_attribute(self.ERRORS_HANDLED_KEY, errors_handled)
