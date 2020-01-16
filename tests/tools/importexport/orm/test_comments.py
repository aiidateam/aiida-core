# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""orm.Comment tests for the export and import routines"""
# pylint: disable=too-many-locals,too-many-statements

import os

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.tools.importexport import import_data, export

from tests.utils.configuration import with_temp_dir


class TestComments(AiidaTestCase):
    """Test ex-/import cases related to Comments"""

    def setUp(self):
        super().setUp()
        self.reset_database()
        self.comments = [
            "We're no strangers to love", 'You know the rules and so do I', "A full commitment's what I'm thinking of",
            "You wouldn't get this from any other guy"
        ]

    def tearDown(self):
        super().tearDown()
        self.reset_database()

    @with_temp_dir
    def test_multiple_imports_for_single_node(self, temp_dir):
        """Test multiple imports for single node with different comments are imported correctly"""
        user = orm.User.objects.get_default()

        # Create Node and initial comments and save UUIDs prior to export
        node = orm.CalculationNode().store()
        node.seal()
        comment_one = orm.Comment(node, user, self.comments[0]).store()
        comment_two = orm.Comment(node, user, self.comments[1]).store()
        node_uuid = node.uuid
        comment_uuids = [c.uuid for c in [comment_one, comment_two]]

        # Export as "EXISTING" DB
        export_file_existing = os.path.join(temp_dir, 'export_EXISTING.tar.gz')
        export([node], outfile=export_file_existing, silent=True)

        # Add 2 more Comments and save UUIDs prior to export
        comment_three = orm.Comment(node, user, self.comments[2]).store()
        comment_four = orm.Comment(node, user, self.comments[3]).store()
        comment_uuids += [c.uuid for c in [comment_three, comment_four]]

        # Export as "FULL" DB
        export_file_full = os.path.join(temp_dir, 'export_FULL.tar.gz')
        export([node], outfile=export_file_full, silent=True)

        # Clean database and reimport "EXISTING" DB
        self.reset_database()
        import_data(export_file_existing, silent=True)

        # Check correct import
        builder = orm.QueryBuilder().append(orm.Node, tag='node', project=['uuid'])
        builder.append(orm.Comment, with_node='node', project=['uuid', 'content'])
        builder = builder.all()

        self.assertEqual(len(builder), 2)  # There are 2 Comments in "EXISTING" DB

        imported_node_uuid = builder[0][0]
        self.assertEqual(imported_node_uuid, node_uuid)
        for comment in builder:
            imported_comment_uuid = comment[1]
            imported_comment_content = comment[2]

            self.assertIn(imported_comment_uuid, comment_uuids[0:2])
            self.assertIn(imported_comment_content, self.comments[0:2])

        # Import "FULL" DB
        import_data(export_file_full, silent=True)

        # Since the UUID of the node is identical with the node already in the DB,
        # the Comments should be added to the existing node, avoiding the addition
        # of the two Comments already present.
        # Check this by retrieving all Comments for the node.
        builder = orm.QueryBuilder().append(orm.Node, tag='node', project=['uuid'])
        builder.append(orm.Comment, with_node='node', project=['uuid', 'content'])
        builder = builder.all()

        self.assertEqual(len(builder), len(self.comments))  # There should now be 4 Comments

        imported_node_uuid = builder[0][0]
        self.assertEqual(imported_node_uuid, node_uuid)
        for comment in builder:
            imported_comment_uuid = comment[1]
            imported_comment_content = comment[2]

            self.assertIn(imported_comment_uuid, comment_uuids)
            self.assertIn(imported_comment_content, self.comments)

    @with_temp_dir
    def test_exclude_comments_flag(self, temp_dir):
        """Test comments and associated commenting users are not exported when using `include_comments=False`."""
        # Create users, node, and comments
        user_one = orm.User.objects.get_default()
        user_two = orm.User(email='commenting@user.s').store()

        node = orm.Data().store()

        orm.Comment(node, user_one, self.comments[0]).store()
        orm.Comment(node, user_one, self.comments[1]).store()
        orm.Comment(node, user_two, self.comments[2]).store()
        orm.Comment(node, user_two, self.comments[3]).store()

        # Get values prior to export
        users_email = [u.email for u in [user_one, user_two]]
        node_uuid = node.uuid

        # Check that node belongs to user_one
        self.assertEqual(node.user.email, users_email[0])

        # Export nodes, excluding comments
        export_file = os.path.join(temp_dir, 'export.tar.gz')
        export([node], outfile=export_file, silent=True, include_comments=False)

        # Clean database and reimport exported file
        self.reset_database()
        import_data(export_file, silent=True)

        # Get node, users, and comments
        import_nodes = orm.QueryBuilder().append(orm.Node, project=['uuid']).all()
        import_comments = orm.QueryBuilder().append(orm.Comment, project=['uuid']).all()
        import_users = orm.QueryBuilder().append(orm.User, project=['email']).all()

        # There should be exactly: 1 Node, 0 Comments, 1 User
        self.assertEqual(len(import_nodes), 1)
        self.assertEqual(len(import_comments), 0)
        self.assertEqual(len(import_users), 1)

        # Check it's the correct user (and node)
        self.assertEqual(str(import_nodes[0][0]), node_uuid)
        self.assertEqual(str(import_users[0][0]), users_email[0])

    @with_temp_dir
    def test_calc_and_data_nodes_with_comments(self, temp_dir):
        """ Test comments for CalculatioNode and Data node are correctly ex-/imported """
        # Create user, nodes, and comments
        user = orm.User.objects.get_default()

        calc_node = orm.CalculationNode().store()
        calc_node.seal()
        data_node = orm.Data().store()

        comment_one = orm.Comment(calc_node, user, self.comments[0]).store()
        comment_two = orm.Comment(calc_node, user, self.comments[1]).store()

        comment_three = orm.Comment(data_node, user, self.comments[2]).store()
        comment_four = orm.Comment(data_node, user, self.comments[3]).store()

        # Get values prior to export
        calc_uuid = calc_node.uuid
        data_uuid = data_node.uuid
        calc_comments_uuid = [c.uuid for c in [comment_one, comment_two]]
        data_comments_uuid = [c.uuid for c in [comment_three, comment_four]]

        # Export nodes
        export_file = os.path.join(temp_dir, 'export.tar.gz')
        export([calc_node, data_node], outfile=export_file, silent=True)

        # Clean database and reimport exported file
        self.reset_database()
        import_data(export_file, silent=True)

        # Get nodes and comments
        builder = orm.QueryBuilder()
        builder.append(orm.Node, tag='node', project=['uuid'])
        builder.append(orm.Comment, with_node='node', project=['uuid'])
        nodes_and_comments = builder.all()

        self.assertEqual(len(nodes_and_comments), len(self.comments))
        for entry in nodes_and_comments:
            self.assertEqual(len(entry), 2)  # 1 Node + 1 Comment

            import_node_uuid = str(entry[0])
            import_comment_uuid = str(entry[1])

            self.assertIn(import_node_uuid, [calc_uuid, data_uuid])
            if import_node_uuid == calc_uuid:
                # Calc node comments
                self.assertIn(import_comment_uuid, calc_comments_uuid)
            else:
                # Data node comments
                self.assertIn(import_comment_uuid, data_comments_uuid)

    @with_temp_dir
    def test_multiple_user_comments_single_node(self, temp_dir):
        """ Test multiple users commenting on a single orm.CalculationNode """
        # Create users, node, and comments
        user_one = orm.User.objects.get_default()
        user_two = orm.User(email='commenting@user.s').store()

        node = orm.CalculationNode().store()
        node.seal()

        comment_one = orm.Comment(node, user_one, self.comments[0]).store()
        comment_two = orm.Comment(node, user_one, self.comments[1]).store()

        comment_three = orm.Comment(node, user_two, self.comments[2]).store()
        comment_four = orm.Comment(node, user_two, self.comments[3]).store()

        # Get values prior to export
        users_email = [u.email for u in [user_one, user_two]]
        node_uuid = str(node.uuid)
        user_one_comments_uuid = [str(c.uuid) for c in [comment_one, comment_two]]
        user_two_comments_uuid = [str(c.uuid) for c in [comment_three, comment_four]]

        # Export node, along with comments and users recursively
        export_file = os.path.join(temp_dir, 'export.tar.gz')
        export([node], outfile=export_file, silent=True)

        # Clean database and reimport exported file
        self.reset_database()
        import_data(export_file, silent=True)

        # Get node, users, and comments
        builder = orm.QueryBuilder()
        builder.append(orm.Node, tag='node', project=['uuid'])
        builder.append(orm.Comment, tag='comment', with_node='node', project=['uuid'])
        builder.append(orm.User, with_comment='comment', project=['email'])
        entries = builder.all()

        # Check that all 4 comments are retrieved, along with their respective node and user
        self.assertEqual(len(entries), len(self.comments))

        # Go through [Node.uuid, Comment.uuid, User.email]-entries
        imported_node_uuids = set()
        imported_user_one_comment_uuids = set()
        imported_user_two_comment_uuids = set()
        imported_user_emails = set()
        for entry in entries:
            self.assertEqual(len(entry), 3)  # 1 Node + 1 Comment + 1 User

            # Add node to set of imported nodes
            imported_node_uuids.add(str(entry[0]))

            # Add user to set of imported users
            import_user_email = entry[2]
            imported_user_emails.add(str(import_user_email))

            # Add comment to set of imported comments pertaining to correct user
            if import_user_email == users_email[0]:
                # User_one comments
                imported_user_one_comment_uuids.add(str(entry[1]))
            else:
                # User_two comments
                imported_user_two_comment_uuids.add(str(entry[1]))

        # Check same number of nodes (1) and users (2) were ex- and imported
        self.assertEqual(len(imported_node_uuids), 1)
        self.assertEqual(len(imported_user_emails), len(users_email))

        # Check imported node equals exported node
        self.assertSetEqual(imported_node_uuids, {node_uuid})

        # Check imported user is part of exported users
        self.assertSetEqual(imported_user_emails, set(users_email))

        # Check same number of comments (2) pertaining to each user were ex- and imported
        self.assertEqual(len(imported_user_one_comment_uuids), len(user_one_comments_uuid))
        self.assertEqual(len(imported_user_two_comment_uuids), len(user_two_comments_uuid))

        # Check imported comments equal exported comments pertaining to specific user
        self.assertSetEqual(imported_user_one_comment_uuids, set(user_one_comments_uuid))
        self.assertSetEqual(imported_user_two_comment_uuids, set(user_two_comments_uuid))

    @with_temp_dir
    def test_mtime_of_imported_comments(self, temp_dir):
        """
        Test mtime does not change for imported comments
        This is related to correct usage of `comment_mode` when importing.
        """
        # Get user
        user = orm.User.objects.get_default()

        comment_content = 'You get what you give'

        # Create node
        calc = orm.CalculationNode().store()
        calc.seal()

        # Create comment
        orm.Comment(calc, user, comment_content).store()
        calc.store()

        # Save UUIDs and mtime
        calc_uuid = calc.uuid
        builder = orm.QueryBuilder().append(orm.Comment, project=['uuid', 'mtime']).all()
        comment_uuid = str(builder[0][0])
        comment_mtime = builder[0][1]

        builder = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid', 'mtime']).all()
        calc_uuid = str(builder[0][0])
        calc_mtime = builder[0][1]

        # Export, reset database and reimport
        export_file = os.path.join(temp_dir, 'export.tar.gz')
        export([calc], outfile=export_file, silent=True)
        self.reset_database()
        import_data(export_file, silent=True)

        # Retrieve node and comment
        builder = orm.QueryBuilder().append(orm.CalculationNode, tag='calc', project=['uuid', 'mtime'])
        builder.append(orm.Comment, with_node='calc', project=['uuid', 'mtime'])

        import_entities = builder.all()[0]

        self.assertEqual(len(import_entities), 4)  # Check we have the correct amount of returned values

        import_calc_uuid = str(import_entities[0])
        import_calc_mtime = import_entities[1]
        import_comment_uuid = str(import_entities[2])
        import_comment_mtime = import_entities[3]

        # Check we have the correct UUIDs
        self.assertEqual(import_calc_uuid, calc_uuid)
        self.assertEqual(import_comment_uuid, comment_uuid)

        # Make sure the mtime is the same after import as it was before export
        self.assertEqual(import_comment_mtime, comment_mtime)
        self.assertEqual(import_calc_mtime, calc_mtime)

    @with_temp_dir
    def test_import_arg_comment_mode(self, temp_dir):
        """
        Test the import keyword `comment_mode`.
        It may be `'newest'` or `'overwrite'`.
        Test import of 'old' comment that has since been changed in DB.
        """
        from aiida.tools.importexport.common.exceptions import ImportValidationError

        # Get user
        # Will have to do this again after resetting the DB
        user = orm.User.objects.get_default()

        ## Test comment_mode='newest'
        # Create node
        calc = orm.CalculationNode().store()
        calc.seal()
        calc_uuid = calc.uuid

        # Creates comment
        cmt = orm.Comment(calc, user, self.comments[0]).store()
        cmt_uuid = cmt.uuid

        # Export calc and comment
        export_file = os.path.join(temp_dir, 'export_file.tar.gz')
        export([calc], outfile=export_file, silent=True)

        # Update comment
        cmt.set_content(self.comments[1])

        # Check that Comment has been updated, and that there is only 1
        export_comments = orm.QueryBuilder().append(orm.Comment, project=['uuid', 'content'])
        self.assertEqual(export_comments.count(), 1)
        self.assertEqual(export_comments.all()[0][0], cmt_uuid)
        self.assertEqual(export_comments.all()[0][1], self.comments[1])

        # Export calc and UPDATED comment
        export_file_updated = os.path.join(temp_dir, 'export_file_updated.tar.gz')
        export([calc], outfile=export_file_updated, silent=True)

        # Reimport exported 'old' calc and comment
        import_data(export_file, silent=True, comment_mode='newest')

        # Check there are exactly 1 CalculationNode and 1 Comment
        import_calcs = orm.QueryBuilder().append(orm.CalculationNode, tag='calc', project=['uuid'])
        self.assertEqual(import_calcs.count(), 1)
        import_comments = import_calcs.append(orm.Comment, with_node='calc', project=['uuid', 'content'])
        self.assertEqual(import_comments.count(), 1)

        # Check the uuids have not changed
        self.assertEqual(import_calcs.all()[0][0], calc_uuid)
        self.assertEqual(import_comments.all()[0][1], cmt_uuid)

        # Check the content of the comment has NOT been rewritten ('newest' mode)
        self.assertEqual(import_comments.all()[0][2], self.comments[1])

        ## Test comment_mode='overwrite'
        # Reimport exported 'old' calc and comment
        import_data(export_file, silent=True, comment_mode='overwrite')

        # Check there are exactly 1 CalculationNode and 1 Comment
        import_calcs = orm.QueryBuilder().append(orm.CalculationNode, tag='calc', project=['uuid'])
        import_comments = import_calcs.append(orm.Comment, with_node='calc', project=['uuid', 'content'])
        self.assertEqual(import_calcs.count(), 1)
        self.assertEqual(import_comments.count(), 1)

        # Check the uuids have not changed
        self.assertEqual(import_calcs.all()[0][0], calc_uuid)
        self.assertEqual(import_comments.all()[0][1], cmt_uuid)

        # Check the content of the comment HAS been rewritten ('overwrite' mode)
        self.assertEqual(import_comments.all()[0][2], self.comments[0])

        ## Test ValueError is raised when using a wrong comment_mode:
        with self.assertRaises(ImportValidationError):
            import_data(export_file, silent=True, comment_mode='invalid')

    @with_temp_dir
    def test_reimport_of_comments_for_single_node(self, temp_dir):
        """
        When a node with comments already exist in the DB, and more comments are
        imported for the same node (same UUID), test that only new comment-entries
        are added.

        Part I:
        Create CalculationNode and 1 Comment for it.
        Export CalculationNode with its 1 Comment to export file #1 "EXISTING database".
        Add 3 Comments to CalculationNode.
        Export CalculationNode with its 4 Comments to export file #2 "FULL database".
        Reset database.

        Part II:
        Reimport export file #1 "EXISTING database".
        Add 3 Comments to CalculationNode.
        Export CalculationNode with its 4 Comments to export file #3 "NEW database".
        Reset database.

        Part III:
        Reimport export file #1 "EXISTING database" (1 CalculationNode, 1 Comment).
        Import export file #2 "FULL database" (1 CalculationNode, 4 Comments).
        Check the database EXACTLY contains 1 CalculationNode and 4 Comments,
        with matching UUIDS all the way through all previous Parts.

        Part IV:
        Import export file #3 "NEW database" (1 CalculationNode, 4 Comments).
        Check the database EXACTLY contains 1 CalculationNode and 7 Comments,
        with matching UUIDS all the way through all previous Parts.
        NB! There should now be 7 Comments in the database. 6 of which are identical
        in pairs, except for their UUID.
        """
        export_filenames = {
            'EXISTING': 'export_EXISTING_db.tar.gz',
            'FULL': 'export_FULL_db.tar.gz',
            'NEW': 'export_NEW_db.tar.gz'
        }

        # Get user
        # Will have to do this again after resetting the DB
        user = orm.User.objects.get_default()

        ## Part I
        # Create node and save UUID
        calc = orm.CalculationNode()
        calc.store()
        calc.seal()
        calc_uuid = calc.uuid

        # Create first comment
        orm.Comment(calc, user, self.comments[0]).store()

        # There should be exactly: 1 CalculationNode, 1 Comment
        export_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid'])
        export_comments = orm.QueryBuilder().append(orm.Comment, project=['uuid'])
        self.assertEqual(export_calcs.count(), 1)
        self.assertEqual(export_comments.count(), 1)

        # Save Comment UUID before export
        existing_comment_uuids = [str(export_comments.all()[0][0])]

        # Export "EXISTING" DB
        export_file_existing = os.path.join(temp_dir, export_filenames['EXISTING'])
        export([calc], outfile=export_file_existing, silent=True)

        # Add remaining Comments
        for comment in self.comments[1:]:
            orm.Comment(calc, user, comment).store()

        # There should be exactly: 1 CalculationNode, 3 Comments (len(self.comments))
        export_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid'])
        export_comments = orm.QueryBuilder().append(orm.Comment, project=['uuid'])
        self.assertEqual(export_calcs.count(), 1)
        self.assertEqual(export_comments.count(), len(self.comments))

        # Save Comment UUIDs before export, there should be 4 UUIDs in total (len(self.comments))
        full_comment_uuids = set(existing_comment_uuids)
        for comment_uuid in export_comments.all():
            full_comment_uuids.add(str(comment_uuid[0]))
        self.assertEqual(len(full_comment_uuids), len(self.comments))

        # Export "FULL" DB
        export_file_full = os.path.join(temp_dir, export_filenames['FULL'])
        export([calc], outfile=export_file_full, silent=True)

        # Clean database
        self.reset_database()

        ## Part II
        # Reimport "EXISTING" DB
        import_data(export_file_existing, silent=True)

        # Check the database is correctly imported.
        # There should be exactly: 1 CalculationNode, 1 Comment
        import_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid'])
        import_comments = orm.QueryBuilder().append(orm.Comment, project=['uuid'])
        self.assertEqual(import_calcs.count(), 1)
        self.assertEqual(import_comments.count(), 1)
        # Furthermore, the UUIDs should be the same
        self.assertEqual(str(import_calcs.all()[0][0]), calc_uuid)
        self.assertIn(str(import_comments.all()[0][0]), existing_comment_uuids)

        # Add remaining Comments (again)
        calc = orm.load_node(import_calcs.all()[0][0])  # Reload CalculationNode
        user = orm.User.objects.get_default()  # Get user - again
        for comment in self.comments[1:]:
            orm.Comment(calc, user, comment).store()

        # There should be exactly: 1 CalculationNode, 4 Comments (len(self.comments))
        export_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid'])
        export_comments = orm.QueryBuilder().append(orm.Comment, project=['uuid'])
        self.assertEqual(export_calcs.count(), 1)
        self.assertEqual(export_comments.count(), len(self.comments))

        # Save Comment UUIDs before export, there should be 4 UUIDs in total (len(self.comments))
        new_comment_uuids = set(existing_comment_uuids)
        for comment_uuid in export_comments.all():
            new_comment_uuids.add(str(comment_uuid[0]))
        self.assertEqual(len(new_comment_uuids), len(self.comments))

        # Export "NEW" DB
        export_file_new = os.path.join(temp_dir, export_filenames['NEW'])
        export([calc], outfile=export_file_new, silent=True)

        # Clean database
        self.reset_database()

        ## Part III
        # Reimport "EXISTING" DB
        import_data(export_file_existing, silent=True)

        # Check the database is correctly imported.
        # There should be exactly: 1 CalculationNode, 1 Comment
        import_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid'])
        import_comments = orm.QueryBuilder().append(orm.Comment, project=['uuid'])
        self.assertEqual(import_calcs.count(), 1)
        self.assertEqual(import_comments.count(), 1)
        # Furthermore, the UUIDs should be the same
        self.assertEqual(str(import_calcs.all()[0][0]), calc_uuid)
        self.assertIn(str(import_comments.all()[0][0]), existing_comment_uuids)

        # Import "FULL" DB
        import_data(export_file_full, silent=True)

        # Check the database is correctly imported.
        # There should be exactly: 1 CalculationNode, 4 Comments (len(self.comments))
        import_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid'])
        import_comments = orm.QueryBuilder().append(orm.Comment, project=['uuid'])
        self.assertEqual(import_calcs.count(), 1)
        self.assertEqual(import_comments.count(), len(self.comments))
        # Furthermore, the UUIDs should be the same
        self.assertEqual(str(import_calcs.all()[0][0]), calc_uuid)
        for comment in import_comments.all():
            comment_uuid = str(comment[0])
            self.assertIn(comment_uuid, full_comment_uuids)

        ## Part IV
        # Import "NEW" DB
        import_data(export_file_new, silent=True)

        # Check the database is correctly imported.
        # There should be exactly: 1 CalculationNode, 7 Comments (org. (1) + 2 x added (3) Comments)
        # 4 of the comments are identical in pairs, except for the UUID.
        import_calcs = orm.QueryBuilder().append(orm.CalculationNode, project=['uuid'])
        import_comments = orm.QueryBuilder().append(orm.Comment, project=['uuid', 'content'])
        self.assertEqual(import_calcs.count(), 1)
        self.assertEqual(import_comments.count(), 7)
        # Furthermore, the UUIDs should be the same
        self.assertEqual(str(import_calcs.all()[0][0]), calc_uuid)
        total_comment_uuids = full_comment_uuids.copy()
        total_comment_uuids.update(new_comment_uuids)
        for comment in import_comments.all():
            comment_uuid = str(comment[0])
            comment_content = str(comment[1])
            self.assertIn(comment_uuid, total_comment_uuids)
            self.assertIn(comment_content, self.comments)
