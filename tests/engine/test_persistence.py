###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test persisting via the AiidaCheckpointPersister."""

import asyncio
import dataclasses
import hashlib
import typing as t
from collections.abc import Callable

import pytest

from aiida import orm
from aiida.common import callables, loaders
from aiida.common.processes import ProcessState
from aiida.engine import Process, WorkChain, persistence, run
from aiida.engine.persistence import AiidaCheckpointPersister
from aiida.engine.processes import _class_identity
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
from aiida.engine.utils import instantiate_process
from aiida.manage import get_manager
from aiida.manage.configuration import Profile
from aiida.orm import ProcessNode
from tests.utils.processes import DummyProcess


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


A_BUNDLE_BIGGER_THAN_ANY_REAL_ONE: t.Final = 200_000
"""Context large enough that a bundle carrying it would tempt a size threshold.

Nothing in the write path branches on size, so this pins the absence of one: the bundle stays in the attribute
however big it grows, and only the class bytes ever leave. Adding a threshold later fails here.
"""


class Padded(WorkChain):
    """A workchain whose context is as large as the test requires."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('x', valid_type=orm.Int)
        spec.outline(cls.record)

    def record(self):
        pass


@pytest.fixture
def persister(aiida_profile: Profile):
    """Yield a persister, with whatever the runner already wrote for the process cleared."""
    return AiidaCheckpointPersister()


@pytest.fixture
def process(aiida_profile: Profile):
    """Yield a factory for a live process, whose checkpoint carries bytes and is padded to the requested size.

    Each one registers an RPC subscriber under its pid on the communicator, which outlives the test, so a later
    process built with the same pid is refused. Closing them here keeps that to this module.
    """
    created = []

    def factory(padding: int = 0, carried: bool = False):
        process_class = Padded

        if carried:
            # Defined here, so no identifier reaches it and the checkpoint has to carry the class as bytes.
            class Local(Padded):
                pass

            process_class = Local

        instance = instantiate_process(get_manager().get_runner(), process_class, x=orm.Int(1))
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


def dirpath():
    """Return the process class byte file directory of the loaded profile."""
    return persistence._checkpoint_classes_dirpath()


def checkpoint_classes():
    """Return the names of the checkpoint class files, so a test can detect one being added or dropped."""
    if not dirpath().exists():
        return set()

    return {path.name for path in dirpath().iterdir()}


def carried_digest(node):
    """Return the digest the checkpoint of ``node`` refers to, or ``None`` where it carries nothing."""
    import re

    match = re.search(f'{ProcessNode.CLASS_BYTES_PREFIX}([0-9a-f]{{64}})', node.checkpoint)

    return match.group(1) if match else None


def test_a_checkpoint_carrying_nothing_writes_no_file(
    persister: AiidaCheckpointPersister, process: Callable[..., Process]
):
    """A bundle a name recovers whole is text, so nothing leaves the database."""
    live = process()
    before = checkpoint_classes()
    persister.save_checkpoint(live)

    assert carried_digest(live.node) is None
    assert checkpoint_classes() == before
    assert persister.load_checkpoint(live.pid)['_pid'] == live.pid


def record_a_different_class(monkeypatch: pytest.MonkeyPatch, live: Process) -> None:
    """Make the next save record a different class for ``live``, which only editing the cell would otherwise do.

    Real bytes rather than a stand-in string, so what the checkpoint refers to stays loadable.
    """
    recorded_for = _class_identity.identity_policy.recorded_for

    def changed(*, value, loader):
        identity = recorded_for(value=value, loader=loader)

        if value is not type(live):
            return identity

        return dataclasses.replace(identity, class_bytes=callables.dumps(value=Padded))

    monkeypatch.setattr(_class_identity.identity_policy, 'recorded_for', changed)


@pytest.mark.parametrize('padding', [0, A_BUNDLE_BIGGER_THAN_ANY_REAL_ONE])
def test_only_the_carried_class_leaves_the_attribute(
    persister: AiidaCheckpointPersister, process: Callable[..., Process], padding: int
):
    """The bundle stays in the attribute whatever its size; only the process class bytes go to a file."""
    live = process(padding=padding, carried=True)
    before = checkpoint_classes()
    persister.save_checkpoint(live)

    digest = carried_digest(live.node)

    assert digest is not None
    assert checkpoint_classes() - before == {f'{live.node.uuid}-{digest}.pkl'}
    assert live.node.checkpoint.startswith('!aiida:bundle'), 'the bundle itself still lives on the node'
    assert '!!binary' not in live.node.checkpoint, 'no bytes in the attributes column'


def test_the_digest_is_the_digest_of_the_class_bytes(
    persister: AiidaCheckpointPersister, process: Callable[..., Process]
):
    """The bundle refers to the file, which is what lets a crash between the writes leave no dangling reference."""
    live = process(carried=True)
    persister.save_checkpoint(live)

    digest = carried_digest(live.node)

    assert digest == hashlib.sha256((dirpath() / f'{live.node.uuid}-{digest}.pkl').read_bytes()).hexdigest()


@pytest.mark.parametrize('carried', [False, True])
def test_a_checkpoint_round_trips(persister: AiidaCheckpointPersister, process: Callable[..., Process], carried: bool):
    """A checkpoint comes back whether or not it carried a class, which is the one branch in the write path."""
    live = process(carried=carried)
    persister.save_checkpoint(live)

    assert persister.load_checkpoint(live.pid)['_pid'] == live.pid


def test_a_carried_class_comes_back_as_the_class(persister: AiidaCheckpointPersister, process: Callable[..., Process]):
    """Loading has to put the bytes back where the bundle refers to them, or the process cannot be rebuilt."""
    live = process(carried=True)
    persister.save_checkpoint(live)

    payload = persister.load_checkpoint(live.pid)

    assert isinstance(payload[META][META__CLASS_BYTES], bytes)
    assert callables.loads(payload[META][META__CLASS_BYTES]) is type(live)


@pytest.mark.parametrize(
    'class_changes',
    (
        # A bundle changes far more often than the class it carries, and then both saves refer to one file.
        pytest.param(False, id='the-class-is-the-same-and-so-is-its-file'),
        # Only a class that changed reaches the discard of the file the last save wrote.
        pytest.param(True, id='the-superseded-file-goes'),
    ),
)
def test_rewriting_leaves_exactly_one_class_byte_file(
    persister: AiidaCheckpointPersister,
    process: Callable[..., Process],
    monkeypatch: pytest.MonkeyPatch,
    class_changes: bool,
):
    """Every write lands on a path of its own, and the superseded file goes once the bundle refers to the new one.

    The exact set is what pins all three of those at once: the new file present, the old one gone where the class
    changed and kept where it did not, and nothing else added either way.
    """
    live = process(carried=True)
    before = checkpoint_classes()
    persister.save_checkpoint(live)
    first = carried_digest(live.node)

    if class_changes:
        record_a_different_class(monkeypatch, live)

    live.ctx.padding += 'more'
    persister.save_checkpoint(live)
    current = carried_digest(live.node)

    assert (current != first) is class_changes
    assert checkpoint_classes() - before == {f'{live.node.uuid}-{current}.pkl'}
    assert persister.load_checkpoint(live.pid)['_pid'] == live.pid


def test_deleting_the_checkpoint_drops_the_class_byte_file(
    persister: AiidaCheckpointPersister, process: Callable[..., Process]
):
    live = process(carried=True)
    before = checkpoint_classes()
    persister.save_checkpoint(live)
    persister.delete_checkpoint(live.pid)

    assert live.node.checkpoint is None
    assert checkpoint_classes() == before


def test_maintenance_keeps_a_live_class_byte_file(persister: AiidaCheckpointPersister, process: Callable[..., Process]):
    """The sweep for unreferenced repository objects derives what is referenced from ``repository_metadata``, which
    covers no checkpoint, so a file the repository held would be a candidate for collection while its
    process is still running.
    """
    live = process(carried=True)
    persister.save_checkpoint(live)

    get_manager().get_profile_storage().maintain(full=False)

    assert persister.load_checkpoint(live.pid)['_pid'] == live.pid


def test_a_deleted_node_leaves_a_class_byte_file_carrying_its_uuid(
    persister: AiidaCheckpointPersister, process: Callable[..., Process]
):
    """Collecting those is the writer's job, and nothing in ``verdi node delete`` reaches checkpoints yet.
    Naming the file after the node is what lets one be found afterwards.
    """
    from aiida.tools import delete_nodes

    live = process(carried=True)
    persister.save_checkpoint(live)
    uuid = live.node.uuid
    delete_nodes([live.node.pk], dry_run=False)

    assert any(name.startswith(uuid) for name in checkpoint_classes())
    assert not orm.QueryBuilder().append(orm.Node, filters={'uuid': uuid}).all()


def test_deleting_the_checkpoint_on_a_storage_without_class_byte_files(
    persister: AiidaCheckpointPersister, process: Callable[..., Process], monkeypatch: pytest.MonkeyPatch
):
    """A storage plugin that predates the byte files raises where asked for their directory, and a process that
    carried no class has nothing there anyway, so its checkpoint still has to go when it terminates.
    """
    from aiida.manage import get_manager

    live = process()
    persister.save_checkpoint(live)

    def keeps_none(self):
        msg = 'keeps no checkpoint class files'
        raise NotImplementedError(msg)

    monkeypatch.setattr(type(get_manager().get_profile_storage()), 'get_checkpoint_classes_dirpath', keeps_none)

    persister.delete_checkpoint(live.pid)

    assert live.node.checkpoint is None


def test_the_class_byte_file_is_there_before_the_attribute_refers_to_it(
    persister: AiidaCheckpointPersister, process: Callable[..., Process], monkeypatch: pytest.MonkeyPatch
):
    """The order of the two writes is the whole of the crash-safety argument, and it is invisible once
    ``save_checkpoint`` has returned: both orderings leave the same files behind. Observing the directory at the
    moment the attribute flips is what tells them apart.
    """
    import dataclasses

    from aiida.engine.processes import _class_identity

    live = process(carried=True)
    persister.save_checkpoint(live)
    first = carried_digest(live.node)

    # The class has to differ between the two saves, or the file the second one writes is already on disk from the
    # first and either ordering looks the same.
    recorded_for = _class_identity.identity_policy.recorded_for

    def changed(*, value, loader):
        identity = recorded_for(value=value, loader=loader)

        return dataclasses.replace(identity, class_bytes=b'a different class') if value is type(live) else identity

    monkeypatch.setattr(_class_identity.identity_policy, 'recorded_for', changed)

    seen: list[set[str]] = []
    original = type(live.node).set_checkpoint

    def observe(self, *, checkpoint: str) -> None:
        seen.append(checkpoint_classes())
        original(self, checkpoint=checkpoint)

    monkeypatch.setattr(type(live.node), 'set_checkpoint', observe)
    live.ctx.padding += 'more'
    persister.save_checkpoint(live)
    monkeypatch.undo()

    current = carried_digest(live.node)

    assert current != first, 'the class has to change, or the ordering is unobservable'
    assert seen, 'the attribute was never written, so the ordering was not exercised'
    assert f'{live.node.uuid}-{current}.pkl' in seen[0], (
        'the bytes have to be on disk before the attribute refers to them'
    )
    assert f'{live.node.uuid}-{first}.pkl' in seen[0], 'the superseded file still revives the process until then'
