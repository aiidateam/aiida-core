# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""orm.User tests for the export and import routines"""

import os

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.tools.importexport import import_data, export

from tests.utils.configuration import with_temp_dir


class TestUsers(AiidaTestCase):
    """Test ex-/import cases related to Users"""

    def setUp(self):
        self.reset_database()

    def tearDown(self):
        self.reset_database()

    @with_temp_dir
    def test_nodes_belonging_to_different_users(self, temp_dir):
        """
        This test checks that nodes belonging to different users are correctly
        exported & imported.
        """
        from aiida.common.links import LinkType
        from aiida.manage.manager import get_manager

        manager = get_manager()

        # Create another user
        new_email = 'newuser@new.n'
        user = orm.User(email=new_email).store()

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

        # Create some nodes from a different user
        sd2 = orm.StructureData()
        sd2.user = user
        sd2.label = 'sd2'
        sd2.store()
        sd2.add_incoming(jc1, link_type=LinkType.CREATE, link_label='l1')  # I assume jc1 CREATED sd2
        jc1.seal()

        jc2 = orm.CalcJobNode()
        jc2.computer = self.computer
        jc2.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        jc2.label = 'jc2'
        jc2.add_incoming(sd2, link_type=LinkType.INPUT_CALC, link_label='l2')
        jc2.store()

        sd3 = orm.StructureData()
        sd3.label = 'sd3'
        sd3.store()
        sd3.add_incoming(jc2, link_type=LinkType.CREATE, link_label='l3')
        jc2.seal()

        uuids_u1 = [sd1.uuid, jc1.uuid, sd2.uuid]
        uuids_u2 = [jc2.uuid, sd3.uuid]

        filename = os.path.join(temp_dir, 'export.tar.gz')

        export([sd3], outfile=filename, silent=True)
        self.clean_db()
        self.create_user()
        import_data(filename, silent=True)

        # Check that the imported nodes are correctly imported and that
        # the user assigned to the nodes is the right one
        for uuid in uuids_u1:
            node = orm.load_node(uuid=uuid)
            self.assertEqual(node.user.email, new_email)
        for uuid in uuids_u2:
            self.assertEqual(orm.load_node(uuid).user.email, manager.get_profile().default_user)

    @with_temp_dir
    def test_non_default_user_nodes(self, temp_dir):  # pylint: disable=too-many-statements
        """
        This test checks that nodes belonging to user A (which is not the
        default user) can be correctly exported, imported, enriched with nodes
        from the default user, re-exported & re-imported and that in the end
        all the nodes that have been finally imported belonging to the right
        users.
        """
        from aiida.common.links import LinkType
        from aiida.manage.manager import get_manager

        manager = get_manager()

        # Create another user
        new_email = 'newuser@new.n'
        user = orm.User(email=new_email).store()

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

        # Create some nodes from a different user
        sd2 = orm.StructureData()
        sd2.user = user
        sd2.label = 'sd2'
        sd2.add_incoming(jc1, link_type=LinkType.CREATE, link_label='l1')
        sd2.store()
        jc1.seal()
        sd2_uuid = sd2.uuid

        # At this point we export the generated data
        filename1 = os.path.join(temp_dir, 'export1.tar.gz')
        export([sd2], outfile=filename1, silent=True)
        uuids1 = [sd1.uuid, jc1.uuid, sd2.uuid]
        self.clean_db()
        self.insert_data()
        import_data(filename1, silent=True)

        # Check that the imported nodes are correctly imported and that
        # the user assigned to the nodes is the right one
        for uuid in uuids1:
            self.assertEqual(orm.load_node(uuid).user.email, new_email)

        # Now we continue to generate more data based on the imported
        # data
        sd2_imp = orm.load_node(sd2_uuid)

        jc2 = orm.CalcJobNode()
        jc2.computer = self.computer
        jc2.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        jc2.label = 'jc2'
        jc2.add_incoming(sd2_imp, link_type=LinkType.INPUT_CALC, link_label='l2')
        jc2.store()

        sd3 = orm.StructureData()
        sd3.label = 'sd3'
        sd3.add_incoming(jc2, link_type=LinkType.CREATE, link_label='l3')
        sd3.store()
        jc2.seal()

        # Store the UUIDs of the nodes that should be checked
        # if they can be imported correctly.
        uuids2 = [jc2.uuid, sd3.uuid]

        filename2 = os.path.join(temp_dir, 'export2.tar.gz')
        export([sd3], outfile=filename2, silent=True)
        self.clean_db()
        self.insert_data()
        import_data(filename2, silent=True)

        # Check that the imported nodes are correctly imported and that
        # the user assigned to the nodes is the right one
        for uuid in uuids1:
            self.assertEqual(orm.load_node(uuid).user.email, new_email)
        for uuid in uuids2:
            self.assertEqual(orm.load_node(uuid).user.email, manager.get_profile().default_user)
