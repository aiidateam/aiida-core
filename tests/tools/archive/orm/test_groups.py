###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""orm.Group tests for the export and import routines"""

import uuid

import pytest

from aiida import orm
from aiida.common.links import LinkType
from aiida.orm import load_group
from aiida.tools.archive import create_archive, import_archive


def test_nodes_in_group(aiida_profile_clean, tmp_path, aiida_localhost):
    """This test checks that nodes that belong to a specific group are
    correctly imported and exported.
    """
    # Create another user
    new_email = uuid.uuid4().hex
    user = orm.User(email=new_email)
    user.store()

    # Create a structure data node that has a calculation as output
    sd1 = orm.StructureData(pbc=False)
    sd1.user = user
    sd1.label = 'sd1'
    sd1.store()

    jc1 = orm.CalcJobNode()
    jc1.computer = aiida_localhost
    jc1.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
    jc1.user = user
    jc1.label = 'jc1'
    jc1.base.links.add_incoming(sd1, link_type=LinkType.INPUT_CALC, link_label='link')
    jc1.store()
    jc1.seal()

    # Create a group and add the data inside
    gr1 = orm.Group(label='node_group')
    gr1.store()
    gr1.add_nodes([sd1, jc1])
    gr1_uuid = gr1.uuid

    # At this point we export the generated data
    filename1 = tmp_path / 'export1.aiida'
    create_archive([sd1, jc1, gr1], filename=filename1)
    n_uuids = [sd1.uuid, jc1.uuid]
    aiida_profile_clean.reset_storage()
    import_archive(filename1)

    # Check that the imported nodes are correctly imported and that
    # the user assigned to the nodes is the right one
    for node_uuid in n_uuids:
        assert orm.load_node(node_uuid).user.email == new_email

    # Check that the exported group is imported correctly
    builder = orm.QueryBuilder()
    builder.append(orm.Group, filters={'uuid': {'==': gr1_uuid}})
    assert builder.count() == 1, 'The group was not found.'


def test_group_export(tmp_path, aiida_profile_clean):
    """Exporting a group includes its extras and nodes."""
    # Create a new user
    new_email = uuid.uuid4().hex
    user = orm.User(email=new_email)
    user.store()

    # Create a structure data node
    sd1 = orm.StructureData(pbc=False)
    sd1.user = user
    sd1.label = 'sd1'
    sd1.store()

    # Create a group and add the node
    group = orm.Group(label=uuid.uuid4().hex)
    group.base.extras.set('test', 1)
    group.store()
    group.add_nodes([sd1])
    group_uuid = group.uuid

    # Export the generated data, clean the database and import it again
    filename = tmp_path / 'export.aiida'
    create_archive([group], filename=filename)
    n_uuids = [sd1.uuid]
    aiida_profile_clean.reset_storage()
    import_archive(filename)

    # Check that the imported nodes are correctly imported and that
    # the user assigned to the nodes is the right one
    for node_uuid in n_uuids:
        assert orm.load_node(node_uuid).user.email == new_email

    # Check that the exported group is imported correctly
    builder = orm.QueryBuilder()
    builder.append(orm.Group, filters={'uuid': {'==': group_uuid}})
    assert builder.count() == 1, 'The group was not found.'
    imported_group = builder.all()[0][0]
    assert imported_group.base.extras.get('test') == 1, 'Extra missing on imported group'


def test_group_import_existing(tmp_path, aiida_profile_clean):
    """Testing what happens when I try to import a group that already exists in the
    database. This should raise an appropriate exception
    """
    grouplabel = 'node_group_existing'

    # Create another user
    new_email = 'newuser@new.n'
    user = orm.User(email=new_email)
    user.store()

    # Create a structure data node
    sd1 = orm.StructureData(pbc=False)
    sd1.user = user
    sd1.label = 'sd'
    sd1.store()

    # Create a group and add the data inside
    group = orm.Group(label=grouplabel)
    group.store()
    group.add_nodes([sd1])

    # At this point we export the generated data
    filename = tmp_path / 'export1.aiida'
    create_archive([group], filename=filename)
    aiida_profile_clean.reset_storage()

    # Creating a group of the same name
    group = orm.Group(label='node_group_existing')
    group.store()
    import_archive(filename)
    # The import should have created a new group with a suffix
    # I check for this:
    builder = orm.QueryBuilder().append(orm.Group, filters={'label': {'like': f'{grouplabel}%'}})
    assert builder.count() == 2
    # Now I check for the group having one member, and whether the name is different:
    builder = orm.QueryBuilder()
    builder.append(orm.Group, filters={'label': {'like': f'{grouplabel}%'}}, tag='g', project='label')
    builder.append(orm.StructureData, with_group='g')
    assert builder.count() == 1
    # I check that the group name was changed:
    assert builder.all()[0][0] != grouplabel
    # I import another name, the group should not be imported again
    import_archive(filename)
    builder = orm.QueryBuilder()
    builder.append(orm.Group, filters={'label': {'like': f'{grouplabel}%'}})
    assert builder.count() == 2


def test_import_to_group(tmp_path, aiida_profile_clean):
    """Test `group` parameter
    Make sure an unstored Group is stored by the import function, forwarding the Group object.
    Make sure the Group is correctly handled and used for imported nodes.
    """
    # Create Nodes to export
    data1 = orm.Data().store()
    data2 = orm.Data().store()
    node_uuids = [node.uuid for node in [data1, data2]]

    # Export Nodes
    filename = tmp_path / 'export.aiida'
    create_archive([data1, data2], filename=filename)
    aiida_profile_clean.reset_storage()

    # Create Group, do not store
    group_label = 'import_madness'
    group = orm.Group(label=group_label)
    group_uuid = group.uuid

    # Try to import to this Group, providing only label - this should fail
    with pytest.raises(TypeError):
        import_archive(filename, group=group_label)

    # Import properly now, providing the Group object
    import_archive(filename, group=group)

    # Check Group for content
    builder = orm.QueryBuilder().append(orm.Group, filters={'label': group_label}, project='uuid')
    assert (
        builder.count() == 1
    ), f'There should be exactly one Group with label {group_label}. Instead {builder.count()} was found.'
    imported_group = load_group(builder.all()[0][0])
    assert imported_group.uuid == group_uuid
    assert imported_group.count() == len(node_uuids), (
        '{} Nodes were found in the automatic import group, instead there should have been exactly {} ' 'Nodes'.format(
            imported_group.count(), len(node_uuids)
        )
    )
    for node in imported_group.nodes:
        assert node.uuid in node_uuids

    # Import again, using a new Group, and make sure the automatic import Group also captures "existing" Nodes
    group_label = 'existing_import'
    group = orm.Group(label=group_label)
    group_uuid = group.uuid

    import_archive(filename, group=group)

    imported_group = load_group(label=group_label)
    assert imported_group.uuid == group_uuid
    assert imported_group.count() == len(node_uuids), (
        '{} Nodes were found in the automatic import group, instead there should have been exactly {} ' 'Nodes'.format(
            imported_group.count(), len(node_uuids)
        )
    )
    for node in imported_group.nodes:
        assert node.uuid in node_uuids


@pytest.mark.usefixtures('aiida_profile_clean')
def test_create_group(tmp_path):
    """Test create_group argument"""
    node = orm.Data().store()
    filename = tmp_path / 'export.aiida'
    create_archive([node], filename=filename)
    assert orm.Group.collection.count() == 0
    # this should create an ImportGroup
    import_archive(filename)
    assert orm.Group.collection.count() == 1
    # this should create another ImportGroup
    import_archive(filename, create_group=True)
    assert orm.Group.collection.count() == 2
    # this should not create a new ImportGroup
    import_archive(filename, create_group=False)
    assert orm.Group.collection.count() == 2
