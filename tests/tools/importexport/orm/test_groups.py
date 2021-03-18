# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""orm.Group tests for the export and import routines"""

import os

from aiida import orm

from aiida.tools.importexport import import_data, export

from tests.utils.configuration import with_temp_dir
from .. import AiidaArchiveTestCase


class TestGroups(AiidaArchiveTestCase):
    """Test ex-/import cases related to Groups"""

    @with_temp_dir
    def test_nodes_in_group(self, temp_dir):
        """
        This test checks that nodes that belong to a specific group are
        correctly imported and exported.
        """
        from aiida.common.links import LinkType

        # Create another user
        new_email = 'newuser@new.n'
        user = orm.User(email=new_email)
        user.store()

        # Create a structure data node that has a calculation as output
        sd1 = orm.StructureData()
        sd1.user = user
        sd1.label = 'sd1'
        sd1.store()

        jc1 = orm.CalcJobNode()
        jc1.computer = self.computer
        jc1.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        jc1.user = user
        jc1.label = 'jc1'
        jc1.add_incoming(sd1, link_type=LinkType.INPUT_CALC, link_label='link')
        jc1.store()
        jc1.seal()

        # Create a group and add the data inside
        gr1 = orm.Group(label='node_group')
        gr1.store()
        gr1.add_nodes([sd1, jc1])
        gr1_uuid = gr1.uuid

        # At this point we export the generated data
        filename1 = os.path.join(temp_dir, 'export1.aiida')
        export([sd1, jc1, gr1], filename=filename1)
        n_uuids = [sd1.uuid, jc1.uuid]
        self.refurbish_db()
        import_data(filename1)

        # Check that the imported nodes are correctly imported and that
        # the user assigned to the nodes is the right one
        for uuid in n_uuids:
            self.assertEqual(orm.load_node(uuid).user.email, new_email)

        # Check that the exported group is imported correctly
        builder = orm.QueryBuilder()
        builder.append(orm.Group, filters={'uuid': {'==': gr1_uuid}})
        self.assertEqual(builder.count(), 1, 'The group was not found.')

    @with_temp_dir
    def test_group_export(self, temp_dir):
        """Exporting a group includes its extras and nodes."""
        # Create a new user
        new_email = 'newuser@new.n'
        user = orm.User(email=new_email)
        user.store()

        # Create a structure data node
        sd1 = orm.StructureData()
        sd1.user = user
        sd1.label = 'sd1'
        sd1.store()

        # Create a group and add the node
        group = orm.Group(label='node_group')
        group.set_extra('test', 1)
        group.store()
        group.add_nodes([sd1])
        group_uuid = group.uuid

        # Export the generated data, clean the database and import it again
        filename = os.path.join(temp_dir, 'export.aiida')
        export([group], filename=filename)
        n_uuids = [sd1.uuid]
        self.refurbish_db()
        import_data(filename)

        # Check that the imported nodes are correctly imported and that
        # the user assigned to the nodes is the right one
        for uuid in n_uuids:
            self.assertEqual(orm.load_node(uuid).user.email, new_email)

        # Check that the exported group is imported correctly
        builder = orm.QueryBuilder()
        builder.append(orm.Group, filters={'uuid': {'==': group_uuid}})
        self.assertEqual(builder.count(), 1, 'The group was not found.')
        imported_group = builder.all()[0][0]
        self.assertEqual(imported_group.get_extra('test'), 1, 'Extra missing on imported group')

    @with_temp_dir
    def test_group_import_existing(self, temp_dir):
        """
        Testing what happens when I try to import a group that already exists in the
        database. This should raise an appropriate exception
        """
        grouplabel = 'node_group_existing'

        # Create another user
        new_email = 'newuser@new.n'
        user = orm.User(email=new_email)
        user.store()

        # Create a structure data node
        sd1 = orm.StructureData()
        sd1.user = user
        sd1.label = 'sd'
        sd1.store()

        # Create a group and add the data inside
        group = orm.Group(label=grouplabel)
        group.store()
        group.add_nodes([sd1])

        # At this point we export the generated data
        filename = os.path.join(temp_dir, 'export1.aiida')
        export([group], filename=filename)
        self.refurbish_db()

        # Creating a group of the same name
        group = orm.Group(label='node_group_existing')
        group.store()
        import_data(filename)
        # The import should have created a new group with a suffix
        # I check for this:
        builder = orm.QueryBuilder().append(orm.Group, filters={'label': {'like': f'{grouplabel}%'}})
        self.assertEqual(builder.count(), 2)
        # Now I check for the group having one member, and whether the name is different:
        builder = orm.QueryBuilder()
        builder.append(orm.Group, filters={'label': {'like': f'{grouplabel}%'}}, tag='g', project='label')
        builder.append(orm.StructureData, with_group='g')
        self.assertEqual(builder.count(), 1)
        # I check that the group name was changed:
        self.assertTrue(builder.all()[0][0] != grouplabel)
        # I import another name, the group should not be imported again
        import_data(filename)
        builder = orm.QueryBuilder()
        builder.append(orm.Group, filters={'label': {'like': f'{grouplabel}%'}})
        self.assertEqual(builder.count(), 2)

    @with_temp_dir
    def test_import_to_group(self, temp_dir):
        """Test `group` parameter
        Make sure an unstored Group is stored by the import function, forwarding the Group object.
        Make sure the Group is correctly handled and used for imported nodes.
        """
        from aiida.orm import load_group
        from aiida.tools.importexport.common.exceptions import ImportValidationError

        # Create Nodes to export
        data1 = orm.Data().store()
        data2 = orm.Data().store()
        node_uuids = [node.uuid for node in [data1, data2]]

        # Export Nodes
        filename = os.path.join(temp_dir, 'export.aiida')
        export([data1, data2], filename=filename)
        self.refurbish_db()

        # Create Group, do not store
        group_label = 'import_madness'
        group = orm.Group(label=group_label)
        group_uuid = group.uuid

        # Try to import to this Group, providing only label - this should fail
        with self.assertRaises(ImportValidationError) as exc:
            import_data(filename, group=group_label)
        self.assertIn('group must be a Group entity', str(exc.exception))

        # Import properly now, providing the Group object
        import_data(filename, group=group)

        # Check Group for content
        builder = orm.QueryBuilder().append(orm.Group, filters={'label': group_label}, project='uuid')
        self.assertEqual(
            builder.count(),
            1,
            msg=f'There should be exactly one Group with label {group_label}. Instead {builder.count()} was found.'
        )
        imported_group = load_group(builder.all()[0][0])
        self.assertEqual(imported_group.uuid, group_uuid)
        self.assertEqual(
            imported_group.count(),
            len(node_uuids),
            msg='{} Nodes were found in the automatic import group, instead there should have been exactly {} '
            'Nodes'.format(imported_group.count(), len(node_uuids))
        )
        for node in imported_group.nodes:
            self.assertIn(node.uuid, node_uuids)

        # Import again, using a new Group, and make sure the automatic import Group also captures "existing" Nodes
        group_label = 'existing_import'
        group = orm.Group(label=group_label)
        group_uuid = group.uuid

        import_data(filename, group=group)

        imported_group = load_group(label=group_label)
        self.assertEqual(imported_group.uuid, group_uuid)
        self.assertEqual(
            imported_group.count(),
            len(node_uuids),
            msg='{} Nodes were found in the automatic import group, instead there should have been exactly {} '
            'Nodes'.format(imported_group.count(), len(node_uuids))
        )
        for node in imported_group.nodes:
            self.assertIn(node.uuid, node_uuids)
