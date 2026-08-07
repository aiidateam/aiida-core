###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The collab endpoint of a profile: the transport server wired to the sync core.

The daemon supervises this as a circus watcher of its own (see ``DaemonClient._create_watchers``), started through
the hidden ``verdi daemon collab-endpoint`` command when ``collab.enabled`` is set on the profile.
"""

from __future__ import annotations

import dataclasses
import threading
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from aiida import __version__
from aiida.common.log import AIIDA_LOGGER
from aiida.tools.archive.abstract import get_format
from aiida.tools.collab.config import (
    OPTION_ACCEPT_PUSH,
    OPTION_BIND,
    OPTION_PEERS,
    OPTION_POLICY,
    OPTION_PORT,
    OPTION_TOKEN,
    OPTION_UUID,
    merge_roster,
    roster_entries,
    self_entry,
    stored_config,
)
from aiida.tools.collab.protocol import (
    DeltaManifest,
    DeltaOffer,
    JoinResponse,
    ManifestDiff,
    PeerInfo,
    PushHandshake,
    delta_id,
)
from aiida.tools.collab.state import CollabState, import_lock, import_lock_held
from aiida.tools.collab.sync import Delta, compute_delta, count_seeds, export_delta, import_delta, missing_uuids

if TYPE_CHECKING:
    from collections.abc import Iterator
    from datetime import datetime
    from pathlib import Path

    from aiida.manage.configuration import Profile
    from aiida.orm.implementation import StorageBackend
    from aiida.tools.collab.sync import DeltaExport

LOGGER = AIIDA_LOGGER.getChild('collab')

# Deltas stay cached while their requester retries an interrupted download; anything beyond a few concurrent
# requesters is stale cursors accumulating, not live transfers.
MAX_CACHED_DELTAS = 8


def local_info(profile: Profile, backend: StorageBackend, cursor: datetime | None = None) -> PeerInfo:
    """Build the handshake of ``profile``: what a peer contacting its endpoint is told.

    :param cursor: the cursor the contacting peer holds for this profile; the pending count estimates what a sync
        bounded by it would deliver.
    """
    from aiida.manage.configuration import get_config

    config = get_config()
    state = CollabState.load(profile)
    # Read from the file rather than from what this process loaded: a daemon serving the endpoint loaded its
    # configuration at startup, and withdrawing consent to be pushed to has to hold from the next request on.
    accept_push = stored_config(config).get_option(OPTION_ACCEPT_PUSH, scope=profile.name)
    policy = config.get_option(OPTION_POLICY, scope=profile.name)

    return PeerInfo(
        version=__version__,
        backend=profile.storage_backend,
        storage_schema=profile.storage_cls.version_head(),
        archive_schema=get_format().latest_version,
        pending_count=count_seeds(cursor, backend) + len(state.imported_uuids_since(cursor)),
        accept_push=accept_push,
        extras_mode=policy['extras_mode'],
        groups_mode=policy['groups_mode'],
        uuid=profile.uuid,
        collab=config.get_option(OPTION_UUID, scope=profile.name),
    )


@contextmanager
def workers_stopped(profile: Profile) -> Iterator[None]:
    """Stop the daemon workers of the profile for the duration, on storage that cannot take a second writer.

    SQLite locks the whole database for a write, so an import holding the lock for minutes and the workers
    starve each other. PostgreSQL takes concurrent writers and nothing is stopped.
    """
    from aiida.engine.daemon.client import DaemonClient

    if 'sqlite' not in profile.storage_backend:
        yield
        return

    client = DaemonClient(profile)
    client.call_client({'command': 'stop', 'properties': {'name': client.daemon_name, 'waiting': True}})

    try:
        yield
    finally:
        client.call_client({'command': 'start', 'properties': {'name': client.daemon_name, 'waiting': True}})


class CollabEndpoint:
    """The callables behind the routes of the ``CollabServer`` of a profile."""

    def __init__(self, profile: Profile, backend: StorageBackend):
        self._profile = profile
        self._backend = backend
        self._dirpath = CollabState.get_workdir(profile)
        self._state_filepath = CollabState.get_filepath(profile)
        self._computed: dict[str, Delta] = {}
        self._deltas: dict[str, DeltaExport] = {}
        self._delta_lock = threading.Lock()
        self._counter = 0
        self._roster_lock = threading.Lock()

        self._dirpath.mkdir(parents=True, exist_ok=True)

        # Deltas of a previous run of the endpoint: nothing tracks them anymore.
        for stale in self._dirpath.glob('delta-*.aiida'):
            stale.unlink()

    @property
    def staging_dir(self) -> Path:
        """The directory in which the server stages the uploads of pushing peers."""
        return self._dirpath / 'staging'

    def info(self, cursor: datetime | None = None) -> PeerInfo:
        """Serve the handshake of this profile."""
        return local_info(self._profile, self._backend, cursor)

    def join(self, entry: dict[str, Any]) -> JoinResponse:
        """Admit a newcomer presenting the join code: record it and hand it the membership of the collab.

        Only a token holder reaches this, and the newcomer's profile UUID is pinned by the very entry it is added
        under, so the admission needs no further ceremony.
        """
        from aiida.manage.configuration import get_config

        peers = self._merge_roster([entry])

        return JoinResponse(
            collab=get_config().get_option(OPTION_UUID, scope=self._profile.name), roster=self._entries(peers)
        )

    def handshake(self, requester: str, roster: list[dict[str, Any]] | None = None) -> PushHandshake:
        """Answer a peer that wants to push: busy while an import is running, else what this profile holds of it.

        Answering busy before anything is exported or uploaded is what serializes concurrent fan-in: the retrying
        pusher negotiates against the post-import cursor and claim, so no redundant bytes travel.
        """
        entries = self._entries(self._merge_roster(roster or []))

        if import_lock_held(self._state_filepath):
            return PushHandshake(busy=True, cursor=None, claim=[], roster=entries)

        state = CollabState.read(self._state_filepath)
        cursor = state.cursors.get(requester)

        return PushHandshake(
            busy=False,
            cursor=cursor,
            claim=sorted(state.imported_uuids_since(cursor)),
            roster=entries,
        )

    def _merge_roster(self, entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Merge gossiped roster entries into the configuration and return the resulting roster."""
        from aiida.manage.configuration import get_config

        if not entries:
            return get_config().get_option(OPTION_PEERS, scope=self._profile.name)

        with self._roster_lock:
            config = stored_config(get_config())
            peers = config.get_option(OPTION_PEERS, scope=self._profile.name)
            merged, reports = merge_roster(peers, entries, self._profile.uuid)

            if merged != peers:
                config.set_option(OPTION_PEERS, merged, scope=self._profile.name)
                config.store()

                for report in reports:
                    LOGGER.report(report)

            return merged

    def _entries(self, peers: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        """Return what this profile gossips back: its own entry and every peer it knows.

        The endpoint never raises its own stamp: only an outbound sync does, which is what the member whose
        address changed runs to spread the correction.
        """
        from aiida.manage.configuration import get_config

        return roster_entries(peers, self_entry(get_config(), self._profile))

    def negotiate_delta(
        self, cursor: datetime | None, claim: frozenset[str], roster: list[dict[str, Any]] | None = None
    ) -> DeltaManifest:
        """Serve the manifest of the delta for a presented cursor and claim: which nodes it holds.

        No archive is built for this — the requester first diffs the manifest against its own nodes and then
        requests only the subset it lacks.
        """
        entries = self._entries(self._merge_roster(roster or []))

        with self._delta_lock:
            delta = self._delta(cursor, claim)

            return DeltaManifest(manifest=delta.uuids, instant=delta.instant, roster=entries)

    def request_delta(self, cursor: datetime | None, claim: frozenset[str], want: frozenset[str]) -> DeltaOffer:
        """Export the requested subset of a delta, reusing the cached archive while nothing changed.

        The transport requires an identifier to keep resolving to the same bytes while a transfer is in progress,
        so a re-export goes to a fresh path: a client still streaming the previous file keeps its open handle on
        the unlinked inode, and one that resumes later is served the new file from the start by the ``ETag``
        validator.
        """
        with self._delta_lock:
            delta = self._delta(cursor, claim)
            key = delta_id(cursor, claim, want)
            cached = self._deltas.pop(key, None)

            # An archive built from a superseded computation of the delta serves stale bytes: the instant ties
            # the archive to the computation it was cut from.
            if cached is None or cached.instant != delta.instant:
                self._counter += 1

                if cached is not None:
                    cached.filepath.unlink(missing_ok=True)

                cached = export_delta(
                    self._dirpath / f'delta-{self._counter}.aiida',
                    delta=delta,
                    backend=self._backend,
                    want=want,
                )

            # Re-inserted last, so the cache evicts in order of least recent use.
            self._deltas[key] = cached

            while len(self._deltas) > MAX_CACHED_DELTAS:
                stale = next(iter(self._deltas))
                self._deltas.pop(stale).filepath.unlink(missing_ok=True)

            return DeltaOffer(delta=key, instant=cached.instant, size=cached.filepath.stat().st_size)

    def diff_manifest(self, uuids: list[str]) -> ManifestDiff:
        """Return what this profile lacks of the nodes a pushing peer offers."""
        return ManifestDiff(missing=missing_uuids(self._backend, uuids))

    def resolve_delta(self, delta_id: str) -> Path | None:
        """Return the path of a negotiated delta, or ``None`` when nothing is on offer under that identifier."""
        with self._delta_lock:
            cached = self._deltas.get(delta_id)

            return cached.filepath if cached is not None else None

    def _delta(self, cursor: datetime | None, claim: frozenset[str]) -> Delta:
        """Return the computed delta for a cursor and claim, recomputing it once the profile gained content."""
        key = delta_id(cursor, claim)
        state = CollabState.read(self._state_filepath)
        cached = self._computed.get(key)

        if cached is None or self._stale(cached.instant, state):
            cached = compute_delta(state=state, backend=self._backend, cursor=cursor, claim=claim)
            self._computed.pop(key, None)
            self._computed[key] = cached

            while len(self._computed) > MAX_CACHED_DELTAS:
                self._computed.pop(next(iter(self._computed)))

        return cached

    def _stale(self, instant: datetime, state: CollabState) -> bool:
        """Return whether the profile gained content since a delta was computed at ``instant``."""
        if count_seeds(instant, self._backend) > 0:
            return True

        return any(event.direction == 'pull' and event.time >= instant for event in state.events)

    def import_staged(self, filepath: Path, peer: str, instant: datetime) -> dict[str, Any]:
        """Import a delta a peer pushed, pausing the daemon workers when the storage cannot take two writers."""
        from aiida.manage.configuration import get_config

        # Read from the file per import, like the handshake that preceded it: withdrawing consent must take effect
        # at once, and a pusher that negotiated before it was withdrawn must not be let through afterwards.
        if not stored_config(get_config()).get_option(OPTION_ACCEPT_PUSH, scope=self._profile.name):
            msg = f'this profile does not accept pushes: its `{OPTION_ACCEPT_PUSH}` option is off'
            raise PermissionError(msg)

        # The import lock wraps the worker stop as well: were it taken inside, a second push could restart the
        # workers while the first is still importing, which is the very starvation the stop exists to prevent.
        with import_lock(self._state_filepath):
            state = CollabState.read(self._state_filepath)

            with workers_stopped(self._profile):
                report = import_delta(
                    filepath,
                    state=state,
                    backend=self._backend,
                    peer=peer,
                    instant=instant,
                )

        return dataclasses.asdict(report)


def serve(profile: Profile, backend: StorageBackend) -> None:
    """Run the collab endpoint of the profile until the process is terminated."""
    from aiida.manage.configuration import get_config
    from aiida.tools.collab.server import CollabServer

    config = get_config()
    endpoint = CollabEndpoint(profile, backend)

    server = CollabServer(
        config.get_option(OPTION_BIND, scope=profile.name),
        config.get_option(OPTION_PORT, scope=profile.name),
        token=config.get_option(OPTION_TOKEN, scope=profile.name),
        collab=config.get_option(OPTION_UUID, scope=profile.name),
        staging_dir=endpoint.staging_dir,
        info=endpoint.info,
        join=endpoint.join,
        negotiate_delta=endpoint.negotiate_delta,
        request_delta=endpoint.request_delta,
        resolve_delta=endpoint.resolve_delta,
        diff_manifest=endpoint.diff_manifest,
        handshake=endpoint.handshake,
        import_staged=endpoint.import_staged,
    )

    with server:
        # An IPv6 socket reports a four-element address, of which only the first two belong in the log line.
        LOGGER.info('collab endpoint of profile `%s` listening on %s:%s', profile.name, *server.server_address[:2])
        server.serve_forever()
