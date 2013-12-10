"""
Generic tests that need the use of the DB
"""
from django.utils import unittest

from aiida.orm import Node
from aiida.common.exceptions import ModificationNotAllowed, UniquenessError
from aiida.djsite.db.testbase import AiidaTestCase

class TestTransitiveNoLoops(AiidaTestCase):
    """
    Test the creation of the transitive closure table
    """
    def test_loop_not_allowed(self):
        n1 = Node().store()
        n2 = Node().store()
        n3 = Node().store()
        n4 = Node().store()

        n1.add_link_to(n2)
        n2.add_link_to(n3)
        n3.add_link_to(n4)

        with self.assertRaises(ValueError): # This would generate a loop
            n4.add_link_to(n1)

class TestTransitiveClosureDeletion(AiidaTestCase):
    """
    Test the creation of the transitive closure table
    """
    def test_creation_and_deletion(self):
        from aiida.djsite.db.models import Link # Direct links
        from aiida.djsite.db.models import Path # The transitive closure table
        
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
        self.assertEquals(
            len(Path.objects.filter(parent=n1,child=n8).distinct()),0)

        n5.add_link_to(n6)
        # Yet, now 2 links from 1 to 8
        self.assertEquals(
            len(Path.objects.filter(parent=n1,child=n8).distinct()),2)

        n9.add_link_to(n7)
        # Still two links...
        self.assertEquals(
            len(Path.objects.filter(parent=n1,child=n8).distinct()),2)

        n6.add_link_to(n9)
        # And now there should be 4 nodes
        self.assertEquals(
            len(Path.objects.filter(parent=n1,child=n8).distinct()),4)
        
        ### I start deleting now

        # I cut one branch below: I should loose 2 links
        Link.objects.filter(input=n6, output=n9).delete()
        self.assertEquals(
            len(Path.objects.filter(parent=n1,child=n8).distinct()),2)

        #print "\n".join([str((i.pk, i.input.pk, i.output.pk))
        #                 for i in Link.objects.filter()])
        #print "\n".join([str((i.pk, i.parent.pk, i.child.pk, i.depth,
        #                      i.entry_edge_id, i.direct_edge_id,
        #                      i.exit_edge_id)) for i in Path.objects.filter()])

        # I cut another branch above: I should loose one more link
        Link.objects.filter(input=n2, output=n4).delete()
        #print "\n".join([str((i.pk, i.input.pk, i.output.pk))
        #                 for i in Link.objects.filter()])
        #print "\n".join([str((i.pk, i.parent.pk, i.child.pk, i.depth,
        #                      i.entry_edge_id, i.direct_edge_id,
        #                      i.exit_edge_id)) for i in Path.objects.filter()])
        self.assertEquals(
            len(Path.objects.filter(parent=n1,child=n8).distinct()),1)
        
        # Another cut should delete all links
        Link.objects.filter(input=n3, output=n5).delete()
        self.assertEquals(
            len(Path.objects.filter(parent=n1,child=n8).distinct()),0)

        # But I did not delete everything! For instance, I can check
        # the following links
        self.assertEquals(
            len(Path.objects.filter(parent=n4,child=n8).distinct()),1)
        self.assertEquals(
            len(Path.objects.filter(parent=n5,child=n7).distinct()),1)

        # Finally, I reconnect in a different way the two graphs and 
        # check that 1 and 8 are again connected
        n3.add_link_to(n4)
        self.assertEquals(
            len(Path.objects.filter(parent=n1,child=n8).distinct()),1)          

class TestQueryWithAiidaObjects(AiidaTestCase):
    """
    Test if queries work properly also with aiida.orm.Node classes instead of
    aiida.djsite.db.models.DbNode objects.
    """
    def test_with_subclasses(self):
        from aiida.orm import Calculation, CalculationFactory, Data, DataFactory
        
        attribute_name = self.__class__.__name__ + ".test_with_subclasses"
        calc_params = {
            'computer': self.computer,
            'resources': {'num_machines': 1,
            'num_cpus_per_machine': 1}
            }
        
        TemplateReplacerCalc = CalculationFactory('simpleplugins.templatereplacer')
        ParameterData = DataFactory('parameter')
        
        a1 = Calculation(**calc_params).store()
        # To query only these nodes later
        a1.set_metadata(attribute_name, True)
        a2 = TemplateReplacerCalc(**calc_params).store()
        # To query only these nodes later
        a2.set_metadata(attribute_name, True)
        a3 = Data().store()        
        a3.set_metadata(attribute_name, True)
        a4 = ParameterData({'a':'b'}).store()        
        a4.set_metadata(attribute_name, True)
        a5 = Node().store()
        a5.set_metadata(attribute_name, True)
        # I don't set the metadata, just to be sure that the filtering works
        # The filtering is needed because other tests will put stuff int he DB
        a6 = Calculation(**calc_params)
        a6.store()
        a7 = Node()
        a7.store()

        # Query by calculation
        results = list(Calculation.query(attributes__key=attribute_name))
        # a3, a4, a5 should not be found because they are not Calculations.
        # a6, a7 should not be found because they have not the attribute set.
        self.assertEquals(set([i.pk for i in results]),
                          set([a1.pk, a2.pk]))        
        
        # Same query, but by the generic Node class
        results = list(Node.query(attributes__key=attribute_name))
        self.assertEquals(set([i.pk for i in results]),
                          set([a1.pk, a2.pk, a3.pk, a4.pk, a5.pk]))
        
        # Same query, but by the Data class
        results = list(Data.query(attributes__key=attribute_name))
        self.assertEquals(set([i.pk for i in results]),
                          set([a3.pk, a4.pk]))
        
        # Same query, but by the ParameterData subclass
        results = list(ParameterData.query(attributes__key=attribute_name))
        self.assertEquals(set([i.pk for i in results]),
                          set([a4.pk]))
        
        # Same query, but by the TemplateReplacerCalc subclass
        results = list(TemplateReplacerCalc.query(attributes__key=attribute_name))
        self.assertEquals(set([i.pk for i in results]),
                          set([a2.pk]))

    
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
        self.assertEquals(set([n.uuid for n in a1.get_inputs()]),
                          set([]))
        self.assertEquals(set([n.uuid for n in a1.get_outputs()]),
                          set([a2.uuid]))

        self.assertEquals(set([n.uuid for n in a2.get_inputs()]),
                          set([a1.uuid]))
        self.assertEquals(set([n.uuid for n in a2.get_outputs()]),
                          set([a3.uuid, a4.uuid]))

        self.assertEquals(set([n.uuid for n in a3.get_inputs()]),
                          set([a2.uuid]))
        self.assertEquals(set([n.uuid for n in a3.get_outputs()]),
                          set([a4.uuid]))

        self.assertEquals(set([n.uuid for n in a4.get_inputs()]),
                          set([a2.uuid, a3.uuid]))
        self.assertEquals(set([n.uuid for n in a4.get_outputs()]),
                          set([]))
        
    def test_links_and_queries(self):
        from aiida.djsite.db.models import DbNode, Link
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
        # It is a aiida.orm.Node instance
        self.assertTrue(isinstance(b[0],Node))
        self.assertEquals(b[0].uuid, a2.uuid)
        
        going_out_from_a2 = Node.query(inputs__in=b)
        # Two nodes going out from a2
        self.assertEquals(len(going_out_from_a2), 2)
        self.assertTrue(isinstance(going_out_from_a2[0],Node))
        self.assertTrue(isinstance(going_out_from_a2[1],Node))
        uuid_set = set([going_out_from_a2[0].uuid, going_out_from_a2[1].uuid])

        # I check that I can query also directly the django DbNode
        # class passing a aiida.orm.Node entity
        
        going_out_from_a2_db = DbNode.objects.filter(inputs__in=b)
        self.assertEquals(len(going_out_from_a2_db), 2)
        self.assertTrue(isinstance(going_out_from_a2_db[0],DbNode))
        self.assertTrue(isinstance(going_out_from_a2_db[1],DbNode))
        uuid_set_db = set([going_out_from_a2_db[0].uuid,
                           going_out_from_a2_db[1].uuid])

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
        uuid_set_db_link = set([output_links_b[0].output.uuid,
                                output_links_b[1].output.uuid])
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


class TestNodeBasic(AiidaTestCase):
    """
    These tests check the basic features of nodes
    (setting of attributes, copying of files, ...)
    """
    boolval = True
    intval = 123
    floatval = 4.56
    stringval = "aaaa"
    # A recursive dictionary
    dictval = {'num': 3, 'something': 'else', 'emptydict': {},
               'recursive': {'a': 1, 'b': True, 'c': 1.2, 'd': [1,2], 
                             'e': {'z': 'z', 'xx': {}, 'yy': []}}}
    listval = [1, "s", True]
    emptydict = {}
    emptylist = []

    def test_attr_before_storing(self):
        a = Node()
        a.set_attr('k1', self.boolval)
        a.set_attr('k2', self.intval)
        a.set_attr('k3', self.floatval)
        a.set_attr('k4', self.stringval)
        a.set_attr('k5', self.dictval)
        a.set_attr('k6', self.listval)
        a.set_attr('k7', self.emptydict)
        a.set_attr('k8', self.emptylist)

        # Now I check if I can retrieve them, before the storage
        self.assertEquals(self.boolval,   a.get_attr('k1'))
        self.assertEquals(self.intval,    a.get_attr('k2'))
        self.assertEquals(self.floatval,  a.get_attr('k3'))
        self.assertEquals(self.stringval, a.get_attr('k4'))
        self.assertEquals(self.dictval,   a.get_attr('k5'))
        self.assertEquals(self.listval,   a.get_attr('k6'))
        self.assertEquals(self.emptydict, a.get_attr('k7'))
        self.assertEquals(self.emptylist, a.get_attr('k8'))

        # And now I try to delete the keys
        a.del_attr('k1')
        a.del_attr('k2')
        a.del_attr('k3')
        a.del_attr('k4')
        a.del_attr('k5')
        a.del_attr('k6')
        a.del_attr('k7')
        a.del_attr('k8')

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
        from django.utils.timezone import (
            get_current_timezone, is_naive, make_aware)

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
            'emptydict': {},
            'emptylist': [],
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
        self.assertEquals({k: v for k,v in b.iterattrs()},
                          b_expected_attributes)
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
        self.assertEquals({k: v for k,v in b.iterattrs()},
                          b_expected_attributes)
        self.assertEquals({k: v for k,v in b.itermetadata()},
                          b_expected_metadata)

    def test_files(self):
        import tempfile

        a = Node()

        file_content = 'some text ABCDE'
        file_content_different = 'other values 12345'

        with tempfile.NamedTemporaryFile() as f:
            f.write(file_content)
            f.flush()
            a.add_path(f.name,'file1.txt')
            a.add_path(f.name,'file2.txt')

        self.assertEquals(set(a.get_path_list()),set(['file1.txt','file2.txt']))
        with open(a.get_abs_path('file1.txt')) as f:
            self.assertEquals(f.read(), file_content)
        with open(a.get_abs_path('file2.txt')) as f:
            self.assertEquals(f.read(), file_content)

        b = a.copy()
        self.assertNotEquals(a.uuid, b.uuid)

        # Check that the content is there
        self.assertEquals(set(b.get_path_list()),set(['file1.txt','file2.txt']))
        with open(b.get_abs_path('file1.txt')) as f:
            self.assertEquals(f.read(), file_content)
        with open(b.get_abs_path('file2.txt')) as f:
            self.assertEquals(f.read(), file_content)

        # I overwrite a file and create a new one in the copy only
        with tempfile.NamedTemporaryFile() as f:
            f.write(file_content_different)
            f.flush()
            b.add_path(f.name,'file2.txt')       
            b.add_path(f.name,'file3.txt')

        # I check the new content, and that the old one has not changed
        self.assertEquals(set(a.get_path_list()),set(['file1.txt','file2.txt']))
        with open(a.get_abs_path('file1.txt')) as f:
            self.assertEquals(f.read(), file_content)
        with open(a.get_abs_path('file2.txt')) as f:
            self.assertEquals(f.read(), file_content)
        self.assertEquals(set(b.get_path_list()),
                          set(['file1.txt','file2.txt','file3.txt']))
        with open(b.get_abs_path('file1.txt')) as f:
            self.assertEquals(f.read(), file_content)
        with open(b.get_abs_path('file2.txt')) as f:
            self.assertEquals(f.read(), file_content_different)
        with open(b.get_abs_path('file3.txt')) as f:
            self.assertEquals(f.read(), file_content_different)

        # This should in principle change the location of the files,
        # so I recheck
        a.store()

        # I now copy after storing
        c = a.copy()
        # I overwrite a file and create a new one in the copy only
        with tempfile.NamedTemporaryFile() as f:
            f.write(file_content_different)
            f.flush()
            c.add_path(f.name,'file1.txt')       
            c.add_path(f.name,'file4.txt')

        self.assertEquals(set(a.get_path_list()),set(['file1.txt','file2.txt']))
        with open(a.get_abs_path('file1.txt')) as f:
            self.assertEquals(f.read(), file_content)
        with open(a.get_abs_path('file2.txt')) as f:
            self.assertEquals(f.read(), file_content)

        self.assertEquals(set(c.get_path_list()),
                          set(['file1.txt','file2.txt','file4.txt']))
        with open(c.get_abs_path('file1.txt')) as f:
            self.assertEquals(f.read(), file_content_different)
        with open(c.get_abs_path('file2.txt')) as f:
            self.assertEquals(f.read(), file_content)
        with open(c.get_abs_path('file4.txt')) as f:
            self.assertEquals(f.read(), file_content_different)


    def test_folders(self):
        """
        Similar as test_files, but I manipulate a tree of folders
        """
        import tempfile
        import os,shutil
        import random,string
        
        a = Node()

        # Since Node uses the same method of Folder(),
        # for this test I create a test folder by hand
        # For any non-test usage, use SandboxFolder()!

        directory = os.path.realpath( os.path.join('/','tmp','tmp_try') )
        while os.path.exists( os.path.join(directory) ):
            # I append a random letter/number until it is unique
            directory += random.choice(
                string.ascii_uppercase + string.digits)
        
        # create a folder structure to copy around
        tree_1 = os.path.join(directory,'tree_1')
        os.makedirs(tree_1)
        file_content = 'some text ABCDE'
        file_content_different = 'other values 12345'
        with open(os.path.join(tree_1,'file1.txt'),'w') as f:
            f.write(file_content)
        os.mkdir( os.path.join(tree_1,'dir1') )
        os.mkdir( os.path.join(tree_1,'dir1','dir2') )
        with open(os.path.join(tree_1,'dir1','file2.txt'),'w') as f:
            f.write(file_content)
        os.mkdir( os.path.join(tree_1,'dir1','dir2','dir3') )

        # add the tree to the node
        
        a.add_path(tree_1,'tree_1')

        # verify if the node has the structure I expect
        self.assertEquals(set(a.get_path_list()),set(['tree_1']))
        self.assertEquals( set( a.get_path_list('tree_1') ),
                           set(['file1.txt','dir1']) )
        self.assertEquals( set( a.get_path_list(os.path.join('tree_1','dir1'))),
                           set(['dir2','file2.txt']) )
        with open(a.get_abs_path( os.path.join('tree_1','file1.txt') )) as f:
            self.assertEquals(f.read(), file_content)
        with open(a.get_abs_path(
                    os.path.join('tree_1','dir1','file2.txt') )) as f:
            self.assertEquals(f.read(), file_content)

        # try to exit from the folder
        with self.assertRaises(ValueError):
            a.get_path_list('..')

        # copy into a new node
        b = a.copy()
        self.assertNotEquals(a.uuid, b.uuid)

        # Check that the content is there
        self.assertEquals(set(b.get_path_list('.')),set(['tree_1']))
        self.assertEquals( set(b.get_path_list('tree_1')),
                           set(['file1.txt','dir1']) )
        self.assertEquals( set(b.get_path_list(os.path.join('tree_1','dir1'))),
                           set(['dir2','file2.txt']) )
        with open(b.get_abs_path( os.path.join('tree_1','file1.txt') )) as f:
            self.assertEquals(f.read(), file_content)
        with open(b.get_abs_path(os.path.join(
                    'tree_1','dir1','file2.txt'))) as f:
            self.assertEquals(f.read(), file_content)

        # I overwrite a file and create a new one in the copy only
        dir3 = os.path.join(directory,'dir3')
        os.mkdir( dir3 )

        b.add_path( dir3 , os.path.join('tree_1','dir3') )
        # no absolute path here
        with self.assertRaises(ValueError):
            b.add_path( 'dir3' , os.path.join('tree_1','dir3') )
        
        with tempfile.NamedTemporaryFile() as f:
            f.write(file_content_different)
            f.flush()
            b.add_path(f.name,'file3.txt')

        # I check the new content, and that the old one has not changed
        # old
        self.assertEquals(set(a.get_path_list('.')),set(['tree_1']))
        self.assertEquals( set( a.get_path_list('tree_1') ),
                           set(['file1.txt','dir1']) )
        self.assertEquals( set( a.get_path_list(os.path.join('tree_1','dir1'))),
                           set(['dir2','file2.txt']) )
        with open(a.get_abs_path( os.path.join('tree_1','file1.txt') )) as f:
            self.assertEquals(f.read(), file_content)
        with open(a.get_abs_path( os.path.join(
                'tree_1','dir1','file2.txt') )) as f:
            self.assertEquals(f.read(), file_content)
        #new
        self.assertEquals(set(b.get_path_list('.')),
                          set(['tree_1','file3.txt']))
        self.assertEquals( set( b.get_path_list('tree_1') ),
                           set(['file1.txt','dir1','dir3']) )
        self.assertEquals( set( b.get_path_list(os.path.join('tree_1','dir1'))),
                           set(['dir2','file2.txt']) )
        with open(b.get_abs_path( os.path.join('tree_1','file1.txt') )) as f:
            self.assertEquals(f.read(), file_content)
        with open(b.get_abs_path( os.path.join(
                'tree_1','dir1','file2.txt') )) as f:
            self.assertEquals(f.read(), file_content)

        # This should in principle change the location of the files,
        # so I recheck
        a.store()

        # I now copy after storing
        c = a.copy()
        # I overwrite a file, create a new one and remove a directory
        # in the copy only
        with tempfile.NamedTemporaryFile() as f:
            f.write(file_content_different)
            f.flush()
            c.add_path( f.name , os.path.join('tree_1','file1.txt') )
            c.add_path( f.name , os.path.join('tree_1','dir1','file4.txt') )
        c.remove_path( os.path.join('tree_1','dir1','dir2') )

        # check old
        self.assertEquals(set(a.get_path_list('.')),set(['tree_1']))
        self.assertEquals( set( a.get_path_list('tree_1') ),
                           set(['file1.txt','dir1']) )
        self.assertEquals( set(a.get_path_list( os.path.join('tree_1','dir1'))),
                           set(['dir2','file2.txt']) )
        with open(a.get_abs_path( os.path.join('tree_1','file1.txt') )) as f:
            self.assertEquals(f.read(), file_content)
        with open(a.get_abs_path( os.path.join(
                'tree_1','dir1','file2.txt') )) as f:
            self.assertEquals(f.read(), file_content)

        # check new
        self.assertEquals( set( c.get_path_list('.')),set(['tree_1']))
        self.assertEquals( set( c.get_path_list('tree_1') ),
                           set(['file1.txt','dir1']) )
        self.assertEquals( set( c.get_path_list(os.path.join('tree_1','dir1'))),
                           set(['file2.txt','file4.txt']) )
        with open(c.get_abs_path( os.path.join('tree_1','file1.txt') )) as f:
            self.assertEquals(f.read(), file_content_different)
        with open(c.get_abs_path( os.path.join(
                'tree_1','dir1','file2.txt') )) as f:
            self.assertEquals(f.read(), file_content)

        # garbage cleaning
        shutil.rmtree(directory)


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
        from aiida.orm.test import myNodeWithFields
        
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

        # In both cases, the node version must increase
        a.label = 'test'
        self.assertEquals(a.dbnode.nodeversion, 4)

        a.description = 'test description'
        self.assertEquals(a.dbnode.nodeversion, 5)


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
        
        
class TestSubNodesAndLinks(AiidaTestCase):
    def test_use_code(self):
        from aiida.orm import Calculation, Code

        computer = self.computer
        
        code = Code(remote_computer_exec=(computer, '/bin/true'))#.store()
        
        unstoredcalc = Calculation(computer=computer,
                                   resources={'num_machines': 1, 'num_cpus_per_machine': 1})
        calc = Calculation(computer=computer,
                           resources={'num_machines': 1, 'num_cpus_per_machine': 1}).store()
        # calc is not stored, and code is not (can't add links to node)
        with self.assertRaises(ModificationNotAllowed):
            unstoredcalc.use_code(code)

        # calc is stored, but code is not
        with self.assertRaises(ModificationNotAllowed):
            calc.use_code(code)

        # calc is not stored, but code is
        code.store()        
        with self.assertRaises(ModificationNotAllowed):
            unstoredcalc.use_code(code)

        # code and calc are stored
        calc.use_code(code) 

    def test_links_label_constraints(self):
        n1 = Node().store()
        n2 = Node().store()
        n3 = Node().store()
        n4 = Node().store()
        n5 = Node().store()

        n3.add_link_from(n1, label='label1')
        # This should be allowed since it is an output label with the same name
        n3.add_link_to(n4, label='label1')

        # An input link with that name already exists
        with self.assertRaises(UniquenessError):
            n3.add_link_from(n2, label='label1')

        # instead, for outputs, I can have multiple times the same label
        # (think to the case where n3 is a StructureData, and both n4 and n5
        #  are calculations that use as label 'input_cell')
        n3.add_link_to(n5, label='label1')

    def test_links_label_autogenerator(self):
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
  
    def test_link_replace(self):
        n1 = Node().store()
        n2 = Node().store()
        n3 = Node().store()
        
        n3.add_link_from(n1,label='the_label')
        with self.assertRaises(UniquenessError):
            # A link with the same name already exists
            n3.add_link_from(n1,label='the_label')
        
        # I can replace the link and check that it was replaced
        n3.replace_link_from(n2, label='the_label')
        the_parent = dict(n3.get_inputs(also_labels=True))['the_label']
        self.assertEquals(n2.uuid, the_parent.uuid)
        
        # replace_link_from should work also if there is no previous link 
        n2 .replace_link_from(n1, label='the_label_2')
        the_parent = dict(n2.get_inputs(also_labels=True))['the_label_2']
        self.assertEquals(n1.uuid, the_parent.uuid)
        
    
    def test_valid_links(self):
        import tempfile

        from aiida.orm import Calculation, Data, Code
        from aiida.orm import Computer, DataFactory
        from aiida.common.datastructures import calc_states

        SinglefileData = DataFactory('singlefile')

        # I create some objects
        d1 = Data().store()
        with tempfile.NamedTemporaryFile() as f:
            d2 = SinglefileData(f.name).store()

        code = Code(remote_computer_exec=(self.computer,'/bin/true')).store()

        unsavedcomputer = Computer(name='localhost2', hostname='localhost')

        with self.assertRaises(ValueError):
            # I need to save the localhost entry first
            _ = Calculation(computer=unsavedcomputer,
                            resources={'num_machines': 1, 'num_cpus_per_machine': 1}).store()

        # I check both with a string or with an object
        calc = Calculation(computer=self.computer,
                           resources={'num_machines': 1, 'num_cpus_per_machine': 1}).store()
        calc2 = Calculation(computer='localhost',
                            resources={'num_machines': 1, 'num_cpus_per_machine': 1}).store()
        with self.assertRaises(TypeError):
            # I don't want to call it with things that are neither
            # strings nor Computer instances
            _ = Calculation(computer=1,
                            resources={'num_machines': 1, 'num_cpus_per_machine': 1}).store()
        
        d1.add_link_to(calc)
        calc.add_link_from(d2,label='some_label')
        calc.use_code(code)

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
                             resources={'num_machines':1,'num_cpus_per_machine':1}).store()
        calc_b = Calculation(computer=self.computer,
                             resources={'num_machines':1,'num_cpus_per_machine':1}).store()

        data_node = Data().store()

        # I do a trick to set it to a state that allows writing
        calc_a._set_state(calc_states.RETRIEVING) 
        calc_b._set_state(calc_states.RETRIEVING) 

        data_node.add_link_from(calc_a)
        # A data cannot have two input calculations
        with self.assertRaises(ValueError):
            data_node.add_link_from(calc_b)

        newdata = Data()
        # Cannot add an input link if the calculation is not in status NEW
        with self.assertRaises(ModificationNotAllowed):
            calc_a.add_link_from(newdata)

        # Cannot replace input nodes if the calculation is not in status NEW    
        with self.assertRaises(ModificationNotAllowed):
            calc_a.replace_link_from(d2, label='some_label')

        # Cannot (re)set the code if the calculation is not in status NEW
        with self.assertRaises(ModificationNotAllowed):
            calc_a.use_code(code)
        

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
        from aiida.orm import Calculation, Data
        from aiida.common.datastructures import calc_states

        d1 = Data().store()
        
        calc = Calculation(computer=self.computer,
                           resources={'num_machines':1,'num_cpus_per_machine':1}).store()
        calc2 = Calculation(computer=self.computer,
                            resources={'num_machines':1,'num_cpus_per_machine':1}).store()

        # I cannot, calc it is in state NEW
        with self.assertRaises(ModificationNotAllowed):
            d1.add_link_from(calc)

        # I do a trick to set it to a state that allows setting the link
        calc._set_state(calc_states.RETRIEVING) 
        calc2._set_state(calc_states.RETRIEVING) 

        d1.add_link_from(calc)

        # more than on input to the same data object!
        with self.assertRaises(ValueError):
            d1.add_link_from(calc2)

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
            'num_cpus_per_machine': 1}
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
        
class TestSinglefileData(AiidaTestCase):
    """
    Test the SinglefileData class.
    """    
    def test_reload_singlefiledata(self):
        import os
        import tempfile

        from aiida.orm.data.singlefile import SinglefileData


        file_content = 'some text ABCDE'
        with tempfile.NamedTemporaryFile() as f:
            filename = f.name
            basename = os.path.split(filename)[1]
            f.write(file_content)
            f.flush()
            a = SinglefileData(filename)

        the_uuid = a.uuid

        self.assertEquals(a.get_path_list(),[basename])

        with open(a.get_abs_path(basename)) as f:
            self.assertEquals(f.read(), file_content)

        a.store()

        with open(a.get_abs_path(basename)) as f:
            self.assertEquals(f.read(), file_content)
        self.assertEquals(a.get_path_list(),[basename])

        b = Node.get_subclass_from_uuid(the_uuid)

        # I check the retrieved object
        self.assertTrue(isinstance(b,SinglefileData))
        self.assertEquals(b.get_path_list(),[basename])
        with open(b.get_abs_path(basename)) as f:
            self.assertEquals(f.read(), file_content)

class TestKindValidSymbols(AiidaTestCase):
    """
    Tests the symbol validation of the
    aiida.orm.data.structure.Kind class.
    """
    def test_bad_symbol(self):
        """
        Should not accept a non-existing symbol.
        """
        from aiida.orm.data.structure import Kind

        with self.assertRaises(ValueError):
            _ = Kind(symbols='Hxx')
    
    def test_empty_list_symbols(self):
        """
        Should not accept an empty list
        """
        from aiida.orm.data.structure import Kind

        with self.assertRaises(ValueError):
            _ = Kind(symbols=[])
    
    def test_valid_list(self):
        """
        Should not raise any error.
        """
        from aiida.orm.data.structure import Kind

        _ = Kind(symbols=['H','He'],weights=[0.5,0.5])

class TestSiteValidWeights(AiidaTestCase):
    """
    Tests valid weight lists.
    """        
    def test_isnot_list(self):
        """
        Should not accept a non-list, non-number weight
        """
        from aiida.orm.data.structure import Kind

        with self.assertRaises(ValueError):
            _ = Kind(symbols='Ba',weights='aaa')
    
    def test_empty_list_weights(self):
        """
        Should not accept an empty list
        """
        from aiida.orm.data.structure import Kind

        with self.assertRaises(ValueError):
            _ = Kind(symbols='Ba',weights=[])

    def test_symbol_weight_mismatch(self):
        """
        Should not accept a size mismatch of the symbols and weights
        list.
        """
        from aiida.orm.data.structure import Kind

        with self.assertRaises(ValueError):
            _ = Kind(symbols=['Ba','C'],weights=[1.])

        with self.assertRaises(ValueError):
            _ = Kind(symbols=['Ba'],weights=[0.1,0.2])

    def test_negative_value(self):
        """
        Should not accept a negative weight
        """
        from aiida.orm.data.structure import Kind

        with self.assertRaises(ValueError):
            _ = Kind(symbols=['Ba','C'],weights=[-0.1,0.3])

    def test_sum_greater_one(self):
        """
        Should not accept a sum of weights larger than one
        """
        from aiida.orm.data.structure import Kind

        with self.assertRaises(ValueError):
            _ = Kind(symbols=['Ba','C'],
                     weights=[0.5,0.6])

    def test_sum_one_weights(self):
        """
        Should accept a sum equal to one
        """
        from aiida.orm.data.structure import Kind

        _ = Kind(symbols=['Ba','C'],
                 weights=[1./3.,2./3.])

    def test_sum_less_one_weights(self):
        """
        Should accept a sum equal less than one
        """
        from aiida.orm.data.structure import Kind

        _ = Kind(symbols=['Ba','C'],
                 weights=[1./3.,1./3.])
    
    def test_none(self):
        """
        Should accept None.
        """
        from aiida.orm.data.structure import Kind

        _ = Kind(symbols='Ba',weights=None)


class TestKindTestGeneral(AiidaTestCase):
    """
    Tests the creation of Kind objects and their methods.
    """
    def test_sum_one_general(self):
        """
        Should accept a sum equal to one
        """
        from aiida.orm.data.structure import Kind

        a = Kind(symbols=['Ba','C'],
                 weights=[1./3.,2./3.])
        self.assertTrue(a.is_alloy())
        self.assertFalse(a.has_vacancies())

    def test_sum_less_one_general(self):
        """
        Should accept a sum equal less than one
        """
        from aiida.orm.data.structure import Kind

        a = Kind(symbols=['Ba','C'],
                 weights=[1./3.,1./3.])
        self.assertTrue(a.is_alloy())
        self.assertTrue(a.has_vacancies())

    def test_no_position(self):
        """
        Should not accept a 'positions' parameter
        """
        from aiida.orm.data.structure import Kind

        with self.assertRaises(ValueError):
            _ = Kind(position=[0.,0.,0.],symbols=['Ba'],
                     weights=[1.])
    
    def test_simple(self):
        """
        Should recognize a simple element.
        """
        from aiida.orm.data.structure import Kind

        a = Kind(symbols='Ba')
        self.assertFalse(a.is_alloy())
        self.assertFalse(a.has_vacancies())

        b = Kind(symbols='Ba',weights=1.)
        self.assertFalse(b.is_alloy())
        self.assertFalse(b.has_vacancies())

        c = Kind(symbols='Ba',weights=None)
        self.assertFalse(c.is_alloy())
        self.assertFalse(c.has_vacancies())


    def test_automatic_name(self):
        """
        Check the automatic name generator.
        """
        from aiida.orm.data.structure import Kind

        a = Kind(symbols='Ba')
        self.assertEqual(a.name,'Ba')

        a = Kind(symbols=('Si','Ge'),weights=(1./3.,2./3.))
        self.assertEqual(a.name,'GeSi')

        a = Kind(symbols=('Si','Ge'),weights=(0.4,0.5))
        self.assertEqual(a.name,'GeSiX')
        
        # Manually setting the name of the species
        a.name = 'newstring'
        self.assertEqual(a.name,'newstring')

class TestKindTestMasses(AiidaTestCase):
    """
    Tests the management of masses during the creation of Kind objects.
    """
    def test_auto_mass_one(self):
        """
        mass for elements with sum one
        """
        from aiida.orm.data.structure import Kind, _atomic_masses

        a = Kind(symbols=['Ba','C'],
                          weights=[1./3.,2./3.])
        self.assertAlmostEqual(a.mass, 
                               (_atomic_masses['Ba'] + 
                                2.* _atomic_masses['C'])/3.)

    def test_sum_less_one_masses(self):
        """
        mass for elements with sum less than one
        """
        from aiida.orm.data.structure import Kind, _atomic_masses

        a = Kind(symbols=['Ba','C'],
                 weights=[1./3.,1./3.])
        self.assertAlmostEqual(a.mass, 
                               (_atomic_masses['Ba'] + 
                                _atomic_masses['C'])/2.)

    def test_sum_less_one_singleelem(self):
        """
        mass for a single element
        """
        from aiida.orm.data.structure import Kind, _atomic_masses

        a = Kind(symbols=['Ba'])
        self.assertAlmostEqual(a.mass, 
                               _atomic_masses['Ba'])
        
    def test_manual_mass(self):
        """
        mass set manually
        """
        from aiida.orm.data.structure import Kind

        a = Kind(symbols=['Ba','C'],
                 weights=[1./3.,1./3.],
                 mass = 1000.)
        self.assertAlmostEqual(a.mass, 1000.)

class TestStructureDataInit(AiidaTestCase):
    """
    Tests the creation of StructureData objects (cell and pbc).
    """
    def test_cell_wrong_size_1(self):
        """
        Wrong cell size (not 3x3)
        """
        from aiida.orm.data.structure import StructureData

        with self.assertRaises(ValueError):
            _ = StructureData(cell=((1.,2.,3.),))

    def test_cell_wrong_size_2(self):
        """
        Wrong cell size (not 3x3)
        """
        from aiida.orm.data.structure import StructureData

        with self.assertRaises(ValueError):
            _ = StructureData(cell=((1.,0.,0.),(0.,0.,3.),(0.,3.)))

    def test_cell_zero_vector(self):
        """
        Wrong cell (one vector has zero length)
        """
        from aiida.orm.data.structure import StructureData

        with self.assertRaises(ValueError):
            _ = StructureData(cell=((0.,0.,0.),(0.,1.,0.),(0.,0.,1.)))

    def test_cell_zero_volume(self):
        """
        Wrong cell (volume is zero)
        """
        from aiida.orm.data.structure import StructureData

        with self.assertRaises(ValueError):
            _ = StructureData(cell=((1.,0.,0.),(0.,1.,0.),(1.,1.,0.)))

    def test_cell_ok_init(self):
        """
        Correct cell
        """
        from aiida.orm.data.structure import StructureData

        cell = ((1.,0.,0.),(0.,2.,0.),(0.,0.,3.))
        a = StructureData(cell=cell)
        out_cell = a.cell
        
        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(cell[i][j],out_cell[i][j])
    
    def test_volume(self):
        """
        Check the volume calculation
        """
        from aiida.orm.data.structure import StructureData

        a = StructureData(cell = ((1.,0.,0.),(0.,2.,0.),(0.,0.,3.)))
        self.assertAlmostEqual(a.get_cell_volume(), 6.)

    def test_wrong_pbc_1(self):
        """
        Wrong pbc parameter (not bool or iterable)
        """
        from aiida.orm.data.structure import StructureData

        with self.assertRaises(ValueError):
            cell = ((1.,0.,0.),(0.,2.,0.),(0.,0.,3.))
            _ = StructureData(cell=cell,pbc=1)

    def test_wrong_pbc_2(self):
        """
        Wrong pbc parameter (iterable but with wrong len)
        """
        from aiida.orm.data.structure import StructureData

        with self.assertRaises(ValueError):
            cell = ((1.,0.,0.),(0.,2.,0.),(0.,0.,3.))
            _ = StructureData(cell=cell,pbc=[True,True])

    def test_wrong_pbc_3(self):
        """
        Wrong pbc parameter (iterable but with wrong len)
        """
        from aiida.orm.data.structure import StructureData

        with self.assertRaises(ValueError):
            cell = ((1.,0.,0.),(0.,2.,0.),(0.,0.,3.))
            _ = StructureData(cell=cell,pbc=[])

    def test_ok_pbc_1(self):
        """
        Single pbc value
        """
        from aiida.orm.data.structure import StructureData

        cell = ((1.,0.,0.),(0.,2.,0.),(0.,0.,3.))
        a = StructureData(cell=cell,pbc=True)
        self.assertEquals(a.pbc,tuple([True,True,True]))

        a = StructureData(cell=cell,pbc=False)
        self.assertEquals(a.pbc,tuple([False,False,False]))

    def test_ok_pbc_2(self):
        """
        One-element list
        """
        from aiida.orm.data.structure import StructureData

        cell = ((1.,0.,0.),(0.,2.,0.),(0.,0.,3.))
        a = StructureData(cell=cell,pbc=[True])
        self.assertEqual(a.pbc,tuple([True,True,True]))

        a = StructureData(cell=cell,pbc=[False])
        self.assertEqual(a.pbc,tuple([False,False,False]))

    def test_ok_pbc_3(self):
        """
        Three-element list
        """
        from aiida.orm.data.structure import StructureData

        cell = ((1.,0.,0.),(0.,2.,0.),(0.,0.,3.))
        a = StructureData(cell=cell,pbc=[True,False,True])
        self.assertEqual(a.pbc,tuple([True,False,True]))

class TestStructureData(AiidaTestCase):
    """
    Tests the creation of StructureData objects (cell and pbc).
    """

    def test_cell_ok_and_atoms(self):
        """
        Test the creation of a cell and the appending of atoms
        """
        from aiida.orm.data.structure import StructureData

        cell = ((2.,0.,0.),(0.,2.,0.),(0.,0.,2.))
        
        a = StructureData(cell=cell)
        out_cell = a.cell
        self.assertAlmostEquals(cell, out_cell)
        
        a.append_atom(position=(0.,0.,0.),symbols=['Ba'])
        a.append_atom(position=(1.,1.,1.),symbols=['Ti'])
        a.append_atom(position=(1.2,1.4,1.6),symbols=['Ti'])
        self.assertFalse(a.is_alloy())
        self.assertFalse(a.has_vacancies())
        # There should be only two kinds! (two atoms of kind Ti should
        # belong to the same kind)
        self.assertEquals(len(a.kinds), 2) 

        a.append_atom(position=(0.5,1.,1.5), symbols=['O', 'C'], 
                         weights=[0.5,0.5])
        self.assertTrue(a.is_alloy())
        self.assertFalse(a.has_vacancies())

        a.append_atom(position=(0.5,1.,1.5), symbols=['O'], weights=[0.5])
        self.assertTrue(a.is_alloy())
        self.assertTrue(a.has_vacancies())

        a.clear_kinds()
        a.append_atom(position=(0.5,1.,1.5), symbols=['O'], weights=[0.5])
        self.assertFalse(a.is_alloy())
        self.assertTrue(a.has_vacancies())

    def test_kind_1(self):
        """
        Test the management of kinds (automatic detection of kind of 
        simple atoms).
        """
        from aiida.orm.data.structure import StructureData

        a = StructureData(cell=((2.,0.,0.),(0.,2.,0.),(0.,0.,2.)))
        
        a.append_atom(position=(0.,0.,0.),symbols=['Ba'])
        a.append_atom(position=(0.5,0.5,0.5),symbols=['Ba'])
        a.append_atom(position=(1.,1.,1.),symbols=['Ti'])
        
        self.assertEqual(len(a.kinds),2) # I should only have two types
        # I check for the default names of kinds
        self.assertEqual(set(k.name for k in a.kinds),
                         set(('Ba', 'Ti')))

    def test_kind_2(self):
        """
        Test the management of kinds (manual specification of kind name).
        """
        from aiida.orm.data.structure import StructureData

        a = StructureData(cell=((2.,0.,0.),(0.,2.,0.),(0.,0.,2.)))
        
        a.append_atom(position=(0.,0.,0.),symbols=['Ba'],name='Ba1')
        a.append_atom(position=(0.5,0.5,0.5),symbols=['Ba'],name='Ba2')
        a.append_atom(position=(1.,1.,1.),symbols=['Ti'])
        
        kind_list = a.kinds
        self.assertEqual(len(kind_list),3) # I should have now three kinds
        self.assertEqual(set(k.name for k in kind_list),
                         set(('Ba1', 'Ba2', 'Ti')))

    def test_kind_3(self):
        """
        Test the management of kinds (adding an atom with different mass).
        """
        from aiida.orm.data.structure import StructureData

        a = StructureData(cell=((2.,0.,0.),(0.,2.,0.),(0.,0.,2.)))
        
        a.append_atom(position=(0.,0.,0.),symbols=['Ba'],mass=100.)
        with self.assertRaises(ValueError):
            # Shouldn't allow, I am adding two sites with the same name 'Ba'
            a.append_atom(position=(0.5,0.5,0.5),symbols=['Ba'],
                          mass=101., name='Ba') 

        # now it should work because I am using a different kind name
        a.append_atom(position=(0.5,0.5,0.5),
                      symbols=['Ba'],mass=101.,name='Ba2') 
            
        a.append_atom(position=(1.,1.,1.),symbols=['Ti'])
        
        self.assertEqual(len(a.kinds),3) # I should have now three types
        self.assertEqual(len(a.sites),3) # and 3 sites
        self.assertEqual(set(k.name for k in a.kinds), set(('Ba', 'Ba2', 'Ti')))

    def test_kind_4(self):
        """
        Test the management of kind (adding an atom with different symbols
        or weights).
        """
        from aiida.orm.data.structure import StructureData

        a = StructureData(cell=((2.,0.,0.),(0.,2.,0.),(0.,0.,2.)))
        
        a.append_atom(position=(0.,0.,0.),symbols=['Ba','Ti'],
                      weights=(1.,0.),name='mytype')

        with self.assertRaises(ValueError):
            # Shouldn't allow, different weights
            a.append_atom(position=(0.5,0.5,0.5),symbols=['Ba','Ti'],
                          weights=(0.9,0.1),name='mytype') 

        with self.assertRaises(ValueError):
            # Shouldn't allow, different weights (with vacancy)
            a.append_atom(position=(0.5,0.5,0.5),symbols=['Ba','Ti'],
                          weights=(0.8,0.1),name='mytype') 

        with self.assertRaises(ValueError):
            # Shouldn't allow, different symbols list
            a.append_atom(position=(0.5,0.5,0.5),symbols=['Ba'],
                          name='mytype') 

        with self.assertRaises(ValueError):
            # Shouldn't allow, different symbols list
            a.append_atom(position=(0.5,0.5,0.5),symbols=['Si','Ti'],
                          weights=(1.,0.),name='mytype') 

        # should allow because every property is identical
        a.append_atom(position=(0.,0.,0.),symbols=['Ba','Ti'],
                      weights=(1.,0.),name='mytype')
        
        self.assertEquals(len(a.kinds), 1)

    def test_kind_5(self):
        """
        Test the management of kinds (automatic creation of new kind
        if name is not specified and properties are different).
        """
        from aiida.orm.data.structure import StructureData

        a = StructureData(cell=((2.,0.,0.),(0.,2.,0.),(0.,0.,2.)))
        
        a.append_atom(position=(0.,0.,0.),symbols='Ba',mass=100.)
        a.append_atom(position=(0.,0.,0.),symbols='Ti')
        # The name does not exist
        a.append_atom(position=(0.,0.,0.),symbols='Ti',name='Ti2')
        # The name already exists, but the properties are identical => OK
        a.append_atom(position=(1.,1.,1.),symbols='Ti',name='Ti2')
        # The name already exists, but the properties are different!
        with self.assertRaises(ValueError):
            a.append_atom(position=(1.,1.,1.),symbols='Ti',mass=100.,name='Ti2')
        # Should not complain, should create a new type
        a.append_atom(position=(0.,0.,0.),symbols='Ba',mass=150.)

        # There should be 4 kinds, the automatic name for the last one
        # should be Ba1
        self.assertEquals([k.name for k in a.kinds],
                          ['Ba', 'Ti', 'Ti2', 'Ba1'])
        self.assertEquals(len(a.sites),5)

class TestStructureDataLock(AiidaTestCase):
    """
    Tests that the structure is locked after storage
    """
    def test_lock(self):
        """
        Start from a StructureData object, convert to raw and then back
        """
        from aiida.orm.data.structure import StructureData, Kind, Site

        cell = ((1.,0.,0.),(0.,2.,0.),(0.,0.,3.))
        a = StructureData(cell=cell)
        
        a.pbc = [False,True,True]

        k = Kind(symbols='Ba',name='Ba')       
        s = Site(position=(0.,0.,0.),kind='Ba')
        a.append_kind(k)
        a.append_site(s)

        a.append_atom(symbols='Ti', position=[0.,0.,0.])

        a.store()

        k2 = Kind(symbols='Ba',name='Ba')
        # Nothing should be changed after store()
        with self.assertRaises(ModificationNotAllowed):
            a.append_kind(k2)
        with self.assertRaises(ModificationNotAllowed):
            a.append_site(s)
        with self.assertRaises(ModificationNotAllowed):
            a.clear_sites()
        with self.assertRaises(ModificationNotAllowed):
            a.clear_kinds()
        with self.assertRaises(ModificationNotAllowed):
            a.cell = cell
        with self.assertRaises(ModificationNotAllowed):
            a.pbc = [True,True,True]

        _ = a.get_cell_volume()
        _ = a.is_alloy()
        _ = a.has_vacancies()

        b = a.copy()
        # I check that I can edit after copy
        b.append_site(s)
        b.clear_sites()
        # I check that the original did not change
        self.assertNotEquals(len(a.sites), 0)
        b.cell = cell
        b.pbc = [True,True,True]

class TestStructureDataReload(AiidaTestCase):
    """
    Tests the creation of StructureData, converting it to a raw format and
    converting it back.
    """
    def test_reload(self):
        """
        Start from a StructureData object, convert to raw and then back
        """
        from aiida.orm.data.structure import StructureData

        cell = ((1.,0.,0.),(0.,2.,0.),(0.,0.,3.))
        a = StructureData(cell=cell)
        
        a.pbc = [False,True,True]

        a.append_atom(position=(0.,0.,0.),symbols=['Ba'])
        a.append_atom(position=(1.,1.,1.),symbols=['Ti'])

        a.store()

        b = StructureData(uuid=a.uuid)
        
        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(cell[i][j], b.cell[i][j])
        
        self.assertEqual(b.pbc, (False,True,True))
        self.assertEqual(len(b.sites), 2)
        self.assertEqual(b.kinds[0].symbols[0], 'Ba')
        self.assertEqual(b.kinds[1].symbols[0], 'Ti')
        for i in range(3):
            self.assertAlmostEqual(b.sites[0].position[i], 0.)
        for i in range(3):
            self.assertAlmostEqual(b.sites[1].position[i], 1.)

    def test_copy(self):
        """
        Start from a StructureData object, copy it and see if it is preserved
        """
        from aiida.orm.data.structure import StructureData

        cell = ((1.,0.,0.),(0.,2.,0.),(0.,0.,3.))
        a = StructureData(cell=cell)
        
        a.pbc = [False,True,True]

        a.append_atom(position=(0.,0.,0.),symbols=['Ba'])
        a.append_atom(position=(1.,1.,1.),symbols=['Ti'])

        b = a.copy()        
        
        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(cell[i][j], b.cell[i][j])
        
        self.assertEqual(b.pbc, (False,True,True))
        self.assertEqual(len(b.kinds), 2)
        self.assertEqual(len(b.sites), 2)
        self.assertEqual(b.kinds[0].symbols[0], 'Ba')
        self.assertEqual(b.kinds[1].symbols[0], 'Ti')
        for i in range(3):
            self.assertAlmostEqual(b.sites[0].position[i], 0.)
        for i in range(3):
            self.assertAlmostEqual(b.sites[1].position[i], 1.)

        a.store()

        # Copy after store()
        c = a.copy()
        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(cell[i][j], c.cell[i][j])
        
        self.assertEqual(c.pbc, (False,True,True))
        self.assertEqual(len(c.kinds), 2)
        self.assertEqual(len(c.sites), 2)
        self.assertEqual(c.kinds[0].symbols[0], 'Ba')
        self.assertEqual(c.kinds[1].symbols[0], 'Ti')
        for i in range(3):
            self.assertAlmostEqual(c.sites[0].position[i], 0.)
        for i in range(3):
            self.assertAlmostEqual(c.sites[1].position[i], 1.)

class TestStructureDataFromAse(AiidaTestCase):
    """
    Tests the creation of Sites from/to a ASE object.
    """
    from aiida.orm.data.structure import has_ase

    @unittest.skipIf(not has_ase(),"Unable to import ase")
    def test_ase(self):
        from aiida.orm.data.structure import StructureData
        import ase

        a = ase.Atoms('SiGe',cell=(1.,2.,3.),pbc=(True,False,False))
        a.set_positions(
            ((0.,0.,0.),
             (0.5,0.7,0.9),)
            )
        a[1].mass = 110.2

        b = StructureData(ase=a)
        c = b.get_ase()

        self.assertEqual(a[0].symbol, c[0].symbol)
        self.assertEqual(a[1].symbol, c[1].symbol)
        for i in range(3):
            self.assertAlmostEqual(a[0].position[i], c[0].position[i])
        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(a.cell[i][j], c.cell[i][j])
           
        self.assertAlmostEqual(c[1].mass, 110.2)

    @unittest.skipIf(not has_ase(),"Unable to import ase")
    def test_conversion_of_types_1(self):
        from aiida.orm.data.structure import StructureData
        import ase

        a = ase.Atoms('Si4Ge4',cell=(1.,2.,3.),pbc=(True,False,False))
        a.set_positions(
            ((0.0,0.0,0.0),
             (0.1,0.1,0.1),
             (0.2,0.2,0.2),
             (0.3,0.3,0.3),
             (0.4,0.4,0.4),
             (0.5,0.5,0.5),
             (0.6,0.6,0.6),
             (0.7,0.7,0.7),
             )
            )

        a.set_tags((0,1,2,3,4,5,6,7))

        b = StructureData(ase=a)
        self.assertEquals([k.name for k in b.kinds],
                          ["Si", "Si1", "Si2", "Si3",
                           "Ge4", "Ge5", "Ge6", "Ge7"])
        c = b.get_ase()

        a_tags = list(a.get_tags())
        c_tags = list(c.get_tags())
        self.assertEqual(a_tags, c_tags)

    @unittest.skipIf(not has_ase(),"Unable to import ase")
    def test_conversion_of_types_2(self):
        from aiida.orm.data.structure import StructureData
        import ase

        a = ase.Atoms('Si4',cell=(1.,2.,3.),pbc=(True,False,False))
        a.set_positions(
            ((0.0,0.0,0.0),
             (0.1,0.1,0.1),
             (0.2,0.2,0.2),
             (0.3,0.3,0.3),
             )
            )

        a.set_tags((0,1,0,1))
        a[2].mass = 100.
        a[3].mass = 300.
        
        b = StructureData(ase=a)
        # This will give funny names to the kinds, because I am using
        # both tags and different properties (mass). I just check to have
        # 4 kinds
        self.assertEquals(len(b.kinds), 4)

        # Do I get the same tags after one full iteration back and forth?
        c = b.get_ase()
        d = StructureData(ase=c)
        e = d.get_ase()       
        c_tags = list(c.get_tags())
        e_tags = list(e.get_tags())
        self.assertEqual(c_tags, e_tags)      
        
        
    @unittest.skipIf(not has_ase(),"Unable to import ase")
    def test_conversion_of_types_3(self):
        from aiida.orm.data.structure import StructureData

        a = StructureData()
        a.append_atom(position=(0.,0.,0.), symbols='Ba', name='Ba')
        a.append_atom(position=(0.,0.,0.), symbols='Ba', name='Ba1')
        a.append_atom(position=(0.,0.,0.), symbols='Cu', name='Cu')
        # continues with a number
        a.append_atom(position=(0.,0.,0.), symbols='Cu', name='Cu2')
        # does not continue with a number
        a.append_atom(position=(0.,0.,0.), symbols='Cu', name='Cu_my')
        # random string
        a.append_atom(position=(0.,0.,0.), symbols='Cu', name='a_name')
        # a name of another chemical symbol
        a.append_atom(position=(0.,0.,0.), symbols='Cu', name='Fe')
        # lowercase! as if it were a random string
        a.append_atom(position=(0.,0.,0.), symbols='Cu', name='cu1') 
        
        # Just to be sure that the species were saved with the correct name
        # in the first place
        self.assertEquals([k.name for k in a.kinds], 
                          ['Ba', 'Ba1', 'Cu', 'Cu2', 'Cu_my',
                           'a_name', 'Fe', 'cu1'])
        
        b = a.get_ase()
        self.assertEquals(b.get_chemical_symbols(), ['Ba', 'Ba', 'Cu', 
                                                     'Cu', 'Cu', 'Cu', 
                                                     'Cu', 'Cu'])
        self.assertEquals(list(b.get_tags()), [0, 1, 0, 2, 3, 4, 5, 6])


class TestArrayData(AiidaTestCase):
    """
    Tests the ArrayData objects.
    """

    def test_creation(self):
        """
        Check the methods to add, remove, modify, and get arrays and
        array shapes.
        """
        from aiida.orm.data.array import ArrayData
        import numpy
        
        # Create a node with two arrays
        n = ArrayData()
        first = numpy.random.rand(2,3,4)
        n.set_array('first', first)
        
        second = numpy.arange(10)
        n.set_array('second', second)

        third = numpy.random.rand(6,6)
        n.set_array('third', third)

        
        # Check if the arrays are there
        self.assertEquals(set(['first', 'second', 'third']), set(n.arraynames()))
        self.assertAlmostEquals(abs(first-n.get_array('first')).max(), 0.)
        self.assertAlmostEquals(abs(second-n.get_array('second')).max(), 0.)
        self.assertAlmostEquals(abs(third-n.get_array('third')).max(), 0.)
        self.assertEquals(first.shape, n.get_cached_shape('first'))
        self.assertEquals(second.shape, n.get_cached_shape('second')) 
        self.assertEquals(third.shape, n.get_cached_shape('third')) 
        
        with self.assertRaises(KeyError):
            n.get_array('nonexistent_array')
        
        # Delete an array, and try to delete a non-existing one
        n.delete_array('third')
        with self.assertRaises(KeyError):
            n.delete_array('nonexistent_array')
          
        # Overwrite an array
        first = numpy.random.rand(4,5,6)
        n.set_array('first', first)
        
        # Check if the arrays are there, and if I am getting the new one
        self.assertEquals(set(['first', 'second']), set(n.arraynames()))
        self.assertAlmostEquals(abs(first-n.get_array('first')).max(), 0.)
        self.assertAlmostEquals(abs(second-n.get_array('second')).max(), 0.)
        self.assertEquals(first.shape, n.get_cached_shape('first'))
        self.assertEquals(second.shape, n.get_cached_shape('second')) 
        
        n.store()
        
        # Same checks, after storing
        self.assertEquals(set(['first', 'second']), set(n.arraynames()))
        self.assertAlmostEquals(abs(first-n.get_array('first')).max(), 0.)
        self.assertAlmostEquals(abs(second-n.get_array('second')).max(), 0.)
        self.assertEquals(first.shape, n.get_cached_shape('first'))
        self.assertEquals(second.shape, n.get_cached_shape('second')) 

        n2 = ArrayData(uuid=n.uuid)
        
        # Same checks, after reloading
        self.assertEquals(set(['first', 'second']), set(n2.arraynames()))
        self.assertAlmostEquals(abs(first-n2.get_array('first')).max(), 0.)
        self.assertAlmostEquals(abs(second-n2.get_array('second')).max(), 0.)
        self.assertEquals(first.shape, n2.get_cached_shape('first'))
        self.assertEquals(second.shape, n2.get_cached_shape('second')) 

        # Check that I cannot modify the node after storing
        with self.assertRaises(ModificationNotAllowed):
            n.delete_array('first')
        with self.assertRaises(ModificationNotAllowed):
            n.set_array('second', first)
            
        # Again same checks, to verify that the attempts to delete/overwrite
        # arrays did not damage the node content
        self.assertEquals(set(['first', 'second']), set(n.arraynames()))
        self.assertAlmostEquals(abs(first-n.get_array('first')).max(), 0.)
        self.assertAlmostEquals(abs(second-n.get_array('second')).max(), 0.)
        self.assertEquals(first.shape, n.get_cached_shape('first'))
        self.assertEquals(second.shape, n.get_cached_shape('second')) 
        
    def test_iteration(self):
        """
        Check the functionality of the iterarrays() iterator
        """
        from aiida.orm.data.array import ArrayData
        import numpy
        
        # Create a node with two arrays
        n = ArrayData()
        first = numpy.random.rand(2,3,4)
        n.set_array('first', first)
        
        second = numpy.arange(10)
        n.set_array('second', second)

        third = numpy.random.rand(6,6)
        n.set_array('third', third)
    
        for name, array in n.iterarrays():
            if name == 'first':
                self.assertAlmostEquals(abs(first-array).max(), 0.)
            if name == 'second':
                self.assertAlmostEquals(abs(second-array).max(), 0.)
            if name == 'third':
                self.assertAlmostEquals(abs(third-array).max(), 0.)
        
        
        