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

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.orm import Data


class TestComputer(AiidaTestCase):
    """
    Test the Computer class.
    """

    def test_deletion(self):
        from aiida.orm import CalcJobNode
        from aiida.common.exceptions import InvalidOperation

        newcomputer = orm.Computer(name="testdeletioncomputer", hostname='localhost',
                                   transport_type='local', scheduler_type='pbspro',
                                   workdir='/tmp/aiida').store()

        # # This should be possible, because nothing is using this computer
        orm.Computer.objects.delete(newcomputer.id)

        calc = CalcJobNode(computer=self.computer)
        calc.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        calc.store()

        # This should fail, because there is at least a calculation
        # using this computer (the one created just above)
        with self.assertRaises(InvalidOperation):
            orm.Computer.objects.delete(self.computer.id)


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

        g1 = backend.groups.create(label='testquery1', user=default_user).store()
        self.addCleanup(lambda: backend.groups.delete(g1.id))
        g2 = backend.groups.create(label='testquery2', user=default_user).store()
        self.addCleanup(lambda: backend.groups.delete(g2.id))

        n1 = Data().store().backend_entity
        n2 = Data().store().backend_entity
        n3 = Data().store().backend_entity
        n4 = Data().store().backend_entity

        g1.add_nodes([n1, n2])
        g2.add_nodes([n1, n3])

        newuser = backend.users.create(email='test@email.xx')
        g3 = backend.groups.create(label='testquery3', user=newuser).store()
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

    def test_creation_from_dbgroup(self):
        backend = self.backend

        n = Data().store()

        default_user = backend.users.create("{}@aiida.net".format(self.id())).store()

        g = backend.groups.create(label='testgroup_from_dbgroup', user=default_user).store()
        self.addCleanup(lambda: backend.groups.delete(g.id))

        g.store()
        g.add_nodes([n.backend_entity])

        dbgroup = g.dbmodel
        gcopy = backend.groups.from_dbmodel(dbgroup)

        self.assertEquals(g.pk, gcopy.pk)
        self.assertEquals(g.uuid, gcopy.uuid)


class TestDbExtrasDjango(AiidaTestCase):
    """Test DbAttributes."""

    def test_replacement_1(self):
        from aiida.backends.djsite.db.models import DbExtra

        n1 = Data().store()
        n2 = Data().store()

        DbExtra.set_value_for_node(n1.backend_entity.dbmodel, "pippo", [1, 2, 'a'])
        DbExtra.set_value_for_node(n1.backend_entity.dbmodel, "pippobis", [5, 6, 'c'])
        DbExtra.set_value_for_node(n2.backend_entity.dbmodel, "pippo2", [3, 4, 'b'])

        self.assertEquals(n1.extras, {'pippo': [1, 2, 'a'],
                                            'pippobis': [5, 6, 'c'],
                                            '_aiida_hash': n1.get_hash()
                                            })
        self.assertEquals(n2.extras, {'pippo2': [3, 4, 'b'],
                                            '_aiida_hash': n2.get_hash()
                                            })

        new_attrs = {"newval1": "v", "newval2": [1, {"c": "d", "e": 2}]}

        DbExtra.reset_values_for_node(n1.backend_entity.dbmodel, attributes=new_attrs)
        self.assertEquals(n1.extras, new_attrs)
        self.assertEquals(n2.extras, {'pippo2': [3, 4, 'b'], '_aiida_hash': n2.get_hash()})

        DbExtra.del_value_for_node(n1.backend_entity.dbmodel, key='newval2')
        del new_attrs['newval2']
        self.assertEquals(n1.extras, new_attrs)
        # Also check that other nodes were not damaged
        self.assertEquals(n2.extras, {'pippo2': [3, 4, 'b'], '_aiida_hash': n2.get_hash()})
