###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module with `Node` sub classes for array based data structures."""

# AUTO-GENERATED

# fmt: off

from aiida.orm.nodes.data.array.array import *
from aiida.orm.nodes.data.array.xy import *

__all__ = (
    'ArrayData',
    'XyData',
)

# fmt: on

# Added by utils/extract_atomistic.py: names that moved to the ``aiida-atomistic`` package.
# ``aiida-core`` must not hard-import the subpackage (see MONOREPO.md), so these
# resolve lazily and raise a helpful error when it is not installed.
import importlib as _importlib

_ATOMISTIC_REDIRECTS = {
    'BandsData': 'aiida_atomistic.orm.nodes.data.array.bands:BandsData',
    'KpointsData': 'aiida_atomistic.orm.nodes.data.array.kpoints:KpointsData',
    'ProjectionData': 'aiida_atomistic.orm.nodes.data.array.projection:ProjectionData',
    'TrajectoryData': 'aiida_atomistic.orm.nodes.data.array.trajectory:TrajectoryData',
    'find_bandgap': 'aiida_atomistic.orm.nodes.data.array.bands:find_bandgap',
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
