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
from typing import TYPE_CHECKING, Any

from aiida.common.exceptions import AiidaException

if TYPE_CHECKING:
    from aiida.manage.configuration.config import CollabExtrasMode, CollabGroupsMode, CollabPolicy

API_PREFIX = '/collab/v1'
ROUTE_INFO = f'{API_PREFIX}/info'
ROUTE_DELTA = f'{API_PREFIX}/delta'
ROUTE_HANDSHAKE = f'{API_PREFIX}/handshake'
ROUTE_MISSING = f'{API_PREFIX}/missing'
ROUTE_JOIN = f'{API_PREFIX}/join'
ROUTE_RETIRED = f'{API_PREFIX}/retired'

HEADER_STAGED = 'X-Collab-Staged-Bytes'

REKEY_HINT = 'obtain the current join code from a member and run `verdi collab rekey <code>`'
"""What a member whose token was retired has to do, said by the advisory signal a rotation sends and offered by
the 401 of every endpoint that rotated. That 401 is what enforces a rotation, and the only thing that does — the
signal is authenticated by the very token being retired, which an excluded member also still holds, so it must
never trigger an action of its own."""

UNAUTHORIZED_DETAIL = f'the token presented is not the one this collab uses. If its key was rotated, {REKEY_HINT}'
"""Answered to every request that fails to authenticate. It cannot claim a rotation: the same 401 answers a
mistyped join code, and the endpoint has no way to tell the two apart."""

CHUNK_SIZE = 1024 * 1024


class CollabRequestError(AiidaException):
    """A request to the collab endpoint of a peer failed."""

    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


class VersionSkew(AiidaException):
    """A delta cannot travel between two peers, because one of them cannot read the archives the other writes."""


@dataclass
class JoinCode:
    """The single code a newcomer needs to join a collab: which collab, whom to ask, the key, and the terms.

    Any member can mint one — after creation the creator is nobody special — so a newcomer joins through whichever
    member happens to be online.
    """

    collab: str
    """The UUID of the collab, which the joiner pins and every later handshake is held against."""

    url: str
    """The endpoint URL of the member that issued the code."""

    token: str
    """The shared secret of the collab."""

    policy: CollabPolicy
    """What the collab shares beyond provenance nodes, fixed at its creation. It travels here because joining is
    the one moment at which it can still be declined: the consent has to precede the profile it governs."""

    def encode(self) -> str:
        """Return the code as one opaque string, to be shared out of band."""
        import base64

        payload = json.dumps(
            {'collab': self.collab, 'url': self.url, 'token': self.token, 'policy': self.policy}
        ).encode('utf-8')

        return base64.urlsafe_b64encode(payload).decode('ascii').rstrip('=')

    @classmethod
    def decode(cls, code: str) -> JoinCode:
        """Parse a join code.

        :raises ValueError: when the code is not one, which is the only thing a user can mistype here.
        """
        import base64
        import binascii
        from typing import get_args

        from aiida.manage.configuration.config import CollabExtrasMode, CollabGroupsMode

        stripped = code.strip()

        try:
            payload = base64.urlsafe_b64decode(stripped + '=' * (-len(stripped) % 4))
            data = json.loads(payload)
            policy = data['policy']

            # The values are checked here, not where the policy is written: writing it is the step *after* the
            # profile is created, so a code naming a mode nobody offers would abort the join with a half-made
            # profile left behind and the retry refusing to reuse its name.
            modes = {'extras_mode': get_args(CollabExtrasMode), 'groups_mode': get_args(CollabGroupsMode)}

            if set(policy) != set(modes) or any(policy[key] not in values for key, values in modes.items()):
                msg = f'it declares a policy this version does not understand: {policy}'
                raise ValueError(msg)

            return cls(collab=data['collab'], url=data['url'], token=data['token'], policy=policy)
        except (binascii.Error, KeyError, TypeError, UnicodeDecodeError, ValueError) as exception:
            msg = f'`{code}` is not a valid join code: {exception}'
            raise ValueError(msg) from exception


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

    extras_mode: CollabExtrasMode
    """How the collab treats extras: ``local`` keeps them private to each profile, ``sync`` replicates them."""

    groups_mode: CollabGroupsMode
    """How the collab treats groups."""

    uuid: str | None = None
    """The UUID of the profile behind the endpoint: its stable identity across the collab, under which cursors are
    kept regardless of how its URL is spelled or changes."""

    collab: str = ''
    """The UUID of the collab the peer takes part in. A contact presenting another one is refused: the token alone
    must not be able to splice two collabs into one."""

    def as_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PeerInfo:
        # The handshake has to survive version skew, since detecting it is its very purpose: a newer peer may
        # serve fields this version does not know, so unknown keys are ignored rather than an error.
        names = {field.name for field in dataclasses.fields(cls)}

        return cls(**{key: value for key, value in data.items() if key in names})


@dataclass
class ExtrasSnapshot:
    """The extras of one shared node as its sender holds them, with the mtime that decides whose version wins.

    The mtime travels with the snapshot and is written as the receiver's own: a refresh must never make the
    receiver the newer side, or the two would echo the same extras back and forth forever.
    """

    uuid: str
    mtime: datetime
    extras: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {'uuid': self.uuid, 'mtime': self.mtime.isoformat(), 'extras': self.extras}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExtrasSnapshot:
        return cls(uuid=data['uuid'], mtime=datetime.fromisoformat(data['mtime']), extras=data['extras'])


def refresh_as_dict(refresh: dict[str, datetime]) -> dict[str, str]:
    """Serialize an offer of extras refreshes: the mtime this profile holds for each shared node it may have edited."""
    return {uuid: mtime.isoformat() for uuid, mtime in refresh.items()}


def refresh_from_dict(data: dict[str, str]) -> dict[str, datetime]:
    """Parse an offer of extras refreshes."""
    return {uuid: datetime.fromisoformat(mtime) for uuid, mtime in data.items()}


@dataclass
class DeltaManifest:
    """The first answer to a delta negotiation: which nodes the delta for the presented cursor and claim holds.

    The manifest is provenance-closed and cheap — no archive is built for it. The requester diffs it against its
    own nodes and requests only the subset it lacks, which is what keeps already-held ancestors off the wire.
    """

    manifest: list[str]
    instant: datetime
    refresh: dict[str, datetime] = dataclasses.field(default_factory=dict)
    """Under the ``sync`` extras policy, the mtime the sender holds for each shared node whose extras it may have
    edited since the presented cursor. The requester keeps the ones it holds an older version of and asks for their
    extras with the export request; under ``local`` the offer is empty."""

    roster: list[dict[str, Any]] = dataclasses.field(default_factory=list)
    """The sender's own roster entry and every peer it knows, so that membership spreads with every sync."""

    def as_dict(self) -> dict[str, Any]:
        return {
            'manifest': self.manifest,
            'instant': self.instant.isoformat(),
            'refresh': refresh_as_dict(self.refresh),
            'roster': self.roster,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeltaManifest:
        return cls(
            manifest=data['manifest'],
            instant=datetime.fromisoformat(data['instant']),
            refresh=refresh_from_dict(data['refresh']),
            roster=data.get('roster', []),
        )


@dataclass
class ManifestDiff:
    """The answer of a receiver to a manifest a pushing peer offers it: what of it the receiver does not have."""

    missing: list[str]
    """The UUIDs of the offered nodes the receiver holds nowhere; only those are exported and uploaded."""

    refresh: list[str]
    """The nodes whose extras the receiver holds an older version of, and whose snapshot it wants with the push."""

    def as_dict(self) -> dict[str, Any]:
        return {'missing': self.missing, 'refresh': self.refresh}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ManifestDiff:
        return cls(missing=data['missing'], refresh=data['refresh'])


@dataclass
class DeltaOffer:
    """The answer to a delta negotiation: what the sender exported for the presented cursor and claim."""

    delta: str
    """The identifier under which the delta is served, from ``delta_id``."""

    instant: datetime
    """The export instant the requester stores as its cursor for the sender once the import succeeds."""

    size: int
    """The size of the delta archive in bytes."""

    refresh: list[ExtrasSnapshot] = dataclasses.field(default_factory=list)
    """The extras snapshots the requester asked for after diffing the manifest's refresh offer."""

    def as_dict(self) -> dict[str, Any]:
        return {
            'delta': self.delta,
            'instant': self.instant.isoformat(),
            'size': self.size,
            'refresh': [snapshot.as_dict() for snapshot in self.refresh],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeltaOffer:
        return cls(
            delta=data['delta'],
            instant=datetime.fromisoformat(data['instant']),
            size=data['size'],
            refresh=[ExtrasSnapshot.from_dict(snapshot) for snapshot in data['refresh']],
        )


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
    """UUIDs the receiver already holds, including its tombstones, which keeps deletions out of re-delivery."""

    roster: list[dict[str, Any]] = dataclasses.field(default_factory=list)
    """The receiver's own roster entry and every peer it knows, so that membership spreads with every sync."""

    def as_dict(self) -> dict[str, Any]:
        return {
            'busy': self.busy,
            'cursor': self.cursor.isoformat() if self.cursor is not None else None,
            'claim': self.claim,
            'roster': self.roster,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PushHandshake:
        return cls(
            busy=data['busy'],
            cursor=datetime.fromisoformat(data['cursor']) if data['cursor'] is not None else None,
            claim=data['claim'],
            roster=data.get('roster', []),
        )


@dataclass
class JoinResponse:
    """The answer of the member that issued a join code to the newcomer presenting it."""

    collab: str
    """The UUID of the collab, which the joiner holds against the one its code carried."""

    roster: list[dict[str, Any]]
    """Every peer the issuer knows, its own entry included: the newcomer starts with the full membership."""

    def as_dict(self) -> dict[str, Any]:
        return {'collab': self.collab, 'roster': self.roster}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> JoinResponse:
        return cls(collab=data['collab'], roster=data['roster'])
