###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Atomistic (materials-science) data types and tools for AiiDA.

Provenance contract: entry-point names (e.g. ``core.structure``) and class
names are identical to the ones formerly shipped by ``aiida-core``; only the
import paths changed from ``aiida.*`` to ``aiida_atomistic.*``.
"""

import importlib as _importlib

__version__ = '0.1.0a0'

# Flat public API (file layout is an implementation detail). Resolved lazily:
# leaf modules import back from ``aiida-core`` at module level, so eager
# star imports here would trigger circular imports.
__all__ = (
    'BandsData',
    'CifData',
    'Kind',
    'KpointsData',
    'Orbital',
    'OrbitalData',
    'ProjectionData',
    'RealhydrogenOrbital',
    'Site',
    'StructureData',
    'TrajectoryData',
    'UpfData',
    'cif_from_ase',
    'find_bandgap',
    'get_explicit_kpoints_path',
    'get_kpoints_path',
    'has_pycifrw',
    'pycifrw_from_cif',
    'spglib_tuple_to_structure',
    'structure_to_spglib_tuple',
)

_PUBLIC_API = {
    'BandsData': 'aiida_atomistic.orm.nodes.data.array.bands',
    'CifData': 'aiida_atomistic.orm.nodes.data.cif',
    'Kind': 'aiida_atomistic.orm.nodes.data.structure',
    'KpointsData': 'aiida_atomistic.orm.nodes.data.array.kpoints',
    'Orbital': 'aiida_atomistic.tools.data.orbital.orbital',
    'OrbitalData': 'aiida_atomistic.orm.nodes.data.orbital',
    'ProjectionData': 'aiida_atomistic.orm.nodes.data.array.projection',
    'RealhydrogenOrbital': 'aiida_atomistic.tools.data.orbital.realhydrogen',
    'Site': 'aiida_atomistic.orm.nodes.data.structure',
    'StructureData': 'aiida_atomistic.orm.nodes.data.structure',
    'TrajectoryData': 'aiida_atomistic.orm.nodes.data.array.trajectory',
    'UpfData': 'aiida_atomistic.orm.nodes.data.upf',
    'cif_from_ase': 'aiida_atomistic.orm.nodes.data.cif',
    'find_bandgap': 'aiida_atomistic.orm.nodes.data.array.bands',
    'get_explicit_kpoints_path': 'aiida_atomistic.tools.data.array.kpoints.main',
    'get_kpoints_path': 'aiida_atomistic.tools.data.array.kpoints.main',
    'has_pycifrw': 'aiida_atomistic.orm.nodes.data.cif',
    'pycifrw_from_cif': 'aiida_atomistic.orm.nodes.data.cif',
    'spglib_tuple_to_structure': 'aiida_atomistic.tools.data.structure',
    'structure_to_spglib_tuple': 'aiida_atomistic.tools.data.structure',
}


def __getattr__(name: str):
    """Lazily resolve flat public names to their defining submodules."""
    if name in _PUBLIC_API:
        return getattr(_importlib.import_module(_PUBLIC_API[name]), name)
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
