# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.orm.calculation import Calculation
from aiida.orm.implementation.calculation import JobCalculation as _JC, \
    _input_subfolder

class JobCalculation(_JC):
    """
    Here I put all the attributes/method that are common to all backends
    """

    def get_desc(self):
        """
        Returns a string with infos retrieved from a JobCalculation node's 
        properties.
        """
        return self.get_state(from_attribute=True)
