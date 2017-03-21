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
import unittest

from aiida.backends.testbase import AiidaTestCase
from aiida.orm.node import Node


class TestComputer(AiidaTestCase):
    """
    Test the Computer class.
    """

    def test_deletion(self):
        from aiida.orm.computer import Computer
        from aiida.orm import delete_computer, JobCalculation
        from aiida.common.exceptions import InvalidOperation
        import aiida.backends.sqlalchemy

        newcomputer = Computer(name="testdeletioncomputer", hostname='localhost',
                               transport_type='local',
                               scheduler_type='pbspro',
                               workdir='/tmp/aiida').store()

        # # This should be possible, because nothing is using this computer
        delete_computer(newcomputer)

        calc_params = {
            'computer': self.computer,
            'resources': {'num_machines': 1,
                          'num_mpiprocs_per_machine': 1}
        }

        _ = JobCalculation(**calc_params).store()

        session = aiida.backends.sqlalchemy.get_scoped_session()

        # This should fail, because there is at least a calculation
        # using this computer (the one created just above)
        try:
            session.begin_nested()
            with self.assertRaises(InvalidOperation):
                delete_computer(self.computer)
        finally:
            session.rollback()


class TestGroupsSqla(AiidaTestCase):
    """
     Characterized functions
     """

    def test_query(self):
        """
        Test if queries are working
        """
        from aiida.orm.group import Group
        from aiida.common.exceptions import NotExistent, MultipleObjectsError

        from aiida.backends.sqlalchemy.models.user import DbUser
        from aiida.backends.utils import get_automatic_user

        g1 = Group(name='testquery1').store()
        g2 = Group(name='testquery2').store()

        n1 = Node().store()
        n2 = Node().store()
        n3 = Node().store()
        n4 = Node().store()

        g1.add_nodes([n1, n2])
        g2.add_nodes([n1, n3])

        newuser = DbUser(email='test@email.xx', password='')
        g3 = Group(name='testquery3', user=newuser).store()

        # I should find it
        g1copy = Group.get(uuid=g1.uuid)
        self.assertEquals(g1.pk, g1copy.pk)

        # Try queries
        res = Group.query(nodes=n4)
        self.assertEquals([_.pk for _ in res], [])

        res = Group.query(nodes=n1)
        self.assertEquals([_.pk for _ in res], [_.pk for _ in [g1, g2]])

        res = Group.query(nodes=n2)
        self.assertEquals([_.pk for _ in res], [_.pk for _ in [g1]])

        # I try to use 'get' with zero or multiple results
        with self.assertRaises(NotExistent):
            Group.get(nodes=n4)
        with self.assertRaises(MultipleObjectsError):
            Group.get(nodes=n1)

        self.assertEquals(Group.get(nodes=n2).pk, g1.pk)

        # Query by user
        res = Group.query(user=newuser)
        self.assertEquals(set(_.pk for _ in res), set(_.pk for _ in [g3]))

        # Same query, but using a string (the username=email) instead of
        # a DbUser object
        res = Group.query(user=newuser.email)
        self.assertEquals(set(_.pk for _ in res), set(_.pk for _ in [g3]))

        res = Group.query(user=get_automatic_user())

        self.assertEquals(set(_.pk for _ in res), set(_.pk for _ in [g1, g2]))

        # Final cleanup
        g1.delete()
        g2.delete()
        newuser.delete()


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

        self.assertEqual(n1.get_extras(),{'pippo': [1, 2, u'a'], 'pippobis': [5, 6, u'c']})

        self.assertEquals(n2.get_extras(), {'pippo2': [3, 4, 'b']})

        new_attrs = {"newval1": "v", "newval2": [1, {"c": "d", "e": 2}]}

        n1.reset_extras(new_attrs)
        self.assertEquals(n1.get_extras(), new_attrs)
        self.assertEquals(n2.get_extras(), {'pippo2': [3, 4, 'b']})

        n1.del_extra('newval2')
        del new_attrs['newval2']
        self.assertEquals(n1.get_extras(), new_attrs)
        # Also check that other nodes were not damaged
        self.assertEquals(n2.get_extras(), {'pippo2': [3, 4, 'b']})
