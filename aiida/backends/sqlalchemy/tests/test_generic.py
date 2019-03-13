# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Generic tests that need the be specific to sqlalchemy
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.backends.testbase import AiidaTestCase
from aiida.orm import Data, Node
from six.moves import range


class TestComputer(AiidaTestCase):
    """
    Test the Computer class.
    """

    def test_deletion(self):
        from aiida.orm import CalcJobNode
        from aiida.common.exceptions import InvalidOperation
        import aiida.backends.sqlalchemy

        newcomputer = self.backend.computers.create(
            name="testdeletioncomputer",
            hostname='localhost',
            transport_type='local',
            scheduler_type='pbspro')
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
                self.backend.computers.delete(self.computer.id)
        finally:
            session.rollback()


class TestGroupsSqla(AiidaTestCase):
    """
     Characterized functions
     """

    def setUp(self):
        from aiida.orm.implementation import sqlalchemy as sqla
        super(TestGroupsSqla, self).setUp()
        self.assertIsInstance(self.backend, sqla.backend.SqlaBackend)

    def test_query(self):
        """
        Test if queries are working
        """
        from aiida.common.exceptions import NotExistent, MultipleObjectsError

        backend = self.backend

        simple_user = backend.users.create('simple@ton.com')

        g1 = backend.groups.create(label='testquery1', user=simple_user).store()
        self.addCleanup(lambda: backend.groups.delete(g1.id))
        g2 = backend.groups.create(label='testquery2', user=simple_user).store()
        self.addCleanup(lambda: backend.groups.delete(g2.id))

        n1 = Data().store().backend_entity
        n2 = Data().store().backend_entity
        n3 = Data().store().backend_entity
        n4 = Data().store().backend_entity

        g1.add_nodes([n1, n2])
        g2.add_nodes([n1, n3])

        # NOTE: Here we pass type_string to query and get calls so that these calls don't
        # find the autogroups (otherwise the assertions will fail)
        newuser = backend.users.create(email='test@email.xx')
        g3 = backend.groups.create(label='testquery3', user=newuser).store()

        # I should find it
        g1copy = backend.groups.get(uuid=g1.uuid)
        self.assertEquals(g1.pk, g1copy.pk)

        # Try queries
        res = backend.groups.query(nodes=n4, type_string='')
        self.assertEquals([_.pk for _ in res], [])

        res = backend.groups.query(nodes=n1, type_string='')
        self.assertEquals([_.pk for _ in res], [_.pk for _ in [g1, g2]])

        res = backend.groups.query(nodes=n2, type_string='')
        self.assertEquals([_.pk for _ in res], [_.pk for _ in [g1]])

        # I try to use 'get' with zero or multiple results
        with self.assertRaises(NotExistent):
            backend.groups.get(nodes=n4, type_string='')
        with self.assertRaises(MultipleObjectsError):
            backend.groups.get(nodes=n1, type_string='')

        self.assertEquals(backend.groups.get(nodes=n2, type_string='').pk, g1.pk)

        # Query by user
        res = backend.groups.query(user=newuser, type_string='')
        self.assertSetEqual(set(_.pk for _ in res), set(_.pk for _ in [g3]))

        # Same query, but using a string (the username=email) instead of
        # a DbUser object
        res = backend.groups.query(user=newuser, type_string='')
        self.assertSetEqual(set(_.pk for _ in res), set(_.pk for _ in [g3]))

        res = backend.groups.query(user=simple_user, type_string='')

        self.assertSetEqual(set(_.pk for _ in res), set(_.pk for _ in [g1, g2]))


class TestGroupNoOrmSQLA(AiidaTestCase):
    """
    These tests check that the group node addition works ok when the skip_orm=True flag is used
    """

    def test_group_general(self):
        """
        General tests to verify that the group addition with the skip_orm=True flag
        work properly
        """
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
        """
        Test that the group addition in batches works as expected.
        """
        from aiida.orm.groups import Group

        # Create 100 nodes
        nodes = []
        for _ in range(100):
            nodes.append(Data().store().backend_entity)

        # Add nodes to groups using different batch size. Check in the end the
        # correct addition.
        batch_sizes = (1, 3, 10, 1000)
        for batch_size in batch_sizes:
            group = Group(name='test_batches_' + str(batch_size)).store()
            group.backend_entity.add_nodes(nodes, skip_orm=True, batch_size=batch_size)
            self.assertEqual(set(_.pk for _ in nodes), set(_.pk for _ in group.nodes))


class TestDbExtrasSqla(AiidaTestCase):
    """
     Characterized functions
     """

    def test_replacement_1(self):
        n1 = Data().store()
        n2 = Data().store()

        n1.set_extra("pippo", [1, 2, u'a'])

        n1.set_extra("pippobis", [5, 6, u'c'])

        n2.set_extra("pippo2", [3, 4, u'b'])

        self.assertEqual(n1.extras,
                         {'pippo': [1, 2, u'a'], 'pippobis': [5, 6, u'c'], '_aiida_hash': n1.get_hash()})

        self.assertEquals(n2.extras, {'pippo2': [3, 4, 'b'], '_aiida_hash': n2.get_hash()})

        new_attrs = {"newval1": "v", "newval2": [1, {"c": "d", "e": 2}]}

        n1.reset_extras(new_attrs)
        self.assertEquals(n1.extras, new_attrs)
        self.assertEquals(n2.extras, {'pippo2': [3, 4, 'b'], '_aiida_hash': n2.get_hash()})

        n1.delete_extra('newval2')
        del new_attrs['newval2']
        self.assertEquals(n1.extras, new_attrs)
        # Also check that other nodes were not damaged
        self.assertEquals(n2.extras, {'pippo2': [3, 4, 'b'], '_aiida_hash': n2.get_hash()})
