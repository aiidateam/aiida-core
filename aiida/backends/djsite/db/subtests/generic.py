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
Generic tests that need the use of the DB
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from aiida.backends.testbase import AiidaTestCase
from aiida.common import exceptions
from aiida.orm.node import Node
from aiida import orm


class TestComputer(AiidaTestCase):
    """
    Test the Computer class.
    """

    def test_deletion(self):
        from aiida.orm.node.process import CalcJobNode
        from aiida.common.exceptions import InvalidOperation

        newcomputer = orm.Computer(name="testdeletioncomputer", hostname='localhost',
                                   transport_type='local', scheduler_type='pbspro',
                                   workdir='/tmp/aiida').store()

        # # This should be possible, because nothing is using this computer
        self.backend.computers.delete(newcomputer.id)

        calc_params = {
            'computer': self.computer,
            'resources': {'num_machines': 1,
                          'num_mpiprocs_per_machine': 1}
        }

        _ = CalcJobNode(**calc_params).store()

        # This should fail, because there is at least a calculation
        # using this computer (the one created just above)
        with self.assertRaises(InvalidOperation):
            self.backend.computers.delete(self.computer.id)


class TestGroupsDjango(AiidaTestCase):
    """
    Test groups.
    """

    # Tests that are specific to the Django backend
    def test_query(self):
        """
        Test if queries are working
        """
        from aiida.common.exceptions import NotExistent, MultipleObjectsError

        backend = self.backend

        default_user = backend.users.create("{}@aiida.net".format(self.id())).store()

        g1 = backend.groups.create(name='testquery1', user=default_user).store()
        self.addCleanup(lambda: backend.groups.delete(g1.id))
        g2 = backend.groups.create(name='testquery2', user=default_user).store()
        self.addCleanup(lambda: backend.groups.delete(g2.id))

        n1 = Node().store()
        n2 = Node().store()
        n3 = Node().store()
        n4 = Node().store()

        g1.add_nodes([n1, n2])
        g2.add_nodes([n1, n3])

        newuser = backend.users.create(email='test@email.xx')
        g3 = backend.groups.create(name='testquery3', user=newuser).store()
        self.addCleanup(lambda: backend.groups.delete(g3.id))

        # I should find it
        g1copy = backend.groups.get(uuid=g1.uuid)
        self.assertEquals(g1.pk, g1copy.pk)

        # NOTE: Here we pass type_string='' to all query and get calls in the groups collection because
        # otherwise run the risk that we will pick up autogroups as well when really we're just interested
        # the the ones that we created in this test
        # Try queries
        res = backend.groups.query(nodes=n4, type_string='')
        self.assertListEqual([_.pk for _ in res], [])

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
        self.assertEquals(set(_.pk for _ in res), set(_.pk for _ in [g3]))

        # Same query, but using a string (the username=email) instead of
        # a DbUser object
        res = backend.groups.query(user=newuser.email, type_string='')
        self.assertEquals(set(_.pk for _ in res), set(_.pk for _ in [g3]))

        res = backend.groups.query(user=default_user, type_string='')
        self.assertEquals(set(_.pk for _ in res), set(_.pk for _ in [g1, g2]))

    def test_rename_existing(self):
        """
        Test that renaming to an already existing name is not permitted
        """
        backend = self.backend

        name_group_a = 'group_a'
        name_group_c = 'group_c'

        default_user = backend.users.create("{}@aiida.net".format(self.id())).store()

        group_a = backend.groups.create(name=name_group_a, description='I am the Original G', user=default_user).store()
        self.addCleanup(lambda: backend.groups.delete(group_a.id))

        # Before storing everything should be fine
        group_b = backend.groups.create(name=name_group_a, description='They will try to rename me', user=default_user)
        group_c = backend.groups.create(name=name_group_c, description='They will try to rename me', user=default_user)

        # Storing for duplicate group name should trigger UniquenessError
        with self.assertRaises(exceptions.IntegrityError):
            group_b.store()

        # Before storing everything should be fine
        group_c.name = name_group_a

        # Reverting to unique name before storing
        group_c.name = name_group_c
        group_c.store()
        self.addCleanup(lambda: backend.groups.delete(group_c.id))

        # After storing name change to existing should raise
        with self.assertRaises(exceptions.IntegrityError):
            group_c.name = name_group_a

    def test_creation_from_dbgroup(self):
        backend = self.backend

        n = Node().store()

        default_user = backend.users.create("{}@aiida.net".format(self.id())).store()

        g = backend.groups.create(name='testgroup_from_dbgroup', user=default_user).store()
        self.addCleanup(lambda: backend.groups.delete(g.id))

        g.store()
        g.add_nodes(n)

        dbgroup = g.dbmodel
        gcopy = backend.groups.from_dbmodel(dbgroup)

        self.assertEquals(g.pk, gcopy.pk)
        self.assertEquals(g.uuid, gcopy.uuid)


class TestDbExtrasDjango(AiidaTestCase):
    """
    Test DbAttributes.
    """

    def test_replacement_1(self):
        from aiida.backends.djsite.db.models import DbExtra

        n1 = Node().store()
        n2 = Node().store()

        DbExtra.set_value_for_node(n1._dbnode, "pippo", [1, 2, 'a'])
        DbExtra.set_value_for_node(n1._dbnode, "pippobis", [5, 6, 'c'])
        DbExtra.set_value_for_node(n2._dbnode, "pippo2", [3, 4, 'b'])

        self.assertEquals(n1.get_extras(), {'pippo': [1, 2, 'a'],
                                            'pippobis': [5, 6, 'c'],
                                            '_aiida_hash': n1.get_hash()
                                            })
        self.assertEquals(n2.get_extras(), {'pippo2': [3, 4, 'b'],
                                            '_aiida_hash': n2.get_hash()
                                            })

        new_attrs = {"newval1": "v", "newval2": [1, {"c": "d", "e": 2}]}

        DbExtra.reset_values_for_node(n1._dbnode, attributes=new_attrs)
        self.assertEquals(n1.get_extras(), new_attrs)
        self.assertEquals(n2.get_extras(), {'pippo2': [3, 4, 'b'], '_aiida_hash': n2.get_hash()})

        DbExtra.del_value_for_node(n1._dbnode, key='newval2')
        del new_attrs['newval2']
        self.assertEquals(n1.get_extras(), new_attrs)
        # Also check that other nodes were not damaged
        self.assertEquals(n2.get_extras(), {'pippo2': [3, 4, 'b'], '_aiida_hash': n2.get_hash()})
