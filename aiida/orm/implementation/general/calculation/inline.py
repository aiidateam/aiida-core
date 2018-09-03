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
from aiida.orm.implementation.calculation import Calculation
from aiida.orm.mixins import FunctionCalculationMixin


class InlineCalculation(FunctionCalculationMixin, Calculation):
    """
    Calculation node to record the results of a function that was run wrapped by the
    :class:`aiida.orm.calculation.inline.make_inline` decorator
    """

    _cacheable = True

    def get_desc(self):
        """
        Returns a string with the name of function that was wrapped by the make_inline decorator
        that resulted in the creation of this InlineCalculation instance

        :return: description string or None if no function name can be retrieved from the node
        """
        if self.function_name is not None:
            return '{}()'.format(self.function_name)
        else:
            return None
