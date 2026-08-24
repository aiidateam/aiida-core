###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""A collab of real profiles, each serving a real endpoint and running the real CLI.

The unit tests beside this file drive one layer at a time against stubs. What they cannot show is whether the
layers agree: the endpoint, the CLI, the configuration file every member shares and the state file each keeps are
tested apart and never together. This fixture puts N members on loopback and lets a scenario read like the prose
it tests -- ``a.run('push', ['bob'])``, ``assert c.graph() == a.graph()``.
"""

from __future__ import annotations

import hashlib
import shutil
import threading
import typing as t
from pathlib import Path

import pytest

from aiida import orm
from aiida.common.links import LinkType
from aiida.tools.collab.config import GENERATED_GROUP_TYPES

NICKNAMES = ('alice', 'bob', 'carol', 'dave', 'erin')

# The groups a person curated, as against the ones AiiDA generates to record how provenance arrived here. Only
# the former are shared, and only they belong in a digest two profiles are compared by.
CURATED: dict = {'type_string': {'!in': list(GENERATED_GROUP_TYPES)}}


class Member:
    """One profile of the collab: its storage, its endpoint, and the CLI run as itself."""

    def __init__(self, nickname: str, profile, config, backend):
        self.nickname = nickname
        self.profile = profile
        self.config = config
        self.backend = backend
        """The storage the endpoint serves from, which is a second connection to the same database as the CLI's."""

        self.endpoint = None
        self.server = None
        self._thread = None

    @property
    def uuid(self) -> str:
        return self.profile.uuid

    @property
    def url(self) -> str:
        host, port = self.server.server_address[:2]
        return f'http://{host}:{port}'

    def serve(self, port: int | None = None) -> int:
        """Start this member's endpoint, exactly as :func:`aiida.tools.collab.endpoint.serve` starts it.

        :param port: the port to listen on; ``None`` takes the one the profile has configured, which is what a
            daemon started after ``verdi collab init`` would do.
        :return: the port that was bound, which is what the peers are told.
        """
        from aiida.tools.collab.config import OPTION_BIND, OPTION_PORT, OPTION_TOKEN, OPTION_UUID
        from aiida.tools.collab.endpoint import CollabEndpoint
        from aiida.tools.collab.server import CollabServer

        self.endpoint = CollabEndpoint(self.profile, self.backend)
        self.server = CollabServer(
            self.option(OPTION_BIND),
            self.option(OPTION_PORT) if port is None else port,
            token=lambda: self.option(OPTION_TOKEN),
            collab=self.option(OPTION_UUID),
            staging_dir=self.endpoint.staging_dir,
            info=self.endpoint.info,
            join=self.endpoint.join,
            retired=self.endpoint.retired,
            negotiate_delta=self.endpoint.negotiate_delta,
            request_delta=self.endpoint.request_delta,
            resolve_delta=self.endpoint.resolve_delta,
            release=self.endpoint.release,
            staging=self.endpoint.staging,
            diff_manifest=self.endpoint.diff_manifest,
            handshake=self.endpoint.handshake,
            import_staged=self.endpoint.import_staged,
        )
        self._thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self._thread.start()

        return self.server.server_address[1]

    def rebind(self) -> int:
        """Move this member's endpoint to another port, as a machine that changed address does.

        The port is written to the configuration but the announcement is left alone, which is exactly the state a
        move leaves behind: the next outbound sync is what notices it and raises the stamp.
        """
        from aiida.tools.collab.config import OPTION_PORT

        self.stop()
        port = self.serve(port=0)
        self.set_option(OPTION_PORT, port)

        return port

    def load(self):
        """Make this member's profile the loaded one and return its storage."""
        from aiida.manage import get_manager
        from aiida.manage.configuration import load_profile

        load_profile(self.profile.name, allow_switch=True)

        return get_manager().get_profile_storage()

    def run(self, command: str, args: t.Sequence[str] = (), **kwargs):
        """Run a ``verdi collab`` subcommand as this member, in this interpreter.

        :param command: the subcommand, as it is spelled on the command line: ``pull``, ``peer set``, ...
        """
        from aiida.cmdline.commands.cmd_collab import verdi_collab

        return self.run_verdi(verdi_collab, [*command.split(), *args], **kwargs)

    def run_verdi(self, command, args: t.Sequence[str] = (), *, raises: bool = False, user_input: str | None = None):
        """Run any ``verdi`` command as this member, in this interpreter.

        :param raises: expect a non-zero exit instead of a successful one.
        """
        from click.testing import CliRunner

        from aiida.cmdline.commands.cmd_verdi import VerdiCommandGroup
        from aiida.cmdline.groups.verdi import LazyVerdiObjAttributeDict
        from aiida.manage.configuration import get_config, get_profile

        self.load()

        obj = LazyVerdiObjAttributeDict(None, {'config': get_config()})
        obj.profile = get_profile()

        result = CliRunner().invoke(
            VerdiCommandGroup.add_verbosity_option(command),
            [str(argument) for argument in args],
            obj=obj,
            input=user_input,
            catch_exceptions=True,
        )

        if raises:
            assert result.exit_code != 0, result.output
        else:
            import traceback

            assert result.exit_code == 0, result.output + ''.join(
                traceback.format_exception(*result.exc_info) if result.exception else []
            )

        return result

    def stop(self):
        """Take this member off the network, closing its listening socket."""
        if self.server is None:
            return

        self.server.shutdown()
        self.server.server_close()
        self._thread.join(timeout=10)
        self.server = None
        self._thread = None

    # -- storage helpers, run against the loaded profile so that the collab hooks of the ORM fire.
    # They take and return UUIDs rather than ORM objects: loading another member's profile closes the storage of
    # this one, so a node held across a switch is a closed-storage error waiting to happen.

    def seal_calculation(
        self, label: str = 'calc', inputs: str | None = None, ballast: int = 0, computer: str | None = None
    ) -> str:
        """Store and seal a one-input, one-output calculation, and return the UUID of the node it created.

        :param ballast: bytes of incompressible payload to put in the calculation's repository, for the scenarios
            whose subject is the size of the transfer rather than its content.
        :param computer: label of the computer the calculation ran on, created here if this profile lacks it. A
            calculation carrying one is what makes a computer travel in the delta at all.
        """
        import os

        backend = self.load()

        source = orm.load_node(uuid=inputs) if inputs else orm.Int(1, backend=backend).store()
        machine = orm.Computer.get_collection(backend).get(uuid=self.computer(computer)) if computer else None
        calculation = orm.CalcJobNode(backend=backend, label=label, computer=machine)
        calculation.base.links.add_incoming(source, link_type=LinkType.INPUT_CALC, link_label='term')

        # Every real calculation writes an input file, and without one here no scenario would ever notice an
        # export that streams the rows of a node and none of its repository.
        calculation.base.repository.put_object_from_bytes(f'{label}\n'.encode(), 'aiida.in')

        if ballast:
            calculation.base.repository.put_object_from_bytes(os.urandom(ballast), 'ballast.dat')

        calculation.store()

        created = orm.Int(2, backend=backend)
        created.base.links.add_incoming(calculation, link_type=LinkType.CREATE, link_label='result')
        created.store()
        calculation.seal()

        return created.uuid

    def seal_cached_calculation(self, computer: str) -> str:
        """Store and seal a finished calculation on a named computer, valid as a cache source, and return its UUID.

        Identical on every call and in every profile but for the machine it ran on, which is the whole point: the
        hash of a calculation includes the UUID of that machine, and a computer mapping is what equates two of them.
        """
        from aiida.engine import ProcessState

        backend = self.load()
        machine = orm.Computer.get_collection(backend).get(uuid=self.computer(computer))
        calculation = orm.CalcJobNode(
            backend=backend, computer=machine, process_type='aiida.calculations:core.arithmetic.add'
        )
        calculation.base.links.add_incoming(
            orm.Int(1, backend=backend).store(), link_type=LinkType.INPUT_CALC, link_label='term'
        )
        calculation.base.repository.put_object_from_bytes(b'1 + 1', 'aiida.in')
        calculation.set_process_state(ProcessState.FINISHED)
        calculation.set_exit_status(0)
        calculation.store()
        calculation.seal()

        return calculation.uuid

    def node(self, uuid: str) -> orm.Node:
        """Return a node of this profile by UUID, valid until another member's profile is loaded."""
        self.load()

        return orm.load_node(uuid=uuid)

    def uuids(self) -> set[str]:
        """Return the UUIDs of every node in this profile."""
        return set(orm.QueryBuilder(backend=self.load()).append(orm.Node, project='uuid').all(flat=True))

    def count(self) -> int:
        """Return the number of nodes in this profile."""
        return orm.QueryBuilder(backend=self.load()).append(orm.Node).count()

    def creator(self, uuid: str) -> str:
        """Return the UUID of the process that created a node."""
        return self.node(uuid).creator.uuid

    def mtime(self, uuid: str):
        """Return the modification time of a node, which is what decides an extras exchange."""
        return self.node(uuid).mtime

    def set_mtime(self, uuid: str, mtime) -> None:
        """Write the modification time of a node, to stand in for a machine whose clock differs."""
        from aiida.orm.entities import EntityTypes

        backend = self.load()
        backend.bulk_update(EntityTypes.NODE, [{'id': orm.load_node(uuid=uuid).pk, 'mtime': mtime}])

    def set_extra(self, uuid: str, key: str, value: t.Any) -> None:
        """Set one extra on a node, which stamps its mtime as a user edit does."""
        self.node(uuid).base.extras.set(key, value)

    def extras(self, uuid: str) -> dict[str, t.Any]:
        """Return the public extras of a node: what a refresh would carry."""
        return {key: value for key, value in self.node(uuid).base.extras.all.items() if not key.startswith('_')}

    def computer(self, label: str) -> str:
        """Return the UUID of the computer with this label, creating the computer if it does not exist yet."""
        backend = self.load()
        found = orm.QueryBuilder(backend=backend).append(orm.Computer, filters={'label': label}, project='uuid').all()

        if found:
            return found[0][0]

        computer = orm.Computer(
            label=label,
            hostname='localhost',
            transport_type='core.local',
            scheduler_type='core.direct',
            backend=backend,
        )

        return computer.store().uuid

    def computers(self) -> dict[str, str]:
        """Return the label of every computer of this profile, keyed by UUID.

        Keyed by UUID because that is the identity of a machine across the collab: the label is what this profile
        happens to call it, and telling one machine from two is the question the marker raises.
        """
        return dict(orm.QueryBuilder(backend=self.load()).append(orm.Computer, project=['uuid', 'label']).all())

    def group(self, label: str) -> str:
        """Return the UUID of the group with this label, creating the group if it does not exist yet."""
        backend = self.load()
        found = orm.QueryBuilder(backend=backend).append(orm.Group, filters={'label': label}, project='uuid').all()

        if found:
            return found[0][0]

        group = orm.Group(label=label, backend=backend)
        group.store()

        return group.uuid

    def curate(self, label: str, *uuids: str) -> str:
        """Add nodes to a group of this profile, which is what the membership journal records."""
        group_uuid = self.group(label)
        backend = self.load()
        group = orm.Group.get_collection(backend).get(uuid=group_uuid)
        group.add_nodes([orm.load_node(uuid=uuid) for uuid in uuids])

        return group_uuid

    def delete(self, *uuids: str) -> None:
        """Delete nodes from this profile, which is what records their tombstones."""
        from aiida.tools.graph.deletions import delete_nodes

        backend = self.load()
        pks = [orm.load_node(uuid=uuid).pk for uuid in uuids]
        delete_nodes(pks, backend=backend, dry_run=False)

    def labels(self) -> set[str]:
        """Return the labels of the curated groups of this profile."""
        return set(
            orm.QueryBuilder(backend=self.load()).append(orm.Group, project='label', filters=CURATED).all(flat=True)
        )

    def groups(self) -> set[str]:
        """Return the UUIDs of every group of this profile, curated or generated.

        Unfiltered on purpose: what a peer may *not* create here is only observable by a query that can see it.
        """
        return set(orm.QueryBuilder(backend=self.load()).append(orm.Group, project='uuid').all(flat=True))

    def state(self):
        """Return the collab state of this member, read from its file."""
        from aiida.tools.collab.state import CollabState

        return CollabState.read(self.state_filepath)

    @property
    def state_filepath(self) -> Path:
        from aiida.tools.collab.state import CollabState

        return CollabState.get_filepath(self.profile)

    @property
    def workdir(self) -> Path:
        from aiida.tools.collab.state import CollabState

        return CollabState.get_workdir(self.profile)

    def option(self, name: str) -> t.Any:
        """Return a configuration option of this member, read from the file every member shares."""
        from aiida.manage.configuration.config import Config

        return Config.from_file(self.config.filepath).get_option(name, scope=self.profile.name)

    def set_option(self, name: str, value: t.Any) -> None:
        """Write a configuration option of this member, into the file and into the loaded configuration."""
        from aiida.tools.collab.config import mutate_config

        with mutate_config(self.config) as stored:
            for target in (stored, self.config):
                target.set_option(name, value, scope=self.profile.name)

    def peers(self) -> dict[str, dict[str, t.Any]]:
        """Return the roster of this member, keyed by profile UUID."""
        from aiida.tools.collab.config import OPTION_PEERS

        return self.option(OPTION_PEERS)

    def graph(self) -> dict[str, t.Any]:
        """Return a canonical digest of this profile: what "did they converge" means.

        Nodes by UUID, links as ``(input, output, type, label)`` quadruples, group memberships as
        ``(group uuid, node uuid)`` pairs, the public extras of every node, and per node its attributes and the
        bytes of its repository -- everything a sync can carry, and nothing that legitimately differs between two
        profiles (primary keys, users, import groups, labels a collision renamed, the checkpoint the export
        strips).

        The content half is not decoration. The transfer rides a bespoke archive writer, and a digest that
        stopped at the shape of the graph would call two profiles converged while one of them held nodes with no
        attributes and empty repositories -- which is precisely what a regression in that writer produces.
        """
        backend = self.load()

        nodes = sorted(orm.QueryBuilder(backend=backend).append(orm.Node, project='uuid').all(flat=True))
        links = sorted(
            tuple(row)
            for row in orm.QueryBuilder(backend=backend)
            .append(orm.Node, tag='input', project='uuid')
            .append(orm.Node, with_incoming='input', project='uuid', edge_project=['type', 'label'])
            .all()
        )
        members = sorted(
            tuple(row)
            for row in orm.QueryBuilder(backend=backend)
            .append(orm.Group, tag='group', project='uuid', filters=CURATED)
            .append(orm.Node, with_group='group', project='uuid')
            .all()
        )
        extras = {
            uuid: {key: value for key, value in (values or {}).items() if not key.startswith('_')}
            for uuid, values in orm.QueryBuilder(backend=backend).append(orm.Node, project=['uuid', 'extras']).all()
        }

        content = {}

        for node in orm.QueryBuilder(backend=backend).append(orm.Node).all(flat=True):
            files = {}

            for root, _, filenames in node.base.repository.walk():
                for name in filenames:
                    path = str(root / name)

                    try:
                        digest = hashlib.sha256(node.base.repository.get_object_content(path, 'rb')).hexdigest()
                    except Exception as exception:
                        # The row promised a file the object store does not hold, which is what an export that
                        # wrote the metadata and skipped the bytes leaves behind. Recorded rather than raised, so
                        # the comparison that fails names the node and the path instead of dying inside a digest.
                        digest = f'unreadable: {type(exception).__name__}'

                    files[path] = digest

            attributes = dict(node.base.attributes.all)
            # Dropped by the export by design -- a checkpoint is where *this* daemon left a process, and means
            # nothing anywhere else -- so it differs legitimately, like the `_`-prefixed extras above.
            attributes.pop(orm.ProcessNode.CHECKPOINT_KEY, None)
            content[node.uuid] = {'attributes': attributes, 'files': files}

        return {'nodes': nodes, 'links': links, 'members': members, 'extras': extras, 'content': content}


def move(source: Member, target: Member, direction: str, *args: str, **kwargs):
    """Move provenance from ``source`` to ``target``, by either of the two routes that do it.

    Pull is receiver-driven and push sender-driven; they share the delta computation and the import and differ in
    who holds the lock, who advances the cursor and whose policy gates what lands. Every scenario whose subject is
    provenance moving between two members runs through this verb, parametrised over both.
    """
    if direction == 'pull':
        return target.run('pull', [source.nickname, '--force', *args], **kwargs)

    return source.run('push', [target.nickname, '--force', *args], **kwargs)


@pytest.fixture
def collab(empty_config, tmp_path, monkeypatch):
    """Return a factory that builds a collab of N real members over one temporary configuration.

    Two things stay mocked and only two: the daemon (no member runs one -- the endpoint thread is what a daemon
    would supervise) and the worker pause it would perform, which is covered against a mocked circus client in
    ``test_endpoint.py`` and would otherwise dominate the runtime.
    """
    import contextlib

    from aiida.manage.configuration import create_profile
    from aiida.tools.collab import config as collab_config
    from aiida.tools.collab import endpoint as collab_endpoint

    monkeypatch.setattr(collab_endpoint, 'workers_stopped', lambda profile: contextlib.nullcontext())
    monkeypatch.setattr('aiida.engine.daemon.client.DaemonClient.is_daemon_running', property(lambda self: False))
    # `init` and `join` end by starting the daemon, which here would supervise an endpoint that ``Member.serve``
    # already runs in a thread of its own. Its restart branch is unreachable: no member's daemon is ever running.
    monkeypatch.setattr('aiida.engine.daemon.client.DaemonClient.start_daemon', lambda self, *args, **kwargs: None)

    members: list[Member] = []

    def factory(
        count: int = 3,
        *,
        extras_mode: str = 'local',
        groups_mode: str = 'local',
        bare: bool = False,
    ) -> list[Member]:
        """Build ``count`` members that know each other and can reach each other.

        :param bare: create the profiles and nothing else -- no collab options, no endpoint. That is the state a
            machine is in before ``verdi collab init``, which is what ``test_e2e_membership.py`` starts from.
        """
        import uuid as uuid_module

        collab_uuid = uuid_module.uuid4().hex
        policy = {'extras_mode': extras_mode, 'groups_mode': groups_mode}

        for nickname in NICKNAMES[:count]:
            members.append(_build(nickname, empty_config, tmp_path, create_profile))

        if bare:
            return members

        for member in members:
            _wire(member, collab_uuid, policy)
            port = member.serve(port=0)
            member.set_option(collab_config.OPTION_PORT, port)
            # Announced as `verdi collab init` announces it, so that a stamp is raised by a move and nothing else.
            member.set_option(collab_config.OPTION_ANNOUNCED, collab_config.endpoint_url('127.0.0.1', port))

        for member in members:
            _set_peers(
                member,
                {
                    other.uuid: {
                        'url': other.url,
                        'nickname': other.nickname,
                        'name': other.profile.name,
                        'stamp': 1,
                        'seen': True,
                        'active': True,
                        'signalled': False,
                    }
                    for other in members
                    if other is not member
                },
            )

        return members

    yield factory

    for member in members:
        member.stop()
        with contextlib.suppress(Exception):
            member.backend.close()


def _build(nickname, config, tmp_path, create_profile) -> Member:
    """Create one profile with its own storage, before anything collab touches it."""
    profile = create_profile(
        config,
        storage_backend='core.sqlite_dos',
        storage_config={'filepath': str(tmp_path / nickname / 'storage')},
        name=nickname,
        email=f'{nickname}@localhost',
        is_test_profile=True,
    )
    config.store()

    return Member(nickname, profile, config, profile.storage_cls(profile))


def _wire(member: Member, collab_uuid: str, policy: dict) -> None:
    """Write the collab options of a member, as ``verdi collab init`` writes them."""
    from aiida.tools.collab import config as collab_config

    values = {
        collab_config.OPTION_ENABLED: True,
        collab_config.OPTION_UUID: collab_uuid,
        collab_config.OPTION_TOKEN: 'collab-token',
        collab_config.OPTION_PEERS: {},
        collab_config.OPTION_BIND: '127.0.0.1',
        collab_config.OPTION_PORT: 0,
        collab_config.OPTION_STAMP: 1,
        collab_config.OPTION_POLICY: policy,
        # Off by default in the schema, so that a profile has to opt in to being written to. Every member of this
        # harness has, since half of these scenarios are pushes; the one that tests the refusal turns it back off.
        collab_config.OPTION_ACCEPT_PUSH: True,
    }

    for name, value in values.items():
        member.config.set_option(name, value, scope=member.profile.name)

    member.config.store()


def _set_peers(member: Member, peers: dict) -> None:
    from aiida.tools.collab.config import OPTION_PEERS

    member.set_option(OPTION_PEERS, peers)


@pytest.fixture
def faults(monkeypatch):
    """Return the fault injector: ways for a transfer to break that leave the rest of the code path real.

    Every injection wraps the genuine handler rather than replacing it, so what the client sees is what a real
    network failure produces -- a short body against a promised ``Content-Length``, a half-staged upload, an
    import that raised -- and the recovery under test is the real one.
    """
    return _Faults(monkeypatch)


class _Faults:
    """Injects one fault at a time, each wrapping the genuine handler rather than replacing it.

    The transfer failures fire once and let the retry through, which is what the recovery under test needs. So do
    the two that stand in for one peer of a round being diverged -- a planted boundary link and an unreadable
    export -- since a loop over several peers is only isolated by the others being served correctly. The ones
    that model a peer simply being that way -- a generated group, an older archive format, a handshake that
    misstates itself -- hold for every call. ``rotate_during_import`` is neither: it fires once, and what it
    models is a second terminal, not a fault at all.
    """

    def __init__(self, monkeypatch):
        self._monkeypatch = monkeypatch

    def drop_next_download(self, after: int) -> dict:
        """Cut the connection ``after`` bytes into the next delta any member serves.

        Only the body copy is intercepted, so the response line, the ``Content-Length`` and above all the ``ETag``
        are the real ones -- which is what makes the resumption that follows a genuine ``Range`` request against a
        validator the endpoint issued.
        """
        import types

        from aiida.tools.collab import server as collab_server

        state: dict = {'dropped': False, 'served': []}
        copy = shutil.copyfileobj

        def copyfileobj(source, target, length=None):
            start = source.tell()

            if not state['dropped']:
                state['dropped'] = True
                chunk = source.read(after)
                target.write(chunk)
                target.flush()
                state['served'].append(len(chunk))
                msg = 'connection dropped mid-download'
                raise BrokenPipeError(msg)

            copy(source, target, length)
            state['served'].append(source.tell() - start)

        self._monkeypatch.setattr(collab_server, 'shutil', types.SimpleNamespace(copyfileobj=copyfileobj))

        return state

    def drop_upload(self, member: Member, after: int) -> dict:
        """Stage only ``after`` bytes of the first upload ``member`` receives, then cut the connection."""
        from aiida.tools.collab.server import CollabRequestHandler

        state = {'dropped': False, 'staged': 0}
        original = CollabRequestHandler._put_upload

        def put_upload(handler, sha256):
            if state['dropped'] or handler.server is not member.server:
                return original(handler, sha256)

            state['dropped'] = True
            chunk = handler.rfile.read(after)

            with (member.endpoint.staging_dir / sha256).open('ab') as target:
                target.write(chunk)

            state['staged'] = len(chunk)
            handler.close_connection = True
            msg = 'connection dropped mid-upload'
            raise BrokenPipeError(msg)

        self._monkeypatch.setattr(CollabRequestHandler, '_put_upload', put_upload)

        return state

    def drop_import(self, member: Member) -> dict:
        """Cut the connection on the first import request ``member`` receives, leaving the upload staged.

        What a peer dying between the upload and the import looks like from the pusher's side: the bytes are all
        there, nothing was imported, and there is no response.
        """
        from aiida.tools.collab.server import CollabRequestHandler

        state = {'dropped': False}
        original = CollabRequestHandler._post_import

        def post_import(handler, sha256):
            if state['dropped'] or handler.server is not member.server:
                return original(handler, sha256)

            state['dropped'] = True
            handler.close_connection = True
            msg = 'the peer died before importing'
            raise BrokenPipeError(msg)

        self._monkeypatch.setattr(CollabRequestHandler, '_post_import', post_import)

        return state

    def corrupt_staged(self, member: Member) -> dict:
        """Flip a byte of the first upload ``member`` has staged, just before it verifies the checksum."""
        from aiida.tools.collab.server import CollabRequestHandler

        state = {'corrupted': False}
        original = CollabRequestHandler._post_import

        def post_import(handler, sha256):
            filepath = member.endpoint.staging_dir / sha256

            if not state['corrupted'] and handler.server is member.server and filepath.exists():
                state['corrupted'] = True
                payload = bytearray(filepath.read_bytes())
                payload[-1] ^= 0xFF
                filepath.write_bytes(payload)

            return original(handler, sha256)

        self._monkeypatch.setattr(CollabRequestHandler, '_post_import', post_import)

        return state

    def failing_import(
        self,
        message: str = 'the import failed',
        times: int = 1,
        after: int = 0,
        error: type[Exception] = RuntimeError,
    ) -> dict:
        """Make imports raise, wherever they run: in the endpoint or in the pulling CLI.

        :param after: imports to let through first, which is how the failure is placed in the middle of a loop
            over several peers rather than at its head.
        :param error: what the import raises. A pull only treats the delta of one peer as unusable for the errors
            that describe the delta, so a scenario about the loop carrying on has to raise one of those.
        """
        from aiida.tools.collab import endpoint as collab_endpoint
        from aiida.tools.collab import sync as collab_sync

        state = {'calls': 0}
        original = collab_sync.import_delta

        def failing(*args, **kwargs):
            state['calls'] += 1

            if after < state['calls'] <= after + times:
                raise error(message)

            return original(*args, **kwargs)

        # Both names, because the endpoint bound its own reference at import time and the pulling CLI resolves
        # the module attribute per call.
        self._monkeypatch.setattr(collab_sync, 'import_delta', failing)
        self._monkeypatch.setattr(collab_endpoint, 'import_delta', failing)

        return state

    def plant_boundary_link(self, link: list[str]) -> None:
        """Add one link quadruple to the metadata of the next delta exported from anywhere.

        A diverged or hostile sender is the only thing that produces one, so this is how the receiver's refusal
        can be exercised at all: the boundary is what the import re-attaches without the archive importer's
        validation, and it must not be able to plant a second creator or a link from a node to itself.

        The next delta and no other, so that in a round over several peers exactly one of them is the diverged
        one -- the pulls and the cuts of a loop are sequential, and the first belongs to the first peer.
        """
        from aiida.tools.collab import sync as collab_sync

        state = {'planted': False}
        original = collab_sync._write_thin_archive

        def planting(filepath, *, boundary, **kwargs):
            if state['planted']:
                return original(filepath, boundary=boundary, **kwargs)

            state['planted'] = True

            return original(filepath, boundary=[*boundary, link], **kwargs)

        self._monkeypatch.setattr(collab_sync, '_write_thin_archive', planting)

    def offer_generated_group(self, label: str, node: str) -> dict:
        """Make every membership offer from here on also offer a group of a type AiiDA generates for itself.

        An honest sender never offers one -- the journal refuses to record them -- so the receiver's gate can only
        be reached by a sender that was tampered with, which is exactly what it exists for.
        """
        import uuid as uuid_module

        from aiida.tools.collab import endpoint as collab_endpoint
        from aiida.tools.collab import sync as collab_sync
        from aiida.tools.collab.protocol import GroupMembers

        planted = GroupMembers(uuid=uuid_module.uuid4().hex, label=label, type_string='core.import', nodes=[node])
        state = {'uuid': planted.uuid}
        original = collab_sync.membership_offer

        def offering(**kwargs):
            return [*original(**kwargs), planted]

        # Both names: the pulling peer is offered by the endpoint, which bound its own reference at import time.
        self._monkeypatch.setattr(collab_sync, 'membership_offer', offering)
        self._monkeypatch.setattr(collab_endpoint, 'membership_offer', offering)

        return state

    def export_at_version(self, version: str) -> None:
        """Write every delta from here on at an older archive format, as a peer on an older release would.

        The only kind of archive a collab ever sends is a thin one with boundary links in its metadata, so this
        is what the interchange contract actually has to survive.
        """
        from aiida.tools.archive.abstract import get_format
        from aiida.tools.collab import endpoint as collab_endpoint
        from aiida.tools.collab import sync as collab_sync

        original = collab_sync.export_delta

        def downgrading(filepath, **kwargs):
            export = original(filepath, **kwargs)
            older = filepath.with_name(f'{filepath.name}.older')
            get_format().migrate(filepath, older, version, compression=0)
            older.replace(filepath)

            return export

        self._monkeypatch.setattr(collab_sync, 'export_delta', downgrading)
        self._monkeypatch.setattr(collab_endpoint, 'export_delta', downgrading)

    def rotate_during_import(self, member: Member) -> dict:
        """Rotate a member's own token from inside its own in-flight import.

        A ``verdi collab rotate`` run in another terminal while a long transfer is under way is the one race the
        commands re-read the configuration for. Driven from inside the import because that is where a sync spends
        its time, and because two ``verdi`` runs cannot genuinely overlap in one interpreter.
        """
        import secrets

        from aiida.cmdline.commands.cmd_collab import set_key
        from aiida.tools.collab import endpoint as collab_endpoint
        from aiida.tools.collab import sync as collab_sync
        from aiida.tools.collab.config import mutate_config

        state = {'rotated': False}
        original = collab_sync.import_delta

        def rotating(*args, **kwargs):
            if not state['rotated']:
                state['rotated'] = True

                with mutate_config(member.config) as stored:
                    set_key(stored, member.config, member.profile, secrets.token_urlsafe(32))

            return original(*args, **kwargs)

        self._monkeypatch.setattr(collab_sync, 'import_delta', rotating)
        self._monkeypatch.setattr(collab_endpoint, 'import_delta', rotating)

        return state

    def negotiate_during_the_closing_write(self, member: Member, peer: Member) -> dict:
        """Serve ``peer`` a negotiation from inside the closing write of ``member``'s own in-flight import.

        The window between an import committing its archive and its event reaching the state file. A negotiation
        served in it reads a state that does not name the imported nodes yet, and stamps the computation it caches
        with the instant it read at -- so whether any later negotiation ever unions those nodes turns on which
        side of that instant the event's own stamp falls. Driven from inside the import for the reason
        ``rotate_during_import`` is: two requests cannot genuinely overlap in one interpreter.
        """
        from aiida.tools.collab import sync as collab_sync

        state = {'negotiated': False}
        original = collab_sync._write_boundary_links

        def writing(backend, pending, tombstones):
            if not state['negotiated']:
                state['negotiated'] = True
                member.endpoint.negotiate_delta(peer.state().cursors.get(member.uuid), frozenset(), requester=peer.uuid)

            return original(backend, pending, tombstones)

        self._monkeypatch.setattr(collab_sync, '_write_boundary_links', writing)

        return state

    def seal_after_the_negotiation(self, member: Member, inputs: str) -> dict:
        """Seal work on ``member`` consuming ``inputs``, after its manifest was served and before the export is.

        The window the export request's instant exists for. The new work links onto a node of the manifest, so a
        cut taken from the recomputed delta carries a boundary link to a node the requester was never offered --
        which its import refuses whole.
        """
        return self._after_the_negotiation(lambda: _seal_calculation(member.backend, inputs))

    def delete_after_the_negotiation(self, member: Member, uuid: str) -> dict:
        """Delete a node of ``member``'s own profile in that same window, as a ``verdi node delete`` there would.

        The sibling trigger, and the quieter one: a deletion moves no seal and records no import, so it makes no
        computation stale at all. The cut simply names a row that is gone.
        """
        return self._after_the_negotiation(lambda: _delete_node(member.backend, uuid))

    def _after_the_negotiation(self, action: t.Callable[[], None]) -> dict:
        """Run ``action`` once, after a manifest was served and before the export request that follows it.

        Hooked on the client's negotiation and driven from inside it for the reason ``rotate_during_import`` is:
        two ``verdi`` runs cannot genuinely overlap in one interpreter. The action is written straight to the
        sender's own storage handle, because loading a second profile mid-command closes the storage the command
        under test is using.
        """
        from aiida.tools.collab.client import CollabClient

        state = {'fired': False}
        original = CollabClient.negotiate_delta

        def negotiating(self, *args, **kwargs):
            manifest = original(self, *args, **kwargs)

            if not state['fired']:
                state['fired'] = True
                action()

            return manifest

        self._monkeypatch.setattr(CollabClient, 'negotiate_delta', negotiating)

        return state

    def delete_during_negotiation(self, member: Member, uuid: str) -> dict:
        """Delete a node of a member's own profile from inside that member's in-flight pull.

        A ``verdi node delete`` run in another terminal while a transfer is under way, driven from inside the
        transfer for the reason ``rotate_during_import`` is: two ``verdi`` runs cannot genuinely overlap in one
        interpreter. Hooked on the negotiation rather than on the download, which is where a pull spends its
        time, because a node the receiver still held when the manifest was diffed is never cut into the delta at
        all -- so a deletion later than that has nothing to be undone by.
        """
        from aiida.tools.collab.client import CollabClient

        state = {'deleted': False}
        original = CollabClient.negotiate_delta

        def negotiating(self, *args, **kwargs):
            if not state['deleted']:
                state['deleted'] = True
                member.delete(uuid)

            return original(self, *args, **kwargs)

        self._monkeypatch.setattr(CollabClient, 'negotiate_delta', negotiating)

        return state

    def refuse_every_contact(self) -> None:
        """Fail the test outright on any request to any peer, for the paths whose claim is that they make none."""
        from aiida.tools.collab.client import CollabClient

        def contacting(self, method, route, **kwargs):
            msg = f'a peer was contacted -- {method} {route} -- where nothing may be'
            raise AssertionError(msg)

        self._monkeypatch.setattr(CollabClient, '_request', contacting)

    def claims(self, member: Member, **fields) -> None:
        """Make one member's handshake declare something other than the truth about itself.

        The version gate is what decides whether a transfer may happen at all, so exercising it needs a peer that
        genuinely answers with another version than this installation has.
        """
        import dataclasses

        from aiida.tools.collab import endpoint as collab_endpoint

        original = collab_endpoint.local_info

        def claiming(profile, backend, cursor=None):
            info = original(profile, backend, cursor)

            if profile.name != member.profile.name:
                return info

            return dataclasses.replace(info, **fields)

        self._monkeypatch.setattr(collab_endpoint, 'local_info', claiming)

    def die_after_the_archive_commits(self) -> dict:
        """Let the next import write its archive and then die before the state is written.

        The window the whole ordering of ``import_delta`` exists for: the archive commits in its own transaction
        and the cursor, the event and the journalled links are written after it, so a crash in between must leave
        a receiver that holds the nodes and claims none of them.
        """
        from aiida.tools.collab import sync as collab_sync

        state = {'calls': 0}
        original = collab_sync.import_archive

        def dying(*args, **kwargs):
            original(*args, **kwargs)
            state['calls'] += 1

            if state['calls'] == 1:
                msg = 'the process died after the archive committed'
                raise RuntimeError(msg)

        self._monkeypatch.setattr(collab_sync, 'import_archive', dying)

        return state

    def corrupt_export(self) -> None:
        """Make the next delta exported from anywhere write bytes that are not an archive at all.

        The next and no other, for the reason ``plant_boundary_link`` fires once: one unusable peer in a round is
        what tells apart a peer being skipped from a run being over.
        """
        from aiida.tools.collab import endpoint as collab_endpoint
        from aiida.tools.collab import sync as collab_sync
        from aiida.tools.collab.sync import DeltaExport

        state = {'corrupted': False}
        original = collab_sync.export_delta

        def corrupting(filepath, **kwargs):
            export = original(filepath, **kwargs)

            if state['corrupted']:
                return export

            state['corrupted'] = True
            filepath.write_bytes(b'not an archive' * 64)

            return DeltaExport(filepath=filepath, uuids=export.uuids, instant=export.instant, computed=export.computed)

        self._monkeypatch.setattr(collab_sync, 'export_delta', corrupting)
        self._monkeypatch.setattr(collab_endpoint, 'export_delta', corrupting)


def _seal_calculation(backend, inputs: str) -> None:
    """Store and seal a calculation consuming an existing node, in a storage handle whose profile is not loaded."""
    source = orm.QueryBuilder(backend=backend).append(orm.Node, filters={'uuid': inputs}).one()[0]
    calculation = orm.CalcJobNode(backend=backend)
    calculation.base.links.add_incoming(source, link_type=LinkType.INPUT_CALC, link_label='term')
    calculation.store()

    created = orm.Int(3, backend=backend)
    created.base.links.add_incoming(calculation, link_type=LinkType.CREATE, link_label='result')
    created.store()
    calculation.seal()


def _delete_node(backend, uuid: str) -> None:
    """Delete a node in a storage handle whose profile is not loaded, through the real deletion path."""
    from aiida.tools.graph.deletions import delete_nodes

    pk = orm.QueryBuilder(backend=backend).append(orm.Node, filters={'uuid': uuid}, project='id').one()[0]
    delete_nodes([pk], backend=backend, dry_run=False)


@pytest.fixture
def stranger():
    """Return a factory for an HTTP server on loopback that is not a collab endpoint.

    A peer URL can reach anything: a reverse-proxy default page, a machine that was reprovisioned into something
    else, a service that is simply broken. None of those may take the sync with everybody else down with them.
    """
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    servers = []

    def factory(status: int = 200, body: bytes = b'{"hello": "world"}') -> str:
        class Handler(BaseHTTPRequestHandler):
            protocol_version = 'HTTP/1.1'

            def _answer(self):
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            do_GET = do_POST = do_PUT = do_HEAD = _answer  # noqa: N815

            def log_message(self, format, *args):
                pass

        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        server.daemon_threads = True
        servers.append(server)
        threading.Thread(target=server.serve_forever, daemon=True).start()

        return f'http://127.0.0.1:{server.server_address[1]}'

    yield factory

    for server in servers:
        server.shutdown()
        server.server_close()
