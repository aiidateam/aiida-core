###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the local state of a collab."""

import threading

import pytest

from aiida import get_profile
from aiida.common import timezone
from aiida.manage.configuration.settings import AiiDAConfigPathResolver
from aiida.tools.collab.state import CollabEvent, CollabState, import_lock, import_lock_held

PEER = 'http://100.64.0.2:9137'


@pytest.mark.usefixtures('config_with_profile')
def test_load_without_file():
    """Test that a profile that never synced loads as empty state instead of raising."""
    profile = get_profile()
    state = CollabState.load(profile)

    assert state.filepath == AiiDAConfigPathResolver().collab_dir / f'{profile.uuid}.json'
    assert not state.filepath.exists()
    assert state.cursors == {}
    assert state.tombstones == set()
    assert state.events == []


@pytest.mark.usefixtures('config_with_profile')
def test_save_load():
    """Test that the cursors, the tombstones and the events survive a save and load cycle."""
    profile = get_profile()
    state = CollabState.load(profile)
    state.cursors[PEER] = timezone.now()
    state.tombstones.update(['uuid-one', 'uuid-two'])
    state.events.append(CollabEvent(time=timezone.now(), direction='pull', peer=PEER, uuids=['uuid-three'], size=128))
    state.save()

    loaded = CollabState.load(profile)

    assert loaded.cursors == state.cursors
    assert loaded.tombstones == state.tombstones
    assert loaded.events == state.events


def test_imported_uuids_since(tmp_path):
    """Test that the imported UUIDs are those of pull events at or after the instant, from any peer."""
    early, late = timezone.now(), timezone.now()
    state = CollabState(
        filepath=tmp_path / 'state.json',
        events=[
            CollabEvent(time=early, direction='pull', peer=PEER, uuids=['uuid-early'], size=1),
            CollabEvent(time=late, direction='push', peer=PEER, uuids=['uuid-pushed'], size=1),
            CollabEvent(time=late, direction='pull', peer='http://other:9137', uuids=['uuid-late'], size=1),
        ],
    )

    assert state.imported_uuids_since(None) == {'uuid-early', 'uuid-late'}
    assert state.imported_uuids_since(late) == {'uuid-late'}


def test_compaction(tmp_path, monkeypatch):
    """Test that saving past the threshold folds the oldest events into one synthetic event per direction.

    No UUID is lost, of either the imported nodes or the refreshed extras. Any query bounded after the horizon is
    unchanged; one bounded inside the folded range may see more than it strictly should (over-delivery, dropped by
    the manifest diff and the mtime comparison), but never less.
    """
    from datetime import timedelta

    from aiida.tools.collab import state as state_module

    monkeypatch.setattr(state_module, 'COMPACT_THRESHOLD', 4)

    base = timezone.now()
    times = [base + timedelta(seconds=index) for index in range(6)]
    directions = ['pull', 'push', 'refresh', 'pull', 'pull', 'refresh']
    state = CollabState(filepath=tmp_path / 'state.json')

    for index, (instant, direction) in enumerate(zip(times, directions)):
        state.events.append(CollabEvent(time=instant, direction=direction, peer=PEER, uuids=[f'uuid-{index}'], size=1))

    ever = state.imported_uuids_since(None)
    since_inside = state.imported_uuids_since(times[3])
    since_after = state.imported_uuids_since(times[5])
    refreshed_ever = state.refreshed_uuids_since(None)

    state.save()
    loaded = CollabState.read(tmp_path / 'state.json')

    assert len(loaded.events) == 5, 'four folded into one synthetic event per direction, the newest two kept'
    assert {event.peer for event in loaded.events[:3]} == {state_module.COMPACTED_PEER}
    assert {event.time for event in loaded.events[:3]} == {times[3]}, 'the synthetic events sit at the horizon'
    assert loaded.imported_uuids_since(None) == ever
    assert loaded.imported_uuids_since(times[5]) == since_after
    assert loaded.imported_uuids_since(times[3]) >= since_inside
    assert loaded.refreshed_uuids_since(None) == refreshed_ever, 'a folded refresh must keep offering its nodes'

    # Saving again folds the same events again, which changes nothing: one synthetic event per direction is what
    # folding one synthetic event per direction produces.
    loaded.save()
    assert len(CollabState.read(tmp_path / 'state.json').events) == 5


def test_import_lock(tmp_path):
    """Test that the import lock reports held exactly while another thread holds it."""
    filepath = tmp_path / 'state.json'
    acquired, release = threading.Event(), threading.Event()

    def hold():
        with import_lock(filepath):
            acquired.set()
            release.wait(timeout=30)

    assert not import_lock_held(filepath)

    thread = threading.Thread(target=hold)
    thread.start()
    acquired.wait(timeout=30)

    assert import_lock_held(filepath)

    release.set()
    thread.join()

    assert not import_lock_held(filepath)
