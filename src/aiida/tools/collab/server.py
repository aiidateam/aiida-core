###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The HTTP endpoint over which the peers of a collab pull and push provenance.

The server is transport only: producing the delta, importing an upload and describing the profile are callables
injected by the caller, so the endpoint can be wired to the sync core by the daemon and to stubs by the tests.
"""

from __future__ import annotations

import json
import re
import shutil
from collections.abc import Callable
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from secrets import compare_digest
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qs, urlparse

from aiida.common.exceptions import ConfigurationError, IntegrityError
from aiida.common.log import AIIDA_LOGGER
from aiida.tools.collab.config import OPTION_BIND, OPTION_PORT, is_ipv6
from aiida.tools.collab.protocol import (
    API_PREFIX,
    CHUNK_SIZE,
    HEADER_COLLAB,
    HEADER_PEER,
    HEADER_STAGED,
    ROUTE_DELTA,
    ROUTE_HANDSHAKE,
    ROUTE_INFO,
    ROUTE_JOIN,
    ROUTE_MISSING,
    ROUTE_RETIRED,
    ROUTE_SESSION,
    UNAUTHORIZED_DETAIL,
    EndpointBusy,
    ExtrasSnapshot,
    GroupMembers,
    PushRefused,
    file_sha256,
    members_from_dict,
    refresh_from_dict,
)

if TYPE_CHECKING:
    from aiida.tools.collab.protocol import (
        DeltaManifest,
        DeltaOffer,
        JoinResponse,
        ManifestDiff,
        PeerInfo,
        PushHandshake,
    )

LOGGER = AIIDA_LOGGER.getChild('collab')

_DELTA_PATTERN = re.compile(f'{ROUTE_DELTA}/([0-9a-f]{{64}})')
_UPLOAD_PATTERN = re.compile(f'{API_PREFIX}/upload/([0-9a-f]{{64}})')
_IMPORT_PATTERN = re.compile(f'{API_PREFIX}/import/([0-9a-f]{{64}})')


class CollabServer(ThreadingHTTPServer):
    """The collab endpoint of a profile.

    :param host: the address to bind. Has to be the address of this machine on the private network of the collab:
        the endpoint speaks plain HTTP and refuses to listen on all interfaces. An IPv6 literal binds an IPv6
        socket, since the overlays this is deployed on commonly hand out IPv6 addresses.
    :param port: the port to bind. Pass ``0`` to let the operating system pick a free one.
    :param token: produces the shared secret of the collab, required of every request as a bearer token. Called
        per request rather than read once, so that a rotation on this machine retires the old token for serving
        the moment it is written — a token pinned at daemon start would keep letting an excluded member read.
    :param collab: the UUID of the collab. Every request but ``GET /collab/v1/info`` has to present it as the
        ``X-Collab-UUID`` header, so that the token alone cannot splice two collabs into one.
    :param staging_dir: the directory in which uploads are staged, one file per checksum.
    :param info: produces the handshake served at ``GET /collab/v1/info``. Receives the cursor presented with the
        request, or ``None``, against which the pending count is computed.
    :param join: admits a newcomer presenting a join code at ``POST /collab/v1/join``: receives its roster entry,
        adds it and answers with the full roster.
    :param retired: notified at ``POST /collab/v1/retired`` that the peer identified by the given profile UUID
        rotated the token of the collab. Advisory only: it makes ``verdi status`` tell the user to rekey.
    :param negotiate_delta: serves the manifest of the delta for the cursor and claim posted to
        ``POST /collab/v1/delta``, and merges the roster gossiped with it. Receives the requester of the
        ``X-Collab-Peer`` header, whose session the serving slot it takes belongs to.
    :param request_delta: exports (or reuses) the subset of that delta named by the ``want`` of a
        ``POST /collab/v1/delta`` and returns its offer, with the extras snapshots of its ``refresh_want``. Also
        receives the requester, as ``negotiate_delta`` does.
    :param resolve_delta: returns the path of the negotiated delta served at ``GET /collab/v1/delta/<id>``, or
        ``None`` when no delta with that identifier is on offer. Each identifier must keep resolving to the same
        bytes while a transfer is in progress; when the delta is re-exported, a client that resumes an interrupted
        download is served the new file from the start instead. Receives the requester too, since a download is
        activity of its session and keeps its slot from expiring under a long transfer.
    :param release: frees the serving slots of the requester, at ``DELETE /collab/v1/session`` and when a download
        was served to the end of the file. A peer that abandons a negotiation — a dry run, a declined prompt —
        ends its session that way instead of leaving the endpoint refusing others until the slot expires.
    :param diff_manifest: answers ``POST /collab/v1/missing`` for a peer that wants to push: which of the offered
        nodes this profile is missing, which of the offered extras it holds an older version of, and which of the
        offered group memberships it can apply.
    :param handshake: answers ``POST /collab/v1/handshake`` for a peer that wants to push: busy while an import is
        running, otherwise what the profile already holds of that peer. Merges the roster gossiped with it. Raising
        ``PushRefused`` means the profile does not accept pushes and is answered 403, here and at the import that
        refuses again for a pusher that skipped the handshake.
    :param import_staged: imports a fully staged upload at ``POST /collab/v1/import/<sha256>`` and returns a
        JSON-serializable report, which is relayed to the client. Receives the path of the staged file, the
        identity the pushing peer declared, the export instant carried with the delta, and the extras snapshots
        and group memberships the pusher was asked for. Raising
        ``IntegrityError`` means the staged delta can never land; it is discarded and answered 422, telling the
        pusher to negotiate afresh instead of retrying the same bytes.
    """

    daemon_threads = True

    def __init__(
        self,
        host: str,
        port: int,
        *,
        token: Callable[[], str],
        staging_dir: Path,
        info: Callable[[datetime | None], PeerInfo],
        negotiate_delta: Callable[[datetime | None, frozenset[str], list[dict[str, Any]], str], DeltaManifest],
        request_delta: Callable[[datetime | None, frozenset[str], frozenset[str], frozenset[str], str], DeltaOffer],
        resolve_delta: Callable[[str, str], Path | None],
        release: Callable[[str], None],
        diff_manifest: Callable[[list[str], dict[str, datetime], list[GroupMembers]], ManifestDiff],
        handshake: Callable[[str, list[dict[str, Any]]], PushHandshake],
        import_staged: Callable[[Path, str, datetime, list[ExtrasSnapshot], list[GroupMembers]], dict[str, Any]],
        join: Callable[[dict[str, Any]], JoinResponse],
        retired: Callable[[str], None],
        collab: str = '',
    ):
        import ipaddress
        import socket

        self.token = token
        self.collab = collab
        self.staging_dir = staging_dir
        self.info = info
        self.join = join
        self.retired = retired
        self.negotiate_delta = negotiate_delta
        self.request_delta = request_delta
        self.resolve_delta = resolve_delta
        self.release = release
        self.diff_manifest = diff_manifest
        self.handshake = handshake
        self.import_staged = import_staged

        staging_dir.mkdir(parents=True, exist_ok=True)

        # The family follows the address rather than the other way around: the code assumes nothing about the
        # network beyond peers being reachable where they said they are.
        if is_ipv6(host):
            self.address_family = socket.AF_INET6

        try:
            super().__init__((host, port), CollabRequestHandler)
        except OSError as exception:
            import errno

            advice = (
                f'Set the `{OPTION_BIND}` option to an address of this machine.'
                if exception.errno == errno.EADDRNOTAVAIL
                else f'Set the `{OPTION_PORT}` option to a free port, or free the one in use.'
            )
            msg = f'cannot serve the collab endpoint on {host}:{port}: {exception}. {advice}'
            raise ConfigurationError(msg) from exception

        # The socket is the authority on which address was bound, since `0`, `::0` and an empty host are all
        # spellings of the wildcard that no comparison against literals catches. Listening on every interface is
        # refused by design: the transport is plain HTTP with the token in cleartext.
        if ipaddress.ip_address(str(self.server_address[0])).is_unspecified:
            self.server_close()
            msg = (
                f'refusing to serve the collab endpoint on `{host or "an empty address"}`: set the `{OPTION_BIND}` '
                "option to this machine's address on the private network of the collab."
            )
            raise ConfigurationError(msg)


class CollabRequestHandler(BaseHTTPRequestHandler):
    """Dispatches the routes of the collab endpoint, after authenticating every request."""

    server: CollabServer

    protocol_version = 'HTTP/1.1'

    peer = ''
    """The requester of the request being dispatched, from its ``X-Collab-Peer`` header."""

    # A client that dies mid-request must not pin its handler thread forever; whatever it managed to stage
    # before the timeout remains resumable.
    timeout = 60

    def do_GET(self) -> None:
        self._dispatch({ROUTE_INFO: self._get_info, _DELTA_PATTERN: self._get_delta})

    def do_HEAD(self) -> None:
        self._dispatch({_UPLOAD_PATTERN: self._head_upload})

    def do_PUT(self) -> None:
        self._dispatch({_UPLOAD_PATTERN: self._put_upload})

    def do_DELETE(self) -> None:
        self._dispatch({ROUTE_SESSION: self._delete_session})

    def do_POST(self) -> None:
        self._dispatch(
            {
                ROUTE_DELTA: self._post_delta,
                ROUTE_MISSING: self._post_missing,
                ROUTE_HANDSHAKE: self._post_handshake,
                ROUTE_JOIN: self._post_join,
                ROUTE_RETIRED: self._post_retired,
                _IMPORT_PATTERN: self._post_import,
            }
        )

    def _dispatch(self, routes: dict[str | re.Pattern[str], Callable[..., None]]) -> None:
        """Authenticate the request, hold it against the collab this endpoint serves, and hand it to its route."""
        # Authentication comes first: an unauthenticated request must not reach any route handler.
        if not self._authenticated():
            # The body of an unauthenticated upload is never read, so the connection cannot be reused: it is
            # closed, and said so, or a pooling client races the close and sees a dropped connection instead of
            # the answer below.
            self.close_connection = True
            # A member whose token this endpoint retired reaches exactly this answer, which is where a rotation
            # is enforced and the only place it is: the detail is what points that member at the rekey.
            self._send_json(
                HTTPStatus.UNAUTHORIZED,
                {'detail': UNAUTHORIZED_DETAIL},
                headers={'WWW-Authenticate': 'Bearer', 'Connection': 'close'},
            )
            return

        path = urlparse(self.path).path
        presented = self.headers.get(HEADER_COLLAB, '')

        # The token authorizes and every member holds the same one, so the collab UUID is the second factor and the
        # only defence against a token that was shared too widely. Checked before routing rather than per handler,
        # which is what covers the upload routes — they stream raw bytes and have no body to carry it — and every
        # route added after this one. `/info` is exempt by design: it is the route whose purpose is to tell a caller
        # which collab this is, so it cannot demand that the caller already know.
        if path != ROUTE_INFO and presented != self.server.collab:
            # The body of a refused upload is never read, so the connection cannot carry another response: it is
            # closed, and said so, since a client that reused it would parse its own unread payload as the answer.
            self.close_connection = True
            self._send_json(
                HTTPStatus.CONFLICT,
                {'detail': f'this endpoint serves collab `{self.server.collab}`, not `{presented}`'},
                headers={'Connection': 'close'},
            )
            return

        # Read here rather than per route, as the collab UUID above is, and for the same reason: the routes that
        # need it include the ones that carry no body. It names a session and authorizes nothing, so a request
        # without it is served rather than refused; such requests share the one anonymous session.
        self.peer = self.headers.get(HEADER_PEER, '')

        try:
            for route, handler in routes.items():
                if isinstance(route, str):
                    if path == route:
                        handler()
                        return
                elif (match := route.fullmatch(path)) is not None:
                    handler(match[1])
                    return

            self._send_json(HTTPStatus.NOT_FOUND, {'detail': f'unknown route `{path}`'})
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            self.close_connection = True
        except EndpointBusy as exception:
            self._send_json(HTTPStatus.SERVICE_UNAVAILABLE, {'detail': str(exception)})
        except PushRefused as exception:
            # A profile that has not opted in to being written to is refusing, not malfunctioning: answering it as
            # the refusal it is keeps a traceback out of the daemon log and tells the pusher what to ask for.
            self._send_json(HTTPStatus.FORBIDDEN, {'detail': str(exception)})
        except Exception as exception:
            LOGGER.exception('collab endpoint request failed')
            self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {'detail': str(exception)})

    def _authenticated(self) -> bool:
        scheme, _, token = self.headers.get('Authorization', '').partition(' ')

        return scheme == 'Bearer' and compare_digest(token.encode(), self.server.token().encode())

    def _get_info(self) -> None:
        cursor = self._query('cursor')

        self._send_json(HTTPStatus.OK, self.server.info(datetime.fromisoformat(cursor) if cursor else None).as_dict())

    def _post_handshake(self) -> None:
        data = self._read_json()
        requester = data.get('requester')

        if requester is None:
            self._send_json(HTTPStatus.BAD_REQUEST, {'detail': 'the handshake requires a `requester`'})
            return

        self._send_json(HTTPStatus.OK, self.server.handshake(requester, data.get('roster', [])).as_dict())

    def _post_join(self) -> None:
        data = self._read_json()

        if not isinstance(data.get('entry'), dict):
            self._send_json(HTTPStatus.BAD_REQUEST, {'detail': 'joining requires the `entry` of the newcomer'})
            return

        self._send_json(HTTPStatus.OK, self.server.join(data['entry']).as_dict())

    def _post_retired(self) -> None:
        data = self._read_json()

        if not isinstance(data.get('peer'), str) or not data['peer']:
            self._send_json(HTTPStatus.BAD_REQUEST, {'detail': 'the signal requires the `peer` that rotated'})
            return

        self.server.retired(data['peer'])
        self._send_json(HTTPStatus.OK, {})

    def _post_delta(self) -> None:
        data = self._read_json()
        cursor = datetime.fromisoformat(data['cursor']) if data.get('cursor') else None
        claim = frozenset(data.get('claim', []))

        # Without a `want` the request negotiates the manifest; with one it asks for that subset to be exported.
        answer: DeltaManifest | DeltaOffer

        if 'want' in data:
            answer = self.server.request_delta(
                cursor, claim, frozenset(data['want']), frozenset(data.get('refresh_want', [])), self.peer
            )
        else:
            answer = self.server.negotiate_delta(cursor, claim, data.get('roster', []), self.peer)

        self._send_json(HTTPStatus.OK, answer.as_dict())

    def _delete_session(self) -> None:
        self.server.release(self.peer)
        self._send_json(HTTPStatus.OK, {})

    def _post_missing(self) -> None:
        data = self._read_json()
        diff = self.server.diff_manifest(
            data.get('uuids', []),
            refresh_from_dict(data.get('refresh', {})),
            members_from_dict(data.get('members', [])),
        )

        self._send_json(HTTPStatus.OK, diff.as_dict())

    def _get_delta(self, delta_id: str) -> None:
        filepath = self.server.resolve_delta(delta_id, self.peer)

        try:
            # The eviction of a delta can unlink the file after it was resolved; that is the same answer as an
            # unknown identifier, and the client recovers from either by negotiating again.
            stat = filepath.stat() if filepath is not None else None
        except FileNotFoundError:
            stat = None

        if filepath is None or stat is None:
            self._send_json(HTTPStatus.NOT_FOUND, {'detail': f'no delta on offer with identifier {delta_id}'})
            return

        # A weak validator in the style of nginx: producing a new delta changes size or mtime, which is what has
        # to invalidate resumption, and hashing the file on every request would not scale to large deltas.
        etag = f'"{stat.st_size:x}-{stat.st_mtime_ns:x}"'

        offset = self._parse_range(self.headers.get('Range'))

        # The file changed under the client: resuming would splice two different deltas, so serve it in full.
        if (if_range := self.headers.get('If-Range')) is not None and if_range != etag:
            offset = None

        if offset is not None and offset >= stat.st_size:
            self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
            self.send_header('Content-Range', f'bytes */{stat.st_size}')
            self.send_header('Content-Length', '0')
            self.end_headers()

            # This is how a client whose file is already complete learns so: its download is done too.
            self.server.release(self.peer)

            return

        self.send_response(HTTPStatus.OK if offset is None else HTTPStatus.PARTIAL_CONTENT)
        self.send_header('Content-Type', 'application/octet-stream')
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('ETag', etag)
        self.send_header('Content-Length', str(stat.st_size - (offset or 0)))

        if offset is not None:
            self.send_header('Content-Range', f'bytes {offset}-{stat.st_size - 1}/{stat.st_size}')

        self.end_headers()

        with filepath.open('rb') as handle:
            handle.seek(offset or 0)
            shutil.copyfileobj(handle, self.wfile, CHUNK_SIZE)

        # Reaching here means the response was written to the end of the file, whatever offset it started from:
        # the client holds the complete delta and the serving slot behind it can be freed.
        self.server.release(self.peer)

    def _head_upload(self, sha256: str) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header(HEADER_STAGED, str(self._staged_size(sha256)))
        self.send_header('Content-Length', '0')
        self.end_headers()

    def _put_upload(self, sha256: str) -> None:
        match = re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)', self.headers.get('Content-Range', ''))

        if match is None:
            self.close_connection = True
            self._send_json(
                HTTPStatus.BAD_REQUEST, {'detail': 'upload requires a `Content-Range: bytes first-last/total` header'}
            )
            return

        first = int(match[1])
        staged = self._staged_size(sha256)

        if first != staged:
            self.close_connection = True
            self._send_json(
                HTTPStatus.CONFLICT,
                {'detail': f'upload has {staged} bytes staged, not {first}: resume from there'},
                headers={HEADER_STAGED: str(staged)},
            )
            return

        remaining = int(self.headers['Content-Length'])

        with self._staging_path(sha256).open('ab') as handle:
            while remaining:
                chunk = self.rfile.read(min(CHUNK_SIZE, remaining))

                if not chunk:
                    # The client died mid-upload; what arrived stays staged for resumption, but there is no one
                    # left to respond to.
                    self.close_connection = True
                    return

                handle.write(chunk)
                remaining -= len(chunk)

        staged = self._staged_size(sha256)
        self._send_json(HTTPStatus.OK, {'staged': staged}, headers={HEADER_STAGED: str(staged)})

    def _post_import(self, sha256: str) -> None:
        data = self._read_json()
        filepath = self._staging_path(sha256)

        if 'peer' not in data or 'instant' not in data:
            self._send_json(
                HTTPStatus.BAD_REQUEST, {'detail': 'the import requires the `peer` and `instant` of the push'}
            )
            return

        if not filepath.exists():
            self._send_json(HTTPStatus.NOT_FOUND, {'detail': f'no staged upload with checksum {sha256}'})
            return

        if file_sha256(filepath) != sha256:
            # The staged bytes are corrupt and rot here otherwise: the client has to upload afresh.
            filepath.unlink()
            self._send_json(
                HTTPStatus.CONFLICT, {'detail': 'staged upload does not match its checksum: upload it again'}
            )
            return

        try:
            # A failing import deliberately leaves the staged file (the exception propagates to `_dispatch`), so
            # the next attempt negotiates that the bytes are already present and retries only the import.
            report = self.server.import_staged(
                filepath,
                data['peer'],
                datetime.fromisoformat(data['instant']),
                [ExtrasSnapshot.from_dict(snapshot) for snapshot in data.get('refresh', [])],
                members_from_dict(data.get('members', [])),
            )
        except IntegrityError as exception:
            # These bytes can never land: the delta references a node this profile no longer holds. Retrying the
            # import is pointless, so the staged file is discarded and the pusher has to negotiate afresh.
            filepath.unlink()
            self._send_json(HTTPStatus.UNPROCESSABLE_ENTITY, {'detail': str(exception)})
            return

        filepath.unlink()
        self._send_json(HTTPStatus.OK, report)

    def _query(self, name: str) -> str | None:
        """Return the value of a query parameter of the request, or ``None`` when it was not passed."""
        values = parse_qs(urlparse(self.path).query).get(name)

        return values[0] if values else None

    def _read_json(self) -> dict[str, Any]:
        """Read the JSON body of the request."""
        length = int(self.headers.get('Content-Length') or 0)

        return json.loads(self.rfile.read(length)) if length else {}

    def _staging_path(self, sha256: str) -> Path:
        return self.server.staging_dir / sha256

    def _staged_size(self, sha256: str) -> int:
        filepath = self._staging_path(sha256)

        return filepath.stat().st_size if filepath.exists() else 0

    @staticmethod
    def _parse_range(header: str | None) -> int | None:
        """Return the offset of a ``Range: bytes=N-`` header, the only form the collab client sends.

        Any other form is ignored, which HTTP allows: the response is simply the full file.
        """
        if header is None:
            return None

        match = re.fullmatch(r'bytes=(\d+)-', header)

        return int(match[1]) if match else None

    def _send_json(self, status: HTTPStatus, data: dict[str, Any], headers: dict[str, str] | None = None) -> None:
        body = json.dumps(data).encode('utf-8')

        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))

        for key, value in (headers or {}).items():
            self.send_header(key, value)

        self.end_headers()

        # A HEAD answer carries no content. Of the JSON answers only the error ones are reachable that way — the
        # upload probe of a pusher that fails to authenticate — and they are answered by their status alone.
        if self.command != 'HEAD':
            self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        LOGGER.debug('%s %s', self.client_address[0], format % args)
