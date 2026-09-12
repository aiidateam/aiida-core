###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Main module to expose all orm classes and methods"""

# AUTO-GENERATED

# fmt: off

from aiida.orm.authinfos import *
from aiida.orm.comments import *
from aiida.orm.computers import *
from aiida.orm.entities import *
from aiida.orm.extras import *
from aiida.orm.fields import *
from aiida.orm.groups import *
from aiida.orm.logs import *
from aiida.orm.nodes import *
from aiida.orm.pydantic import *
from aiida.orm.querybuilder import *
from aiida.orm.users import *
from aiida.orm.utils import *

__all__ = (
    'ASCENDING',
    'DESCENDING',
    'AbstractCode',
    'AbstractNodeMeta',
    'ArrayData',
    'AttributeManager',
    'AuthInfo',
    'AutoGroup',
    'BaseType',
    'Bool',
    'CalcFunctionNode',
    'CalcJobNode',
    'CalcJobResultManager',
    'CalculationEntityLoader',
    'CalculationNode',
    'Code',
    'CodeEntityLoader',
    'Collection',
    'Comment',
    'Computer',
    'ComputerEntityLoader',
    'ContainerizedCode',
    'Data',
    'Dict',
    'Entity',
    'EntityExtras',
    'EntityTypes',
    'EntryPointData',
    'EnumData',
    'Float',
    'FolderData',
    'Group',
    'GroupEntityLoader',
    'ImportGroup',
    'InstalledCode',
    'Int',
    'JsonableData',
    'LinkManager',
    'LinkPair',
    'LinkTriple',
    'List',
    'Log',
    'Node',
    'NodeAttributes',
    'NodeEntityLoader',
    'NodeLinksManager',
    'NodeRepository',
    'NumericType',
    'OrderSpecifier',
    'OrmEntityLoader',
    'OrmModel',
    'PickledData',
    'PortableCode',
    'ProcessNode',
    'QbField',
    'QbFieldFilters',
    'QbFields',
    'QueryBuilder',
    'RemoteData',
    'RemoteStashCompressedData',
    'RemoteStashCustomData',
    'RemoteStashData',
    'RemoteStashFolderData',
    'ShellCode',
    'SinglefileData',
    'Str',
    'UpfFamily',
    'User',
    'WorkChainNode',
    'WorkFunctionNode',
    'WorkflowNode',
    'XyData',
    'get_loader',
    'get_query_type_from_type_string',
    'get_type_string_from_class',
    'load_code',
    'load_computer',
    'load_entity',
    'load_group',
    'load_node',
    'load_node_class',
    'to_aiida_type',
    'validate_link',
)

# fmt: on

# Added by utils/extract_atomistic.py: names that moved to the ``aiida-atomistic`` package.
# ``aiida-core`` must not hard-import the subpackage (see MONOREPO.md), so these
# resolve lazily and raise a helpful error when it is not installed.
import importlib as _importlib

_ATOMISTIC_REDIRECTS = {
    'BandsData': 'aiida_atomistic.orm.nodes.data.array.bands:BandsData',
    'CifData': 'aiida_atomistic.orm.nodes.data.cif:CifData',
    'Kind': 'aiida_atomistic.orm.nodes.data.structure:Kind',
    'KpointsData': 'aiida_atomistic.orm.nodes.data.array.kpoints:KpointsData',
    'OrbitalData': 'aiida_atomistic.orm.nodes.data.orbital:OrbitalData',
    'ProjectionData': 'aiida_atomistic.orm.nodes.data.array.projection:ProjectionData',
    'Site': 'aiida_atomistic.orm.nodes.data.structure:Site',
    'StructureData': 'aiida_atomistic.orm.nodes.data.structure:StructureData',
    'TrajectoryData': 'aiida_atomistic.orm.nodes.data.array.trajectory:TrajectoryData',
    'UpfData': 'aiida_atomistic.orm.nodes.data.upf:UpfData',
    'cif_from_ase': 'aiida_atomistic.orm.nodes.data.cif:cif_from_ase',
    'find_bandgap': 'aiida_atomistic.orm.nodes.data.array.bands:find_bandgap',
    'has_pycifrw': 'aiida_atomistic.orm.nodes.data.cif:has_pycifrw',
    'pycifrw_from_cif': 'aiida_atomistic.orm.nodes.data.cif:pycifrw_from_cif',
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
