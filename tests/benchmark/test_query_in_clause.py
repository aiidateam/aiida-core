###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Performance benchmark tests for ``IN`` filters on large value lists.

Above ``aiida.storage.utils.IN_CLAUSE_BATCH_SIZE_FLOOR`` the list is split into batches, which each
dialect combines in the shape its planner handles best. The real floor is 500k, far more values than
a benchmark wants to seed, so these parametrise over it to put the batching branch within reach.

What they measure is the cost of batching itself, against the same query unbatched. The planner
difference that motivated the batching shapes is between dialects, not between batch sizes, so it
does not show up here. A run on a loaded machine is dominated by the load rather than by any of
this: the spread across batch sizes is small, so treat a difference as real only once the standard
deviations separate.
"""

import pytest

from aiida import orm
from aiida.storage.utils import IN_CLAUSE_BATCH_SIZE_FLOOR
from tests.utils.nodes import create_int_nodes

GROUP_NAME = 'query-in-clause'

# Enough nodes for the filter to do real work, seeded through bulk_insert: ~9k nodes/s, so a couple
# of seconds. Creating them one at a time through the ORM runs at ~240/s and is not worth the wait.
NUM_NODES = 20_000

# Batch sizes to compare, as fractions of NUM_NODES, so each yields a different number of batches.
BATCH_SIZES = [500, 2_000, 10_000]


@pytest.fixture(scope='module')
def int_node_pks(aiida_profile):
    """Return the PKs of a fixed set of stored ``Int`` nodes, seeded once for the whole module."""
    aiida_profile.reset_storage()
    return create_int_nodes(NUM_NODES)


@pytest.mark.benchmark(group=GROUP_NAME, min_rounds=100)
@pytest.mark.parametrize('batch_size', BATCH_SIZES)
def test_in_filter_batched(benchmark, monkeypatch, int_node_pks, batch_size):
    """Benchmark an ``IN`` filter over every seeded PK, batched at ``batch_size``."""
    monkeypatch.setattr('aiida.storage.utils.IN_CLAUSE_BATCH_SIZE_FLOOR', batch_size)

    def query():
        return orm.QueryBuilder().append(orm.Int, filters={'id': {'in': int_node_pks}}).count()

    assert benchmark(query) == NUM_NODES


@pytest.mark.benchmark(group=GROUP_NAME, min_rounds=100)
def test_in_filter_unbatched(benchmark, int_node_pks):
    """Benchmark the same filter below the floor, so it stays a single subquery.

    The baseline the batched cases above are worth comparing against.
    """
    assert NUM_NODES < IN_CLAUSE_BATCH_SIZE_FLOOR, 'the floor has to leave this list unbatched'

    def query():
        return orm.QueryBuilder().append(orm.Int, filters={'id': {'in': int_node_pks}}).count()

    assert benchmark(query) == NUM_NODES
