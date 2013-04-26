"""
This file contains tests for AIDA.
They are executed when when you run "manage.py test" or
"manage.py test db" (much faster, tests only the 'db' app, i.e., only this file)
"""
from django.utils import unittest

from aida.node import Node
from aida.common.exceptions import ModificationNotAllowed

class TestQueryWithAidaObjects(unittest.TestCase):
    """
    Test if queries work properly also with aida.node.Node classes instead of
    aida.djsite.db.models.DbNode objects.
    """
    @classmethod
    def setUpClass(cls):
        import getpass
        from django.contrib.auth.models import User

        User.objects.create_user(getpass.getuser(), 'unknown@mail.com', 'fakepwd')

    @classmethod
    def tearDownClass(cls):
        import getpass
        from django.contrib.auth.models import User
        from django.core.exceptions import ObjectDoesNotExist

        try:
            User.objects.get(username=getpass.getuser).delete()
        except ObjectDoesNotExist:
            pass
        
    def test_queries(self):
        ## TODO: make a good test, not just random stuff!!

        from aida.djsite.db.models import DbNode, Link
        a  = Node().store()
        a2 = Node().store()
        a3 = Node().store()
        a4 = Node().store()        

        a.add_link_to(a2)
        a2.add_link_to(a3)
        a4.add_link_from(a2)
        a3.add_link_to(a4)

        b = Node.query(pk=a2)
        print '0>>>', b
        print '1>>>', Node.query(inputs__in=b)
        print '1b>>', DbNode.objects.filter(inputs__in=b)
        belem = b[0]
        print '2>>>', Node.query(inputs=belem)

        print '3>>>', Link.objects.filter(input=belem)


        print '4>>>', Node.query(attributes__key='_integer',
                                       attributes__ival=123)


class TestNodeBasic(unittest.TestCase):
    """
    These tests check the basic features of nodes (setting of attributes, copying of files, ...)
    """
    boolval = True
    intval = 123
    floatval = 4.56
    stringval = "aaaa"
    dictval = {'num': 3, 'something': 'else'}
    listval = [1, "s", True]

    @classmethod
    def setUpClass(cls):
        import getpass
        from django.contrib.auth.models import User

        User.objects.create_user(getpass.getuser(), 'unknown@mail.com', 'fakepwd')

    @classmethod
    def tearDownClass(cls):
        import getpass
        from django.contrib.auth.models import User
        from django.core.exceptions import ObjectDoesNotExist

        try:
            User.objects.get(username=getpass.getuser).delete()
        except ObjectDoesNotExist:
            pass

    def test_int_attr_before_storing(self):
        a = Node()
        a.set_internal_attr('bool', self.boolval)
        a.set_internal_attr('integer', self.intval)
        a.set_internal_attr('float', self.floatval)
        a.set_internal_attr('string', self.stringval)
        a.set_internal_attr('dict', self.dictval)
        a.set_internal_attr('list', self.listval)

        # Now I check if I can retrieve them, before the storage
        self.assertEquals(self.boolval, a.get_internal_attr('bool'))
        self.assertEquals(self.intval, a.get_internal_attr('integer'))
        self.assertEquals(self.floatval, a.get_internal_attr('float'))
        self.assertEquals(self.stringval, a.get_internal_attr('string'))
        self.assertEquals(self.dictval, a.get_internal_attr('dict'))
        self.assertEquals(self.listval, a.get_internal_attr('list'))

        # And now I try to delete the keys
        a.del_internal_attr('bool')
        a.del_internal_attr('integer')
        a.del_internal_attr('float')
        a.del_internal_attr('string')
        a.del_internal_attr('dict')
        a.del_internal_attr('list')

        with self.assertRaises(AttributeError):
            # I delete twice the same attribute
            a.del_internal_attr('bool')

        with self.assertRaises(AttributeError):
            # I delete a non-existing attribute
            a.del_internal_attr('nonexisting')

        with self.assertRaises(AttributeError):
            # I get a deleted attribute
            a.get_internal_attr('bool')

        with self.assertRaises(AttributeError):
            # I get a non-existing attribute
            a.get_internal_attr('nonexisting')
        

    def test_int_attr_after_storing(self):
        a = Node()
        a.set_internal_attr('bool', self.boolval)
        a.set_internal_attr('integer', self.intval)
        a.set_internal_attr('float', self.floatval)
        a.set_internal_attr('string', self.stringval)
        a.set_internal_attr('dict', self.dictval)
        a.set_internal_attr('list', self.listval)

        a.store()

        # Now I check if I can retrieve them, before the storage
        self.assertEquals(self.boolval, a.get_internal_attr('bool'))
        self.assertEquals(self.intval, a.get_internal_attr('integer'))
        self.assertEquals(self.floatval, a.get_internal_attr('float'))
        self.assertEquals(self.stringval, a.get_internal_attr('string'))
        self.assertEquals(self.dictval, a.get_internal_attr('dict'))
        self.assertEquals(self.listval, a.get_internal_attr('list'))

        # And now I try to edit/delete the keys; I should not be able to do it
        # after saving. I try only for a couple of attributes
        with self.assertRaises(ModificationNotAllowed):                
            a.del_internal_attr('bool')
        with self.assertRaises(ModificationNotAllowed):                
            a.set_internal_attr('integer',13)


    def test_int_attr_with_reload(self):
        a = Node()
        a.set_internal_attr('bool', self.boolval)
        a.set_internal_attr('integer', self.intval)
        a.set_internal_attr('float', self.floatval)
        a.set_internal_attr('string', self.stringval)
        a.set_internal_attr('dict', self.dictval)
        a.set_internal_attr('list', self.listval)

        a.store()

        b = Node(uuid=a.uuid)
        self.assertEquals(self.boolval, b.get_internal_attr('bool'))
        self.assertEquals(self.intval, b.get_internal_attr('integer'))
        self.assertEquals(self.floatval, b.get_internal_attr('float'))
        self.assertEquals(self.stringval, b.get_internal_attr('string'))
        self.assertEquals(self.dictval, b.get_internal_attr('dict'))
        self.assertEquals(self.listval, b.get_internal_attr('list'))

        with self.assertRaises(ModificationNotAllowed):                
            a.set_internal_attr('i',12)
        

     ## TO TEST:
     # create a copy, and recheck attrs, and modify them and check they don't change on original instance
     # check for files
     # Store internal and external attribute with same name
