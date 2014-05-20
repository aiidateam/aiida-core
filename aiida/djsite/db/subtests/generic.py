"""
Generic tests that need the use of the DB
"""
from django.utils import unittest

from aiida.orm import Node
from aiida.common.exceptions import ModificationNotAllowed, UniquenessError
from aiida.djsite.db.testbase import AiidaTestCase

class TestComputer(AiidaTestCase):
    """
    Test the Computer class.
    """
    def test_deletion(self):
        from aiida.orm.computer import Computer, delete_computer
        from aiida.orm import Calculation
        from aiida.common.exceptions import InvalidOperation
    
        newcomputer = Computer(name="testdeletioncomputer", hostname='localhost',
                              transport_type='ssh',
                              scheduler_type='pbspro',
                              workdir='/tmp/aiida').store()

        # This should be possible, because nothing is using this computer
        delete_computer(newcomputer)
        
        calc_params = {
            'computer': self.computer,
            'resources': {'num_machines': 1,
            'num_mpiprocs_per_machine': 1}
            }
    
        _ = Calculation(**calc_params).store()
        # This should fail, because there is at least a calculation
        # using this computer (the one created just above)
        with self.assertRaises(InvalidOperation):
            delete_computer(self.computer)

class TestCode(AiidaTestCase):
    """
    Test the Code class.
    """            
    def test_code_local(self):
        import tempfile

        from aiida.orm import Code
        from aiida.common.exceptions import ValidationError

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
        self.assertTrue(code.get_local_executable(),'test.sh')
        self.assertTrue(code.get_execname(),'stest.sh')
                

    def test_remote(self):
        import tempfile

        from aiida.orm import Code, Computer
        from aiida.common.exceptions import ValidationError

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
                                 transport_type='ssh',
                                 scheduler_type='pbspro',
                                 workdir='/tmp/aiida').store()
        self.assertFalse(code.can_run_on(othercomputer))
        

class TestWfBasic(AiidaTestCase):
    """
    Tests for the workflows
    """
    def test_versioning_lowlevel(self):
        """
        Checks the versioning.
        """
        from aiida.workflows.test import WorkflowTestEmpty
        
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


class TestGroups(AiidaTestCase):
    """
    Test groups.
    """
    def test_creation(self):
        from aiida.orm import Group
        
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

    def test_creation_from_dbgroup(self):
        from aiida.orm import Group
        
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
        from aiida.orm import Group
                
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
        from aiida.orm import Group
        from aiida.common.exceptions import NotExistent
        
        n = Node().store()
                
        g = Group(name='testgroup3', description = 'some other desc')
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
