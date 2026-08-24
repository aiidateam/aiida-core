###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the transport layer of a collab: the endpoint and its client, over loopback."""

import socket
import threading
import time
from dataclasses import dataclass, replace
from datetime import datetime
from http import HTTPStatus
from pathlib import Path

import pytest
import requests

from aiida.common import timezone
from aiida.common.exceptions import ConfigurationError
from aiida.tools.collab.client import CollabClient
from aiida.tools.collab.config import endpoint_url
from aiida.tools.collab.protocol import (
    API_PREFIX,
    HEADER_COLLAB,
    REKEY_HINT,
    ROUTE_DELTA,
    ROUTE_HANDSHAKE,
    ROUTE_INFO,
    ROUTE_JOIN,
    ROUTE_MISSING,
    ROUTE_RETIRED,
    ROUTE_SESSION,
    CollabRequestError,
    DeltaManifest,
    DeltaOffer,
    ExtrasSnapshot,
    GroupMembers,
    JoinResponse,
    ManifestDiff,
    PeerInfo,
    PushHandshake,
    VersionSkew,
    delta_id,
    file_sha256,
    route_delta,
    route_import,
    route_upload,
)
from aiida.tools.collab.server import CollabServer

TOKEN = 'the-collab-token'
COLLAB = 'uuid-of-the-collab'
PEER = 'uuid-of-the-requester'

DELTA = bytes(range(256)) * 1024
UPLOAD = bytes(reversed(range(256))) * 512

PEER_INFO = PeerInfo(
    version='2.9.0',
    backend='core.sqlite_dos',
    storage_schema='main_0002',
    archive_schema='main_0001',
    pending_count=3,
    accept_push=True,
    extras_mode='local',
    groups_mode='local',
    collab=COLLAB,
)

LOCAL_INFO = replace(PEER_INFO, backend='core.psql_dos', pending_count=0)


class StubSyncCore:
    """Stands in for the sync core: a fixed-bytes delta, recorded imports and a configurable handshake."""

    def __init__(self, delta_path: Path):
        self.delta_path = delta_path
        self.peer_info = PEER_INFO
        self.push_handshake = PushHandshake(busy=False, cursor=None, claim=[])
        self.manifest = ['uuid-offered']
        self.missing = ['uuid-missing']
        self.refused = ['uuid-deleted']
        self.instant = timezone.now()
        self.import_exception: Exception | None = None
        self.negotiated: list[tuple[datetime | None, frozenset]] = []
        self.requested: list[tuple[datetime | None, frozenset, frozenset]] = []
        self.instants: list[datetime | None] = []
        self.requesters: list[str] = []
        self.offered: set[str] = set()
        self.released: list[str] = []
        self.serves: list[tuple[str, str]] = []
        self.stagings: list[str] = []
        self.diffed: list[list[str]] = []
        self.handshakes: list[str] = []
        self.joined: list[dict] = []
        self.token = TOKEN
        self.retirements: list[str] = []
        self.roster: list[dict] = [{'uuid': 'uuid-of-the-peer', 'url': 'http://peer:9137', 'name': 'peer', 'stamp': 1}]
        self.info_cursors: list[datetime | None] = []
        self.imported: list[tuple[str, datetime, bytes]] = []
        self.applied: list = []
        self.delay = 0.0
        """Seconds the two routes that compute a delta take to answer, as a large profile makes them take."""

    def info(self, cursor: datetime | None) -> PeerInfo:
        self.info_cursors.append(cursor)
        return self.peer_info

    def negotiate_delta(
        self, cursor: datetime | None, claim: frozenset, roster: list | None = None, requester: str = ''
    ) -> DeltaManifest:
        time.sleep(self.delay)
        self.negotiated.append((cursor, claim))
        self.requesters.append(requester)
        return DeltaManifest(manifest=self.manifest, instant=self.instant, roster=self.roster)

    def request_delta(
        self,
        cursor: datetime | None,
        claim: frozenset,
        want: frozenset,
        refresh_want: frozenset,
        refuse: frozenset,
        requester: str = '',
        computed: datetime | None = None,
    ) -> DeltaOffer:
        time.sleep(self.delay)
        self.requested.append((cursor, claim, want, refuse))
        self.instants.append(computed)
        self.offered.add(delta_id(cursor, claim, want, refuse))
        return DeltaOffer(
            delta=delta_id(cursor, claim, want, refuse),
            instant=self.instant,
            size=self.delta_path.stat().st_size,
            refresh=[ExtrasSnapshot(uuid=uuid, mtime=self.instant, extras={'k': 1}) for uuid in sorted(refresh_want)],
        )

    def resolve_delta(self, requested_id: str, requester: str = '') -> Path | None:
        time.sleep(self.delay)
        # Whether an identifier is on offer, never whether its file is still there — the endpoint looks it up in
        # its cache of computations, and an eviction that unlinks the file does not go back and tell the caller.
        return self.delta_path if requested_id in self.offered else None

    def release(self, requester: str) -> None:
        self.released.append(requester)

    def served(self, delta_id: str, requester: str) -> None:
        self.serves.append((delta_id, requester))

    def staging(self, requester: str) -> None:
        self.stagings.append(requester)

    def diff_manifest(self, uuids: list, refresh: dict, members: list) -> ManifestDiff:
        self.diffed.append(uuids)
        return ManifestDiff(missing=self.missing, refresh=sorted(refresh), refuse=self.refused, members=members)

    def handshake(self, requester: str, roster: list | None = None) -> PushHandshake:
        time.sleep(self.delay)
        self.handshakes.append(requester)
        return self.push_handshake

    def join(self, entry: dict) -> JoinResponse:
        self.joined.append(entry)
        return JoinResponse(collab=COLLAB, roster=self.roster)

    def retired(self, peer: str) -> None:
        self.retirements.append(peer)

    def import_staged(self, filepath: Path, peer: str, instant: datetime, refresh: list, members: list) -> dict:
        if self.import_exception is not None:
            raise self.import_exception

        self.imported.append((peer, instant, filepath.read_bytes()))
        self.applied = members
        return {'imported': 7}


@dataclass
class Transport:
    """The moving parts of a running endpoint, handed to each test."""

    client: CollabClient
    stub: StubSyncCore
    staging_dir: Path
    url: str


def build_server(host: str, port: int, stub: StubSyncCore, staging_dir: Path) -> CollabServer:
    """Build an endpoint wired to a stubbed sync core."""
    return CollabServer(
        host,
        port,
        # Read per request, so a rotation retires the old token for serving without a restart.
        token=lambda: stub.token,
        collab=COLLAB,
        staging_dir=staging_dir,
        info=stub.info,
        join=stub.join,
        retired=stub.retired,
        negotiate_delta=stub.negotiate_delta,
        request_delta=stub.request_delta,
        resolve_delta=stub.resolve_delta,
        release=stub.release,
        served=stub.served,
        staging=stub.staging,
        diff_manifest=stub.diff_manifest,
        handshake=stub.handshake,
        import_staged=stub.import_staged,
    )


@pytest.fixture
def transport(tmp_path):
    """A collab endpoint on a loopback port with a stubbed sync core, and a client talking to it."""
    delta_path = tmp_path / 'delta.aiida'
    delta_path.write_bytes(DELTA)

    stub = StubSyncCore(delta_path)
    staging_dir = tmp_path / 'staging'

    server = build_server('127.0.0.1', 0, stub, staging_dir)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    url = f'http://127.0.0.1:{server.server_address[1]}'

    try:
        with CollabClient(url, TOKEN, collab=COLLAB, peer=PEER, timeout=10) as client:
            yield Transport(client=client, stub=stub, staging_dir=staging_dir, url=url)
    finally:
        # Torn down however the test ended: a failing one would otherwise leak its thread and its port for the
        # rest of the session, and the next failure would be an unrelated bind error.
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.mark.parametrize('host', ['0.0.0.0', '', '::', '::0', '0'])
def test_bind_refused(tmp_path, host):
    """The endpoint refuses to listen on all interfaces, whichever of its many spellings was configured.

    The socket is asked what was bound rather than the string compared against literals, since `0`, `::0` and an
    empty host are all the wildcard and no list of literals is ever complete.
    """
    stub = StubSyncCore(tmp_path / 'delta.aiida')

    with pytest.raises(ConfigurationError, match=r'collab\.bind'):
        build_server(host, 0, stub, tmp_path)


def test_bind_port_in_use(tmp_path):
    """A port another process already listens on is a configuration error naming the option to change.

    The daemon starts the endpoint, so this has to be an error the user can act on rather than a traceback in the
    daemon log followed by a profile whose peers can never reach it.
    """
    stub = StubSyncCore(tmp_path / 'delta.aiida')

    with socket.socket() as occupant:
        occupant.bind(('127.0.0.1', 0))
        occupant.listen()

        with pytest.raises(ConfigurationError, match=r'collab\.port'):
            build_server('127.0.0.1', occupant.getsockname()[1], stub, tmp_path)


def test_serves_on_ipv6(tmp_path):
    """An IPv6 bind address is served over IPv6 and reached at the bracketed URL the roster carries.

    The overlays a collab runs on commonly hand out IPv6 addresses, and the socket family is not something a user
    should have to configure: it follows the address.
    """
    stub = StubSyncCore(tmp_path / 'delta.aiida')

    try:
        server = build_server('::1', 0, stub, tmp_path / 'staging')
    except ConfigurationError as exception:
        pytest.skip(f'no IPv6 loopback on this host: {exception}')

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        with CollabClient(endpoint_url('::1', server.server_address[1]), TOKEN, collab=COLLAB, timeout=10) as client:
            assert client.info() == PEER_INFO
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_join(transport):
    """A newcomer presenting the join code is recorded by the issuer and answered with the full membership."""
    entry = {'uuid': 'uuid-of-the-newcomer', 'url': 'http://newcomer:9137', 'name': 'newcomer', 'stamp': 1}

    response = transport.client.join(entry)

    assert transport.stub.joined == [entry]
    assert response == JoinResponse(collab=COLLAB, roster=transport.stub.roster)


def test_join_refuses_a_foreign_collab(transport):
    """Joining a collab other than the one the endpoint serves is refused, whatever token was presented.

    A token shared too widely would otherwise splice two collabs into one, which no later handshake could undo.
    """
    with CollabClient(transport.url, TOKEN, collab='uuid-of-another-collab', timeout=10) as client:
        with pytest.raises(CollabRequestError) as excinfo:
            client.join({'uuid': 'uuid-of-the-newcomer', 'url': 'http://newcomer:9137', 'name': 'x', 'stamp': 1})

    assert excinfo.value.status == HTTPStatus.CONFLICT
    assert transport.stub.joined == []


def test_client_foreign_service(tmp_path):
    """Test that any 200 from a service that is not a collab endpoint surfaces as ``CollabRequestError``.

    A peer URL can reach a reverse-proxy default or a reprovisioned machine; the sync loops must be able to
    warn and skip such a peer, which requires the client to fold the unparseable answer into its request error.
    """
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class ForeignHandler(BaseHTTPRequestHandler):
        def _answer(self):
            body = b'<html>not a collab endpoint</html>'
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()

            if self.command != 'HEAD':
                self.wfile.write(body)

        do_GET = do_POST = do_PUT = do_HEAD = _answer  # noqa: N815

        def log_message(self, format, *args):
            pass

    server = HTTPServer(('127.0.0.1', 0), ForeignHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    filepath = tmp_path / 'push.aiida'
    filepath.write_bytes(b'delta')

    try:
        with CollabClient(f'http://127.0.0.1:{server.server_address[1]}', TOKEN) as client:
            with pytest.raises(CollabRequestError, match='like a collab endpoint'):
                client.info()

            with pytest.raises(CollabRequestError, match='like a collab endpoint'):
                client.push_handshake('some-uuid')

            with pytest.raises(CollabRequestError, match='like a collab endpoint'):
                client.upload_delta(filepath)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_client_error_body_that_is_not_an_object(tmp_path):
    """An error status whose body is valid JSON but not an object still surfaces as ``CollabRequestError``.

    A reverse proxy in front of a peer answers its own 500 with whatever body it likes, a JSON list among them,
    and subscripting that by a string raises ``TypeError``. Uncaught it escapes the client entirely, so the sync
    loop that is prepared to warn and skip an unreachable peer instead aborts the whole run over one bad peer.
    """
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class ProxyHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = b'["upstream is down"]'
            self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            pass

    server = HTTPServer(('127.0.0.1', 0), ProxyHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        with CollabClient(f'http://127.0.0.1:{server.server_address[1]}', TOKEN) as client:
            with pytest.raises(CollabRequestError) as excinfo:
                client.info()

        assert excinfo.value.status == HTTPStatus.INTERNAL_SERVER_ERROR
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_an_upload_without_a_matching_length_is_refused(transport):
    """A ``PUT`` whose ``Content-Length`` is absent or contradicts its range is refused before anything is staged.

    Without the header there is nothing to read the body to, and the handler would read the declared range out of
    a socket the client is not sending on — hanging until the timeout with the slot held. With a length that
    disagrees with the range, the bytes staged are not the bytes the range says they are, and the checksum that
    would catch it is only verified once the whole file is claimed complete.
    """
    sha256 = 'd' * 64
    host, port = transport.url.removeprefix('http://').split(':')

    def refused(*headers: str) -> bytes:
        lines = [
            f'PUT {route_upload(sha256)} HTTP/1.1',
            f'Host: {host}:{port}',
            f'Authorization: Bearer {TOKEN}',
            f'{HEADER_COLLAB}: {COLLAB}',
            'Content-Range: bytes 0-63/64',
            *headers,
        ]
        answer = b''

        with socket.create_connection((host, int(port)), timeout=10) as connection:
            # latin-1, which is how a header value reaches the handler: encoded as UTF-8 a superscript
            # arrives as two characters and never reaches `int` at all.
            connection.sendall(('\r\n'.join(lines) + '\r\n\r\n').encode('latin-1'))

            # Read to end of stream: a refusal that left the connection open would hang here until the timeout,
            # and that is the very failure the close exists to prevent.
            while chunk := connection.recv(4096):
                answer += chunk

        return answer

    assert refused().startswith(b'HTTP/1.1 400'), 'a body with no length to read to must be refused'
    assert refused('Content-Length: 8').startswith(b'HTTP/1.1 400'), 'a length that is not the range is refused'
    # `str.isdigit` is true of this and `int` refuses it, so a guard using the first raises out of its own
    # condition and answers the 500-on-an-unread-body it exists to prevent.
    assert refused('Content-Length: \u00b2').startswith(b'HTTP/1.1 400'), 'a digit `int` cannot parse is refused'
    assert not (transport.staging_dir / sha256).exists()


def test_a_delta_evicted_while_it_is_being_served_is_never_a_short_body(transport, tmp_path, monkeypatch):
    """A delta unlinked in the window between measuring it and reading it is served whole, not truncated.

    The eviction of a cached delta unlinks the file, and nothing holds it against a download that is starting:
    measuring the file and then opening it are two syscalls, and an eviction landing between them leaves a
    response that already promised 200 and a length with no bytes to send. What the client writes then is a
    short file the length check should have caught, and an import that fails on a corrupt archive.

    The window is entered deterministically through ``_parse_range``, which is the one call the handler makes
    between the two — a race is only testable by standing in it. On a handler that opens first, the unlink is
    what it must be: harmless, because the bytes are already reachable through an open descriptor.
    """
    from aiida.tools.collab.server import CollabRequestHandler

    offer = transport.client.request_delta(None, frozenset(), frozenset())
    parse_range = CollabRequestHandler._parse_range

    def evict_then_parse(header):
        transport.stub.delta_path.unlink(missing_ok=True)
        return parse_range(header)

    monkeypatch.setattr(CollabRequestHandler, '_parse_range', staticmethod(evict_then_parse))
    filepath = tmp_path / 'download.aiida'

    assert transport.client.download_delta(filepath, offer.delta) == len(DELTA)
    assert not transport.stub.delta_path.exists(), 'the eviction has to land, or the window is never entered'
    assert filepath.read_bytes() == DELTA


def test_auth_rejected(transport):
    """A request without the correct bearer token returns 401 and never reaches a route handler."""
    routes = [
        ('GET', ROUTE_INFO),
        ('POST', ROUTE_HANDSHAKE),
        ('POST', ROUTE_JOIN),
        ('POST', ROUTE_RETIRED),
        ('GET', route_delta('0' * 64)),
        ('POST', ROUTE_DELTA),
        ('POST', ROUTE_MISSING),
        ('HEAD', route_upload('0' * 64)),
        ('PUT', route_upload('0' * 64)),
        ('POST', route_import('0' * 64)),
        ('DELETE', ROUTE_SESSION),
    ]

    for headers in ({}, {'Authorization': 'Bearer not-the-collab-token'}):
        for method, route in routes:
            response = requests.request(method, f'{transport.url}{route}', headers=headers, timeout=10)
            assert response.status_code == HTTPStatus.UNAUTHORIZED, (method, route)
            # The request body is never read, so the socket is closed; a pooling client that is not told races
            # the close and sees a dropped connection instead of the answer that tells it to rekey.
            assert response.headers.get('Connection') == 'close', (method, route)

    refused = requests.get(f'{transport.url}{ROUTE_INFO}', headers={'Authorization': 'Bearer wrong'}, timeout=10)

    assert transport.stub.info_cursors == []
    assert transport.stub.negotiated == []
    assert transport.stub.requested == []
    assert transport.stub.diffed == []
    assert transport.stub.handshakes == []
    assert transport.stub.joined == []
    assert transport.stub.retirements == []
    assert transport.stub.imported == []
    assert transport.stub.released == []
    assert REKEY_HINT in refused.json()['detail'], 'the 401 is where a rotation is enforced, and it has to say so'


def test_rotated_token_is_refused_at_once(transport):
    """A token the endpoint no longer holds is refused from the next request on, without a restart.

    This is the whole enforcement of a rotation: the excluded member keeps its copy of the retired token, so
    everything depends on the endpoints that rotated stopping to honour it — and a restart nobody is told to run
    would leave that member reading in the meantime.
    """
    assert transport.client.info() == PEER_INFO

    transport.stub.token = 'the-rotated-token'

    with pytest.raises(CollabRequestError) as excinfo:
        transport.client.info()

    assert excinfo.value.status == HTTPStatus.UNAUTHORIZED
    assert 'verdi collab rekey' in str(excinfo.value)


def test_signal_retired(transport):
    """The rotation signal reaches the peer and hands it the identity of whoever rotated, and nothing more."""
    transport.client.signal_retired('uuid-of-the-rotator')

    assert transport.stub.retirements == ['uuid-of-the-rotator']


def test_signal_retired_refuses_a_foreign_collab(transport):
    """A signal presenting another collab is refused like every other request that does."""
    with CollabClient(transport.url, TOKEN, collab='uuid-of-another-collab', timeout=10) as client:
        with pytest.raises(CollabRequestError) as excinfo:
            client.signal_retired('uuid-of-the-rotator')

    assert excinfo.value.status == HTTPStatus.CONFLICT
    assert transport.stub.retirements == []


@pytest.mark.parametrize(
    'method, route',
    [
        ('POST', ROUTE_MISSING),
        ('HEAD', route_upload('b' * 64)),
        ('PUT', route_upload('b' * 64)),
        ('POST', route_import('b' * 64)),
    ],
)
def test_the_push_data_path_refuses_a_foreign_collab(transport, method, route):
    """Every route a push carries its payload over is refused, not only the handshake a client is free to skip.

    Parametrised because the claim is that ``_dispatch`` covers these routes uniformly rather than that four
    handlers each remembered to check: two of them carry no ``collab`` field and ``PUT`` carries no body at all.
    """
    response = requests.request(
        method,
        f'{transport.url}{route}',
        headers={'Authorization': f'Bearer {TOKEN}', HEADER_COLLAB: 'uuid-of-another-collab'},
        data=UPLOAD[:64] if method == 'PUT' else None,
        timeout=10,
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert transport.stub.diffed == []
    assert transport.stub.imported == []
    assert list(transport.staging_dir.iterdir()) == []


def test_a_refused_upload_closes_the_connection(transport):
    """A refused ``PUT /upload`` announces and performs a close, because the body it promised was never read.

    The refusal comes before the handler, so the bytes the client is still sending are never consumed: a 409 that
    left the connection open would leave that client parsing its own unread payload as the next response. Both
    halves are asserted, because a socket that closes without saying so is one a pooling client still reuses.
    """
    sha256 = 'c' * 64
    host, port = transport.url.removeprefix('http://').split(':')
    request = (
        f'PUT {route_upload(sha256)} HTTP/1.1\r\n'
        f'Host: {host}:{port}\r\n'
        f'Authorization: Bearer {TOKEN}\r\n'
        f'{HEADER_COLLAB}: uuid-of-another-collab\r\n'
        'Content-Range: bytes 0-63/64\r\n'
        'Content-Length: 64\r\n'
        '\r\n'
    ).encode()
    answer = b''

    with socket.create_connection((host, int(port)), timeout=10) as connection:
        connection.sendall(request)

        # Reads to end of stream: the endpoint answering a body it never asked for is only half of the property,
        # and this loop would hang until the timeout if the socket were left open for another request.
        while chunk := connection.recv(4096):
            answer += chunk

    assert answer.startswith(b'HTTP/1.1 409')
    assert b'Connection: close' in answer
    assert not (transport.staging_dir / sha256).exists()


def test_an_unknown_route_refuses_a_foreign_collab(transport):
    """A route this endpoint does not serve is refused 409 rather than 404 when the collab is foreign.

    The check runs before routing, which is what makes "every route added after it is covered" true rather than
    a promise the next route has to remember to keep.
    """
    response = requests.get(
        f'{transport.url}{API_PREFIX}/added-by-a-later-phase',
        headers={'Authorization': f'Bearer {TOKEN}', HEADER_COLLAB: 'uuid-of-another-collab'},
        timeout=10,
    )

    assert response.status_code == HTTPStatus.CONFLICT


def test_download(transport, tmp_path):
    """The negotiated delta downloads in full and byte-identical."""
    offer = transport.client.request_delta(None, frozenset(), frozenset())
    filepath = tmp_path / 'download.aiida'
    transferred = transport.client.download_delta(filepath, offer.delta)

    assert transferred == len(DELTA)
    assert filepath.read_bytes() == DELTA


def test_download_resume(transport, tmp_path):
    """A download interrupted at N bytes and resumed transfers only the rest and yields a byte-identical file."""
    offer = transport.client.request_delta(None, frozenset(), frozenset())
    filepath = tmp_path / 'download.aiida'
    transport.client.download_delta(filepath, offer.delta)

    offset = len(DELTA) // 3
    with filepath.open('rb+') as handle:
        handle.truncate(offset)

    transferred = transport.client.download_delta(filepath, offer.delta)

    assert transferred == len(DELTA) - offset
    assert filepath.read_bytes() == DELTA


def test_download_reports_what_it_transfers(transport, tmp_path):
    """The download callback adds up to the whole delta, and on a resumption to the part that still travelled."""
    offer = transport.client.request_delta(None, frozenset(), frozenset())
    filepath = tmp_path / 'download.aiida'
    chunks: list[int] = []

    transport.client.download_delta(filepath, offer.delta, progress=chunks.append)

    assert sum(chunks) == len(DELTA)

    offset = len(DELTA) // 3
    with filepath.open('rb+') as handle:
        handle.truncate(offset)

    resumed: list[int] = []
    transport.client.download_delta(filepath, offer.delta, progress=resumed.append)

    assert sum(resumed) == len(DELTA) - offset


def test_download_resume_stale(transport, tmp_path):
    """A resumption after the peer produced a new delta starts over instead of splicing two files."""
    offer = transport.client.request_delta(None, frozenset(), frozenset())
    filepath = tmp_path / 'download.aiida'
    transport.client.download_delta(filepath, offer.delta)

    with filepath.open('rb+') as handle:
        handle.truncate(1000)

    stale_delta = b'a brand new delta' * 100
    transport.stub.delta_path.write_bytes(stale_delta)

    transferred = transport.client.download_delta(filepath, offer.delta)

    assert transferred == len(stale_delta)
    assert filepath.read_bytes() == stale_delta


def test_download_already_complete(transport, tmp_path):
    """Re-requesting a finished download transfers zero bytes, leaves the file untouched and reads nothing.

    The range it asks for is one the peer cannot satisfy because the client already holds every byte, so the
    audit row belongs to the download that fetched them and not to the client saying so.
    """
    offer = transport.client.request_delta(None, frozenset(), frozenset())
    filepath = tmp_path / 'download.aiida'
    transport.client.download_delta(filepath, offer.delta)

    assert transport.client.download_delta(filepath, offer.delta) == 0
    assert filepath.read_bytes() == DELTA
    assert transport.stub.serves == [(offer.delta, PEER)], 'a range already satisfied is not a second reading'


def test_a_completed_download_ends_the_session(transport, tmp_path):
    """A download served to the end of the file frees the slot behind it without waiting to be told."""
    offer = transport.client.request_delta(None, frozenset(), frozenset())
    transport.client.download_delta(tmp_path / 'download.aiida', offer.delta)

    assert transport.stub.released == [PEER]


def test_negotiate_delta(transport):
    """The negotiation relays the cursor and claim to the sync core and returns its manifest."""
    cursor = timezone.now()
    claim = frozenset({'uuid-one', 'uuid-two'})

    manifest = transport.client.negotiate_delta(cursor, claim)

    assert transport.stub.negotiated == [(cursor, claim)]
    assert manifest.manifest == transport.stub.manifest
    assert manifest.instant == transport.stub.instant


def test_request_delta(transport):
    """The request relays cursor, claim, the wanted subset, the refusal and the manifest's own export instant."""
    cursor = timezone.now()
    claim = frozenset({'uuid-held'})
    want = frozenset({'uuid-wanted'})
    refuse = frozenset({'uuid-deleted'})
    negotiated = timezone.now()

    offer = transport.client.request_delta(cursor, claim, want, frozenset({'uuid-stale'}), refuse, negotiated)

    assert transport.stub.requested == [(cursor, claim, want, refuse)]
    assert transport.stub.instants == [negotiated], 'the export serves only the computation the want was diffed with'
    assert offer.delta == delta_id(cursor, claim, want, refuse)
    assert offer.instant == transport.stub.instant
    assert offer.size == len(DELTA)
    assert [(snapshot.uuid, snapshot.mtime, snapshot.extras) for snapshot in offer.refresh] == [
        ('uuid-stale', transport.stub.instant, {'k': 1})
    ], 'the extras snapshots of the requested refreshes travel with the offer'


def test_the_delta_requests_get_the_time_an_export_takes(transport, tmp_path):
    """The two delta requests wait as long as a serving slot lives; every other route keeps the plain timeout.

    The endpoint computes the delta and exports its archive while those two are open, and holds one lock across
    both, so a first pull of a large profile times out client-side *systematically* under the plain timeout — the
    orphaned handler finishes and caches, so only the retry ever succeeds — and a second peer queued behind it
    starves into a connection error instead of the busy answer the slot machinery promises.
    """
    transport.stub.delay = 0.5

    with CollabClient(transport.url, TOKEN, collab=COLLAB, peer=PEER, timeout=0.2) as client:
        with pytest.raises(CollabRequestError):
            client.push_handshake(PEER)

        assert client.negotiate_delta(None, frozenset()).manifest == transport.stub.manifest

        offer = client.request_delta(None, frozenset(), frozenset({'uuid-wanted'}))

        assert offer.size == len(DELTA)
        # The download too: resolving a delta waits on the lock an export holds, so under the plain timeout a
        # peer queued behind one gets a read timeout reported as the peer being unreachable.
        assert client.download_delta(tmp_path / 'download.aiida', offer.delta) == len(DELTA)


def test_release_ends_the_session_of_the_requester(transport):
    """The requester of a negotiation is named by its header, and is who the release frees the slots of."""
    transport.client.negotiate_delta(None, frozenset())
    transport.client.release()

    assert transport.stub.requesters == [PEER]
    assert transport.stub.released == [PEER]


def test_a_request_without_the_peer_header_is_served(transport):
    """A client that names no session is served under the anonymous one rather than refused.

    The header names a session and authorizes nothing — the token and the collab UUID do that — so treating it
    as required would turn a client that omits it into a lockout.
    """
    response = requests.post(
        f'{transport.url}{ROUTE_DELTA}',
        headers={'Authorization': f'Bearer {TOKEN}', HEADER_COLLAB: COLLAB},
        json={'cursor': None, 'claim': []},
        timeout=10,
    )

    assert response.status_code == HTTPStatus.OK
    assert transport.stub.requesters == ['']


def test_diff_manifest(transport):
    """The manifest, the edited extras and the memberships offered before a push reach the sync core."""
    mtime = timezone.now()
    members = [GroupMembers(uuid='uuid-of-group', label='curated', type_string='', nodes=['uuid-held'])]

    diff = transport.client.diff_manifest(['uuid-one', 'uuid-two'], {'uuid-edited': mtime}, members)

    assert diff.missing == ['uuid-missing']
    assert diff.refresh == ['uuid-edited']
    assert diff.refuse == ['uuid-deleted'], 'what the receiver deleted has to reach the sender that must cut it out'
    assert diff.members == members, 'the membership offer has to survive the round trip over the wire'
    assert transport.stub.diffed == [['uuid-one', 'uuid-two']]


def test_download_unknown_delta(transport, tmp_path):
    """Requesting a delta that is not on offer, such as after an endpoint restart, is a clean 404."""
    with pytest.raises(CollabRequestError) as excinfo:
        transport.client.download_delta(tmp_path / 'download.aiida', '0' * 64)

    assert excinfo.value.status == HTTPStatus.NOT_FOUND


def test_push_handshake(transport):
    """The handshake relays the requester to the sync core and returns what the receiver holds of it."""
    cursor = timezone.now()
    transport.stub.push_handshake = PushHandshake(busy=False, cursor=cursor, claim=['uuid-held'])

    handshake = transport.client.push_handshake('http://pusher:9137')

    assert transport.stub.handshakes == ['http://pusher:9137']
    assert handshake == PushHandshake(busy=False, cursor=cursor, claim=['uuid-held'])


def test_push_handshake_busy(transport):
    """A busy receiver is reported as such, before anything is uploaded."""
    transport.stub.push_handshake = PushHandshake(busy=True, cursor=None, claim=[])

    assert transport.client.push_handshake('http://pusher:9137').busy is True


def test_push_handshake_requires_requester(transport):
    """A handshake without a requester is rejected: the receiver could not know whose cursor to serve."""
    response = requests.post(
        f'{transport.url}{ROUTE_HANDSHAKE}',
        headers={'Authorization': f'Bearer {TOKEN}', HEADER_COLLAB: COLLAB},
        json={},
        timeout=10,
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert transport.stub.handshakes == []


def test_info_relays_cursor(transport):
    """The cursor passed to the info request reaches the sync core, and its absence arrives as ``None``."""
    cursor = timezone.now()
    transport.client.info(cursor)
    transport.client.info()

    assert transport.stub.info_cursors == [cursor, None]


def test_import_requires_peer_and_instant(transport, tmp_path):
    """An import request without the identity and instant of the push is rejected before touching the staging."""
    filepath = tmp_path / 'upload.aiida'
    filepath.write_bytes(UPLOAD)
    report = transport.client.upload_delta(filepath)

    response = requests.post(
        f'{transport.url}{route_import(report.sha256)}',
        headers={'Authorization': f'Bearer {TOKEN}', HEADER_COLLAB: COLLAB},
        timeout=10,
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert transport.stub.imported == []
    assert (transport.staging_dir / report.sha256).exists()


def test_upload(transport, tmp_path):
    """A delta uploads in full, is staged under its checksum, and tells the endpoint its sender is still there.

    The last of those is what keeps a transfer longer than a serving slot lives from losing the slot while it is
    actively sending. It is asserted here rather than in a test of its own because it is a property of the
    upload: reached through the real probe and chunk requests, not by calling the hook.
    """
    filepath = tmp_path / 'upload.aiida'
    filepath.write_bytes(UPLOAD)

    report = transport.client.upload_delta(filepath)

    assert report.sent == len(UPLOAD)
    assert report.staged == len(UPLOAD)
    assert (transport.staging_dir / report.sha256).read_bytes() == UPLOAD
    assert transport.stub.stagings == [PEER, PEER], 'the probe and the chunk each refresh the slot of the sender'


def test_upload_resume(transport, tmp_path):
    """An interrupted upload resumes from the bytes the peer already staged."""
    filepath = tmp_path / 'upload.aiida'
    filepath.write_bytes(UPLOAD)

    offset = len(UPLOAD) // 3
    (transport.staging_dir / file_sha256(filepath)).write_bytes(UPLOAD[:offset])

    report = transport.client.upload_delta(filepath)

    assert report.sent == len(UPLOAD) - offset
    assert report.staged == len(UPLOAD)
    assert (transport.staging_dir / report.sha256).read_bytes() == UPLOAD


def test_upload_reports_what_it_sends(transport, tmp_path):
    """The upload callback adds up to the bytes that travelled, which on a resumption is not the whole file."""
    filepath = tmp_path / 'upload.aiida'
    filepath.write_bytes(UPLOAD)

    offset = len(UPLOAD) // 3
    (transport.staging_dir / file_sha256(filepath)).write_bytes(UPLOAD[:offset])

    blocks: list[int] = []
    report = transport.client.upload_delta(filepath, progress=blocks.append)

    assert sum(blocks) == report.sent == len(UPLOAD) - offset
    assert (transport.staging_dir / report.sha256).read_bytes() == UPLOAD, 'the reporting must not eat a byte'


def test_upload_already_staged(transport, tmp_path):
    """Re-uploading a fully staged delta transfers zero bytes and reports the staged size."""
    filepath = tmp_path / 'upload.aiida'
    filepath.write_bytes(UPLOAD)
    transport.client.upload_delta(filepath)

    report = transport.client.upload_delta(filepath)

    assert report.sent == 0
    assert report.staged == len(UPLOAD)


def test_import_staged(transport, tmp_path):
    """A staged upload imports on request, relays the report and is cleaned up afterwards."""
    filepath = tmp_path / 'upload.aiida'
    filepath.write_bytes(UPLOAD)
    report = transport.client.upload_delta(filepath)

    instant = timezone.now()
    members = [GroupMembers(uuid='uuid-of-group', label='curated', type_string='', nodes=['uuid-held'])]

    assert transport.client.trigger_import(
        report.sha256, peer='http://pusher:9137', instant=instant, members=members
    ) == {'imported': 7}
    assert transport.stub.imported == [('http://pusher:9137', instant, UPLOAD)]
    assert transport.stub.applied == members, 'the memberships the receiver asked for ride the import request'
    assert not (transport.staging_dir / report.sha256).exists()


def test_import_failure_keeps_staged(transport, tmp_path):
    """A failed import keeps the staged file, so the retry uploads zero bytes and repeats only the import."""
    filepath = tmp_path / 'upload.aiida'
    filepath.write_bytes(UPLOAD)
    report = transport.client.upload_delta(filepath)

    transport.stub.import_exception = RuntimeError('database is locked')
    instant = timezone.now()

    with pytest.raises(CollabRequestError, match='database is locked'):
        transport.client.trigger_import(report.sha256, peer='http://pusher:9137', instant=instant)

    assert (transport.staging_dir / report.sha256).exists()

    transport.stub.import_exception = None
    retry = transport.client.upload_delta(filepath)

    assert retry.sent == 0
    assert transport.client.trigger_import(retry.sha256, peer='http://pusher:9137', instant=instant) == {'imported': 7}


def test_import_unresolvable_delta_discards_staged(transport, tmp_path):
    """An import that can never land is answered 422 and the staged file is discarded, forcing a renegotiation."""
    from aiida.common.exceptions import IntegrityError

    filepath = tmp_path / 'upload.aiida'
    filepath.write_bytes(UPLOAD)
    report = transport.client.upload_delta(filepath)

    transport.stub.import_exception = IntegrityError('refusing to import the delta: it links to node gone-uuid')

    with pytest.raises(CollabRequestError) as excinfo:
        transport.client.trigger_import(report.sha256, peer='http://pusher:9137', instant=timezone.now())

    assert excinfo.value.status == HTTPStatus.UNPROCESSABLE_ENTITY
    assert 'gone-uuid' in str(excinfo.value)
    assert not (transport.staging_dir / report.sha256).exists(), 'the unusable staged upload should be discarded'


def test_import_checksum_mismatch(transport):
    """A staged file that does not match its checksum is rejected and dropped, forcing a fresh upload."""
    sha256 = 'a' * 64
    (transport.staging_dir / sha256).write_bytes(b'corrupted bytes')

    with pytest.raises(CollabRequestError, match='checksum'):
        transport.client.trigger_import(sha256, peer='http://pusher:9137', instant=timezone.now())

    assert not (transport.staging_dir / sha256).exists()
    assert transport.stub.imported == []


def test_version_skew_ignores_storage(transport):
    """A newer storage schema on another backend is no obstacle: only the archive format has to be readable.

    ``LOCAL_INFO`` and ``PEER_INFO`` already run different storage backends, so this covers both halves of the
    "storage is a local concern" decision.
    """
    transport.stub.peer_info = replace(PEER_INFO, storage_schema='main_0099')

    assert transport.client.check_version_skew(LOCAL_INFO, direction='pull') == transport.stub.peer_info
    assert transport.client.check_version_skew(LOCAL_INFO, direction='push') == transport.stub.peer_info


def test_version_skew_pull_from_newer_peer(transport):
    """A pull from a peer writing an archive format this profile cannot read is refused, telling it to upgrade."""
    transport.stub.peer_info = replace(PEER_INFO, version='3.1.0', archive_schema='main_0099')

    with pytest.raises(VersionSkew) as excinfo:
        transport.client.check_version_skew(LOCAL_INFO, direction='pull')

    message = str(excinfo.value)
    assert '3.1.0' in message
    assert 'main_0099' in message
    assert 'please upgrade it' in message

    # The other direction is unaffected: the peer reads everything this profile writes.
    assert transport.client.check_version_skew(LOCAL_INFO, direction='push') == transport.stub.peer_info


def test_version_skew_push_to_older_peer(transport):
    """A push the peer could not read is refused, with the message aimed at the collaborator who has to upgrade."""
    transport.stub.peer_info = replace(PEER_INFO, version='2.5.0', archive_schema='main_0000')

    with pytest.raises(VersionSkew) as excinfo:
        transport.client.check_version_skew(LOCAL_INFO, direction='push')

    message = str(excinfo.value)
    assert 'main_0000' in message
    assert 'ask your collaborator' in message

    # Pulling from it stays allowed: its older archives are migrated forward on import.
    assert transport.client.check_version_skew(LOCAL_INFO, direction='pull') == transport.stub.peer_info
