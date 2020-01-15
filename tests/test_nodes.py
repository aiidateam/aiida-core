# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=too-many-lines,invalid-name,protected-access
# pylint: disable=missing-docstring,too-many-locals,too-many-statements
# pylint: disable=too-many-public-methods
import copy
import io
import tempfile


from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.common.exceptions import InvalidOperation, ModificationNotAllowed, StoringNotAllowed, ValidationError
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
        self.assertEqual(qb.count(), 1)
        self.assertEqual(qb.first()[0], n.id)

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
        f1 = self.create_folderdata_with_empty_file().store()
        f2 = self.create_folderdata_with_empty_folder().store()

        assert (f1.list_object_names('path') == f2.list_object_names('path'))
        assert f1.get_hash() != f2.get_hash()

    def test_updatable_attributes(self):
        """
        Tests that updatable attributes are ignored.
        """
        node = orm.CalculationNode().store()
        hash1 = node.get_hash()
        node.set_process_state('finished')
        hash2 = node.get_hash()
        self.assertNotEqual(hash1, None)
        self.assertEqual(hash1, hash2)


class TestTransitiveNoLoops(AiidaTestCase):
    """
    Test the transitive closure functionality
    """

    def test_loop_not_allowed(self):
        d1 = orm.Data().store()
        c1 = orm.CalculationNode()
        d2 = orm.Data().store()
        c2 = orm.CalculationNode()

        c1.add_incoming(d1, link_type=LinkType.INPUT_CALC, link_label='link')
        c1.store()
        d2.add_incoming(c1, link_type=LinkType.CREATE, link_label='link')
        c2.add_incoming(d2, link_type=LinkType.INPUT_CALC, link_label='link')
        c2.store()

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
            self.assertTrue(isinstance(uuid, str))
            self.assertTrue(isinstance(data.uuid, str))


class TestQueryWithAiidaObjects(AiidaTestCase):
    """
    Test if queries work properly also with aiida.orm.Node classes instead of
    aiida.backends.djsite.db.models.DbNode objects.
    """

    def test_with_subclasses(self):
        from aiida.plugins import DataFactory

        extra_name = self.__class__.__name__ + '/test_with_subclasses'

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
        self.assertEqual(set([i.pk for i in results]), set([a1.pk]))

        # Same query, but by the generic Node class
        qb = orm.QueryBuilder()
        qb.append(orm.Node, filters={'extras': {'has_key': extra_name}})
        results = [_ for [_] in qb.all()]
        self.assertEqual(set([i.pk for i in results]), set([a1.pk, a3.pk, a4.pk]))

        # Same query, but by the Data class
        qb = orm.QueryBuilder()
        qb.append(orm.Data, filters={'extras': {'has_key': extra_name}})
        results = [_ for [_] in qb.all()]
        self.assertEqual(set([i.pk for i in results]), set([a3.pk, a4.pk]))

        # Same query, but by the Dict subclass
        qb = orm.QueryBuilder()
        qb.append(orm.Dict, filters={'extras': {'has_key': extra_name}})
        results = [_ for [_] in qb.all()]
        self.assertEqual(set([i.pk for i in results]), set([a4.pk]))


class TestNodeBasic(AiidaTestCase):
    """
    These tests check the basic features of nodes
    (setting of attributes, copying of files, ...)
    """
    boolval = True
    intval = 123
    floatval = 4.56
    stringval = 'aaaa'
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
    listval = [1, 's', True, None]
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
        self.assertEqual(self.boolval, a.get_attribute('k1'))
        self.assertEqual(self.intval, a.get_attribute('k2'))
        self.assertEqual(self.floatval, a.get_attribute('k3'))
        self.assertEqual(self.stringval, a.get_attribute('k4'))
        self.assertEqual(self.dictval, a.get_attribute('k5'))
        self.assertEqual(self.listval, a.get_attribute('k6'))
        self.assertEqual(self.emptydict, a.get_attribute('k7'))
        self.assertEqual(self.emptylist, a.get_attribute('k8'))
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
        self.assertEqual(a.attributes, target_attrs)

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

        self.assertEqual(a.attributes, {})

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
        self.assertEqual(a.attributes, target_attrs)

    def test_store_object(self):
        """Trying to set objects as attributes should fail, because they are not json-serializable."""
        a = orm.Data()

        a.set_attribute('object', object())
        with self.assertRaises(ValidationError):
            a.store()

        b = orm.Data()
        b.set_attribute('object_list', [object(), object()])
        with self.assertRaises(ValidationError):
            b.store()

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
        self.assertEqual(b.attributes, b_expected_attributes)
        # Note that during copy, I do not copy the extras!
        self.assertEqual({k: v for k, v in b.extras.items()}, {})

        # I store now
        b.store()
        # and I finally add a extras
        b.set_extra('meta', 'textofext')
        b_expected_extras = {'meta': 'textofext', '_aiida_hash': AnyValue()}

        # Now I check that the attributes of the original node have not changed
        self.assertEqual({k: v for k, v in a.attributes.items()}, attrs_to_set)

        # I check then on the 'b' copy
        self.assertEqual({k: v for k, v in b.attributes.items()}, b_expected_attributes)
        self.assertEqual({k: v for k, v in b.extras.items()}, b_expected_extras)

    def test_files(self):
        import tempfile

        a = orm.Data()

        file_content = 'some text ABCDE'
        file_content_different = 'other values 12345'

        with tempfile.NamedTemporaryFile('w+') as handle:
            handle.write(file_content)
            handle.flush()
            a.put_object_from_file(handle.name, 'file1.txt')
            a.put_object_from_file(handle.name, 'file2.txt')

        self.assertEqual(set(a.list_object_names()), set(['file1.txt', 'file2.txt']))
        with a.open('file1.txt') as fhandle:
            self.assertEqual(fhandle.read(), file_content)
        with a.open('file2.txt') as fhandle:
            self.assertEqual(fhandle.read(), file_content)

        b = a.clone()
        self.assertNotEqual(a.uuid, b.uuid)

        # Check that the content is there
        self.assertEqual(set(b.list_object_names()), set(['file1.txt', 'file2.txt']))
        with b.open('file1.txt') as handle:
            self.assertEqual(handle.read(), file_content)
        with b.open('file2.txt') as handle:
            self.assertEqual(handle.read(), file_content)

        # I overwrite a file and create a new one in the clone only
        with tempfile.NamedTemporaryFile(mode='w+') as handle:
            handle.write(file_content_different)
            handle.flush()
            b.put_object_from_file(handle.name, 'file2.txt')
            b.put_object_from_file(handle.name, 'file3.txt')

        # I check the new content, and that the old one has not changed
        self.assertEqual(set(a.list_object_names()), set(['file1.txt', 'file2.txt']))
        with a.open('file1.txt') as handle:
            self.assertEqual(handle.read(), file_content)
        with a.open('file2.txt') as handle:
            self.assertEqual(handle.read(), file_content)
        self.assertEqual(set(b.list_object_names()), set(['file1.txt', 'file2.txt', 'file3.txt']))
        with b.open('file1.txt') as handle:
            self.assertEqual(handle.read(), file_content)
        with b.open('file2.txt') as handle:
            self.assertEqual(handle.read(), file_content_different)
        with b.open('file3.txt') as handle:
            self.assertEqual(handle.read(), file_content_different)

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

        self.assertEqual(set(a.list_object_names()), set(['file1.txt', 'file2.txt']))
        with a.open('file1.txt') as handle:
            self.assertEqual(handle.read(), file_content)
        with a.open('file2.txt') as handle:
            self.assertEqual(handle.read(), file_content)

        self.assertEqual(set(c.list_object_names()), set(['file1.txt', 'file2.txt', 'file4.txt']))
        with c.open('file1.txt') as handle:
            self.assertEqual(handle.read(), file_content_different)
        with c.open('file2.txt') as handle:
            self.assertEqual(handle.read(), file_content)
        with c.open('file4.txt') as handle:
            self.assertEqual(handle.read(), file_content_different)

    def test_folders(self):
        """
        Similar as test_files, but I manipulate a tree of folders
        """
        import os
        import shutil
        import random
        import string

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
        file_content = 'some text ABCDE'
        file_content_different = 'other values 12345'
        with open(os.path.join(tree_1, 'file1.txt'), 'w', encoding='utf8') as fhandle:
            fhandle.write(file_content)
        os.mkdir(os.path.join(tree_1, 'dir1'))
        os.mkdir(os.path.join(tree_1, 'dir1', 'dir2'))
        with open(os.path.join(tree_1, 'dir1', 'file2.txt'), 'w', encoding='utf8') as fhandle:
            fhandle.write(file_content)
        os.mkdir(os.path.join(tree_1, 'dir1', 'dir2', 'dir3'))

        # add the tree to the node
        a.put_object_from_tree(tree_1, 'tree_1')

        # verify if the node has the structure I expect
        self.assertEqual(set(a.list_object_names()), set(['tree_1']))
        self.assertEqual(set(a.list_object_names('tree_1')), set(['file1.txt', 'dir1']))
        self.assertEqual(set(a.list_object_names(os.path.join('tree_1', 'dir1'))), set(['dir2', 'file2.txt']))
        with a.open(os.path.join('tree_1', 'file1.txt')) as fhandle:
            self.assertEqual(fhandle.read(), file_content)
        with a.open(os.path.join('tree_1', 'dir1', 'file2.txt')) as fhandle:
            self.assertEqual(fhandle.read(), file_content)

        # try to exit from the folder
        with self.assertRaises(ValueError):
            a.list_object_names('..')

        # clone into a new node
        b = a.clone()
        self.assertNotEqual(a.uuid, b.uuid)

        # Check that the content is there
        self.assertEqual(set(b.list_object_names('.')), set(['tree_1']))
        self.assertEqual(set(b.list_object_names('tree_1')), set(['file1.txt', 'dir1']))
        self.assertEqual(set(b.list_object_names(os.path.join('tree_1', 'dir1'))), set(['dir2', 'file2.txt']))
        with b.open(os.path.join('tree_1', 'file1.txt')) as fhandle:
            self.assertEqual(fhandle.read(), file_content)
        with b.open(os.path.join('tree_1', 'dir1', 'file2.txt')) as fhandle:
            self.assertEqual(fhandle.read(), file_content)

        # I overwrite a file and create a new one in the copy only
        dir3 = os.path.join(directory, 'dir3')
        os.mkdir(dir3)

        b.put_object_from_tree(dir3, os.path.join('tree_1', 'dir3'))
        # no absolute path here
        with self.assertRaises(ValueError):
            b.put_object_from_tree('dir3', os.path.join('tree_1', 'dir3'))

        stream = io.StringIO(file_content_different)
        b.put_object_from_filelike(stream, 'file3.txt')

        # I check the new content, and that the old one has not changed old
        self.assertEqual(set(a.list_object_names('.')), set(['tree_1']))
        self.assertEqual(set(a.list_object_names('tree_1')), set(['file1.txt', 'dir1']))
        self.assertEqual(set(a.list_object_names(os.path.join('tree_1', 'dir1'))), set(['dir2', 'file2.txt']))
        with a.open(os.path.join('tree_1', 'file1.txt')) as fhandle:
            self.assertEqual(fhandle.read(), file_content)
        with a.open(os.path.join('tree_1', 'dir1', 'file2.txt')) as fhandle:
            self.assertEqual(fhandle.read(), file_content)
        # new
        self.assertEqual(set(b.list_object_names('.')), set(['tree_1', 'file3.txt']))
        self.assertEqual(set(b.list_object_names('tree_1')), set(['file1.txt', 'dir1', 'dir3']))
        self.assertEqual(set(b.list_object_names(os.path.join('tree_1', 'dir1'))), set(['dir2', 'file2.txt']))
        with b.open(os.path.join('tree_1', 'file1.txt')) as fhandle:
            self.assertEqual(fhandle.read(), file_content)
        with b.open(os.path.join('tree_1', 'dir1', 'file2.txt')) as fhandle:
            self.assertEqual(fhandle.read(), file_content)

        # This should in principle change the location of the files, so I recheck
        a.store()

        # I now copy after storing
        c = a.clone()
        # I overwrite a file, create a new one and remove a directory
        # in the copy only
        stream = io.StringIO(file_content_different)
        c.put_object_from_filelike(stream, os.path.join('tree_1', 'file1.txt'))
        c.put_object_from_filelike(stream, os.path.join('tree_1', 'dir1', 'file4.txt'))
        c.delete_object(os.path.join('tree_1', 'dir1', 'dir2'))

        # check old
        self.assertEqual(set(a.list_object_names('.')), set(['tree_1']))
        self.assertEqual(set(a.list_object_names('tree_1')), set(['file1.txt', 'dir1']))
        self.assertEqual(set(a.list_object_names(os.path.join('tree_1', 'dir1'))), set(['dir2', 'file2.txt']))
        with a.open(os.path.join('tree_1', 'file1.txt')) as fhandle:
            self.assertEqual(fhandle.read(), file_content)
        with a.open(os.path.join('tree_1', 'dir1', 'file2.txt')) as fhandle:
            self.assertEqual(fhandle.read(), file_content)

        # check new
        self.assertEqual(set(c.list_object_names('.')), set(['tree_1']))
        self.assertEqual(set(c.list_object_names('tree_1')), set(['file1.txt', 'dir1']))
        self.assertEqual(set(c.list_object_names(os.path.join('tree_1', 'dir1'))), set(['file2.txt', 'file4.txt']))
        with c.open(os.path.join('tree_1', 'file1.txt')) as fhandle:
            self.assertEqual(fhandle.read(), file_content_different)
        with c.open(os.path.join('tree_1', 'dir1', 'file2.txt')) as fhandle:
            self.assertEqual(fhandle.read(), file_content)

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
        self.assertEqual(self.boolval, a.get_attribute('bool'))
        self.assertEqual(self.intval, a.get_attribute('integer'))
        self.assertEqual(self.floatval, a.get_attribute('float'))
        self.assertEqual(self.stringval, a.get_attribute('string'))
        self.assertEqual(self.dictval, a.get_attribute('dict'))
        self.assertEqual(self.listval, a.get_attribute('list'))

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
        self.assertEqual(self.boolval, b.get_attribute('bool'))
        self.assertEqual(self.intval, b.get_attribute('integer'))
        self.assertEqual(self.floatval, b.get_attribute('float'))
        self.assertEqual(self.stringval, b.get_attribute('string'))
        self.assertEqual(self.dictval, b.get_attribute('dict'))
        self.assertEqual(self.listval, b.get_attribute('list'))

    def test_extra_with_reload(self):
        a = orm.Data()
        a.set_extra('none', None)
        a.set_extra('bool', self.boolval)
        a.set_extra('integer', self.intval)
        a.set_extra('float', self.floatval)
        a.set_extra('string', self.stringval)
        a.set_extra('dict', self.dictval)
        a.set_extra('list', self.listval)

        # Check before storing
        self.assertEqual(self.boolval, a.get_extra('bool'))
        self.assertEqual(self.intval, a.get_extra('integer'))
        self.assertEqual(self.floatval, a.get_extra('float'))
        self.assertEqual(self.stringval, a.get_extra('string'))
        self.assertEqual(self.dictval, a.get_extra('dict'))
        self.assertEqual(self.listval, a.get_extra('list'))

        a.store()

        # Check after storing
        self.assertEqual(self.boolval, a.get_extra('bool'))
        self.assertEqual(self.intval, a.get_extra('integer'))
        self.assertEqual(self.floatval, a.get_extra('float'))
        self.assertEqual(self.stringval, a.get_extra('string'))
        self.assertEqual(self.dictval, a.get_extra('dict'))
        self.assertEqual(self.listval, a.get_extra('list'))

        b = orm.load_node(uuid=a.uuid)
        self.assertIsNone(a.get_extra('none'))
        self.assertEqual(self.boolval, b.get_extra('bool'))
        self.assertEqual(self.intval, b.get_extra('integer'))
        self.assertEqual(self.floatval, b.get_extra('float'))
        self.assertEqual(self.stringval, b.get_extra('string'))
        self.assertEqual(self.dictval, b.get_extra('dict'))
        self.assertEqual(self.listval, b.get_extra('list'))

    def test_get_extras_with_default(self):
        a = orm.Data()
        a.store()
        a.set_extra('a', 'b')

        self.assertEqual(a.get_extra('a'), 'b')
        with self.assertRaises(AttributeError):
            a.get_extra('c')

        self.assertEqual(a.get_extra('c', 'def'), 'def')

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

        self.assertEqual(set(list(a.attributes.keys())), set(attrs_to_set.keys()))
        self.assertEqual(set(list(a.extras.keys())), set(all_extras.keys()))

        self.assertEqual(a.attributes, attrs_to_set)

        self.assertEqual(a.extras, all_extras)

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

        self.assertEqual({k: v for k, v in a.extras.items()}, all_extras)

        # I pregenerate it, it cannot change during iteration
        list_keys = list(extras_to_set.keys())
        for k in list_keys:
            # I delete one by one the keys and check if the operation is
            # performed correctly
            a.delete_extra(k)
            del all_extras[k]
            self.assertEqual({k: v for k, v in a.extras.items()}, all_extras)

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
            'string': 'a string',
            'dict': {
                'a': 'b',
                'sublist': [1, 2, 3],
                'subdict': {
                    'c': 'd'
                }
            },
            'list': [1, True, 'ggg', {
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

        self.assertEqual(a.extras, all_extras)

        for k, v in new_extras.items():
            # I delete one by one the keys and check if the operation is
            # performed correctly
            a.set_extra(k, v)

        # I update extras_to_set with the new entries, and do the comparison
        # again
        all_extras.update(new_extras)
        self.assertEqual(a.extras, all_extras)

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
        p = orm.Dict(dict={'b': orm.Str('sometext'), 'c': l1})
        p.store()
        self.assertEqual(p.get_attribute('b'), 'sometext')
        self.assertIsInstance(p.get_attribute('b'), str)
        self.assertEqual(p.get_attribute('c'), ['b', [1, 2]])
        self.assertIsInstance(p.get_attribute('c'), (list, tuple))

        # Check also before storing
        n = orm.Data()
        n.set_attribute('a', orm.Str('sometext2'))
        n.set_attribute('b', l2)
        self.assertEqual(n.get_attribute('a').value, 'sometext2')
        self.assertIsInstance(n.get_attribute('a'), orm.Str)
        self.assertEqual(n.get_attribute('b').get_list(), ['f', True, {'gg': None}])
        self.assertIsInstance(n.get_attribute('b'), orm.List)

        # Check also deep in a dictionary/list
        n = orm.Data()
        n.set_attribute('a', {'b': [orm.Str('sometext3')]})
        self.assertEqual(n.get_attribute('a')['b'][0].value, 'sometext3')
        self.assertIsInstance(n.get_attribute('a')['b'][0], orm.Str)
        n.store()
        self.assertEqual(n.get_attribute('a')['b'][0], 'sometext3')
        self.assertIsInstance(n.get_attribute('a')['b'][0], str)

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
        n.set_extra('a', orm.Str('sometext2'))
        n.set_extra('c', l1)
        n.set_extra('d', l2)
        self.assertEqual(n.get_extra('a'), 'sometext2')
        self.assertIsInstance(n.get_extra('a'), str)
        self.assertEqual(n.get_extra('c'), ['b', [1, 2]])
        self.assertIsInstance(n.get_extra('c'), (list, tuple))
        self.assertEqual(n.get_extra('d'), ['f', True, {'gg': None}])
        self.assertIsInstance(n.get_extra('d'), (list, tuple))

        # Check also deep in a dictionary/list
        n = orm.Data()
        n.store()
        n.set_extra('a', {'b': [orm.Str('sometext3')]})
        self.assertEqual(n.get_extra('a')['b'][0], 'sometext3')
        self.assertIsInstance(n.get_extra('a')['b'][0], str)

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
        self.assertEqual(a.get_comments(), [])

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

        self.assertEqual([(i.user.email, i.content) for i in comments], [
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
        self.assertEqual(q_code_1.id, code1.id)
        self.assertEqual(q_code_1.label, code1.label)
        self.assertEqual(q_code_1.get_remote_exec_path(), code1.get_remote_exec_path())

        # Test that the code2 can be loaded correctly with its label
        q_code_2 = orm.Code.get_from_string(code2.label + '@' + self.computer.get_name())
        self.assertEqual(q_code_2.id, code2.id)
        self.assertEqual(q_code_2.label, code2.label)
        self.assertEqual(q_code_2.get_remote_exec_path(), code2.get_remote_exec_path())

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
        self.assertEqual(q_code_1.id, code1.id)
        self.assertEqual(q_code_1.label, code1.label)
        self.assertEqual(q_code_1.get_remote_exec_path(), code1.get_remote_exec_path())

        # Test that the code1 can be loaded correctly with its id/pk
        q_code_1 = orm.Code.get(code1.id)
        self.assertEqual(q_code_1.id, code1.id)
        self.assertEqual(q_code_1.label, code1.label)
        self.assertEqual(q_code_1.get_remote_exec_path(), code1.get_remote_exec_path())

        # Test that the code2 can be loaded correctly with its label and computername
        q_code_2 = orm.Code.get(label=code2.label, machinename=self.computer.get_name())
        self.assertEqual(q_code_2.id, code2.id)
        self.assertEqual(q_code_2.label, code2.label)
        self.assertEqual(q_code_2.get_remote_exec_path(), code2.get_remote_exec_path())

        # Test that the code2 can be loaded correctly with its id/pk
        q_code_2 = orm.Code.get(code2.id)
        self.assertEqual(q_code_2.id, code2.id)
        self.assertEqual(q_code_2.label, code2.label)
        self.assertEqual(q_code_2.get_remote_exec_path(), code2.get_remote_exec_path())

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
        self.assertEqual(q_code_4.id, code1.id)
        self.assertEqual(q_code_4.label, code1.label)
        self.assertEqual(q_code_4.get_remote_exec_path(), code1.get_remote_exec_path())

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
        self.assertEqual(code.description, str(q_code1.description))

        q_code2 = orm.Code.get(code.id)
        self.assertEqual(code.description, str(q_code2.description))

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
        """Test the proper functionality of the links cache, with different scenarios."""
        n1 = orm.Data()
        n2 = orm.Data()
        n3 = orm.Data().store()
        n4 = orm.Data().store()
        endcalc = orm.CalculationNode()

        # Nothing stored
        endcalc.add_incoming(n1, LinkType.INPUT_CALC, 'N1')
        # Try also reverse storage
        endcalc.add_incoming(n2, LinkType.INPUT_CALC, 'N2')

        self.assertEqual(
            set([(i.link_label, i.node.uuid) for i in endcalc.get_incoming()]), set([('N1', n1.uuid), ('N2', n2.uuid)])
        )

        # Endnode not stored yet, n3 and n4 already stored
        endcalc.add_incoming(n3, LinkType.INPUT_CALC, 'N3')
        # Try also reverse storage
        endcalc.add_incoming(n4, LinkType.INPUT_CALC, 'N4')

        self.assertEqual(
            set([(i.link_label, i.node.uuid) for i in endcalc.get_incoming()]),
            set([('N1', n1.uuid), ('N2', n2.uuid), ('N3', n3.uuid), ('N4', n4.uuid)])
        )

        # Some parent nodes are not stored yet
        with self.assertRaises(ModificationNotAllowed):
            endcalc.store()

        self.assertEqual(
            set([(i.link_label, i.node.uuid) for i in endcalc.get_incoming()]),
            set([('N1', n1.uuid), ('N2', n2.uuid), ('N3', n3.uuid), ('N4', n4.uuid)])
        )

        # This will also store n1 and n2!
        endcalc.store_all()

        self.assertEqual(
            set([(i.link_label, i.node.uuid) for i in endcalc.get_incoming()]),
            set([('N1', n1.uuid), ('N2', n2.uuid), ('N3', n3.uuid), ('N4', n4.uuid)])
        )

    def test_store_with_unstored_parents(self):
        """
        I want to check that if parents are unstored I cannot store
        """
        n1 = orm.Data()
        n2 = orm.Data().store()
        endcalc = orm.CalculationNode()

        endcalc.add_incoming(n1, LinkType.INPUT_CALC, 'N1')
        endcalc.add_incoming(n2, LinkType.INPUT_CALC, 'N2')

        # Some parent nodes are not stored yet
        with self.assertRaises(ModificationNotAllowed):
            endcalc.store()

        n1.store()
        # Now I can store
        endcalc.store()

        self.assertEqual(
            set([(i.link_label, i.node.uuid) for i in endcalc.get_incoming()]), set([('N1', n1.uuid), ('N2', n2.uuid)])
        )

    def test_storeall_with_unstored_grandparents(self):
        """
        I want to check that if grandparents are unstored I cannot store_all
        """
        n1 = orm.CalculationNode()
        n2 = orm.Data()
        endcalc = orm.CalculationNode()

        n2.add_incoming(n1, LinkType.CREATE, 'N1')
        endcalc.add_incoming(n2, LinkType.INPUT_CALC, 'N2')

        # Grandparents are unstored
        with self.assertRaises(ModificationNotAllowed):
            endcalc.store_all()

        n1.store()
        # Now it should work
        endcalc.store_all()

        # Check the parents...
        self.assertEqual(set([(i.link_label, i.node.uuid) for i in n2.get_incoming()]), set([('N1', n1.uuid)]))
        self.assertEqual(set([(i.link_label, i.node.uuid) for i in endcalc.get_incoming()]), set([('N2', n2.uuid)]))

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
        calc = orm.CalculationNode()
        d2 = orm.Data().store()
        d3 = orm.Data().store()
        d4 = orm.Data().store()
        calc2a = orm.CalculationNode()
        calc2b = orm.CalculationNode()

        calc.add_incoming(d1, LinkType.INPUT_CALC, link_label='label1')
        with self.assertRaises(ValueError):
            calc.add_incoming(d1bis, LinkType.INPUT_CALC, link_label='label1')
        calc.store()

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
        self.assertEqual(sorted(n2_in_links), sorted([
            ('l1', n1.uuid),
        ]))
        n3_in_links = [(n.link_label, n.node.uuid) for n in n3.get_incoming()]
        self.assertEqual(sorted(n3_in_links), sorted([
            ('l2', n2.uuid),
            ('l3', n1.uuid),
        ]))

        n1_out_links = [(entry.link_label, entry.node.pk) for entry in n1.get_outgoing()]
        self.assertEqual(sorted(n1_out_links), sorted([
            ('l1', n2.pk),
            ('l3', n3.pk),
        ]))
        n2_out_links = [(entry.link_label, entry.node.pk) for entry in n2.get_outgoing()]
        self.assertEqual(sorted(n2_out_links), sorted([('l2', n3.pk)]))

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

        unsavedcomputer = orm.Computer(
            name='localhost2', hostname='localhost', scheduler_type='direct', transport_type='local'
        )

        with self.assertRaises(ValueError):
            # I need to save the localhost entry first
            orm.CalcJobNode(computer=unsavedcomputer).store()

        # Load calculations with two different ways
        calc = orm.CalcJobNode(computer=self.computer)
        calc.set_option('resources', {'num_machines': 1, 'num_mpiprocs_per_machine': 1})

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

        calc.store()

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
        self.assertEqual(len(calculation_inputs), 2)

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
        node_origin = orm.WorkflowNode()
        node_origin2 = orm.WorkflowNode()
        node_caller_stored = orm.WorkflowNode().store()
        node_called = orm.WorkflowNode()
        node_input_stored = orm.Data().store()
        node_output = orm.Data().store()
        node_return = orm.Data().store()

        # Input links of node_origin
        node_origin.add_incoming(node_caller_stored, link_type=LinkType.CALL_WORK, link_label='caller_stored')
        node_origin.add_incoming(node_input_stored, link_type=LinkType.INPUT_WORK, link_label='input_stored')
        node_origin.store()

        node_origin2.add_incoming(node_caller_stored, link_type=LinkType.CALL_WORK, link_label='caller_unstored')
        node_origin2.store()

        # Output links of node_origin
        node_called.add_incoming(node_origin, link_type=LinkType.CALL_WORK, link_label='called')
        node_called.store()
        node_output.add_incoming(node_origin, link_type=LinkType.RETURN, link_label='return1')
        node_return.add_incoming(node_origin, link_type=LinkType.RETURN, link_label='return2')

        # All incoming and outgoing
        self.assertEqual(len(node_origin.get_incoming().all()), 2)
        self.assertEqual(len(node_origin.get_outgoing().all()), 3)

        # Link specific incoming
        self.assertEqual(len(node_origin.get_incoming(link_type=LinkType.CALL_WORK).all()), 1)
        self.assertEqual(len(node_origin2.get_incoming(link_type=LinkType.CALL_WORK).all()), 1)
        self.assertEqual(len(node_origin.get_incoming(link_type=LinkType.INPUT_WORK).all()), 1)
        self.assertEqual(len(node_origin.get_incoming(link_label_filter='in_ut%').all()), 1)
        self.assertEqual(len(node_origin.get_incoming(node_class=orm.Node).all()), 2)

        # Link specific outgoing
        self.assertEqual(len(node_origin.get_outgoing(link_type=LinkType.CALL_WORK).all()), 1)
        self.assertEqual(len(node_origin.get_outgoing(link_type=LinkType.RETURN).all()), 2)


class AnyValue:
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

        for uuid in uuids_check_existence:
            # This will raise if node is not existent:
            orm.load_node(uuid)
        for uuid in uuids_check_deleted:
            # I check that it raises
            with self.assertRaises(NotExistent):
                orm.load_node(uuid)

    def test_deletion_non_existing_pk(self):
        """Verify that passing a non-existing pk should not raise."""
        non_existing_pk = -1
        with Capturing():
            delete_nodes([non_existing_pk], force=True)

#   TEST BASIC CASES

    def _create_simple_graph(self):
        """
        Creates a simple graph which has one parent workflow (WN2) that calls a child
        workflow (WN1) and then a calculation (CN2). The child workflow (WN1) calls
        its own calculation (CN1). There is one input data node (DNI), on middle data
        node (DNM) and one output data node (DNO). There is at least one link of each
        type and there are two "one-step" calculation calls (WN1 -> CN1 and WN2 -> CN2)
        and one "two-step" calculation call (WN2 -> WN1 -> CN1).

        The existing links are:

        * CALL_WORK from WN2 to WN1.
        * CALL_CALC from WN2 to CN2.
        * CALL_CALC from WN1 to CN1.
        * INPUT_WORK from DNI to WN1 and RETURN from WN1 to DNM.
        * INPUT_WORK from DNI to WN2 and RETURN from WN2 to DNO.
        * INPUT_CALC from DNI to CN1 and CREATE from CN1 to DNM.
        * INPUT_CALC from DNM to CN2 and CREATE from CN2 to DNO.

        And this graph looks like this::

                            input_work             +-----+              return
               +---------------------------------> | WN2 | ----------------------------------+
               |                                   +-----+                                   |
               |                        call_work     |      call_calc                       |
               |                    +-----------------+--------------------+                 |
               |                    |                                      |                 |
               |                    v                                      |                 |
               |    input_work   +-----+    return                         |                 |
               +---------------> | WN1 | -------------+                    |                 |
               |                 +-----+              |                    |                 |
               |                    |                 |                    |                 |
               |                    | call_calc       |                    |                 |
               |                    |                 |                    |                 |
               |                    v                 v                    v                 v
            +-----+  input_calc  +-----+  create   +-----+  input_calc  +-----+  create   +-----+
            | DNI | -----------> | CN1 | --------> | DNM | -----------> | CN2 | --------> | DNO |
            +-----+              +-----+           +-----+              +-----+           +-----+
        """

        dni = orm.Data().store()
        dnm = orm.Data().store()
        dno = orm.Data().store()

        cn1 = orm.CalculationNode()
        cn2 = orm.CalculationNode()
        wn1 = orm.WorkflowNode()
        wn2 = orm.WorkflowNode()

        wn1.add_incoming(dni, link_type=LinkType.INPUT_WORK, link_label='inpwork1')
        wn2.add_incoming(dni, link_type=LinkType.INPUT_WORK, link_label='inpwork2')
        cn1.add_incoming(dni, link_type=LinkType.INPUT_CALC, link_label='inpcalc1')
        cn2.add_incoming(dnm, link_type=LinkType.INPUT_CALC, link_label='inpcalc2')

        cn1.add_incoming(wn1, link_type=LinkType.CALL_CALC, link_label='callcalc1')
        cn2.add_incoming(wn2, link_type=LinkType.CALL_CALC, link_label='callcalc2')
        wn1.add_incoming(wn2, link_type=LinkType.CALL_WORK, link_label='callwork0')

        wn2.store()
        wn1.store()
        cn2.store()
        cn1.store()

        dnm.add_incoming(cn1, link_type=LinkType.CREATE, link_label='create1')
        dnm.add_incoming(wn1, link_type=LinkType.RETURN, link_label='return1')
        dno.add_incoming(cn2, link_type=LinkType.CREATE, link_label='create2')
        dno.add_incoming(wn2, link_type=LinkType.RETURN, link_label='return2')

        return dni, dnm, dno, cn1, cn2, wn1, wn2

    def test_delete_cases(self):
        """
        Using a simple graph to test all the conditions established for the
        consistent deletion of nodes. The first part tests the default behavior,
        which is to delete every node within the highest level workflows that
        link to the targetted nodes (except for non targetted inputs).
        The second part tests the available options to customize deletion in
        their expected use cases.
        """

        # By default, targetting any workflow will propagate to any incoming or
        # outgoing workflows connected to it, therefore resulting in the deletion
        # of the highest level workflow that contains the targetted workflow and
        # of every other workflow called within it.
        # This will also delete any calculation called by all those workflows, and
        # also of any data node that was created by those calculations.
        # The end result is the deletion of all nodes contained within the highest
        # level workflow, except for the inputs that were not targetted.
        di, dm, do, c1, c2, w1, w2 = self._create_simple_graph()
        uuids_check_existence = [n.uuid for n in [di]]
        uuids_check_deleted = [n.uuid for n in [dm, do, c1, c2, w1, w2]]
        with Capturing():
            delete_nodes([w1.pk], force=True)
        self._check_existence(uuids_check_existence, uuids_check_deleted)

        di, dm, do, c1, c2, w1, w2 = self._create_simple_graph()
        uuids_check_existence = [n.uuid for n in [di]]
        uuids_check_deleted = [n.uuid for n in [dm, do, c1, c2, w1, w2]]
        with Capturing():
            delete_nodes([w2.pk], force=True)
        self._check_existence(uuids_check_existence, uuids_check_deleted)

        # By default, targetting a calculation will have the same effect because
        # it will also delete any calling workflows and therefore the previously
        # described chain will activate.
        di, dm, do, c1, c2, w1, w2 = self._create_simple_graph()
        uuids_check_existence = [n.uuid for n in [di]]
        uuids_check_deleted = [n.uuid for n in [dm, do, c1, c2, w1, w2]]
        with Capturing():
            delete_nodes([c1.pk], force=True)
        self._check_existence(uuids_check_existence, uuids_check_deleted)

        di, dm, do, c1, c2, w1, w2 = self._create_simple_graph()
        uuids_check_existence = [n.uuid for n in [di]]
        uuids_check_deleted = [n.uuid for n in [dm, do, c1, c2, w1, w2]]
        with Capturing():
            delete_nodes([c2.pk], force=True)
        self._check_existence(uuids_check_existence, uuids_check_deleted)

        # By default, targetting a data node will also have the same effect because
        # it will also delete the calculation that created it, and therefore the
        # previously described chain will activate.
        di, dm, do, c1, c2, w1, w2 = self._create_simple_graph()
        uuids_check_existence = [n.uuid for n in []]
        uuids_check_deleted = [n.uuid for n in [di, dm, do, c1, c2, w1, w2]]
        with Capturing():
            delete_nodes([di.pk], force=True)
        self._check_existence(uuids_check_existence, uuids_check_deleted)

        di, dm, do, c1, c2, w1, w2 = self._create_simple_graph()
        uuids_check_existence = [n.uuid for n in [di]]
        uuids_check_deleted = [n.uuid for n in [dm, do, c1, c2, w1, w2]]
        with Capturing():
            delete_nodes([dm.pk], force=True)
        self._check_existence(uuids_check_existence, uuids_check_deleted)

        di, dm, do, c1, c2, w1, w2 = self._create_simple_graph()
        uuids_check_existence = [n.uuid for n in [di]]
        uuids_check_deleted = [n.uuid for n in [dm, do, c1, c2, w1, w2]]
        with Capturing():
            delete_nodes([do.pk], force=True)
        self._check_existence(uuids_check_existence, uuids_check_deleted)

        # Data deletion within the highest level workflow can be prevented by
        # disabling the rule that follows forward any creation link. This will
        # still delete any data node explicitly required.
        di, dm, do, c1, c2, w1, w2 = self._create_simple_graph()
        uuids_check_existence = [n.uuid for n in [di, dm, do]]
        uuids_check_deleted = [n.uuid for n in [c1, c2, w1, w2]]
        with Capturing():
            delete_nodes([w2.pk], force=True, create_forward=False)
        self._check_existence(uuids_check_existence, uuids_check_deleted)

        di, dm, do, c1, c2, w1, w2 = self._create_simple_graph()
        uuids_check_existence = [n.uuid for n in [dm, do]]
        uuids_check_deleted = [n.uuid for n in [di, c1, c2, w1, w2]]
        with Capturing():
            delete_nodes([di.pk], force=True, create_forward=False)
        self._check_existence(uuids_check_existence, uuids_check_deleted)

        # On the other hand, the whole data provenance can be protected by
        # disabling the rule to go forwards through the call_calc links.
        # Again, this still allows to target specific sections to be deleted
        # (which will also delete any forward data provenance because the rules
        # to traverse 'create' and 'input_calc' links forward are always on).
        di, dm, do, c1, c2, w1, w2 = self._create_simple_graph()
        uuids_check_existence = [n.uuid for n in [di, dm, do, c1, c2]]
        uuids_check_deleted = [n.uuid for n in [w1, w2]]
        with Capturing():
            delete_nodes([w2.pk], force=True, call_calc_forward=False)
        self._check_existence(uuids_check_existence, uuids_check_deleted)

        di, dm, do, c1, c2, w1, w2 = self._create_simple_graph()
        uuids_check_existence = [n.uuid for n in [di, dm, c1]]
        uuids_check_deleted = [n.uuid for n in [do, c2, w1, w2]]
        with Capturing():
            delete_nodes([c2.pk], force=True, call_calc_forward=False)
        self._check_existence(uuids_check_existence, uuids_check_deleted)

        # Another posibility which also exists, though may have more limited
        # uses, is to protect underlying workflows by disabling the rule that
        # allows the traversal of 'call_work' links forward. This alone will
        # still delete any calculations that are directly called by any of the
        # workflows that are targeted (or that call the targeted ones), but
        # this can be combined with any of the previous cases as well.
        di, dm, do, c1, c2, w1, w2 = self._create_simple_graph()
        uuids_check_existence = [n.uuid for n in [di, dm, c1, w1]]
        uuids_check_deleted = [n.uuid for n in [do, c2, w2]]
        with Capturing():
            delete_nodes([w2.pk], force=True, call_work_forward=False)
        self._check_existence(uuids_check_existence, uuids_check_deleted)

        di, dm, do, c1, c2, w1, w2 = self._create_simple_graph()
        uuids_check_existence = [n.uuid for n in [di, dm, do, c1, w1]]
        uuids_check_deleted = [n.uuid for n in [c2, w2]]
        with Capturing():
            delete_nodes([w2.pk], force=True, call_work_forward=False, create_forward=False)
        self._check_existence(uuids_check_existence, uuids_check_deleted)

        di, dm, do, c1, c2, w1, w2 = self._create_simple_graph()
        uuids_check_existence = [n.uuid for n in [di, dm, do, c1, c2, w1]]
        uuids_check_deleted = [n.uuid for n in [w2]]
        with Capturing():
            delete_nodes([w2.pk], force=True, call_work_forward=False, call_calc_forward=False)
        self._check_existence(uuids_check_existence, uuids_check_deleted)

    def _create_indep2w_graph(self):
        """
        Creates a simple graph with one workflow handling two independent workflows
        (with one simple calculation each). It was designed and used mainly to point
        out how the deletion behaviour works when setting call_work_forward to true:
        in this case if PWA is deleted, the somewhat independent PWB will also be
        deleted. Even worse, if call_calc_forward was also enabled, even the data
        provenance controlled by PWB (PCB and DOB) would be deleted as well.
        The graph is composed of the following nodes:

        * PW0: parent workflow, which calls both PWA and PWB.
        * PWA: it has a single call to PCA, with input DIA and output DOA.
        * PWB: it has a single call to PCB, with input DIB and output DOB.

        This should look something like this (you can find a nicer version of
        this graph in the documentation, as it is the same used to explain the
        consistency rules)::

              +-------------------------------------+   +-------------------------------------+
              |     inwork                          |   |                          inwork     |
              |                                     v   v                                     |
              |                      call_work    +-------+    call_work                      |
              |                 +---------------- |  PW0  | -----------------+                |
              |                 |                 +-------+                  |                |
              |                 v                  |     |                   v                |
              |     inwork    +---+    return      |     |      return    +---+    inwork     |
              | +-----------> |PWA| ------------+  |     |  +-----------> |PWB| ------------+ |
              | |             +---+             |  |     |  |             +---+             | |
              | |               |               |  |     |  |               |               | |
              | |               | call_calc     |  |     |  |               | call_calc     | |
              | |               |               |  |     |  |               |               | |
              | |               v               v  v     v  v               v               | |
            +-----+  incall   +---+  create   +-----+   +-----+   create  +---+   incall  +-----+
            | DIA | --------> |PCA| --------> | DOA |   | DOB | <-------- |PCB| <-------- | DIB |
            +-----+           +---+           +-----+   +-----+           +---+           +-----+

        """

        dia = orm.Data().store()
        dib = orm.Data().store()

        pw0 = orm.WorkflowNode()
        pw0.add_incoming(dia, link_type=LinkType.INPUT_WORK, link_label='inpwork0a')
        pw0.add_incoming(dib, link_type=LinkType.INPUT_WORK, link_label='inpwork0b')
        pw0.store()

        pwa = orm.WorkflowNode()
        pwa.add_incoming(dia, link_type=LinkType.INPUT_WORK, link_label='inpworka')
        pwa.add_incoming(pw0, link_type=LinkType.CALL_WORK, link_label='callworka')
        pwa.store()

        pwb = orm.WorkflowNode()
        pwb.add_incoming(dib, link_type=LinkType.INPUT_WORK, link_label='inpworkb')
        pwb.add_incoming(pw0, link_type=LinkType.CALL_WORK, link_label='callworkb')
        pwb.store()

        pca = orm.CalculationNode()
        pca.add_incoming(dia, link_type=LinkType.INPUT_CALC, link_label='inpcalca')
        pca.add_incoming(pwa, link_type=LinkType.CALL_CALC, link_label='calla')
        pca.store()

        pcb = orm.CalculationNode()
        pcb.add_incoming(dib, link_type=LinkType.INPUT_CALC, link_label='inpcalcb')
        pcb.add_incoming(pwb, link_type=LinkType.CALL_CALC, link_label='callb')
        pcb.store()

        doa = orm.Data().store()
        doa.add_incoming(pca, link_type=LinkType.CREATE, link_label='createa')
        doa.add_incoming(pwa, link_type=LinkType.RETURN, link_label='returna')
        doa.add_incoming(pw0, link_type=LinkType.RETURN, link_label='return0a')

        dob = orm.Data().store()
        dob.add_incoming(pcb, link_type=LinkType.CREATE, link_label='createb')
        dob.add_incoming(pwb, link_type=LinkType.RETURN, link_label='returnb')
        dob.add_incoming(pw0, link_type=LinkType.RETURN, link_label='return0b')

        return dia, doa, pca, pwa, dib, dob, pcb, pwb, pw0

    def test_indep2w(self):
        """
        Using a simple graph, will test the behaviour when deleting an independent
        workflow that is somehow connected to another one simply by being part of
        the the same parent workflow (i.e. two workflows connected by the logical
        provenance but not the data provenance).
        """

        # First of all one should notice that enabling all forward traverse rules
        # (call_calc, call_work, create) will end up deleting everything under both
        # workflows no matter what is targetted.
        dia, doa, pca, pwa, dib, dob, pcb, pwb, pw0 = self._create_indep2w_graph()
        uuids_check_existence = [n.uuid for n in [dia, dib]]
        uuids_check_deleted = [n.uuid for n in [doa, pca, pwa, dob, pcb, pwb, pw0]]
        with Capturing():
            delete_nodes((pca.pk,), force=True, create_forward=True, call_calc_forward=True, call_work_forward=True)
        self._check_existence(uuids_check_existence, uuids_check_deleted)

        dia, doa, pca, pwa, dib, dob, pcb, pwb, pw0 = self._create_indep2w_graph()
        uuids_check_existence = [n.uuid for n in [dia, dib]]
        uuids_check_deleted = [n.uuid for n in [doa, pca, pwa, dob, pcb, pwb, pw0]]
        with Capturing():
            delete_nodes((pwa.pk,), force=True, create_forward=True, call_calc_forward=True, call_work_forward=True)
        self._check_existence(uuids_check_existence, uuids_check_deleted)

        # In this particular case where the workflow (pwa) only calls a single
        # calculation (pca), one could target either and obtain the desired result
        # just by disabling the call_work forward traverse.
        # This solution stops being viable in the cases with more calculations that
        # are directly called both by pwa and pw0 (which will have problems with the
        # call_calc traversal), or having other subworkflows being called by pwa that
        # need to be deleted as well (which, on the other hand, will have problems
        # with the call_work traversal).
        dia, doa, pca, pwa, dib, dob, pcb, pwb, pw0 = self._create_indep2w_graph()
        uuids_check_existence = [n.uuid for n in [dia, dib, dob, pcb, pwb]]
        uuids_check_deleted = [n.uuid for n in [doa, pca, pwa, pw0]]
        with Capturing():
            delete_nodes((pca.pk,), force=True, create_forward=True, call_calc_forward=True, call_work_forward=False)
        self._check_existence(uuids_check_existence, uuids_check_deleted)

        dia, doa, pca, pwa, dib, dob, pcb, pwb, pw0 = self._create_indep2w_graph()
        uuids_check_existence = [n.uuid for n in [dia, dib, dob, pcb, pwb]]
        uuids_check_deleted = [n.uuid for n in [doa, pca, pwa, pw0]]
        with Capturing():
            delete_nodes((pwa.pk,), force=True, create_forward=True, call_calc_forward=True, call_work_forward=False)
        self._check_existence(uuids_check_existence, uuids_check_deleted)

        # The best and most controlled way to deal with this situation would be
        # to use a multiple step approach: first deleting with the safest setup
        # ONLY the workflow that calls the one that needs to be deleted, and then
        # actually deleting that workflow with the normal setup.
        # (Some of the rules disabled in the first delete may not have been needed
        # for this particular case, but this setup would be more generalizable)
        dia, doa, pca, pwa, dib, dob, pcb, pwb, pw0 = self._create_indep2w_graph()

        uuids_check_existence1 = [n.uuid for n in [dia, doa, pca, pwa, dib, dob, pcb, pwb]]
        uuids_check_deleted1 = [n.uuid for n in [pw0]]

        uuids_check_existence2 = [n.uuid for n in [dia, dib, dob, pcb, pwb]]
        uuids_check_deleted2 = [n.uuid for n in [doa, pca, pwa, pw0]]

        with Capturing():
            delete_nodes((pw0.pk,), force=True, create_forward=False, call_calc_forward=False, call_work_forward=False)
        self._check_existence(uuids_check_existence1, uuids_check_deleted1)

        with Capturing():
            delete_nodes((pwa.pk,), force=True, create_forward=True, call_calc_forward=True, call_work_forward=True)
        self._check_existence(uuids_check_existence2, uuids_check_deleted2)

    def _create_looped_graph(self):
        """
        Creates a basic graph with one parent workflow (PWM) which first calls a child
        workflow (PWS) to choose one input from a set (DI1 from DI1-DI3), and then use
        it to perform a calculation (PCS) and obtain an output (DO1). The node PWM will
        call both PWS and PCS itself. The final graph looks like this::

            +-----+     input_work   +-----+                         return
            | DI3 | --+------------> | PWM | -----------------+-----------------+
            +-----+   |              +-----+                  |                 |
                      |                 |                     |                 |
                      |                 | call_work           |                 |
                      |                 v                     |                 |
            +-----+   | input_work   +-----+                  |                 |
            | DI2 | --+------------> | PWS |                  | call_calc       |
            +-----+   |              +-----+                  |                 |
                      |                 |                     |                 |
                      |    (CYCLE)      | return              |                 |
                      |                 v                     v                 v
                      |              +-----+  input_calc   +-----+  create   +-----+
                      +------------- | DI1 | ------------> | PCS | --------> | DO1 |
                                     +-----+               +-----+           +-----+
        """

        di1 = orm.Data().store()
        di2 = orm.Data().store()
        di3 = orm.Data().store()

        pwm = orm.WorkflowNode()
        pwm.add_incoming(di1, link_type=LinkType.INPUT_WORK, link_label='inpwm1')
        pwm.add_incoming(di2, link_type=LinkType.INPUT_WORK, link_label='inpwm2')
        pwm.add_incoming(di3, link_type=LinkType.INPUT_WORK, link_label='inpwm3')
        pwm.store()

        pws = orm.WorkflowNode()
        pws.add_incoming(di1, link_type=LinkType.INPUT_WORK, link_label='inpws1')
        pws.add_incoming(di2, link_type=LinkType.INPUT_WORK, link_label='inpws2')
        pws.add_incoming(di3, link_type=LinkType.INPUT_WORK, link_label='inpws3')
        pws.add_incoming(pwm, link_type=LinkType.CALL_WORK, link_label='callw')
        pws.store()

        di1.add_incoming(pws, link_type=LinkType.RETURN, link_label='outpws')

        pcs = orm.CalculationNode()
        pcs.add_incoming(di1, link_type=LinkType.INPUT_CALC, link_label='inpcs1')
        pcs.add_incoming(pwm, link_type=LinkType.CALL_CALC, link_label='callc')
        pcs.store()

        do1 = orm.Data().store()
        do1.add_incoming(pcs, link_type=LinkType.CREATE, link_label='outpcs')
        do1.add_incoming(pwm, link_type=LinkType.RETURN, link_label='outpwm')

        return di1, di2, di3, do1, pws, pcs, pwm

    def test_loop_cases(self):
        """
        Using a looped graph, will test the behaviour when deleting nodes that
        can be both input and output of a workflow.
        """

        # Deleting any of the nodes while having enabled all the toggable
        # forward traversal rules will end up deleting the whole workflow
        # (excluding input nodes except specifically targetted).
        di1, di2, di3, do1, pws, pcs, pwm = self._create_looped_graph()
        uuids_check_existence = [n.uuid for n in [di1, di2]]
        uuids_check_deleted = [n.uuid for n in [di3, do1, pcs, pws, pwm]]
        with Capturing():
            delete_nodes([di3.pk], force=True, create_forward=True, call_calc_forward=True, call_work_forward=True)
        self._check_existence(uuids_check_existence, uuids_check_deleted)

        # When disabling the call_calc and call_work forward rules, deleting
        # inputs will only delete the master and selection workflows, but will
        # leave the calculation and outputs.
        di1, di2, di3, do1, pws, pcs, pwm = self._create_looped_graph()
        uuids_check_existence = [n.uuid for n in [di1, di2, do1, pcs]]
        uuids_check_deleted = [n.uuid for n in [di3, pws, pwm]]
        with Capturing():
            delete_nodes([di3.pk], force=True, create_forward=True, call_calc_forward=False, call_work_forward=False)
        self._check_existence(uuids_check_existence, uuids_check_deleted)

        # Of course, deleting the selected input will cause all the procedure to
        # be deleted, no matter the flags chosen.
        di1, di2, di3, do1, pws, pcs, pwm = self._create_looped_graph()
        uuids_check_existence = [n.uuid for n in [di2, di3]]
        uuids_check_deleted = [n.uuid for n in [di1, do1, pws, pcs, pwm]]
        with Capturing():
            delete_nodes([di1.pk], force=True, create_forward=True, call_calc_forward=False, call_work_forward=False)
        self._check_existence(uuids_check_existence, uuids_check_deleted)

        # Deleting with these settings the workflow that chooses inputs should
        # not affect the data provenance either.
        di1, di2, di3, do1, pws, pcs, pwm = self._create_looped_graph()
        uuids_check_existence = [n.uuid for n in [di1, di2, di3, do1, pcs]]
        uuids_check_deleted = [n.uuid for n in [pws, pwm]]
        with Capturing():
            delete_nodes([pws.pk], force=True, create_forward=True, call_calc_forward=False, call_work_forward=False)
        self._check_existence(uuids_check_existence, uuids_check_deleted)


    def _create_long_graph(self, total_calcs):
        """
        Creates a straighforward graph with the required number of calculation nodes.
        All these calculation nodes are connected through a series of data nodes,
        starting with a data node D0 as the first input and each calculation C(N)
        will have data node D(N-1) as an input and data node D(N) as an output.
        The final graph looks like this::

            +----+     +----+     +----+     +----+     +----+
            | D0 | --> | C1 | --> | D1 | --> | C2 | --> | D2 | --> ...
            +----+     +----+     +----+     +----+     +----+
        """

        old_data = orm.Data().store()
        node_list = [old_data]

        for ii in range(total_calcs):
            new_calc = orm.CalculationNode()
            new_data = orm.Data().store()
            new_calc.add_incoming(old_data, link_type=LinkType.INPUT_CALC, link_label='inp' + str(ii))
            new_calc.store()
            new_data.add_incoming(new_calc, link_type=LinkType.CREATE, link_label='out' + str(ii))
            node_list.append(new_calc)
            node_list.append(new_data)
            old_data = new_data

        return node_list

    def test_long_case(self):
        """
        Using a simple but long graph, this test checks the propagation of the delete
        functionality forward in data provenance.
        """

        node_list = self._create_long_graph(10)
        uuids_check_existence = [n.uuid for n in node_list[:3]]
        uuids_check_deleted = [n.uuid for n in node_list[3:]]
        with Capturing():
            delete_nodes((node_list[3].pk,), force=True, create_forward=True)
        self._check_existence(uuids_check_existence, uuids_check_deleted)
