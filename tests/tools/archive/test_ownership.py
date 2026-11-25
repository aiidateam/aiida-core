###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Round-trip owned container trees through the SQLite archive format."""

import io

import pytest

from aiida import orm
from aiida.common.links import LinkType
from aiida.engine import calcfunction
from aiida.orm.entities import EntityTypes
from aiida.tools.archive import create_archive, import_archive
from aiida.tools.archive.exceptions import ImportValidationError
from aiida.tools.archive.implementations.sqlite_zip.main import ArchiveFormatSqlZip


@pytest.mark.usefixtures('aiida_profile_clean')
@pytest.mark.parametrize('selection', ['root', 'process', 'group', 'all'])
def test_ownership_round_trip(tmp_path, aiida_profile_clean, selection):
    """Restore both owned members and references, including provenance, after remapping IDs."""

    @calcfunction
    def produce():
        return orm.Int(8)

    source = produce()
    source_uuid, creator_uuid = source.uuid, source.creator.uuid
    root = orm.DataDict(
        {'z': orm.DataList([orm.Int(7), orm.SinglefileData(io.BytesIO(b'owned content'))]), 'a': orm.DataDict()}
    )
    root['z'].append(source)
    root.store()
    process = orm.CalcJobNode()
    process.base.links.add_incoming(root, LinkType.INPUT_CALC, 'input')
    process.store().seal()
    group = orm.Group(label='owned-collection').store()
    selected_nodes = [root, root['z'], root['a'], *root['z']]
    group.add_nodes(selected_nodes)
    uuid = root.uuid
    process_uuid = process.uuid
    archive_ids = {node.pk for node in group.nodes}
    original_group_uuids = {node.uuid for node in group.nodes}
    source_node_count = orm.QueryBuilder().append(orm.Node).count()
    selected = {
        'root': selected_nodes,
        'process': [process, *selected_nodes[1:]],
        'group': [group],
        'all': None,
    }[selection]
    path = create_archive(selected, filename=tmp_path / 'owned.aiida')

    with ArchiveFormatSqlZip().open(path, 'r') as reader:
        archived = reader.querybuilder().append(orm.DataDict, filters={'uuid': uuid}, project='*').one()[0]
        assert list(archived.keys()) == ['z', 'a']
        assert archived['z'][0].value == 7

    aiida_profile_clean.reset_storage()
    # Occupy the IDs SQLite can reuse after a reset. PostgreSQL keeps advancing its sequence,
    # so using the maximum primary key here would scale with previous tests rather than this graph.
    for value in range(source_node_count):
        orm.Int(value).store()
    import_group_id = import_archive(path, create_group=True)
    import_archive(path, create_group=False)
    imported = orm.load_node(uuid)
    assert imported.pk not in archive_ids
    assert list(imported.keys()) == ['z', 'a']
    assert type(imported['a']) is orm.DataDict
    assert len(imported['a']) == 0
    assert imported['z'][0].value == 7
    assert imported['z'][1].get_content() == 'owned content'
    assert imported['z'][2].uuid == source_uuid
    assert imported['z'][2].creator.uuid == creator_uuid
    assert orm.QueryBuilder().append(orm.Container).count() == 3
    expected_imported = original_group_uuids | {creator_uuid}
    if selection in ('process', 'all'):
        assert orm.load_node(process_uuid).inputs.input.uuid == uuid
        expected_imported.add(process_uuid)
    assert {node.uuid for node in orm.load_group(import_group_id).nodes} == expected_imported
    if selection in ('group', 'all'):
        imported_group = orm.load_group(label='owned-collection')
        assert {node.uuid for node in imported_group.nodes} == original_group_uuids


@pytest.mark.parametrize('selection', ['leaf', 'group', 'nested', 'root-and-leaf', 'root-and-group', 'nested-and-leaf'])
def test_export_projects_ownership(tmp_path, aiida_profile_clean, selection):
    """An unselected owner is omitted without copying or dropping the selected member."""
    root = orm.DataList([orm.DataList([orm.Int(1)]), orm.Int(2)]).store()
    nested = root[0]
    leaf = nested[0]
    group = orm.Group(label='only-leaf').store()
    group.add_nodes(leaf)
    starting = {
        'leaf': [leaf],
        'group': [group],
        'nested': [nested],
        'root-and-leaf': [root, leaf],
        'root-and-group': [root, group],
        'nested-and-leaf': [nested, leaf],
    }
    path = create_archive(starting[selection], filename=tmp_path / 'selection.aiida')
    root_uuid, nested_uuid, leaf_uuid = root.uuid, nested.uuid, leaf.uuid
    expected = {node.uuid for node in starting[selection] if isinstance(node, orm.Node)}
    if group in starting[selection]:
        expected.add(leaf_uuid)
    assert orm.load_node(root_uuid)[0][0].uuid == leaf_uuid

    aiida_profile_clean.reset_storage()
    import_archive(path, create_group=False)
    assert set(orm.QueryBuilder().append(orm.Node, project='uuid').all(flat=True)) == expected
    if selection == 'nested-and-leaf':
        assert orm.load_node(nested_uuid)[0].uuid == leaf_uuid
    elif selection == 'nested':
        assert list(orm.load_node(nested_uuid)) == []
    elif selection.startswith('root-'):
        assert list(orm.load_node(root_uuid)) == []
    if selection in ('group', 'root-and-group'):
        assert {node.uuid for node in orm.load_group(label='only-leaf').nodes} == {leaf_uuid}


@pytest.mark.parametrize('projection', ['member', 'container', 'partial-tree'])
@pytest.mark.parametrize('projection_first', [True, False])
def test_import_merges_projected_ownership(tmp_path, aiida_profile_clean, projection, projection_first):
    """Full and projected archives reuse UUIDs and preserve explicit membership in either order."""
    root = orm.DataList([orm.Int(1), orm.Int(2)]).store()
    root_uuid, member_uuids = root.uuid, [child.uuid for child in root]
    selections = {'member': [root[0]], 'container': [root], 'partial-tree': [root, root[1]]}
    projected = create_archive(selections[projection], filename=tmp_path / 'projected.aiida')
    tree = create_archive([root, *root], filename=tmp_path / 'tree.aiida')
    first, second = (projected, tree) if projection_first else (tree, projected)
    aiida_profile_clean.reset_storage()
    import_archive(first, create_group=False)
    previous = dict(orm.QueryBuilder().append(orm.Node, project=['uuid', 'id']).all())
    retained_root = orm.load_node(root_uuid) if root_uuid in previous else None
    if retained_root is not None:
        list(retained_root)  # Exercise refreshing a materialized container after a merge.
    import_archive(second, create_group=False)
    current = dict(orm.QueryBuilder().append(orm.Node, project=['uuid', 'id']).all())
    assert set(current) == {root_uuid, *member_uuids}
    assert previous.items() <= current.items()
    assert [
        child.uuid for child in (retained_root if retained_root is not None else orm.load_node(root_uuid))
    ] == member_uuids


def test_import_adds_members_to_an_owned_container(tmp_path, aiida_profile_clean):
    """A partial import can be completed beneath a container that already has an owner."""
    root = orm.DataList([orm.DataList([orm.Int(1)])]).store()
    nested = root[0]
    leaf = nested[0]
    root_uuid, nested_uuid, leaf_uuid = root.uuid, nested.uuid, leaf.uuid
    partial = create_archive([root, nested], filename=tmp_path / 'partial.aiida')
    full = create_archive([root, nested, leaf], filename=tmp_path / 'full.aiida')

    aiida_profile_clean.reset_storage()
    import_archive(partial, create_group=False)
    imported = orm.load_node(root_uuid)
    assert list(imported[0]) == []
    import_archive(full, create_group=False)
    assert imported[0].uuid == nested_uuid
    assert [child.uuid for child in imported[0]] == [leaf_uuid]


def test_import_empty_container_keeps_members(tmp_path, aiida_profile_clean):
    """An empty archive contributes no edges and cannot remove stored members."""
    from aiida.tools import delete_nodes

    root = orm.DataList([orm.Int(1)]).store()
    full = create_archive([root, *root], filename=tmp_path / 'full.aiida')
    delete_nodes([root[0].pk], dry_run=False)
    root.base.caching.rehash()
    assert root.base.caching.get_hash() is not None
    empty = create_archive([root], filename=tmp_path / 'empty.aiida')
    root_uuid = root.uuid
    aiida_profile_clean.reset_storage()
    import_archive(full, create_group=False)
    import_archive(empty, create_group=False, merge_extras=('n', 'c', 'u'))
    reused = orm.load_node(root_uuid)
    assert [child.value for child in reused] == [1]
    assert reused.base.caching.get_hash() is None  # The empty container's archived hash doesn't apply.


def test_import_standalone_node_keeps_owner(tmp_path, aiida_profile_clean):
    """A node with no archived owner can reuse an existing owned node."""
    from aiida.tools import delete_nodes

    root = orm.DataList([orm.Int(1)]).store()
    root_uuid, child_uuid = root.uuid, root[0].uuid
    full = create_archive([root, *root], filename=tmp_path / 'full.aiida')
    delete_nodes([root.pk], dry_run=False, contains_forward=False)
    detached = create_archive([orm.load_node(child_uuid)], filename=tmp_path / 'standalone.aiida')
    aiida_profile_clean.reset_storage()
    import_archive(full, create_group=False)
    child_pk = orm.load_node(child_uuid).pk
    import_archive(detached, create_group=False)
    assert orm.load_node(root_uuid)[0].pk == child_pk


def test_import_rejects_a_second_explicit_owner(tmp_path, aiida_profile_clean):
    """An explicit edge cannot reassign an owned child to a different container."""
    from aiida.tools import delete_nodes

    original = orm.DataList([orm.Int(1)]).store()
    original_uuid, child_uuid = original.uuid, original[0].uuid
    full = create_archive([original, *original], filename=tmp_path / 'full.aiida')
    delete_nodes([original.pk], dry_run=False)
    other = orm.DataList([orm.Int(1)]).store()
    node_model, _ = other.backend._ownership_models()
    with other.backend.transaction() as session:
        session.query(node_model).filter_by(id=other[0].pk).update({'uuid': child_uuid})
    conflicting = create_archive([other, *other], filename=tmp_path / 'conflict.aiida')
    aiida_profile_clean.reset_storage()
    import_archive(full, create_group=False)
    with pytest.raises(ImportValidationError, match='already owned'):
        import_archive(conflicting, create_group=False)
    assert orm.load_node(original_uuid)[0].uuid == child_uuid
    assert orm.QueryBuilder().append(orm.Container).count() == 1


@pytest.mark.usefixtures('aiida_profile_clean')
def test_import_rejects_conflicting_ownership(tmp_path, backend):
    """Matching all UUIDs is insufficient if the persisted order differs."""
    root = orm.DataList([orm.Int(1), orm.Int(2)]).store()
    path = create_archive([root, *root], filename=tmp_path / 'owned.aiida')
    # Change an edge at the SQL layer: the public API correctly disallows this mutation.
    _, membership = backend._ownership_models()
    with backend.transaction() as session:
        session.query(membership).filter_by(owner_id=root.pk, position=0).update({'position': 3})
    with pytest.raises(ImportValidationError, match='conflicting ownership'):
        import_archive(path)
    assert [member.value for member in orm.load_node(root.uuid)] == [2, 1]


@pytest.mark.usefixtures('aiida_profile_clean')
def test_empty_container_derived_from_node_type(tmp_path, aiida_profile_clean):
    """An empty container needs no membership rows: its kind comes from the node type."""
    user = orm.User('archive@example.org').store()
    root = orm.DataList(user=user).store()
    uuid = root.uuid
    path = tmp_path / 'empty.aiida'
    with ArchiveFormatSqlZip().open(path, mode='x') as writer:
        for entity, cls, pk in ((EntityTypes.USER, orm.User, user.pk), (EntityTypes.NODE, orm.Node, root.pk)):
            row = orm.QueryBuilder().append(cls, filters={'id': pk}, project='**', tag='entity').dict()[0]['entity']
            writer.bulk_insert(entity, [row])

    aiida_profile_clean.reset_storage()
    import_archive(path)
    imported = orm.load_node(uuid)
    assert type(imported) is orm.DataList
    assert len(imported) == 0


@pytest.mark.usefixtures('aiida_profile_clean')
def test_import_rejects_adopting_linked_node(tmp_path, aiida_profile_clean):
    """A standalone child with provenance links cannot become an owned member."""
    root = orm.DataList([orm.Int(1)]).store()
    child_uuid = root[0].uuid
    path = create_archive([root, *root], filename=tmp_path / 'owned.aiida')

    aiida_profile_clean.reset_storage()

    @calcfunction
    def produce():
        return orm.Int(1)

    standalone = produce()
    backend = standalone.backend
    node_model, _ = backend._ownership_models()
    with backend.transaction() as session:
        session.query(node_model).filter_by(id=standalone.pk).update({'uuid': child_uuid})

    with pytest.raises(ImportValidationError, match='existing provenance links'):
        import_archive(path)
    assert orm.load_node(child_uuid).creator is not None
    assert orm.QueryBuilder().append(orm.Container).count() == 0
