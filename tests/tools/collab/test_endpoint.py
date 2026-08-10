###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the daemon integration of the collab endpoint."""

import threading
import time
from unittest.mock import MagicMock

import pytest

from aiida import orm
from aiida.common import timezone
from aiida.engine.daemon.client import DaemonClient
from aiida.storage.sqlite_temp import SqliteTempBackend
from aiida.tools.collab import endpoint as endpoint_module
from aiida.tools.collab.endpoint import CollabEndpoint
from aiida.tools.collab.protocol import PushRefused
from aiida.tools.collab.state import CollabEvent, CollabState, import_lock
from aiida.tools.collab.sync import DeltaReport


@pytest.fixture
def make_profile(empty_config, profile_factory):
    """Return a factory creating a profile registered in the temporary config."""

    def factory(**kwargs):
        profile = profile_factory('collab-profile', **kwargs)
        empty_config.add_profile(profile)
        # Pushes are opt-in; what the endpoint tests are about is what happens once a profile accepts them.
        empty_config.set_option('collab.accept_push', True, scope=profile.name)
        # Stored, because the endpoint reads consent to be pushed to from the file on every request.
        empty_config.store()
        return profile

    return factory


def test_create_watchers_with_collab(make_profile, empty_config):
    """Test that the daemon watcher list contains the collab endpoint when ``collab.enabled`` is set."""
    profile = make_profile()
    empty_config.set_option('collab.enabled', True, scope=profile.name)
    client = DaemonClient(profile)

    names = [watcher['name'] for watcher in client._create_watchers(1)]

    assert names.count(f'{client.daemon_name}-collab-endpoint') == 1


def test_create_watchers_without_collab(make_profile):
    """Test that the daemon watcher list has no collab endpoint when the profile is not part of a collab."""
    profile = make_profile()
    client = DaemonClient(profile)

    names = [watcher['name'] for watcher in client._create_watchers(1)]

    assert f'{client.daemon_name}-collab-endpoint' not in names


@pytest.fixture
def record_calls(monkeypatch):
    """Record circus commands and the import in order, the import succeeding unless given an error."""
    calls = []

    def factory(import_error=None):
        def import_delta(filepath, **kwargs):
            calls.append('import')

            if import_error is not None:
                raise RuntimeError(import_error)

            return DeltaReport(uuids=[], skipped=[], size=0)

        monkeypatch.setattr(DaemonClient, 'call_client', lambda self, command: calls.append(command) or {})
        monkeypatch.setattr(endpoint_module, 'import_delta', import_delta)

        return calls

    return factory


def circus_command(command, profile):
    return {'command': command, 'properties': {'name': f'aiida-{profile.name}', 'waiting': True}}


def test_import_staged_pauses_workers_on_sqlite(make_profile, record_calls, tmp_path):
    """Test that an import on SQLite storage stops the worker watcher first and restarts it after."""
    profile = make_profile(storage_backend='core.sqlite_dos')
    calls = record_calls()

    endpoint = CollabEndpoint(profile, backend=MagicMock())
    report = endpoint.import_staged(tmp_path / 'staged', 'http://pusher:9137', timezone.now())

    assert calls == [circus_command('stop', profile), 'import', circus_command('start', profile)]
    assert report == {'uuids': [], 'skipped': [], 'size': 0, 'refreshed': [], 'members': []}


def test_import_staged_restarts_workers_on_failure(make_profile, record_calls, tmp_path):
    """Test that the workers are restarted even when the import raises."""
    profile = make_profile(storage_backend='core.sqlite_dos')
    calls = record_calls(import_error='the import failed')

    endpoint = CollabEndpoint(profile, backend=MagicMock())

    with pytest.raises(RuntimeError, match='the import failed'):
        endpoint.import_staged(tmp_path / 'staged', 'http://pusher:9137', timezone.now())

    assert calls == [circus_command('stop', profile), 'import', circus_command('start', profile)]


def test_import_staged_no_pause_on_postgresql(make_profile, record_calls, tmp_path):
    """Test that an import on PostgreSQL storage issues no circus commands at all."""
    profile = make_profile(storage_backend='core.psql_dos')
    calls = record_calls()

    endpoint = CollabEndpoint(profile, backend=MagicMock())
    endpoint.import_staged(tmp_path / 'staged', 'http://pusher:9137', timezone.now())

    assert calls == ['import']


def test_import_staged_refused_unless_accepted(make_profile, empty_config, record_calls, tmp_path):
    """Test that a push is refused, before touching the workers, unless the profile opted in to accepting them."""
    profile = make_profile(storage_backend='core.sqlite_dos')
    # Back to the schema default, which is what a profile that never opted in has.
    empty_config.unset_option('collab.accept_push', scope=profile.name)
    empty_config.store()
    calls = record_calls()

    endpoint = CollabEndpoint(profile, backend=MagicMock())

    with pytest.raises(PushRefused, match='collab.accept_push'):
        endpoint.import_staged(tmp_path / 'staged', 'http://pusher:9137', timezone.now())

    assert calls == []


def test_accept_push_is_read_per_request(make_profile, empty_config, record_calls, tmp_path):
    """Test that withdrawing consent to be pushed to holds from the next request, without a daemon restart.

    The endpoint of a running daemon holds the configuration it loaded at startup, so the handshake it serves, the
    push it would admit and the import it would run all have to go back to the file.
    """
    from aiida.manage.configuration.config import Config
    from aiida.tools.collab.endpoint import local_info

    profile = make_profile(storage_backend='core.sqlite_dos')
    record_calls()
    endpoint = CollabEndpoint(profile, backend=MagicMock())

    assert local_info(profile, MagicMock()).accept_push is True

    # Withdrawn through a second handle on the file, which is what `verdi config unset` in another shell amounts
    # to: the configuration this process loaded still says yes, so only a read of the file can see the no.
    withdrawn = Config.from_file(empty_config.filepath)
    withdrawn.unset_option('collab.accept_push', scope=profile.name)
    withdrawn.store()

    assert empty_config.get_option('collab.accept_push', scope=profile.name) is True, 'the staging is stale'
    assert local_info(profile, MagicMock()).accept_push is False, 'the handshake must stop inviting pushes'

    with pytest.raises(PushRefused, match='collab.accept_push'):
        endpoint.handshake('http://pusher:9137')

    with pytest.raises(PushRefused, match='collab.accept_push'):
        endpoint.import_staged(tmp_path / 'staged', 'http://pusher:9137', timezone.now())


def seal_calculation(backend):
    calculation = orm.CalcJobNode(backend=backend).store()
    calculation.seal()


@pytest.fixture
def temp_backend(tmp_path):
    backend = SqliteTempBackend(SqliteTempBackend.create_profile(filepath=str(tmp_path / 'storage')))
    yield backend
    backend.close()


def test_negotiate_delta_cached(make_profile, temp_backend):
    """Test that a delta is computed and cut once while nothing changed, and afresh after a new seal."""
    profile = make_profile()
    seal_calculation(temp_backend)
    endpoint = CollabEndpoint(profile, temp_backend)

    manifest = endpoint.negotiate_delta(None, frozenset())

    assert endpoint.negotiate_delta(None, frozenset()) == manifest

    offer = endpoint.request_delta(None, frozenset(), frozenset(manifest.manifest))
    filepath = endpoint.resolve_delta(offer.delta)

    assert endpoint.request_delta(None, frozenset(), frozenset(manifest.manifest)) == offer
    assert endpoint.resolve_delta(offer.delta) == filepath

    seal_calculation(temp_backend)
    fresh = endpoint.negotiate_delta(None, frozenset())

    assert fresh.instant > manifest.instant
    assert len(fresh.manifest) > len(manifest.manifest)

    # The same request now cuts from the fresh computation: same identifier, new file.
    refreshed = endpoint.request_delta(None, frozenset(), frozenset(manifest.manifest))

    assert refreshed.delta == offer.delta, 'the identifier derives from the request, which did not change'
    assert refreshed.instant == fresh.instant
    assert endpoint.resolve_delta(offer.delta) != filepath
    assert not filepath.exists(), 'the superseded delta should have been removed'


def test_negotiate_delta_per_requester(make_profile, temp_backend):
    """Test that requesters presenting different cursors are served their own deltas, cached side by side."""
    profile = make_profile()
    seal_calculation(temp_backend)
    endpoint = CollabEndpoint(profile, temp_backend)

    # One cursor per requester, reused between its negotiation and its request, as the client does.
    cursor = timezone.now()
    everything = endpoint.negotiate_delta(None, frozenset())
    nothing = endpoint.negotiate_delta(cursor, frozenset())

    assert everything.manifest
    assert nothing.manifest == []

    offer_all = endpoint.request_delta(None, frozenset(), frozenset(everything.manifest))
    offer_none = endpoint.request_delta(cursor, frozenset(), frozenset())

    assert offer_all.delta != offer_none.delta
    assert offer_all.size > offer_none.size, 'one requester is owed a calculation, the other nothing'
    assert endpoint.resolve_delta(offer_all.delta).exists()
    assert endpoint.resolve_delta(offer_none.delta).exists()
    assert endpoint.resolve_delta('0' * 64) is None


def test_negotiate_delta_refresh_only_under_sync(make_profile, empty_config, temp_backend):
    """Test that the manifest offers the mtimes of edited extras only when the collab syncs extras."""
    profile = make_profile()
    cursor = timezone.now()
    seal_calculation(temp_backend)

    assert CollabEndpoint(profile, temp_backend).negotiate_delta(cursor, frozenset()).refresh == {}

    empty_config.set_option('collab.policy', {'extras_mode': 'sync', 'groups_mode': 'local'}, scope=profile.name)

    assert CollabEndpoint(profile, temp_backend).negotiate_delta(cursor, frozenset()).refresh


def test_request_delta_groups_only_under_grow(make_profile, empty_config, temp_backend):
    """Test that the delta the daemon serves carries groups only when the collab grows them.

    The endpoint is the only path that delivers a pull, so it is the only place where the groups policy of a
    served delta can be observed.
    """
    from aiida.tools.collab.protocol import member_pairs
    from aiida.tools.collab.sync import _archive_contents

    profile = make_profile()
    seal_calculation(temp_backend)
    orm.Group(label='curated', backend=temp_backend).store().add_nodes(
        orm.QueryBuilder(backend=temp_backend).append(orm.CalcJobNode).all(flat=True)
    )

    def served() -> list:
        endpoint = CollabEndpoint(profile, temp_backend)
        manifest = endpoint.negotiate_delta(None, frozenset())
        offer = endpoint.request_delta(None, frozenset(), frozenset(manifest.manifest))

        return member_pairs(_archive_contents(endpoint.resolve_delta(offer.delta))[1])

    assert served() == []

    empty_config.set_option('collab.policy', {'extras_mode': 'local', 'groups_mode': 'grow'}, scope=profile.name)

    assert served(), 'the endpoint must serve group memberships once the collab grows groups'


def test_slots_cap_and_expiry(make_profile, monkeypatch):
    """Test that sessions beyond ``collab.max_concurrency`` answer busy, until a stale slot expires."""
    from types import SimpleNamespace

    from aiida.tools.collab.protocol import EndpointBusy

    profile = make_profile()
    endpoint = CollabEndpoint(profile, backend=MagicMock())

    assert endpoint.handshake('pusher-one').busy is False
    assert endpoint.handshake('pusher-one').busy is False, 'refreshing an own slot is never refused'
    assert endpoint.handshake('pusher-two').busy is False
    assert endpoint.handshake('pusher-three').busy is True

    with pytest.raises(EndpointBusy):
        endpoint.negotiate_delta(None, frozenset())

    now = time.monotonic()
    monkeypatch.setattr(
        endpoint_module, 'time', SimpleNamespace(monotonic=lambda: now + endpoint_module.SLOT_IDLE_SECONDS + 1)
    )

    assert endpoint.handshake('pusher-three').busy is False, 'the slots of the silent holders should have expired'


def test_slot_released_after_import(make_profile, record_calls, tmp_path):
    """Test that a pusher's slot is freed when its import commits, admitting the next pusher."""
    profile = make_profile(storage_backend='core.psql_dos')
    record_calls()
    endpoint = CollabEndpoint(profile, backend=MagicMock())

    assert endpoint.handshake('pusher-one').busy is False
    assert endpoint.handshake('pusher-two').busy is False
    assert endpoint.handshake('pusher-three').busy is True

    endpoint.import_staged(tmp_path / 'staged', 'pusher-one', timezone.now())

    assert endpoint.handshake('pusher-three').busy is False


def test_slot_released_when_a_negotiation_ends(make_profile, temp_backend):
    """Test that ending a negotiation frees its slot, whether or not anything was ever exported.

    A dry run negotiates and stops there. Until the end could be signalled, only an export registered a slot that
    could be given back, so two dry runs left the endpoint answering everybody else busy until they expired.
    """
    profile = make_profile()
    endpoint = CollabEndpoint(profile, temp_backend)

    endpoint.negotiate_delta(None, frozenset(), requester='puller-one')
    endpoint.release('puller-one')
    endpoint.negotiate_delta(None, frozenset(), requester='puller-two')
    endpoint.release('puller-two')

    # `collab.max_concurrency` is 2, so this is refused unless both ended negotiations gave their slot back.
    endpoint.negotiate_delta(None, frozenset(), requester='puller-three')


def test_slots_are_held_per_peer_not_per_request(make_profile, temp_backend):
    """Test that two peers presenting the same cursor and claim hold a slot each, and neither frees the other's.

    Every newcomer of a collab presents the same empty cursor and claim: keyed by the request, two of them
    counted as one session against the cap, and whichever ended first freed the slot the other was served under.
    """
    from aiida.tools.collab.protocol import EndpointBusy

    profile = make_profile()
    endpoint = CollabEndpoint(profile, temp_backend)

    endpoint.negotiate_delta(None, frozenset(), requester='puller-one')
    endpoint.negotiate_delta(None, frozenset(), requester='puller-two')

    with pytest.raises(EndpointBusy):
        endpoint.negotiate_delta(None, frozenset(), requester='puller-three')

    endpoint.release('puller-one')
    endpoint.negotiate_delta(None, frozenset(), requester='puller-three')

    with pytest.raises(EndpointBusy):
        # Only the peer that ended gave a slot back; the one still being served kept its own.
        endpoint.negotiate_delta(None, frozenset(), requester='puller-four')


def test_join_records_the_newcomer_and_answers_with_the_membership(make_profile, empty_config):
    """Test that admitting a newcomer stores it and hands it everyone this profile knows, itself included.

    The roster is written to the configuration file rather than to the daemon's own copy of it: that copy is a
    snapshot from the moment the daemon started, and storing it wholesale would undo everything ``verdi`` wrote
    since.
    """
    from aiida.manage.configuration.config import Config

    profile = make_profile()
    alice = {
        'url': 'http://100.64.0.2:9137',
        'nickname': 'alice',
        'name': 'alice',
        'stamp': 1,
        'seen': True,
        'active': True,
        'signalled': False,
    }

    empty_config.set_option('collab.uuid', 'uuid-of-the-collab', scope=profile.name)
    empty_config.set_option('collab.bind', '127.0.0.1', scope=profile.name)
    empty_config.set_option('collab.port', 9137, scope=profile.name)
    empty_config.set_option('collab.peers', {'uuid-of-alice': alice}, scope=profile.name)
    empty_config.store()

    endpoint = CollabEndpoint(profile, backend=MagicMock())
    newcomer = {'uuid': 'uuid-of-carol', 'url': 'http://100.64.0.3:9137', 'name': 'carol', 'stamp': 1}

    response = endpoint.join(newcomer)

    assert response.collab == 'uuid-of-the-collab'
    assert {entry['uuid'] for entry in response.roster} == {profile.uuid, 'uuid-of-alice', 'uuid-of-carol'}

    stored = Config.from_file(empty_config.filepath).get_option('collab.peers', scope=profile.name)

    assert stored['uuid-of-carol'] == {
        'url': 'http://100.64.0.3:9137',
        'nickname': 'carol',
        'name': 'carol',
        'stamp': 1,
        'seen': False,
        'active': True,
        'signalled': False,
    }
    assert stored['uuid-of-alice'] == alice


def test_handshake_merges_the_gossiped_roster(make_profile, empty_config):
    """Test that a peer's own announcement corrects the address held for it, on the served side too.

    The endpoint is how a moved member reaches a peer whose daemon is the only thing running there, so the merge
    has to happen here as much as in the ``verdi`` commands.
    """
    from aiida.manage.configuration.config import Config

    profile = make_profile()
    empty_config.set_option(
        'collab.peers',
        {
            'uuid-of-alice': {
                'url': 'http://old:9137',
                'nickname': 'alice',
                'name': 'alice',
                'stamp': 1,
                'seen': True,
                'active': True,
                'signalled': False,
            }
        },
        scope=profile.name,
    )
    empty_config.store()

    endpoint = CollabEndpoint(profile, backend=MagicMock())
    moved = {'uuid': 'uuid-of-alice', 'url': 'http://100.64.0.9:9137', 'name': 'alice', 'stamp': 2}

    handshake = endpoint.handshake('uuid-of-alice', [moved])

    stored = Config.from_file(empty_config.filepath).get_option('collab.peers', scope=profile.name)

    assert stored['uuid-of-alice']['url'] == 'http://100.64.0.9:9137'
    assert stored['uuid-of-alice']['seen'] is False, 'the new address is unproven until the peer answers at it'
    assert {entry['uuid'] for entry in handshake.roster} == {profile.uuid, 'uuid-of-alice'}


def dormant(nickname, url):
    """Return a roster entry of a member that has not been seen under the current token."""
    return {
        'url': url,
        'nickname': nickname,
        'name': nickname,
        'stamp': 1,
        'seen': True,
        'active': False,
        'signalled': False,
    }


def test_handshake_reactivates_the_returning_peer_and_leaves_the_others_dormant(make_profile, empty_config):
    """Test the inbound half of recognition: whoever contacts under the current token is active again.

    This is the only way a rekeyed member comes back — nobody polls a dormant peer — and it must reach exactly
    that member: the peers it gossips along are vouched for, the ones it says nothing about stay dormant.
    """
    from aiida.manage.configuration.config import Config

    profile = make_profile()
    empty_config.set_option(
        'collab.peers',
        {
            'uuid-of-alice': dormant('alice', 'http://100.64.0.2:9137'),
            'uuid-of-bob': dormant('bob', 'http://100.64.0.3:9137'),
        },
        scope=profile.name,
    )
    empty_config.store()

    endpoint = CollabEndpoint(profile, backend=MagicMock())
    returning = {'uuid': 'uuid-of-alice', 'url': 'http://100.64.0.2:9137', 'name': 'alice', 'stamp': 1}

    handshake = endpoint.handshake('uuid-of-alice', [returning])

    peers = Config.from_file(empty_config.filepath).get_option('collab.peers', scope=profile.name)

    assert peers['uuid-of-alice']['active'] is True
    assert peers['uuid-of-bob']['active'] is False
    assert {entry['uuid'] for entry in handshake.roster} == {profile.uuid, 'uuid-of-alice'}, (
        'a dormant peer is never gossiped: vouching for it would undo the rotation everywhere'
    )


def test_retired_records_the_signal_and_nothing_else(make_profile, empty_config):
    """Test that the rotation signal is recorded against its sender and changes nothing else.

    Acting on it is what must not happen: it is authenticated by the token being retired, which an excluded
    member holds too, so anything automatic would let that member paralyse the collab by sending it.
    """
    from aiida.manage.configuration.config import Config

    profile = make_profile()
    alice = {'url': 'http://100.64.0.2:9137', 'nickname': 'alice', 'name': 'alice', 'stamp': 1, 'seen': True}
    bob = dormant('bob', 'http://100.64.0.3:9137')
    empty_config.set_option(
        'collab.peers',
        {'uuid-of-alice': {**alice, 'active': True, 'signalled': False}, 'uuid-of-bob': bob},
        scope=profile.name,
    )
    empty_config.set_option('collab.token', 'the-token', scope=profile.name)
    empty_config.store()

    endpoint = CollabEndpoint(profile, backend=MagicMock())

    endpoint.retired('uuid-of-alice')
    # Neither a member this roster does not know nor one it holds dormant has anywhere to be shown, since
    # `verdi status` is the active list and nothing else.
    endpoint.retired('uuid-of-a-stranger')
    endpoint.retired('uuid-of-bob')

    stored = Config.from_file(empty_config.filepath)
    peers = stored.get_option('collab.peers', scope=profile.name)

    assert peers == {'uuid-of-alice': {**alice, 'active': True, 'signalled': True}, 'uuid-of-bob': bob}
    assert stored.get_option('collab.token', scope=profile.name) == 'the-token', 'the signal is advisory only'


def test_serve_carries_the_collab_and_its_roster(empty_config, tmp_path, monkeypatch):
    """Test the seam between client, server and endpoint, through the wiring the daemon itself starts.

    Every layer is tested apart from the others: the merge as a unit, the endpoint called directly, the commands
    with the client stubbed, the server with a stubbed core. This is the test that fails if the roster stops
    crossing the wire, if the endpoint stops admitting newcomers, or if the handshake stops naming the collab —
    none of which any of those can see.
    """
    import socket
    import threading
    from http import HTTPStatus

    from aiida.manage.configuration.config import Config
    from aiida.manage.configuration.profile import Profile
    from aiida.storage.sqlite_dos.backend import SqliteDosStorage
    from aiida.tools.collab import server as server_module
    from aiida.tools.collab.client import CollabClient
    from aiida.tools.collab.endpoint import serve
    from aiida.tools.collab.protocol import CollabRequestError

    collab, token = 'uuid-of-the-collab', 'the-token'

    # A file-backed storage, since the handshake is answered from the server's own handler thread and an
    # in-memory SQLite is not the same database there.
    profile = Profile(
        'collab-profile',
        {
            'default_user_email': 'dummy@localhost',
            'storage': {'backend': 'core.sqlite_dos', 'config': {'filepath': str(tmp_path / 'served-storage')}},
            'process_control': {'backend': None, 'config': {}},
            'test_profile': True,
        },
    )
    empty_config.add_profile(profile)
    SqliteDosStorage.initialise(profile)
    backend = SqliteDosStorage(profile)

    # `serve` takes the port from the configuration, so one is reserved here to know where to knock.
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]

    options = {
        'collab.enabled': True,
        'collab.accept_push': True,
        'collab.uuid': collab,
        'collab.token': token,
        'collab.bind': '127.0.0.1',
        'collab.port': port,
        'collab.peers': {
            'uuid-of-alice': {
                'url': 'http://old:9137',
                'nickname': 'alice',
                'name': 'alice',
                'stamp': 1,
                'seen': True,
                'active': True,
                'signalled': False,
            }
        },
    }

    for option, value in options.items():
        empty_config.set_option(option, value, scope=profile.name)

    empty_config.store()

    started = threading.Event()
    servers = []
    build = server_module.CollabServer

    def capture(*args, **kwargs):
        """Keep the server `serve` builds, which is the only handle on it, without touching how it is built."""
        servers.append(build(*args, **kwargs))
        started.set()

        return servers[-1]

    monkeypatch.setattr(server_module, 'CollabServer', capture)

    thread = threading.Thread(target=serve, args=(profile, backend), daemon=True)
    thread.start()

    assert started.wait(timeout=30), 'the endpoint never started'

    try:
        with CollabClient(f'http://127.0.0.1:{port}', token, collab=collab, timeout=30) as client:
            assert client.info().collab == collab, 'a peer that does not name its collab is refused by every peer'

            newcomer = {'uuid': 'uuid-of-carol', 'url': 'http://100.64.0.3:9137', 'name': 'carol', 'stamp': 1}
            response = client.join(newcomer)

            assert response.collab == collab
            assert {entry['uuid'] for entry in response.roster} == {profile.uuid, 'uuid-of-alice', 'uuid-of-carol'}

            mine = next(entry for entry in response.roster if entry['uuid'] == profile.uuid)

            assert mine == {
                'uuid': profile.uuid,
                'url': f'http://127.0.0.1:{port}',
                'name': profile.name,
                'stamp': 0,
            }, 'the address a newcomer adopts for this profile is the one its endpoint is serving on'

            # Alice announces that she moved; the raised stamp is what makes it supersede the address held here.
            moved = [{'uuid': 'uuid-of-alice', 'url': 'http://100.64.0.9:9137', 'name': 'alice', 'stamp': 2}]
            handshake = client.push_handshake('uuid-of-carol', moved)

            assert {entry['uuid'] for entry in handshake.roster} == {profile.uuid, 'uuid-of-alice', 'uuid-of-carol'}

            manifest = client.negotiate_delta(
                None, frozenset(), [dict(newcomer, url='http://100.64.0.4:9137', stamp=2)]
            )

            assert {entry['uuid'] for entry in manifest.roster} == {profile.uuid, 'uuid-of-alice', 'uuid-of-carol'}

            # A rotation runs in another process — `verdi collab rotate` — and reaches the endpoint through the
            # configuration file alone. The old token has to stop working from the next request on: this is the
            # whole enforcement of a rotation, and a restart nobody is told to run would leave the member that
            # was excluded reading in the meantime.
            rotating = Config.from_file(empty_config.filepath)
            rotating.set_option('collab.token', 'the-rotated-token', scope=profile.name)
            rotating.store()

            with pytest.raises(CollabRequestError) as excinfo:
                client.info()

            assert excinfo.value.status == HTTPStatus.UNAUTHORIZED
            assert 'verdi collab rekey' in str(excinfo.value)
    finally:
        servers[0].shutdown()
        servers[0].server_close()
        thread.join()
        backend.close()

    peers = Config.from_file(empty_config.filepath).get_option('collab.peers', scope=profile.name)

    assert peers['uuid-of-carol']['url'] == 'http://100.64.0.4:9137', 'the last announcement of the newcomer wins'
    assert peers['uuid-of-alice']['url'] == 'http://100.64.0.9:9137'


def test_handshake(make_profile):
    """Test that the handshake serves the cursor of the requester and claims held nodes and tombstones."""
    profile = make_profile()
    endpoint = CollabEndpoint(profile, backend=MagicMock())

    cursor = timezone.now()
    state = CollabState(filepath=CollabState.get_filepath(profile))
    state.cursors['http://pusher:9137'] = cursor
    state.tombstones.add('uuid-deleted')
    state.events.append(
        CollabEvent(time=timezone.now(), direction='pull', peer='http://other:9137', uuids=['uuid-held'], size=1)
    )
    state.save()

    handshake = endpoint.handshake('http://pusher:9137')

    assert handshake.busy is False
    assert handshake.cursor == cursor
    assert handshake.claim == ['uuid-deleted', 'uuid-held']

    assert endpoint.handshake('http://unknown:9137').cursor is None


def test_handshake_busy_while_importing(make_profile):
    """Test that the handshake answers busy exactly while the import lock of the profile is held."""
    profile = make_profile()
    endpoint = CollabEndpoint(profile, backend=MagicMock())
    acquired, release = threading.Event(), threading.Event()

    def hold():
        with import_lock(CollabState.get_filepath(profile)):
            acquired.set()
            release.wait(timeout=30)

    thread = threading.Thread(target=hold)
    thread.start()
    acquired.wait(timeout=30)

    try:
        assert endpoint.handshake('http://pusher:9137').busy is True
    finally:
        release.set()
        thread.join()

    assert endpoint.handshake('http://pusher:9137').busy is False


def test_concurrent_imports_serialize(make_profile, monkeypatch, tmp_path):
    """Test that two pushes imported at the same time run strictly one after the other."""
    profile = make_profile(storage_backend='core.psql_dos')
    intervals = []

    def slow_import(filepath, **kwargs):
        start = time.monotonic()
        time.sleep(0.2)
        intervals.append((start, time.monotonic()))
        return DeltaReport(uuids=[], skipped=[], size=0)

    monkeypatch.setattr(endpoint_module, 'import_delta', slow_import)
    endpoint = CollabEndpoint(profile, backend=MagicMock())

    threads = [
        threading.Thread(target=endpoint.import_staged, args=(tmp_path / 'staged', f'http://{name}', timezone.now()))
        for name in ('one', 'two')
    ]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    (_, first_end), (second_start, _) = sorted(intervals)

    assert second_start >= first_end, 'the imports interleaved'
