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
import tempfile
import unittest

import six
from six.moves import range
from sqlalchemy.exc import StatementError

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.common.exceptions import InvalidOperation, ModificationNotAllowed, StoringNotAllowed
from aiida.common.links import LinkType
from aiida.common.utils import Capturing
from aiida.manage.database.delete.nodes import delete_nodes


class TestNodeIsStorable(AiidaTestCase):
    """
    Test if one can store specific Node subclasses, and that Node and
    ProcessType are not storable, intead.
    """

    def test_storable_unstorable(self):
        """
        Test storability of Nodes
        """
        node = orm.Node()
        with self.assertRaises(StoringNotAllowed):
            node.store()

        process = orm.ProcessNode()
        with self.assertRaises(StoringNotAllowed):
            process.store()

        # These below should be allowed instead
        data = orm.Data()
        data.store()

        calc = orm.CalculationNode()
        calc.store()

        work = orm.WorkflowNode()
        work.store()


class TestNodeCopyDeepcopy(AiidaTestCase):
    """Test that calling copy and deepcopy on a Node does the right thing."""

    def test_copy_not_supported(self):
        """Copying a base Node instance is not supported."""
        node = orm.Node()
        with self.assertRaises(InvalidOperation):
            copy.copy(node)

    def test_deepcopy_not_supported(self):
        """Deep copying a base Node instance is not supported."""
        node = orm.Node()
        with self.assertRaises(InvalidOperation):
            copy.deepcopy(node)


class TestNodeHashing(AiidaTestCase):
    """
    Tests the functionality of hashing a node
    """

    @staticmethod
    def create_simple_node(a, b=0, c=0):
        n = orm.Data()
        n.set_attribute('a', a)
        n.set_attribute('b', b)
        n.set_attribute('c', c)
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
        n = orm.Data()
        n.store()

        # Search for the UUID of the stored node
        qb = orm.QueryBuilder()
        qb.append(orm.Data, project=['uuid'], filters={'id': {'==': n.id}})
        [uuid] = qb.first()

        # Look the node with the previously returned UUID
        qb = orm.QueryBuilder()
        qb.append(orm.Data, project=['id'], filters={'uuid': {'==': uuid}})

        # Check that the query doesn't fail
        qb.all()
        # And that the results are correct
        self.assertEquals(qb.count(), 1)
        self.assertEquals(qb.first()[0], n.id)

    @staticmethod
    def create_folderdata_with_empty_file():
        node = orm.FolderData()
        with tempfile.NamedTemporaryFile() as handle:
            node.put_object_from_filelike(handle, 'path/name')
        return node

    @staticmethod
    def create_folderdata_with_empty_folder():
        dirpath = tempfile.mkdtemp()
        node = orm.FolderData()
        node.put_object_from_tree(dirpath, 'path/name')
        return node

    def test_folder_file_different(self):
        f1 = self.create_folderdata_with_empty_file()
        f2 = self.create_folderdata_with_empty_folder()

        assert (f1.list_object_names('path') == f2.list_object_names('path'))
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
            self.assertFalse('_aiida_cached_from' in n2.extras)

    def test_unequal_arrays(self):
        import numpy as np
        arrays = [(np.zeros(1001), np.zeros(1005)), (np.array([1, 2, 3]), np.array([2, 3, 4]))]

        def create_arraydata(arr):
            a = orm.ArrayData()
            a.set_array('a', arr)
            return a

        for arr1, arr2 in arrays:
            a1 = create_arraydata(arr1)
            a1.store()
            a2 = create_arraydata(arr2)
            a2.store(use_cache=True)
            self.assertNotEquals(a1.uuid, a2.uuid)
            self.assertFalse('_aiida_cached_from' in a2.extras)

    def test_updatable_attributes(self):
        """
        Tests that updatable attributes are ignored.
        """
        node = orm.ProcessNode()
        hash1 = node.get_hash()
        node.set_process_state('finished')
        hash2 = node.get_hash()
        self.assertNotEquals(hash1, None)
        self.assertEquals(hash1, hash2)


class TestTransitiveNoLoops(AiidaTestCase):
    """
    Test the transitive closure functionality
    """

    def test_loop_not_allowed(self):
        d1 = orm.Data().store()
        c1 = orm.CalculationNode().store()
        d2 = orm.Data().store()
        c2 = orm.CalculationNode().store()

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
        orm.Data().store()
        orm.Data().store()

        results = orm.QueryBuilder().append(orm.Data, project=('uuid', '*')).all()
        for uuid, data in results:
            self.assertTrue(isinstance(uuid, six.string_types))
            self.assertTrue(isinstance(data.uuid, six.string_types))


class TestQueryWithAiidaObjects(AiidaTestCase):
    """
    Test if queries work properly also with aiida.orm.Node classes instead of
    aiida.backends.djsite.db.models.DbNode objects.
    """

    def test_with_subclasses(self):
        from aiida.plugins import DataFactory

        extra_name = self.__class__.__name__ + "/test_with_subclasses"

        Dict = DataFactory('dict')

        a1 = orm.CalcJobNode(computer=self.computer)
        a1.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        a1.store()
        # To query only these nodes later
        a1.set_extra(extra_name, True)
        a3 = orm.Data().store()
        a3.set_extra(extra_name, True)
        a4 = Dict(dict={'a': 'b'}).store()
        a4.set_extra(extra_name, True)
        # I don't set the extras, just to be sure that the filtering works
        # The filtering is needed because other tests will put stuff int he DB
        a6 = orm.CalcJobNode(computer=self.computer)
        a6.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        a1.store()
        a7 = orm.Data()
        a7.store()

        # Query by calculation
        qb = orm.QueryBuilder()
        qb.append(orm.CalcJobNode, filters={'extras': {'has_key': extra_name}})
        results = [_ for [_] in qb.all()]
        # a3, a4 should not be found because they are not CalcJobNodes.
        # a6, a7 should not be found because they have not the attribute set.
        self.assertEquals(set([i.pk for i in results]), set([a1.pk]))

        # Same query, but by the generic Node class
        qb = orm.QueryBuilder()
        qb.append(orm.Node, filters={'extras': {'has_key': extra_name}})
        results = [_ for [_] in qb.all()]
        self.assertEquals(set([i.pk for i in results]), set([a1.pk, a3.pk, a4.pk]))

        # Same query, but by the Data class
        qb = orm.QueryBuilder()
        qb.append(orm.Data, filters={'extras': {'has_key': extra_name}})
        results = [_ for [_] in qb.all()]
        self.assertEquals(set([i.pk for i in results]), set([a3.pk, a4.pk]))

        # Same query, but by the Dict subclass
        qb = orm.QueryBuilder()
        qb.append(orm.Dict, filters={'extras': {'has_key': extra_name}})
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

        a = orm.Data()
        b = orm.Data()
        b.backend_entity.dbmodel.uuid = a.uuid
        a.store()

        with self.assertRaises((DjIntegrityError, SqlaIntegrityError)):
            b.store()

    def test_attribute_mutability(self):
        """
        Attributes of a node should be immutable after storing, unless the stored_check is
        disabled in the call
        """
        a = orm.Data()
        a.set_attribute('bool', self.boolval)
        a.set_attribute('integer', self.intval)
        a.store()

        # After storing attributes should now be immutable
        with self.assertRaises(ModificationNotAllowed):
            a.delete_attribute('bool')

        with self.assertRaises(ModificationNotAllowed):
            a.set_attribute('integer', self.intval)

        # Passing stored_check=False should disable the mutability check
        a.delete_attribute('bool', stored_check=False)
        a.set_attribute('integer', self.intval, stored_check=False)

        self.assertEquals(a.get_attribute('integer'), self.intval)

        with self.assertRaises(AttributeError):
            a.get_attribute('bool')

    def test_attr_before_storing(self):
        a = orm.Data()
        a.set_attribute('k1', self.boolval)
        a.set_attribute('k2', self.intval)
        a.set_attribute('k3', self.floatval)
        a.set_attribute('k4', self.stringval)
        a.set_attribute('k5', self.dictval)
        a.set_attribute('k6', self.listval)
        a.set_attribute('k7', self.emptydict)
        a.set_attribute('k8', self.emptylist)
        a.set_attribute('k9', None)

        # Now I check if I can retrieve them, before the storage
        self.assertEquals(self.boolval, a.get_attribute('k1'))
        self.assertEquals(self.intval, a.get_attribute('k2'))
        self.assertEquals(self.floatval, a.get_attribute('k3'))
        self.assertEquals(self.stringval, a.get_attribute('k4'))
        self.assertEquals(self.dictval, a.get_attribute('k5'))
        self.assertEquals(self.listval, a.get_attribute('k6'))
        self.assertEquals(self.emptydict, a.get_attribute('k7'))
        self.assertEquals(self.emptylist, a.get_attribute('k8'))
        self.assertIsNone(a.get_attribute('k9'))

        # And now I try to delete the keys
        a.delete_attribute('k1')
        a.delete_attribute('k2')
        a.delete_attribute('k3')
        a.delete_attribute('k4')
        a.delete_attribute('k5')
        a.delete_attribute('k6')
        a.delete_attribute('k7')
        a.delete_attribute('k8')
        a.delete_attribute('k9')

        with self.assertRaises(AttributeError):
            # I delete twice the same attribute
            a.delete_attribute('k1')

        with self.assertRaises(AttributeError):
            # I delete a non-existing attribute
            a.delete_attribute('nonexisting')

        with self.assertRaises(AttributeError):
            # I get a deleted attribute
            a.get_attribute('k1')

        with self.assertRaises(AttributeError):
            # I get a non-existing attribute
            a.get_attribute('nonexisting')

    def test_get_attrs_before_storing(self):
        a = orm.Data()
        a.set_attribute('k1', self.boolval)
        a.set_attribute('k2', self.intval)
        a.set_attribute('k3', self.floatval)
        a.set_attribute('k4', self.stringval)
        a.set_attribute('k5', self.dictval)
        a.set_attribute('k6', self.listval)
        a.set_attribute('k7', self.emptydict)
        a.set_attribute('k8', self.emptylist)
        a.set_attribute('k9', None)

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
        self.assertEquals(a.attributes, target_attrs)

        # And now I try to delete the keys
        a.delete_attribute('k1')
        a.delete_attribute('k2')
        a.delete_attribute('k3')
        a.delete_attribute('k4')
        a.delete_attribute('k5')
        a.delete_attribute('k6')
        a.delete_attribute('k7')
        a.delete_attribute('k8')
        a.delete_attribute('k9')

        self.assertEquals(a.attributes, {})

    def test_get_attrs_after_storing(self):
        a = orm.Data()
        a.set_attribute('k1', self.boolval)
        a.set_attribute('k2', self.intval)
        a.set_attribute('k3', self.floatval)
        a.set_attribute('k4', self.stringval)
        a.set_attribute('k5', self.dictval)
        a.set_attribute('k6', self.listval)
        a.set_attribute('k7', self.emptydict)
        a.set_attribute('k8', self.emptylist)
        a.set_attribute('k9', None)

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
        self.assertEquals(a.attributes, target_attrs)

    def test_store_object(self):
        """Trying to store objects should fail"""
        a = orm.Data()
        a.set_attribute('object', object(), clean=False)

        # django raises ValueError
        # sqlalchemy raises StatementError
        with self.assertRaises((ValueError, StatementError)):
            a.store()

        b = orm.Data()
        b.set_attribute('object_list', [object(), object()], clean=False)
        with self.assertRaises((ValueError, StatementError)):
            # objects are not json-serializable
            b.store()

    def test_append_to_empty_attr(self):
        """Appending to an empty attribute"""
        a = orm.Data()
        a.append_to_attr('test', 0)
        a.append_to_attr('test', 1)

        self.assertEquals(a.get_attribute('test'), [0, 1])

    def test_append_no_side_effects(self):
        """Check that append_to_attr has no side effects"""
        a = orm.Data()
        mylist = [1, 2, 3]

        a.set_attribute('list', mylist)
        a.append_to_attr('list', 4)

        self.assertEquals(a.get_attribute('list'), [1, 2, 3, 4])
        self.assertEquals(mylist, [1, 2, 3])

    def test_datetime_attribute(self):
        from aiida.common.timezone import (get_current_timezone, is_naive, make_aware, now)

        a = orm.Data()

        date = now()

        a.set_attribute('some_date', date)
        a.store()

        retrieved = a.get_attribute('some_date')

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

        a = orm.Data()
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
            a.set_attribute(k, v)

        # Create a copy
        b = copy.deepcopy(a)
        # I modify an attribute and add a new one; I mirror it in the dictionary
        # for later checking
        b_expected_attributes = copy.deepcopy(attrs_to_set)
        b.set_attribute('integer', 489)
        b_expected_attributes['integer'] = 489
        b.set_attribute('new', 'cvb')
        b_expected_attributes['new'] = 'cvb'

        # I check before storing that the attributes are ok
        self.assertEquals(b.attributes, b_expected_attributes)
        # Note that during copy, I do not copy the extras!
        self.assertEquals({k: v for k, v in b.extras.items()}, {})

        # I store now
        b.store()
        # and I finally add a extras
        b.set_extra('meta', 'textofext')
        b_expected_extras = {'meta': 'textofext', '_aiida_hash': AnyValue()}

        # Now I check that the attributes of the original node have not changed
        self.assertEquals({k: v for k, v in a.attributes.items()}, attrs_to_set)

        # I check then on the 'b' copy
        self.assertEquals({k: v for k, v in b.attributes.items()}, b_expected_attributes)
        self.assertEquals({k: v for k, v in b.extras.items()}, b_expected_extras)

    def test_files(self):
        import tempfile

        a = orm.Data()

        file_content = u'some text ABCDE'
        file_content_different = u'other values 12345'

        with tempfile.NamedTemporaryFile('w+') as handle:
            handle.write(file_content)
            handle.flush()
            a.put_object_from_file(handle.name, 'file1.txt')
            a.put_object_from_file(handle.name, 'file2.txt')

        self.assertEquals(set(a.list_object_names()), set(['file1.txt', 'file2.txt']))
        with a.open('file1.txt') as fhandle:
            self.assertEquals(fhandle.read(), file_content)
        with a.open('file2.txt') as fhandle:
            self.assertEquals(fhandle.read(), file_content)

        b = a.clone()
        self.assertNotEquals(a.uuid, b.uuid)

        # Check that the content is there
        self.assertEquals(set(b.list_object_names()), set(['file1.txt', 'file2.txt']))
        with b.open('file1.txt') as handle:
            self.assertEquals(handle.read(), file_content)
        with b.open('file2.txt') as handle:
            self.assertEquals(handle.read(), file_content)

        # I overwrite a file and create a new one in the clone only
        with tempfile.NamedTemporaryFile(mode='w+') as handle:
            handle.write(file_content_different)
            handle.flush()
            b.put_object_from_file(handle.name, 'file2.txt')
            b.put_object_from_file(handle.name, 'file3.txt')

        # I check the new content, and that the old one has not changed
        self.assertEquals(set(a.list_object_names()), set(['file1.txt', 'file2.txt']))
        with a.open('file1.txt') as handle:
            self.assertEquals(handle.read(), file_content)
        with a.open('file2.txt') as handle:
            self.assertEquals(handle.read(), file_content)
        self.assertEquals(set(b.list_object_names()), set(['file1.txt', 'file2.txt', 'file3.txt']))
        with b.open('file1.txt') as handle:
            self.assertEquals(handle.read(), file_content)
        with b.open('file2.txt') as handle:
            self.assertEquals(handle.read(), file_content_different)
        with b.open('file3.txt') as handle:
            self.assertEquals(handle.read(), file_content_different)

        # This should in principle change the location of the files,
        # so I recheck
        a.store()

        # I now clone after storing
        c = a.clone()
        # I overwrite a file and create a new one in the clone only
        with tempfile.NamedTemporaryFile(mode='w+') as handle:
            handle.write(file_content_different)
            handle.flush()
            c.put_object_from_file(handle.name, 'file1.txt')
            c.put_object_from_file(handle.name, 'file4.txt')

        self.assertEquals(set(a.list_object_names()), set(['file1.txt', 'file2.txt']))
        with a.open('file1.txt') as handle:
            self.assertEquals(handle.read(), file_content)
        with a.open('file2.txt') as handle:
            self.assertEquals(handle.read(), file_content)

        self.assertEquals(set(c.list_object_names()), set(['file1.txt', 'file2.txt', 'file4.txt']))
        with c.open('file1.txt') as handle:
            self.assertEquals(handle.read(), file_content_different)
        with c.open('file2.txt') as handle:
            self.assertEquals(handle.read(), file_content)
        with c.open('file4.txt') as handle:
            self.assertEquals(handle.read(), file_content_different)

    def test_folders(self):
        """
        Similar as test_files, but I manipulate a tree of folders
        """
        import os
        import shutil
        import random
        import string
        from six.moves import StringIO

        a = orm.Data()

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
        a.put_object_from_tree(tree_1, 'tree_1')

        # verify if the node has the structure I expect
        self.assertEquals(set(a.list_object_names()), set(['tree_1']))
        self.assertEquals(set(a.list_object_names('tree_1')), set(['file1.txt', 'dir1']))
        self.assertEquals(set(a.list_object_names(os.path.join('tree_1', 'dir1'))), set(['dir2', 'file2.txt']))
        with a.open(os.path.join('tree_1', 'file1.txt')) as fhandle:
            self.assertEquals(fhandle.read(), file_content)
        with a.open(os.path.join('tree_1', 'dir1', 'file2.txt')) as fhandle:
            self.assertEquals(fhandle.read(), file_content)

        # try to exit from the folder
        with self.assertRaises(ValueError):
            a.list_object_names('..')

        # clone into a new node
        b = a.clone()
        self.assertNotEquals(a.uuid, b.uuid)

        # Check that the content is there
        self.assertEquals(set(b.list_object_names('.')), set(['tree_1']))
        self.assertEquals(set(b.list_object_names('tree_1')), set(['file1.txt', 'dir1']))
        self.assertEquals(set(b.list_object_names(os.path.join('tree_1', 'dir1'))), set(['dir2', 'file2.txt']))
        with b.open(os.path.join('tree_1', 'file1.txt')) as fhandle:
            self.assertEquals(fhandle.read(), file_content)
        with b.open(os.path.join('tree_1', 'dir1', 'file2.txt')) as fhandle:
            self.assertEquals(fhandle.read(), file_content)

        # I overwrite a file and create a new one in the copy only
        dir3 = os.path.join(directory, 'dir3')
        os.mkdir(dir3)

        b.put_object_from_tree(dir3, os.path.join('tree_1', 'dir3'))
        # no absolute path here
        with self.assertRaises(ValueError):
            b.put_object_from_tree('dir3', os.path.join('tree_1', 'dir3'))

        stream = StringIO(file_content_different)
        b.put_object_from_filelike(stream, 'file3.txt')

        # I check the new content, and that the old one has not changed old
        self.assertEquals(set(a.list_object_names('.')), set(['tree_1']))
        self.assertEquals(set(a.list_object_names('tree_1')), set(['file1.txt', 'dir1']))
        self.assertEquals(set(a.list_object_names(os.path.join('tree_1', 'dir1'))), set(['dir2', 'file2.txt']))
        with a.open(os.path.join('tree_1', 'file1.txt')) as fhandle:
            self.assertEquals(fhandle.read(), file_content)
        with a.open(os.path.join('tree_1', 'dir1', 'file2.txt')) as fhandle:
            self.assertEquals(fhandle.read(), file_content)
        # new
        self.assertEquals(set(b.list_object_names('.')), set(['tree_1', 'file3.txt']))
        self.assertEquals(set(b.list_object_names('tree_1')), set(['file1.txt', 'dir1', 'dir3']))
        self.assertEquals(set(b.list_object_names(os.path.join('tree_1', 'dir1'))), set(['dir2', 'file2.txt']))
        with b.open(os.path.join('tree_1', 'file1.txt')) as fhandle:
            self.assertEquals(fhandle.read(), file_content)
        with b.open(os.path.join('tree_1', 'dir1', 'file2.txt')) as fhandle:
            self.assertEquals(fhandle.read(), file_content)

        # This should in principle change the location of the files, so I recheck
        a.store()

        # I now copy after storing
        c = a.clone()
        # I overwrite a file, create a new one and remove a directory
        # in the copy only
        stream = StringIO(file_content_different)
        c.put_object_from_filelike(stream, os.path.join('tree_1', 'file1.txt'))
        c.put_object_from_filelike(stream, os.path.join('tree_1', 'dir1', 'file4.txt'))
        c.delete_object(os.path.join('tree_1', 'dir1', 'dir2'))

        # check old
        self.assertEquals(set(a.list_object_names('.')), set(['tree_1']))
        self.assertEquals(set(a.list_object_names('tree_1')), set(['file1.txt', 'dir1']))
        self.assertEquals(set(a.list_object_names(os.path.join('tree_1', 'dir1'))), set(['dir2', 'file2.txt']))
        with a.open(os.path.join('tree_1', 'file1.txt')) as fhandle:
            self.assertEquals(fhandle.read(), file_content)
        with a.open(os.path.join('tree_1', 'dir1', 'file2.txt')) as fhandle:
            self.assertEquals(fhandle.read(), file_content)

        # check new
        self.assertEquals(set(c.list_object_names('.')), set(['tree_1']))
        self.assertEquals(set(c.list_object_names('tree_1')), set(['file1.txt', 'dir1']))
        self.assertEquals(set(c.list_object_names(os.path.join('tree_1', 'dir1'))), set(['file2.txt', 'file4.txt']))
        with c.open(os.path.join('tree_1', 'file1.txt')) as fhandle:
            self.assertEquals(fhandle.read(), file_content_different)
        with c.open(os.path.join('tree_1', 'dir1', 'file2.txt')) as fhandle:
            self.assertEquals(fhandle.read(), file_content)

        # garbage cleaning
        shutil.rmtree(directory)

    def test_attr_after_storing(self):
        a = orm.Data()
        a.set_attribute('none', None)
        a.set_attribute('bool', self.boolval)
        a.set_attribute('integer', self.intval)
        a.set_attribute('float', self.floatval)
        a.set_attribute('string', self.stringval)
        a.set_attribute('dict', self.dictval)
        a.set_attribute('list', self.listval)

        a.store()

        # Now I check if I can retrieve them, before the storage
        self.assertIsNone(a.get_attribute('none'))
        self.assertEquals(self.boolval, a.get_attribute('bool'))
        self.assertEquals(self.intval, a.get_attribute('integer'))
        self.assertEquals(self.floatval, a.get_attribute('float'))
        self.assertEquals(self.stringval, a.get_attribute('string'))
        self.assertEquals(self.dictval, a.get_attribute('dict'))
        self.assertEquals(self.listval, a.get_attribute('list'))

    def test_attr_with_reload(self):
        a = orm.Data()
        a.set_attribute('none', None)
        a.set_attribute('bool', self.boolval)
        a.set_attribute('integer', self.intval)
        a.set_attribute('float', self.floatval)
        a.set_attribute('string', self.stringval)
        a.set_attribute('dict', self.dictval)
        a.set_attribute('list', self.listval)

        a.store()

        b = orm.load_node(uuid=a.uuid)
        self.assertIsNone(a.get_attribute('none'))
        self.assertEquals(self.boolval, b.get_attribute('bool'))
        self.assertEquals(self.intval, b.get_attribute('integer'))
        self.assertEquals(self.floatval, b.get_attribute('float'))
        self.assertEquals(self.stringval, b.get_attribute('string'))
        self.assertEquals(self.dictval, b.get_attribute('dict'))
        self.assertEquals(self.listval, b.get_attribute('list'))

        # Reload directly
        b = orm.Data.from_backend_entity(a.backend_entity)
        self.assertIsNone(a.get_attribute('none'))
        self.assertEquals(self.boolval, b.get_attribute('bool'))
        self.assertEquals(self.intval, b.get_attribute('integer'))
        self.assertEquals(self.floatval, b.get_attribute('float'))
        self.assertEquals(self.stringval, b.get_attribute('string'))
        self.assertEquals(self.dictval, b.get_attribute('dict'))
        self.assertEquals(self.listval, b.get_attribute('list'))

    def test_attr_and_extras(self):
        a = orm.Data()
        a.set_attribute('bool', self.boolval)
        a.set_attribute('integer', self.intval)
        a.set_attribute('float', self.floatval)
        a.set_attribute('string', self.stringval)
        a.set_attribute('dict', self.dictval)
        a.set_attribute('list', self.listval)

        with self.assertRaises(ModificationNotAllowed):
            # I did not store, I cannot modify
            a.set_extra('bool', 'blablabla')

        a.store()

        a_string = 'some non-boolean value'
        # I now set an extra with the same name of an attr
        a.set_extra('bool', a_string)
        # and I check that there is no name clash
        self.assertEquals(self.boolval, a.get_attribute('bool'))
        self.assertEquals(a_string, a.get_extra('bool'))

        self.assertEquals(a.extras, {'bool': a_string, '_aiida_hash': AnyValue()})

    def test_get_extras_with_default(self):
        a = orm.Data()
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
        n1 = orm.Data().store()
        n2 = orm.Data().store()

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
        a = orm.Data()
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
            a.set_attribute(k, v)

        a.store()

        # I now set extras
        extras_to_set = {'bool': 'some non-boolean value', 'some_other_name': 987}

        for k, v in extras_to_set.items():
            a.set_extra(k, v)

        all_extras = dict(_aiida_hash=AnyValue(), **extras_to_set)

        self.assertEquals(set(list(a.attributes.keys())), set(attrs_to_set.keys()))
        self.assertEquals(set(list(a.extras.keys())), set(all_extras.keys()))

        self.assertEquals(a.attributes, attrs_to_set)

        self.assertEquals(a.extras, all_extras)

    def test_versioning(self):
        """
        Test the versioning of the node when setting attributes and extras
        """
        a = orm.Data()
        attrs_to_set = {
            'bool': self.boolval,
            'integer': self.intval,
            'float': self.floatval,
            'string': self.stringval,
            'dict': self.dictval,
            'list': self.listval,
        }

        for key, value in attrs_to_set.items():
            a.set_attribute(key, value)
            self.assertEquals(a.get_attribute(key), value)

        a.store()

        # Check after storing
        for key, value in attrs_to_set.items():
            self.assertEquals(a.get_attribute(key), value)

        # Even if I stored many attributes, this should stay at 1
        self.assertEquals(a.version, 1)

        # I check increment on new version
        a.set_extra('a', 'b')
        self.assertEquals(a.version, 2)

        # In both cases, the node version must increase
        a.label = 'test'
        self.assertEquals(a.version, 3)

        a.description = 'test description'
        self.assertEquals(a.version, 4)

    def test_delete_extras(self):
        """
        Checks the ability of deleting extras, also when they are dictionaries
        or lists.
        """

        a = orm.Data().store()
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

        self.assertEquals({k: v for k, v in a.extras.items()}, all_extras)

        # I pregenerate it, it cannot change during iteration
        list_keys = list(extras_to_set.keys())
        for k in list_keys:
            # I delete one by one the keys and check if the operation is
            # performed correctly
            a.delete_extra(k)
            del all_extras[k]
            self.assertEquals({k: v for k, v in a.extras.items()}, all_extras)

    def test_replace_extras_1(self):
        """
        Checks the ability of replacing extras, removing the subkeys also when
        these are dictionaries or lists.
        """
        a = orm.Data().store()
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

        self.assertEquals(a.extras, all_extras)

        for k, v in new_extras.items():
            # I delete one by one the keys and check if the operation is
            # performed correctly
            a.set_extra(k, v)

        # I update extras_to_set with the new entries, and do the comparison
        # again
        all_extras.update(new_extras)
        self.assertEquals(a.extras, all_extras)

    def test_basetype_as_attr(self):
        """
        Test that setting a basetype as an attribute works transparently
        """
        # This one is unstored
        l1 = orm.List()
        l1.set_list(['b', [1, 2]])

        # This one is stored
        l2 = orm.List()
        l2.set_list(['f', True, {'gg': None}])
        l2.store()

        # Manages to store, and value is converted to its base type
        p = orm.Dict(dict={'b': orm.Str("sometext"), 'c': l1})
        p.store()
        self.assertEqual(p.get_attribute('b'), "sometext")
        self.assertIsInstance(p.get_attribute('b'), six.string_types)
        self.assertEqual(p.get_attribute('c'), ['b', [1, 2]])
        self.assertIsInstance(p.get_attribute('c'), (list, tuple))

        # Check also before storing
        n = orm.Data()
        n.set_attribute('a', orm.Str("sometext2"))
        n.set_attribute('b', l2)
        self.assertEqual(n.get_attribute('a'), "sometext2")
        self.assertIsInstance(n.get_attribute('a'), six.string_types)
        self.assertEqual(n.get_attribute('b'), ['f', True, {'gg': None}])
        self.assertIsInstance(n.get_attribute('b'), (list, tuple))

        # Check also deep in a dictionary/list
        n = orm.Data()
        n.set_attribute('a', {'b': [orm.Str("sometext3")]})
        self.assertEqual(n.get_attribute('a')['b'][0], "sometext3")
        self.assertIsInstance(n.get_attribute('a')['b'][0], six.string_types)
        n.store()
        self.assertEqual(n.get_attribute('a')['b'][0], "sometext3")
        self.assertIsInstance(n.get_attribute('a')['b'][0], six.string_types)

    def test_basetype_as_extra(self):
        """
        Test that setting a basetype as an attribute works transparently
        """
        # This one is unstored
        l1 = orm.List()
        l1.set_list(['b', [1, 2]])

        # This one is stored
        l2 = orm.List()
        l2.set_list(['f', True, {'gg': None}])
        l2.store()

        # Check also before storing
        n = orm.Data()
        n.store()
        n.set_extra('a', orm.Str("sometext2"))
        n.set_extra('c', l1)
        n.set_extra('d', l2)
        self.assertEqual(n.get_extra('a'), "sometext2")
        self.assertIsInstance(n.get_extra('a'), six.string_types)
        self.assertEqual(n.get_extra('c'), ['b', [1, 2]])
        self.assertIsInstance(n.get_extra('c'), (list, tuple))
        self.assertEqual(n.get_extra('d'), ['f', True, {'gg': None}])
        self.assertIsInstance(n.get_extra('d'), (list, tuple))

        # Check also deep in a dictionary/list
        n = orm.Data()
        n.store()
        n.set_extra('a', {'b': [orm.Str("sometext3")]})
        self.assertEqual(n.get_extra('a')['b'][0], "sometext3")
        self.assertIsInstance(n.get_extra('a')['b'][0], six.string_types)

    def test_versioning_lowlevel(self):
        """
        Checks the versioning.
        """
        a = orm.Data()
        a.store()

        # Even if I stored many attributes, this should stay at 1
        self.assertEquals(a.version, 1)

        a.label = "label1"
        a.label = "label2"
        self.assertEquals(a.version, 3)

        a.description = "desc1"
        a.description = "desc2"
        a.description = "desc3"
        self.assertEquals(a.version, 6)

    def test_comments(self):
        # This is the best way to compare dates with the stored ones, instead
        # of directly loading datetime.datetime.now(), or you can get a
        # "can't compare offset-naive and offset-aware datetimes" error
        from datetime import timedelta
        from aiida.common import timezone
        from time import sleep

        user = orm.User.objects.get_default()

        a = orm.Data()
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
        from aiida.common.exceptions import NotExistent, MultipleObjectsError, InputValidationError

        # Create some code nodes
        code1 = orm.Code()
        code1.set_remote_computer_exec((self.computer, '/bin/true'))
        code1.label = 'test_code1'
        code1.store()

        code2 = orm.Code()
        code2.set_remote_computer_exec((self.computer, '/bin/true'))
        code2.label = 'test_code2'
        code2.store()

        # Test that the code1 can be loaded correctly with its label
        q_code_1 = orm.Code.get_from_string(code1.label)
        self.assertEquals(q_code_1.id, code1.id)
        self.assertEquals(q_code_1.label, code1.label)
        self.assertEquals(q_code_1.get_remote_exec_path(), code1.get_remote_exec_path())

        # Test that the code2 can be loaded correctly with its label
        q_code_2 = orm.Code.get_from_string(code2.label + '@' + self.computer.get_name())
        self.assertEquals(q_code_2.id, code2.id)
        self.assertEquals(q_code_2.label, code2.label)
        self.assertEquals(q_code_2.get_remote_exec_path(), code2.get_remote_exec_path())

        # Calling get_from_string for a non string type raises exception
        with self.assertRaises(InputValidationError):
            orm.Code.get_from_string(code1.id)

        # Test that the lookup of a nonexistent code works as expected
        with self.assertRaises(NotExistent):
            orm.Code.get_from_string('nonexistent_code')

        # Add another code with the label of code1
        code3 = orm.Code()
        code3.set_remote_computer_exec((self.computer, '/bin/true'))
        code3.label = 'test_code1'
        code3.store()

        # Query with the common label
        with self.assertRaises(MultipleObjectsError):
            orm.Code.get_from_string(code3.label)

    def test_code_loading_using_get(self):
        """
        Checks that the method Code.get(pk) works correctly.
        """
        from aiida.common.exceptions import NotExistent, MultipleObjectsError

        # Create some code nodes
        code1 = orm.Code()
        code1.set_remote_computer_exec((self.computer, '/bin/true'))
        code1.label = 'test_code3'
        code1.store()

        code2 = orm.Code()
        code2.set_remote_computer_exec((self.computer, '/bin/true'))
        code2.label = 'test_code4'
        code2.store()

        # Test that the code1 can be loaded correctly with its label only
        q_code_1 = orm.Code.get(label=code1.label)
        self.assertEquals(q_code_1.id, code1.id)
        self.assertEquals(q_code_1.label, code1.label)
        self.assertEquals(q_code_1.get_remote_exec_path(), code1.get_remote_exec_path())

        # Test that the code1 can be loaded correctly with its id/pk
        q_code_1 = orm.Code.get(code1.id)
        self.assertEquals(q_code_1.id, code1.id)
        self.assertEquals(q_code_1.label, code1.label)
        self.assertEquals(q_code_1.get_remote_exec_path(), code1.get_remote_exec_path())

        # Test that the code2 can be loaded correctly with its label and computername
        q_code_2 = orm.Code.get(label=code2.label, machinename=self.computer.get_name())
        self.assertEquals(q_code_2.id, code2.id)
        self.assertEquals(q_code_2.label, code2.label)
        self.assertEquals(q_code_2.get_remote_exec_path(), code2.get_remote_exec_path())

        # Test that the code2 can be loaded correctly with its id/pk
        q_code_2 = orm.Code.get(code2.id)
        self.assertEquals(q_code_2.id, code2.id)
        self.assertEquals(q_code_2.label, code2.label)
        self.assertEquals(q_code_2.get_remote_exec_path(), code2.get_remote_exec_path())

        # Test that the lookup of a nonexistent code works as expected
        with self.assertRaises(NotExistent):
            orm.Code.get(label='nonexistent_code')

        # Add another code with the label of code1
        code3 = orm.Code()
        code3.set_remote_computer_exec((self.computer, '/bin/true'))
        code3.label = 'test_code3'
        code3.store()

        # Query with the common label
        with self.assertRaises(MultipleObjectsError):
            orm.Code.get(label=code3.label)

        # Add another code whose label is equal to pk of another code
        pk_label_duplicate = code1.pk
        code4 = orm.Code()
        code4.set_remote_computer_exec((self.computer, '/bin/true'))
        code4.label = pk_label_duplicate
        code4.store()

        # Since the label of code4 is identical to the pk of code1, calling
        # Code.get(pk_label_duplicate) should return code1, as the pk takes
        # precedence
        q_code_4 = orm.Code.get(code4.label)
        self.assertEquals(q_code_4.id, code1.id)
        self.assertEquals(q_code_4.label, code1.label)
        self.assertEquals(q_code_4.get_remote_exec_path(), code1.get_remote_exec_path())

    def test_code_description(self):
        """
        This test checks that the code description is retrieved correctly
        when the code is searched with its id and label.
        """
        # Create a code node
        code = orm.Code()
        code.set_remote_computer_exec((self.computer, '/bin/true'))
        code.label = 'test_code_label'
        code.description = 'test code description'
        code.store()

        q_code1 = orm.Code.get(label=code.label)
        self.assertEquals(code.description, str(q_code1.description))

        q_code2 = orm.Code.get(code.id)
        self.assertEquals(code.description, str(q_code2.description))

    def test_list_for_plugin(self):
        """
        This test checks the Code.list_for_plugin()
        """
        code1 = orm.Code()
        code1.set_remote_computer_exec((self.computer, '/bin/true'))
        code1.label = 'test_code1'
        code1.set_input_plugin_name('plugin_name')
        code1.store()

        code2 = orm.Code()
        code2.set_remote_computer_exec((self.computer, '/bin/true'))
        code2.label = 'test_code2'
        code2.set_input_plugin_name('plugin_name')
        code2.store()

        retrieved_pks = set(orm.Code.list_for_plugin('plugin_name', labels=False))
        self.assertEqual(retrieved_pks, set([code1.pk, code2.pk]))

        retrieved_labels = set(orm.Code.list_for_plugin('plugin_name', labels=True))
        self.assertEqual(retrieved_labels, set([code1.label, code2.label]))

    def test_load_node(self):
        """
        Tests the load node functionality
        """
        from aiida.common.exceptions import NotExistent

        # I only need one node to test
        node = orm.Data().store()
        uuid_stored = node.uuid  # convenience to store the uuid
        # Simple test to see whether I load correctly from the pk:
        self.assertEqual(uuid_stored, orm.load_node(pk=node.pk).uuid)
        # Testing the loading with the uuid:
        self.assertEqual(uuid_stored, orm.load_node(uuid=uuid_stored).uuid)

        # Here I'm testing whether loading the node with the beginnings of a uuid works
        for i in range(10, len(uuid_stored), 2):
            start_uuid = uuid_stored[:i]
            self.assertEqual(uuid_stored, orm.load_node(uuid=start_uuid).uuid)

        # Testing whether loading the node with part of UUID works, removing the dashes
        for i in range(10, len(uuid_stored), 2):
            start_uuid = uuid_stored[:i].replace('-', '')
            self.assertEqual(uuid_stored, orm.load_node(uuid=start_uuid).uuid)
            # If I don't allow load_node to fix the dashes, this has to raise:
            with self.assertRaises(NotExistent):
                orm.load_node(uuid=start_uuid, query_with_dashes=False)

        # Now I am reverting the order of the uuid, this will raise a NotExistent error:
        with self.assertRaises(NotExistent):
            orm.load_node(uuid=uuid_stored[::-1])

        # I am giving a non-sensical pk, this should also raise
        with self.assertRaises(NotExistent):
            orm.load_node(-1)

        # Last check, when asking for specific subclass, this should raise:
        for spec in (node.pk, uuid_stored):
            with self.assertRaises(NotExistent):
                orm.load_node(spec, sub_classes=(orm.ArrayData,))

    @unittest.skip('open issue JobCalculations cannot be stored')
    def test_load_unknown_calculation_type(self):
        """
        Test that the loader will choose a common calculation ancestor for an unknown data type.
        For the case where, e.g., the user doesn't have the necessary plugin.
        """
        from aiida.plugins import CalculationFactory

        TemplateReplacerCalc = CalculationFactory('templatereplacer')
        testcalc = TemplateReplacerCalc(computer=self.computer)
        testcalc.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        testcalc.store()

        # compare if plugin exist
        obj = orm.load_node(uuid=testcalc.uuid)
        self.assertEqual(type(testcalc), type(obj))

        # Create a custom calculation type that inherits from CalcJobNode but change the plugin type string
        class TestCalculation(orm.CalcJobNode):
            pass

        TestCalculation._plugin_type_string = 'nodes.process.calculation.calcjob.notexisting.TemplatereplacerCalculation.'
        TestCalculation._query_type_string = 'nodes.process.calculation.calcjob.notexisting.TemplatereplacerCalculation'

        jobcalc = orm.CalcJobNode(computer=self.computer)
        jobcalc.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        jobcalc.store()

        testcalc = TestCalculation(computer=self.computer)
        testcalc.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        testcalc.store()

        # Changed node should return CalcJobNode type as its plugin does not exist
        obj = orm.load_node(uuid=testcalc.uuid)
        self.assertEqual(type(jobcalc), type(obj))

    def test_load_unknown_data_type(self):
        """
        Test that the loader will choose a common data ancestor for an unknown data type.
        For the case where, e.g., the user doesn't have the necessary plugin.
        """
        from aiida.plugins import DataFactory

        KpointsData = DataFactory('array.kpoints')
        kpoint = KpointsData().store()

        # compare if plugin exist
        obj = orm.load_node(uuid=kpoint.uuid)
        self.assertEqual(type(kpoint), type(obj))

        class TestKpointsData(KpointsData):
            pass

        # change node type and save in database again
        TestKpointsData().store()

        # changed node should return data node as its plugin is not exist
        obj = orm.load_node(uuid=kpoint.uuid)
        self.assertEqual(type(kpoint), type(obj))

        # for node
        n1 = orm.Data().store()
        obj = orm.load_node(n1.uuid)
        self.assertEqual(type(n1), type(obj))


class TestSubNodesAndLinks(AiidaTestCase):

    def test_cachelink(self):
        """
        Test the proper functionality of the links cache, with different
        scenarios.
        """
        n1 = orm.Data()
        n2 = orm.Data()
        n3 = orm.Data().store()
        n4 = orm.Data().store()
        endcalc = orm.CalculationNode()

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
        n1 = orm.Data()
        n2 = orm.Data().store()
        endcalc = orm.CalculationNode()

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
        n1 = orm.CalculationNode()
        n2 = orm.Data()
        endcalc = orm.CalculationNode()

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

    # pylint: disable=unused-variable,no-member,no-self-use
    def test_calculation_load(self):
        from aiida.orm import CalcJobNode

        # I check with a string, with an object and with the computer pk/id
        calc = CalcJobNode(computer=self.computer)
        calc.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        calc.store()

        with self.assertRaises(Exception):
            # I should get an error if I ask for a computer id/pk that doesn't exist
            CalcJobNode(computer=self.computer.id + 100000).store()

    def test_links_label_constraints(self):
        d1 = orm.Data().store()
        d1bis = orm.Data().store()
        calc = orm.CalculationNode().store()
        d2 = orm.Data().store()
        d3 = orm.Data().store()
        d4 = orm.Data().store()
        calc2a = orm.CalculationNode().store()
        calc2b = orm.CalculationNode().store()

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
        n1 = orm.WorkflowNode().store()
        n2 = orm.WorkflowNode().store()
        n3 = orm.WorkflowNode().store()
        n4 = orm.WorkflowNode().store()
        n5 = orm.WorkflowNode().store()
        n6 = orm.WorkflowNode().store()
        n7 = orm.WorkflowNode().store()
        n8 = orm.WorkflowNode().store()
        n9 = orm.WorkflowNode().store()
        data = orm.Data().store()

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

    def test_link_with_unstored(self):
        """
        It is possible to store links between nodes even if they are unstored these links are cached.
        """
        n1 = orm.Data()
        n2 = orm.WorkflowNode()
        n3 = orm.CalculationNode()
        n4 = orm.Data()

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
        n1 = orm.CalculationNode()
        n2 = orm.CalculationNode()
        n3 = orm.Data()

        # Caching the links
        n3.add_incoming(n1, link_type=LinkType.CREATE, link_label='CREATE')
        with self.assertRaises(ValueError):
            n3.add_incoming(n2, link_type=LinkType.CREATE, link_label='CREATE')

    def test_valid_links(self):
        import tempfile
        from aiida.plugins import DataFactory

        SinglefileData = DataFactory('singlefile')

        # I create some objects
        d1 = orm.Data().store()
        with tempfile.NamedTemporaryFile('w+') as handle:
            d2 = SinglefileData(file=handle).store()

        unsavedcomputer = orm.Computer(name='localhost2', hostname='localhost', scheduler_type='direct', transport_type='local')

        with self.assertRaises(ValueError):
            # I need to save the localhost entry first
            orm.CalcJobNode(computer=unsavedcomputer).store()

        # Load calculations with two different ways
        calc = orm.CalcJobNode(computer=self.computer)
        calc.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        calc.store()

        calc2 = orm.CalcJobNode(computer=self.computer)
        calc2.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        calc2.store()

        calc.add_incoming(d1, link_type=LinkType.INPUT_CALC, link_label='link')
        calc.add_incoming(d2, link_type=LinkType.INPUT_CALC, link_label='some_label')

        # Cannot link to itself
        with self.assertRaises(ValueError):
            d1.add_incoming(d1, link_type=LinkType.INPUT_CALC, link_label='link')

        # I try to add wrong links (data to data, calc to calc, etc.)
        with self.assertRaises(ValueError):
            d2.add_incoming(d1, link_type=LinkType.INPUT_CALC, link_label='link')

        with self.assertRaises(ValueError):
            d1.add_incoming(d2, link_type=LinkType.INPUT_CALC, link_label='link')

        with self.assertRaises(ValueError):
            calc.add_incoming(calc2, link_type=LinkType.INPUT_CALC, link_label='link')

        calc_a = orm.CalcJobNode(computer=self.computer)
        calc_a.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        calc_a.store()
        calc_b = orm.CalcJobNode(computer=self.computer)
        calc_b.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        calc_b.store()

        data_node = orm.Data().store()
        data_node.add_incoming(calc_a, link_type=LinkType.CREATE, link_label='link')
        # A data cannot have two input calculations
        with self.assertRaises(ValueError):
            data_node.add_incoming(calc_b, link_type=LinkType.CREATE, link_label='link')

        calculation_inputs = calc.get_incoming().all()

        # This calculation has two data inputs
        self.assertEquals(len(calculation_inputs), 2)

    def test_check_single_calc_source(self):
        """
        Each data node can only have one input calculation
        """
        d1 = orm.Data().store()

        calc = orm.CalcJobNode(computer=self.computer)
        calc.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        calc.store()
        calc2 = orm.CalcJobNode(computer=self.computer)
        calc2.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})
        calc2.store()

        d1.add_incoming(calc, link_type=LinkType.CREATE, link_label='link')

        # more than one input to the same data object!
        with self.assertRaises(ValueError):
            d1.add_incoming(calc2, link_type=LinkType.CREATE, link_label='link')

    def test_node_get_incoming_outgoing_links(self):
        """
        Test that the link_type parameter in get_incoming and get_outgoing only
        returns those nodes with the correct link type for stored nodes
        """
        node_origin = orm.WorkflowNode().store()
        node_origin2 = orm.WorkflowNode().store()
        node_caller_stored = orm.WorkflowNode().store()
        node_called = orm.WorkflowNode().store()
        node_input_stored = orm.Data().store()
        node_output = orm.Data().store()
        node_return = orm.Data().store()
        node_caller_unstored = orm.WorkflowNode()
        node_input_unstored = orm.Data()

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
        self.assertEquals(len(node_origin.get_incoming(node_class=orm.Node).all()), 3)

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
                orm.load_node(uuid)
            for uuid in uuids_check_deleted:
                # I check that it raises
                with self.assertRaises(NotExistent):
                    orm.load_node(uuid)
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
        in1 = orm.Data().store()
        in2 = orm.Data().store()
        wf = orm.WorkflowNode().store()
        slave1 = orm.WorkflowNode().store()
        outp1 = orm.Data().store()
        outp2 = orm.Data().store()
        slave2 = orm.CalculationNode().store()
        outp3 = orm.Data().store()
        outp4 = orm.Data().store()
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
            orm.Data(),  # 0
            orm.CalculationNode(), orm.CalculationNode(), orm.CalculationNode(),  # 1, 2, 3
            orm.Data(), orm.Data(), orm.Data(),  # 4, 5, 6
            orm.CalculationNode(), orm.CalculationNode(), orm.CalculationNode(),  # 7, 8, 9
            orm.Data(),  # 10
            orm.CalculationNode(),  # 11
            orm.Data(),  # 12
            orm.CalculationNode(),  # 13
            orm.Data(),  # 14
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

    def test_deletion_non_existing_pk(self):
        """Verify that passing a non-existing pk should not raise."""
        nodes = self._create_calls_n_returns_graph()
        existing_pks = [node.pk for node in nodes]

        non_existing_pk = 1

        # Starting from pk=1, find a pk that does not exist
        while(True):
            if non_existing_pk not in existing_pks:
                break

            non_existing_pk += 1

        with Capturing():
            delete_nodes([non_existing_pk], verbosity=2, force=True)

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
        in1, in2, wf = [orm.Data().store(), orm.Data().store(), orm.WorkflowNode().store()]
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
        caller, called = [orm.WorkflowNode().store() for i in range(2)]
        called.add_incoming(caller, link_type=LinkType.CALL_WORK, link_label='link')

        uuids_check_existence = (caller.uuid,)
        uuids_check_deleted = [n.uuid for n in (called,)]

        with Capturing():
            delete_nodes([called.pk], verbosity=2, force=True, follow_returns=True)

        self._check_existence(uuids_check_existence, uuids_check_deleted)
