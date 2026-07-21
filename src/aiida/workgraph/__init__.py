###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The AiiDA WorkGraph: a data-dependency workflow language and runtime.

This subpackage is the AiiDA-specific layer over the generic node-graph SDK. It is imported lazily and depends on
node-graph, so it must not be imported from aiida-core's own import path; a plain ``import aiida`` stays free of the
node-graph dependency, which the (optional) workgraph install provides.
"""

# AUTO-GENERATED

# fmt: off

from .enums import *
from .utils import *

__all__ = (
    'TERMINAL_TASK_STATES',
    'RuntimeInfoKey',
    'TaskAction',
    'TaskActionMessage',
    'TaskState',
    'get_nested_dict',
    'resolve_node_link_managers',
    'update_nested_dict',
    'update_nested_dict_with_special_keys',
)

# fmt: on
