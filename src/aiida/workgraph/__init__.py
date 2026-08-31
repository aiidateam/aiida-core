###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The AiiDA WorkGraph: a data-dependency workflow language and runtime.

This subpackage is the AiiDA-specific layer over the generic node-graph SDK. It depends on node-graph, so it is not
imported from aiida-core's own import path; a plain ``import aiida`` stays free of the node-graph dependency, which the
workgraph install provides. Hand-maintained (excluded from the autogenerate-imports hook) so that importing it exposes
the curated authoring API without pulling optional plugin task types.
"""

from aiida import __version__ as __version__

from . import decorator
from . import socket_spec as spec
from .collection import group
from .enums import *
from .manager import If, Map, While, Zone, get_current_graph
from .serialization import *
from .socket_spec import dynamic, meta, namespace, select
from .task import Task
from .tasks import TaskPool
from .utils import (
    get_nested_dict,
    resolve_node_link_managers,
    update_nested_dict,
    update_nested_dict_with_special_keys,
)
from .workgraph import WorkGraph

# The ``task`` decorator must be the ``aiida.workgraph.task`` package attribute; the
# ``from .task import Task`` import above otherwise binds the ``task`` *submodule* there.
task = decorator.task

__all__ = (
    'TERMINAL_TASK_STATES',
    'AiidaSerializationAdapter',
    'If',
    'Map',
    'RuntimeInfoKey',
    'Task',
    'TaskAction',
    'TaskActionMessage',
    'TaskPool',
    'TaskState',
    'While',
    'WorkGraph',
    'Zone',
    'dynamic',
    'get_current_graph',
    'get_nested_dict',
    'group',
    'meta',
    'namespace',
    'resolve_node_link_managers',
    'select',
    'serialize_ports',
    'spec',
    'task',
    'update_nested_dict',
    'update_nested_dict_with_special_keys',
)
