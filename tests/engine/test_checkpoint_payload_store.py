###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for where :class:`aiida.engine.persistence.AiidaCheckpointPersister` puts a checkpoint payload."""

import pytest

from aiida import orm
from aiida.engine import WorkChain
from aiida.engine.persistence import MAX_ATTRIBUTE_PAYLOAD_LENGTH, AiidaCheckpointPersister
from aiida.engine.utils import instantiate_process
from aiida.manage import get_manager
from aiida.orm import ProcessNode


class Padded(WorkChain):
    """A workchain whose context is as large as the test asks for."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('x', valid_type=orm.Int)
        spec.outline(cls.record)

    def record(self):
        pass


@pytest.fixture
def persister(aiida_profile):
    """Yield a persister, with whatever the runner already wrote for the process cleared."""
    return AiidaCheckpointPersister()


@pytest.fixture
def process(aiida_profile):
    """Yield a factory for a live process whose checkpoint is as large as asked.

    Each one registers an RPC subscriber under its pid on the communicator, which outlives the test, so a later
    process built with the same pid is refused. Closing them here keeps that to this module.
    """
    created = []

    def factory(padding=0):
        instance = instantiate_process(get_manager().get_runner(), Padded, x=orm.Int(1))
        # The context is what a running workchain accumulates, and it is what makes a real checkpoint large.
        instance.ctx.padding = 'x' * padding
        instance.node.delete_checkpoint()
        created.append(instance)
        return instance

    yield factory

    for instance in created:
        instance.close()


def managed_objects():
    """Return the managed objects in the repository, so a test can tell whether one was added or dropped."""
    container = get_manager().get_profile_storage().get_repository()._container

    return set(container.list_managed_objects())


def test_a_small_payload_stays_on_the_node(persister, process):
    """Test that an ordinary checkpoint is an attribute, which is cheaper for it than an object."""
    live = process()
    before = managed_objects()
    persister.save_checkpoint(live)

    assert not live.node.checkpoint.startswith(ProcessNode.CHECKPOINT_OBJECT_PREFIX)
    assert len(live.node.checkpoint) < MAX_ATTRIBUTE_PAYLOAD_LENGTH
    assert managed_objects() == before


def test_a_large_payload_goes_to_the_repository(persister, process):
    """Test that a checkpoint past the plateau is an object, with the node holding only its key."""
    live = process(padding=MAX_ATTRIBUTE_PAYLOAD_LENGTH)
    before = managed_objects()
    persister.save_checkpoint(live)

    assert live.node.checkpoint.startswith(ProcessNode.CHECKPOINT_OBJECT_PREFIX)
    assert len(managed_objects() - before) == 1


@pytest.mark.parametrize('padding', [0, MAX_ATTRIBUTE_PAYLOAD_LENGTH])
def test_both_destinations_round_trip(persister, process, padding):
    """Test that a payload comes back whichever store it went to."""
    live = process(padding=padding)
    persister.save_checkpoint(live)

    assert persister.load_checkpoint(live.pid)['_pid'] == live.pid


def test_rewriting_drops_the_object_it_replaces(persister, process):
    """Test that a process checkpointed twice leaves one object rather than two.

    A checkpoint is rewritten at every transition, and the repository collects objects by what references them,
    so nothing else would remove the one that was superseded.
    """
    live = process(padding=MAX_ATTRIBUTE_PAYLOAD_LENGTH)
    before = managed_objects()

    persister.save_checkpoint(live)
    first = live.node.checkpoint

    live.ctx.padding += 'more'
    persister.save_checkpoint(live)

    assert live.node.checkpoint != first
    assert len(managed_objects() - before) == 1
    assert persister.load_checkpoint(live.pid)['_pid'] == live.pid


@pytest.mark.parametrize('padding', [0, MAX_ATTRIBUTE_PAYLOAD_LENGTH])
def test_an_unchanged_payload_is_not_rewritten(persister, process, padding, monkeypatch):
    """Test that saving the same payload twice writes the node once, and leaves it readable.

    The repository addresses an object by its content, so an unchanged payload keeps its key; writing it again
    would cost a row rewrite, and dropping the key it replaced would delete the object it still names.
    """
    live = process(padding=padding)
    persister.save_checkpoint(live)

    writes = []
    monkeypatch.setattr(type(live.node), 'set_checkpoint', lambda self, value: writes.append(value))
    persister.save_checkpoint(live)
    monkeypatch.undo()

    assert writes == []
    assert persister.load_checkpoint(live.pid)['_pid'] == live.pid


def test_deleting_the_checkpoint_drops_the_object(persister, process):
    """Test that a terminating process leaves nothing behind in either store."""
    live = process(padding=MAX_ATTRIBUTE_PAYLOAD_LENGTH)
    before = managed_objects()
    persister.save_checkpoint(live)
    persister.delete_checkpoint(live.pid)

    assert live.node.checkpoint is None
    assert managed_objects() == before


def test_maintenance_keeps_a_live_checkpoint_object(persister, process):
    """Test that the object of a running process survives the sweep for unreferenced objects.

    The collector derives what is referenced from `repository_metadata`, which says nothing about a checkpoint.
    A managed object is the answer: it is omitted from the listing the sweep works off, so it is never a
    candidate.
    """
    live = process(padding=MAX_ATTRIBUTE_PAYLOAD_LENGTH)
    persister.save_checkpoint(live)
    key = live.node.checkpoint[len(ProcessNode.CHECKPOINT_OBJECT_PREFIX) :]

    storage = get_manager().get_profile_storage()

    assert key not in storage.get_unreferenced_keyset()
    assert key not in set(storage.get_repository().list_objects())
    assert key in managed_objects()

    persister.delete_checkpoint(live.pid)

    assert key not in managed_objects()


def test_a_deleted_node_leaves_its_checkpoint_object(persister, process):
    """Test that deleting a node leaves its payload behind, since the sweep never considers a managed object.

    Collecting those is the writer's job, and nothing in `verdi node delete` knows about checkpoints yet.
    """
    from aiida.tools import delete_nodes

    live = process(padding=MAX_ATTRIBUTE_PAYLOAD_LENGTH)
    persister.save_checkpoint(live)
    key = live.node.checkpoint[len(ProcessNode.CHECKPOINT_OBJECT_PREFIX) :]
    delete_nodes([live.node.pk], dry_run=False)

    assert key not in get_manager().get_profile_storage().get_unreferenced_keyset()
    assert key in managed_objects()
