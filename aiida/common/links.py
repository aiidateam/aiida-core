# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from enum import Enum



class LinkType(Enum):
    """
    A simple enum of allowed link types.
    """
    UNSPECIFIED = 'unspecified'
    CREATE = 'createlink'
    RETURN = 'returnlink'
    INPUT = 'inputlink'
    CALL = 'calllink'
