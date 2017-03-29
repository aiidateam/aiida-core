# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Classes needed for tests.
Must be here because subclasses of 'Node' must be within aiida.orm
"""
from aiida.orm.calculation import Calculation



class myNodeWithFields(Calculation):
    # State can be updated even after storing
    _updatable_attributes = ('state',)
