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
import json
import logging
import sys

import pytest

from aiida import orm
from aiida.common import callables, loaders
from aiida.common.processes import ProcessState
from aiida.engine import Process, calcfunction, run
from aiida.engine.persistence import AiidaCheckpointPersister
from aiida.engine.processes import persistence
from aiida.engine.processes.persistence import (
    META,
    META__CLASS_NAME,
    META__CLASS_PAYLOAD,
    META__OBJECT_LOADER,
    META__USER,
    CheckpointContext,
    CheckpointFuture,
    CheckpointPayload,
    CheckpointSerializable,
    identifier_resolves_for_reader,
)
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


class ImportableSerializable(CheckpointSerializable):
    """Defined by this module, so its identifier resolves wherever this module can be imported."""


class NestedHolder:
    """Holds a class whose qualified name the loader's ``module:name`` identifier form cannot express."""

    class Nested(CheckpointSerializable):
        """Importable by following its qualified name, yet no identifier the loader builds reaches it."""


@calcfunction
def module_level_calcfunction(value):
    """A process function this module defines, so the function that identifies its process resolves."""
    return value


def class_identity(cls, monkeypatch, reader_paths):
    """Return the metadata that would record ``cls`` for a reader searching ``reader_paths``."""
    monkeypatch.setattr(persistence, 'reader_import_paths', lambda: reader_paths)
    out_state: dict = {}
    CheckpointSerializable._save_class_identity(out_state, cls, loaders.get_object_loader())
    return out_state[META]


def test_class_identity_uses_a_name_the_reader_resolves(monkeypatch):
    """Test that a class the reader can import is recorded by name alone."""
    metadata = class_identity(ImportableSerializable, monkeypatch, tuple(sys.path))

    assert metadata[META__CLASS_NAME] == f'{__name__}:ImportableSerializable'
    assert META__CLASS_PAYLOAD not in metadata


@pytest.fixture
def user_serializable(tmp_path):
    """Yield a class from a directory on this interpreter's path only, as a user's own module would be."""
    (tmp_path / 'usercheckpoint.py').write_text(
        'from aiida.engine.processes.persistence import CheckpointSerializable\n\n\n'
        'class UserSerializable(CheckpointSerializable):\n'
        '    def __init__(self, value="from the user module"):\n'
        '        self.value = value\n\n'
        '    def save_instance_state(self, out_state, save_context):\n'
        '        super().save_instance_state(out_state, save_context)\n'
        "        out_state['value'] = self.value\n\n"
        '    def load_instance_state(self, saved_state, load_context):\n'
        '        super().load_instance_state(saved_state, load_context)\n'
        "        self.value = saved_state['value']\n"
    )
    sys.path.insert(0, str(tmp_path))

    try:
        import usercheckpoint

        yield usercheckpoint.UserSerializable
    finally:
        sys.path.remove(str(tmp_path))
        del sys.modules['usercheckpoint']


def reader_without(tmp_path):
    """The paths of an interpreter that has everything this one has, except the user's own directory."""
    return tuple(entry for entry in sys.path if entry != str(tmp_path))


def test_class_identity_carries_a_class_the_reader_cannot_import(user_serializable, monkeypatch, tmp_path):
    """Test that a class whose module the reader lacks travels in the checkpoint, and comes back out of it."""
    metadata = class_identity(user_serializable, monkeypatch, reader_without(tmp_path))

    assert callables.loads(metadata[META__CLASS_PAYLOAD]) is user_serializable


def test_class_identity_of_a_process_function_stays_a_name(monkeypatch):
    """Test that a process built from a function is judged by the function that identifies it.

    Its class is built for each function and no name refers to that class, so asking about the class itself would
    carry every process function ever run into its own checkpoint, and change its node hash with it.
    """
    metadata = class_identity(module_level_calcfunction.process_class, monkeypatch, tuple(sys.path))

    assert metadata[META__CLASS_NAME].endswith(':module_level_calcfunction')
    assert META__CLASS_PAYLOAD not in metadata


def test_class_identity_keeps_the_name_when_the_class_cannot_be_serialized(monkeypatch):
    """Test that a class that refuses to serialize is left exactly as it was recorded before.

    A class defined inside a function closes over whatever that function held, which may be a node, and a node
    refuses to be pickled. Failing the checkpoint over it would break a process that used to run.
    """
    node = orm.Int(1).store()

    class ClosesOverANode(CheckpointSerializable):
        """Its methods hold a node, so serializing the class means serializing that node."""

        def value(self):
            return node

    class ClosesOverNothing(CheckpointSerializable):
        """Defined in the same place, and nothing stops it being written into the checkpoint."""

    # No name reaches either, so both get as far as being offered to the serializer. Only one survives it, which is
    # what says the refusal was handled rather than never reached.
    refused = class_identity(ClosesOverANode, monkeypatch, tuple(sys.path))
    carried = class_identity(ClosesOverNothing, monkeypatch, tuple(sys.path))

    assert META__CLASS_PAYLOAD not in refused
    assert refused[META__CLASS_NAME] == f'{__name__}:{ClosesOverANode.__qualname__}'
    assert META__CLASS_PAYLOAD in carried


def test_class_identity_of_a_class_no_identifier_reaches(monkeypatch):
    """Test that a class the loader cannot identify is recorded rather than raising out of the checkpoint.

    ``identify_object`` builds ``module:name`` and then resolves it, which fails for a class defined inside a
    function. Saving a checkpoint is not where that should surface.
    """

    class Local(CheckpointSerializable):
        """Nothing in its module is bound to this name, so no identifier reaches it."""

    with pytest.raises(ImportError):
        loaders.get_object_loader().identify_object(Local)

    metadata = class_identity(Local, monkeypatch, None)

    assert metadata[META__CLASS_NAME] == f'{__name__}:{Local.__qualname__}'
    assert callables.loads(metadata[META__CLASS_PAYLOAD]).__qualname__ == Local.__qualname__


def test_class_identity_carries_a_nested_class_without_a_daemon(monkeypatch):
    """Test that a class the loader's identifier form cannot express travels rather than keeping a name.

    ``resolves_here`` follows a dotted qualified name and says yes, while the loader builds ``module:name`` and
    resolves that, which reaches nothing. Only both answers together say whether a name is worth keeping.
    """
    with pytest.raises(ImportError):
        loaders.get_object_loader().identify_object(NestedHolder.Nested)

    assert callables.resolves_here(NestedHolder.Nested)

    metadata = class_identity(NestedHolder.Nested, monkeypatch, None)

    assert metadata[META__CLASS_NAME] == f'{__name__}:NestedHolder.Nested'
    assert callables.loads(metadata[META__CLASS_PAYLOAD]) is NestedHolder.Nested


def test_class_identity_carries_a_main_class_without_a_daemon(monkeypatch):
    """Test that a class defined in ``__main__`` travels even when nothing is known about the reader.

    Submitting while the daemon is down is ordinary: the task waits in the broker and a worker rebuilds the process
    from the checkpoint once it starts. ``__main__`` is that worker's own entry point, so the name that would
    otherwise be kept reaches nothing there.
    """

    class Notebookish(CheckpointSerializable):
        """Stands in for a class defined in a notebook cell, which is bound in ``__main__`` as this one is."""

    Notebookish.__module__ = '__main__'
    Notebookish.__qualname__ = 'Notebookish'
    Notebookish.__name__ = 'Notebookish'
    monkeypatch.setattr(sys.modules['__main__'], 'Notebookish', Notebookish, raising=False)

    metadata = class_identity(Notebookish, monkeypatch, None)

    assert metadata[META__CLASS_NAME] == '__main__:Notebookish'
    assert callables.loads(metadata[META__CLASS_PAYLOAD]).__qualname__ == 'Notebookish'


def test_load_prefers_a_carried_class_over_the_name(user_serializable, monkeypatch, tmp_path):
    """Test that a class carried in the checkpoint is the one that comes back, without any name being resolved."""
    monkeypatch.setattr(persistence, 'reader_import_paths', lambda: reader_without(tmp_path))
    saved = user_serializable('carried').save()

    assert CheckpointSerializable._get_class_payload(saved) is not None

    # The name is now unresolvable, so anything that comes back came out of the payload.
    saved[META][META__CLASS_NAME] = 'no.such.module:Missing'

    assert CheckpointSerializable.load(saved).value == 'carried'


def test_identifier_resolves_for_reader_without_a_daemon(monkeypatch):
    """Test that nothing is claimed about a reader nothing is known about, which is how this behaved before."""
    monkeypatch.setattr(persistence, 'reader_import_paths', lambda: None)

    assert identifier_resolves_for_reader('json:dumps') is True


def test_identifier_resolves_for_reader_leaves_an_unfamiliar_form_alone(monkeypatch):
    """Test that an identifier from another loader is trusted rather than guessed at."""
    monkeypatch.setattr(persistence, 'reader_import_paths', lambda: ())

    assert identifier_resolves_for_reader('an-opaque-identifier') is True


def test_modules_unimportable_in_refuses_an_implausible_answer(caplog):
    """Test that paths which make almost everything look missing are distrusted rather than acted on.

    Carrying the interpreter's own machinery does not merely waste bytes: registering ``cloudpickle`` itself by
    value recurses until the stack is gone. An answer that wide means the paths are wrong, so keep names instead.
    """
    with caplog.at_level('WARNING'):
        carried = persistence.modules_unimportable_in(())

    # `None` rather than an empty mapping: the latter would say the reader lacks nothing, which sends the callable
    # down the payload branch carrying none of what it needs.
    assert carried is None
    assert 'look wrong' in caplog.text


def test_carried_modules_keeps_the_name_when_the_reader_is_not_believable(monkeypatch):
    """Test that an importable callable keeps its name when the reader's paths cannot be trusted.

    Writing a payload instead would carry none of the modules it needs, and fail at load rather than here.
    """
    monkeypatch.setattr(persistence, 'reader_import_paths', lambda: ('/nowhere',))

    assert persistence.carried_modules(json.dumps) is None


def test_identifier_resolves_for_reader_refuses_a_qualname_going_nowhere(monkeypatch):
    """Test that a name whose attribute path leads nowhere here is not offered to a reader either.

    A class defined inside a function carries ``<locals>`` in its qualified name, and its module resolving says
    nothing about whether that path can be followed.
    """
    monkeypatch.setattr(persistence, 'reader_import_paths', lambda: tuple(sys.path))

    def make():
        class Local:
            pass

        return Local

    identifier = f'{__name__}:{make().__qualname__}'

    assert '<locals>' in identifier
    assert persistence.identifier_resolves_for_reader(
        f'{__name__}:test_identifier_resolves_for_reader_refuses_a_qualname_going_nowhere'
    )
    assert not persistence.identifier_resolves_for_reader(identifier)


def test_modules_unimportable_in_acts_on_a_plausible_one(tmp_path):
    """Test that the ordinary answer, a handful of modules, is passed through."""
    (tmp_path / 'plausible_lib.py').write_text('value = 1\n')
    sys.path.insert(0, str(tmp_path))

    try:
        import plausible_lib  # noqa: F401

        carried = persistence.modules_unimportable_in(tuple(p for p in sys.path if p != str(tmp_path)))
    finally:
        sys.path.remove(str(tmp_path))
        del sys.modules['plausible_lib']

    assert 'plausible_lib' in carried
    assert len(carried) * 2 <= len(sys.modules), 'the ordinary answer is a handful, not most of what is loaded'


def test_load_falls_back_to_the_name_when_the_carried_class_will_not_load(
    user_serializable, monkeypatch, caplog, tmp_path
):
    """Test that a payload that cannot be deserialized is answered with the name recorded beside it.

    A submitter whose daemon cannot import a class carries it, and a worker that can import it may still fail to
    deserialize it, on nothing more than a difference in interpreter or ``cloudpickle`` version.
    """
    monkeypatch.setattr(persistence, 'reader_import_paths', lambda: reader_without(tmp_path))
    out_state = user_serializable(value='carried').save()

    assert out_state[META][META__CLASS_PAYLOAD], 'the class was not carried, so there is no fallback to test'

    out_state[META][META__CLASS_PAYLOAD] = b'not a pickle'

    with caplog.at_level(logging.WARNING, logger=persistence.LOGGER.name):
        loaded = CheckpointSerializable.load(out_state)

    assert isinstance(loaded, user_serializable)
    assert loaded.value == 'carried'
    assert 'recorded name is being followed instead' in caplog.text


def test_the_refusal_to_carry_is_reported_once_per_path_list(caplog):
    """Test that paths describing another machine are complained about once, not once per checkpoint.

    This runs on every checkpoint of every process, so a deployment whose reported paths belong to another machine
    would otherwise repeat the warning on every state transition it makes.
    """
    elsewhere = ('/srv/pod/venv/lib/python3.12/site-packages',)
    persistence._REFUSED_READER_PATHS.discard(elsewhere)

    with caplog.at_level(logging.WARNING, logger=persistence.LOGGER.name):
        for _ in range(3):
            assert persistence.modules_unimportable_in(elsewhere) is None

    assert caplog.text.count('refusing to carry') == 1
