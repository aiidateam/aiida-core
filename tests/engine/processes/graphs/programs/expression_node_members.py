###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Graph programs forwarding owned members through inline comprehensions.

Every accepted graph threads a node-valued collection expression into an
``@task`` consumer annotated ``list[Int]``/``dict[str, Int]``, so the root
output stays a task-produced node with normal provenance. The expressions
return plain Python at runtime; only their static contract declares the owned
``DataList``/``DataDict`` shape.
"""

from aiida.engine.processes.graphs.lowering import graph, task
from aiida.orm import Int


@task
def consume_nodes(values: list[Int]) -> int:
    """Sum owned members; runtime values stay a plain list of nodes."""
    assert type(values) is list
    assert all(isinstance(item, Int) for item in values)
    return sum(item.value for item in values)


@task
def consume_mapping(values: dict[str, Int]) -> int:
    """Sum owned mapping values; runtime values stay a plain dict of nodes."""
    assert type(values) is dict
    assert all(isinstance(item, Int) for item in values.values())
    return sum(item.value for item in values.values())


@graph
def forward_nodes(values: list[Int]) -> int:
    """Forward every owned member inline into the owned consumer."""
    forwarded = [item for item in values]  # noqa: C416 - exercise comprehension syntax
    return consume_nodes(values=forwarded)


@graph
def filtered_nodes(values: list[Int]) -> int:
    """Forward only positive owned members inline into the owned consumer."""
    kept = [item for item in values if item.value > 0]
    return consume_nodes(values=kept)


@graph
def forward_mapping(values: dict[str, Int]) -> int:
    """Forward every owned mapping value inline into the owned consumer."""
    forwarded = {key: value for key, value in values.items()}  # noqa: C416 - exercise comprehension syntax
    return consume_mapping(values=forwarded)


@graph
def filtered_mapping(values: dict[str, Int]) -> int:
    """Forward only positive owned mapping values inline into the owned consumer."""
    kept = {key: value for key, value in values.items() if value.value > 0}
    return consume_mapping(values=kept)
