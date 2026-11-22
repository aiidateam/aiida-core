###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Checkpoint file transaction cleanup regressions."""

from pathlib import Path

import pytest

from aiida.orm.implementation.storage_backend import StorageBackend


@pytest.mark.parametrize('outcome', ['commit', 'rollback'])
def test_transaction_defers_discard_until_commit(backend: StorageBackend, tmp_path: Path, outcome: str) -> None:
    """Separate store lookups share exact-path cleanup, conditional on commit."""
    obsolete: Path = tmp_path / 'obsolete.pkl'
    unrelated: Path = tmp_path / 'unrelated.pkl'
    _ = obsolete.write_bytes(b'old checkpoint')
    _ = unrelated.write_bytes(b'uncommitted checkpoint from another writer')

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

    # A failed transaction must not leak its queue into another save.
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
