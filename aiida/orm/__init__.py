# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Main module to expose all orm classes and methods"""
# pylint: disable=wildcard-import

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from .data import *
from .data.code import Code

from .authinfos import *
from .calculation import *
from .computers import *
from .entities import *
from .groups import *
from .logs import *
from .node import *
from .querybuilder import *
from .users import *
from .utils import *

# For legacy reasons support the singulars as well
authinfo = authinfos
computer = computers
group = groups
log = logs
user = users

_local = 'Code', 'CalculationFactory', 'DataFactory', 'WorkflowFactory', \
         'Group', 'user', 'Computer', 'group', 'computers', 'authinfo'

__all__ = (_local +
           authinfos.__all__ +
           calculation.__all__ +
           computers.__all__ +
           entities.__all__ +
           groups.__all__ +
           logs.__all__ +
           querybuilder.__all__ +
           users.__all__ +
           utils.__all__)
