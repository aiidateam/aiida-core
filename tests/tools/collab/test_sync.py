###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the export and import of the delta of a collab."""

import pytest

from aiida import orm
from aiida.common import timezone
from aiida.common.links import LinkType
from aiida.storage.sqlite_temp import SqliteTempBackend
from aiida.tools.collab.state import CollabEvent, CollabState
from aiida.tools.collab.sync import compute_delta, export_delta

PEER = 'http://100.64.0.2:9137'


def seal_calculation(backend, label):
    """Store a calculation with one input and one output in ``backend`` and seal it."""
    inputs = orm.Int(1, backend=backend).store()
    calculation = orm.CalcJobNode(backend=backend, label=label)
    calculation.base.links.add_incoming(inputs, link_type=LinkType.INPUT_CALC, link_label='input')
    calculation.store()
    outputs = orm.Int(2, backend=backend)
    outputs.base.links.add_incoming(calculation, link_type=LinkType.CREATE, link_label='result')
    outputs.store()
    calculation.seal()

    return calculation


@pytest.fixture
def peers(tmp_path):
    """Return a factory for the storage of a profile of a collab and the state of that profile."""
    backends = []

    def factory(name):
        backend = SqliteTempBackend(SqliteTempBackend.create_profile(filepath=str(tmp_path / name)))
        backends.append(backend)
        return backend, CollabState(filepath=tmp_path / f'{name}.json')

    yield factory

    for backend in backends:
        backend.close()


def node_count(backend):
    return orm.QueryBuilder(backend=backend).append(orm.Node).count()


def load_node(backend, uuid):
    return orm.QueryBuilder(backend=backend).append(orm.Node, filters={'uuid': uuid}).one()[0]


def linked_uuids(calculation):
    """Return the UUIDs of a calculation and of the nodes directly linked to it."""
    links = calculation.base.links.get_incoming().all() + calculation.base.links.get_outgoing().all()

    return {calculation.uuid} | {link.node.uuid for link in links}


def export_full(filepath, *, state, backend, cursor, claim=frozenset()):
    """Compute the delta and export all of it, as a requester that holds none of its nodes would receive it."""
    delta = compute_delta(state=state, backend=backend, cursor=cursor, claim=claim)

    return export_delta(filepath, delta=delta, backend=backend)


def test_export_only_sealed(tmp_path, peers):
    """Test that a sealed calculation is exported with its inputs and outputs, and an unsealed one is not."""
    backend, state = peers('one')
    sealed = seal_calculation(backend, 'sealed')
    unsealed = orm.CalcJobNode(backend=backend, label='unsealed').store()

    export = export_full(tmp_path / 'delta.aiida', state=state, backend=backend, cursor=None)

    assert set(export.uuids) == linked_uuids(sealed)
    assert unsealed.uuid not in export.uuids


def excepted_over_running(backend):
    """Store a sealed workchain that called a calculation which is still running, and return both.

    The workchain has an input of its own, which is reachable only through it.
    """
    excepted = orm.WorkChainNode(backend=backend, label='excepted')
    excepted.base.links.add_incoming(orm.Int(1, backend=backend).store(), link_type=LinkType.INPUT_WORK, link_label='x')
    excepted.store()
    running = orm.CalcJobNode(backend=backend, label='running')
    running.base.links.add_incoming(excepted, link_type=LinkType.CALL_CALC, link_label='child')
    running.store()
    excepted.seal()

    return excepted, running


def test_export_skips_unsealed_children(tmp_path, peers):
    """Test that a sealed process that called one which is still running is left out instead of aborting the export."""
    backend, state = peers('one')
    sealed = seal_calculation(backend, 'sealed')
    excepted_over_running(backend)

    export = export_full(tmp_path / 'delta.aiida', state=state, backend=backend, cursor=None)

    assert set(export.uuids) == linked_uuids(sealed)


def test_export_withheld_seed_travels_later(tmp_path, peers):
    """Test that a seed withheld for an unsealed child is offered again once that child seals.

    The export instant is pinned to the withheld seed, so a requester that stores it as its cursor presents one
    the seed still re-enters at.
    """
    backend, state = peers('one')
    excepted, running = excepted_over_running(backend)

    instant = export_full(tmp_path / 'delta.aiida', state=state, backend=backend, cursor=None).instant
    running.seal()

    export = export_full(tmp_path / 'delta-later.aiida', state=state, backend=backend, cursor=instant)

    assert linked_uuids(excepted) | {running.uuid} <= set(export.uuids)


def test_export_bounded_by_cursor(tmp_path, peers):
    """Test that a requester presenting the instant of the previous export is served nothing it already has."""
    backend, state = peers('one')
    seal_calculation(backend, 'sealed')

    export = export_full(tmp_path / 'delta.aiida', state=state, backend=backend, cursor=None)

    assert export.uuids

    again = export_full(tmp_path / 'delta-again.aiida', state=state, backend=backend, cursor=export.instant)

    assert again.uuids == []


def test_export_ignores_push_history(tmp_path, peers):
    """Test that the sender keeps no send-state: a recorded push does not diminish what a later requester is served."""
    backend, state = peers('one')
    seal_calculation(backend, 'sealed')

    export = export_full(tmp_path / 'delta.aiida', state=state, backend=backend, cursor=None)
    state.events.append(CollabEvent(time=timezone.now(), direction='push', peer=PEER, uuids=export.uuids, size=1))

    again = export_full(tmp_path / 'delta-again.aiida', state=state, backend=backend, cursor=None)

    assert set(again.uuids) == set(export.uuids)
