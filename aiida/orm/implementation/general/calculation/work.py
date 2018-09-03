# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from __future__ import absolute_import
from aiida.common.utils import classproperty
from aiida.orm.implementation.calculation import Calculation


class WorkCalculation(Calculation):
    """
    Calculation node to record the results of a :class:`aiida.work.processes.Process`
    from the workflow system in the database
    """

    STEPPER_STATE_INFO_KEY = 'stepper_state_info'

    @classproperty
    def _updatable_attributes(cls):
        return super(WorkCalculation, cls)._updatable_attributes + (cls.STEPPER_STATE_INFO_KEY,)

    @property
    def stepper_state_info(self):
        """
        Return the stepper state info of the Calculation

        :returns: string representation of the stepper state info
        """
        return self.get_attr(self.STEPPER_STATE_INFO_KEY, None)

    def set_stepper_state_info(self, stepper_state_info):
        """
        Set the stepper state info of the Calculation

        :param state: string representation of the stepper state info
        """
        return self._set_attr(self.STEPPER_STATE_INFO_KEY, stepper_state_info)
