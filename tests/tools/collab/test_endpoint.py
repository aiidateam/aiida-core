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


@pytest.fixture
def record_calls(monkeypatch):
    """Record circus commands and the import in order, the import succeeding unless given an error."""
    calls = []

    def factory(import_error=None):
        def import_delta(filepath, **kwargs):
            calls.append('import')

            if import_error is not None:
                raise RuntimeError(import_error)

            return DeltaReport(uuids=[], size=0)

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
    assert report == {'uuids': [], 'size': 0}


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

    with pytest.raises(PermissionError, match='collab.accept_push'):
        endpoint.import_staged(tmp_path / 'staged', 'http://pusher:9137', timezone.now())

    assert calls == []


def test_accept_push_is_read_per_request(make_profile, empty_config, record_calls, tmp_path):
    """Test that withdrawing consent to be pushed to holds from the next request, without a daemon restart.

    The endpoint of a running daemon holds the configuration it loaded at startup, so both the handshake it
    serves and the import it would run have to go back to the file.
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

    with pytest.raises(PermissionError, match='collab.accept_push'):
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


def test_handshake(make_profile):
    """Test that the handshake serves the cursor of the requester and claims the nodes it holds."""
    profile = make_profile()
    endpoint = CollabEndpoint(profile, backend=MagicMock())

    cursor = timezone.now()
    state = CollabState(filepath=CollabState.get_filepath(profile))
    state.cursors['http://pusher:9137'] = cursor
    state.events.append(
        CollabEvent(time=timezone.now(), direction='pull', peer='http://other:9137', uuids=['uuid-held'], size=1)
    )
    state.save()

    handshake = endpoint.handshake('http://pusher:9137')

    assert handshake.busy is False
    assert handshake.cursor == cursor
    assert handshake.claim == ['uuid-held']

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
        return DeltaReport(uuids=[], size=0)

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
