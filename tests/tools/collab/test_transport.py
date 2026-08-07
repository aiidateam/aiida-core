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
from dataclasses import dataclass
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
    delta_id,
    file_sha256,
    route_delta,
    route_import,
    route_upload,
)
from aiida.tools.collab.server import CollabServer

TOKEN = 'the-collab-token'

DELTA = bytes(range(256)) * 1024
UPLOAD = bytes(reversed(range(256))) * 512

PEER_INFO = PeerInfo(
    version='2.9.0',
    backend='core.sqlite_dos',
    storage_schema='main_0002',
    archive_schema='main_0001',
    pending_count=3,
    accept_push=True,
)


class StubSyncCore:
    """Stands in for the sync core: a fixed-bytes delta, recorded imports and a configurable handshake."""

    def __init__(self, delta_path: Path):
        self.delta_path = delta_path
        self.peer_info = PEER_INFO
        self.push_handshake = PushHandshake(busy=False, cursor=None, claim=[])
        self.manifest = ['uuid-offered']
        self.missing = ['uuid-missing']
        self.instant = timezone.now()
        self.import_exception: Exception | None = None
        self.negotiated: list[tuple[datetime | None, frozenset]] = []
        self.requested: list[tuple[datetime | None, frozenset, frozenset]] = []
        self.diffed: list[list[str]] = []
        self.handshakes: list[str] = []
        self.token = TOKEN
        self.info_cursors: list[datetime | None] = []
        self.imported: list[tuple[str, datetime, bytes]] = []

    def info(self, cursor: datetime | None) -> PeerInfo:
        self.info_cursors.append(cursor)
        return self.peer_info

    def negotiate_delta(self, cursor: datetime | None, claim: frozenset) -> DeltaManifest:
        self.negotiated.append((cursor, claim))
        return DeltaManifest(manifest=self.manifest, instant=self.instant)

    def request_delta(self, cursor: datetime | None, claim: frozenset, want: frozenset) -> DeltaOffer:
        self.requested.append((cursor, claim, want))
        return DeltaOffer(
            delta=delta_id(cursor, claim, want), instant=self.instant, size=self.delta_path.stat().st_size
        )

    def resolve_delta(self, requested_id: str) -> Path | None:
        return self.delta_path if self.delta_path.exists() else None

    def diff_manifest(self, uuids: list) -> ManifestDiff:
        self.diffed.append(uuids)
        return ManifestDiff(missing=self.missing)

    def handshake(self, requester: str) -> PushHandshake:
        self.handshakes.append(requester)
        return self.push_handshake

    def import_staged(self, filepath: Path, peer: str, instant: datetime) -> dict:
        if self.import_exception is not None:
            raise self.import_exception

        self.imported.append((peer, instant, filepath.read_bytes()))
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
        token=stub.token,
        staging_dir=staging_dir,
        info=stub.info,
        negotiate_delta=stub.negotiate_delta,
        request_delta=stub.request_delta,
        resolve_delta=stub.resolve_delta,
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

    with CollabClient(url, TOKEN, timeout=10) as client:
        yield Transport(client=client, stub=stub, staging_dir=staging_dir, url=url)

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

    with pytest.raises(ConfigurationError, match='collab.bind'):
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

        with pytest.raises(ConfigurationError, match='collab.port'):
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
        with CollabClient(endpoint_url('::1', server.server_address[1]), TOKEN, timeout=10) as client:
            assert client.info() == PEER_INFO
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


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


def test_auth_rejected(transport):
    """A request without the correct bearer token returns 401 and never reaches a route handler."""
    routes = [
        ('GET', ROUTE_INFO),
        ('POST', ROUTE_HANDSHAKE),
        ('GET', route_delta('0' * 64)),
        ('POST', ROUTE_DELTA),
        ('POST', ROUTE_MISSING),
        ('HEAD', route_upload('0' * 64)),
        ('PUT', route_upload('0' * 64)),
        ('POST', route_import('0' * 64)),
    ]

    for headers in ({}, {'Authorization': 'Bearer not-the-collab-token'}):
        for method, route in routes:
            response = requests.request(method, f'{transport.url}{route}', headers=headers, timeout=10)
            assert response.status_code == HTTPStatus.UNAUTHORIZED, (method, route)

    assert transport.stub.info_cursors == []
    assert transport.stub.negotiated == []
    assert transport.stub.requested == []
    assert transport.stub.diffed == []
    assert transport.stub.handshakes == []
    assert transport.stub.imported == []


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
    """Re-requesting a finished download transfers zero bytes and leaves the file untouched."""
    offer = transport.client.request_delta(None, frozenset(), frozenset())
    filepath = tmp_path / 'download.aiida'
    transport.client.download_delta(filepath, offer.delta)

    assert transport.client.download_delta(filepath, offer.delta) == 0
    assert filepath.read_bytes() == DELTA


def test_negotiate_delta(transport):
    """The negotiation relays the cursor and claim to the sync core and returns its manifest."""
    cursor = timezone.now()
    claim = frozenset({'uuid-one', 'uuid-two'})

    manifest = transport.client.negotiate_delta(cursor, claim)

    assert transport.stub.negotiated == [(cursor, claim)]
    assert manifest.manifest == transport.stub.manifest
    assert manifest.instant == transport.stub.instant


def test_request_delta(transport):
    """The request relays cursor, claim and the wanted subset, and returns the offer of the cut archive."""
    cursor = timezone.now()
    claim = frozenset({'uuid-held'})
    want = frozenset({'uuid-wanted'})

    offer = transport.client.request_delta(cursor, claim, want)

    assert transport.stub.requested == [(cursor, claim, want)]
    assert offer.delta == delta_id(cursor, claim, want)
    assert offer.instant == transport.stub.instant
    assert offer.size == len(DELTA)


def test_diff_manifest(transport):
    """The manifest offered before a push reaches the sync core."""
    diff = transport.client.diff_manifest(['uuid-one', 'uuid-two'])

    assert diff.missing == ['uuid-missing']
    assert transport.stub.diffed == [['uuid-one', 'uuid-two']]


def test_download_unknown_delta(transport, tmp_path):
    """Requesting a delta that is not on offer, such as after an endpoint restart, is a clean 404."""
    transport.stub.delta_path.unlink()

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
        headers={'Authorization': f'Bearer {TOKEN}'},
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
        headers={'Authorization': f'Bearer {TOKEN}'},
        timeout=10,
    )

    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert transport.stub.imported == []
    assert (transport.staging_dir / report.sha256).exists()


def test_upload(transport, tmp_path):
    """A delta uploads in full and is staged under its checksum."""
    filepath = tmp_path / 'upload.aiida'
    filepath.write_bytes(UPLOAD)

    report = transport.client.upload_delta(filepath)

    assert report.sent == len(UPLOAD)
    assert report.staged == len(UPLOAD)
    assert (transport.staging_dir / report.sha256).read_bytes() == UPLOAD


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

    assert transport.client.trigger_import(report.sha256, peer='http://pusher:9137', instant=instant) == {'imported': 7}
    assert transport.stub.imported == [('http://pusher:9137', instant, UPLOAD)]
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
