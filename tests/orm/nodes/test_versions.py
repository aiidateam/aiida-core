###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for versioned nodes."""

import pytest

from aiida import orm
from aiida.common import exceptions
from aiida.common.links import LinkType


@pytest.mark.usefixtures('aiida_profile_clean')
def test_revise_data_node():
    """Test creating and navigating a new version of a data node."""
    node = orm.Data()
    node.base.attributes.set_many({'temperature': 300.0, 'obsolete': True})
    node.base.extras.set('note', 'not versioned')
    node.store()

    revised = node.revise()

    assert not revised.is_stored
    assert revised.base.attributes.all == {'temperature': 300.0, 'obsolete': True}
    assert revised.base.extras.all == {}
    assert revised.base.versions.number == 2
    assert revised.base.versions.lineage_uuid == node.uuid

    revised.base.attributes.set('temperature', 320.0)
    revised.base.attributes.delete('obsolete')
    revised.base.attributes.set('pressure', 1.0)
    revised.store()

    assert revised.pk != node.pk
    assert node.base.attributes.all == {'temperature': 300.0, 'obsolete': True}
    assert revised.base.attributes.all == {'temperature': 320.0, 'pressure': 1.0}

    assert node.base.versions.number == 1
    assert revised.base.versions.number == 2
    assert node.base.versions.lineage_uuid == revised.base.versions.lineage_uuid
    assert not node.base.versions.is_head
    assert revised.base.versions.is_head

    assert node.base.versions.next.pk == revised.pk
    assert revised.base.versions.previous.pk == node.pk
    assert node.base.versions.head.pk == revised.pk
    assert revised.base.versions.first.pk == node.pk
    assert revised.base.versions.get(1).pk == node.pk
    assert revised.base.versions.get(2).pk == revised.pk
    assert [version.pk for version in node.base.versions.all()] == [node.pk, revised.pk]

    next_version_link = revised.base.links.get_incoming(link_type=LinkType.NEXT_VERSION).one()
    assert next_version_link.node.pk == node.pk
    assert next_version_link.link_label == 'next_version'

    history = revised.base.versions.history()
    assert [entry['version'] for entry in history] == [1, 2]
    assert [entry['pk'] for entry in history] == [node.pk, revised.pk]

    assert node.base.versions.diff(revised) == {
        'added': {'pressure': 1.0},
        'removed': {'obsolete': True},
        'changed': {'temperature': {'old': 300.0, 'new': 320.0}},
    }


@pytest.mark.usefixtures('aiida_profile_clean')
def test_revise_preserves_repository_copy_on_write():
    """Test revising a node preserves its repository content."""
    node = orm.Data()
    node.base.repository.put_object_from_bytes(b'content', 'relative/path')
    node.store()

    revised = node.base.revise()
    assert revised.base.repository.list_object_names('relative') == ['path']
    assert revised.base.repository.get_object_content('relative/path', mode='rb') == b'content'

    revised.store()
    assert revised.base.repository.metadata == node.base.repository.metadata
    assert revised.base.repository.hash() == node.base.repository.hash()


@pytest.mark.usefixtures('aiida_profile_clean')
def test_revise_guards():
    """Test the guards for creating a new version."""
    with pytest.raises(exceptions.ModificationNotAllowed, match='only stored nodes can be revised'):
        orm.Data().base.revise()

    for process_node in (orm.ProcessNode(), orm.CalculationNode().store(), orm.WorkflowNode().store()):
        with pytest.raises(exceptions.ModificationNotAllowed, match='only Data nodes can be revised'):
            process_node.base.revise()

    node = orm.Data().store()
    revised = node.base.revise().store()

    with pytest.raises(exceptions.ModificationNotAllowed, match='only the head of a lineage can be revised'):
        node.base.revise()

    with pytest.raises(exceptions.ModificationNotAllowed, match='NEXT_VERSION links are managed'):
        node.base.links.add_incoming(revised, LinkType.NEXT_VERSION, 'next_version')

    with pytest.raises(TypeError, match='managed by the versioning API'):
        orm.Data(lineage_uuid=node.uuid)

    with pytest.raises(TypeError, match='managed by the versioning API'):
        orm.Data(version=2)


@pytest.mark.usefixtures('aiida_profile_clean')
def test_revise_two_pending_revisions_from_same_head():
    """Test that only one pending revision from a head can be stored."""
    node = orm.Data().store()
    first = node.base.revise()
    second = node.base.revise()

    first.store()

    with pytest.raises(exceptions.ModificationNotAllowed, match='only the head of a lineage can be revised'):
        second.store()

    assert second.pk is None
    assert node.base.versions.next.pk == first.pk
    assert first.base.versions.is_head

    third = first.base.revise().store()
    assert third.base.versions.number == 3
    assert first.base.versions.next.pk == third.pk


@pytest.mark.usefixtures('aiida_profile_clean')
def test_load_node_version():
    """Test loading versions by explicit lineage UUID and version."""
    node = orm.Data().store()
    revised = node.base.revise().store()
    lineage_uuid = node.base.versions.lineage_uuid

    assert orm.load_node(pk=node.pk).pk == node.pk
    assert orm.load_node(uuid=node.uuid).pk == node.pk
    assert orm.load_node(uuid=lineage_uuid, version=2).pk == revised.pk
    assert orm.load_node(lineage_uuid=lineage_uuid).pk == revised.pk
    assert orm.load_node_version(lineage_uuid, version=1).pk == node.pk
    assert orm.load_node_version(lineage_uuid, version=2).pk == revised.pk
    assert orm.load_node_version(lineage_uuid).pk == revised.pk

    with pytest.raises(exceptions.NotExistent):
        orm.load_node_version(lineage_uuid, version=3)

    with pytest.raises(ValueError, match='version can only be specified together with uuid or lineage_uuid'):
        orm.load_node(pk=node.pk, version=1)


def test_archive_round_trip(aiida_profile_clean, tmp_path):
    """Test export/import preserves the version chain."""
    from aiida.tools.archive import create_archive, import_archive

    node = orm.Data().store()
    revised = node.base.revise().store()
    archive_path = tmp_path / 'versioned.aiida'

    create_archive([revised], filename=archive_path)

    node_uuid = node.uuid
    revised_uuid = revised.uuid
    lineage_uuid = node.base.versions.lineage_uuid

    aiida_profile_clean.reset_storage()
    import_archive(archive_path)

    imported_node = orm.load_node(uuid=node_uuid)
    imported_revised = orm.load_node(uuid=revised_uuid)

    assert imported_node.base.versions.lineage_uuid == lineage_uuid
    assert imported_revised.base.versions.lineage_uuid == lineage_uuid
    assert imported_revised.base.versions.previous.uuid == node_uuid
    assert imported_node.base.versions.head.uuid == revised_uuid


@pytest.mark.usefixtures('aiida_profile_clean')
def test_querybuilder_version_fields():
    """Test querying and projecting version fields."""
    node = orm.Data().store()
    revised = node.base.revise().store()
    independent = orm.Data().store()

    heads = (
        orm.QueryBuilder()
        .append(orm.Data, tag='node', filters={'is_head': True}, project='id')
        .order_by({'node': 'id'})
        .all(flat=True)
    )

    assert node.pk not in heads
    assert revised.pk in heads
    assert independent.pk in heads

    non_heads = orm.QueryBuilder().append(orm.Data, filters={'is_head': False}, project='id').all(flat=True)
    assert node.pk in non_heads
    assert revised.pk not in non_heads
    assert independent.pk not in non_heads

    rows = (
        orm.QueryBuilder()
        .append(
            orm.Data,
            tag='node',
            filters={'id': {'in': [node.pk, revised.pk]}},
            project=['id', 'lineage_uuid', 'version', 'is_head'],
        )
        .order_by({'node': 'id'})
        .all()
    )

    assert rows == [[node.pk, node.uuid, 1, False], [revised.pk, node.uuid, 2, True]]
