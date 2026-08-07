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
from typing import TYPE_CHECKING, Any

import requests

from aiida.tools.collab.protocol import (
    CHUNK_SIZE,
    HEADER_STAGED,
    ROUTE_DELTA,
    ROUTE_HANDSHAKE,
    ROUTE_INFO,
    ROUTE_MISSING,
    CollabRequestError,
    DeltaManifest,
    DeltaOffer,
    ManifestDiff,
    PeerInfo,
    PushHandshake,
    file_sha256,
    route_delta,
    route_import,
    route_upload,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime
    from pathlib import Path

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

    def __init__(self, base_url: str, token: str, *, timeout: float = TIMEOUT):
        self._base_url = base_url.rstrip('/')
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

    def negotiate_delta(self, cursor: datetime | None, claim: frozenset[str] | set[str]) -> DeltaManifest:
        """Present a cursor and a claim to the peer and receive the manifest of the delta they negotiate.

        :param cursor: the export instant of the last delta imported from this peer, or ``None`` for everything.
        :param claim: UUIDs this profile already holds and does not want re-delivered.
        """
        body = {
            'cursor': cursor.isoformat() if cursor is not None else None,
            'claim': sorted(claim),
        }

        return self._answer(DeltaManifest.from_dict, 'POST', ROUTE_DELTA, json=body)

    def request_delta(
        self,
        cursor: datetime | None,
        claim: frozenset[str] | set[str],
        want: frozenset[str] | set[str],
    ) -> DeltaOffer:
        """Ask the peer to export the subset of the negotiated delta this profile lacks, and receive its offer.

        :param cursor: the cursor the manifest was negotiated with.
        :param claim: the claim the manifest was negotiated with.
        :param want: the UUIDs of the manifest this profile is missing.
        """
        body = {
            'cursor': cursor.isoformat() if cursor is not None else None,
            'claim': sorted(claim),
            'want': sorted(want),
        }

        return self._answer(DeltaOffer.from_dict, 'POST', ROUTE_DELTA, json=body)

    def diff_manifest(self, uuids: list[str]) -> ManifestDiff:
        """Offer the peer a manifest of nodes and receive what it lacks.

        :param uuids: the manifest of the delta this profile would push.
        """
        return self._answer(ManifestDiff.from_dict, 'POST', ROUTE_MISSING, json={'uuids': uuids})

    def push_handshake(self, requester: str) -> PushHandshake:
        """Ask the peer what it already holds of this profile, in preparation of a push.

        :param requester: the identity under which the peer tracks this profile: its profile UUID.
        """
        body = {'requester': requester}

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

    def trigger_import(self, sha256: str, *, peer: str, instant: datetime) -> dict[str, Any]:
        """Ask the peer to import the staged upload with the given checksum.

        The peer imports synchronously, so the response may take as long as the import; only the connection
        itself is subject to the timeout.

        :param sha256: the checksum under which the upload was staged.
        :param peer: the identity under which the receiver tracks this profile.
        :param instant: the export instant of the staged delta, which the receiver's cursor advances to.
        :return: the import report of the peer.
        :raises CollabRequestError: when the import fails, with the reason of the peer. The peer keeps the staged
            upload in that case, so a retry only repeats the import, not the transfer — unless the upload failed
            its checksum verification (409) or can never land because it links to a node the peer no longer holds
            (422), in which cases the peer discards it and the push has to be negotiated afresh.
        """
        body = {'peer': peer, 'instant': instant.isoformat()}

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
