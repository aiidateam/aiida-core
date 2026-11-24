###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Controlled-entrypoint contract for container persistence at archive boundaries.

Relational container state (``db_dbcontainer`` + kind markers, membership rows) has no
archive representation (deferred integration: ownership unsupported in archives). The
controlled storage entrypoint is therefore explicit rejection at the archive
entrypoints — never a bare ``bulk_insert`` of a container row without its container
state, and never a silent export of an (even empty) container as a plain node row.

These tests document that contract:

- export rejects containers, including empty ones with no membership rows;
- import validation rejects archive rows with a container ``node_type``;
- standalone non-container nodes still export/import-validate cleanly (dedup preserved).

Low-level ``bulk_insert`` is intentionally *not* changed to reject staged writes inside
a multi-step transaction; completeness is enforced at these controlled entrypoints.
"""

import pytest

from aiida import orm
from aiida.tools.archive.create import _assert_no_ownership_members
from aiida.tools.archive.exceptions import ExportValidationError, ImportValidationError
from aiida.tools.archive.imports import _validate_ownership_agreement


def test_export_rejects_empty_container(aiida_profile_clean, backend):
    """Empty containers carry container state but no membership rows: export must reject."""
    from aiida.orm import DataList

    empty = DataList().store()
    # Sanity: the stored empty container really has container state but no membership.
    session = backend.get_session()
    _node_model, membership_model = backend._ownership_models()
    container_model, _, _ = backend._container_models()
    assert session.query(container_model).filter(container_model.node_id == empty.pk).one_or_none() is not None
    assert session.query(membership_model).filter(membership_model.owner_id == empty.pk).count() == 0

    with pytest.raises(ExportValidationError, match=r'ownership|container|Container'):
        _assert_no_ownership_members(backend, {empty.pk})


def test_export_rejects_nonempty_container(aiida_profile_clean, backend):
    """Non-empty ownership units are rejected (membership-backed path)."""
    from aiida.orm import DataList, Int

    container = DataList([Int(1)]).store()
    with pytest.raises(ExportValidationError, match=r'ownership|container|Container'):
        _assert_no_ownership_members(backend, {container.pk})


def test_export_allows_standalone(aiida_profile_clean, backend):
    """Standalone non-container nodes still export (no false positives)."""
    from aiida.orm import Int

    node = Int(1).store()
    _assert_no_ownership_members(backend, {node.pk})


def test_import_rejects_container_rows(aiida_profile_clean, backend):
    """Archive rows with a container node_type cannot round-trip: import must reject.

    Uses the live backend as both archive source and target: any container row present in
    the source (empty or not) is rejected before any write, so no incomplete container
    row is ever ``bulk_insert``-ed without its ``db_dbcontainer``/kind state.
    """
    from aiida.orm import DataList, Int

    container = DataList([Int(1)]).store()
    plain = Int(2).store()
    input_id_uuid = {container.pk: container.uuid, plain.pk: plain.uuid}
    with pytest.raises(ImportValidationError, match=r'container|ownership|Container'):
        _validate_ownership_agreement(backend, backend, 100, input_id_uuid, {})


def test_import_rejects_empty_container_row(aiida_profile_clean, backend):
    """Empty containers (container type, no membership) are rejected on import too."""
    from aiida.orm import DataList, Int

    empty = DataList().store()
    plain = Int(3).store()
    input_id_uuid = {empty.pk: empty.uuid, plain.pk: plain.uuid}
    with pytest.raises(ImportValidationError, match=r'container|ownership|Container'):
        _validate_ownership_agreement(backend, backend, 100, input_id_uuid, {})


def test_import_allows_standalone_rows(aiida_profile_clean, backend):
    """Standalone archive rows validate cleanly (existing import/dedup unaffected)."""
    from aiida.orm import Int

    plain = Int(4).store()
    # No reuse: nothing stored under these UUIDs in the target beyond the plain node itself,
    # and the source row is standalone, so validation passes.
    _validate_ownership_agreement(backend, backend, 100, {plain.pk: plain.uuid}, {})
    assert orm.load_node(plain.pk).value == 4
