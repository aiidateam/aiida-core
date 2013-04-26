from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db import transaction

import aida.common
from aida.djsite.db.models import DbNode, Attribute
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

    def __int__(self):
        """
        Convert the class to an integer. This is needed to allow querying with Django.
        Be careful, though, not to pass it to a wrong field! This only returns the
        local DB principal key value.
        """
        if self.dbnode is not None:
            return self.dbnode.pk
        else:
            return None
    
    def __init__(self,uuid=None):
        self._can_be_modified = False
        self._temp_folder = None
        if uuid is not None:
            # If I am loading, I cannot modify it
            self._can_be_modified = False
            try:
                self._dbnode = DbNode.objects.get(uuid=uuid)
                # I do not check for multiple entries found
            except ObjectDoesNotExist:
                raise NotExistent("No entry with the UUID {} found".format(
                    uuid))
        else:
            self._dbnode = DbNode.objects.create(user=get_automatic_user())
            self._can_be_modified = True
            self._temp_folder = SandboxFolder()
            # Used only before the first save
            self._intattrs_cache = {}
        self._repo_folder = RepositoryFolder(section=_section_name, uuid=self.uuid)

    @classmethod
    def query(cls,**kwargs):
        """
        Map to the aidaobjects manager of the DbNode, that returns
        Node objects (or their subclasses) instead of DbNode entities.
        """
        return DbNode.aidaobjects.filter(**kwargs)

    @property
    def logger(self):
        return self._logger

    def add_link_to(self,dest,label=None):
        """
        Add a link from the current node to the 'dest' node.
        Both nodes must be a Node instance (or a subclass of Node)
        """
        from aida.djsite.db.models import Link
        if self._can_be_modified:
            raise ModificationNotAllowed("You have to store the source link")
        if not isinstance(dest,Node):
            raise ValueError("dest must be a Node instance")
        if dest._can_be_modified:
            raise ModificationNotAllowed("You have to store the destination link")

        if label is None:
            Link.objects.create(input=self.dbnode, output=dest.dbnode)
        else:
            Link.objects.create(input=self.dbnode, output=dest.dbnode, label=label)

    def add_link_from(self,src,label=None):
        """
        Add a link to the current node from the 'src' node.
        Both nodes must be a Node instance (or a subclass of Node)
        """
        if not isinstance(src,Node):
            raise ValueError("src must be a Node instance")
        src.add_link_to(self,label)

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
        after saving self.dbnode.
        """
        try:
            attr = Attribute.objects.get(dbnode=self.dbnode, key=key)
        except ObjectDoesNotExist:
            raise AttributeError("Key {} not found in db".format(key))
        return attr.getvalue()

    def _del_attribute_db(self,key):
        """
        This is the raw-level method that accesses the DB. No checks are done
        to prevent the user from deleting a valid key. To be used only internally,
        after saving self.dbnode.
        """
        try:
            Attribute.objects.get(dbnode=self.dbnode, key=key).delete()
        except ObjectDoesNotExist:
            raise AttributeError("Cannot delete attribute {}, not found in db".format(key))

    def _set_attribute_db(self,key,value):
        """
        This is the raw-level method that accesses the DB. No checks are done
        to prevent the user from (re)setting a valid key. To be used only internally,
        after saving self.dbnode.

        Note: there may be some error on concurrent write; not checked in this unlucky case!
        """
        attr, created = Attribute.objects.get_or_create(dbnode=self.dbnode, key=key)
        ## TODO: create a get_or_create_with_value method
        attr.setvalue(value)

    @property
    def uuid(self):
        return unicode(self.dbnode.uuid)

    @property
    def dbnode(self):
        return self._dbnode

    @property
    def repo_folder(self):
        return self._repo_folder

    @property
    def current_folder(self):
        if self._can_be_modified:
            return self.get_temp_folder()
        else:
            return self.repo_folder

    def get_temp_folder(self):
        if self._temp_folder is None:
            raise InternalError("The temp_folder was asked for node {}, but it is "
                                "not set!".format(self.uuid))
        return self._temp_folder

    def add_file(self,src_abs,dst_filename):
        """
        Copy a file from a local file inside the repository directory.
        The file cannot be put in a subfolder.

        Copy to a cache directory if the entry has not been saved yet.
        src_abs: the absolute path of the file to copy.
        dst_filename: the filename on which to copy.

        TODO: in the future, add an internal=True optional parameter, and allow for files
        to be added later, in the same way in which we have internal and non-internal attributes.
        Decide also how to store. If in two separate subfolders, remember to reset the limit.
        """
        if not self._can_be_modified:
            raise ValueError("Cannot insert file after storing the node")
        
        if not os.path.isabs(src_abs):
            raise ValueError("The source file in add_file must be an absolute path")
        if os.path.isabs(dst_rel):
            raise ValueError("The destination file in add_file must be a filename")
        self.get_temp_folder().insertfile(src_abs,dst_filename)

    def get_file_path(self,filename):
        """
        TODO: For the moment works only for one kind of files, 'internal'
        """
        self.current_folder.get_file_path(filename,check_existence=True)

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
                self.dbnode.save()
                # Save its (internal) attributes
                for k, v in self._intattrs_cache.iteritems():
                    self._set_attribute_db(k,v)

                # I set the folder
                self.repo_folder.replace_with_folder(self.get_temp_folder().abspath, move=True, overwrite=True)
            
            self._temp_folder = None            
            self._can_be_modified = False
        else:
            # I just issue a warning
            self.logger.warning("Trying to store an already saved node: {}".format(self.uuid))

        # This is useful because I can do a2 = Node().store()
        return self

    def __del__(self):
        """
        Called only upon real object destruction from memory
        I just try to remove junk, whenever possible; do not trust too much this function!
        """
        if getattr(self,'_temp_folder',None) is not None:
            self._temp_folder.erase()

