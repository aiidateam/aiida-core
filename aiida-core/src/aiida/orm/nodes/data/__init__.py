###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module with `Node` sub classes for data structures."""

# AUTO-GENERATED

# fmt: off

from aiida.orm.nodes.data.array import *
from aiida.orm.nodes.data.base import *
from aiida.orm.nodes.data.bool import *
from aiida.orm.nodes.data.code import *
from aiida.orm.nodes.data.data import *
from aiida.orm.nodes.data.dict import *
from aiida.orm.nodes.data.entry_point import *
from aiida.orm.nodes.data.enum import *
from aiida.orm.nodes.data.float import *
from aiida.orm.nodes.data.folder import *
from aiida.orm.nodes.data.int import *
from aiida.orm.nodes.data.jsonable import *
from aiida.orm.nodes.data.list import *
from aiida.orm.nodes.data.numeric import *
from aiida.orm.nodes.data.pickled import *
from aiida.orm.nodes.data.remote import *
from aiida.orm.nodes.data.singlefile import *
from aiida.orm.nodes.data.str import *

__all__ = (
    'AbstractCode',
    'ArrayData',
    'BaseType',
    'Bool',
    'Code',
    'ContainerizedCode',
    'Data',
    'Dict',
    'EntryPointData',
    'EnumData',
    'Float',
    'FolderData',
    'InstalledCode',
    'Int',
    'JsonableData',
    'List',
    'NumericType',
    'PickledData',
    'PortableCode',
    'RemoteData',
    'RemoteStashCompressedData',
    'RemoteStashCustomData',
    'RemoteStashData',
    'RemoteStashFolderData',
    'ShellCode',
    'SinglefileData',
    'Str',
    'XyData',
    'to_aiida_type',
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
