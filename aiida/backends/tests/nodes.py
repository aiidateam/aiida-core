# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=too-many-lines,invalid-name,protected-access
# pylint: disable=missing-docstring,too-many-locals,too-many-statements
# pylint: disable=too-many-public-methods
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
import copy
import io
import unittest

import six
from six.moves import range
from sqlalchemy.exc import StatementError

from aiida.backends.testbase import AiidaTestCase
from aiida.common.exceptions import InvalidOperation, ModificationNotAllowed, StoringNotAllowed
from aiida.common.links import LinkType
from aiida.manage.database.delete.nodes import delete_nodes
from aiida.orm import User, Data, Node
from aiida.orm.node.process import ProcessNode
from aiida.orm.node.process.calculation import CalculationNode
from aiida.orm.node.process.workflow import WorkflowNode
from aiida.orm.utils import load_node
from aiida.orm.convert import get_orm_entity
from aiida.common.utils import Capturing


class TestNodeIsStorable(AiidaTestCase):
    """
    Test if one can store specific Node subclasses, and that Node and
    ProcessType are not storable, intead.
    """

    def test_storable_unstorable(self):
        """
        Test storability of Nodes
        """
        node = Node()
        with self.assertRaises(StoringNotAllowed):
            node.store()

        process = ProcessNode()
        with self.assertRaises(StoringNotAllowed):
            process.store()

        # These below should be allowed instead
        data = Data()
        data.store()

        calc = CalculationNode()
        calc.store()

        work = WorkflowNode()
        work.store()


class TestNodeCopyDeepcopy(AiidaTestCase):
    """Test that calling copy and deepcopy on a Node does the right thing."""

    def test_copy_not_supported(self):
        """Copying a base Node instance is not supported."""
        node = Node()
        with self.assertRaises(InvalidOperation):
            clone = copy.copy(node)  # pylint: disable=unused_variable

    def test_copy_not_supported(self):
        """Deep copying a base Node instance is not supported."""
        node = Node()
        with self.assertRaises(InvalidOperation):
            clone = copy.deepcopy(node)  # pylint: disable=unused_variable


class TestNodeHashing(AiidaTestCase):
    """
    Tests the functionality of hashing a node
    """

    @staticmethod
    def create_simple_node(a, b=0, c=0):
        n = Data()
        n._set_attr('a', a)
        n._set_attr('b', b)
        n._set_attr('c', c)
        return n

    def test_simple_equal_nodes(self):
        attributes = [(1.0, 1.1, 1.2), ({'a': 'b', 'c': 'd'}, [1, 2, 3], {4, 1, 2})]
        for attr in attributes:
            n1 = self.create_simple_node(*attr)
            n2 = self.create_simple_node(*attr)
            n1.store(use_cache=True)
            n2.store(use_cache=True)
            self.assertEqual(n1.uuid, n2.get_extra('_aiida_cached_from'))

    def test_node_uuid_hashing_for_querybuidler(self):
        """
        QueryBuilder results should be reusable and shouldn't brake hashing.
        """
        from aiida.orm.querybuilder import QueryBuilder

        n = Data()
        n.store()

        # Search for the UUID of the stored node
        qb = QueryBuilder()
        qb.append(Data, project=['uuid'], filters={'id': {'==': n.id}})
        [uuid] = qb.first()

        # Look the node with the previously returned UUID
        qb = QueryBuilder()
        qb.append(Data, project=['id'], filters={'uuid': {'==': uuid}})

        # Check that the query doesn't fail
        qb.all()
        # And that the results are correct
        self.assertEquals(qb.count(), 1)
        self.assertEquals(qb.first()[0], n.id)

    @staticmethod
    def create_folderdata_with_empty_file():
        from aiida.orm.data.folder import FolderData
        res = FolderData()
        with res.folder.get_subfolder('path').open('name', 'w') as fhandle:
            pass
        return res

    @staticmethod
    def create_folderdata_with_empty_folder():
        from aiida.orm.data.folder import FolderData
        res = FolderData()
        res.folder.get_subfolder('path/name').create()
        return res

    def test_folder_file_different(self):
        f1 = self.create_folderdata_with_empty_file()
        f2 = self.create_folderdata_with_empty_folder()

        assert (
                f1.folder.get_subfolder('path').get_content_list() == f2.folder.get_subfolder(
            'path').get_content_list())
        assert f1.get_hash() != f2.get_hash()

    def test_folder_same(self):
        f1 = self.create_folderdata_with_empty_folder()
        f2 = self.create_folderdata_with_empty_folder()
        f1.store()
        f2.store(use_cache=True)
        assert f1.uuid == f2.get_extra('_aiida_cached_from')

    def test_file_same(self):
        f1 = self.create_folderdata_with_empty_file()
        f2 = self.create_folderdata_with_empty_file()
        f1.store()
        f2.store(use_cache=True)
        assert f1.uuid == f2.get_extra('_aiida_cached_from')

    def test_simple_unequal_nodes(self):
        attributes = [
            [(1.0, 1.1, 1.2), (2.0, 1.1, 1.2)],
            [(1e-14,), (2e-14,)],
        ]
        for attr1, attr2 in attributes:
            n1 = self.create_simple_node(*attr1)
            n2 = self.create_simple_node(*attr2)
            n1.store()
            n2.store(use_cache=True)
            self.assertNotEquals(n1.uuid, n2.uuid)
            self.assertFalse('_aiida_cached_from' in n2.extras())

    def test_unequal_arrays(self):
        import numpy as np
        from aiida.orm.data.array import ArrayData
        arrays = [(np.zeros(1001), np.zeros(1005)), (np.array([1, 2, 3]), np.array([2, 3, 4]))]

        def create_arraydata(arr):
            a = ArrayData()
            a.set_array('a', arr)
            return a

        for arr1, arr2 in arrays:
            a1 = create_arraydata(arr1)
            a1.store()
            a2 = create_arraydata(arr2)
            a2.store(use_cache=True)
            self.assertNotEquals(a1.uuid, a2.uuid)
            self.assertFalse('_aiida_cached_from' in a2.extras())

    def test_updatable_attributes(self):
        """
        Tests that updatable attributes are ignored.
        """
        node = ProcessNode()
        hash1 = node.get_hash()
        node._set_process_state('finished')
        hash2 = node.get_hash()
        self.assertNotEquals(hash1, None)
        self.assertEquals(hash1, hash2)


class TestTransitiveNoLoops(AiidaTestCase):
    """
    Test the transitive closure functionality
    """

    def test_loop_not_allowed(self):
        d1 = Data().store()
        c1 = CalculationNode().store()
        d2 = Data().store()
        c2 = CalculationNode().store()

        c1.add_incoming(d1, link_type=LinkType.INPUT_CALC, link_label='link')
        d2.add_incoming(c1, link_type=LinkType.CREATE, link_label='link')
        c2.add_incoming(d2, link_type=LinkType.INPUT_CALC, link_label='link')

        with self.assertRaises(ValueError):  # This would generate a loop
            d1.add_incoming(c2, link_type=LinkType.CREATE, link_label='link')


class TestTypes(AiidaTestCase):
    """
    Generic test class to test types
    """

    def test_uuid_type(self):
        """
        Checking whether the UUID is returned as a string. In old implementations it was returned as uuid type
        """
        from aiida.orm.querybuilder import QueryBuilder
        n1 = Data().store()
        n2 = Data().store()

        results = QueryBuilder().append(Data, project=('uuid', '*')).all()
        for uuid, data in results:
            self.assertTrue(isinstance(uuid, six.string_types))
            self.assertTrue(isinstance(data.uuid, six.string_types))


class TestQueryWithAiidaObjects(AiidaTestCase):
    """
    Test if queries work properly also with aiida.orm.Node classes instead of
    aiida.backends.djsite.db.models.DbNode objects.
    """

    def test_with_subclasses(self):
        from aiida.orm.querybuilder import QueryBuilder
        from aiida.orm import CalculationFactory, DataFactory
        from aiida.orm.node.process import CalcJobNode

        extra_name = self.__class__.__name__ + "/test_with_subclasses"
        calc_params = {'computer': self.computer, 'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 1}}

        TemplateReplacerCalc = CalculationFactory('templatereplacer')
        ParameterData = DataFactory('parameter')

        a1 = CalcJobNode(**calc_params).store()
        # To query only these nodes later
        a1.set_extra(extra_name, True)
        a3 = Data().store()
        a3.set_extra(extra_name, True)
        a4 = ParameterData(dict={'a': 'b'}).store()
        a4.set_extra(extra_name, True)
        # I don't set the extras, just to be sure that the filtering works
        # The filtering is needed because other tests will put stuff int he DB
        a6 = CalcJobNode(**calc_params)
        a6.store()
        a7 = Data()
        a7.store()

        # Query by calculation
        qb = QueryBuilder()
        qb.append(CalcJobNode, filters={'extras': {'has_key': extra_name}})
        results = [_ for [_] in qb.all()]
        # a3, a4 should not be found because they are not CalcJobNodes.
        # a6, a7 should not be found because they have not the attribute set.
        self.assertEquals(set([i.pk for i in results]), set([a1.pk]))

        # Same query, but by the generic Node class
        qb = QueryBuilder()
        qb.append(Node, filters={'extras': {'has_key': extra_name}})
        results = [_ for [_] in qb.all()]
        self.assertEquals(set([i.pk for i in results]), set([a1.pk, a3.pk, a4.pk]))

        # Same query, but by the Data class
        qb = QueryBuilder()
        qb.append(Data, filters={'extras': {'has_key': extra_name}})
        results = [_ for [_] in qb.all()]
        self.assertEquals(set([i.pk for i in results]), set([a3.pk, a4.pk]))

        # Same query, but by the ParameterData subclass
        qb = QueryBuilder()
        qb.append(ParameterData, filters={'extras': {'has_key': extra_name}})
        results = [_ for [_] in qb.all()]
        self.assertEquals(set([i.pk for i in results]), set([a4.pk]))


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
    dictval = {
        'num': 3,
        'something': 'else',
        'emptydict': {},
        'recursive': {
            'a': 1,
            'b': True,
            'c': 1.2,
            'd': [1, 2, None],
            'e': {
                'z': 'z',
                'x': None,
                'xx': {},
                'yy': []
            }
        }
    }
    listval = [1, "s", True, None]
    emptydict = {}
    emptylist = []

    def test_uuid_uniquess(self):
        """
        A uniqueness constraint on the UUID column of the Node model should prevent multiple nodes with identical UUID
        """
        from django.db import IntegrityError as DjIntegrityError
        from sqlalchemy.exc import IntegrityError as SqlaIntegrityError

        a = Data()
        b = Data()
        b._dbnode.uuid = a.uuid
        a.store()

        with self.assertRaises((DjIntegrityError, SqlaIntegrityError)):
            b.store()

    def test_attribute_mutability(self):
        """
        Attributes of a node should be immutable after storing, unless the stored_check is
        disabled in the call
        """
        a = Data()
        a._set_attr('bool', self.boolval)
        a._set_attr('integer', self.intval)
        a.store()

        # After storing attributes should now be immutable
        with self.assertRaises(ModificationNotAllowed):
            a._del_attr('bool')

        with self.assertRaises(ModificationNotAllowed):
            a._set_attr('integer', self.intval)

        # Passing stored_check=False should disable the mutability check
        a._del_attr('bool', stored_check=False)
        a._set_attr('integer', self.intval, stored_check=False)

        self.assertEquals(a.get_attr('integer'), self.intval)

        with self.assertRaises(AttributeError):
            a.get_attr('bool')

    def test_attr_before_storing(self):
        a = Data()
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

    def test_get_attrs_before_storing(self):
        a = Data()
        a._set_attr('k1', self.boolval)
        a._set_attr('k2', self.intval)
        a._set_attr('k3', self.floatval)
        a._set_attr('k4', self.stringval)
        a._set_attr('k5', self.dictval)
        a._set_attr('k6', self.listval)
        a._set_attr('k7', self.emptydict)
        a._set_attr('k8', self.emptylist)
        a._set_attr('k9', None)

        target_attrs = {
            'k1': self.boolval,
            'k2': self.intval,
            'k3': self.floatval,
            'k4': self.stringval,
            'k5': self.dictval,
            'k6': self.listval,
            'k7': self.emptydict,
            'k8': self.emptylist,
            'k9': None
        }

        # Now I check if I can retrieve them, before the storage
        self.assertEquals(a.get_attrs(), target_attrs)

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

        self.assertEquals(a.get_attrs(), {})

    def test_get_attrs_after_storing(self):
        a = Data()
        a._set_attr('k1', self.boolval)
        a._set_attr('k2', self.intval)
        a._set_attr('k3', self.floatval)
        a._set_attr('k4', self.stringval)
        a._set_attr('k5', self.dictval)
        a._set_attr('k6', self.listval)
        a._set_attr('k7', self.emptydict)
        a._set_attr('k8', self.emptylist)
        a._set_attr('k9', None)

        a.store()

        target_attrs = {
            'k1': self.boolval,
            'k2': self.intval,
            'k3': self.floatval,
            'k4': self.stringval,
            'k5': self.dictval,
            'k6': self.listval,
            'k7': self.emptydict,
            'k8': self.emptylist,
            'k9': None
        }

        # Now I check if I can retrieve them, before the storage
        self.assertEquals(a.get_attrs(), target_attrs)

    def test_store_object(self):
        """Trying to store objects should fail"""
        a = Data()
        a._set_attr('object', object(), clean=False)

        # django raises ValueError
        # sqlalchemy raises StatementError
        with self.assertRaises((ValueError, StatementError)):
            a.store()

        b = Data()
        b._set_attr('object_list', [object(), object()], clean=False)
        with self.assertRaises((ValueError, StatementError)):
            # objects are not json-serializable
            b.store()

    def test_append_to_empty_attr(self):
        """Appending to an empty attribute"""
        a = Data()
        a._append_to_attr('test', 0)
        a._append_to_attr('test', 1)

        self.assertEquals(a.get_attr('test'), [0, 1])

    def test_append_no_side_effects(self):
        """Check that _append_to_attr has no side effects"""
        a = Data()
        mylist = [1, 2, 3]

        a._set_attr('list', mylist)
        a._append_to_attr('list', 4)

        self.assertEquals(a.get_attr('list'), [1, 2, 3, 4])
        self.assertEquals(mylist, [1, 2, 3])

    def test_datetime_attribute(self):
        from aiida.common.timezone import (get_current_timezone, is_naive, make_aware, now)

        a = Data()

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

    def test_attributes_on_clone(self):
        import copy

        a = Data()
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

        for k, v in attrs_to_set.items():
            a._set_attr(k, v)

        # Create a copy
        b = copy.deepcopy(a)
        # I modify an attribute and add a new one; I mirror it in the dictionary
        # for later checking
        b_expected_attributes = copy.deepcopy(attrs_to_set)
        b._set_attr('integer', 489)
        b_expected_attributes['integer'] = 489
        b._set_attr('new', 'cvb')
        b_expected_attributes['new'] = 'cvb'

        # I check before storing that the attributes are ok
        self.assertEquals({k: v for k, v in b.iterattrs()}, b_expected_attributes)
        # Note that during copy, I do not copy the extras!
        self.assertEquals({k: v for k, v in b.iterextras()}, {})

        # I store now
        b.store()
        # and I finally add a extras
        b.set_extra('meta', 'textofext')
        b_expected_extras = {'meta': 'textofext', '_aiida_hash': AnyValue()}

        # Now I check that the attributes of the original node have not changed
        self.assertEquals({k: v for k, v in a.iterattrs()}, attrs_to_set)

        # I check then on the 'b' copy
        self.assertEquals({k: v for k, v in b.iterattrs()}, b_expected_attributes)
        self.assertEquals({k: v for k, v in b.iterextras()}, b_expected_extras)

    def test_files(self):
        import tempfile

        a = Data()

        file_content = 'some text ABCDE'
        file_content_different = 'other values 12345'

        with tempfile.NamedTemporaryFile(mode='w+') as tmpf:
            tmpf.write(file_content)
            tmpf.flush()
            a.add_path(tmpf.name, 'file1.txt')
            a.add_path(tmpf.name, 'file2.txt')

        self.assertEquals(set(a.get_folder_list()), set(['file1.txt', 'file2.txt']))
        with io.open(a.get_abs_path('file1.txt'), encoding='utf8') as fhandle:
            self.assertEquals(fhandle.read(), file_content)
        with io.open(a.get_abs_path('file2.txt'), encoding='utf8') as fhandle:
            self.assertEquals(fhandle.read(), file_content)

        b = a.clone()
        self.assertNotEquals(a.uuid, b.uuid)

        # Check that the content is there
        self.assertEquals(set(b.get_folder_list()), set(['file1.txt', 'file2.txt']))
        with io.open(b.get_abs_path('file1.txt'), encoding='utf8') as fhandle:
            self.assertEquals(fhandle.read(), file_content)
        with io.open(b.get_abs_path('file2.txt'), encoding='utf8') as fhandle:
            self.assertEquals(fhandle.read(), file_content)

        # I overwrite a file and create a new one in the clone only
        with tempfile.NamedTemporaryFile(mode='w+') as tmpf:
            tmpf.write(file_content_different)
            tmpf.flush()
            b.add_path(tmpf.name, 'file2.txt')
            b.add_path(tmpf.name, 'file3.txt')

        # I check the new content, and that the old one has not changed
        self.assertEquals(set(a.get_folder_list()), set(['file1.txt', 'file2.txt']))
        with io.open(a.get_abs_path('file1.txt'), encoding='utf8') as fhandle:
            self.assertEquals(fhandle.read(), file_content)
        with io.open(a.get_abs_path('file2.txt'), encoding='utf8') as fhandle:
            self.assertEquals(fhandle.read(), file_content)
        self.assertEquals(set(b.get_folder_list()), set(['file1.txt', 'file2.txt', 'file3.txt']))
        with io.open(b.get_abs_path('file1.txt'), encoding='utf8') as fhandle:
            self.assertEquals(fhandle.read(), file_content)
        with io.open(b.get_abs_path('file2.txt'), encoding='utf8') as fhandle:
            self.assertEquals(fhandle.read(), file_content_different)
        with io.open(b.get_abs_path('file3.txt'), encoding='utf8') as fhandle:
            self.assertEquals(fhandle.read(), file_content_different)

        # This should in principle change the location of the files,
        # so I recheck
        a.store()

        # I now clone after storing
        c = a.clone()
        # I overwrite a file and create a new one in the clone only
        with tempfile.NamedTemporaryFile(mode='w+') as tmpf:
            tmpf.write(file_content_different)
            tmpf.flush()
            c.add_path(tmpf.name, 'file1.txt')
            c.add_path(tmpf.name, 'file4.txt')

        self.assertEquals(set(a.get_folder_list()), set(['file1.txt', 'file2.txt']))
        with io.open(a.get_abs_path('file1.txt'), encoding='utf8') as fhandle:
            self.assertEquals(fhandle.read(), file_content)
        with io.open(a.get_abs_path('file2.txt'), encoding='utf8') as fhandle:
            self.assertEquals(fhandle.read(), file_content)

        self.assertEquals(set(c.get_folder_list()), set(['file1.txt', 'file2.txt', 'file4.txt']))
        with io.open(c.get_abs_path('file1.txt'), encoding='utf8') as fhandle:
            self.assertEquals(fhandle.read(), file_content_different)
        with io.open(c.get_abs_path('file2.txt'), encoding='utf8') as fhandle:
            self.assertEquals(fhandle.read(), file_content)
        with io.open(c.get_abs_path('file4.txt'), encoding='utf8') as fhandle:
            self.assertEquals(fhandle.read(), file_content_different)

    def test_folders(self):
        """
        Similar as test_files, but I manipulate a tree of folders
        """
        import tempfile
        import os
        import shutil
        import random
        import string

        a = Data()

        # Since Node uses the same method of Folder(),
        # for this test I create a test folder by hand
        # For any non-test usage, use SandboxFolder()!

        directory = os.path.realpath(os.path.join('/', 'tmp', 'tmp_try'))
        while os.path.exists(os.path.join(directory)):
            # I append a random letter/number until it is unique
            directory += random.choice(string.ascii_uppercase + string.digits)

        # create a folder structure to copy around
        tree_1 = os.path.join(directory, 'tree_1')
        os.makedirs(tree_1)
        file_content = u'some text ABCDE'
        file_content_different = u'other values 12345'
        with io.open(os.path.join(tree_1, 'file1.txt'), 'w', encoding='utf8') as fhandle:
            fhandle.write(file_content)
        os.mkdir(os.path.join(tree_1, 'dir1'))
        os.mkdir(os.path.join(tree_1, 'dir1', 'dir2'))
        with io.open(os.path.join(tree_1, 'dir1', 'file2.txt'), 'w', encoding='utf8') as fhandle:
            fhandle.write(file_content)
        os.mkdir(os.path.join(tree_1, 'dir1', 'dir2', 'dir3'))

        # add the tree to the node

        a.add_path(tree_1, 'tree_1')

        # verify if the node has the structure I expect
        self.assertEquals(set(a.get_folder_list()), set(['tree_1']))
        self.assertEquals(set(a.get_folder_list('tree_1')), set(['file1.txt', 'dir1']))
        self.assertEquals(set(a.get_folder_list(os.path.join('tree_1', 'dir1'))), set(['dir2', 'file2.txt']))
        with io.open(a.get_abs_path(os.path.join('tree_1', 'file1.txt')), encoding='utf8') as fhandle:
            self.assertEquals(fhandle.read(), file_content)
        with io.open(a.get_abs_path(os.path.join('tree_1', 'dir1', 'file2.txt')), encoding='utf8') as fhandle:
            self.assertEquals(fhandle.read(), file_content)

        # try to exit from the folder
        with self.assertRaises(ValueError):
            a.get_folder_list('..')

        # clone into a new node
        b = a.clone()
        self.assertNotEquals(a.uuid, b.uuid)

        # Check that the content is there
        self.assertEquals(set(b.get_folder_list('.')), set(['tree_1']))
        self.assertEquals(set(b.get_folder_list('tree_1')), set(['file1.txt', 'dir1']))
        self.assertEquals(set(b.get_folder_list(os.path.join('tree_1', 'dir1'))), set(['dir2', 'file2.txt']))
        with io.open(b.get_abs_path(os.path.join('tree_1', 'file1.txt')), encoding='utf8') as fhandle:
            self.assertEquals(fhandle.read(), file_content)
        with io.open(b.get_abs_path(os.path.join('tree_1', 'dir1', 'file2.txt')), encoding='utf8') as fhandle:
            self.assertEquals(fhandle.read(), file_content)

        # I overwrite a file and create a new one in the copy only
        dir3 = os.path.join(directory, 'dir3')
        os.mkdir(dir3)

        b.add_path(dir3, os.path.join('tree_1', 'dir3'))
        # no absolute path here
        with self.assertRaises(ValueError):
            b.add_path('dir3', os.path.join('tree_1', 'dir3'))

        with tempfile.NamedTemporaryFile(mode='w+') as tmpf:
            tmpf.write(file_content_different)
            tmpf.flush()
            b.add_path(tmpf.name, 'file3.txt')

        # I check the new content, and that the old one has not changed
        # old
        self.assertEquals(set(a.get_folder_list('.')), set(['tree_1']))
        self.assertEquals(set(a.get_folder_list('tree_1')), set(['file1.txt', 'dir1']))
        self.assertEquals(set(a.get_folder_list(os.path.join('tree_1', 'dir1'))), set(['dir2', 'file2.txt']))
        with io.open(a.get_abs_path(os.path.join('tree_1', 'file1.txt')), encoding='utf8') as fhandle:
            self.assertEquals(fhandle.read(), file_content)
        with io.open(a.get_abs_path(os.path.join('tree_1', 'dir1', 'file2.txt')), encoding='utf8') as fhandle:
            self.assertEquals(fhandle.read(), file_content)
        # new
        self.assertEquals(set(b.get_folder_list('.')), set(['tree_1', 'file3.txt']))
        self.assertEquals(set(b.get_folder_list('tree_1')), set(['file1.txt', 'dir1', 'dir3']))
        self.assertEquals(set(b.get_folder_list(os.path.join('tree_1', 'dir1'))), set(['dir2', 'file2.txt']))
        with io.open(b.get_abs_path(os.path.join('tree_1', 'file1.txt')), encoding='utf8') as fhandle:
            self.assertEquals(fhandle.read(), file_content)
        with io.open(b.get_abs_path(os.path.join('tree_1', 'dir1', 'file2.txt')), encoding='utf8') as fhandle:
            self.assertEquals(fhandle.read(), file_content)

        # This should in principle change the location of the files,
        # so I recheck
        a.store()

        # I now copy after storing
        c = a.clone()
        # I overwrite a file, create a new one and remove a directory
        # in the copy only
        with tempfile.NamedTemporaryFile(mode='w+') as tmpf:
            tmpf.write(file_content_different)
            tmpf.flush()
            c.add_path(tmpf.name, os.path.join('tree_1', 'file1.txt'))
            c.add_path(tmpf.name, os.path.join('tree_1', 'dir1', 'file4.txt'))
        c.remove_path(os.path.join('tree_1', 'dir1', 'dir2'))

        # check old
        self.assertEquals(set(a.get_folder_list('.')), set(['tree_1']))
        self.assertEquals(set(a.get_folder_list('tree_1')), set(['file1.txt', 'dir1']))
        self.assertEquals(set(a.get_folder_list(os.path.join('tree_1', 'dir1'))), set(['dir2', 'file2.txt']))
        with io.open(a.get_abs_path(os.path.join('tree_1', 'file1.txt')), encoding='utf8') as fhandle:
            self.assertEquals(fhandle.read(), file_content)
        with io.open(a.get_abs_path(os.path.join('tree_1', 'dir1', 'file2.txt')), encoding='utf8') as fhandle:
            self.assertEquals(fhandle.read(), file_content)

        # check new
        self.assertEquals(set(c.get_folder_list('.')), set(['tree_1']))
        self.assertEquals(set(c.get_folder_list('tree_1')), set(['file1.txt', 'dir1']))
        self.assertEquals(set(c.get_folder_list(os.path.join('tree_1', 'dir1'))), set(['file2.txt', 'file4.txt']))
        with io.open(c.get_abs_path(os.path.join('tree_1', 'file1.txt'))) as fhandle:
            self.assertEquals(fhandle.read(), file_content_different)
        with io.open(c.get_abs_path(os.path.join('tree_1', 'dir1', 'file2.txt')), encoding='utf8') as fhandle:
            self.assertEquals(fhandle.read(), file_content)

        # garbage cleaning
        shutil.rmtree(directory)

    def test_attr_after_storing(self):
        a = Data()
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

    def test_attr_with_reload(self):
        a = Data()
        a._set_attr('none', None)
        a._set_attr('bool', self.boolval)
        a._set_attr('integer', self.intval)
        a._set_attr('float', self.floatval)
        a._set_attr('string', self.stringval)
        a._set_attr('dict', self.dictval)
        a._set_attr('list', self.listval)

        a.store()

        b = load_node(uuid=a.uuid)
        self.assertIsNone(a.get_attr('none'))
        self.assertEquals(self.boolval, b.get_attr('bool'))
        self.assertEquals(self.intval, b.get_attr('integer'))
        self.assertEquals(self.floatval, b.get_attr('float'))
        self.assertEquals(self.stringval, b.get_attr('string'))
        self.assertEquals(self.dictval, b.get_attr('dict'))
        self.assertEquals(self.listval, b.get_attr('list'))

        # Reload directly
        b = Data(dbnode=a.dbnode)
        self.assertIsNone(a.get_attr('none'))
        self.assertEquals(self.boolval, b.get_attr('bool'))
        self.assertEquals(self.intval, b.get_attr('integer'))
        self.assertEquals(self.floatval, b.get_attr('float'))
        self.assertEquals(self.stringval, b.get_attr('string'))
        self.assertEquals(self.dictval, b.get_attr('dict'))
        self.assertEquals(self.listval, b.get_attr('list'))

    def test_attr_and_extras(self):
        a = Data()
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

        self.assertEquals(a.get_extras(), {'bool': a_string, '_aiida_hash': AnyValue()})

    def test_get_extras_with_default(self):
        a = Data()
        a.store()
        a.set_extra('a', 'b')

        self.assertEquals(a.get_extra('a'), 'b')
        with self.assertRaises(AttributeError):
            a.get_extra('c')

        self.assertEquals(a.get_extra('c', 'def'), 'def')

    def test_attr_and_extras_multikey(self):
        """
        Multiple nodes with the same key. This should not be a problem

        I test only extras because the two tables are formally identical
        """
        n1 = Data().store()
        n2 = Data().store()

        n1.set_extra('samename', 1)
        # No problem, they are two different nodes
        n2.set_extra('samename', 1)

    def test_settings_methods(self):
        from aiida.backends.utils import (get_global_setting_description, get_global_setting, set_global_setting,
                                          del_global_setting)

        set_global_setting(key="aaa", value={'b': 'c'}, description="pippo")

        self.assertEqual(get_global_setting('aaa'), {'b': 'c'})
        self.assertEqual(get_global_setting_description('aaa'), "pippo")
        self.assertEqual(get_global_setting('aaa.b'), 'c')

        # The following is disabled because it is not supported in SQLAlchemy
        # Only top level elements can have descriptions
        # self.assertEqual(get_global_setting_description('aaa.b'), "")

        del_global_setting('aaa')

        with self.assertRaises(KeyError):
            get_global_setting('aaa.b')

        with self.assertRaises(KeyError):
            get_global_setting('aaa')

    def test_attr_listing(self):
        """
        Checks that the list of attributes and extras is ok.
        """
        a = Data()
        attrs_to_set = {
            'none': None,
            'bool': self.boolval,
            'integer': self.intval,
            'float': self.floatval,
            'string': self.stringval,
            'dict': self.dictval,
            'list': self.listval,
        }

        for k, v in attrs_to_set.items():
            a._set_attr(k, v)

        a.store()

        # I now set extras
        extras_to_set = {'bool': 'some non-boolean value', 'some_other_name': 987}

        for k, v in extras_to_set.items():
            a.set_extra(k, v)

        all_extras = dict(_aiida_hash=AnyValue(), **extras_to_set)

        self.assertEquals(set(a.attrs()), set(attrs_to_set.keys()))
        self.assertEquals(set(a.extras()), set(all_extras.keys()))

        returned_internal_attrs = {k: v for k, v in a.iterattrs()}
        self.assertEquals(returned_internal_attrs, attrs_to_set)

        returned_attrs = {k: v for k, v in a.iterextras()}
        self.assertEquals(returned_attrs, all_extras)

    def test_versioning(self):
        """
        Test the versioning of the node when setting attributes and extras
        """
        a = Data()
        attrs_to_set = {
            'bool': self.boolval,
            'integer': self.intval,
            'float': self.floatval,
            'string': self.stringval,
            'dict': self.dictval,
            'list': self.listval,
        }

        for key, value in attrs_to_set.items():
            a._set_attr(key, value)
            self.assertEquals(a.get_attr(key), value)

        a.store()

        # Check after storing
        for key, value in attrs_to_set.items():
            self.assertEquals(a.get_attr(key), value)

        # Even if I stored many attributes, this should stay at 1
        self.assertEquals(a.dbnode.nodeversion, 1)

        # I check increment on new version
        a.set_extra('a', 'b')
        self.assertEquals(a.dbnode.nodeversion, 2)

        # In both cases, the node version must increase
        a.label = 'test'
        self.assertEquals(a.dbnode.nodeversion, 3)

        a.description = 'test description'
        self.assertEquals(a.dbnode.nodeversion, 4)

    def test_delete_extras(self):
        """
        Checks the ability of deleting extras, also when they are dictionaries
        or lists.
        """

        a = Data().store()
        extras_to_set = {
            'bool': self.boolval,
            'integer': self.intval,
            'float': self.floatval,
            'string': self.stringval,
            'dict': self.dictval,
            'list': self.listval,
            'further': 267,
        }

        all_extras = dict(_aiida_hash=AnyValue(), **extras_to_set)

        for k, v in extras_to_set.items():
            a.set_extra(k, v)

        self.assertEquals({k: v for k, v in a.iterextras()}, all_extras)

        # I pregenerate it, it cannot change during iteration
        list_keys = list(extras_to_set.keys())
        for k in list_keys:
            # I delete one by one the keys and check if the operation is
            # performed correctly
            a.del_extra(k)
            del all_extras[k]
            self.assertEquals({k: v for k, v in a.iterextras()}, all_extras)

    def test_replace_extras_1(self):
        """
        Checks the ability of replacing extras, removing the subkeys also when
        these are dictionaries or lists.
        """
        a = Data().store()
        extras_to_set = {
            'bool': True,
            'integer': 12,
            'float': 26.2,
            'string': "a string",
            'dict': {
                "a": "b",
                "sublist": [1, 2, 3],
                "subdict": {
                    "c": "d"
                }
            },
            'list': [1, True, "ggg", {
                'h': 'j'
            }, [9, 8, 7]],
        }
        all_extras = dict(_aiida_hash=AnyValue(), **extras_to_set)

        # I redefine the keys with more complicated data, and
        # changing the data type too
        new_extras = {
            'bool': 12,
            'integer': [2, [3], 'a'],
            'float': {
                'n': 'm',
                'x': [1, 'r', {}]
            },
            'string': True,
            'dict': 'text',
            'list': 66.3,
        }

        for k, v in extras_to_set.items():
            a.set_extra(k, v)

        self.assertEquals({k: v for k, v in a.iterextras()}, all_extras)

        for k, v in new_extras.items():
            # I delete one by one the keys and check if the operation is
            # performed correctly
            a.set_extra(k, v)

        # I update extras_to_set with the new entries, and do the comparison
        # again
        all_extras.update(new_extras)
        self.assertEquals({k: v for k, v in a.iterextras()}, all_extras)

    def test_basetype_as_attr(self):
        """
        Test that setting a basetype as an attribute works transparently
        """
        from aiida.orm.data.list import List
        from aiida.orm.data.parameter import ParameterData
        from aiida.orm.data.str import Str

        # This one is unstored
        l1 = List()
        l1.set_list(['b', [1, 2]])

        # This one is stored
        l2 = List()
        l2.set_list(['f', True, {'gg': None}])
        l2.store()

        # Manages to store, and value is converted to its base type
        p = ParameterData(dict={'b': Str("sometext"), 'c': l1})
        p.store()
        self.assertEqual(p.get_attr('b'), "sometext")
        self.assertIsInstance(p.get_attr('b'), six.string_types)
        self.assertEqual(p.get_attr('c'), ['b', [1, 2]])
        self.assertIsInstance(p.get_attr('c'), (list, tuple))

        # Check also before storing
        n = Data()
        n._set_attr('a', Str("sometext2"))
        n._set_attr('b', l2)
        self.assertEqual(n.get_attr('a'), "sometext2")
        self.assertIsInstance(n.get_attr('a'), six.string_types)
        self.assertEqual(n.get_attr('b'), ['f', True, {'gg': None}])
        self.assertIsInstance(n.get_attr('b'), (list, tuple))

        # Check also deep in a dictionary/list
        n = Data()
        n._set_attr('a', {'b': [Str("sometext3")]})
        self.assertEqual(n.get_attr('a')['b'][0], "sometext3")
        self.assertIsInstance(n.get_attr('a')['b'][0], six.string_types)
        n.store()
        self.assertEqual(n.get_attr('a')['b'][0], "sometext3")
        self.assertIsInstance(n.get_attr('a')['b'][0], six.string_types)

    def test_basetype_as_extra(self):
        """
        Test that setting a basetype as an attribute works transparently
        """
        from aiida.orm.data.list import List
        from aiida.orm.data.str import Str

        # This one is unstored
        l1 = List()
        l1.set_list(['b', [1, 2]])

        # This one is stored
        l2 = List()
        l2.set_list(['f', True, {'gg': None}])
        l2.store()

        # Check also before storing
        n = Data()
        n.store()
        n.set_extra('a', Str("sometext2"))
        n.set_extra('c', l1)
        n.set_extra('d', l2)
        self.assertEqual(n.get_extra('a'), "sometext2")
        self.assertIsInstance(n.get_extra('a'), six.string_types)
        self.assertEqual(n.get_extra('c'), ['b', [1, 2]])
        self.assertIsInstance(n.get_extra('c'), (list, tuple))
        self.assertEqual(n.get_extra('d'), ['f', True, {'gg': None}])
        self.assertIsInstance(n.get_extra('d'), (list, tuple))

        # Check also deep in a dictionary/list
        n = Data()
        n.store()
        n.set_extra('a', {'b': [Str("sometext3")]})
        self.assertEqual(n.get_extra('a')['b'][0], "sometext3")
        self.assertIsInstance(n.get_extra('a')['b'][0], six.string_types)

    def test_versioning_lowlevel(self):
        """
        Checks the versioning.
        """
        a = Data()
        a.store()

        # Even if I stored many attributes, this should stay at 1
        self.assertEquals(a.nodeversion, 1)
        self.assertEquals(a.nodeversion, 1)
        self.assertEquals(a.nodeversion, 1)

        a.label = "label1"
        a.label = "label2"
        self.assertEquals(a.nodeversion, 3)
        self.assertEquals(a.nodeversion, 3)
        self.assertEquals(a.nodeversion, 3)

        a.description = "desc1"
        a.description = "desc2"
        a.description = "desc3"
        self.assertEquals(a.nodeversion, 6)
        self.assertEquals(a.nodeversion, 6)
        self.assertEquals(a.nodeversion, 6)

    def test_comments(self):
        # This is the best way to compare dates with the stored ones, instead
        # of directly loading datetime.datetime.now(), or you can get a
        # "can't compare offset-naive and offset-aware datetimes" error
        from datetime import timedelta
        from aiida.common import timezone
        from time import sleep

        user = User.objects.get_default()

        a = Data()
        with self.assertRaises(ModificationNotAllowed):
            a.add_comment('text', user=user)

        a.store()
        self.assertEquals(a.get_comments(), [])

        before = timezone.now() - timedelta(seconds=1)
        a.add_comment('text', user=user)
        sleep(0.1)
        a.add_comment('text2', user=user)
        after = timezone.now() + timedelta(seconds=1)

        # Make sure comments are sorted to avoid
        # random test failures
        comments = sorted(a.get_comments(), key=lambda comment: comment.ctime)

        times = [i.ctime for i in comments]

        for time in times:
            self.assertTrue(time > before)
            self.assertTrue(time < after)

        self.assertEquals([(i.user.email, i.content) for i in comments], [
            (self.user_email, 'text'),
            (self.user_email, 'text2'),
        ])

    def test_code_loading_from_string(self):
        """
        Checks that the method Code.get_from_string works correctly.
        """
        from aiida.orm.code import Code
        from aiida.common.exceptions import NotExistent, MultipleObjectsError, InputValidationError

        # Create some code nodes
        code1 = Code()
        code1.set_remote_computer_exec((self.computer, '/bin/true'))
        code1.label = 'test_code1'
        code1.store()

        code2 = Code()
        code2.set_remote_computer_exec((self.computer, '/bin/true'))
        code2.label = 'test_code2'
        code2.store()

        # Test that the code1 can be loaded correctly with its label
        q_code_1 = Code.get_from_string(code1.label)
        self.assertEquals(q_code_1.id, code1.id)
        self.assertEquals(q_code_1.label, code1.label)
        self.assertEquals(q_code_1.get_remote_exec_path(), code1.get_remote_exec_path())

        # Test that the code2 can be loaded correctly with its label
        q_code_2 = Code.get_from_string(code2.label + '@' + self.computer.get_name())
        self.assertEquals(q_code_2.id, code2.id)
        self.assertEquals(q_code_2.label, code2.label)
        self.assertEquals(q_code_2.get_remote_exec_path(), code2.get_remote_exec_path())

        # Calling get_from_string for a non string type raises exception
        with self.assertRaises(InputValidationError):
            Code.get_from_string(code1.id)

        # Test that the lookup of a nonexistent code works as expected
        with self.assertRaises(NotExistent):
            Code.get_from_string('nonexistent_code')

        # Add another code with the label of code1
        code3 = Code()
        code3.set_remote_computer_exec((self.computer, '/bin/true'))
        code3.label = 'test_code1'
        code3.store()

        # Query with the common label
        with self.assertRaises(MultipleObjectsError):
            Code.get_from_string(code3.label)

    def test_get_subclass_from_pk(self):
        """
        This test checks that
        aiida.orm.implementation.general.node.AbstractNode#get_subclass_from_pk
        works correctly for both backends.
        """
        a1 = Data().store()

        # Check that you can load it with a simple integer id.
        a2 = Node.get_subclass_from_pk(a1.id)
        self.assertEquals(a1.id, a2.id, "The ids of the stored and loaded node"
                                        "should be equal (since it should be "
                                        "the same node")

        if six.PY2:  # In Python 3, int is always long (enough)
            # Check that you can load it with an id of type long
            a3 = Node.get_subclass_from_pk(long(a1.id))
            self.assertEquals(a1.id, a3.id, "The ids of the stored and loaded node"
                                            "should be equal (since it should be "
                                            "the same node")

        # Check that it manages to load the node even if the id is
        # passed as a string.
        a4 = Node.get_subclass_from_pk(str(a1.id))
        self.assertEquals(a1.id, a4.id, "The ids of the stored and loaded node"
                                        "should be equal (since it should be "
                                        "the same node")

        # Check that a ValueError exception is raised when a string that can
        # not be casted to integer is passed.
        with self.assertRaises(ValueError):
            Node.get_subclass_from_pk("not_existing_node")

        # Check that a NotExistent exception is raised when an unknown id
        # is passed.
        from aiida.common.exceptions import NotExistent
        with self.assertRaises(NotExistent):
            Node.get_subclass_from_pk(9999999999)

        # Check that we get a NotExistent exception if we try to load an
        # instance of a node that doesn't correspond to the Class used to
        # load it.
        from aiida.orm.code import Code
        with self.assertRaises(NotExistent):
            Code.get_subclass_from_pk(a1.id)

    def test_code_loading_using_get(self):
        """
        Checks that the method Code.get(pk) works correctly.
        """
        from aiida.orm.code import Code
        from aiida.common.exceptions import NotExistent, MultipleObjectsError

        # Create some code nodes
        code1 = Code()
        code1.set_remote_computer_exec((self.computer, '/bin/true'))
        code1.label = 'test_code3'
        code1.store()

        code2 = Code()
        code2.set_remote_computer_exec((self.computer, '/bin/true'))
        code2.label = 'test_code4'
        code2.store()

        # Test that the code1 can be loaded correctly with its label only
        q_code_1 = Code.get(label=code1.label)
        self.assertEquals(q_code_1.id, code1.id)
        self.assertEquals(q_code_1.label, code1.label)
        self.assertEquals(q_code_1.get_remote_exec_path(), code1.get_remote_exec_path())

        # Test that the code1 can be loaded correctly with its id/pk
        q_code_1 = Code.get(code1.id)
        self.assertEquals(q_code_1.id, code1.id)
        self.assertEquals(q_code_1.label, code1.label)
        self.assertEquals(q_code_1.get_remote_exec_path(), code1.get_remote_exec_path())

        # Test that the code2 can be loaded correctly with its label and computername
        q_code_2 = Code.get(label=code2.label, machinename=self.computer.get_name())
        self.assertEquals(q_code_2.id, code2.id)
        self.assertEquals(q_code_2.label, code2.label)
        self.assertEquals(q_code_2.get_remote_exec_path(), code2.get_remote_exec_path())

        # Test that the code2 can be loaded correctly with its id/pk
        q_code_2 = Code.get(code2.id)
        self.assertEquals(q_code_2.id, code2.id)
        self.assertEquals(q_code_2.label, code2.label)
        self.assertEquals(q_code_2.get_remote_exec_path(), code2.get_remote_exec_path())

        # Test that the lookup of a nonexistent code works as expected
        with self.assertRaises(NotExistent):
            Code.get(label='nonexistent_code')

        # Add another code with the label of code1
        code3 = Code()
        code3.set_remote_computer_exec((self.computer, '/bin/true'))
        code3.label = 'test_code3'
        code3.store()

        # Query with the common label
        with self.assertRaises(MultipleObjectsError):
            Code.get(label=code3.label)

        # Add another code whose label is equal to pk of another code
        pk_label_duplicate = code1.pk
        code4 = Code()
        code4.set_remote_computer_exec((self.computer, '/bin/true'))
        code4.label = pk_label_duplicate
        code4.store()

        # Since the label of code4 is identical to the pk of code1, calling
        # Code.get(pk_label_duplicate) should return code1, as the pk takes
        # precedence
        q_code_4 = Code.get(code4.label)
        self.assertEquals(q_code_4.id, code1.id)
        self.assertEquals(q_code_4.label, code1.label)
        self.assertEquals(q_code_4.get_remote_exec_path(), code1.get_remote_exec_path())

    def test_code_description(self):
        """
        This test checks that the code description is retrieved correctly
        when the code is searched with its id and label.
        """
        from aiida.orm.code import Code

        # Create a code node
        code = Code()
        code.set_remote_computer_exec((self.computer, '/bin/true'))
        code.label = 'test_code_label'
        code.description = 'test code description'
        code.store()

        q_code1 = Code.get(label=code.label)
        self.assertEquals(code.description, str(q_code1.description))

        q_code2 = Code.get(code.id)
        self.assertEquals(code.description, str(q_code2.description))

    def test_list_for_plugin(self):
        """
        This test checks the Code.list_for_plugin()
        """
        from aiida.orm.code import Code

        code1 = Code()
        code1.set_remote_computer_exec((self.computer, '/bin/true'))
        code1.label = 'test_code1'
        code1.set_input_plugin_name('plugin_name')
        code1.store()

        code2 = Code()
        code2.set_remote_computer_exec((self.computer, '/bin/true'))
        code2.label = 'test_code2'
        code2.set_input_plugin_name('plugin_name')
        code2.store()

        retrieved_pks = set(Code.list_for_plugin('plugin_name', labels=False))
        self.assertEqual(retrieved_pks, set([code1.pk, code2.pk]))

        retrieved_labels = set(Code.list_for_plugin('plugin_name', labels=True))
        self.assertEqual(retrieved_labels, set([code1.label, code2.label]))

    def test_load_node(self):
        """
        Tests the load node functionality
        """
        from aiida.orm.data.array import ArrayData
        from aiida.common.exceptions import NotExistent

        # I only need one node to test
        node = Data().store()
        uuid_stored = node.uuid  # convenience to store the uuid
        # Simple test to see whether I load correctly from the pk:
        self.assertEqual(uuid_stored, load_node(pk=node.pk).uuid)
        # Testing the loading with the uuid:
        self.assertEqual(uuid_stored, load_node(uuid=uuid_stored).uuid)

        # Here I'm testing whether loading the node with the beginnings of a uuid works
        for i in range(10, len(uuid_stored), 2):
            start_uuid = uuid_stored[:i]
            self.assertEqual(uuid_stored, load_node(uuid=start_uuid).uuid)

        # Testing whether loading the node with part of UUID works, removing the dashes
        for i in range(10, len(uuid_stored), 2):
            start_uuid = uuid_stored[:i].replace('-', '')
            self.assertEqual(uuid_stored, load_node(uuid=start_uuid).uuid)
            # If I don't allow load_node to fix the dashes, this has to raise:
            with self.assertRaises(NotExistent):
                load_node(uuid=start_uuid, query_with_dashes=False)

        # Now I am reverting the order of the uuid, this will raise a NotExistent error:
        with self.assertRaises(NotExistent):
            load_node(uuid=uuid_stored[::-1])

        # I am giving a non-sensical pk, this should also raise
        with self.assertRaises(NotExistent):
            load_node(-1)

        # Last check, when asking for specific subclass, this should raise:
        for spec in (node.pk, uuid_stored):
            with self.assertRaises(NotExistent):
                load_node(spec, sub_classes=(ArrayData,))

    @unittest.skip('open issue JobCalculations cannot be stored')
    def test_load_unknown_calculation_type(self):
        """
        Test that the loader will choose a common calculation ancestor for an unknown data type.
        For the case where, e.g., the user doesn't have the necessary plugin.
        """
        from aiida.orm import CalculationFactory
        from aiida.orm.node.process import CalcJobNode

        ###### for calculation
        calc_params = {'computer': self.computer, 'resources': {'num_machines': 1, 'num_mpiprocs_per_machine': 1}}

        TemplateReplacerCalc = CalculationFactory('templatereplacer')
        testcalc = TemplateReplacerCalc(**calc_params).store()

        # compare if plugin exist
        obj = load_node(uuid=testcalc.uuid)
        self.assertEqual(type(testcalc), type(obj))

        # Create a custom calculation type that inherits from CalcJobNode but change the plugin type string
        class TestCalculation(CalcJobNode):
            pass

        TestCalculation._plugin_type_string = 'node.process.calculation.calcjob.notexisting.TemplatereplacerCalculation.'
        TestCalculation._query_type_string = 'node.process.calculation.calcjob.notexisting.TemplatereplacerCalculation'

        jobcalc = CalcJobNode(**calc_params).store()
        testcalc = TestCalculation(**calc_params).store()

        # Changed node should return CalcJobNode type as its plugin does not exist
        obj = load_node(uuid=testcalc.uuid)
        self.assertEqual(type(jobcalc), type(obj))

    def test_load_unknown_data_type(self):
        """
        Test that the loader will choose a common data ancestor for an unknown data type.
        For the case where, e.g., the user doesn't have the necessary plugin.
        """
        from aiida.orm import DataFactory
        from aiida.orm.data import Data

        KpointsData = DataFactory('array.kpoints')
        kpoint = KpointsData().store()
        data = Data().store()

        # compare if plugin exist
        obj = load_node(uuid=kpoint.uuid)
        self.assertEqual(type(kpoint), type(obj))

        class TestKpointsData(KpointsData):
            pass

        # change node type and save in database again
        test_kpoint = TestKpointsData().store()

        # changed node should return data node as its plugin is not exist
        obj = load_node(uuid=kpoint.uuid)
        self.assertEqual(type(kpoint), type(obj))

        ###### for node
        n1 = Data().store()
        obj = get_orm_entity(n1)
        self.assertEqual(type(n1), type(obj))


class TestSubNodesAndLinks(AiidaTestCase):

    def test_cachelink(self):
        """
        Test the proper functionality of the links cache, with different
        scenarios.
        """
        n1 = Data()
        n2 = Data()
        n3 = Data().store()
        n4 = Data().store()
        endcalc = CalculationNode()

        # Nothing stored
        endcalc.add_incoming(n1, LinkType.INPUT_CALC, "N1")
        # Try also reverse storage
        endcalc.add_incoming(n2, LinkType.INPUT_CALC, "N2")

        self.assertEqual(
            set([(i.link_label, i.node.uuid) for i in endcalc.get_incoming()]),
            set([("N1", n1.uuid), ("N2", n2.uuid)]))

        # Endnode not stored yet, n3 and n4 already stored
        endcalc.add_incoming(n3, LinkType.INPUT_CALC, "N3")
        # Try also reverse storage
        endcalc.add_incoming(n4, LinkType.INPUT_CALC, "N4")

        self.assertEqual(
            set([(i.link_label, i.node.uuid) for i in endcalc.get_incoming()]),
            set([("N1", n1.uuid), ("N2", n2.uuid), ("N3", n3.uuid), ("N4", n4.uuid)]))

        # Some parent nodes are not stored yet
        with self.assertRaises(ModificationNotAllowed):
            endcalc.store()

        self.assertEqual(
            set([(i.link_label, i.node.uuid) for i in endcalc.get_incoming()]),
            set([("N1", n1.uuid), ("N2", n2.uuid), ("N3", n3.uuid), ("N4", n4.uuid)]))

        # This will also store n1 and n2!
        endcalc.store_all()

        self.assertEqual(
            set([(i.link_label, i.node.uuid) for i in endcalc.get_incoming()]),
            set([("N1", n1.uuid), ("N2", n2.uuid), ("N3", n3.uuid), ("N4", n4.uuid)]))

    def test_store_with_unstored_parents(self):
        """
        I want to check that if parents are unstored I cannot store
        """
        n1 = Data()
        n2 = Data().store()
        endcalc = CalculationNode()

        endcalc.add_incoming(n1, LinkType.INPUT_CALC, "N1")
        endcalc.add_incoming(n2, LinkType.INPUT_CALC, "N2")

        # Some parent nodes are not stored yet
        with self.assertRaises(ModificationNotAllowed):
            endcalc.store()

        n1.store()
        # Now I can store
        endcalc.store()

        self.assertEqual(
            set([(i.link_label, i.node.uuid) for i in endcalc.get_incoming()]),
            set([("N1", n1.uuid), ("N2", n2.uuid)]))

    def test_storeall_with_unstored_grandparents(self):
        """
        I want to check that if grandparents are unstored I cannot store_all
        """
        n1 = CalculationNode()
        n2 = Data()
        endcalc = CalculationNode()

        n2.add_incoming(n1, LinkType.CREATE, "N1")
        endcalc.add_incoming(n2, LinkType.INPUT_CALC, "N2")

        # Grandparents are unstored
        with self.assertRaises(ModificationNotAllowed):
            endcalc.store_all()

        n1.store()
        # Now it should work
        endcalc.store_all()

        # Check the parents...
        self.assertEqual(set([(i.link_label, i.node.uuid) for i in n2.get_incoming()]), set([("N1", n1.uuid)]))
        self.assertEqual(set([(i.link_label, i.node.uuid) for i in endcalc.get_incoming()]), set([("N2", n2.uuid)]))

    def test_has_children_has_parents(self):
        """
        This check verifies that the properties has_children has_parents of the
        Node class behave correctly.
        """
        from aiida.common.links import LinkType

        # Create 2 nodes and store them
        n1 = CalculationNode().store()
        n2 = Data().store()

        # Create a link between these 2 nodes, link type CREATE so we track the provenance
        n2.add_incoming(n1, LinkType.CREATE, "N1")

        self.assertTrue(n1.has_children, "It should be true since n2 is the child of n1.")
        self.assertFalse(n1.has_parents, "It should be false since n1 doesn't have any parents.")
        self.assertFalse(n2.has_children, "It should be false since n2 doesn't have any children.")
        self.assertTrue(n2.has_parents, "It should be true since n1 is the parent of n2.")

    def test_use_code(self):
        from aiida.orm.node.process import CalcJobNode
        from aiida.orm.code import Code

        computer = self.computer

        code = Code(remote_computer_exec=(computer, '/bin/true'))  # .store()

        unstoredcalc = CalcJobNode(computer=computer, resources={'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        calc = CalcJobNode(computer=computer, resources={'num_machines': 1, 'num_mpiprocs_per_machine': 1}).store()

        # calc is not stored, and also code is not
        unstoredcalc.use_code(code)

        # calc is stored, but code is not
        calc.use_code(code)

        self.assertEqual(calc.get_code().uuid, code.uuid)
        self.assertEqual(unstoredcalc.get_code().uuid, code.uuid)

        # calc is not stored, but code is
        code.store()

        self.assertEqual(calc.get_code().uuid, code.uuid)
        self.assertEqual(unstoredcalc.get_code().uuid, code.uuid)

        unstoredcalc.store()

        self.assertEqual(calc.get_code().uuid, code.uuid)
        self.assertEqual(unstoredcalc.get_code().uuid, code.uuid)

    # pylint: disable=unused-variable,no-member,no-self-use
    def test_calculation_load(self):
        from aiida.orm.node.process import CalcJobNode

        # I check with a string, with an object and with the computer pk/id
        calc = CalcJobNode(
            computer=self.computer, resources={
                'num_machines': 1,
                'num_mpiprocs_per_machine': 1
            }).store()
        with self.assertRaises(Exception):
            # I should get an error if I ask for a computer id/pk that doesn't
            # exist
            _ = CalcJobNode(
                computer=self.computer.id + 100000, resources={
                    'num_machines': 2,
                    'num_mpiprocs_per_machine': 1
                }).store()

    def test_links_label_constraints(self):
        d1 = Data().store()
        d1bis = Data().store()
        calc = CalculationNode().store()
        d2 = Data().store()
        d3 = Data().store()
        d4 = Data().store()
        calc2a = CalculationNode().store()
        calc2b = CalculationNode().store()

        calc.add_incoming(d1, LinkType.INPUT_CALC, link_label='label1')
        with self.assertRaises(ValueError):
            calc.add_incoming(d1bis, LinkType.INPUT_CALC, link_label='label1')

        # This should be allowed since it is an output label with the same name
        # as an input label: no problem
        d2.add_incoming(calc, LinkType.CREATE, link_label='label1')
        # This should be allowed, it's a different label
        d3.add_incoming(calc, LinkType.CREATE, link_label='label2')

        # This shouldn't be allowed, it's an output CREATE link with 
        # the same same of an existing output CREATE link
        with self.assertRaises(ValueError):
            d4.add_incoming(calc, LinkType.CREATE, link_label='label2')

        # instead, for outputs, I can have multiple times the same label
        # (think to the case where d4 is a StructureData, and both calc2a and calc2b
        # are calculations that use as label 'input_cell')
        calc2a.add_incoming(d4, LinkType.INPUT_CALC, link_label='label3')
        calc2b.add_incoming(d4, LinkType.INPUT_CALC, link_label='label3')

    @unittest.skip('activate this test once #2238 is addressed')
    def test_links_label_autogenerator(self):
        """Test the auto generation of link labels when labels are no longer required to be explicitly specified.
        """
        n1 = WorkflowNode().store()
        n2 = WorkflowNode().store()
        n3 = WorkflowNode().store()
        n4 = WorkflowNode().store()
        n5 = WorkflowNode().store()
        n6 = WorkflowNode().store()
        n7 = WorkflowNode().store()
        n8 = WorkflowNode().store()
        n9 = WorkflowNode().store()
        data = Data().store()

        data.add_incoming(n1, link_type=LinkType.RETURN)
        # Label should be automatically generated
        data.add_incoming(n2, link_type=LinkType.RETURN)
        data.add_incoming(n3, link_type=LinkType.RETURN)
        data.add_incoming(n4, link_type=LinkType.RETURN)
        data.add_incoming(n5, link_type=LinkType.RETURN)
        data.add_incoming(n6, link_type=LinkType.RETURN)
        data.add_incoming(n7, link_type=LinkType.RETURN)
        data.add_incoming(n8, link_type=LinkType.RETURN)
        data.add_incoming(n9, link_type=LinkType.RETURN)

        all_labels = [_.link_label for _ in data.get_incoming()]
        self.assertEquals(len(set(all_labels)), len(all_labels), "There are duplicate links, that are not expected")

    @unittest.skip('activate this test once #2238 is addressed')
    def test_link_label_autogenerator(self):
        """
        When the uniqueness constraints on links are reimplemented on the database level, auto generation of
        labels that relies directly on those database level constraints should be reinstated and tested for here.
        """
        raise NotImplementedError

    @unittest.skip('remove this test once #2219 is addressed')
    def test_link_replace(self):
        from aiida.orm.node.process import CalculationNode
        from aiida.orm import Data

        n1 = CalculationNode().store()
        n2 = CalculationNode().store()
        n3 = Data().store()
        n4 = Data().store()

        n3.add_incoming(n1, link_type=LinkType.CREATE, link_label='the_label')
        with self.assertRaises(ValueError):
            # A link with the same name already exists
            n3.add_incoming(n1, link_type=LinkType.CREATE, link_label='the_label')

        # I can replace the link and check that it was replaced
        n3._replace_link_from(n2, LinkType.CREATE, link_label='the_label')
        the_parent = [_.node.uuid for _ in n3.get_incoming() if _.link_label == 'the_label']
        self.assertEquals(len(the_parent), 1, "There are multiple input links with the same label (the_label)!")
        self.assertEquals(n2.uuid, the_parent[0])

        # _replace_link_from should work also if there is no previous link
        n2._replace_link_from(n1, LinkType.CREATE, link_label='the_label_2')
        the_parent_2 = [_.node.uuid for _ in n4.get_incoming() if _.link_label == 'the_label_2']
        self.assertEquals(len(the_parent_2), 1, "There are multiple input links with the same label (the_label_2)!")
        self.assertEquals(n1.uuid, the_parent_2[0])

    def test_link_with_unstored(self):
        """
        It is possible to store links between nodes even if they are unstored these links are cached.
        """
        from aiida.orm.node.process import CalculationNode, WorkflowNode
        from aiida.orm import Data

        n1 = Data()
        n2 = WorkflowNode()
        n3 = CalculationNode()
        n4 = Data()

        # Caching the links
        n2.add_incoming(n1, link_type=LinkType.INPUT_WORK, link_label='l1')
        n3.add_incoming(n1, link_type=LinkType.INPUT_CALC, link_label='l3')
        n3.add_incoming(n2, link_type=LinkType.CALL_CALC, link_label='l2')

        # Twice the same link name
        with self.assertRaises(ValueError):
            n3.add_incoming(n4, link_type=LinkType.INPUT_CALC, link_label='l3')

        n2.store_all()
        n3.store_all()

        n2_in_links = [(n.link_label, n.node.uuid) for n in n2.get_incoming()]
        self.assertEquals(sorted(n2_in_links), sorted([
            ('l1', n1.uuid),
        ]))
        n3_in_links = [(n.link_label, n.node.uuid) for n in n3.get_incoming()]
        self.assertEquals(sorted(n3_in_links), sorted([
            ('l2', n2.uuid),
            ('l3', n1.uuid),
        ]))

        n1_out_links = [(entry.link_label, entry.node.pk) for entry in n1.get_outgoing()]
        self.assertEquals(sorted(n1_out_links), sorted([
            ('l1', n2.pk),
            ('l3', n3.pk),
        ]))
        n2_out_links = [(entry.link_label, entry.node.pk) for entry in n2.get_outgoing()]
        self.assertEquals(sorted(n2_out_links), sorted([('l2', n3.pk)]))

    def test_multiple_create_links(self):
        """
        Cannot have two CREATE links for the same node.
        """
        from aiida.orm.data import Data
        from aiida.orm.node.process import CalculationNode

        n1 = CalculationNode()
        n2 = CalculationNode()
        n3 = Data()

        # Caching the links
        n3.add_incoming(n1, link_type=LinkType.CREATE, link_label='CREATE')
        with self.assertRaises(ValueError):
            n3.add_incoming(n2, link_type=LinkType.CREATE, link_label='CREATE')

    def test_valid_links(self):
        import tempfile
        from aiida import orm
        from aiida.orm import DataFactory
        from aiida.orm.node.process import CalcJobNode
        from aiida.orm.code import Code
        from aiida.common.datastructures import calc_states

        SinglefileData = DataFactory('singlefile')

        # I create some objects
        d1 = Data().store()
        with tempfile.NamedTemporaryFile('w+') as tmpf:
            d2 = SinglefileData(file=tmpf.name).store()

        code = Code()
        code._set_remote()
        code.set_computer(self.computer)
        code.set_remote_computer_exec((self.computer, '/bin/true'))
        code.store()

        unsavedcomputer = orm.Computer(name='localhost2', hostname='localhost')

        with self.assertRaises(ValueError):
            # I need to save the localhost entry first
            _ = CalcJobNode(
                computer=unsavedcomputer, resources={
                    'num_machines': 1,
                    'num_mpiprocs_per_machine': 1
                }).store()

        # Load calculations with two different ways
        calc = CalcJobNode(
            computer=self.computer, resources={
                'num_machines': 1,
                'num_mpiprocs_per_machine': 1
            }).store()
        calc2 = CalcJobNode(
            computer=self.computer, resources={
                'num_machines': 1,
                'num_mpiprocs_per_machine': 1
            }).store()

        calc.add_incoming(d1, link_type=LinkType.INPUT_CALC, link_label='link')
        calc.add_incoming(d2, link_type=LinkType.INPUT_CALC, link_label='some_label')
        calc.use_code(code)

        # Cannot link to itself
        with self.assertRaises(ValueError):
            d1.add_incoming(d1, link_type=LinkType.INPUT_CALC, link_label='link')

        # I try to add wrong links (data to data, calc to calc, etc.)
        with self.assertRaises(ValueError):
            d2.add_incoming(d1, link_type=LinkType.INPUT_CALC, link_label='link')

        with self.assertRaises(ValueError):
            d1.add_incoming(d2, link_type=LinkType.INPUT_CALC, link_label='link')

        with self.assertRaises(ValueError):
            d1.add_incoming(code, link_type=LinkType.INPUT_CALC, link_label='link')

        with self.assertRaises(ValueError):
            code.add_incoming(d1, link_type=LinkType.INPUT_CALC, link_label='link')

        with self.assertRaises(ValueError):
            calc.add_incoming(calc2, link_type=LinkType.INPUT_CALC, link_label='link')

        calc_a = CalcJobNode(
            computer=self.computer, resources={
                'num_machines': 1,
                'num_mpiprocs_per_machine': 1
            }).store()
        calc_b = CalcJobNode(
            computer=self.computer, resources={
                'num_machines': 1,
                'num_mpiprocs_per_machine': 1
            }).store()

        data_node = Data().store()

        # I do a trick to set it to a state that allows writing
        calc_a._set_state(calc_states.RETRIEVING)
        calc_b._set_state(calc_states.RETRIEVING)

        data_node.add_incoming(calc_a, link_type=LinkType.CREATE, link_label='link')
        # A data cannot have two input calculations
        with self.assertRaises(ValueError):
            data_node.add_incoming(calc_b, link_type=LinkType.CREATE, link_label='link')

        newdata = Data()
        # Cannot add an input link if the calculation is not in status NEW
        with self.assertRaises(ModificationNotAllowed):
            calc_a.add_incoming(newdata, link_type=LinkType.INPUT_CALC, link_label='link')

        # Cannot replace input nodes if the calculation is not in status NEW
        with self.assertRaises(ModificationNotAllowed):
            calc_a._replace_link_from(d2, LinkType.INPUT_CALC, link_label='some_label')

        # Cannot (re)set the code if the calculation is not in status NEW
        with self.assertRaises(ModificationNotAllowed):
            calc_a.use_code(code)

        calculation_inputs = calc.get_incoming().all()

        # This calculation has three inputs (2 data and one code)
        self.assertEquals(len(calculation_inputs), 3)

    def test_check_single_calc_source(self):
        """
        Each data node can only have one input calculation
        """
        from aiida.orm.node.process import CalcJobNode
        from aiida.common.datastructures import calc_states

        d1 = Data().store()

        calc = CalcJobNode(
            computer=self.computer, resources={
                'num_machines': 1,
                'num_mpiprocs_per_machine': 1
            }).store()
        calc2 = CalcJobNode(
            computer=self.computer, resources={
                'num_machines': 1,
                'num_mpiprocs_per_machine': 1
            }).store()

        # I cannot, calc it is in state NEW
        with self.assertRaises(ModificationNotAllowed):
            d1.add_incoming(calc, link_type=LinkType.CREATE, link_label='link')

        # I do a trick to set it to a state that allows setting the link
        calc._set_state(calc_states.RETRIEVING)
        calc2._set_state(calc_states.RETRIEVING)

        d1.add_incoming(calc, link_type=LinkType.CREATE, link_label='link')

        # more than one input to the same data object!
        with self.assertRaises(ValueError):
            d1.add_incoming(calc2, link_type=LinkType.CREATE, link_label='link')

    def test_node_get_incoming_outgoing_links(self):
        """
        Test that the link_type parameter in get_incoming and get_outgoing only
        returns those nodes with the correct link type for stored nodes
        """
        node_origin = WorkflowNode().store()
        node_origin2 = WorkflowNode().store()
        node_caller_stored = WorkflowNode().store()
        node_called = WorkflowNode().store()
        node_input_stored = Data().store()
        node_output = Data().store()
        node_return = Data().store()
        node_caller_unstored = WorkflowNode()
        node_input_unstored = Data()

        # Input links of node_origin
        node_origin.add_incoming(node_caller_stored, link_type=LinkType.CALL_WORK, link_label='caller_stored')
        node_origin.add_incoming(node_input_stored, link_type=LinkType.INPUT_WORK, link_label='input_stored')
        node_origin.add_incoming(node_input_unstored, link_type=LinkType.INPUT_WORK, link_label='input_unstored')

        node_origin2.add_incoming(node_caller_unstored, link_type=LinkType.CALL_WORK, link_label='caller_unstored')

        # Output links of node_origin
        node_called.add_incoming(node_origin, link_type=LinkType.CALL_WORK, link_label='called')
        node_output.add_incoming(node_origin, link_type=LinkType.RETURN, link_label='return1')
        node_return.add_incoming(node_origin, link_type=LinkType.RETURN, link_label='return2')

        # All incoming and outgoing
        self.assertEquals(len(node_origin.get_incoming().all()), 3)
        self.assertEquals(len(node_origin.get_outgoing().all()), 3)

        # Link specific incoming
        self.assertEquals(len(node_origin.get_incoming(link_type=LinkType.CALL_WORK).all()), 1)
        self.assertEquals(len(node_origin2.get_incoming(link_type=LinkType.CALL_WORK).all()), 1)
        self.assertEquals(len(node_origin.get_incoming(link_type=LinkType.INPUT_WORK).all()), 2)
        self.assertEquals(len(node_origin.get_incoming(link_label_filter="in_ut%").all()), 2)
        self.assertEquals(len(node_origin.get_incoming(node_class=Node).all()), 3)

        # Link specific outgoing
        self.assertEquals(len(node_origin.get_outgoing(link_type=LinkType.CALL_WORK).all()), 1)
        self.assertEquals(len(node_origin.get_outgoing(link_type=LinkType.RETURN).all()), 2)


class AnyValue(object):
    """
    Helper class that compares equal to everything.
    """

    def __eq__(self, other):
        return True


class TestNodeDeletion(AiidaTestCase):

    def _check_existence(self, uuids_check_existence, uuids_check_deleted):
        """
        I get 2 lists of uuids

        :param uuids_check_existence: The list of uuids that have to exist
        :param uuids_check_deleted: The list of uuids that should not exist,
            I check that NotExistent is raised.
        """
        from aiida.common.exceptions import NotExistent

        # Shouldn't be needed, but just to avoid an exception being
        # raised from the exception management block below
        uuid = None

        try:
            for uuid in uuids_check_existence:
                # This will raise if node is not existent:
                load_node(uuid)
            for uuid in uuids_check_deleted:
                # I check that it raises
                with self.assertRaises(NotExistent):
                    load_node(uuid)
        except Exception as exc:  # pylint: disable=broad-except
            import sys
            six.reraise(
                type(exc),
                str(exc) +
                "\nCurrent UUID being processed: {}\nFull uuids_check_existence: {}; full uuids_check_deleted: {}".format(
                    uuid, uuids_check_existence, uuids_check_deleted),
                sys.exc_info()[2])

    def _create_calls_n_returns_graph(self):
        """
        Creates a complicated graph with a master with 1 inputs,
        2 slaves of it also using that input and an additional 1,
        producing output that is either returned or not returned by the master.
        Master also creates one nodes. This allows to check whether the delete_nodes
        command works as anticipated.
        """
        # in1 -> wf
        #     `-> slave1
        #      ____^  ^
        #     /       "CALL
        # in2 -> slave2
        # ind
        in1 = Data().store()
        in2 = Data().store()
        wf = WorkflowNode().store()
        slave1 = WorkflowNode().store()
        outp1 = Data().store()
        outp2 = Data().store()
        slave2 = CalculationNode().store()
        outp3 = Data().store()
        outp4 = Data().store()
        wf.add_incoming(in1, link_type=LinkType.INPUT_WORK, link_label='link1')
        slave1.add_incoming(in1, link_type=LinkType.INPUT_WORK, link_label='link2')
        slave1.add_incoming(in2, link_type=LinkType.INPUT_WORK, link_label='link3')
        slave2.add_incoming(in2, link_type=LinkType.INPUT_CALC, link_label='link4')
        slave1.add_incoming(wf, link_type=LinkType.CALL_WORK, link_label='link5')
        slave2.add_incoming(wf, link_type=LinkType.CALL_CALC, link_label='link6')
        outp1.add_incoming(slave1, link_type=LinkType.RETURN, link_label='link7')
        outp2.add_incoming(slave2, link_type=LinkType.CREATE, link_label='link8')
        outp2.add_incoming(wf, link_type=LinkType.RETURN, link_label='link9')
        outp3.add_incoming(wf, link_type=LinkType.RETURN, link_label='link10')
        outp4.add_incoming(wf, link_type=LinkType.RETURN, link_label='link11')
        return in1, in2, wf, slave1, outp1, outp2, slave2, outp3, outp4

    def test_deletion_simple(self):
        """
        I'm setting up a sequence of nodes connected by data provenance links.
        Testing whether I will delete the right ones.
        """
        nodes = [
            Data(),  # 0
            CalculationNode(), CalculationNode(), CalculationNode(),  # 1, 2, 3
            Data(), Data(), Data(),  # 4, 5, 6
            CalculationNode(), CalculationNode(), CalculationNode(),  # 7, 8, 9
            Data(),  # 10
            CalculationNode(),  # 11
            Data(),  # 12
            CalculationNode(),  # 13
            Data(),  # 14
        ]
        # Store all of them
        for node in nodes:
            node.store()

        uuids_check_existence = [n.uuid for n in nodes[:3]]
        uuids_check_deleted = [n.uuid for n in nodes[3:]]

        # Now I am linking the nodes in a branched network
        # Connecting nodes 1,2,3 to 0
        for i in range(1, 4):
            nodes[i].add_incoming(nodes[0], link_type=LinkType.INPUT_CALC, link_label='link{}'.format(i))
        # Connecting nodes 4,5,6 to 3
        for i in range(4, 7):
            nodes[i].add_incoming(nodes[3], link_type=LinkType.CREATE, link_label='link{}'.format(i))
        # Connecting nodes 7,8 to 4
        for i in range(7, 9):
            nodes[i].add_incoming(nodes[4], link_type=LinkType.INPUT_CALC, link_label='link{}'.format(i))
        # Connecting node 9 (WF) to 5 (input data)
        nodes[9].add_incoming(nodes[5], link_type=LinkType.INPUT_CALC, link_label='link9')

        # Connect each node to the next one
        for i in range(10, 14):
            # First link to create: 10 (Data) -> 11 (Calc) via a INPUT_CALC
            link_type = LinkType.CREATE if i % 2 else LinkType.INPUT_CALC
            nodes[i + 1].add_incoming(nodes[i], link_type=link_type, link_label='link{}'.format(i))

        with Capturing():
            delete_nodes((nodes[3].pk, nodes[10].pk), force=True, verbosity=2)

        self._check_existence(uuids_check_existence, uuids_check_deleted)

    def test_deletion_with_calls_with_returns(self):
        """
        Checking the case where I follow calls and return links for deletion
        """
        in1, in2, wf, slave1, outp1, outp2, slave2, outp3, outp4 = self._create_calls_n_returns_graph()
        # The inputs are not harmed.
        uuids_check_existence = (in1.uuid, in2.uuid)
        # the slaves and their outputs have to disappear since calls are followed!
        uuids_check_deleted = [n.uuid for n in (wf, slave1, outp1, outp2, outp3, slave2, outp4)]

        with Capturing():
            delete_nodes([wf.pk], verbosity=2, force=True, follow_calls=True, follow_returns=True)

        self._check_existence(uuids_check_existence, uuids_check_deleted)

    def test_deletion_with_calls_no_returns(self):
        """
        Checking the case where I follow calls and not return links for deletion
        """
        in1, in2, wf, slave1, outp1, outp2, slave2, outp3, outp4 = self._create_calls_n_returns_graph()
        # The inputs are not harmed.
        uuids_check_existence = [n.uuid for n in (in1, in2, outp1, outp3, outp4)]
        # the slaves and their outputs have to disappear since calls are followed!
        uuids_check_deleted = [n.uuid for n in (wf, slave1, slave2, outp2)]

        with Capturing():
            delete_nodes([wf.pk], verbosity=2, force=True, follow_calls=True, follow_returns=False)

        self._check_existence(uuids_check_existence, uuids_check_deleted)

    def test_deletion_no_calls_no_returns(self):
        """
        Checking the case where I don't follow calls and also not return links for deletion
        """
        in1, in2, wf, slave1, outp1, outp2, slave2, outp3, outp4 = self._create_calls_n_returns_graph()
        # I don't follow calls, so the slaves and their output are unharmed, as well as input
        uuids_check_existence = [n.uuid for n in (in1, in2, slave1, outp1, outp2, outp3, slave2, outp4)]
        # the wf and it's direct output
        uuids_check_deleted = [n.uuid for n in (wf,)]

        with Capturing():
            delete_nodes([wf.pk], verbosity=2, force=True, follow_calls=False, follow_returns=False)

        self._check_existence(uuids_check_existence, uuids_check_deleted)
        self._check_existence(uuids_check_existence, uuids_check_deleted)

    def test_deletion_no_calls_with_returns(self):
        """
        Checking the case where I follow returns and not calls for deletion
        """
        in1, in2, wf, slave1, outp1, outp2, slave2, outp3, outp4 = self._create_calls_n_returns_graph()
        # I don't follow calls, so the slaves and their output are unharmed, as well as input
        uuids_check_existence = [n.uuid for n in (in1, in2, slave1, outp1, slave2)]
        # the wf and it's direct output and what it returned
        uuids_check_deleted = [n.uuid for n in (wf, outp3, outp2, outp4)]

        with Capturing():
            delete_nodes([wf.pk], verbosity=2, force=True, follow_calls=False, follow_returns=True)

        self._check_existence(uuids_check_existence, uuids_check_deleted)
        self._check_existence(uuids_check_existence, uuids_check_deleted)

    def test_deletion_with_returns_n_loops(self):
        """
        Setting up a simple loop, to check that the following doesn't go bananas.
        """
        in1, in2, wf = [Data().store(), Data().store(), WorkflowNode().store()]
        wf.add_incoming(in1, link_type=LinkType.INPUT_WORK, link_label='link1')
        wf.add_incoming(in2, link_type=LinkType.INPUT_WORK, link_label='link2')
        in2.add_incoming(wf, link_type=LinkType.RETURN, link_label='link3')

        uuids_check_existence = (in1.uuid,)
        uuids_check_deleted = [n.uuid for n in (wf, in2)]

        with Capturing():
            delete_nodes([wf.pk], verbosity=2, force=True, follow_returns=True)

        self._check_existence(uuids_check_existence, uuids_check_deleted)

    def test_delete_called_but_not_caller(self):
        """
        Check that deleting a ProcessNode that was called by another ProcessNode which won't be
        deleted works, even though it will raise a warning
        """
        caller, called = [WorkflowNode().store() for i in range(2)]
        called.add_incoming(caller, link_type=LinkType.CALL_WORK, link_label='link')

        uuids_check_existence = (caller.uuid,)
        uuids_check_deleted = [n.uuid for n in (called,)]

        with Capturing():
            delete_nodes([called.pk], verbosity=2, force=True, follow_returns=True)

        self._check_existence(uuids_check_existence, uuids_check_deleted)
