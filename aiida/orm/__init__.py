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
from aiida.orm.code import Code
from aiida.orm.querybuilder import QueryBuilder
from aiida.orm.workflow import Workflow
from aiida.orm.group import Group

from .authinfos import *
from .calculation import *
from .computers import *
from .log import *
from .node import *
from .backends import *
from .users import *
from .utils import *
from .querybuilder import *

# For legacy reasons support the singulars as well
authinfo = authinfos
computer = computers
user = users

_local = 'JobCalculation', 'WorkCalculation', 'Code', 'CalculationFactory', 'DataFactory', 'WorkflowFactory', \
         'Workflow', 'Group', 'user', 'Computer'

__all__ = (_local +
           calculation.__all__ +
           utils.__all__ +
           users.__all__ +
           authinfos.__all__ +
           backends.__all__ +
           querybuilder.__all__)
