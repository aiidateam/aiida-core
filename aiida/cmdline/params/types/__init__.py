# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Provides all parameter types."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from .calculation import CalculationParamType
from .choice import LazyChoice
from .code import CodeParamType
from .computer import ComputerParamType, ShebangParamType, MpirunCommandParamType
from .config import ConfigOptionParamType
from .data import DataParamType
from .group import GroupParamType
from .identifier import IdentifierParamType
from .multiple import MultipleValueParamType
from .node import NodeParamType
from .process import ProcessParamType
from .nonemptystring import NonEmptyStringParamType
from .path import AbsolutePathParamType
from .plugin import PluginParamType
from .profile import ProfileParamType
from .user import UserParamType
from .test_module import TestModuleParamType
from .workflow import WorkflowParamType

__all__ = ('LazyChoice', 'IdentifierParamType', 'CalculationParamType', 'CodeParamType', 'ComputerParamType',
           'ConfigOptionParamType', 'DataParamType', 'GroupParamType', 'NodeParamType', 'MpirunCommandParamType',
           'MultipleValueParamType', 'NonEmptyStringParamType', 'PluginParamType', 'AbsolutePathParamType',
           'ShebangParamType', 'UserParamType', 'TestModuleParamType', 'ProfileParamType', 'WorkflowParamType',
           'ProcessParamType')
