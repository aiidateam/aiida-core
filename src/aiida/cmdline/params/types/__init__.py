###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Provides all parameter types."""

# AUTO-GENERATED

# fmt: off

from .calculation import *
from .choice import *
from .code import *
from .computer import *
from .config import *
from .data import *
from .group import *
from .identifier import *
from .multiple import *
from .node import *
from .path import *
from .plugin import *
from .process import *
from .profile import *
from .strings import *
from .user import *
from .workflow import *

__all__ = (
    'AbsolutePathParamType',
    'CalculationParamType',
    'CodeParamType',
    'ComputerParamType',
    'ConfigOptionParamType',
    'DataParamType',
    'EmailType',
    'EntryPointType',
    'FileOrUrl',
    'GroupParamType',
    'HostnameType',
    'IdentifierParamType',
    'LabelStringType',
    'LazyChoice',
    'MpirunCommandParamType',
    'MultipleValueParamType',
    'NodeParamType',
    'NonEmptyStringParamType',
    'PathOrUrl',
    'PluginParamType',
    'ProcessParamType',
    'ProfileParamType',
    'ShebangParamType',
    'UserParamType',
    'WorkflowParamType',
)

# fmt: on
