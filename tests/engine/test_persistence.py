###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test persisting via the AiidaCheckpointPersister.

Tests share one profile, so the checkpoint directory can hold other processes' files. Tests snapshot
its entries before acting and assert diffs, with premises pinning the snapshot.
"""

import asyncio
import hashlib
import logging
import os
import pathlib
import subprocess
import sys
import typing as t
from collections.abc import Callable, Iterator
from uuid import uuid4

import pytest

from aiida import orm
from aiida.common import _callables as callables
from aiida.common import exceptions, loaders
from aiida.common.processes import ProcessState
from aiida.engine import Process, WorkChain, run
from aiida.engine.persistence import AiidaCheckpointPersister
from aiida.engine.processes.persistence import (
    META,
    META__CLASS_BYTES,
    META__CLASS_NAME,
    META__OBJECT_LOADER,
    META__USER,
    CheckpointContext,
    CheckpointFuture,
    CheckpointPayload,
    CheckpointSerializable,
)
from aiida.engine.processes.states import State
from aiida.engine.utils import instantiate_process
from aiida.manage import get_manager
from aiida.manage.configuration import Profile
from aiida.orm.implementation import StorageBackend
from tests.utils.processes import DummyProcess

TransitionSnapshot: t.TypeAlias = tuple[ProcessState | None, str | None, list[str]]
CHECKPOINT_FAILURE_MESSAGE: t.Final = (
    'Exception trying to save checkpoint, this means you will '
    'not be able to restart in case of a crash until the next successful checkpoint.'
)
NO_PERSISTER_MESSAGE: t.Final = (
    'No persister set to save checkpoint, this means you will '
    'not be able to restart in case of a crash until the next successful checkpoint.'
)


class MetadataCheckpointSerializable(CheckpointSerializable):
    """Minimal checkpoint serializable for persistence tests."""

    def __init__(self, value: str = 'value') -> None:
        self.value = value

    def save_instance_state(self, out_state, save_context):
        super().save_instance_state(out_state, save_context)
        out_state['value'] = self.value

    def load_instance_state(self, saved_state, load_context):
        super().load_instance_state(saved_state, load_context)
        self.value = saved_state['value']


class CustomLoaderCheckpointSerializable(MetadataCheckpointSerializable):
    """CheckpointSerializable whose class is identified through a custom loader."""


class NameMappingObjectLoader(loaders.ObjectLoader):
    """Object loader mapping a test identifier to ``CustomLoaderCheckpointSerializable``."""

    identifier = 'custom-loader-savable'

    def load_object(self, identifier: str):
        if identifier == self.identifier:
            return CustomLoaderCheckpointSerializable
        return loaders.DefaultObjectLoader().load_object(identifier)

    def identify_object(self, obj):
        if obj is CustomLoaderCheckpointSerializable:
            return self.identifier
        return loaders.DefaultObjectLoader().identify_object(obj)


class ExplicitContextObjectLoader(loaders.ObjectLoader):
    """Object loader used to test explicit context priority."""

    identifier = 'explicit-context-savable'

    def load_object(self, identifier: str):
        if identifier == self.identifier:
            return MetadataCheckpointSerializable
        msg = f'Unexpected identifier: {identifier}'
        raise ImportError(msg)

    def identify_object(self, obj):
        return self.identifier


def test_custom_metadata_uses_user_namespace():
    """Custom metadata is written to and read from the user metadata namespace."""
    saved_state = {}

    CheckpointSerializable.set_custom_meta(saved_state, 'key', 'value')

    assert saved_state[META][META__USER]['key'] == 'value'
    assert CheckpointSerializable.get_custom_meta(saved_state, 'key') == 'value'


@pytest.mark.parametrize('saved_state', [{}, {META: {}}, {META: {META__USER: {}}}])
def test_get_custom_metadata_missing_raises(saved_state):
    """Missing custom metadata raises the legacy exception message."""
    with pytest.raises(ValueError, match="Unknown meta key 'key'"):
        CheckpointSerializable.get_custom_meta(saved_state, 'key')


def test_checkpoint_payload_from_object_stores_class_metadata():
    """Constructing a checkpoint payload from a serializable stores the class metadata."""
    payload = CheckpointPayload.from_object(MetadataCheckpointSerializable())

    assert payload[META][META__CLASS_NAME] == loaders.get_object_loader().identify_object(
        MetadataCheckpointSerializable
    )


def test_checkpoint_payload_decodes_legacy_saved_state():
    """Legacy saved-state dictionaries can still be loaded through a checkpoint payload."""
    payload = CheckpointPayload.from_saved_state(
        {
            META: {META__CLASS_NAME: loaders.get_object_loader().identify_object(MetadataCheckpointSerializable)},
            'value': 'loaded',
        }
    )

    restored = payload.decode()

    assert isinstance(restored, MetadataCheckpointSerializable)
    assert restored.value == 'loaded'


def test_default_loader_restores_saved_state():
    """The default object loader restores importable checkpoint serializables."""
    restored = CheckpointPayload.from_object(MetadataCheckpointSerializable()).decode()

    assert isinstance(restored, MetadataCheckpointSerializable)
    assert restored.value == 'value'


def test_recreation_tolerates_renamed_override_parameters():
    """Subclass overrides retain their parameter-name independence."""

    class RenamedParameters(MetadataCheckpointSerializable):
        @classmethod
        def recreate_from(cls, state, context=None):
            return super().recreate_from(state, context)

    restored = CheckpointPayload.from_object(RenamedParameters()).decode()
    assert isinstance(restored, RenamedParameters)
    assert restored.value == 'value'


def test_explicit_load_context_loader_takes_priority():
    """An explicit load-context loader takes priority over saved loader metadata."""
    saved_state = {
        META: {
            META__CLASS_NAME: ExplicitContextObjectLoader.identifier,
            META__USER: {META__OBJECT_LOADER: 'not:importable'},
        },
        'value': 'explicit',
    }

    restored = CheckpointSerializable.load(saved_state, CheckpointContext(loader=ExplicitContextObjectLoader()))

    assert isinstance(restored, MetadataCheckpointSerializable)
    assert restored.value == 'explicit'


def test_saved_custom_loader_takes_priority_over_global_loader():
    """Saved custom loader metadata is used when no explicit loader is provided."""
    payload = CheckpointPayload.from_object(
        CustomLoaderCheckpointSerializable(), CheckpointContext(loader=NameMappingObjectLoader())
    )

    restored = payload.decode()

    assert isinstance(restored, CustomLoaderCheckpointSerializable)
    assert restored.value == 'value'


def test_fallback_to_global_loader_without_custom_loader_metadata():
    """The global loader is used when no custom loader metadata exists."""
    saved_state = {
        META: {META__CLASS_NAME: loaders.get_object_loader().identify_object(MetadataCheckpointSerializable)},
        'value': 'global',
    }

    restored = CheckpointSerializable.load(saved_state)

    assert isinstance(restored, MetadataCheckpointSerializable)
    assert restored.value == 'global'


def test_cancelled_checkpoint_future():
    """Test a cancelled checkpoint future can be saved and recreated."""
    loop = asyncio.new_event_loop()

    try:
        future = CheckpointFuture(loop=loop)
        future.cancel()

        restored = CheckpointPayload.from_object(future).decode(CheckpointContext(loop=loop))

        assert isinstance(restored, CheckpointFuture)
        assert restored.cancelled()
    finally:
        loop.close()


@pytest.mark.requires_broker
class TestProcess:
    """Test the basic saving and loading of process states."""

    @pytest.fixture(autouse=True)
    def init_profile(self):
        """Initialize the profile."""
        assert Process.current() is None
        yield
        assert Process.current() is None

    def test_save_load(self):
        """Test load saved state."""
        process = DummyProcess()
        saved_state = CheckpointPayload.from_object(process)
        process.close()

        loaded_process = saved_state.decode()
        run(loaded_process)

        assert loaded_process.state == ProcessState.FINISHED


@pytest.mark.requires_broker
class TestAiidaCheckpointPersister:
    """Test AiidaCheckpointPersister."""

    maxDiff = 1024

    @pytest.fixture(autouse=True)
    def init_profile(self):
        """Initialize the profile."""
        self.persister = AiidaCheckpointPersister()

    def test_save_load_checkpoint(self):
        """Test checkpoint saving."""
        process = DummyProcess()
        payload_saved = self.persister.save_checkpoint(process)
        payload_loaded = self.persister.load_checkpoint(process.node.pk)

        assert payload_saved == payload_loaded

    def test_delete_checkpoint(self):
        """Test checkpoint deletion."""
        process = DummyProcess()

        self.persister.save_checkpoint(process)
        assert isinstance(process.node.checkpoint, str)

        self.persister.delete_checkpoint(process.pid)
        assert process.node.checkpoint is None


LARGE_CONTEXT_PADDING: t.Final = 200_000
"""Context padding for testing size-independent checkpoint storage."""


class PaddedWorkChain(WorkChain):
    """Minimal workchain for checkpoint tests; callers pad its context."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('x', valid_type=orm.Int)
        spec.output('result', valid_type=orm.Int, required=False)
        spec.outline(cls.record)

    def record(self):
        pass


@pytest.fixture
def persister(aiida_profile: Profile) -> AiidaCheckpointPersister:
    """Return a checkpoint persister.

    :param aiida_profile: Unused; orders profile setup first, the only dependency a fixture can declare.
    """
    return AiidaCheckpointPersister()


@pytest.fixture
def make_process(aiida_profile: Profile):
    """Yield a process factory with optional carried classes and context padding.

    Close created processes after the test to release RPC subscriptions.
    """
    created = []

    def factory(padding: int = 0, carried: bool = False, *, enable_persistence: bool = True):
        process_class = PaddedWorkChain

        if carried:
            # Defined here, so no identifier reaches it and the checkpoint has to carry the class as bytes.
            class Local(PaddedWorkChain):
                pass

            process_class = Local

        instance = process_class(
            runner=get_manager().get_runner(), inputs={'x': orm.Int(1)}, enable_persistence=enable_persistence
        )
        # The context is what a running workchain accumulates, and it is what makes a real checkpoint large.
        instance.ctx.padding = 'x' * padding

        # Instantiating already checkpointed it, and the file goes with the attribute, so a test counting files
        # starts from what the profile held before this process existed.
        AiidaCheckpointPersister().delete_checkpoint(instance.pid)
        created.append(instance)
        return instance

    yield factory

    for instance in created:
        instance.close()


def dirpath() -> pathlib.Path:
    """Return the loaded profile's checkpoint file directory."""
    return get_manager().get_profile_storage().get_checkpoint_directory()


def checkpoint_files() -> set[str]:
    """Return checkpoint directory entry names."""
    if not dirpath().exists():
        return set()

    return {path.name for path in dirpath().iterdir()}


def checkpoint_digest(node: orm.ProcessNode) -> str:
    """Read the SHA-256 reference stored on the node."""
    assert node.checkpoint is not None
    version, digest = node.checkpoint.split(':')
    assert version == 'checkpoint-pickle-v1'
    assert len(digest) == 64
    return digest


@pytest.mark.parametrize('padding', [pytest.param(0, id='empty'), pytest.param(LARGE_CONTEXT_PADDING, id='large')])
@pytest.mark.parametrize('carried', [pytest.param(False, id='importable'), pytest.param(True, id='carried')])
def test_checkpoint_is_one_raw_pickle_with_a_fixed_size_database_reference(
    persister: AiidaCheckpointPersister, make_process: Callable[..., Process], padding: int, carried: bool
):
    """The database reference does not grow with the state or carried class."""
    live = make_process(padding=padding, carried=carried)
    before = checkpoint_files()
    persister.save_checkpoint(live)

    node = orm.load_node(live.pid)
    assert node.checkpoint is not None
    assert len(node.checkpoint) == len('checkpoint-pickle-v1:') + 64
    digest = checkpoint_digest(node)
    filename = f'{live.node.uuid}-{digest}.pkl'
    assert checkpoint_files() - before == {filename}

    data = (dirpath() / filename).read_bytes()
    assert data.startswith(b'\x80\x05')  # Pickle protocol 5.
    assert hashlib.sha256(data).hexdigest() == digest
    if padding:
        assert b'x' * padding in data
    assert (META__CLASS_BYTES in persister.load_checkpoint(live.pid)[META]) is carried


@pytest.mark.parametrize('carried', [pytest.param(False, id='importable'), pytest.param(True, id='carried')])
def test_importable_and_carried_checkpoints_round_trip(
    persister: AiidaCheckpointPersister, make_process: Callable[..., Process], carried: bool
):
    """Checkpoints round-trip with importable and carried classes."""
    live = make_process(carried=carried)
    persister.save_checkpoint(live)
    padding = live.ctx.padding
    live.close()
    loaded = persister.load_checkpoint(live.pid)
    assert loaded['_pid'] == live.pid
    restored = loaded.decode()
    try:
        assert type(restored) is type(live)
        assert restored.ctx.padding == padding
    finally:
        restored.close()


def test_checkpoint_restores_python_objects_and_shared_references(
    persister: AiidaCheckpointPersister, make_process: Callable[..., Process]
):
    """A dynamic object and its closure can share state, including cycles and stored nodes."""
    from dataclasses import dataclass

    @dataclass
    class Local:
        values: list
        node: orm.Node

    live = make_process()
    node = live.node.inputs.x
    values: list = []
    values.append(values)
    live.ctx.data = Local(values, node)
    live.ctx.callback = lambda: (values, node)
    live.ctx.inputs = live.node.inputs

    persister.save_checkpoint(live)
    live.close()
    restored = persister.load_checkpoint(live.pid).decode()
    try:
        restored_values, restored_node = restored.ctx.callback()
        assert restored_values is restored.ctx.data.values
        assert restored_values[0] is restored_values
        assert restored_node is restored.ctx.data.node
        assert restored_node.uuid == node.uuid
        assert restored.ctx.inputs.x.uuid == node.uuid
    finally:
        restored.close()


def test_checkpoint_keeps_inputs_as_node_references(
    persister: AiidaCheckpointPersister, make_process: Callable[..., Process]
):
    """Raw and provenance inputs reach the pickle as objects, so one stored node restores as one object."""
    from aiida.engine.processes.generic.process import CheckpointPayloadKeys

    live = make_process()
    persister.save_checkpoint(live)
    loaded = persister.load_checkpoint(live.pid)

    raw = loaded[CheckpointPayloadKeys.INPUTS_RAW]['x']
    provenance = loaded['provenance_inputs']['x']
    assert raw.uuid == live.inputs.x.uuid
    assert raw is provenance


def test_encode_decode_input_args_snapshot_containers():
    """Encoded and decoded inputs are new containers, so a decoded process never aliases the payload."""
    from aiida.engine import Process

    process = Process.__new__(Process)
    source: dict[str, int] = {'x': 1}
    encoded = process._encode_input_args(source)
    assert encoded == source and encoded is not source
    decoded = process._decode_input_args(encoded)
    assert decoded == encoded and decoded is not encoded
    decoded['y'] = 2
    assert 'y' not in encoded and 'y' not in source


def test_encode_decode_input_args_copy_nested_containers():
    """Nested containers are copied, so mutating one decode leaves later decodes untouched."""
    from aiida.engine import Process

    process = Process.__new__(Process)
    leaf = orm.Int(1)
    source: dict[str, t.Any] = {'nested': {'second': leaf}}
    encoded = process._encode_input_args(source)
    assert encoded == source and encoded is not source
    assert encoded['nested'] is not source['nested']
    assert encoded['nested']['second'] is leaf

    first = process._decode_input_args(encoded)
    assert first['nested'] is not encoded['nested']
    assert first['nested']['second'] is leaf
    first['nested']['second'] = orm.Int(2)

    second = process._decode_input_args(encoded)
    assert second['nested']['second'] is leaf


def test_checkpoint_restores_group_and_computer_references(
    persister: AiidaCheckpointPersister, make_process: Callable[..., Process], aiida_localhost: orm.Computer
):
    """Groups and computers round-trip as UUID references to their stored entities."""
    live = make_process()
    group = orm.Group(label=str(uuid4())).store()
    live.ctx.references = [group, aiida_localhost]

    persister.save_checkpoint(live)
    live.close()
    restored = persister.load_checkpoint(live.pid).decode()
    try:
        assert [(type(entity), entity.uuid) for entity in restored.ctx.references] == [
            (type(group), group.uuid),
            (type(aiida_localhost), aiida_localhost.uuid),
        ]
    finally:
        restored.close()


def test_link_manager_with_truthy_incoming_round_trips(make_process: Callable[..., Process]):
    """A `NodeLinksManager` with truthy non-`bool` incoming persists as `bool` and reloads."""
    from aiida.common.links import LinkType
    from aiida.engine import _checkpoint_pickle
    from aiida.engine.processes.persistence import CheckpointPayload
    from aiida.orm.utils.managers import NodeLinksManager

    make_process()
    node = orm.Int(3).store()
    manager = NodeLinksManager(node=node, link_type=LinkType.INPUT_CALC, incoming=1)
    payload = CheckpointPayload({'manager': manager})
    restored = _checkpoint_pickle.loads_unsafe(_checkpoint_pickle.dumps(payload))['manager']

    assert isinstance(restored, NodeLinksManager)
    assert restored._incoming is True


@pytest.mark.parametrize(
    'checkpoint',
    [
        pytest.param('!aiida:bundle {}', id='yaml-bundle'),
        pytest.param('!!python/object/apply:builtins.print [unexpected]', id='yaml-object-tag'),
        pytest.param('checkpoint-pickle-v2:' + 'a' * 64, id='unknown-version'),
    ],
)
def test_checkpoint_rejects_unsupported_formats(persister, make_process, checkpoint: str, monkeypatch):
    """Unsupported checkpoints raise a format error without invoking YAML deserialization."""
    from aiida.engine.processes.exceptions import PersistenceError
    from aiida.orm.utils import serialize

    live = make_process()
    live.node.set_checkpoint(checkpoint)

    def fail(value):
        pytest.fail('unsupported checkpoint was deserialized')

    monkeypatch.setattr(serialize, 'deserialize_unsafe', fail)
    with pytest.raises(PersistenceError, match=rf'^Process<{live.pid}> has an unsupported checkpoint format\.$'):
        persister.load_checkpoint(live.pid)
    assert live.node.checkpoint == checkpoint


def test_checkpoint_rejects_load_inside_transaction(
    persister: AiidaCheckpointPersister, make_process: Callable[..., Process]
):
    """Loading inside an active transaction raises before reading the checkpoint reference."""
    from aiida.engine.processes.exceptions import PersistenceError

    live = make_process()
    persister.save_checkpoint(live)
    storage = get_manager().get_profile_storage()
    with storage.transaction():
        with pytest.raises(
            PersistenceError, match=f'Process<{live.pid}> cannot be loaded inside an open storage transaction'
        ):
            persister.load_checkpoint(live.pid)


def test_checkpoint_rejects_an_unstored_node_without_replacing_the_previous_checkpoint(
    persister: AiidaCheckpointPersister, make_process: Callable[..., Process]
):
    """Nodes must be stored before they can be referenced by a checkpoint."""
    from aiida.engine.processes.exceptions import PersistenceError

    live = make_process()
    persister.save_checkpoint(live)
    original = live.node.checkpoint
    live.ctx.unstored = orm.Int(2)

    with pytest.raises(PersistenceError, match='is not stored'):
        persister.save_checkpoint(live)

    assert live.node.checkpoint == original


def test_carried_bytes_deserialize_to_the_original_class(
    persister: AiidaCheckpointPersister, make_process: Callable[..., Process]
):
    """Loaded carried bytes deserialize to the original process class."""
    live = make_process(carried=True)
    persister.save_checkpoint(live)

    payload = persister.load_checkpoint(live.pid)

    assert isinstance(payload[META][META__CLASS_BYTES], bytes)
    assert callables.loads(payload[META][META__CLASS_BYTES]) is type(live)


def test_returned_payload_equals_loaded_and_decodes(
    persister: AiidaCheckpointPersister, make_process: Callable[..., Process]
):
    """The returned payload matches a fresh load and still decodes."""
    live = make_process(carried=True)
    returned = persister.save_checkpoint(live)
    assert returned == persister.load_checkpoint(live.pid)
    assert isinstance(returned[META][META__CLASS_BYTES], bytes)
    live.close()
    restored = returned.decode()
    try:
        assert type(restored) is type(live)
    finally:
        restored.close()


def test_loading_checkpoint_checks_the_digest(
    persister: AiidaCheckpointPersister, make_process: Callable[..., Process]
):
    """A referenced file containing different bytes fails before deserialization."""
    from aiida.engine.processes.exceptions import PersistenceError

    live = make_process(carried=True)
    persister.save_checkpoint(live)
    digest = checkpoint_digest(live.node)
    filepath = dirpath() / f'{live.node.uuid}-{digest}.pkl'
    original = filepath.read_bytes()
    try:
        filepath.write_bytes(b'corrupted checkpoint')
        with pytest.raises(PersistenceError, match='digest mismatch'):
            persister.load_checkpoint(live.pid)
    finally:
        filepath.write_bytes(original)


@pytest.mark.usefixtures('aiida_profile')
def test_checkpoint_write_syncs_parent_directory(monkeypatch):
    """The profile directory is synchronized before a new class directory can be referenced."""
    from aiida.orm.implementation.checkpoint_store import CheckpointBytes, CheckpointStore

    synced: list[tuple[int, int]] = []
    fsync = os.fsync

    def record(descriptor):
        info = os.fstat(descriptor)
        synced.append((info.st_dev, info.st_ino))
        fsync(descriptor)

    monkeypatch.setattr(target=os, name='fsync', value=record)
    files = CheckpointStore(storage=get_manager().get_profile_storage())
    node_uuid: str = str(uuid4())
    content = CheckpointBytes(content=b'bytes')
    try:
        files.write(node_uuid=node_uuid, data=content)
        for directory in (dirpath().parent, dirpath()):
            info = directory.stat()
            assert (info.st_dev, info.st_ino) in synced
    finally:
        files.discard_one(node_uuid=node_uuid, digest=content.digest)


@pytest.mark.parametrize(
    ('checkpoint', 'digest'),
    [
        pytest.param(None, None, id='absent'),
        pytest.param('{}', None, id='yaml'),
        pytest.param('checkpoint-pickle-v2:' + 'a' * 64, None, id='unknown-version'),
        pytest.param('checkpoint-pickle-v1:' + 'a' * 64, 'a' * 64, id='valid'),
        pytest.param('checkpoint-pickle-v1:' + 'A' * 64, None, id='uppercase'),
        pytest.param('checkpoint-pickle-v1:' + 'z' * 64, None, id='non-hex'),
        pytest.param('checkpoint-pickle-v1:' + 'a' * 63, None, id='short'),
        pytest.param('checkpoint-pickle-v1:' + 'a' * 65, None, id='long'),
    ],
)
def test_checkpoint_digest_accepts_only_supported_references(checkpoint: str | None, digest: str | None):
    """Cleanup extracts digests only from valid references in the supported format."""
    from aiida.engine.persistence import _checkpoint_digest

    assert _checkpoint_digest(checkpoint=checkpoint) == digest


@pytest.mark.parametrize('carried', [pytest.param(False, id='importable'), pytest.param(True, id='carried')])
def test_rewriting_keeps_only_the_current_checkpoint(
    persister: AiidaCheckpointPersister, make_process: Callable[..., Process], carried: bool
):
    """Unchanged state isn't rewritten; changed state supersedes the previous file."""
    live = make_process(carried=carried)
    before = checkpoint_files()
    persister.save_checkpoint(live)
    first = checkpoint_digest(live.node)
    path = dirpath() / f'{live.node.uuid}-{first}.pkl'
    original_inode = path.stat().st_ino

    persister.save_checkpoint(live)
    assert checkpoint_digest(live.node) == first
    assert path.stat().st_ino == original_inode

    live.ctx.padding += 'more'
    persister.save_checkpoint(live)
    current = checkpoint_digest(live.node)
    assert current != first
    assert checkpoint_files() - before == {f'{live.node.uuid}-{current}.pkl'}
    assert persister.load_checkpoint(live.pid)['_pid'] == live.pid


def test_resaving_restores_a_missing_checkpoint_file(
    persister: AiidaCheckpointPersister, make_process: Callable[..., Process]
):
    """A file lost after its reference was stored is rewritten on the next save."""
    live = make_process()
    before = checkpoint_files()
    persister.save_checkpoint(live)
    digest = checkpoint_digest(live.node)
    path = dirpath() / f'{live.node.uuid}-{digest}.pkl'
    path.unlink()
    assert checkpoint_files() == before

    persister.save_checkpoint(live)
    assert checkpoint_digest(live.node) == digest
    assert checkpoint_files() - before == {path.name}


def test_resaving_rewrites_a_corrupted_checkpoint_file(
    persister: AiidaCheckpointPersister, make_process: Callable[..., Process]
):
    """A file with unreadable bytes and a matching reference is rewritten on the next save."""
    live = make_process()
    persister.save_checkpoint(live)
    digest = checkpoint_digest(live.node)
    path = dirpath() / f'{live.node.uuid}-{digest}.pkl'
    path.write_bytes(b'not a checkpoint')

    persister.save_checkpoint(live)

    assert persister.load_checkpoint(live.pid)['_pid'] == live.pid
    assert hashlib.sha256(path.read_bytes()).hexdigest() == checkpoint_digest(live.node)


def test_deleting_checkpoint_removes_file(persister: AiidaCheckpointPersister, make_process: Callable[..., Process]):
    """Checkpoint deletion clears the attribute and removes the class file with it."""
    live = make_process(carried=True)
    before = checkpoint_files()
    persister.save_checkpoint(live)
    persister.delete_checkpoint(live.pid)

    assert live.node.checkpoint is None
    assert checkpoint_files() == before


@pytest.mark.parametrize('operation', [pytest.param('replace', id='replace'), pytest.param('delete', id='delete')])
def test_checkpoint_survives_transaction_rollback(
    persister: AiidaCheckpointPersister,
    make_process: Callable[..., Process],
    operation: str,
):
    """Rollback preserves the file referenced by the restored checkpoint."""
    live = make_process(carried=True)
    persister.save_checkpoint(live)
    original = live.node.checkpoint
    digest = checkpoint_digest(live.node)
    storage = get_manager().get_profile_storage()

    with pytest.raises(RuntimeError, match='rollback'):
        with storage.transaction():
            if operation == 'replace':
                live.ctx.padding += 'changed'
                persister.save_checkpoint(live)
            else:
                persister.delete_checkpoint(live.pid)
            raise RuntimeError('rollback')

    assert orm.load_node(live.pid).checkpoint == original
    assert f'{live.node.uuid}-{digest}.pkl' in checkpoint_files()
    assert persister.load_checkpoint(live.pid)['_pid'] == live.pid


def test_temporary_class_files_are_outside_repository_objects(aiida_config_tmp, aiida_profile_factory):
    """Checkpoint files share cleanup with the repository without becoming object keys."""
    from aiida.orm.implementation.checkpoint_store import CheckpointBytes
    from aiida.storage.sqlite_temp import SqliteTempBackend

    with aiida_profile_factory(aiida_config_tmp, storage_backend='core.sqlite_temp'):
        storage = get_manager().get_profile_storage()
        assert isinstance(storage, SqliteTempBackend)
        repository = storage.get_repository()
        before = set(repository.list_objects())
        directory = storage.get_checkpoint_directory()
        storage.checkpoint_store.write(node_uuid=str(uuid4()), data=CheckpointBytes(content=b'bytes'))
        assert set(repository.list_objects()) == before
        storage.close()
        assert not directory.exists()


def test_a_staged_file_carries_the_node_uuid(
    persister: AiidaCheckpointPersister, make_process: Callable[..., Process], monkeypatch: pytest.MonkeyPatch
):
    """Staged filenames contain the owning node UUID for crash cleanup."""
    staged: list[str] = []
    replace = os.replace

    def record(source: str, destination: str) -> None:
        # A checkpoint save renames more than this one file, so only the ones landing in the checkpoint directory
        # are this test's business.
        if pathlib.Path(destination).parent == dirpath():
            staged.append(pathlib.Path(source).name)

        return replace(source, destination)

    monkeypatch.setattr(target=os, name='replace', value=record)

    live = make_process(carried=True)
    persister.save_checkpoint(live)

    assert staged, 'premise: a file was staged and renamed into place'
    assert all(name.startswith(f'.{live.node.uuid}-') for name in staged), staged


def test_a_partial_write_left_by_a_killed_worker_is_dropped(
    persister: AiidaCheckpointPersister, make_process: Callable[..., Process]
):
    """Checkpoint deletion removes staged files left by interrupted writes."""
    live = make_process(carried=True)
    before = checkpoint_files()
    persister.save_checkpoint(live)

    staged = dirpath() / f'.{live.node.uuid}-{uuid4().hex}'
    staged.write_bytes(b'half of a pickle')
    assert staged.name in checkpoint_files(), 'premise: the staged file is there to be collected'

    persister.delete_checkpoint(live.pid)

    assert checkpoint_files() == before


def test_superseded_file_cleanup_ignores_a_context_checksum(
    persister: AiidaCheckpointPersister, make_process: Callable[..., Process]
):
    """A context checksum does not interfere with superseded file cleanup."""
    live = make_process(carried=True)
    before = checkpoint_files()

    live.ctx.checksum = f'sha256:{"a" * 64}'
    persister.save_checkpoint(live)
    first = checkpoint_digest(live.node)
    assert first != 'a' * 64

    live.ctx.padding += 'more'
    persister.save_checkpoint(live)
    current = checkpoint_digest(live.node)

    assert current != first, 'premise: the second checkpoint carries different state'
    assert checkpoint_files() - before == {f'{live.node.uuid}-{current}.pkl'}


def test_maintenance_preserves_an_uncommitted_owner(
    persister: AiidaCheckpointPersister, make_process: Callable[..., Process]
):
    """A separate collector cannot discard files whose new owner is still uncommitted."""
    storage: StorageBackend = get_manager().get_profile_storage()
    collector: StorageBackend = type(storage)(profile=storage.profile)
    try:
        with storage.transaction():
            live: Process = make_process(carried=True, enable_persistence=False)
            persister.save_checkpoint(live)
            digest: str = checkpoint_digest(live.node)
            assert not collector.in_transaction
            owners: int = (
                orm.QueryBuilder(backend=collector).append(orm.ProcessNode, filters={'uuid': live.node.uuid}).count()
            )
            assert owners == 0
            dropped = collector.delete_orphaned_checkpoint_files()
            assert f'{live.node.uuid}-{digest}.pkl' not in [path.name for path in dropped]
        assert f'{live.node.uuid}-{digest}.pkl' in checkpoint_files()
        assert persister.load_checkpoint(live.pid)['_pid'] == live.pid
    finally:
        collector.close()


def test_maintenance_defers_uncommitted_sealing(
    persister: AiidaCheckpointPersister, make_process: Callable[..., Process]
):
    """A seal that can roll back cannot make its checkpoint files collectible."""
    live = make_process(carried=True)
    persister.save_checkpoint(live)
    digest = checkpoint_digest(live.node)
    storage = get_manager().get_profile_storage()
    with pytest.raises(RuntimeError, match='rollback'):
        with storage.transaction():
            live.node.seal()
            assert storage.delete_orphaned_checkpoint_files() == []
            assert storage.delete_orphaned_checkpoint_files(dry_run=True) == []
            msg = 'rollback'
            raise RuntimeError(msg)
    assert not orm.load_node(live.pid).is_sealed
    assert f'{live.node.uuid}-{digest}.pkl' in checkpoint_files()
    assert persister.load_checkpoint(live.pid)['_pid'] == live.pid


def _populate_mixed_directory(
    storage: StorageBackend,
) -> tuple[list[pathlib.Path], tuple[pathlib.Path, pathlib.Path]]:
    """Write foreign and orphaned checkpoint files, returning both groups."""
    directory = storage.get_checkpoint_directory()
    directory.mkdir(parents=True, exist_ok=True)
    owner = str(uuid4())
    foreign = [directory / f'{owner}-notes.txt', directory / f'{owner}-{"a" * 32}']
    for path in foreign:
        path.write_bytes(b'foreign content')
    finished = directory / f'{owner}-{"b" * 64}.pkl'
    staged = directory / f'.{owner}-{"c" * 32}'
    for path in (finished, staged):
        path.write_bytes(b'orphaned bytes')
    return foreign, (finished, staged)


@pytest.mark.usefixtures('stopped_daemon_client', 'aiida_profile')
def test_live_collection_ignores_incomplete_formats():
    """Live collection drops nothing with an incomplete filename format."""
    storage = get_manager().get_profile_storage()
    _, (finished, staged) = _populate_mixed_directory(storage)

    dropped = storage.delete_orphaned_checkpoint_files()

    assert finished not in dropped and staged not in dropped


@pytest.mark.usefixtures('stopped_daemon_client', 'aiida_profile')
def test_exclusive_collection_takes_complete_formats():
    """Exclusive collection takes both complete filename formats."""
    from aiida.manage.profile_access import ProfileAccessManager

    storage = get_manager().get_profile_storage()
    _, (finished, staged) = _populate_mixed_directory(storage)

    with ProfileAccessManager(storage.profile).lock():
        collected = set(storage.delete_orphaned_checkpoint_files(only_sealed=False))

    assert {finished, staged} <= collected


@pytest.mark.usefixtures('stopped_daemon_client', 'aiida_profile')
def test_collection_preserves_foreign_files():
    """Foreign files survive live and exclusive collection."""
    from aiida.manage.profile_access import ProfileAccessManager

    storage = get_manager().get_profile_storage()
    foreign, _ = _populate_mixed_directory(storage)

    storage.delete_orphaned_checkpoint_files()
    with ProfileAccessManager(storage.profile).lock():
        storage.delete_orphaned_checkpoint_files(only_sealed=False)

    assert all(path.read_bytes() == b'foreign content' for path in foreign)


def test_maintenance_keeps_live_checkpoint(persister: AiidaCheckpointPersister, make_process: Callable[..., Process]):
    """Live maintenance preserves checkpoint files required to load running processes."""
    live = make_process(carried=True)
    persister.save_checkpoint(live)

    get_manager().get_profile_storage().maintain(full=False)

    assert persister.load_checkpoint(live.pid)['_pid'] == live.pid


@pytest.mark.usefixtures('stopped_daemon_client')
def test_maintenance_drops_the_file_of_a_deleted_node(
    persister: AiidaCheckpointPersister, make_process: Callable[..., Process]
):
    """Live maintenance retains deleted owners' checkpoint files; full maintenance collects them."""
    from aiida.tools import delete_nodes

    live = make_process(carried=True)
    persister.save_checkpoint(live)
    filename = f'{live.node.uuid}-{checkpoint_digest(live.node)}.pkl'
    storage = get_manager().get_profile_storage()

    # A reader or backup holding the lock leaves the file to maintenance.
    with storage.checkpoint_store.retain_files():
        delete_nodes([live.node.pk], dry_run=False)
    assert filename in checkpoint_files(), 'premise: node deletion left the file'

    storage.maintain(full=False)
    assert filename in checkpoint_files()
    storage.maintain(full=True)
    assert filename not in checkpoint_files()


def test_maintenance_drops_the_file_of_a_sealed_node(
    persister: AiidaCheckpointPersister, make_process: Callable[..., Process]
):
    """Live maintenance collects checkpoint files retained by sealed nodes."""
    live = make_process(carried=True)
    persister.save_checkpoint(live)
    filename = f'{live.node.uuid}-{checkpoint_digest(live.node)}.pkl'
    assert filename in checkpoint_files(), 'premise: a file was written for this node'
    live.node.seal()

    get_manager().get_profile_storage().maintain(full=False)

    assert filename not in checkpoint_files()


def test_live_maintenance_defers_without_file_locking(
    persister: AiidaCheckpointPersister, make_process: Callable[..., Process], monkeypatch: pytest.MonkeyPatch
):
    """Live maintenance defers collection where the platform provides no file locking."""
    live = make_process(carried=True)
    persister.save_checkpoint(live)
    filename = f'{live.node.uuid}-{checkpoint_digest(live.node)}.pkl'
    live.node.seal()
    monkeypatch.setitem(sys.modules, 'fcntl', None)

    # `maintain(full=False)` runs this step and also `tqdm`, which crashes without `fcntl` on `tqdm==4.45`.
    storage = get_manager().get_profile_storage()
    storage.delete_orphaned_checkpoint_files(only_sealed=True)

    assert filename in checkpoint_files()

    # Exclusive profile access, as in full maintenance, still collects without locking.
    storage.delete_orphaned_checkpoint_files(only_sealed=False)

    assert filename not in checkpoint_files()


def test_maintenance_keeps_a_live_file_beside_an_orphaned_one(
    persister: AiidaCheckpointPersister, make_process: Callable[..., Process]
):
    """Maintenance collects sealed owners' files while retaining unsealed owners' files."""
    live = make_process(carried=True)
    sealed = make_process(carried=True)
    before = checkpoint_files()

    persister.save_checkpoint(live)
    persister.save_checkpoint(sealed)
    sealed.node.seal()

    written = checkpoint_files() - before
    kept = {name for name in written if name.startswith(live.node.uuid)}
    dropped = {name for name in written if name.startswith(sealed.node.uuid)}
    assert kept and dropped, 'premise: each of the two nodes has a file of its own'

    get_manager().get_profile_storage().maintain(full=False)

    assert checkpoint_files() - before == kept


def test_collection_dry_run_reports_eligible_files(
    persister: AiidaCheckpointPersister, make_process: Callable[..., Process]
):
    """Dry-run collection returns eligible paths and preserves their files."""
    live = make_process(carried=True)
    persister.save_checkpoint(live)
    live.node.seal()
    before = checkpoint_files()

    storage = get_manager().get_profile_storage()
    would_drop = storage.delete_orphaned_checkpoint_files(dry_run=True)

    expected = sorted(name for name in before if name.startswith(live.node.uuid))
    assert sorted(path.name for path in would_drop if path.name.startswith(live.node.uuid)) == expected
    assert checkpoint_files() == before


def test_maintenance_survives_a_file_it_cannot_delete(
    persister: AiidaCheckpointPersister, make_process: Callable[..., Process], monkeypatch: pytest.MonkeyPatch
):
    """Collection retains files whose deletion raises `PermissionError` and returns no deleted paths."""
    live = make_process(carried=True)
    persister.save_checkpoint(live)
    live.node.seal()
    before = checkpoint_files()
    assert before, 'premise: there is a file to collect'

    def refuse(self, missing_ok: bool = False) -> None:
        msg = 'Operation not permitted'
        raise PermissionError(msg)

    monkeypatch.setattr(target=pathlib.Path, name='unlink', value=refuse)
    storage = get_manager().get_profile_storage()

    assert storage.delete_orphaned_checkpoint_files() == [], 'a file that stayed is not reported as dropped'

    monkeypatch.undo()

    assert checkpoint_files() == before, 'and it is still there for the next run'


def test_maintain_dry_run_preserves_collectible_files(
    persister: AiidaCheckpointPersister, make_process: Callable[..., Process]
):
    """`maintain(dry_run=True)` preserves collectible checkpoint files."""
    live = make_process(carried=True)
    persister.save_checkpoint(live)
    live.node.seal()
    before = checkpoint_files()
    assert before, 'premise: there is a file to collect'

    get_manager().get_profile_storage().maintain(full=False, dry_run=True)

    assert checkpoint_files() == before


@pytest.mark.usefixtures('persister')
def test_maintenance_leaves_a_file_it_cannot_attribute():
    """Maintenance preserves files with unrecognized checkpoint-class filenames."""
    storage = get_manager().get_profile_storage()
    dirpath().mkdir(parents=True, exist_ok=True)
    foreign = dirpath() / 'not-a-class-byte-file.txt'
    foreign.write_text('left here by something else')

    storage.maintain(full=False)

    assert foreign.exists()
    foreign.unlink()


def test_node_deletion_deletes_checkpoint_files(
    persister: AiidaCheckpointPersister, make_process: Callable[..., Process]
):
    """Node deletion deletes the checkpoint files of deleted nodes and keeps those of other nodes."""
    from aiida.tools import delete_nodes

    before = checkpoint_files()
    deleted = make_process(carried=True)
    kept = make_process(carried=True)
    persister.save_checkpoint(deleted)
    persister.save_checkpoint(kept)
    assert len(checkpoint_files() - before) == 2, 'premise: each node has a file'

    delete_nodes([deleted.node.pk], dry_run=False)

    assert checkpoint_files() - before == {f'{kept.node.uuid}-{checkpoint_digest(kept.node)}.pkl'}


def test_checkpoint_deletion_drops_the_reference_before_the_file(
    persister: AiidaCheckpointPersister, make_process: Callable[..., Process], monkeypatch: pytest.MonkeyPatch
):
    """Delete the checkpoint attribute before its pickle file to prevent dangling references."""
    live = make_process(carried=True)
    before = checkpoint_files()
    persister.save_checkpoint(live)
    digest = checkpoint_digest(live.node)
    assert digest

    seen: list[set[str]] = []
    original = type(live.node).delete_checkpoint

    def observe(self) -> None:
        seen.append(checkpoint_files())
        original(self)

    monkeypatch.setattr(target=type(live.node), name='delete_checkpoint', value=observe)
    persister.delete_checkpoint(live.pid)
    monkeypatch.undo()

    assert seen, 'the attribute was never deleted, so the ordering was not exercised'
    assert f'{live.node.uuid}-{digest}.pkl' in seen[0], (
        'the file has to outlive the attribute that refers to it, so a kill between the two leaves only an orphan'
    )
    assert checkpoint_files() == before, 'and both are gone once it returns'


def test_checkpoint_save_writes_the_file_before_the_reference(
    persister: AiidaCheckpointPersister, make_process: Callable[..., Process], monkeypatch: pytest.MonkeyPatch
):
    """Publish the new file before updating the reference, while retaining the old file."""

    live = make_process(carried=True)
    persister.save_checkpoint(live)
    first = checkpoint_digest(live.node)

    seen: list[set[str]] = []
    original = type(live.node).set_checkpoint

    def observe(self, *, checkpoint: str) -> None:
        seen.append(checkpoint_files())
        original(self, checkpoint=checkpoint)

    monkeypatch.setattr(target=type(live.node), name='set_checkpoint', value=observe)
    live.ctx.padding += 'more'
    persister.save_checkpoint(live)
    monkeypatch.undo()

    current = checkpoint_digest(live.node)

    assert current != first, 'premise: the two checkpoints use different files'
    assert seen, 'the attribute was never written, so the ordering was not exercised'
    assert f'{live.node.uuid}-{current}.pkl' in seen[0], (
        'the bytes have to be on disk before the attribute refers to them'
    )
    assert f'{live.node.uuid}-{first}.pkl' in seen[0], 'the superseded file still revives the process until then'


_CROSS_SEED_MODULE: t.Final[str] = """\
from aiida import orm
from aiida.common.extendeddicts import AttributesFrozendict
from aiida.engine import WorkChain

KEY = AttributesFrozendict({'role': 'lookup'})


class CrossSeedWorkChain(WorkChain):
    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('x', valid_type=orm.Int)
        spec.outline(cls.check)

    def check(self):
        assert self.ctx.lookup[KEY] == self.inputs.x.value
"""

_CROSS_SEED_RESUME: t.Final[str] = """\
import sys
from pathlib import Path

from aiida import load_profile, orm
from aiida.manage.configuration.settings import AiiDAConfigDir

AiiDAConfigDir.set(Path(sys.argv[1]))
load_profile(sys.argv[2])

from aiida.engine.persistence import AiidaCheckpointPersister
from aiida.engine.processes.persistence import CheckpointContext
from aiida.manage import get_manager

pk = int(sys.argv[3])
payload = AiidaCheckpointPersister().load_checkpoint(pk)
payload.decode(CheckpointContext(runner=get_manager().get_runner())).execute()
node = orm.load_node(pk)
print(node.process_state.value, node.exit_status)
"""


def test_checkpoint_resumes_under_another_hash_seed(
    persister: AiidaCheckpointPersister, aiida_profile: Profile, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
):
    """A checkpoint saved here finishes in a fresh interpreter with a different `PYTHONHASHSEED`."""
    _ = (tmp_path / 'cross_seed.py').write_text(_CROSS_SEED_MODULE)
    _ = (tmp_path / 'resume.py').write_text(_CROSS_SEED_RESUME)
    monkeypatch.syspath_prepend(str(tmp_path))
    from cross_seed import KEY, CrossSeedWorkChain  # type: ignore[import-not-found]

    process = instantiate_process(get_manager().get_runner(), CrossSeedWorkChain, x=orm.Int(7))
    process.ctx.lookup = {KEY: 7}
    persister.save_checkpoint(process)
    process.close()

    seed: str = '2' if os.environ.get('PYTHONHASHSEED') == '1' else '1'
    pythonpath: str = os.pathsep.join(filter(None, [str(tmp_path), os.environ.get('PYTHONPATH')]))
    completed = subprocess.run(
        [
            sys.executable,
            str(tmp_path / 'resume.py'),
            str(get_manager().get_config().dirpath),
            aiida_profile.name,
            str(process.node.pk),
        ],
        capture_output=True,
        text=True,
        env={**os.environ, 'PYTHONHASHSEED': seed, 'PYTHONPATH': pythonpath},
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.splitlines()[-1] == 'finished 0', completed.stderr


@pytest.fixture
def transition_observer(
    make_process: Callable[..., Process], persister: AiidaCheckpointPersister
) -> Iterator[tuple[Process, Callable[[], TransitionSnapshot]]]:
    """Observe committed state on a separate connection during a checkpoint transition."""
    live = make_process()
    persister.save_checkpoint(live)
    storage = live.node.backend
    observer = type(storage)(profile=storage.profile)

    def snapshot() -> TransitionSnapshot:
        node = orm.ProcessNode.get_collection(backend=observer).get(pk=live.pid)
        result = (node.process_state, node.checkpoint, node.base.links.get_outgoing().all_link_labels())
        observer.get_session().rollback()
        return result

    try:
        yield live, snapshot
    finally:
        observer.close()


@pytest.mark.parametrize('failure', ['none', 'publication', 'database'])
def test_transition_checkpoint_atomicity(
    transition_observer: tuple[Process, Callable[[], TransitionSnapshot]],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    failure: str,
) -> None:
    """Outputs, state and reference commit together; a failed publication keeps the old reference."""
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError

    import aiida.engine.utils
    from aiida.engine.processes.exceptions import PersistenceError
    from aiida.engine.processes.generic.process import Process as ProcessBase
    from aiida.orm.implementation.checkpoint_store import CheckpointBytes, CheckpointStore

    live, snapshot = transition_observer
    old = snapshot()
    old_path = dirpath() / f'{live.node.uuid}-{checkpoint_digest(live.node)}.pkl'
    output = orm.Int(2).store()
    live.out('result', output)
    previous_state = live._state
    live._state = live.create_state(ProcessState.RUNNING, live.run)
    original_write = CheckpointStore.write
    notified = []
    published = []

    def write(store: CheckpointStore, *, node_uuid: str, data: CheckpointBytes) -> None:
        assert snapshot() == old, 'No transition writes may be visible before publication'
        assert old_path.exists()
        if failure == 'publication':
            raise OSError('publication failed')
        original_write(store, node_uuid=node_uuid, data=data)
        published.append(dirpath() / f'{node_uuid}-{data.digest}.pkl')

    def timestamp(node: orm.ProcessNode) -> None:
        assert snapshot() == old, 'The new reference and outputs must remain uncommitted'
        assert old_path.exists(), 'The old committed reference still needs this file'
        if failure == 'database':
            node.backend.get_session().execute(text('SELECT * FROM checkpoint_transition_missing_table'))

    def notify(process: Process, from_state: State | None) -> None:
        assert not process.node.backend.in_transaction
        notified.append((*snapshot(), old_path.exists()))

    monkeypatch.setattr(CheckpointStore, 'write', write)
    monkeypatch.setattr(aiida.engine.utils, 'set_process_state_change_timestamp', timestamp)
    monkeypatch.setattr(ProcessBase, 'on_entered', notify)
    if failure == 'database':
        with pytest.raises(DBAPIError, match='checkpoint_transition_missing_table'):
            live.on_entered(previous_state)
        assert snapshot() == old
        assert live.node.checkpoint == old[1]
        assert old_path.exists()
        assert not notified
        assert published[0].exists(), 'Rollback may leave an unreferenced newly published file'
        return

    live.on_entered(previous_state)
    errors = [record for record in caplog.records if record.levelno >= logging.ERROR]
    if failure == 'none':
        assert live.node.checkpoint != old[1]
        assert notified == [(ProcessState.RUNNING, live.node.checkpoint, ['result'], False)], (
            'Cleanup follows commit and precedes notifications'
        )
        assert published[0].exists()
        assert not errors
    else:
        assert notified == [(ProcessState.RUNNING, old[1], ['result'], True)]
        assert live.node.checkpoint == old[1]
        assert not published
        assert [record.getMessage() for record in errors] == [CHECKPOINT_FAILURE_MESSAGE]
        assert isinstance(errors[0].exc_info[1], PersistenceError)


def test_transition_checkpoint_failure_keeps_previous_checkpoint(
    transition_observer: tuple[Process, Callable[[], TransitionSnapshot]],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A failed checkpoint save is logged and the transition commits with the previous checkpoint."""
    from aiida.engine.processes.exceptions import PersistenceError
    from aiida.engine.processes.generic.process import Process as ProcessBase
    from aiida.orm.implementation.checkpoint_store import CheckpointStore

    live, snapshot = transition_observer
    old = snapshot()
    old_path = dirpath() / f'{live.node.uuid}-{checkpoint_digest(live.node)}.pkl'
    notified = []

    def fail(store: CheckpointStore, **kwargs: t.Any) -> None:
        raise OSError('publication failed')

    monkeypatch.setattr(CheckpointStore, 'write', fail)
    monkeypatch.setattr(ProcessBase, 'on_entered', lambda process, from_state: notified.append(process.state))
    live.transition_to(live.create_state(ProcessState.RUNNING, live.run))
    assert live.state == ProcessState.RUNNING
    assert not live.node.is_excepted and not live.node.is_sealed
    assert not live.future().done()
    assert notified == [ProcessState.RUNNING]
    assert snapshot() == (ProcessState.RUNNING, old[1], [])
    assert old_path.exists()
    errors = [record for record in caplog.records if record.levelno >= logging.ERROR]
    assert [record.getMessage() for record in errors] == [CHECKPOINT_FAILURE_MESSAGE]
    assert isinstance(errors[0].exc_info[1], PersistenceError)


def test_failed_finish_commit_rolls_back_exit_status(
    transition_observer: tuple[Process, Callable[[], TransitionSnapshot]], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failed `FINISHED` commit rolls back the exit status and resolves the awaited future with the error."""
    import aiida.engine.utils

    live, _ = transition_observer

    def fail(node: orm.ProcessNode) -> None:
        raise OSError('timestamp failed')

    live._state = live.create_state(ProcessState.RUNNING, live.run)
    live.out('result', orm.Int(2).store())
    future = live.future()
    monkeypatch.setattr(aiida.engine.utils, 'set_process_state_change_timestamp', fail)
    live.transition_to(live.create_state(ProcessState.FINISHED, 0, True))
    assert live.state == ProcessState.EXCEPTED
    assert orm.load_node(live.pid).exit_status is None
    assert future is live.future()
    assert str(future.exception()) == 'timestamp failed'


def test_transition_rejects_caller_transaction(
    transition_observer: tuple[Process, Callable[[], TransitionSnapshot]], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reject before state callbacks mutate memory or commit a caller-owned transaction."""
    from aiida.engine.processes.generic.process import Process as ProcessBase

    live, snapshot = transition_observer
    old = snapshot()
    old_state = live.state
    notified = []
    monkeypatch.setattr(ProcessBase, 'on_entered', lambda *args: notified.append(True))
    with live.node.backend.transaction():
        live.node.base.extras.set('uncommitted', True)
        with pytest.raises(exceptions.InvalidOperation, match='iterall'):
            live.transition_to(live.create_state(ProcessState.RUNNING, live.run))
        assert live.node.backend.in_transaction
        assert snapshot() == old
        assert live.state == old_state
        assert not notified
    assert orm.load_node(live.pid).base.extras.get('uncommitted') is True


@pytest.mark.parametrize('store_provenance', [True, False])
def test_creation_inside_caller_transaction(aiida_profile: Profile, store_provenance: bool) -> None:
    """Reject persisted creation after input validation; provenance-disabled construction remains supported."""
    storage = get_manager().get_profile_storage()
    with storage.transaction():
        before = orm.QueryBuilder().append(orm.ProcessNode).count()
        if store_provenance:
            with pytest.raises(exceptions.InvalidOperation, match='iterall'):
                PaddedWorkChain(inputs={'x': orm.Int(1)})
        else:
            live = PaddedWorkChain(inputs={'x': orm.Int(1), 'metadata': {'store_provenance': False}})
            try:
                assert not live.node.is_stored
                assert live.state == ProcessState.CREATED
            finally:
                live.close()
        assert storage.in_transaction
        assert orm.QueryBuilder().append(orm.ProcessNode).count() == before


def test_failed_creation_checkpoint_finalizes_node(aiida_profile: Profile, monkeypatch: pytest.MonkeyPatch) -> None:
    """A failed first checkpoint reraises while leaving the stored node sealed and excepted."""
    from aiida.engine.processes.exceptions import PersistenceError
    from aiida.orm.implementation.checkpoint_store import CheckpointStore

    seen: dict[str, str] = {}

    def fail(store: CheckpointStore, *, node_uuid: str, data: t.Any) -> None:
        seen['uuid'] = node_uuid
        raise OSError('no disk')

    monkeypatch.setattr(CheckpointStore, 'write', fail)
    with pytest.raises(PersistenceError, match='no disk'):
        PaddedWorkChain(inputs={'x': orm.Int(1)})

    node = orm.load_node(seen['uuid'])
    assert node.process_state == ProcessState.EXCEPTED
    assert node.exception is not None
    assert node.is_sealed
    assert node.checkpoint is None


def test_missing_persister_logs_and_commits_transition(
    transition_observer: tuple[Process, Callable[[], TransitionSnapshot]],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A transition without a persister is logged and commits with the previous checkpoint."""
    from aiida.engine.processes.generic.process import Process as ProcessBase

    live, snapshot = transition_observer
    old = snapshot()
    old_path = dirpath() / f'{live.node.uuid}-{checkpoint_digest(live.node)}.pkl'
    notified = []
    live.out('result', orm.Int(2).store())
    monkeypatch.setattr(live.runner, '_persister', None)
    monkeypatch.setattr(ProcessBase, 'on_entered', lambda process, from_state: notified.append(process.state))
    live.transition_to(live.create_state(ProcessState.RUNNING, live.run))
    assert live.state == ProcessState.RUNNING
    assert not live.node.is_sealed
    assert notified == [ProcessState.RUNNING]
    assert snapshot() == (ProcessState.RUNNING, old[1], ['result'])
    assert old_path.exists()
    errors = [record.getMessage() for record in caplog.records if record.levelno >= logging.ERROR]
    assert errors == [NO_PERSISTER_MESSAGE]


def test_missing_persister_still_allows_pause(
    transition_observer: tuple[Process, Callable[[], TransitionSnapshot]], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Pause retains its historical log-and-continue behavior when checkpointing fails."""
    live, snapshot = transition_observer
    old = snapshot()
    monkeypatch.setattr(live.runner, '_persister', None)
    assert live.pause() is True
    assert live.paused
    assert live.node.paused
    assert snapshot() == old


def test_root_commit_failure_rolls_back_before_recovery(
    transition_observer: tuple[Process, Callable[[], TransitionSnapshot]], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A rejected root commit cannot leak failed writes into EXCEPTED recovery's next commit."""
    from sqlalchemy import event
    from sqlalchemy.exc import OperationalError
    from sqlalchemy.orm import Session

    from aiida.engine.processes.generic.process import Process as ProcessBase

    live, snapshot = transition_observer
    old = snapshot()
    old_path = dirpath() / f'{live.node.uuid}-{checkpoint_digest(live.node)}.pkl'
    live.out('result', orm.Int(2).store())
    assert live.node.checkpoint == old[1]
    session = live.node.backend.get_session()
    assert session.in_transaction()
    original_terminated = Process.on_terminated
    original_entered = Process.on_entered
    notified = []
    failed = []

    def entered(process: Process, from_state: State | None) -> None:
        # on_run commits WorkChain stepper metadata; start a read transaction after that callback.
        assert process.node.checkpoint == old[1]
        original_entered(process, from_state)

    def fail_root_commit(session: Session) -> None:
        if live.state is ProcessState.RUNNING and not session.in_nested_transaction() and not failed:
            failed.append(True)
            assert live.node.checkpoint != old[1], 'The new checkpoint must be published before this failure'
            assert snapshot() == old
            raise OperationalError('COMMIT', {}, RuntimeError('root commit failed'))

    def terminated(process: Process) -> None:
        assert snapshot() == (ProcessState.EXCEPTED, old[1], [])
        assert process.node.checkpoint == old[1]
        assert old_path.exists()
        original_terminated(process)

    event.listen(session, 'before_commit', fail_root_commit)
    monkeypatch.setattr(Process, 'on_entered', entered)
    monkeypatch.setattr(Process, 'on_terminated', terminated)
    monkeypatch.setattr(ProcessBase, 'on_entered', lambda process, from_state: notified.append(process.state))
    try:
        live.transition_to(live.create_state(ProcessState.RUNNING, live.run))
    finally:
        event.remove(session, 'before_commit', fail_root_commit)
    assert failed == [True]
    assert live.node.is_excepted and live.node.is_sealed
    assert isinstance(live.future().exception(), OperationalError)
    assert not live._transitioning
    assert notified == [ProcessState.EXCEPTED]
    assert live.node.checkpoint is None
