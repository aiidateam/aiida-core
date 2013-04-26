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

    def test_get_inputs_and_outputs(self):
        a1 = Node().store()
        a2 = Node().store()        
        a3 = Node().store()
        a4 = Node().store()        

        a1.add_link_to(a2)
        a2.add_link_to(a3)
        a4.add_link_from(a2)
        a3.add_link_to(a4)

        # I check that I get the correct links
        self.assertEquals(set([n.uuid for n in a1.get_inputs()]),set([]))
        self.assertEquals(set([n.uuid for n in a1.get_outputs()]),set([a2.uuid]))

        self.assertEquals(set([n.uuid for n in a2.get_inputs()]),set([a1.uuid]))
        self.assertEquals(set([n.uuid for n in a2.get_outputs()]),set([a3.uuid, a4.uuid]))

        self.assertEquals(set([n.uuid for n in a3.get_inputs()]),set([a2.uuid]))
        self.assertEquals(set([n.uuid for n in a3.get_outputs()]),set([a4.uuid]))

        self.assertEquals(set([n.uuid for n in a4.get_inputs()]),set([a2.uuid, a3.uuid]))
        self.assertEquals(set([n.uuid for n in a4.get_outputs()]),set([]))
        
    def test_links_and_queries(self):
        from aida.djsite.db.models import DbNode, Link
        a  = Node()
        a.set_attr('myvalue', 123)
        a.store()
        
        a2 = Node().store()
        
        a3 = Node()
        a3.set_attr('myvalue', 145)
        a3.store()
        
        a4 = Node().store()        

        a.add_link_to(a2)
        a2.add_link_to(a3)
        a4.add_link_from(a2)
        a3.add_link_to(a4)

        b = Node.query(pk=a2)
        self.assertEquals(len(b), 1)
        # It is a aida.node.Node instance
        self.assertTrue(isinstance(b[0],Node))
        self.assertEquals(b[0].uuid, a2.uuid)
        
        going_out_from_a2 = Node.query(inputs__in=b)
        # Two nodes going out from a2
        self.assertEquals(len(going_out_from_a2), 2)
        self.assertTrue(isinstance(going_out_from_a2[0],Node))
        self.assertTrue(isinstance(going_out_from_a2[1],Node))
        uuid_set = set([going_out_from_a2[0].uuid, going_out_from_a2[1].uuid])

        # I check that I can query also directly the django DbNode
        # class passing a aida.node.Node entity
        
        going_out_from_a2_db = DbNode.objects.filter(inputs__in=b)
        self.assertEquals(len(going_out_from_a2_db), 2)
        self.assertTrue(isinstance(going_out_from_a2_db[0],DbNode))
        self.assertTrue(isinstance(going_out_from_a2_db[1],DbNode))
        uuid_set_db = set([going_out_from_a2_db[0].uuid, going_out_from_a2_db[1].uuid])

        # I check that doing the query with a Node or DbNode instance,
        # I get the same nodes
        self.assertEquals(uuid_set, uuid_set_db)

        # This time I don't use the __in filter, but I still pass a Node instance
        going_out_from_a2_bis = Node.query(inputs=b[0])
        self.assertEquals(len(going_out_from_a2_bis), 2)
        self.assertTrue(isinstance(going_out_from_a2_bis[0],Node))
        self.assertTrue(isinstance(going_out_from_a2_bis[1],Node))

        # Query for links starting from b[0]==a2 using again the Node class
        output_links_b = Link.objects.filter(input=b[0])
        self.assertEquals(len(output_links_b), 2)
        self.assertTrue(isinstance(output_links_b[0],Link))
        self.assertTrue(isinstance(output_links_b[1],Link))
        uuid_set_db_link = set([output_links_b[0].output.uuid, output_links_b[1].output.uuid])
        self.assertEquals(uuid_set, uuid_set_db_link)        
        

        # Query for related fields using django syntax
        # Note that being myvalue an attribute, it is internally stored starting
        # with an underscore
        nodes_with_given_attribute = Node.query(attributes__key='_myvalue',
                                                attributes__ival=145)
        # should be entry a3
        self.assertEquals(len(nodes_with_given_attribute), 1)
        self.assertTrue(isinstance(nodes_with_given_attribute[0],Node))
        self.assertEquals(nodes_with_given_attribute[0].uuid,a3.uuid)


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

    def test_attr_before_storing(self):
        a = Node()
        a.set_attr('k1', self.boolval)
        a.set_attr('k2', self.intval)
        a.set_attr('k3', self.floatval)
        a.set_attr('k4', self.stringval)
        a.set_attr('k5', self.dictval)
        a.set_attr('k6', self.listval)

        # Now I check if I can retrieve them, before the storage
        self.assertEquals(self.boolval,   a.get_attr('k1'))
        self.assertEquals(self.intval,    a.get_attr('k2'))
        self.assertEquals(self.floatval,  a.get_attr('k3'))
        self.assertEquals(self.stringval, a.get_attr('k4'))
        self.assertEquals(self.dictval,   a.get_attr('k5'))
        self.assertEquals(self.listval,   a.get_attr('k6'))

        # And now I try to delete the keys
        a.del_attr('k1')
        a.del_attr('k2')
        a.del_attr('k3')
        a.del_attr('k4')
        a.del_attr('k5')
        a.del_attr('k6')

        with self.assertRaises(AttributeError):
            # I delete twice the same attribute
            a.del_attr('k1')

        with self.assertRaises(AttributeError):
            # I delete a non-existing attribute
            a.del_attr('nonexisting')

        with self.assertRaises(AttributeError):
            # I get a deleted attribute
            a.get_attr('k1')

        with self.assertRaises(AttributeError):
            # I get a non-existing attribute
            a.get_attr('nonexisting')

    def test_attributes_on_copy(self):
        import copy
        
        a = Node()
        attrs_to_set = {
            'bool': self.boolval,
            'integer': self.intval,
            'float': self.floatval,
            'string': self.stringval,
            'dict': self.dictval,
            'list': self.listval,
            }

        for k,v in attrs_to_set.iteritems():
            a.set_attr(k, v)

        a.store()

        # I now set metadata
        metadata_to_set = {
            'bool': 'some non-boolean value',
            'some_other_name': 987}

        for k,v in metadata_to_set.iteritems():
            a.set_metadata(k, v)    

        # I make a copy
        b = a.copy()
        # I modify an attribute and add a new one; I mirror it in the dictionary
        # for later checking
        b_expected_attributes = copy.deepcopy(attrs_to_set)
        b.set_attr('integer', 489)
        b_expected_attributes['integer'] = 489
        b.set_attr('new', 'cvb')
        b_expected_attributes['new'] = 'cvb'

        # I check before storing that the attributes are ok
        self.assertEquals({k: v for k,v in b.iterattrs()}, b_expected_attributes)
        # Note that during copy, I do not copy the metadata!
        self.assertEquals({k: v for k,v in b.itermetadata()}, {})
        
        # I store now
        b.store()
        # and I finally add a metadata
        b.set_metadata('meta', 'textofext')
        b_expected_metadata = {'meta': 'textofext'}

        # Now I check for the attributes
        # First I check that nothing has changed 
        self.assertEquals({k: v for k,v in a.iterattrs()}, attrs_to_set)
        self.assertEquals({k: v for k,v in a.itermetadata()}, metadata_to_set)

        # I check then on the 'b' copy
        self.assertEquals({k: v for k,v in b.iterattrs()}, b_expected_attributes)
        self.assertEquals({k: v for k,v in b.itermetadata()}, b_expected_metadata)

    def test_files(self):
        import tempfile

        a = Node()

        file_content = 'some text ABCDE'
        file_content_different = 'other values 12345'

        with tempfile.NamedTemporaryFile() as f:
            f.write(file_content)
            f.flush()
            a.add_file(f.name,'file1.txt')
            a.add_file(f.name,'file2.txt')

        self.assertEquals(set(a.current_folder.get_file_list()),set(['file1.txt','file2.txt']))
        with open(a.current_folder.get_file_path('file1.txt')) as f:
            self.assertEquals(f.read(), file_content)
        with open(a.current_folder.get_file_path('file2.txt')) as f:
            self.assertEquals(f.read(), file_content)

        b = a.copy()
        self.assertNotEquals(a.uuid, b.uuid)

        # Check that the content is there
        self.assertEquals(set(b.current_folder.get_file_list()),set(['file1.txt','file2.txt']))
        with open(b.current_folder.get_file_path('file1.txt')) as f:
            self.assertEquals(f.read(), file_content)
        with open(b.current_folder.get_file_path('file2.txt')) as f:
            self.assertEquals(f.read(), file_content)

        # I overwrite a file and create a new one in the copy only
        with tempfile.NamedTemporaryFile() as f:
            f.write(file_content_different)
            f.flush()
            b.add_file(f.name,'file2.txt')       
            b.add_file(f.name,'file3.txt')

        # I check the new content, and that the old one has not changed
        self.assertEquals(set(a.current_folder.get_file_list()),set(['file1.txt','file2.txt']))
        with open(a.current_folder.get_file_path('file1.txt')) as f:
            self.assertEquals(f.read(), file_content)
        with open(a.current_folder.get_file_path('file2.txt')) as f:
            self.assertEquals(f.read(), file_content)
        self.assertEquals(set(b.current_folder.get_file_list()),
                          set(['file1.txt','file2.txt','file3.txt']))
        with open(b.current_folder.get_file_path('file1.txt')) as f:
            self.assertEquals(f.read(), file_content)
        with open(b.current_folder.get_file_path('file2.txt')) as f:
            self.assertEquals(f.read(), file_content_different)
        with open(b.current_folder.get_file_path('file3.txt')) as f:
            self.assertEquals(f.read(), file_content_different)

        # This should in principle change the location of the files, so I recheck
        a.store()

        # I now copy after storing
        c = a.copy()
        # I overwrite a file and create a new one in the copy only
        with tempfile.NamedTemporaryFile() as f:
            f.write(file_content_different)
            f.flush()
            c.add_file(f.name,'file1.txt')       
            c.add_file(f.name,'file4.txt')

        self.assertEquals(set(a.current_folder.get_file_list()),set(['file1.txt','file2.txt']))
        with open(a.current_folder.get_file_path('file1.txt')) as f:
            self.assertEquals(f.read(), file_content)
        with open(a.current_folder.get_file_path('file2.txt')) as f:
            self.assertEquals(f.read(), file_content)

        self.assertEquals(set(c.current_folder.get_file_list()),
                          set(['file1.txt','file2.txt','file4.txt']))
        with open(c.current_folder.get_file_path('file1.txt')) as f:
            self.assertEquals(f.read(), file_content_different)
        with open(c.current_folder.get_file_path('file2.txt')) as f:
            self.assertEquals(f.read(), file_content)
        with open(c.current_folder.get_file_path('file4.txt')) as f:
            self.assertEquals(f.read(), file_content_different)
        

    def test_attr_after_storing(self):
        a = Node()
        a.set_attr('bool', self.boolval)
        a.set_attr('integer', self.intval)
        a.set_attr('float', self.floatval)
        a.set_attr('string', self.stringval)
        a.set_attr('dict', self.dictval)
        a.set_attr('list', self.listval)

        a.store()

        # Now I check if I can retrieve them, before the storage
        self.assertEquals(self.boolval,   a.get_attr('bool'))
        self.assertEquals(self.intval,    a.get_attr('integer'))
        self.assertEquals(self.floatval,  a.get_attr('float'))
        self.assertEquals(self.stringval, a.get_attr('string'))
        self.assertEquals(self.dictval,   a.get_attr('dict'))
        self.assertEquals(self.listval,   a.get_attr('list'))

        # And now I try to edit/delete the keys; I should not be able to do it
        # after saving. I try only for a couple of attributes
        with self.assertRaises(ModificationNotAllowed):                
            a.del_attr('bool')
        with self.assertRaises(ModificationNotAllowed):                
            a.set_attr('integer',13)


    def test_attr_with_reload(self):
        a = Node()
        a.set_attr('bool', self.boolval)
        a.set_attr('integer', self.intval)
        a.set_attr('float', self.floatval)
        a.set_attr('string', self.stringval)
        a.set_attr('dict', self.dictval)
        a.set_attr('list', self.listval)

        a.store()

        b = Node(uuid=a.uuid)
        self.assertEquals(self.boolval,   b.get_attr('bool'))
        self.assertEquals(self.intval,    b.get_attr('integer'))
        self.assertEquals(self.floatval,  b.get_attr('float'))
        self.assertEquals(self.stringval, b.get_attr('string'))
        self.assertEquals(self.dictval,   b.get_attr('dict'))
        self.assertEquals(self.listval,   b.get_attr('list'))

        with self.assertRaises(ModificationNotAllowed):                
            a.set_attr('i',12)

    def test_attr_and_metadata(self):
        a = Node()
        a.set_attr('bool', self.boolval)
        a.set_attr('integer', self.intval)
        a.set_attr('float', self.floatval)
        a.set_attr('string', self.stringval)
        a.set_attr('dict', self.dictval)
        a.set_attr('list', self.listval)

        with self.assertRaises(ModificationNotAllowed):
            # I did not store, I cannot modify
            a.set_metadata('bool', 'blablabla')

        a.store()

        # I check that I cannot store a metadata with key starting with underscore
        with self.assertRaises(ValueError):
            a.set_metadata('_start_with_underscore', 'some text')

        a_string = 'some non-boolean value'
        # I now set
        a.set_metadata('bool', a_string)

        # I check that there is no name clash
        self.assertEquals(self.boolval, a.get_attr('bool'))
        self.assertEquals(a_string, a.get_metadata('bool'))
        
    def test_attr_listing(self):
        """
        Checks that the list of attributes and metadata is ok.
        """
        a = Node()
        attrs_to_set = {
            'bool': self.boolval,
            'integer': self.intval,
            'float': self.floatval,
            'string': self.stringval,
            'dict': self.dictval,
            'list': self.listval,
            }

        for k,v in attrs_to_set.iteritems():
            a.set_attr(k, v)

        a.store()

        # I now set metadata
        metadata_to_set = {
            'bool': 'some non-boolean value',
            'some_other_name': 987}

        for k,v in metadata_to_set.iteritems():
            a.set_metadata(k, v)        

        self.assertEquals(set(a.attrs()),
                          set(attrs_to_set.keys()))
        self.assertEquals(set(a.metadata()),
                          set(metadata_to_set.keys()))

        returned_internal_attrs = {k: v for k, v in a.iterattrs()}
        self.assertEquals(returned_internal_attrs, attrs_to_set)

        returned_attrs = {k: v for k, v in a.itermetadata()}
        self.assertEquals(returned_attrs, metadata_to_set)

