###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The wire protocol spoken between the collab endpoint of a profile and the clients of its peers."""

from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from aiida.common.exceptions import AiidaException

API_PREFIX = '/collab/v1'
ROUTE_INFO = f'{API_PREFIX}/info'
ROUTE_DELTA = f'{API_PREFIX}/delta'
ROUTE_HANDSHAKE = f'{API_PREFIX}/handshake'
ROUTE_MISSING = f'{API_PREFIX}/missing'

HEADER_STAGED = 'X-Collab-Staged-Bytes'

UNAUTHORIZED_DETAIL = 'the token presented is not the one this collab uses'
"""Answered to every request that fails to authenticate."""

CHUNK_SIZE = 1024 * 1024


class CollabRequestError(AiidaException):
    """A request to the collab endpoint of a peer failed."""

    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


def route_delta(delta_id: str) -> str:
    """Return the route at which the negotiated delta with the given identifier is served."""
    return f'{ROUTE_DELTA}/{delta_id}'


def delta_id(
    cursor: datetime | None, claim: frozenset[str] | set[str], want: frozenset[str] | set[str] | None = None
) -> str:
    """Return the identifier of the delta a cursor, claim and requested subset negotiate.

    Derived from the request alone, so a client that re-negotiates after an interrupted download is offered the
    same identifier and can resume, and the sender can key its cache of exported deltas by it.
    """
    key = json.dumps(
        [
            cursor.isoformat() if cursor is not None else None,
            sorted(claim),
            sorted(want) if want is not None else None,
        ]
    )

    return hashlib.sha256(key.encode('utf-8')).hexdigest()


def route_upload(sha256: str) -> str:
    """Return the route at which the upload with the given checksum is staged."""
    return f'{API_PREFIX}/upload/{sha256}'


def route_import(sha256: str) -> str:
    """Return the route that imports the staged upload with the given checksum."""
    return f'{API_PREFIX}/import/{sha256}'


def file_sha256(filepath: Path) -> str:
    """Return the hexadecimal SHA-256 checksum of a file."""
    digest = hashlib.sha256()

    with filepath.open('rb') as handle:
        while chunk := handle.read(CHUNK_SIZE):
            digest.update(chunk)

    return digest.hexdigest()


@dataclass
class PeerInfo:
    """The handshake a collab endpoint serves about its profile."""

    version: str
    """The aiida-core version of the peer."""

    backend: str
    """The entry point name of the storage backend of the peer."""

    storage_schema: str
    """The schema version of the storage of the peer."""

    archive_schema: str
    """The latest archive format version the peer can write."""

    pending_count: int
    """An estimate of what a sync would deliver: the sealed processes and imported nodes the peer gained since the
    cursor presented with the request, or everything when none was."""

    accept_push: bool
    """Whether the peer accepts pushes."""

    def as_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PeerInfo:
        # The handshake has to survive version skew, since detecting it is its very purpose: a newer peer may
        # serve fields this version does not know, so unknown keys are ignored rather than an error.
        names = {field.name for field in dataclasses.fields(cls)}

        return cls(**{key: value for key, value in data.items() if key in names})


@dataclass
class DeltaManifest:
    """The first answer to a delta negotiation: which nodes the delta for the presented cursor and claim holds.

    The manifest is provenance-closed and cheap — no archive is built for it. The requester diffs it against its
    own nodes and requests only the subset it lacks, which is what keeps already-held ancestors off the wire.
    """

    manifest: list[str]
    instant: datetime

    def as_dict(self) -> dict[str, Any]:
        return {
            'manifest': self.manifest,
            'instant': self.instant.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeltaManifest:
        return cls(
            manifest=data['manifest'],
            instant=datetime.fromisoformat(data['instant']),
        )


@dataclass
class ManifestDiff:
    """The answer of a receiver to a manifest a pushing peer offers it: what of it the receiver does not have."""

    missing: list[str]
    """The UUIDs of the offered nodes the receiver holds nowhere; only those are exported and uploaded."""

    def as_dict(self) -> dict[str, Any]:
        return {'missing': self.missing}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ManifestDiff:
        return cls(missing=data['missing'])


@dataclass
class DeltaOffer:
    """The answer to a delta negotiation: what the sender exported for the presented cursor and claim."""

    delta: str
    """The identifier under which the delta is served, from ``delta_id``."""

    instant: datetime
    """The export instant the requester stores as its cursor for the sender once the import succeeds."""

    size: int
    """The size of the delta archive in bytes."""

    def as_dict(self) -> dict[str, Any]:
        return {'delta': self.delta, 'instant': self.instant.isoformat(), 'size': self.size}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeltaOffer:
        return cls(delta=data['delta'], instant=datetime.fromisoformat(data['instant']), size=data['size'])


@dataclass
class PushHandshake:
    """The answer of a receiver to a peer that wants to push: what it already holds of that peer.

    The pusher exports its delta bounded by this cursor and claim, exactly as it would serve a pull presenting them.
    """

    busy: bool
    """Whether the receiver is importing right now; the pusher retries once the import released the lock."""

    cursor: datetime | None
    """The export instant of the last delta the receiver imported from the pusher, or ``None`` for none."""

    claim: list[str]
    """UUIDs the receiver already holds, which the sender subtracts from what it would send."""

    def as_dict(self) -> dict[str, Any]:
        return {
            'busy': self.busy,
            'cursor': self.cursor.isoformat() if self.cursor is not None else None,
            'claim': self.claim,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PushHandshake:
        return cls(
            busy=data['busy'],
            cursor=datetime.fromisoformat(data['cursor']) if data['cursor'] is not None else None,
            claim=data['claim'],
        )
