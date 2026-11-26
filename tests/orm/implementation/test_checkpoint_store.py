###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Checkpoint file retention and lock failure regressions."""

import errno
import sys
from pathlib import Path

import pytest

from aiida.orm.implementation.storage_backend import StorageBackend


def test_retention_propagates_body_oserror(backend: StorageBackend, caplog: pytest.LogCaptureFixture) -> None:
    """An `OSError` from the protected operation retains its identity and traceback."""
    failure: OSError = OSError('checkpoint read failed')

    with pytest.raises(OSError) as raised:
        with backend.checkpoint_store.retain_files():
            raise failure

    assert raised.value is failure
    assert 'could not lock checkpoint files' not in caplog.text


def test_retention_falls_back_on_lock_failure(
    backend: StorageBackend, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """A lock acquisition error permits one protected operation."""
    import fcntl

    def fail_lock(_descriptor: int, _operation: int) -> None:
        msg: str = 'lock unavailable'
        raise OSError(msg)

    monkeypatch.setattr(fcntl, 'flock', fail_lock)
    calls: list[str] = []
    with backend.checkpoint_store.retain_files():
        calls.append('loaded')

    assert calls == ['loaded']
    assert 'lock unavailable' in caplog.text


def test_retention_releases_lock_after_body_failure(backend: StorageBackend, tmp_path: Path) -> None:
    """A failed reader releases its lock so deferred cleanup can proceed."""
    obsolete: Path = tmp_path / 'obsolete.pkl'
    _ = obsolete.write_bytes(b'checkpoint')
    with pytest.raises(ValueError, match='decode failed'):
        with backend.checkpoint_store.retain_files():
            assert backend.checkpoint_store.discard_files(paths=[obsolete]) == []
            msg: str = 'decode failed'
            raise ValueError(msg)

    assert backend.checkpoint_store.discard_files(paths=[obsolete]) == [obsolete]
    assert not obsolete.exists()


@pytest.fixture(
    params=[pytest.param('missing-fcntl', id='missing-fcntl'), pytest.param('flock-error', id='flock-error')]
)
def unlockable(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    """Make file locking unavailable, as on Windows or on a filesystem without `flock` support."""
    if request.param == 'missing-fcntl':
        monkeypatch.setitem(sys.modules, 'fcntl', None)
        return

    import fcntl

    def fail_lock(_descriptor: int, _operation: int) -> None:
        raise OSError(errno.ENOLCK, 'No locks available')

    monkeypatch.setattr(fcntl, 'flock', fail_lock)


@pytest.mark.usefixtures('unlockable')
def test_discarding_without_locking_leaves_files_to_maintenance(backend: StorageBackend, tmp_path: Path) -> None:
    """Without file locking, saves and terminations keep obsolete files for maintenance."""
    obsolete: Path = tmp_path / 'obsolete.pkl'
    _ = obsolete.write_bytes(b'checkpoint')

    assert backend.checkpoint_store.discard_files(paths=[obsolete]) == []
    assert obsolete.exists()


@pytest.mark.usefixtures('unlockable')
def test_orphan_collection_retains_without_locking(backend: StorageBackend, tmp_path: Path) -> None:
    """Without file locking, orphan collection keeps files unless forced with exclusive access."""
    orphan: Path = tmp_path / 'orphan.pkl'
    _ = orphan.write_bytes(b'checkpoint')

    assert backend.checkpoint_store.discard_orphans(paths=[orphan]) == []
    assert orphan.exists()
    assert backend.checkpoint_store.discard_orphans(paths=[orphan], force=True) == [orphan]
    assert not orphan.exists()


def test_orphan_collection_waits_for_a_reader(backend: StorageBackend, tmp_path: Path) -> None:
    """A held reader lock defers orphan collection to a later maintenance run."""
    orphan: Path = tmp_path / 'orphan.pkl'
    _ = orphan.write_bytes(b'checkpoint')

    with backend.checkpoint_store.retain_files():
        assert backend.checkpoint_store.discard_orphans(paths=[orphan]) == []

    assert orphan.exists()


@pytest.mark.parametrize('outcome', ['commit', 'rollback', 'retained'])
def test_transaction_defers_discard_until_commit(backend: StorageBackend, tmp_path: Path, outcome: str) -> None:
    """Separate store lookups share exact-path cleanup, conditional on commit and reader locks."""
    from contextlib import nullcontext

    obsolete: Path = tmp_path / 'obsolete.pkl'
    unrelated: Path = tmp_path / 'unrelated.pkl'
    _ = obsolete.write_bytes(b'old checkpoint')
    _ = unrelated.write_bytes(b'uncommitted checkpoint from another writer')

    with backend.checkpoint_store.retain_files() if outcome == 'retained' else nullcontext():
        try:
            with backend.checkpoint_store.transaction():
                assert backend.in_transaction
                assert backend.checkpoint_store.discard_files(paths=[obsolete]) == []
                assert obsolete.exists()
                if outcome == 'rollback':
                    msg: str = 'rollback'
                    raise RuntimeError(msg)
        except RuntimeError:
            assert outcome == 'rollback'
        assert obsolete.exists() is (outcome != 'commit')
    assert unrelated.exists()

    # A failed or lock-blocked transaction must not leak its queue into another save.
    with backend.checkpoint_store.transaction():
        pass
    assert obsolete.exists() is (outcome != 'commit')


def test_transaction_joins_without_committing_caller(backend: StorageBackend, tmp_path: Path) -> None:
    """Lower-level callers retain rollback safety, leaving old files to maintenance."""
    obsolete: Path = tmp_path / 'obsolete.pkl'
    _ = obsolete.write_bytes(b'old checkpoint')
    with backend.transaction():
        with backend.checkpoint_store.transaction():
            assert backend.checkpoint_store.discard_files(paths=[obsolete]) == []
        assert backend.in_transaction
        assert obsolete.exists()
    assert obsolete.exists()


def test_transaction_keeps_republished_file(backend: StorageBackend) -> None:
    """Saving the same checkpoint again in a transaction cancels its pending discard."""
    from uuid import uuid4

    from aiida.orm.implementation.checkpoint_store import CheckpointBytes

    node_uuid: str = str(uuid4())
    data: CheckpointBytes = CheckpointBytes(content=b'original checkpoint')
    store = backend.checkpoint_store
    store.write(node_uuid=node_uuid, data=data)
    with store.transaction():
        store.discard_one(node_uuid=node_uuid, digest=data.digest)
        backend.checkpoint_store.write(node_uuid=node_uuid, data=data)
    assert store.read(node_uuid=node_uuid, digest=data.digest) == data.content


def test_transaction_discard_queue_is_thread_local(backend: StorageBackend, tmp_path: Path) -> None:
    """A cached store cannot enqueue another thread's cleanup in the current transaction."""
    from concurrent.futures import ThreadPoolExecutor

    obsolete: Path = tmp_path / 'obsolete.pkl'
    _ = obsolete.write_bytes(b'checkpoint from another thread')
    with backend.checkpoint_store.transaction():
        with ThreadPoolExecutor(max_workers=1) as executor:
            removed = executor.submit(backend.checkpoint_store.discard_files, paths=[obsolete]).result()
        assert removed == [obsolete]
        assert backend.in_transaction
    assert not obsolete.exists()
