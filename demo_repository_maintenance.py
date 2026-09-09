###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Demonstrate how repository maintenance interacts with soft-deleted entries.

This script creates an isolated temporary ``sqlite_dos`` profile and shows two cases:

1. A node marks a repository entry for deletion and no other node references the same repository object.
   Maintenance hard-deletes the repository object.
2. Two nodes reference the same repository object and only one marks it for deletion.
   Maintenance does not hard-delete the repository object.

Run with:

    uv run python demo_repository_maintenance.py
"""

from __future__ import annotations

import atexit
import os
import shutil
import tempfile

DIRPATH_AIIDA = tempfile.mkdtemp(prefix='aiida-demo-config-')
os.environ['AIIDA_PATH'] = DIRPATH_AIIDA
atexit.register(lambda: shutil.rmtree(DIRPATH_AIIDA, ignore_errors=True))

from aiida import orm
from aiida.manage import get_manager
from aiida.manage.configuration import create_profile, get_config, profile_context
from aiida.repository import Repository


def get_single_repo_key(node: orm.Node) -> str:
    """Return the single repository key stored for a node."""
    flattened = Repository.flatten(node.base.repository.metadata, include_deleted=True)
    keys = [value for value in flattened.values() if value is not None]
    if len(keys) != 1:
        msg = f'expected exactly one repository key, got: {keys}'
        raise RuntimeError(msg)
    return keys[0]


def print_case_header(title: str) -> None:
    """Print a case header."""
    print(f'\n{"=" * 79}')
    print(title)
    print(f'{"=" * 79}')


def demo_case_one() -> None:
    """Show that maintenance deletes an unshared object marked for deletion."""
    storage = get_manager().get_profile_storage()
    repository_backend = storage.get_repository()

    node = orm.Data()
    node.base.repository.put_object_from_bytes(b'case-1-unique-content', 'file.txt')
    node.store()

    key = get_single_repo_key(node)

    print_case_header('Case 1: one node marks a unique repository object for deletion')
    print(f'node uuid: {node.uuid}')
    print(f'repository key: {key}')
    print(f'backend has object before mark: {repository_backend.has_object(key)}')
    print(f'visible repository entries before mark: {node.base.repository.list_object_names()}')

    node.base.repository.mark_for_deletion('file.txt')

    print(f'visible repository entries after mark: {node.base.repository.list_object_names()}')
    print(f'unreferenced keyset before maintenance: {storage.get_unreferenced_keyset()}')

    storage.maintain(full=False, dry_run=False, compress=False)

    print(f'backend has object after maintenance: {repository_backend.has_object(key)}')
    print('result: maintenance deleted the repository object')


def demo_case_two() -> None:
    """Show that maintenance does not delete a shared object marked for deletion by one node."""
    storage = get_manager().get_profile_storage()
    repository_backend = storage.get_repository()

    node_deleted = orm.Data()
    node_deleted.base.repository.put_object_from_bytes(b'case-2-shared-content', 'file.txt')
    node_deleted.store()
    node_deleted.base.repository.mark_for_deletion('file.txt')

    node_active = orm.Data()
    node_active.base.repository.put_object_from_bytes(b'case-2-shared-content', 'other-name.txt')
    node_active.store()

    key_deleted = get_single_repo_key(node_deleted)
    key_active = get_single_repo_key(node_active)
    conflict_messages = storage._get_repository_deletion_conflicts()

    print_case_header('Case 2: one node marks a shared repository object for deletion')
    print(f'deleted node uuid: {node_deleted.uuid}')
    print(f'active node uuid: {node_active.uuid}')
    print(f'deleted-node key: {key_deleted}')
    print(f'active-node key: {key_active}')
    print(f'keys are shared: {key_deleted == key_active}')
    print(f'backend has object before maintenance: {repository_backend.has_object(key_deleted)}')
    print(f'unreferenced keyset before maintenance: {storage.get_unreferenced_keyset()}')
    print('conflicts that maintenance will report:')
    for message in conflict_messages:
        print(f'  - {message}')

    storage.maintain(full=False, dry_run=False, compress=False)

    print(f'backend has object after maintenance: {repository_backend.has_object(key_deleted)}')
    print('result: maintenance kept the repository object because another node still references it')


def main() -> None:
    """Run the repository maintenance demonstration."""
    dirpath_storage = tempfile.mkdtemp(prefix='aiida-demo-storage-')
    atexit.register(lambda: shutil.rmtree(dirpath_storage, ignore_errors=True))

    profile = create_profile(
        get_config(create=True),
        name='repository-maintenance-demo',
        email='demo@localhost',
        storage_backend='core.sqlite_dos',
        storage_config={'filepath': dirpath_storage},
        broker_backend=None,
        broker_config=None,
        is_test_profile=True,
    )

    with profile_context(profile, allow_switch=True):
        demo_case_one()
        demo_case_two()

    print(f'\nTemporary AIIDA_PATH: {DIRPATH_AIIDA}')
    print(f'Temporary storage path: {dirpath_storage}')


if __name__ == '__main__':
    main()
