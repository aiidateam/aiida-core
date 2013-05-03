"""
This file contains tests for AIDA.
They are executed when when you run "manage.py test" or
"manage.py test db" (much faster, tests only the 'db' app, i.e., only this file)
"""
from django.utils import unittest

from aida.orm import Node
from aida.common.exceptions import ModificationNotAllowed

class TransitiveClosure(unittest.TestCase):
    """
    Test the creation of the transitive closure table
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

    def test_creation_and_deletion(self):
        from aida.djsite.db.models import Link # Direct links
        from aida.djsite.db.models import Path # The transitive closure table
        
        n1 = Node().store()
        n2 = Node().store()
        n3 = Node().store()
        n4 = Node().store()
        n5 = Node().store()
        n6 = Node().store()
        n7 = Node().store()
        n8 = Node().store()        
        n9 = Node().store()

        # I create a strange graph, inserting links in a order
        # such that I often have to create the transitive closure
        # between two graphs
        n2.add_link_to(n3)
        n1.add_link_to(n2)
        n3.add_link_to(n5)
        n4.add_link_to(n5)
        n2.add_link_to(n4)


        n6.add_link_to(n7)
        n7.add_link_to(n8)

        # Yet, no links from 1 to 8
        self.assertEquals(len(Path.objects.filter(parent=n1,child=n8).distinct()),0)

        n5.add_link_to(n6)
        # Yet, now 2 links from 1 to 8
        self.assertEquals(len(Path.objects.filter(parent=n1,child=n8).distinct()),2)

        n9.add_link_to(n7)
        # Still two links...
        self.assertEquals(len(Path.objects.filter(parent=n1,child=n8).distinct()),2)

        n6.add_link_to(n9)
        # And now there should be 4 nodes
        self.assertEquals(len(Path.objects.filter(parent=n1,child=n8).distinct()),4)
        
        ### I start deleting now

        # I cut one branch below: I should loose 2 links
        Link.objects.filter(input=n6, output=n9).delete()
        self.assertEquals(len(Path.objects.filter(parent=n1,child=n8).distinct()),2)

        # I cut another branch above: I should loose one more link
        Link.objects.filter(input=n2, output=n4).delete()
        self.assertEquals(len(Path.objects.filter(parent=n1,child=n8).distinct()),1)
        
        # Another cut should delete all links
        Link.objects.filter(input=n3, output=n5).delete()
        self.assertEquals(len(Path.objects.filter(parent=n1,child=n8).distinct()),0)

        # But I did not delete everything! For instance, I can check the following links
        self.assertEquals(len(Path.objects.filter(parent=n4,child=n8).distinct()),1)
        self.assertEquals(len(Path.objects.filter(parent=n5,child=n7).distinct()),1)

        # Finally, I reconnect in a different way the two graphs and check that 1 and
        # 8 are again connected
        n3.add_link_to(n4)
        self.assertEquals(len(Path.objects.filter(parent=n1,child=n8).distinct()),1)          

class TestQueryWithAidaObjects(unittest.TestCase):
    """
    Test if queries work properly also with aida.orm.Node classes instead of
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
        # It is a aida.orm.Node instance
        self.assertTrue(isinstance(b[0],Node))
        self.assertEquals(b[0].uuid, a2.uuid)
        
        going_out_from_a2 = Node.query(inputs__in=b)
        # Two nodes going out from a2
        self.assertEquals(len(going_out_from_a2), 2)
        self.assertTrue(isinstance(going_out_from_a2[0],Node))
        self.assertTrue(isinstance(going_out_from_a2[1],Node))
        uuid_set = set([going_out_from_a2[0].uuid, going_out_from_a2[1].uuid])

        # I check that I can query also directly the django DbNode
        # class passing a aida.orm.Node entity
        
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

        cls.user = User.objects.create_user(getpass.getuser(), 'unknown@mail.com', 'fakepwd')

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

    def test_datetime_attribute(self):
        import datetime
        from django.utils.timezone import make_aware, get_current_timezone, is_naive

        a = Node()

        date = datetime.datetime.now()

        a.set_attr('some_date', date)
        a.store()

        retrieved = a.get_attr('some_date')

        if is_naive(date):
            date_to_compare = make_aware(date, get_current_timezone())
        else:
            date_to_compare = date

        self.assertEquals(date_to_compare,retrieved)


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

        self.assertEquals(set(a.get_file_list()),set(['file1.txt','file2.txt']))
        with open(a.get_file_path('file1.txt')) as f:
            self.assertEquals(f.read(), file_content)
        with open(a.get_file_path('file2.txt')) as f:
            self.assertEquals(f.read(), file_content)

        b = a.copy()
        self.assertNotEquals(a.uuid, b.uuid)

        # Check that the content is there
        self.assertEquals(set(b.get_file_list()),set(['file1.txt','file2.txt']))
        with open(b.get_file_path('file1.txt')) as f:
            self.assertEquals(f.read(), file_content)
        with open(b.get_file_path('file2.txt')) as f:
            self.assertEquals(f.read(), file_content)

        # I overwrite a file and create a new one in the copy only
        with tempfile.NamedTemporaryFile() as f:
            f.write(file_content_different)
            f.flush()
            b.add_file(f.name,'file2.txt')       
            b.add_file(f.name,'file3.txt')

        # I check the new content, and that the old one has not changed
        self.assertEquals(set(a.get_file_list()),set(['file1.txt','file2.txt']))
        with open(a.get_file_path('file1.txt')) as f:
            self.assertEquals(f.read(), file_content)
        with open(a.get_file_path('file2.txt')) as f:
            self.assertEquals(f.read(), file_content)
        self.assertEquals(set(b.get_file_list()),
                          set(['file1.txt','file2.txt','file3.txt']))
        with open(b.get_file_path('file1.txt')) as f:
            self.assertEquals(f.read(), file_content)
        with open(b.get_file_path('file2.txt')) as f:
            self.assertEquals(f.read(), file_content_different)
        with open(b.get_file_path('file3.txt')) as f:
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

        self.assertEquals(set(a.get_file_list()),set(['file1.txt','file2.txt']))
        with open(a.get_file_path('file1.txt')) as f:
            self.assertEquals(f.read(), file_content)
        with open(a.get_file_path('file2.txt')) as f:
            self.assertEquals(f.read(), file_content)

        self.assertEquals(set(c.get_file_list()),
                          set(['file1.txt','file2.txt','file4.txt']))
        with open(c.get_file_path('file1.txt')) as f:
            self.assertEquals(f.read(), file_content_different)
        with open(c.get_file_path('file2.txt')) as f:
            self.assertEquals(f.read(), file_content)
        with open(c.get_file_path('file4.txt')) as f:
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


    def test_versioning_and_postsave_attributes(self):
        """
        Checks the versioning.
        """
        class myNodeWithFields(Node):
            # State can be updated even after storing
            _updatable_attributes = ('state',) 
        
        a = myNodeWithFields()
        attrs_to_set = {
            'bool': self.boolval,
            'integer': self.intval,
            'float': self.floatval,
            'string': self.stringval,
            'dict': self.dictval,
            'list': self.listval,
            'state': 267,
            }

        for k,v in attrs_to_set.iteritems():
            a.set_attr(k, v)
            
        # Check before storing
        self.assertEquals(267,a.get_attr('state'))

        a.store()

        # Check after storing
        self.assertEquals(267,a.get_attr('state'))        

        # Even if I stored many attributes, this should stay at 1
        self.assertEquals(a.dbnode.nodeversion, 1)
        self.assertEquals(a.dbnode.lastsyncedversion, 0)

        # I check increment on new version
        a.set_metadata('a', 'b')
        self.assertEquals(a.dbnode.nodeversion, 2)

        # I check that I can set this attribute
        a.set_attr('state', 999)

        # I check increment on new version
        self.assertEquals(a.dbnode.nodeversion, 3)

        with self.assertRaises(ModificationNotAllowed):
            # I check that I cannot modify this attribute
            a.set_attr('otherattribute', 222)

        # I check that the counter was not incremented
        self.assertEquals(a.dbnode.nodeversion, 3)

        b = a.copy()
        # updatable attributes are not copied
        with self.assertRaises(AttributeError):
            b.get_attr('state')

    def test_comments(self):
        # This is the best way to compare dates with the stored ones, instead of
        # directly loading datetime.datetime.now(), or you can get a
        # "can't compare offset-naive and offset-aware datetimes" error
        from django.utils import timezone
        import time

        a = Node()
        with self.assertRaises(ModificationNotAllowed):
            a.add_comment('text')
        self.assertEquals(a.get_comments(),[])
        a.store()
        before = timezone.now()
        time.sleep(1) # I wait 1 second because MySql time precision is 1 sec
        a.add_comment('text')
        a.add_comment('text2')        
        time.sleep(1)
        after = timezone.now()

        comments = a.get_comments()
        
        times = [i[2] for i in comments]
        for time in times:
            self.assertTrue(time > before)
            self.assertTrue(time < after )

        self.assertEquals([(i[0], i[1], i[3]) for i in comments],
                          [(self.user.username, self.user.email, 'text'),
                           (self.user.username, self.user.email, 'text2'),])
        
        
class TestSubNodes(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        import getpass
        from django.contrib.auth.models import User
        from aida.orm import Computer

        User.objects.create_user(getpass.getuser(), 'unknown@mail.com', 'fakepwd')
        cls.computer = Computer(hostname='localhost',
                                transport_type='ssh',
                                scheduler_type='pbspro',
                                workdir='/tmp/aida')
        cls.computer.store()

    @classmethod
    def tearDownClass(cls):
        import getpass
        from django.contrib.auth.models import User
        from django.core.exceptions import ObjectDoesNotExist
        from aida.djsite.db.models import DbComputer

        try:
            User.objects.get(username=getpass.getuser).delete()
        except ObjectDoesNotExist:
            pass

        DbComputer.objects.filter().delete()

    def test_set_code(self):
        from aida.orm import Node, Calculation, Data, Code
        from aida.orm import Computer
        from aida.common.pluginloader import load_plugin
        from aida.djsite.db.models import DbComputer
        
        code = Code(remote_machine_exec=('localhost','/bin/true'),
                    input_plugin='simple_plugins.template_replacer')#.store()
        
        computer = self.computer

        unstoredcalc = Calculation(computer=computer,
                           num_nodes=1,num_cpus_per_node=1)
        calc = Calculation(computer=computer,
                           num_nodes=1,num_cpus_per_node=1).store()
        # calc is not stored, and code is not (can't add links to node)
        with self.assertRaises(ModificationNotAllowed):
            unstoredcalc.set_code(code)

        # calc is stored, but code is not
        with self.assertRaises(ModificationNotAllowed):
            calc.set_code(code)

        # calc is not stored, but code is
        code.store()        
        with self.assertRaises(ModificationNotAllowed):
            unstoredcalc.set_code(code)

        # code and calc are stored
        calc.set_code(code)
        

    def test_links_label_constraints(self):
        from aida.orm import Node

        n1 = Node().store()
        n2 = Node().store()
        n3 = Node().store()
        n4 = Node().store()
        n5 = Node().store()

        n3.add_link_from(n1, label='label1')
        # This should be allowed since it is an output label with the same name
        n3.add_link_to(n4, label='label1')

        # An input link with that name already exists
        with self.assertRaises(ValueError):
            n3.add_link_from(n2, label='label1')

        # instead, for outputs, I can have multiple times the same label
        # (think to the case where n3 is a StructureData, and both n4 and n5
        #  are calculations that use as label 'input_cell')
        n3.add_link_to(n5, label='label1')


    def test_links_label_autogenerator(self):
        from django.db import transaction

        from aida.orm import Node

        n1 = Node().store()
        n2 = Node().store()
        n3 = Node().store()
        n4 = Node().store()
        n5 = Node().store()
        n6 = Node().store()
        n7 = Node().store()
        n8 = Node().store()
        n9 = Node().store()
        n10 = Node().store()


        n10.add_link_from(n1)
        # Label should be automatically generated
        n10.add_link_from(n2)
        n10.add_link_from(n3)
        n10.add_link_from(n4)
        n10.add_link_from(n5)
        n10.add_link_from(n6)
        n10.add_link_from(n7)
        n10.add_link_from(n8)
        n10.add_link_from(n9)
    
    def test_valid_links(self):
        import tempfile

        from aida.orm import Node, Calculation, Data, Code
        from aida.orm import Computer
        from aida.common.pluginloader import load_plugin
        from aida.djsite.db.models import DbComputer

        FileData = load_plugin(Data, 'aida.orm.dataplugins', 'file')

        # I create some objects
        d1 = Data().store()
        with tempfile.NamedTemporaryFile() as f:
            d2 = FileData(f.name).store()

        code = Code(remote_machine_exec=('localhost','/bin/true'),
                    input_plugin='simple_plugins.template_replacer').store()

        unsavedcomputer = Computer(dbcomputer=DbComputer(hostname='localhost'))

        with self.assertRaises(ValueError):
            # I need to save the localhost entry first
            calc = Calculation(computer=unsavedcomputer,
                num_nodes=1,num_cpus_per_node=1).store()

        # I check both with a string or with an object
        calc = Calculation(computer=self.computer,
            num_nodes=1,num_cpus_per_node=1).store()
        calc2 = Calculation(computer='localhost',
            num_nodes=1,num_cpus_per_node=1).store()
        with self.assertRaises(TypeError):
            # I don't want to call it with things that are neither
            # strings nor Computer instances
            calc3 = Calculation(computer=1,
                num_nodes=1,num_cpus_per_node=1).store()
        
        d1.add_link_to(calc)
        calc.add_link_from(d2)
        calc.add_link_from(code)

        # Cannot link to itself
        with self.assertRaises(ValueError):
            d1.add_link_to(d1)

        # I try to add wrong links (data to data, calc to calc, etc.)
        with self.assertRaises(ValueError):
            d1.add_link_to(d2)

        with self.assertRaises(ValueError):
            d1.add_link_from(d2)

        with self.assertRaises(ValueError):
            d1.add_link_from(code)

        with self.assertRaises(ValueError):
            code.add_link_from(d1)

        with self.assertRaises(ValueError):
            calc.add_link_from(calc2)

        calc_a = Calculation(computer=self.computer,
            num_nodes=1,num_cpus_per_node=1).store()
        calc_b = Calculation(computer=self.computer,
            num_nodes=1,num_cpus_per_node=1).store()

        data_node = Data().store()

        data_node.add_link_from(calc_a)
        # A data cannot have to input calculations
        with self.assertRaises(ValueError):
            data_node.add_link_from(calc_b)

        calculation_inputs = calc.get_inputs()
        inputs_type_data = [i for i in calculation_inputs if isinstance(i,Data)]
        inputs_type_code = [i for i in calculation_inputs if isinstance(i,Code)]

        # This calculation has three inputs (2 data and one code)
        self.assertEquals(len(calculation_inputs), 3)
        self.assertEquals(len(inputs_type_data), 2)
        self.assertEquals(len(inputs_type_code), 1)
        
    def test_check_single_calc_source(self):
        """
        Each data node can only have one input calculation
        """
        from aida.orm import Node, Calculation, Data, Code
        
        d1 = Data().store()
        
        calc = Calculation(computer=self.computer,
            num_nodes=1,num_cpus_per_node=1).store()
        calc2 = Calculation(computer=self.computer,
            num_nodes=1,num_cpus_per_node=1).store()

        d1.add_link_from(calc)

        with self.assertRaises(ValueError):
            d1.add_link_from(calc2)

class TestCode(unittest.TestCase):
    """
    Test the FileData class.
    """    
    @classmethod
    def setUpClass(cls):
        import getpass
        from django.contrib.auth.models import User
        from aida.orm import Computer

        User.objects.create_user(getpass.getuser(), 'unknown@mail.com', 'fakepwd')
        cls.computer = Computer(hostname='localhost',
                                transport_type='ssh',
                                scheduler_type='pbspro',
                                workdir='/tmp/aida')
        cls.computer.store()

    @classmethod
    def tearDownClass(cls):
        import getpass
        from django.contrib.auth.models import User
        from django.core.exceptions import ObjectDoesNotExist
        from aida.djsite.db.models import DbComputer

        try:
            User.objects.get(username=getpass.getuser).delete()
        except ObjectDoesNotExist:
            pass

        DbComputer.objects.filter().delete()
        
        
    def test_code_local(self):
        import tempfile

        from aida.orm import Code
        from aida.common.exceptions import ValidationError

        code = Code(local_executable='test.sh',
                    input_plugin='simple_plugins.template_replacer')
        with self.assertRaises(ValidationError):
            # No file with name test.sh
            code.store()

        with tempfile.NamedTemporaryFile() as f:
            f.write("#/bin/bash\n\necho test run\n")
            f.flush()
            code.add_file(f.name, 'test.sh')

        code.store()
        self.assertTrue(code.can_run_on(self.computer))
        self.assertTrue(code.get_local_executable(),'test.sh')
        self.assertTrue(code.get_execname(),'stest.sh')
                

    def test_remote(self):
        import tempfile

        from aida.orm import Code
        from aida.common.exceptions import ValidationError

        with self.assertRaises(ValueError):
            # remote_machine_exec has length 2 but is not a list or tuple
            code = Code(remote_machine_exec='ab',
                        input_plugin='simple_plugins.template_replacer')

        # invalid code path
        with self.assertRaises(ValueError):
            code = Code(remote_machine_exec=('localhost', ''),
                        input_plugin='simple_plugins.template_replacer')

        # Relative path is invalid for remote code
        with self.assertRaises(ValueError):
            code = Code(remote_machine_exec=('localhost', 'subdir/run.exe'),
                        input_plugin='simple_plugins.template_replacer')

        # No input plugin specified
        with self.assertRaises(ValueError):
            code = Code(remote_machine_exec=('localhost', 'subdir/run.exe'))
        
        code = Code(remote_machine_exec=('localhost', '/bin/ls'),
                    input_plugin='simple_plugins.template_replacer')
        with tempfile.NamedTemporaryFile() as f:
            f.write("#/bin/bash\n\necho test run\n")
            f.flush()
            code.add_file(f.name, 'test.sh')

        with self.assertRaises(ValidationError):
            # There are files inside
            code.store()

        # If there are no files, I can store
        code.remove_file('test.sh')
        code.store()

        self.assertEquals(code.get_remote_machine(), 'localhost')
        self.assertEquals(code.get_remote_executable(), '/bin/ls')
        self.assertEquals(code.get_execname(), '/bin/ls')

        self.assertTrue(code.can_run_on('localhost')) 
        self.assertTrue(code.can_run_on(self.computer))         
        self.assertFalse(code.can_run_on('another.computer.com'))
        
class TestFileData(unittest.TestCase):
    """
    Test the FileData class.
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
        
    def test_reload(self):
        import os
        import tempfile

        from aida.orm.dataplugins.file import FileData

        # Or, equivalently:
        #        from aida.orm import Data
        #        from aida.common.pluginloader import load_plugin        
        #        FileData = load_plugin(Data,'aida.orm.dataplugins','file')

        file_content = 'some text ABCDE'
        with tempfile.NamedTemporaryFile() as f:
            filename = f.name
            basename = os.path.split(filename)[1]
            f.write(file_content)
            f.flush()
            a = FileData(filename)

        the_uuid = a.uuid

        self.assertEquals(a.get_file_list(),[basename])

        with open(a.get_file_path(basename)) as f:
            self.assertEquals(f.read(), file_content)

        a.store()

        with open(a.get_file_path(basename)) as f:
            self.assertEquals(f.read(), file_content)
        self.assertEquals(a.get_file_list(),[basename])

        b = Node.get_subclass_from_uuid(the_uuid)

        # I check the retrieved object
        self.assertTrue(isinstance(b,FileData))
        self.assertEquals(b.get_file_list(),[basename])
        with open(b.get_file_path(basename)) as f:
            self.assertEquals(f.read(), file_content)

