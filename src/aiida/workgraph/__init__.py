from .workgraph import WorkGraph
from .task import Task
from .decorator import task
from .tasks import TaskPool
from .tasks.shelljob_task import shelljob
from .manager import get_current_graph, If, Map, While, Zone
from . import socket_spec as spec
from .socket_spec import namespace, dynamic, select, meta
from .collection import group

__version__ = '0.8.1'

__all__ = [
    'WorkGraph',
    'Task',
    'task',
    'get_current_graph',
    'Zone',
    'If',
    'Map',
    'While',
    'TaskPool',
    'shelljob',
    'spec',
    'namespace',
    'dynamic',
    'select',
    'meta',
    'group',
]
