###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file      #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Branch member contracts and mapped result members in static graph metadata.

Branch arms sharing a stored container but declaring different members (for
example ``list[int]`` against ``list[str]``) must fail at build instead of
claiming the taken arm's member. Matching arms keep their member, and maps
expose the mapped callable's result as the result container's member.
"""

import pytest

from aiida.common.exceptions import GraphTypeCheckError
from aiida.engine.processes.graphs.lowering import compile_graph, graph, par_map, task
from aiida.engine.processes.graphs.shapes import LeafShape
from aiida.orm import DataList
from aiida.orm.nodes.data.int import Int
from aiida.orm.nodes.data.list import List


@task
def pack_ints(x: int) -> list[int]:
    """Pack one integer as a plain list."""
    return [x]


@task
def wrap_ints(x: int) -> list[int]:
    """Wrap one integer as a plain list through a second task."""
    return [x + 0]


@task
def pack_strs(x: int) -> list[str]:
    """Pack one integer spelling as a plain list."""
    return [str(x)]


@task
def bump(x: int) -> int:
    """Add one to the input."""
    return x + 1


@graph
def choose_int_lists(x: int, flag: bool) -> list[int]:
    """Select between two integer lists; the joined wire keeps the member."""
    return pack_ints(x=x) if flag else wrap_ints(x=x)


@graph
def choose_mixed_lists(x: int, flag: bool) -> list[int]:
    """Select between integer and string lists; the members disagree."""
    return pack_ints(x=x) if flag else pack_strs(x=x)


@graph
def map_ints(values: DataList) -> DataList:
    """Map a scalar task over an owned list."""
    return par_map(bump, values)


def test_matching_branch_arms_keep_member() -> None:
    """Two integer-list arms expose one integer-list member."""
    assert compile_graph(choose_int_lists).result_shape == LeafShape(types=(List,), element=LeafShape(types=(int,)))


def test_mismatched_branch_members_rejected() -> None:
    """Integer-list against string-list arms fail at build."""
    with pytest.raises(GraphTypeCheckError, match='incompatible collection members'):
        compile_graph(choose_mixed_lists)


def test_mapped_result_propagates_member() -> None:
    """A mapped scalar result becomes the result container's member."""
    assert compile_graph(map_ints).result_shape == LeafShape(types=(DataList,), element=LeafShape(types=(Int,)))
