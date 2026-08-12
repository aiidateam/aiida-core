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
from datetime import timedelta

import pytest

from aiida import get_profile
from aiida.common import timezone
from aiida.manage.configuration.settings import AiiDAConfigPathResolver
from aiida.tools.collab.state import CollabEvent, CollabState, exclusive_lock, import_lock, import_lock_held

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
    # Built apart rather than taken twice, since a coarse clock returns one instant for both and the `>=` filter
    # then answers with the early event too, passing the assertion below for the wrong reason.
    early = timezone.now()
    late = early + timedelta(seconds=1)
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


def test_a_lock_that_cannot_be_taken_raises_in_either_mode(tmp_path, monkeypatch):
    """Test that a filesystem without locking raises, rather than being reported as a lock somebody else holds.

    Both modes have to say so, for different reasons. The blocking callers — the state file, the configuration,
    the imports — spell this ``with exclusive_lock(p):`` and never read what it yields, so a failure they are not
    told about is a write that believes it holds a lock it does not. The non-blocking caller does read it, but
    ``False`` means "somebody is syncing": answering that here refuses every sync of the profile forever, and it
    is the first lock either command takes, so nothing louder follows to correct the diagnosis.
    """
    import errno
    import fcntl

    def refuse(handle, operation):
        raise OSError(errno.ENOLCK, 'no locks available')

    monkeypatch.setattr(fcntl, 'flock', refuse)
    lockpath = tmp_path / 'guarded.lock'

    for blocking in (True, False):
        with pytest.raises(OSError):
            with exclusive_lock(lockpath, blocking=blocking):
                pytest.fail('the body must not run when the lock could not be taken')


def test_two_probes_do_not_report_each_other(tmp_path):
    """Test that asking whether an import is running does not itself look like one to a second asker.

    The probe is a question, so it takes the lock in the shared mode that answers one. Asking for the exclusive
    mode instead would make two peers handshaking at the same moment report each other as a running import —
    both told busy while the profile is idle, which is precisely the moment the busy answer is supposed to
    distinguish from. The concurrent probe is a second descriptor here rather than a thread: ``flock`` contends
    per open file, so this is the same contention with none of the race.
    """
    import fcntl

    filepath = tmp_path / 'state.json'
    lockpath = filepath.with_name(f'{filepath.name}.import.lock')
    lockpath.touch()

    with lockpath.open('w') as concurrent_probe:
        fcntl.flock(concurrent_probe, fcntl.LOCK_SH)

        assert not import_lock_held(filepath)


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
