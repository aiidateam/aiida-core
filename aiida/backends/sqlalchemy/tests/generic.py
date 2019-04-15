# -*- coding: utf-8 -*-

import tempfile


from aiida.backends.utils import get_automatic_user
from aiida.backends.sqlalchemy.tests.base import SqlAlchemyTests
from aiida.backends.sqlalchemy.models.user import DbUser

from aiida.common.exceptions import (InvalidOperation, ValidationError,
                                     NotExistent, MultipleObjectsError,
                                     ModificationNotAllowed)

from aiida.orm import delete_computer, JobCalculation
from aiida.orm.computer import Computer
from aiida.orm.code import Code
from aiida.orm.group import Group
from aiida.orm.node import Node


from aiida.workflows.test import WorkflowTestEmpty



__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.0.1"

class TestComputer(SqlAlchemyTests):
    """
    Test the Computer class.
    """

    def test_deletion(self):
        newcomputer = Computer(name="testdeletioncomputer", hostname='localhost',
                               transport_type='local',
                               scheduler_type='pbspro',
                               workdir='/tmp/aiida').store()

        # This should be possible, because nothing is using this computer
        delete_computer(newcomputer)

        calc_params = {
            'computer': self.computer,
            'resources': {'num_machines': 1,
                          'num_mpiprocs_per_machine': 1}
        }

        _ = JobCalculation(**calc_params).store()
        # This should fail, because there is at least a calculation
        # using this computer (the one created just above)
        with self.assertRaises(InvalidOperation):
            delete_computer(self.computer)


class TestCode(SqlAlchemyTests):
    """
    Test the Code class.
    """

    def test_code_local(self):
        code = Code(local_executable='test.sh')
        with self.assertRaises(ValidationError):
            # No file with name test.sh
            code.store()

        with tempfile.NamedTemporaryFile() as f:
            f.write("#/bin/bash\n\necho test run\n")
            f.flush()
            code.add_path(f.name, 'test.sh')

        code.store()
        self.assertTrue(code.can_run_on(self.computer))
        self.assertTrue(code.get_local_executable(), 'test.sh')
        self.assertTrue(code.get_execname(), 'stest.sh')


    def test_remote(self):
        with self.assertRaises(ValueError):
            # remote_computer_exec has length 2 but is not a list or tuple
            _ = Code(remote_computer_exec='ab')

        # invalid code path
        with self.assertRaises(ValueError):
            _ = Code(remote_computer_exec=(self.computer, ''))

        # Relative path is invalid for remote code
        with self.assertRaises(ValueError):
            _ = Code(remote_computer_exec=(self.computer, 'subdir/run.exe'))

        # first argument should be a computer, not a string
        with self.assertRaises(TypeError):
            _ = Code(remote_computer_exec=('localhost', '/bin/ls'))

        code = Code(remote_computer_exec=(self.computer, '/bin/ls'))
        with tempfile.NamedTemporaryFile() as f:
            f.write("#/bin/bash\n\necho test run\n")
            f.flush()
            code.add_path(f.name, 'test.sh')

        with self.assertRaises(ValidationError):
            # There are files inside
            code.store()

        # If there are no files, I can store
        code.remove_path('test.sh')
        code.store()

        self.assertEquals(code.get_remote_computer().pk, self.computer.pk)
        self.assertEquals(code.get_remote_exec_path(), '/bin/ls')
        self.assertEquals(code.get_execname(), '/bin/ls')

        self.assertTrue(code.can_run_on(self.computer.dbcomputer))
        self.assertTrue(code.can_run_on(self.computer))
        othercomputer = Computer(name='another_localhost',
                                 hostname='localhost',
                                 transport_type='local',
                                 scheduler_type='pbspro',
                                 workdir='/tmp/aiida').store()
        self.assertFalse(code.can_run_on(othercomputer))


class TestWfBasic(SqlAlchemyTests):
    """
    Tests for the workflows
    """

    def test_versioning_lowlevel(self):
        """
        Checks the versioning.
        """
        w = WorkflowTestEmpty().store()

        # Even if I stored many attributes, this should stay at 1
        self.assertEquals(w._dbworkflowinstance.nodeversion, 1)
        self.assertEquals(w.dbworkflowinstance.nodeversion, 1)
        self.assertEquals(w._dbworkflowinstance.nodeversion, 1)

        w.label = "label1"
        w.label = "label2"
        self.assertEquals(w._dbworkflowinstance.nodeversion, 3)
        self.assertEquals(w.dbworkflowinstance.nodeversion, 3)
        self.assertEquals(w._dbworkflowinstance.nodeversion, 3)

        w.description = "desc1"
        w.description = "desc2"
        w.description = "desc3"
        self.assertEquals(w._dbworkflowinstance.nodeversion, 6)
        self.assertEquals(w.dbworkflowinstance.nodeversion, 6)
        self.assertEquals(w._dbworkflowinstance.nodeversion, 6)


class TestGroups(SqlAlchemyTests):
    """
    Test groups.
    """

    def test_creation(self):
        n = Node()
        stored_n = Node().store()

        with self.assertRaises(ValueError):
            # No name specified
            g = Group()

        g = Group(name='testgroup')

        with self.assertRaises(ValueError):
            # Too many parameters
            g = Group(name='testgroup', not_existing_kwarg=True)

        with self.assertRaises(ModificationNotAllowed):
            # g unstored
            g.add_nodes(n)

        with self.assertRaises(ModificationNotAllowed):
            # g unstored
            g.add_nodes(stored_n)

        g.store()

        with self.assertRaises(ValueError):
            # n unstored
            g.add_nodes(n)

        g.add_nodes(stored_n)

        nodes = list(g.nodes)
        self.assertEquals(len(nodes), 1)
        self.assertEquals(nodes[0].pk, stored_n.pk)

        # To avoid to find it in further tests
        g.delete()

    def test_description(self):
        """
        Test the update of the description both for stored and unstored
        groups.
        """
        n = Node().store()

        g1 = Group(name='testgroupdescription1', description="g1").store()
        g1.add_nodes(n)

        g2 = Group(name='testgroupdescription2', description="g2")

        # Preliminary checks
        self.assertTrue(g1.is_stored)
        self.assertFalse(g2.is_stored)
        self.assertEquals(g1.description, "g1")
        self.assertEquals(g2.description, "g2")

        # Change
        g1.description = "new1"
        g2.description = "new2"

        # Test that the groups remained in their proper stored state and that
        # the description was updated
        self.assertTrue(g1.is_stored)
        self.assertFalse(g2.is_stored)
        self.assertEquals(g1.description, "new1")
        self.assertEquals(g2.description, "new2")

        # Store g2 and check that the description is OK
        g2.store()
        self.assertTrue(g2.is_stored)
        self.assertEquals(g2.description, "new2")

        # clean-up
        g1.delete()
        g2.delete()

    def test_add_nodes(self):
        """
        Test different ways of adding nodes
        """
        n1 = Node().store()
        n2 = Node().store()
        n3 = Node().store()
        n4 = Node().store()
        n5 = Node().store()
        n6 = Node().store()
        n7 = Node().store()
        n8 = Node().store()

        g = Group(name='test_adding_nodes')
        g.store()
        # Single node
        g.add_nodes(n1)
        # List of nodes
        g.add_nodes([n2, n3])
        # Single DbNode
        g.add_nodes(n4.dbnode)
        # List of DbNodes
        g.add_nodes([n5.dbnode, n6.dbnode])
        # List of Nodes and DbNodes
        g.add_nodes([n7, n8.dbnode])

        # Check
        self.assertEquals(set([_.pk for _ in [n1, n2, n3, n4, n5, n6, n7, n8]]),
                          set([_.pk for _ in g.nodes]))

        # Try to add a node that is already present: there should be no problem
        g.add_nodes(n1)
        self.assertEquals(set([_.pk for _ in [n1, n2, n3, n4, n5, n6, n7, n8]]),
                          set([_.pk for _ in g.nodes]))

        # Cleanup
        g.delete()

    def test_remove_nodes(self):
        """
        Test node removal
        """
        n1 = Node().store()
        n2 = Node().store()
        n3 = Node().store()
        n4 = Node().store()
        n5 = Node().store()
        n6 = Node().store()
        n7 = Node().store()
        n8 = Node().store()
        n_out = Node().store()

        g = Group(name='test_remove_nodes').store()

        # Add initial nodes
        g.add_nodes([n1, n2, n3, n4, n5, n6, n7, n8])
        # Check
        self.assertEquals(set([_.pk for _ in [n1, n2, n3, n4, n5, n6, n7, n8]]),
                          set([_.pk for _ in g.nodes]))

        # Remove a node that is not in the group: nothing should happen
        # (same behavior of Django)
        g.remove_nodes(n_out)
        # Re-check
        self.assertEquals(set([_.pk for _ in [n1, n2, n3, n4, n5, n6, n7, n8]]),
                          set([_.pk for _ in g.nodes]))

        # Remove one Node and check
        g.remove_nodes(n4)
        self.assertEquals(set([_.pk for _ in [n1, n2, n3, n5, n6, n7, n8]]),
                          set([_.pk for _ in g.nodes]))
        # Remove one DbNode and check
        g.remove_nodes(n7.dbnode)
        self.assertEquals(set([_.pk for _ in [n1, n2, n3, n5, n6, n8]]),
                          set([_.pk for _ in g.nodes]))
        # Remove a list of Nodes and check
        g.remove_nodes([n1, n8])
        self.assertEquals(set([_.pk for _ in [n2, n3, n5, n6]]),
                          set([_.pk for _ in g.nodes]))
        # Remove a list of Nodes and check
        g.remove_nodes([n1, n8])
        self.assertEquals(set([_.pk for _ in [n2, n3, n5, n6]]),
                          set([_.pk for _ in g.nodes]))
        # Remove a list of DbNodes and check
        g.remove_nodes([n2.dbnode, n5.dbnode])
        self.assertEquals(set([_.pk for _ in [n3, n6]]),
                          set([_.pk for _ in g.nodes]))

        # Remove a mixed list of Nodes and DbNodes and check
        g.remove_nodes([n3, n6.dbnode])
        self.assertEquals(set(),
                          set([_.pk for _ in g.nodes]))

        # Cleanup
        g.delete()

    def test_creation_from_dbgroup(self):
        n = Node().store()

        g = Group(name='testgroup_from_dbgroup')
        g.store()
        g.add_nodes(n)

        dbgroup = g.dbgroup

        with self.assertRaises(ValueError):
            # Cannot pass more parameters, even if valid, if
            # dbgroup is specified
            Group(dbgroup=dbgroup, name="test")

        gcopy = Group(dbgroup=dbgroup)

        self.assertEquals(g.pk, gcopy.pk)
        self.assertEquals(g.uuid, gcopy.uuid)

        # To avoid to find it in further tests
        g.delete()

    def test_name_desc(self):
        g = Group(name='testgroup2', description='some desc')
        self.assertEquals(g.name, 'testgroup2')
        self.assertEquals(g.description, 'some desc')
        self.assertTrue(g.is_user_defined)
        g.store()
        # Same checks after storing
        self.assertEquals(g.name, 'testgroup2')
        self.assertTrue(g.is_user_defined)
        self.assertEquals(g.description, 'some desc')

        # To avoid to find it in further tests
        g.delete()

    def test_delete(self):
        n = Node().store()

        g = Group(name='testgroup3', description='some other desc')
        g.store()

        gcopy = Group.get(name='testgroup3')
        self.assertEquals(g.uuid, gcopy.uuid)

        g.add_nodes(n)
        self.assertEquals(len(g.nodes), 1)

        g.delete()

        with self.assertRaises(NotExistent):
            # The group does not exist anymore
            Group.get(name='testgroup3')

        # I should be able to restore it
        g.store()

        # Now, however, by deleting and recreating it, I lost the elements
        self.assertEquals(len(g.nodes), 0)
        self.assertEquals(g.name, 'testgroup3')
        self.assertEquals(g.description, 'some other desc')
        self.assertTrue(g.is_user_defined)

        # To avoid to find it in further tests
        g.delete()

    def test_query(self):
        """
        Test if queries are working
        """

        g1 = Group(name='testquery1').store()
        g2 = Group(name='testquery2').store()

        n1 = Node().store()
        n2 = Node().store()
        n3 = Node().store()
        n4 = Node().store()

        g1.add_nodes([n1, n2])
        g2.add_nodes([n1, n3])

        newuser = DbUser(email='test@email.xx', password='').save()
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


class TestDbExtras(SqlAlchemyTests):
    """
    Test extras attributes. This might not be really relevant anymmore with
    SqlA and JSONB attributes, and might need to be deleted/rewritten
    """

    def test_replacement_1(self):
        n1 = Node().store()
        n2 = Node().store()

        n1.dbnode.set_extra("pippo", [1, 2, 'a'])
        n1.dbnode.set_extra("pippobis", [5, 6, 'c'])
        n2.dbnode.set_extra("pippo2", [3, 4, 'b'])

        self.assertEquals(n1.dbnode.extras, {'pippo': [1, 2, 'a'],
                                             'pippobis': [5, 6, 'c']})
        self.assertEquals(n2.dbnode.extras, {'pippo2': [3, 4, 'b']})

        new_attrs = {"newval1": "v", "newval2": [1, {"c": "d", "e": 2}]}

        # Old way of doing. With SqlAlchemy, just set the dictionnary to a new
        # one and you're done
        # DbExtra.reset_values_for_node(n1.dbnode, attributes=new_attrs)
        n1.dbnode.extras = new_attrs
        self.assertEquals(n1.dbnode.extras, new_attrs)
        self.assertEquals(n2.dbnode.extras, {'pippo2': [3, 4, 'b']})

        n1.dbnode.del_extra('newval2')
        self.assertEquals(n1.dbnode.extras, new_attrs)
        # Also check that other nodes were not damaged
        self.assertEquals(n2.dbnode.extras, {'pippo2': [3, 4, 'b']})


