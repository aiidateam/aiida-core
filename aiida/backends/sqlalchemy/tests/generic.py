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
from aiida.orm.node import Node
from aiida.common import exceptions


class TestComputer(AiidaTestCase):
    """
    Test the Computer class.
    """

    def test_deletion(self):
        from aiida.orm.node.process import CalcJobNode
        from aiida.common.exceptions import InvalidOperation
        import aiida.backends.sqlalchemy

        newcomputer = self.backend.computers.create(
            name="testdeletioncomputer",
            hostname='localhost',
            transport_type='local',
            scheduler_type='pbspro').store()

        # # This should be possible, because nothing is using this computer
        self.backend.computers.delete(newcomputer.id)

        calc_params = {
            'computer': self.computer,
            'resources': {'num_machines': 1,
                          'num_mpiprocs_per_machine': 1}
        }

        _ = CalcJobNode(**calc_params).store()

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
        self.assertIsInstance(self.backend, sqla.SqlaBackend)

    def test_query(self):
        """
        Test if queries are working
        """
        from aiida.common.exceptions import NotExistent, MultipleObjectsError

        backend = self.backend

        simple_user = backend.users.create('simple@ton.com')

        g1 = backend.groups.create(name='testquery1', user=simple_user).store()
        self.addCleanup(lambda: backend.groups.delete(g1.id))
        g2 = backend.groups.create(name='testquery2', user=simple_user).store()
        self.addCleanup(lambda: backend.groups.delete(g2.id))

        n1 = Node().store()
        n2 = Node().store()
        n3 = Node().store()
        n4 = Node().store()

        g1.add_nodes([n1, n2])
        g2.add_nodes([n1, n3])

        # NOTE: Here we pass type_string to query and get calls so that these calls don't
        # find the autogroups (otherwise the assertions will fail)
        newuser = backend.users.create(email='test@email.xx')
        g3 = backend.groups.create(name='testquery3', user=newuser).store()

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

    def test_rename_existing(self):
        """
        Test that renaming to an already existing name is not permitted
        """
        from aiida.backends.sqlalchemy import get_scoped_session

        backend = self.backend
        user = backend.users.create(email="{}@aiida.net".format(self.id())).store()

        name_group_a = 'group_a'
        name_group_c = 'group_c'

        group_a = backend.groups.create(name=name_group_a, description='I am the Original G', user=user)
        group_a.store()

        # Before storing everything should be fine
        group_b = backend.groups.create(name=name_group_a, description='They will try to rename me', user=user)
        group_c = backend.groups.create(name=name_group_c, description='They will try to rename me', user=user)

        session = get_scoped_session()

        # Storing for duplicate group name should trigger Integrity
        try:
            session.begin_nested()
            with self.assertRaises(exceptions.IntegrityError):
                group_b.store()
        finally:
            session.rollback()

        # Before storing everything should be fine
        group_c.name = name_group_a

        # Reverting to unique name before storing
        group_c.name = name_group_c
        group_c.store()

        # After storing name change to existing should raise
        try:
            session.begin_nested()
            with self.assertRaises(exceptions.IntegrityError):
                group_c.name = name_group_a
        finally:
            session.rollback()


class TestDbExtrasSqla(AiidaTestCase):
    """
     Characterized functions
     """

    def test_replacement_1(self):
        n1 = Node().store()
        n2 = Node().store()

        n1.set_extra("pippo", [1, 2, u'a'])

        n1.set_extra("pippobis", [5, 6, u'c'])

        n2.set_extra("pippo2", [3, 4, u'b'])

        self.assertEqual(n1.get_extras(),
                         {'pippo': [1, 2, u'a'], 'pippobis': [5, 6, u'c'], '_aiida_hash': n1.get_hash()})

        self.assertEquals(n2.get_extras(), {'pippo2': [3, 4, 'b'], '_aiida_hash': n2.get_hash()})

        new_attrs = {"newval1": "v", "newval2": [1, {"c": "d", "e": 2}]}

        n1.reset_extras(new_attrs)
        self.assertEquals(n1.get_extras(), new_attrs)
        self.assertEquals(n2.get_extras(), {'pippo2': [3, 4, 'b'], '_aiida_hash': n2.get_hash()})

        n1.del_extra('newval2')
        del new_attrs['newval2']
        self.assertEquals(n1.get_extras(), new_attrs)
        # Also check that other nodes were not damaged
        self.assertEquals(n2.get_extras(), {'pippo2': [3, 4, 'b'], '_aiida_hash': n2.get_hash()})
