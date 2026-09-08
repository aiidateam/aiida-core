"""Sub commands of the ``verdi`` command line interface.

The commands need to be imported here for them to be registered with the top-level command group.
"""

from aiida.plugins.entry_point import get_entry_points
from aiida.workgraph.cli import cmd_task

eps = get_entry_points('workgraph.cmdline')
for ep in eps:
    ep.load()

__all__ = ['cmd_task']
