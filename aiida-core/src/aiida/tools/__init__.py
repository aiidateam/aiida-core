###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tools to operate on AiiDA ORM class instances

What functionality should go directly in the ORM class in `aiida.orm` and what in `aiida.tools`?

    - The ORM class should define basic functions to set and get data from the object
    - More advanced functionality to operate on the ORM class instances can be placed in `aiida.tools`
        to prevent the ORM namespace from getting too cluttered.

.. note:: Modules in this sub package may require the database environment to be loaded

"""

# AUTO-GENERATED

# fmt: off

from aiida.tools.archive import *
from aiida.tools.calculations import *
from aiida.tools.graph import *
from aiida.tools.groups import *
from aiida.tools.shell import *
from aiida.tools.visualization import *
from aiida.tools.workflows import *

__all__ = (
    'ArchiveExportError',
    'ArchiveImportError',
    'CalculationTools',
    'ExportImportException',
    'ExportValidationError',
    'Graph',
    'GroupNotFoundError',
    'GroupNotUniqueError',
    'GroupPath',
    'ImportUniquenessError',
    'ImportValidationError',
    'InvalidPath',
    'NoGroupsInPathError',
    'WorkflowTools',
    'create_archive',
    'default_link_styles',
    'default_node_styles',
    'default_node_sublabels',
    'delete_group_nodes',
    'delete_nodes',
    'import_archive',
    'launch_shell_job',
    'pstate_node_styles',
)

# fmt: on

# Added by utils/extract_atomistic.py: names that moved to the ``aiida-atomistic`` package.
# ``aiida-core`` must not hard-import the subpackage (see MONOREPO.md), so these
# resolve lazily and raise a helpful error when it is not installed.
import importlib as _importlib

_ATOMISTIC_REDIRECTS = {
    'Orbital': 'aiida_atomistic.tools.data.orbital.orbital:Orbital',
    'RealhydrogenOrbital': 'aiida_atomistic.tools.data.orbital.realhydrogen:RealhydrogenOrbital',
    'get_explicit_kpoints_path': 'aiida_atomistic.tools.data.array.kpoints.main:get_explicit_kpoints_path',
    'get_kpoints_path': 'aiida_atomistic.tools.data.array.kpoints.main:get_kpoints_path',
    'spglib_tuple_to_structure': 'aiida_atomistic.tools.data.structure:spglib_tuple_to_structure',
    'structure_to_spglib_tuple': 'aiida_atomistic.tools.data.structure:structure_to_spglib_tuple',
}


def __getattr__(name: str):
    """Lazily resolve names that moved to :mod:`aiida_atomistic`."""
    if name in _ATOMISTIC_REDIRECTS:
        modpath, attr = _ATOMISTIC_REDIRECTS[name].split(':')
        try:
            module = _importlib.import_module(modpath)
        except ImportError as exc:
            msg = (
                f'{name!r} moved to the `aiida-atomistic` package, which is not installed. '
                'Install it with `pip install aiida-atomistic` (or `uv sync --project aiida-atomistic`).'
            )
            raise AttributeError(msg) from exc
        return getattr(module, attr)
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
