# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Generic tests that need the be specific to sqlalchemy."""

from aiida.backends.testbase import AiidaTestCase
from aiida.orm import Data


class TestComputer(AiidaTestCase):
    """Test the Computer class."""

    def test_deletion(self):
        """Test computer deletion."""
        from aiida.orm import CalcJobNode
        from aiida.common.exceptions import InvalidOperation
        import aiida.backends.sqlalchemy

        newcomputer = self.backend.computers.create(
            name='testdeletioncomputer', hostname='localhost', transport_type='local', scheduler_type='pbspro'
        )
        newcomputer.store()

        # This should be possible, because nothing is using this computer
        self.backend.computers.delete(newcomputer.id)

        node = CalcJobNode()
        node.computer = self.computer
        node.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        node.store()

        session = aiida.backends.sqlalchemy.get_scoped_session()

        # This should fail, because there is at least a calculation
        # using this computer (the one created just above)
        try:
            session.begin_nested()
            with self.assertRaises(InvalidOperation):
                self.backend.computers.delete(self.computer.id)  # pylint: disable=no-member
        finally:
            session.rollback()


class TestGroupsSqla(AiidaTestCase):
    """Test group queries for sqlalchemy backend."""

    def setUp(self):
        from aiida.orm.implementation import sqlalchemy as sqla
        super().setUp()
        self.assertIsInstance(self.backend, sqla.backend.SqlaBackend)

    def test_query(self):
        """Test if queries are working."""
        from aiida.common.exceptions import NotExistent, MultipleObjectsError

        backend = self.backend

        simple_user = backend.users.create('simple@ton.com')

        g_1 = backend.groups.create(label='testquery1', user=simple_user).store()
        self.addCleanup(lambda: backend.groups.delete(g_1.id))
        g_2 = backend.groups.create(label='testquery2', user=simple_user).store()
        self.addCleanup(lambda: backend.groups.delete(g_2.id))

        n_1 = Data().store().backend_entity
        n_2 = Data().store().backend_entity
        n_3 = Data().store().backend_entity
        n_4 = Data().store().backend_entity

        g_1.add_nodes([n_1, n_2])
        g_2.add_nodes([n_1, n_3])

        # NOTE: Here we pass type_string to query and get calls so that these calls don't
        # find the autogroups (otherwise the assertions will fail)
        newuser = backend.users.create(email='test@email.xx')
        g_3 = backend.groups.create(label='testquery3', user=newuser).store()

        # I should find it
        g_1copy = backend.groups.get(uuid=g_1.uuid)
        self.assertEqual(g_1.pk, g_1copy.pk)

        # Try queries
        res = backend.groups.query(nodes=n_4, type_string='')
        self.assertEqual([_.pk for _ in res], [])

        res = backend.groups.query(nodes=n_1, type_string='')
        self.assertEqual([_.pk for _ in res], [_.pk for _ in [g_1, g_2]])

        res = backend.groups.query(nodes=n_2, type_string='')
        self.assertEqual([_.pk for _ in res], [_.pk for _ in [g_1]])

        # I try to use 'get' with zero or multiple results
        with self.assertRaises(NotExistent):
            backend.groups.get(nodes=n_4, type_string='')
        with self.assertRaises(MultipleObjectsError):
            backend.groups.get(nodes=n_1, type_string='')

        self.assertEqual(backend.groups.get(nodes=n_2, type_string='').pk, g_1.pk)

        # Query by user
        res = backend.groups.query(user=newuser, type_string='')
        self.assertSetEqual(set(_.pk for _ in res), set(_.pk for _ in [g_3]))

        # Same query, but using a string (the username=email) instead of
        # a DbUser object
        res = backend.groups.query(user=newuser, type_string='')
        self.assertSetEqual(set(_.pk for _ in res), set(_.pk for _ in [g_3]))

        res = backend.groups.query(user=simple_user, type_string='')

        self.assertSetEqual(set(_.pk for _ in res), set(_.pk for _ in [g_1, g_2]))


class TestGroupNoOrmSQLA(AiidaTestCase):
    """These tests check that the group node addition works ok when the skip_orm=True flag is used."""

    def test_group_general(self):
        """General tests to verify that the group addition with the skip_orm=True flag
        work properly."""
        backend = self.backend

        node_01 = Data().store().backend_entity
        node_02 = Data().store().backend_entity
        node_03 = Data().store().backend_entity
        node_04 = Data().store().backend_entity
        node_05 = Data().store().backend_entity
        nodes = [node_01, node_02, node_03, node_04, node_05]

        simple_user = backend.users.create('simple1@ton.com')
        group = backend.groups.create(label='test_adding_nodes', user=simple_user).store()
        # Single node in a list
        group.add_nodes([node_01], skip_orm=True)
        # List of nodes
        group.add_nodes([node_02, node_03], skip_orm=True)
        # Tuple of nodes
        group.add_nodes((node_04, node_05), skip_orm=True)

        # Check
        self.assertEqual(set(_.pk for _ in nodes), set(_.pk for _ in group.nodes))

        # Try to add a node that is already present: there should be no problem
        group.add_nodes([node_01], skip_orm=True)
        self.assertEqual(set(_.pk for _ in nodes), set(_.pk for _ in group.nodes))

    def test_group_batch_size(self):
        """Test that the group addition in batches works as expected."""
        from aiida.orm.groups import Group

        # Create 100 nodes
        nodes = []
        for _ in range(100):
            nodes.append(Data().store().backend_entity)

        # Add nodes to groups using different batch size. Check in the end the
        # correct addition.
        batch_sizes = (1, 3, 10, 1000)
        for batch_size in batch_sizes:
            group = Group(label='test_batches_' + str(batch_size)).store()
            group.backend_entity.add_nodes(nodes, skip_orm=True, batch_size=batch_size)
            self.assertEqual(set(_.pk for _ in nodes), set(_.pk for _ in group.nodes))
