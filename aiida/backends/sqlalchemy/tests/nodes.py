# -*- coding: utf-8 -*-

import unittest
import time



from sqlalchemy.exc import SQLAlchemyError


from aiida.backends.sqlalchemy.models.node import DbLink, DbPath, DbNode
from aiida.backends.sqlalchemy.tests.base import SqlAlchemyTests
from aiida.backends.utils import get_automatic_user

from aiida.common.exceptions import ModificationNotAllowed, NotExistent

from aiida.orm.node import Node
from aiida.orm import (JobCalculation, CalculationFactory, Data, DataFactory,
                       load_node)

from aiida.utils import timezone


__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__authors__ = "The AiiDA team."
__version__ = "0.6.0.1"

class TestTransitive(SqlAlchemyTests):

    def test_loop_not_allowed(self):
        """
        Test that no loop can be formed when inserting link
        """
        n1 = Node().store()
        n2 = Node().store()
        n3 = Node().store()
        n4 = Node().store()

        n2._add_link_from(n1)
        n3._add_link_from(n2)
        n4._add_link_from(n3)

        with self.assertRaises(ValueError):  # This would generate a loop
            n1._add_link_from(n4)

    def test_creation_and_deletion(self):
        """
        Test the creation and deletion of the transitive closure table
        """

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
        n3._add_link_from(n2)
        n2._add_link_from(n1)
        n5._add_link_from(n3)
        n5._add_link_from(n4)
        n4._add_link_from(n2)

        n7._add_link_from(n6)
        n8._add_link_from(n7)

        # Yet, no links from 1 to 8
        self.assertEquals(DbPath.query.filter_by(parent_id=n1.dbnode.id,
                                                 child_id=n8.dbnode.id).count(), 0)

        n6._add_link_from(n5)
        # Yet, now 2 links from 1 to 8
        self.assertEquals(DbPath.query.filter_by(parent_id=n1.dbnode.id,
                                                 child_id=n8.dbnode.id).count(), 2)

        n7._add_link_from(n9)
        # Still two links...
        self.assertEquals(DbPath.query.filter_by(parent_id=n1.dbnode.id,
                                                 child_id=n8.dbnode.id).count(), 2)

        n9._add_link_from(n6)
        # And now there should be 4 nodes
        self.assertEquals(DbPath.query.filter_by(parent_id=n1.dbnode.id,
                                                 child_id=n8.dbnode.id).count(), 4)

        ### I start deleting now

        # I cut one branch below: I should loose 2 links
        self.session.delete(DbLink.query.filter_by(input_id=n6.dbnode.id,
                                                     output_id=n9.dbnode.id).first())
        self.assertEquals(DbPath.query.filter_by(parent_id=n1.dbnode.id,
                                                 child_id=n8.dbnode.id).count(), 2)


        # I cut another branch above: I should loose one more link
        self.session.delete(DbLink.query.filter_by(input_id=n2.dbnode.id,
                                                     output_id=n4.dbnode.id).first())

        self.assertEquals(DbPath.query.filter_by(parent_id=n1.dbnode.id,
                                                 child_id=n8.dbnode.id).count(), 1)

        # Another cut should delete all links
        self.session.delete(DbLink.query.filter_by(input_id=n3.dbnode.id,
                                                     output_id=n5.dbnode.id).first())

        self.assertEquals(DbPath.query.filter_by(parent_id=n1.dbnode.id,
                                                 child_id=n8.dbnode.id).count(), 0)

        # But I did not delete everything! For instance, I can check
        # the following links
        self.assertEquals(DbPath.query.filter_by(parent_id=n4.dbnode.id,
                                                 child_id=n8.dbnode.id).count(), 1)
        self.assertEquals(DbPath.query.filter_by(parent_id=n5.dbnode.id,
                                                 child_id=n8.dbnode.id).count(), 1)

        # Finally, I reconnect in a different way the two graphs and
        # check that 1 and 8 are again connected
        n4._add_link_from(n3)
        self.assertEquals(DbPath.query.filter_by(parent_id=n1.dbnode.id,
                                                 child_id=n8.dbnode.id).count(), 1)

class TestQueryWithAiidaObjects(SqlAlchemyTests):
    """
    Test if queries work properly also with aiida.orm.Node classes instead of
    aiida.backends.sqlalchemy.models.node.DbNode objects.
    """

    @SqlAlchemyTests.inject_computer
    def test_with_subclasses(self, computer):

        extra_name = self.__class__.__name__ + "/test_with_subclasses"
        calc_params = {
            'computer': computer,
            'resources': {'num_machines': 1,
                          'num_mpiprocs_per_machine': 1}
        }

        TemplateReplacerCalc = CalculationFactory('simpleplugins.templatereplacer')
        ParameterData = DataFactory('parameter')

        a1 = JobCalculation(**calc_params).store()
        # To query only these nodes later
        a1.set_extra(extra_name, True)
        a2 = TemplateReplacerCalc(**calc_params).store()
        # To query only these nodes later
        a2.set_extra(extra_name, True)
        a3 = Data().store()
        a3.set_extra(extra_name, True)
        a4 = ParameterData(dict={'a': 'b'}).store()
        a4.set_extra(extra_name, True)
        a5 = Node().store()
        a5.set_extra(extra_name, True)
        # I don't set the extras, just to be sure that the filtering works
        # The filtering is needed because other tests will put stuff int he DB
        a6 = JobCalculation(**calc_params)
        a6.store()
        a7 = Node()
        a7.store()

        # Query by calculation
        results = list(JobCalculation.query(dbextras__key=extra_name))
        # a3, a4, a5 should not be found because they are not JobCalculations.
        # a6, a7 should not be found because they have not the attribute set.
        self.assertEquals(set([i.pk for i in results]),
                          set([a1.pk, a2.pk]))

        # Same query, but by the generic Node class
        results = list(Node.query(dbextras__key=extra_name))
        self.assertEquals(set([i.pk for i in results]),
                          set([a1.pk, a2.pk, a3.pk, a4.pk, a5.pk]))

        # Same query, but by the Data class
        results = list(Data.query(dbextras__key=extra_name))
        self.assertEquals(set([i.pk for i in results]),
                          set([a3.pk, a4.pk]))

        # Same query, but by the ParameterData subclass
        results = list(ParameterData.query(dbextras__key=extra_name))
        self.assertEquals(set([i.pk for i in results]),
                          set([a4.pk]))

        # Same query, but by the TemplateReplacerCalc subclass
        results = list(TemplateReplacerCalc.query(dbextras__key=extra_name))
        self.assertEquals(set([i.pk for i in results]),
                          set([a2.pk]))


    def test_get_inputs_and_outputs(self):
        a1 = Node().store()
        a2 = Node().store()
        a3 = Node().store()
        a4 = Node().store()

        a2._add_link_from(a1)
        a3._add_link_from(a2)
        a4._add_link_from(a2)
        a4._add_link_from(a3)

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
        a = Node()
        a._set_attr('myvalue', 123)
        a.store()

        a2 = Node().store()

        a3 = Node()
        a3._set_attr('myvalue', 145)
        a3.store()

        a4 = Node().store()

        a2._add_link_from(a)
        a3._add_link_from(a2)
        a4._add_link_from(a2)
        a4._add_link_from(a3)

        b = Node.query(id=a2.id).all()
        self.assertEquals(len(b), 1)
        # It is a aiida.orm.Node instance
        self.assertTrue(isinstance(b[0], Node))
        self.assertEquals(b[0].uuid, a2.uuid)

        going_out_from_a2 = Node.query(inputs__id__in=[_.id for _ in b]).all()
        # Two nodes going out from a2
        self.assertEquals(len(going_out_from_a2), 2)
        self.assertTrue(isinstance(going_out_from_a2[0], Node))
        self.assertTrue(isinstance(going_out_from_a2[1], Node))
        uuid_set = set([going_out_from_a2[0].uuid, going_out_from_a2[1].uuid])

        # I check that I can query also directly the django DbNode
        # class passing a aiida.orm.Node entity

        # # XXX SP: we can't do this using SqlAlchemy => pass a Node instance and
        # # expect a filter on the DbNode id
        # going_out_from_a2_db = DbNode.query.filter(DbNode.inputs.in_(b)).all()
        # self.assertEquals(len(going_out_from_a2_db), 2)
        # self.assertTrue(isinstance(going_out_from_a2_db[0], DbNode))
        # self.assertTrue(isinstance(going_out_from_a2_db[1], DbNode))
        # uuid_set_db = set([going_out_from_a2_db[0].uuid,
        #                    going_out_from_a2_db[1].uuid])
        #
        # # I check that doing the query with a Node or DbNode instance,
        # # I get the same nodes
        # self.assertEquals(uuid_set, uuid_set_db)
        #
        # # This time I don't use the __in filter, but I still pass a Node instance
        # going_out_from_a2_bis = Node.query(inputs=b[0]).all()
        # self.assertEquals(len(going_out_from_a2_bis), 2)
        # self.assertTrue(isinstance(going_out_from_a2_bis[0], Node))
        # self.assertTrue(isinstance(going_out_from_a2_bis[1], Node))
        #
        # # Query for links starting from b[0]==a2 using again the Node class
        # output_links_b = DbLink.query.filter_by(input=b[0])
        # self.assertEquals(len(output_links_b), 2)
        # self.assertTrue(isinstance(output_links_b[0], DbLink))
        # self.assertTrue(isinstance(output_links_b[1], DbLink))
        # uuid_set_db_link = set([output_links_b[0].output.uuid,
        #                         output_links_b[1].output.uuid])
        # self.assertEquals(uuid_set, uuid_set_db_link)


        # Query for related fields using django syntax
        # Note that being myvalue an attribute, it is internally stored starting
        # with an underscore
        nodes_with_given_attribute = Node.query(dbattributes__key='myvalue',
                                                dbattributes__ival=145).all()
        # should be entry a3
        self.assertEquals(len(nodes_with_given_attribute), 1)
        self.assertTrue(isinstance(nodes_with_given_attribute[0], Node))
        self.assertEquals(nodes_with_given_attribute[0].uuid, a3.uuid)


class TestNodeBasic(SqlAlchemyTests):
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
               'recursive': {'a': 1, 'b': True, 'c': 1.2, 'd': [1, 2, None],
                             'e': {'z': 'z', 'x': None, 'xx': {}, 'yy': []}}}
    listval = [1, "s", True, None]
    emptydict = {}
    emptylist = []

    def test_attr_before_storing(self):
        a = Node()
        a._set_attr('k1', self.boolval)
        a._set_attr('k2', self.intval)
        a._set_attr('k3', self.floatval)
        a._set_attr('k4', self.stringval)
        a._set_attr('k5', self.dictval)
        a._set_attr('k6', self.listval)
        a._set_attr('k7', self.emptydict)
        a._set_attr('k8', self.emptylist)
        a._set_attr('k9', None)

        # Now I check if I can retrieve them, before the storage
        self.assertEquals(self.boolval, a.get_attr('k1'))
        self.assertEquals(self.intval, a.get_attr('k2'))
        self.assertEquals(self.floatval, a.get_attr('k3'))
        self.assertEquals(self.stringval, a.get_attr('k4'))
        self.assertEquals(self.dictval, a.get_attr('k5'))
        self.assertEquals(self.listval, a.get_attr('k6'))
        self.assertEquals(self.emptydict, a.get_attr('k7'))
        self.assertEquals(self.emptylist, a.get_attr('k8'))
        self.assertIsNone(a.get_attr('k9'))

        # And now I try to delete the keys
        a._del_attr('k1')
        a._del_attr('k2')
        a._del_attr('k3')
        a._del_attr('k4')
        a._del_attr('k5')
        a._del_attr('k6')
        a._del_attr('k7')
        a._del_attr('k8')
        a._del_attr('k9')

        with self.assertRaises(AttributeError):
            # I delete twice the same attribute
            a._del_attr('k1')

        with self.assertRaises(AttributeError):
            # I delete a non-existing attribute
            a._del_attr('nonexisting')

        with self.assertRaises(AttributeError):
            # I get a deleted attribute
            a.get_attr('k1')

        with self.assertRaises(AttributeError):
            # I get a non-existing attribute
            a.get_attr('nonexisting')

    def DISABLED(self):
        """
        This test routine is disabled for the time being; I will re-enable
        when I have time to implement the check of the length of the 'key'.
        """

        def test_very_deep_attributes(self):
            """
            Test attributes where the total length of the key, including the
            separators, would be longer than the field length in the DB.
            """
            from aiida.backends.djsite.db import models

            n = Node()

            semi_long_string = "abcdefghijklmnopqrstuvwxyz"
            value = "some value"

            attribute = {semi_long_string: value}
            key_len = len(semi_long_string)

            max_len = models.DbAttribute._meta.get_field_by_name('key')[0].max_length

            while key_len < 2 * max_len:
                # Create a deep, recursive attribute
                attribute = {semi_long_string: attribute}
                key_len += len(semi_long_string) + len(models.DbAttribute._sep)

            n._set_attr(semi_long_string, attribute)

            n.store()

            all_keys = models.DbAttribute.objects.filter(
                dbnode=n.dbnode).values_list('key', flat=True)

            print max(len(i) for i in all_keys)

    def test_datetime_attribute(self):
        from aiida.utils.timezone import (
            get_current_timezone, is_naive, make_aware, now)

        a = Node()

        date = now()

        a._set_attr('some_date', date)
        a.store()

        retrieved = a.get_attr('some_date')

        if is_naive(date):
            date_to_compare = make_aware(date, get_current_timezone())
        else:
            date_to_compare = date

        # Do not compare microseconds (they are not stored in the case of MySQL)
        date_to_compare = date_to_compare.replace(microsecond=0)
        retrieved = retrieved.replace(microsecond=0)

        self.assertEquals(date_to_compare, retrieved)


    def test_attributes_on_copy(self):
        import copy

        a = Node()
        attrs_to_set = {
            'none': None,
            'bool': self.boolval,
            'integer': self.intval,
            'float': self.floatval,
            'string': self.stringval,
            'dict': self.dictval,
            'list': self.listval,
            'emptydict': {},
            'emptylist': [],
        }

        for k, v in attrs_to_set.iteritems():
            a._set_attr(k, v)

        a.store()

        # I now set extras
        extras_to_set = {
            'bool': 'some non-boolean value',
            'some_other_name': 987}

        for k, v in extras_to_set.iteritems():
            a.set_extra(k, v)

            # I make a copy
        b = a.copy()
        # I modify an attribute and add a new one; I mirror it in the dictionary
        # for later checking
        b_expected_attributes = copy.deepcopy(attrs_to_set)
        b._set_attr('integer', 489)
        b_expected_attributes['integer'] = 489
        b._set_attr('new', 'cvb')
        b_expected_attributes['new'] = 'cvb'

        # I check before storing that the attributes are ok
        self.assertEquals({k: v for k, v in b.iterattrs()},
                          b_expected_attributes)
        # Note that during copy, I do not copy the extras!
        self.assertEquals({k: v for k, v in b.iterextras()}, {})

        # I store now
        b.store()
        # and I finally add a extras
        b.set_extra('meta', 'textofext')
        b_expected_extras = {'meta': 'textofext'}

        # Now I check for the attributes
        # First I check that nothing has changed
        self.assertEquals({k: v for k, v in a.iterattrs()}, attrs_to_set)
        self.assertEquals({k: v for k, v in a.iterextras()}, extras_to_set)

        # I check then on the 'b' copy
        self.assertEquals({k: v for k, v in b.iterattrs()},
                          b_expected_attributes)
        self.assertEquals({k: v for k, v in b.iterextras()},
                          b_expected_extras)

    def test_files(self):
        import tempfile

        a = Node()

        file_content = 'some text ABCDE'
        file_content_different = 'other values 12345'

        with tempfile.NamedTemporaryFile() as f:
            f.write(file_content)
            f.flush()
            a.add_path(f.name, 'file1.txt')
            a.add_path(f.name, 'file2.txt')

        self.assertEquals(set(a.get_folder_list()), set(['file1.txt', 'file2.txt']))
        with open(a.get_abs_path('file1.txt')) as f:
            self.assertEquals(f.read(), file_content)
        with open(a.get_abs_path('file2.txt')) as f:
            self.assertEquals(f.read(), file_content)

        b = a.copy()
        self.assertNotEquals(a.uuid, b.uuid)

        # Check that the content is there
        self.assertEquals(set(b.get_folder_list()), set(['file1.txt', 'file2.txt']))
        with open(b.get_abs_path('file1.txt')) as f:
            self.assertEquals(f.read(), file_content)
        with open(b.get_abs_path('file2.txt')) as f:
            self.assertEquals(f.read(), file_content)

        # I overwrite a file and create a new one in the copy only
        with tempfile.NamedTemporaryFile() as f:
            f.write(file_content_different)
            f.flush()
            b.add_path(f.name, 'file2.txt')
            b.add_path(f.name, 'file3.txt')

        # I check the new content, and that the old one has not changed
        self.assertEquals(set(a.get_folder_list()), set(['file1.txt', 'file2.txt']))
        with open(a.get_abs_path('file1.txt')) as f:
            self.assertEquals(f.read(), file_content)
        with open(a.get_abs_path('file2.txt')) as f:
            self.assertEquals(f.read(), file_content)
        self.assertEquals(set(b.get_folder_list()),
                          set(['file1.txt', 'file2.txt', 'file3.txt']))
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
            c.add_path(f.name, 'file1.txt')
            c.add_path(f.name, 'file4.txt')

        self.assertEquals(set(a.get_folder_list()), set(['file1.txt', 'file2.txt']))
        with open(a.get_abs_path('file1.txt')) as f:
            self.assertEquals(f.read(), file_content)
        with open(a.get_abs_path('file2.txt')) as f:
            self.assertEquals(f.read(), file_content)

        self.assertEquals(set(c.get_folder_list()),
                          set(['file1.txt', 'file2.txt', 'file4.txt']))
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
        import os, shutil
        import random, string

        a = Node()

        # Since Node uses the same method of Folder(),
        # for this test I create a test folder by hand
        # For any non-test usage, use SandboxFolder()!

        directory = os.path.realpath(os.path.join('/', 'tmp', 'tmp_try'))
        while os.path.exists(os.path.join(directory)):
            # I append a random letter/number until it is unique
            directory += random.choice(
                string.ascii_uppercase + string.digits)

        # create a folder structure to copy around
        tree_1 = os.path.join(directory, 'tree_1')
        os.makedirs(tree_1)
        file_content = 'some text ABCDE'
        file_content_different = 'other values 12345'
        with open(os.path.join(tree_1, 'file1.txt'), 'w') as f:
            f.write(file_content)
        os.mkdir(os.path.join(tree_1, 'dir1'))
        os.mkdir(os.path.join(tree_1, 'dir1', 'dir2'))
        with open(os.path.join(tree_1, 'dir1', 'file2.txt'), 'w') as f:
            f.write(file_content)
        os.mkdir(os.path.join(tree_1, 'dir1', 'dir2', 'dir3'))

        # add the tree to the node

        a.add_path(tree_1, 'tree_1')

        # verify if the node has the structure I expect
        self.assertEquals(set(a.get_folder_list()), set(['tree_1']))
        self.assertEquals(set(a.get_folder_list('tree_1')),
                          set(['file1.txt', 'dir1']))
        self.assertEquals(set(a.get_folder_list(os.path.join('tree_1', 'dir1'))),
                          set(['dir2', 'file2.txt']))
        with open(a.get_abs_path(os.path.join('tree_1', 'file1.txt'))) as f:
            self.assertEquals(f.read(), file_content)
        with open(a.get_abs_path(
                os.path.join('tree_1', 'dir1', 'file2.txt'))) as f:
            self.assertEquals(f.read(), file_content)

        # try to exit from the folder
        with self.assertRaises(ValueError):
            a.get_folder_list('..')

        # copy into a new node
        b = a.copy()
        self.assertNotEquals(a.uuid, b.uuid)

        # Check that the content is there
        self.assertEquals(set(b.get_folder_list('.')), set(['tree_1']))
        self.assertEquals(set(b.get_folder_list('tree_1')),
                          set(['file1.txt', 'dir1']))
        self.assertEquals(set(b.get_folder_list(os.path.join('tree_1', 'dir1'))),
                          set(['dir2', 'file2.txt']))
        with open(b.get_abs_path(os.path.join('tree_1', 'file1.txt'))) as f:
            self.assertEquals(f.read(), file_content)
        with open(b.get_abs_path(os.path.join(
                'tree_1', 'dir1', 'file2.txt'))) as f:
            self.assertEquals(f.read(), file_content)

        # I overwrite a file and create a new one in the copy only
        dir3 = os.path.join(directory, 'dir3')
        os.mkdir(dir3)

        b.add_path(dir3, os.path.join('tree_1', 'dir3'))
        # no absolute path here
        with self.assertRaises(ValueError):
            b.add_path('dir3', os.path.join('tree_1', 'dir3'))

        with tempfile.NamedTemporaryFile() as f:
            f.write(file_content_different)
            f.flush()
            b.add_path(f.name, 'file3.txt')

        # I check the new content, and that the old one has not changed
        # old
        self.assertEquals(set(a.get_folder_list('.')), set(['tree_1']))
        self.assertEquals(set(a.get_folder_list('tree_1')),
                          set(['file1.txt', 'dir1']))
        self.assertEquals(set(a.get_folder_list(os.path.join('tree_1', 'dir1'))),
                          set(['dir2', 'file2.txt']))
        with open(a.get_abs_path(os.path.join('tree_1', 'file1.txt'))) as f:
            self.assertEquals(f.read(), file_content)
        with open(a.get_abs_path(os.path.join(
                'tree_1', 'dir1', 'file2.txt'))) as f:
            self.assertEquals(f.read(), file_content)
        # new
        self.assertEquals(set(b.get_folder_list('.')),
                          set(['tree_1', 'file3.txt']))
        self.assertEquals(set(b.get_folder_list('tree_1')),
                          set(['file1.txt', 'dir1', 'dir3']))
        self.assertEquals(set(b.get_folder_list(os.path.join('tree_1', 'dir1'))),
                          set(['dir2', 'file2.txt']))
        with open(b.get_abs_path(os.path.join('tree_1', 'file1.txt'))) as f:
            self.assertEquals(f.read(), file_content)
        with open(b.get_abs_path(os.path.join(
                'tree_1', 'dir1', 'file2.txt'))) as f:
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
            c.add_path(f.name, os.path.join('tree_1', 'file1.txt'))
            c.add_path(f.name, os.path.join('tree_1', 'dir1', 'file4.txt'))
        c.remove_path(os.path.join('tree_1', 'dir1', 'dir2'))

        # check old
        self.assertEquals(set(a.get_folder_list('.')), set(['tree_1']))
        self.assertEquals(set(a.get_folder_list('tree_1')),
                          set(['file1.txt', 'dir1']))
        self.assertEquals(set(a.get_folder_list(os.path.join('tree_1', 'dir1'))),
                          set(['dir2', 'file2.txt']))
        with open(a.get_abs_path(os.path.join('tree_1', 'file1.txt'))) as f:
            self.assertEquals(f.read(), file_content)
        with open(a.get_abs_path(os.path.join(
                'tree_1', 'dir1', 'file2.txt'))) as f:
            self.assertEquals(f.read(), file_content)

        # check new
        self.assertEquals(set(c.get_folder_list('.')), set(['tree_1']))
        self.assertEquals(set(c.get_folder_list('tree_1')),
                          set(['file1.txt', 'dir1']))
        self.assertEquals(set(c.get_folder_list(os.path.join('tree_1', 'dir1'))),
                          set(['file2.txt', 'file4.txt']))
        with open(c.get_abs_path(os.path.join('tree_1', 'file1.txt'))) as f:
            self.assertEquals(f.read(), file_content_different)
        with open(c.get_abs_path(os.path.join(
                'tree_1', 'dir1', 'file2.txt'))) as f:
            self.assertEquals(f.read(), file_content)

        # garbage cleaning
        shutil.rmtree(directory)


    def test_attr_after_storing(self):
        a = Node()
        a._set_attr('none', None)
        a._set_attr('bool', self.boolval)
        a._set_attr('integer', self.intval)
        a._set_attr('float', self.floatval)
        a._set_attr('string', self.stringval)
        a._set_attr('dict', self.dictval)
        a._set_attr('list', self.listval)

        a.store()

        # Now I check if I can retrieve them, before the storage
        self.assertIsNone(a.get_attr('none'))
        self.assertEquals(self.boolval, a.get_attr('bool'))
        self.assertEquals(self.intval, a.get_attr('integer'))
        self.assertEquals(self.floatval, a.get_attr('float'))
        self.assertEquals(self.stringval, a.get_attr('string'))
        self.assertEquals(self.dictval, a.get_attr('dict'))
        self.assertEquals(self.listval, a.get_attr('list'))

        # And now I try to edit/delete the keys; I should not be able to do it
        # after saving. I try only for a couple of attributes
        with self.assertRaises(ModificationNotAllowed):
            a._del_attr('bool')
        with self.assertRaises(ModificationNotAllowed):
            a._set_attr('integer', 13)


    def test_attr_with_reload(self):
        a = Node()
        a._set_attr('none', None)
        a._set_attr('bool', self.boolval)
        a._set_attr('integer', self.intval)
        a._set_attr('float', self.floatval)
        a._set_attr('string', self.stringval)
        a._set_attr('dict', self.dictval)
        a._set_attr('list', self.listval)

        a.store()

        b = Node.get_subclass_from_uuid(a.uuid)
        self.assertIsNone(a.get_attr('none'))
        self.assertEquals(self.boolval, b.get_attr('bool'))
        self.assertEquals(self.intval, b.get_attr('integer'))
        self.assertEquals(self.floatval, b.get_attr('float'))
        self.assertEquals(self.stringval, b.get_attr('string'))
        self.assertEquals(self.dictval, b.get_attr('dict'))
        self.assertEquals(self.listval, b.get_attr('list'))

        # Reload directly
        b = Node(dbnode=a.dbnode)
        self.assertIsNone(a.get_attr('none'))
        self.assertEquals(self.boolval, b.get_attr('bool'))
        self.assertEquals(self.intval, b.get_attr('integer'))
        self.assertEquals(self.floatval, b.get_attr('float'))
        self.assertEquals(self.stringval, b.get_attr('string'))
        self.assertEquals(self.dictval, b.get_attr('dict'))
        self.assertEquals(self.listval, b.get_attr('list'))

        with self.assertRaises(ModificationNotAllowed):
            a._set_attr('i', 12)

    @unittest.skip("Not relevant")
    def test_attrs_and_extras_wrong_keyname(self):
        """
        Attribute keys cannot include the separator symbol in the key
        """

        separator = DbAttributeBaseClass._sep

        a = Node()

        with self.assertRaises(ValidationError):
            # I did not store, I cannot modify
            a._set_attr('name' + separator, 'blablabla')

        with self.assertRaises(ValidationError):
            # I did not store, I cannot modify
            a.set_extra('bool' + separator, 'blablabla')

    def test_attr_and_extras(self):
        a = Node()
        a._set_attr('bool', self.boolval)
        a._set_attr('integer', self.intval)
        a._set_attr('float', self.floatval)
        a._set_attr('string', self.stringval)
        a._set_attr('dict', self.dictval)
        a._set_attr('list', self.listval)

        with self.assertRaises(ModificationNotAllowed):
            # I did not store, I cannot modify
            a.set_extra('bool', 'blablabla')

        a.store()

        a_string = 'some non-boolean value'
        # I now set an extra with the same name of an attr
        a.set_extra('bool', a_string)
        # and I check that there is no name clash
        self.assertEquals(self.boolval, a.get_attr('bool'))
        self.assertEquals(a_string, a.get_extra('bool'))

    def test_attr_and_extras_multikey(self):
        """
        Multiple nodes with the same key. This should not be a problem

        I test only extras because the two tables are formally identical
        """
        n1 = Node().store()
        n2 = Node().store()

        n1.set_extra('samename', 1)
        # No problem, they are two different nodes
        n2.set_extra('samename', 1)

    @unittest.skip("Settings not implemented yet")
    def test_settings(self):
        """
        Test the settings table (similar to Attributes, but without the key.
        """
        from aiida.backends.djsite.db import models
        from django.db import IntegrityError, transaction

        models.DbSetting.set_value(key='pippo', value=[1, 2, 3])

        s1 = models.DbSetting.objects.get(key='pippo')

        self.assertEqual(s1.getvalue(), [1, 2, 3])

        s2 = models.DbSetting(key='pippo')

        sid = transaction.savepoint()
        with self.assertRaises(IntegrityError):
            # same name...
            s2.save()
        transaction.savepoint_rollback(sid)

        # Should replace pippo
        models.DbSetting.set_value(key='pippo', value="a")
        s1 = models.DbSetting.objects.get(key='pippo')

        self.assertEqual(s1.getvalue(), "a")

    @unittest.skip("Settings not implemented yet")
    def test_settings_methods(self):
        from aiida.common.globalsettings import (
            get_global_setting_description, get_global_setting,
            set_global_setting, del_global_setting)

        set_global_setting(key="aaa", value={'b': 'c'}, description="pippo")

        self.assertEqual(get_global_setting('aaa'), {'b': 'c'})
        self.assertEqual(get_global_setting_description('aaa'), "pippo")
        self.assertEqual(get_global_setting('aaa.b'), 'c')
        self.assertEqual(get_global_setting_description('aaa.b'), "")

        del_global_setting('aaa')

        with self.assertRaises(KeyError):
            get_global_setting('aaa.b')

        with self.assertRaises(KeyError):
            get_global_setting('aaa')

    def test_attr_listing(self):
        """
        Checks that the list of attributes and extras is ok.
        """
        a = Node()
        attrs_to_set = {
            'none': None,
            'bool': self.boolval,
            'integer': self.intval,
            'float': self.floatval,
            'string': self.stringval,
            'dict': self.dictval,
            'list': self.listval,
        }

        for k, v in attrs_to_set.iteritems():
            a._set_attr(k, v)

        a.store()

        # I now set extras
        extras_to_set = {
            'bool': 'some non-boolean value',
            'some_other_name': 987}

        for k, v in extras_to_set.iteritems():
            a.set_extra(k, v)

        self.assertEquals(set(a.attrs()),
                          set(attrs_to_set.keys()))
        self.assertEquals(set(a.extras()),
                          set(extras_to_set.keys()))

        returned_internal_attrs = {k: v for k, v in a.iterattrs()}
        self.assertEquals(returned_internal_attrs, attrs_to_set)

        returned_attrs = {k: v for k, v in a.iterextras()}
        self.assertEquals(returned_attrs, extras_to_set)


    def test_versioning_and_postsave_attributes(self):
        """
        Checks the versioning.
        """
        from aiida.orm.test import myNodeWithFields

        # Has 'state' as updatable attribute
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

        for k, v in attrs_to_set.iteritems():
            a._set_attr(k, v)

        # Check before storing
        self.assertEquals(267, a.get_attr('state'))

        a.store()

        # Check after storing
        self.assertEquals(267, a.get_attr('state'))

        # Even if I stored many attributes, this should stay at 1
        self.assertEquals(a.dbnode.nodeversion, 1)

        # I check increment on new version
        a.set_extra('a', 'b')
        self.assertEquals(a.dbnode.nodeversion, 2)

        # I check that I can set this attribute
        a._set_attr('state', 999)

        # I check increment on new version
        self.assertEquals(a.dbnode.nodeversion, 3)

        with self.assertRaises(ModificationNotAllowed):
            # I check that I cannot modify this attribute
            a._set_attr('otherattribute', 222)

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

    def test_delete_updatable_attributes(self):
        """
        Checks the versioning.
        """
        from aiida.orm.test import myNodeWithFields

        # Has 'state' as updatable attribute
        a = myNodeWithFields()
        attrs_to_set = {
            'bool': self.boolval,
            'integer': self.intval,
            'float': self.floatval,
            'string': self.stringval,
            'dict': self.dictval,
            'list': self.listval,
            'state': 267,  # updatable
        }

        for k, v in attrs_to_set.iteritems():
            a._set_attr(k, v)

        # Check before storing
        self.assertEquals(267, a.get_attr('state'))

        a.store()

        # Check after storing
        self.assertEquals(267, a.get_attr('state'))

        # Even if I stored many attributes, this should stay at 1
        self.assertEquals(a.dbnode.nodeversion, 1)

        # I should be able to delete the attribute
        a._del_attr('state')

        # I check increment on new version
        self.assertEquals(a.dbnode.nodeversion, 2)

        with self.assertRaises(AttributeError):
            # I check that I cannot modify this attribute
            _ = a.get_attr('state')


    def test_delete_extras(self):
        """
        Checks the ability of deleting extras, also when they are dictionaries
        or lists.
        """

        a = Node().store()
        extras_to_set = {
            'bool': self.boolval,
            'integer': self.intval,
            'float': self.floatval,
            'string': self.stringval,
            'dict': self.dictval,
            'list': self.listval,
            'further': 267,
        }

        for k, v in extras_to_set.iteritems():
            a.set_extra(k, v)

        self.assertEquals({k: v for k, v in a.iterextras()}, extras_to_set)

        # I pregenerate it, it cannot change during iteration
        list_keys = list(extras_to_set.keys())
        for k in list_keys:
            # I delete one by one the keys and check if the operation is
            # performed correctly
            a.del_extra(k)
            del extras_to_set[k]
            self.assertEquals({k: v for k, v in a.iterextras()}, extras_to_set)


    def test_replace_extras(self):
        """
        Checks the ability of replacing extras, removing the subkeys also when
        these are dictionaries or lists.
        """
        a = Node().store()
        extras_to_set = {
            'bool': True,
            'integer': 12,
            'float': 26.2,
            'string': "a string",
            'dict': {"a": "b",
                     "sublist": [1, 2, 3],
                     "subdict": {
                         "c": "d"}},
            'list': [1, True, "ggg", {'h': 'j'}, [9, 8, 7]],
        }

        # I redefine the keys with more complicated data, and
        # changing the data type too
        new_extras = {
            'bool': 12,
            'integer': [2, [3], 'a'],
            'float': {'n': 'm', 'x': [1, 'r', {}]},
            'string': True,
            'dict': 'text',
            'list': 66.3,
        }

        for k, v in extras_to_set.iteritems():
            a.set_extra(k, v)

        self.assertEquals({k: v for k, v in a.iterextras()}, extras_to_set)

        for k, v in new_extras.iteritems():
            # I delete one by one the keys and check if the operation is
            # performed correctly
            a.set_extra(k, v)

        # I update extras_to_set with the new entries, and do the comparison
        # again
        extras_to_set.update(new_extras)
        self.assertEquals({k: v for k, v in a.iterextras()}, extras_to_set)

    def test_versioning_lowlevel(self):
        """
        Checks the versioning.
        """
        from aiida.orm.test import myNodeWithFields

        a = myNodeWithFields()
        a.store()

        # Even if I stored many attributes, this should stay at 1
        self.assertEquals(a._dbnode.nodeversion, 1)
        self.assertEquals(a.dbnode.nodeversion, 1)
        self.assertEquals(a._dbnode.nodeversion, 1)

        a.label = "label1"
        a.label = "label2"
        self.assertEquals(a._dbnode.nodeversion, 3)
        self.assertEquals(a.dbnode.nodeversion, 3)
        self.assertEquals(a._dbnode.nodeversion, 3)

        a.description = "desc1"
        a.description = "desc2"
        a.description = "desc3"
        self.assertEquals(a._dbnode.nodeversion, 6)
        self.assertEquals(a.dbnode.nodeversion, 6)
        self.assertEquals(a._dbnode.nodeversion, 6)


    def test_comments(self):
        # This is the best way to compare dates with the stored ones, instead of
        # directly loading datetime.datetime.now(), or you can get a
        # "can't compare offset-naive and offset-aware datetimes" error
        user = get_automatic_user()
        a = Node()
        with self.assertRaises(ModificationNotAllowed):
            a.add_comment('text', user=user)
        self.assertEquals(a.get_comments(), [])
        a.store()
        before = timezone.now()
        time.sleep(1)  # I wait 1 second because MySql time precision is 1 sec
        a.add_comment('text', user=user)
        a.add_comment('text2', user=user)
        time.sleep(1)
        after = timezone.now()

        comments = a.get_comments()

        times = [i['mtime'] for i in comments]
        for t in times:
            self.assertTrue(t > before)
            self.assertTrue(t < after)

        self.assertEquals([(i['user__email'], i['content']) for i in comments],
                          [(user.email, 'text'),
                           (user.email, 'text2'), ])


    def test_load_nodes(self):
        """
        Test for load_node() function.
        """
        a = Node()
        a.store()

        self.assertEquals(a.pk, load_node(node_id=a.pk).pk)
        self.assertEquals(a.pk, load_node(node_id=a.uuid).pk)
        self.assertEquals(a.pk, load_node(pk=a.pk).pk)
        self.assertEquals(a.pk, load_node(uuid=a.uuid).pk)

        with self.assertRaises(ValueError):
            load_node(node_id=a.pk, pk=a.pk)
        with self.assertRaises(ValueError):
            load_node(pk=a.pk, uuid=a.uuid)
        with self.assertRaises(ValueError):
            load_node(pk=a.uuid)
        with self.assertRaises(NotExistent):
            load_node(uuid=a.pk)
        with self.assertRaises(ValueError):
            load_node()
