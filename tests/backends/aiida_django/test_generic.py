# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
Generic tests that need the use of the DB
"""

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.orm import Data


class TestComputer(AiidaTestCase):
    """Test the Computer class."""

    def test_deletion(self):
        """Test computer deletion."""
        from aiida.orm import CalcJobNode, Computer
        from aiida.common.exceptions import InvalidOperation

        newcomputer = Computer(
            name='testdeletioncomputer',
            hostname='localhost',
            transport_type='local',
            scheduler_type='pbspro',
            workdir='/tmp/aiida'
        ).store()

        # This should be possible, because nothing is using this computer
        orm.Computer.objects.delete(newcomputer.id)

        calc = CalcJobNode(computer=self.computer)
        calc.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        calc.store()

        # This should fail, because there is at least a calculation
        # using this computer (the one created just above)
        with self.assertRaises(InvalidOperation):
            orm.Computer.objects.delete(self.computer.id)  # pylint: disable=no-member


class TestGroupsDjango(AiidaTestCase):
    """Test groups."""

    # Tests that are specific to the Django backend
    def test_query(self):
        """
        Test if queries are working
        """
        from aiida.common.exceptions import NotExistent, MultipleObjectsError

        backend = self.backend

        default_user = backend.users.create('{}@aiida.net'.format(self.id())).store()

        g_1 = backend.groups.create(label='testquery1', user=default_user).store()
        self.addCleanup(lambda: backend.groups.delete(g_1.id))
        g_2 = backend.groups.create(label='testquery2', user=default_user).store()
        self.addCleanup(lambda: backend.groups.delete(g_2.id))

        n_1 = Data().store().backend_entity
        n_2 = Data().store().backend_entity
        n_3 = Data().store().backend_entity
        n_4 = Data().store().backend_entity

        g_1.add_nodes([n_1, n_2])
        g_2.add_nodes([n_1, n_3])

        newuser = backend.users.create(email='test@email.xx')
        g_3 = backend.groups.create(label='testquery3', user=newuser).store()
        self.addCleanup(lambda: backend.groups.delete(g_3.id))

        # I should find it
        g_1copy = backend.groups.get(uuid=g_1.uuid)
        self.assertEqual(g_1.pk, g_1copy.pk)

        # NOTE: Here we pass type_string='' to all query and get calls in the groups collection because
        # otherwise run the risk that we will pick up autogroups as well when really we're just interested
        # the the ones that we created in this test
        # Try queries
        res = backend.groups.query(nodes=n_4, type_string='')
        self.assertListEqual([_.pk for _ in res], [])

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
        self.assertEqual(set(_.pk for _ in res), set(_.pk for _ in [g_3]))

        # Same query, but using a string (the username=email) instead of
        # a DbUser object
        res = backend.groups.query(user=newuser.email, type_string='')
        self.assertEqual(set(_.pk for _ in res), set(_.pk for _ in [g_3]))

        res = backend.groups.query(user=default_user, type_string='')
        self.assertEqual(set(_.pk for _ in res), set(_.pk for _ in [g_1, g_2]))

    def test_creation_from_dbgroup(self):
        """Test creation of a group from another group."""
        backend = self.backend

        node = Data().store()

        default_user = backend.users.create('{}@aiida.net'.format(self.id())).store()

        grp = backend.groups.create(label='testgroup_from_dbgroup', user=default_user).store()
        self.addCleanup(lambda: backend.groups.delete(grp.id))

        grp.store()
        grp.add_nodes([node.backend_entity])

        dbgroup = grp.dbmodel
        gcopy = backend.groups.from_dbmodel(dbgroup)

        self.assertEqual(grp.pk, gcopy.pk)
        self.assertEqual(grp.uuid, gcopy.uuid)
