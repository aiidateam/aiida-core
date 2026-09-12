###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utilities to build :class:`~aiida.orm.nodes.data.data.Data` nodes from plain Python values."""

from __future__ import annotations

import pathlib
import typing as t

from aiida.orm.nodes.data.data import Data
from aiida.orm.nodes.data.singlefile import SinglefileData


def convert_nodes_single_file_data(nodes: t.Mapping[str, str | pathlib.Path | Data]) -> t.MutableMapping[str, Data]:
    """Convert ``str`` and ``pathlib.Path`` instances to ``SinglefileData`` nodes.

    :param nodes: Dictionary of ``Data``, ``str``, or ``pathlib.Path``.
    :raises TypeError: If a value in the mapping is of invalid type.
    :raises FileNotFoundError: If a filepath ``str`` or ``pathlib.Path`` does not correspond to existing file.
    :returns: Dictionary of filenames onto ``SinglefileData`` nodes.
    """
    processed_nodes: t.MutableMapping[str, Data] = {}

    for key, value in nodes.items():
        if isinstance(value, Data):
            processed_nodes[key] = value
            continue

        if isinstance(value, str):
            filepath = pathlib.Path(value)
        else:
            filepath = value

        if not isinstance(filepath, pathlib.Path):
            raise TypeError(
                f'received type {type(filepath)} for `{key}` in `nodes`. Should be `Data`, `str`, or `Path`.'
            )

        filepath.resolve()

        if not filepath.exists():
            msg = f'the path `{filepath}` specified in `nodes` does not exist.'
            raise FileNotFoundError(msg)

        with filepath.open('rb') as handle:
            processed_nodes[key] = SinglefileData(handle, filename=str(filepath.name))

    return processed_nodes
