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
from aiida.orm.data import *
from aiida.orm.data.code import Code
from aiida.orm.workflow import Workflow

from .authinfos import *
from .calculation import *
from .computers import *
from .groups import *
from .log import *
from .node import *
from .backends import *
from .users import *
from .utils import *
from .querybuilder import *

# For legacy reasons support the singulars as well
authinfo = authinfos
computer = computers
group = groups
user = users

_local = 'Code', 'CalculationFactory', 'DataFactory', 'WorkflowFactory', \
         'Workflow', 'Group', 'user', 'Computer', 'group', 'computers', 'authinfo'

__all__ = (_local +
           authinfos.__all__ +
           calculation.__all__ +
           computers.__all__ +
           utils.__all__ +
           users.__all__ +
           backends.__all__ +
           querybuilder.__all__ +
           groups.__all__)
