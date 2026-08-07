###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The client with which a profile talks to the collab endpoint of a peer."""

from __future__ import annotations

import re
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, Literal

import requests

from aiida.tools.collab.protocol import (
    CHUNK_SIZE,
    HEADER_STAGED,
    ROUTE_DELTA,
    ROUTE_HANDSHAKE,
    ROUTE_INFO,
    ROUTE_JOIN,
    ROUTE_MISSING,
    ROUTE_RETIRED,
    CollabRequestError,
    DeltaManifest,
    DeltaOffer,
    JoinResponse,
    ManifestDiff,
    PeerInfo,
    PushHandshake,
    VersionSkew,
    file_sha256,
    members_as_dict,
    refresh_as_dict,
    route_delta,
    route_import,
    route_upload,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime
    from pathlib import Path

    from aiida.tools.collab.protocol import ExtrasSnapshot, GroupMembers

TIMEOUT = 60.0


@dataclass
class UploadReport:
    """The outcome of staging a delta on a peer."""

    sha256: str
    sent: int
    staged: int


class CollabClient:
    """Talks to the collab endpoint of a single peer.

    Interrupted transfers resume from the bytes that already arrived: downloads through ``Range`` requests
    guarded by the served ``ETag``, uploads by first asking the peer how much of the file it already staged.
    """

    def __init__(self, base_url: str, token: str, *, collab: str = '', timeout: float = TIMEOUT):
        self._base_url = base_url.rstrip('/')
        self._collab = collab
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers['Authorization'] = f'Bearer {token}'

    def close(self) -> None:
        self._session.close()

    def __enter__(self) -> CollabClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def info(self, cursor: datetime | None = None) -> PeerInfo:
        """Fetch the handshake of the peer.

        :param cursor: the cursor this profile holds for the peer; the peer's pending count is relative to it.
        """
        params = {'cursor': cursor.isoformat()} if cursor is not None else None

        return self._answer(PeerInfo.from_dict, 'GET', ROUTE_INFO, params=params)

    def join(self, entry: dict[str, Any]) -> JoinResponse:
        """Present the join code to the member that issued it, announce this profile and receive the roster.

        :param entry: the roster entry of this profile: its UUID, endpoint URL, announced name and version stamp.
        """
        body = {'collab': self._collab, 'entry': entry}

        return self._answer(JoinResponse.from_dict, 'POST', ROUTE_JOIN, json=body)

    def signal_retired(self, peer: str) -> None:
        """Tell the peer that this profile retired the token both were using, so it can ask its user to rekey.

        Sent with the token being retired, which is the only one the peer still knows. It is advisory and nothing
        more: an excluded member holds that same token, so any automatic reaction to this would hand it the power
        to freeze the collab.

        :param peer: the profile UUID of this profile, under which the receiver knows it.
        """
        self._request('POST', ROUTE_RETIRED, json={'collab': self._collab, 'peer': peer})

    def check_version_skew(self, local: PeerInfo, *, direction: Literal['pull', 'push']) -> PeerInfo:
        """Fetch the handshake of the peer and refuse the transfer when it could not read what the sender writes.

        The delta travels as an archive, so the archive format is the interchange contract of a collab; the storage
        schema of either side is its own concern, which is what makes a collab of mixed PostgreSQL and SQLite
        profiles first-class. Since a profile reads its own archive format and every older one, only the sending
        side can be too new, so exactly one direction is refused and the message names whoever has to act on it.

        :param local: the handshake of this side, to compare against.
        :param direction: which way the delta would travel, since that decides who has to upgrade.
        :return: the handshake of the peer, so that callers can display both sides.
        :raises VersionSkew: when the receiving side of the transfer cannot read the sender's archive format.
        """
        peer = self.info()

        # Archive format versions are zero-padded (`main_0002`), so string comparison orders them.
        if direction == 'pull' and peer.archive_schema > local.archive_schema:
            msg = (
                f'cannot pull from the peer at {self._base_url}: it writes archive format '
                f'`{peer.archive_schema}`, this profile reads up to `{local.archive_schema}`. Its deltas are not '
                f'compatible with your aiida-core; please upgrade it to the latest stable release (your '
                f'collaborator runs {peer.version}).'
            )
        elif direction == 'push' and local.archive_schema > peer.archive_schema:
            msg = (
                f'cannot push to the peer at {self._base_url}: this profile writes archive format '
                f'`{local.archive_schema}`, the peer reads up to `{peer.archive_schema}`. Please ask your '
                f'collaborator to upgrade their aiida-core to the latest stable release (they run {peer.version}).'
            )
        else:
            return peer

        raise VersionSkew(msg)

    def negotiate_delta(
        self, cursor: datetime | None, claim: frozenset[str] | set[str], roster: list[dict[str, Any]] | None = None
    ) -> DeltaManifest:
        """Present a cursor and a claim to the peer and receive the manifest of the delta they negotiate.

        :param cursor: the export instant of the last delta imported from this peer, or ``None`` for everything.
        :param claim: UUIDs this profile already holds and does not want re-delivered.
        :param roster: this profile's own entry and the peers it knows, gossiped with the negotiation; the answer
            carries the peer's own in return.
        """
        body = {
            'cursor': cursor.isoformat() if cursor is not None else None,
            'claim': sorted(claim),
            'collab': self._collab,
            'roster': roster or [],
        }

        return self._answer(DeltaManifest.from_dict, 'POST', ROUTE_DELTA, json=body)

    def request_delta(
        self,
        cursor: datetime | None,
        claim: frozenset[str] | set[str],
        want: frozenset[str] | set[str],
        refresh_want: frozenset[str] | set[str] | list[str] = frozenset(),
    ) -> DeltaOffer:
        """Ask the peer to export the subset of the negotiated delta this profile lacks, and receive its offer.

        :param cursor: the cursor the manifest was negotiated with.
        :param claim: the claim the manifest was negotiated with.
        :param want: the UUIDs of the manifest this profile is missing.
        :param refresh_want: the nodes of the manifest's refresh offer whose extras this profile holds an older
            version of; their snapshots come with the offer.
        """
        body = {
            'cursor': cursor.isoformat() if cursor is not None else None,
            'claim': sorted(claim),
            'want': sorted(want),
            'refresh_want': sorted(refresh_want),
            'collab': self._collab,
        }

        return self._answer(DeltaOffer.from_dict, 'POST', ROUTE_DELTA, json=body)

    def diff_manifest(
        self,
        uuids: list[str],
        refresh: dict[str, datetime] | None = None,
        members: list[GroupMembers] | None = None,
    ) -> ManifestDiff:
        """Offer the peer a manifest of nodes, of edited extras and of memberships, and receive what it lacks.

        :param uuids: the manifest of the delta this profile would push.
        :param refresh: the mtimes this profile holds for the shared nodes whose extras it may have edited.
        :param members: the group memberships this profile gained since the peer's cursor, offered under ``grow``.
        """
        body = {'uuids': uuids, 'refresh': refresh_as_dict(refresh or {}), 'members': members_as_dict(members or [])}

        return self._answer(ManifestDiff.from_dict, 'POST', ROUTE_MISSING, json=body)

    def push_handshake(self, requester: str, roster: list[dict[str, Any]] | None = None) -> PushHandshake:
        """Ask the peer what it already holds of this profile, in preparation of a push.

        :param requester: the identity under which the peer tracks this profile: its profile UUID.
        :param roster: this profile's own entry and the peers it knows, gossiped with the handshake; the answer
            carries the peer's own in return.
        """
        body = {'requester': requester, 'collab': self._collab, 'roster': roster or []}

        return self._answer(PushHandshake.from_dict, 'POST', ROUTE_HANDSHAKE, json=body)

    def download_delta(self, filepath: Path, delta_id: str) -> int:
        """Download a negotiated delta of the peer, resuming a partial file at ``filepath`` where it was interrupted.

        The ``ETag`` served with the first attempt is kept next to the file; when the peer produced a new delta
        in the meantime, the resumption starts over instead of splicing two different deltas.

        :param filepath: the path to download to.
        :param delta_id: the identifier under which the delta is on offer, from ``negotiate_delta``.
        :return: the number of bytes transferred by this call.
        """
        filepath_etag = filepath.with_name(f'{filepath.name}.etag')
        offset = filepath.stat().st_size if filepath.exists() else 0
        headers = {}

        if offset:
            headers['Range'] = f'bytes={offset}-'

            if filepath_etag.exists():
                headers['If-Range'] = filepath_etag.read_text(encoding='utf-8')

        response = self._request(
            'GET',
            route_delta(delta_id),
            headers=headers,
            stream=True,
            allowed=(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE,),
        )

        if response.status_code == HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE:
            # The only range the client asks for starts at the end of its partial file, so an unsatisfiable one
            # of the same size means the download is already complete.
            match = re.fullmatch(r'bytes \*/(\d+)', response.headers.get('Content-Range', ''))

            if match is not None and int(match[1]) == offset:
                return 0

            msg = f'the peer cannot serve the delta from offset {offset}'
            raise CollabRequestError(msg, status=response.status_code)

        if etag := response.headers.get('ETag'):
            # Recorded before consuming the body, so that an interrupted transfer leaves it for the resumption.
            filepath_etag.write_text(etag, encoding='utf-8')

        transferred = 0

        with filepath.open('ab' if response.status_code == HTTPStatus.PARTIAL_CONTENT else 'wb') as handle:
            try:
                for chunk in response.iter_content(CHUNK_SIZE):
                    handle.write(chunk)
                    transferred += len(chunk)
            except requests.RequestException as exception:
                msg = f'downloading the delta was interrupted after {offset + transferred} bytes: {exception}'
                raise CollabRequestError(msg) from exception

        return transferred

    def upload_delta(self, filepath: Path) -> UploadReport:
        """Stage a delta on the peer, sending only the bytes it does not already hold.

        :param filepath: the path of the archive to upload.
        :return: the checksum under which the upload is staged, the bytes sent by this call and the total staged.
        """
        sha256 = file_sha256(filepath)
        size = filepath.stat().st_size
        response = self._request('HEAD', route_upload(sha256))

        try:
            staged = int(response.headers[HEADER_STAGED])
        except (KeyError, ValueError) as exception:
            msg = f'the peer at {self._base_url} did not answer the upload probe like a collab endpoint: {exception}'
            raise CollabRequestError(msg) from exception

        if staged == size:
            return UploadReport(sha256=sha256, sent=0, staged=staged)

        with filepath.open('rb') as handle:
            handle.seek(staged)
            headers = {'Content-Range': f'bytes {staged}-{size - 1}/{size}'}
            total = self._answer(
                lambda data: int(data['staged']), 'PUT', route_upload(sha256), data=handle, headers=headers
            )

        return UploadReport(sha256=sha256, sent=size - staged, staged=total)

    def trigger_import(
        self,
        sha256: str,
        *,
        peer: str,
        instant: datetime,
        refresh: list[ExtrasSnapshot] | None = None,
        members: list[GroupMembers] | None = None,
    ) -> dict[str, Any]:
        """Ask the peer to import the staged upload with the given checksum.

        The peer imports synchronously, so the response may take as long as the import; only the connection
        itself is subject to the timeout.

        :param sha256: the checksum under which the upload was staged.
        :param peer: the identity under which the receiver tracks this profile.
        :param instant: the export instant of the staged delta, which the receiver's cursor advances to.
        :param refresh: the extras snapshots the receiver asked for when it diffed the manifest.
        :param members: the group memberships the receiver asked for when it diffed the manifest.
        :return: the import report of the peer.
        :raises CollabRequestError: when the import fails, with the reason of the peer. The peer keeps the staged
            upload in that case, so a retry only repeats the import, not the transfer — unless the upload failed
            its checksum verification (409) or can never land because it links to a node the peer no longer holds
            (422), in which cases the peer discards it and the push has to be negotiated afresh.
        """
        body = {
            'peer': peer,
            'instant': instant.isoformat(),
            'refresh': [snapshot.as_dict() for snapshot in refresh or []],
            'members': members_as_dict(members or []),
        }

        return self._answer(dict, 'POST', route_import(sha256), json=body, timeout=(self._timeout, None))

    def _answer(self, parser: Callable[[Any], Any], method: str, route: str, **kwargs: Any) -> Any:
        """Request and parse the answer; a body that does not parse as the expected answer is a request error.

        A peer URL can reach a service that is not a collab endpoint — a reverse-proxy default, a machine that
        was reprovisioned — whose 200 with an arbitrary body must fail like an unreachable peer, not crash the
        caller.
        """
        response = self._request(method, route, **kwargs)

        try:
            return parser(response.json())
        except (AttributeError, KeyError, TypeError, ValueError) as exception:
            msg = f'the peer at {self._base_url} did not answer `{method} {route}` like a collab endpoint: {exception}'
            raise CollabRequestError(msg) from exception

    def _request(
        self, method: str, route: str, *, allowed: tuple[HTTPStatus, ...] = (), **kwargs: Any
    ) -> requests.Response:
        kwargs.setdefault('timeout', self._timeout)

        try:
            response = self._session.request(method, f'{self._base_url}{route}', **kwargs)
        except requests.RequestException as exception:
            msg = f'request to the peer at {self._base_url} failed: {exception}'
            raise CollabRequestError(msg) from exception

        if response.status_code >= HTTPStatus.BAD_REQUEST and response.status_code not in allowed:
            try:
                detail = response.json()['detail']
            except (ValueError, KeyError):
                detail = response.reason

            msg = f'the peer at {self._base_url} responded {response.status_code} to {method} {route}: {detail}'
            raise CollabRequestError(msg, status=response.status_code)

        return response
