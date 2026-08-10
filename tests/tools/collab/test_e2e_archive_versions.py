###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The interchange contract: the archive format is what a collab of mixed aiida-core versions rests on.

A delta travels as an archive, so the archive format is the one version that has to be agreed between two
members. The storage schema of either side deliberately is not: a collab of a PostgreSQL profile and a SQLite one
is first-class, and nothing here may gate on it.
"""

import pytest

from tests.tools.collab.conftest import move

DIRECTIONS = ('pull', 'push')

# The archive revision before the current head, which is what an older aiida-core writes.
OLDER_VERSION = 'main_0000'


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_a_thin_delta_at_an_older_format_is_migrated_and_imported(collab, faults, direction):
    """Test that a thin delta written at an older archive format is migrated forward, boundary links and all.

    The case ``phase-11/deferred.md`` recorded as untested: the migration was only ever exercised against a
    full-closure archive, and the boundary links a collab depends on live in a metadata key of its own that no
    migration knows about.
    """
    a, b, _ = collab(3)
    first = a.seal_calculation()

    move(a, b, direction)

    # A second generation whose input node Bob already holds, so the delta is thin and its link crosses the
    # boundary rather than travelling as a row.
    second = a.seal_calculation(inputs=first)

    faults.export_at_version(OLDER_VERSION)

    move(a, b, direction)

    assert second in b.uuids()
    assert b.graph() == a.graph()


def test_a_peer_writing_a_newer_format_is_not_pulled_from(collab, faults):
    """EXPECTED (phase 11): a peer this profile cannot read is skipped, with the message that names who must act.

    Only the sending side can be too new, since a profile reads its own format and every older one — so pulling
    is the direction that is refused when the *peer* is ahead, and the advice is to upgrade oneself.
    """
    a, b, c = collab(3)
    created = c.seal_calculation()

    # The skew has to be one the loop gets past, not one it ends on.
    assert list(a.peers()) == [b.uuid, c.uuid]
    faults.claims(b, archive_schema='main_9999')

    result = a.run('pull', ['--force'])

    assert 'cannot pull from the peer' in result.output
    assert 'upgrade it to the latest stable release' in result.output
    assert created in a.uuids(), 'the skew with one peer stopped the sync with the others'


def test_a_peer_reading_an_older_format_is_not_pushed_to(collab, faults):
    """EXPECTED (phase 11): a peer that could not read this profile's delta is skipped, not upgraded around.

    The mirror of the test above, and single-direction for the same reason: only the sending side can be too new,
    so each skew has exactly one direction it is refused in.
    """
    a, b, c = collab(3)
    created = a.seal_calculation()

    assert list(a.peers()) == [b.uuid, c.uuid]
    faults.claims(b, archive_schema='main_0000')

    result = a.run('push', ['--force'])

    assert 'cannot push to the peer' in result.output
    assert 'ask your collaborator to upgrade' in result.output
    assert created not in b.uuids()
    assert created in c.uuids(), 'the skew with one peer stopped the sync with the others'


@pytest.mark.parametrize('direction', DIRECTIONS)
def test_a_different_storage_backend_is_not_a_gate(collab, faults, direction):
    """Test that two members on different storage backends and schemas sync without complaint.

    The storage schema is each profile's own concern; declaring it in the handshake is for display. Faked here
    rather than run against PostgreSQL, because what is under test is the gate, and the gate is the only thing
    that could make a mixed collab impossible.
    """
    a, b, _ = collab(3)
    created = a.seal_calculation()

    faults.claims(b, backend='core.psql_dos', storage_schema='some-other-schema')

    move(a, b, direction)

    assert created in b.uuids()
    assert b.graph() == a.graph()


def test_verdi_archive_import_refuses_a_thin_delta(collab, tmp_path):
    """Test that a thin delta imported as a general-purpose archive is refused and names the command that does it.

    Its boundary links live in a metadata key the archive importer knows nothing about, so importing it there
    would land the nodes with their links to everything outside the delta silently missing.
    """
    from aiida.cmdline.commands.cmd_archive import import_archive
    from aiida.tools.collab.state import CollabState
    from aiida.tools.collab.sync import compute_delta, export_delta

    a, b, _ = collab(3)
    first = a.seal_calculation()

    b.run('pull', ['alice', '--force'])

    a.seal_calculation(inputs=first)

    state = CollabState.read(a.state_filepath)
    delta = compute_delta(state=state, backend=a.backend, cursor=None, claim=frozenset(b.uuids()))
    export = export_delta(tmp_path / 'thin.aiida', delta=delta, backend=a.backend, want=set(delta.uuids) - b.uuids())

    result = b.run_verdi(import_archive, [str(export.filepath)], raises=True)

    assert 'collab transfer delta' in result.output
    assert 'verdi collab pull' in result.output


def test_a_thin_import_and_a_full_one_produce_the_same_graph(collab):
    """Test the invariant the thin delta rests on: leaving held ancestors off the wire changes nothing.

    Bob receives the second generation alone, with its link to the first crossing the boundary as a UUID
    quadruple; Carol receives the whole closure in one archive. Both must end up with Alice's graph exactly, and
    Bob must have paid less for it — which is the whole reason the thin delta exists.

    Run as pulls only: what is compared is two receivers of the same provenance, and the route it took is what
    the tests above vary.
    """
    a, b, c = collab(3)
    # Incompressible ballast on the first generation, so that "did the ancestors travel" is visible in the size.
    first = a.seal_calculation(ballast=200_000)

    b.run('pull', ['alice', '--force'])

    a.seal_calculation(inputs=first)

    b.run('pull', ['alice', '--force'])
    c.run('pull', ['alice', '--force'])

    assert b.graph() == a.graph()
    assert c.graph() == a.graph()
    assert b.state().events[-1].size < c.state().events[-1].size
