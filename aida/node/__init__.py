#if __name__ == "__main__":
from aida.djsite.settings import settings
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'aida.djsite.settings.settings'

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db import transaction

import aida.common
from aida.djsite.main.models import Node as DjangoNode, Attribute
from aida.common.exceptions import (
    InternalError, InvalidOperation, ModificationNotAllowed, NotExistent )
from aida.djsite.utils import get_automatic_user
from aida.common.folders import RepositoryFolder, SandboxFolder

# Name to be used for the section
_section_name = 'node'

class Node(object):
    """
    Base class to map a node in the DB + its permanent repository counterpart.

    Stores internal attributes starting with an underscore.

    Caches files and attributes before the first save, and saves everything only on save.
    After the first save (or upon loading from uuid), only non-internal attributes can be modified
    and in this case they are directly set on the db.
    """
    _logger = aida.common.aidalogger.getChild('node')
    
    def __init__(self,uuid=None):
        self._can_be_modified = False
        if uuid is not None:
            # If I am loading, I cannot modify it
            self._can_be_modified = False
            try:
                self._tablerow = DjangoNode.objects.get(uuid=uuid)
                # I do not check for multiple entries found
            except ObjectDoesNotExist:
                raise NotExistent("No entry with the UUID {} found".format(
                    uuid))
            self._temp_folder = None
        else:
            self._tablerow = DjangoNode.objects.create(user=get_automatic_user())
            self._can_be_modified = True
            self._temp_folder = SandboxFolder()
            # Used only before the first save
            self._intattrs_cache = {}
        self._repo_folder = RepositoryFolder(section=_section_name, uuid=self.uuid)

    @property
    def logger(self):
        return self._logger

    def set_internal_attr(self, key, value):
        if not self._can_be_modified:
            raise ModificationNotAllowed("Cannot set an internal attribute after saving a node")
        self._intattrs_cache["_{}".format(key)] = value

    def del_internal_attr(self, key):
        if not self._can_be_modified:
            raise ModificationNotAllowed("Cannot delete an internal attribute after saving a node")
        try:
            del self._intattrs_cache["_{}".format(key)]
        except KeyError:
            raise AttributeError("Attribute {} does not exist".format(key))

    def get_internal_attr(self, key):
        if self._can_be_modified:
            try:
                return self._intattrs_cache["_{}".format(key)]
            except KeyError:
                raise AttributeError("Attribute {} does not exist".format(key))
        else:
            return self._get_attribute_db('_{}'.format(key))

    def set_attr(self,key,value):
        """
        Immediately sets a non-internal attribute of a calculation, in the DB!
        No .save() to be called.
        Can be used only after saving.

        Attributes cannot start with an underscore.
        """
        if key.startswith('_'):
            raise ValueError("An attribute cannot start with an underscore")
        if self._can_be_modified:
            raise InvalidOperation("The non-internal attributes of a node can be set only after "
                                   "storing the node")
        self._set_attribute_db(key,value)
            
    def get_attr(self,key):
        """
        Get the value of a non-internal attribute, reading directly from the DB!
        Since non-internal attributes can be added only after storing the node, this
        function is meaningful to be called only after the .store() method.

        Attributes cannot start with an underscore.
        """
        if key.startswith('_'):
            raise AttributeError("An attribute cannot start with an underscore")
        return self._get_attribute_db(key)

    def del_attr(self,key):
        """
        Delete the value of a non-internal attribute, acting directly on the DB!
        The action is immediately performed on the DB>
        Since non-internal attributes can be added only after storing the node, this
        function is meaningful to be called only after the .store() method.

        Attributes cannot start with an underscore.
        """
        if key.startswith('_'):
            raise ValueError("An attribute cannot start with an underscore")
        if self._can_be_modified:
            raise InvalidOperation("The non-internal attributes of a node can be set and deleted "
                                   "only after storing the node")
        self._del_attribute_db(key)

    def _get_attribute_db(self, key):
        """
        This is the raw-level method that accesses the DB. To be used only internally,
        after saving self.tablerow.
        """
        try:
            attr = Attribute.objects.get(node=self.tablerow, key=key)
        except ObjectDoesNotExist:
            raise AttributeError("Key {} not found in db".format(key))
        return attr.getvalue()

    def _del_attribute_db(self,key):
        """
        This is the raw-level method that accesses the DB. No checks are done
        to prevent the user from deleting a valid key. To be used only internally,
        after saving self.tablerow.
        """
        try:
            Attribute.objects.get(node=self.tablerow, key=key).delete()
        except ObjectDoesNotExist:
            raise AttributeError("Cannot delete attribute {}, not found in db".format(key))

    def _set_attribute_db(self,key,value):
        """
        This is the raw-level method that accesses the DB. No checks are done
        to prevent the user from (re)setting a valid key. To be used only internally,
        after saving self.tablerow.

        Note: there may be some error on concurrent write; not checked in this unlucky case!
        """
        attr, created = Attribute.objects.get_or_create(node=self.tablerow, key=key)
        ## TODO: create a get_or_create_with_value method
        attr.setvalue(value)

    @property
    def uuid(self):
        return unicode(self.tablerow.uuid)

    @property
    def tablerow(self):
        return self._tablerow

    @property
    def folder(self):
        return self._repo_folder

    def get_temp_folder(self):
        if self._temp_folder is None:
            raise InternalError("The temp_folder was asked for node {}, but it is "
                                "not set!".format(self.uuid))
        return self._temp_folder

    def add_file(self,src_abs,dst_rel):
        """
        Copy a file from a local file inside the repository directory.

        Copy to a cache directory if the entry has not been saved yet.
        src_abs: the absolute path of the file to copy.
        dst_rel: the relative path in which to copy.

        TODO: in the future, add an internal=True optional parameter, and allow for files
        to be added later, in the same way in which we have internal and non-internal attributes.
        Decide also how to store. If in two separate subfolders, remember to reset the limit.
        """
        if not os.path.isabs(src_abs):
            raise ValueError("The source file in add_file must be an absolute path")
        if os.path.isabs(dst_rel):
            raise ValueError("The destination file in add_file must be a relative path")
        subfolder_path, dst_filename = os.path.split(dst_rel)
        subfolder = self.folder.subfolder(subfolder_path,create=True)
        subfolder.insertfile(src_abs,dst_filename)

    def store(self):
        """
        Store a new node in the DB, also saving its repository directory and attributes.

        Can be called only once. Afterwards, internal attributes cannot be changed anymore!
        Instead, non-internal attributes can be changed only AFTER calling this store() function.
        """
        if self._can_be_modified:
            
            # I save the corresponding django entry
            with transaction.commit_on_success():
                # Save the row
                self.tablerow.save()
                # Save its (internal) attributes
                for k, v in self._intattrs_cache.iteritems():
                    self._set_attribute_db(k,v)

                # I set the folder
                self.folder.replace_with_folder(self.get_temp_folder().abspath, move=True, overwrite=True)
            
            self._temp_folder = None            
            self._can_be_modified = False
        else:
            # I just issue a warning
            self.logger.warning("Trying to store an already saved node: {}".format(self.uuid))

    # Called only upon real object destruction from memory
    # I just try to remove junk, whenever possible
    def __del__(self):
        if self._temp_folder is not None:
            self._temp_folder.erase()

if __name__ == '__main__':
    ## TODO: TO MOVE TO DJANGO TESTS!
    import unittest
    
    class TestDirectoryManipulation(unittest.TestCase):
        boolval = True
        intval = 123
        floatval = 4.56
        stringval = "aaaa"
        dictval = {'num': 3, 'something': 'else'}
        listval = [1, "s", True]

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
            

    unittest.main()
        


    ## TO TEST:
    # reload from uuid, an re-check attrs
    # create a copy, and recheck attrs, and modify them and check they don't change on original instance
    # check for files
    # Store internal and external attribute with same name
