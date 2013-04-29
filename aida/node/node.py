import os

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

import aida.common
#from aida.djsite.db.models import DbNode, Attribute
from aida.common.exceptions import (
    InternalError, ModificationNotAllowed, NotExistent, ValidationError )
from aida.common.folders import RepositoryFolder, SandboxFolder

# Name to be used for the section
_section_name = 'node'

class Node(object):
    """
    Base class to map a node in the DB + its permanent repository counterpart.

    Stores attributes starting with an underscore.

    Caches files and attributes before the first save, and saves everything only on store().
    After the call to store(), in general attributes cannot be changed, except for those
    listed in the self._updatable_attributes tuple (empty for this class, can be
    extended in a subclass).

    Only after storing (or upon loading from uuid) metadata can be modified
    and in this case they are directly set on the db.

    In the plugin, also set the _plugin_type_string, to be set in the DB in the 'type' field.
    """
    _logger = aida.common.aidalogger.getChild('node')

    # A tuple with attributes that can be updated even after the call of the store() method
    _updatable_attributes = tuple() 

    _plugin_type_string = "" # For base nodes, it is an empty string; to be subclassed
    
    @classmethod
    def get_subclass_from_uuid(cls,uuid):
        """
        This class method will load an entry from the uuid, but loading the proper
        subclass where appropriate (while if Node(uuid=...) is called, only the Node
        class is loaded, even if the node is of a subclass).
        """
        from aida.djsite.db.models import DbNode
        try:
            return DbNode.objects.get(uuid=uuid).get_aida_class()
        except ObjectDoesNotExist:
            raise NotExistent("No entry with the UUID {} found".format(uuid))
        
    def __int__(self):
        """
        Convert the class to an integer. This is needed to allow querying with Django.
        Be careful, though, not to pass it to a wrong field! This only returns the
        local DB principal key value.
        """
        if self._to_be_stored:
            return None
        else:
            return self._dbnode.pk
    
    def __init__(self,**kwargs):
        from aida.djsite.utils import get_automatic_user
        from aida.djsite.db.models import DbNode

        self._to_be_stored = False
        self._temp_folder = None
        uuid = kwargs.pop('uuid', None)
        
        if uuid is not None:
            if kwargs:
                raise ValueError("If you pass a UUID, you cannot pass any further parameter")
            # If I am loading, I cannot modify it
            self._to_be_stored = False
            try:
                self._dbnode = DbNode.objects.get(uuid=uuid)
                # I do not check for multiple entries found
            except ObjectDoesNotExist:
                raise NotExistent("No entry with the UUID {} found".format(
                    uuid))

            self._repo_folder = RepositoryFolder(section=_section_name, uuid=self.uuid)
            try:
                self.validate()
            except ValidationError:
                raise DBContentError("The data in the DB with UUID={} is not valid for class {}".format(
                    uuid, self.__class__.__name__))
        else:
            self._dbnode = DbNode.objects.create(user=get_automatic_user())
            self._dbnode.type = self._plugin_type_string
            self._to_be_stored = True
            self._temp_folder = SandboxFolder()
            # Used only before the first save
            self._attrs_cache = {}
            self._repo_folder = RepositoryFolder(section=_section_name, uuid=self.uuid)

    @classmethod
    def query(cls,**kwargs):
        """
        Map to the aidaobjects manager of the DbNode, that returns
        Node objects (or their subclasses) instead of DbNode entities.
        """
        from aida.djsite.db.models import DbNode
        
        return DbNode.aidaobjects.filter(**kwargs)

    @property
    def logger(self):
        return self._logger

    def validate(self):
        """
        Check if the attributes and files retrieved from the DB are valid.
        Raise a ValidationError if something is wrong.

        Must be able to work even before storing: therefore, use the get_attr and similar methods
        that automatically read either from the DB or from the internal attribute cache.

        For the base class, this is always valid. Subclasses will reimplement this.
        In the subclass, always call the super().validate() method first!
        """
        return True

    def add_link_from(self,src,label=None):
        """
        Add a link to the current node from the 'src' node.
        Both nodes must be a Node instance (or a subclass of Node)

        In subclasses, change only this.
        """
        from aida.djsite.db.models import Link
        if self._to_be_stored:
            raise ModificationNotAllowed("You have to store the destination node to make link")
        if not isinstance(src,Node):
            raise ValueError("src must be a Node instance")
        if src._to_be_stored:
            raise ModificationNotAllowed("You have to store the source node to make a link")

        if self.uuid == src.uuid:
            raise ValueError("Cannot link to itself")

        if label is None:
            Link.objects.create(input=src.dbnode, output=self.dbnode)
        else:
            Link.objects.create(input=src.dbnode, output=self.dbnode, label=label)

    def add_link_to(self,dest,label=None):
        """
        Add a link from the current node to the 'dest' node.
        Both nodes must be a Node instance (or a subclass of Node)

        Do not change in subclasses, subclass the add_link_from class only.
        """
        if not isinstance(dest,Node):
            raise ValueError("dest must be a Node instance")
        dest.add_link_from(self,label)

    def get_inputs(self):
        """
        Return a list of nodes that enter (directly) in this node
        """
        from aida.djsite.db.models import DbNode
        
        return list(DbNode.aidaobjects.filter(outputs=self.dbnode).distinct())

    def get_outputs(self):
        """
        Return a list of nodes that exit (directly) in this node
        """
        from aida.djsite.db.models import DbNode
        
        return list(DbNode.aidaobjects.filter(inputs=self.dbnode).distinct())

    def set_attr(self, key, value):
        if self._to_be_stored:
            self._attrs_cache["_{}".format(key)] = value
        else:
            if key in self._updatable_attributes:
                return self._set_attribute_db('_{}'.format(key),value)
            else:
                raise ModificationNotAllowed("Cannot set an attribute after saving a node")

    def del_attr(self, key):
        if self._to_be_stored:
            try:
                del self._attrs_cache["_{}".format(key)]
            except KeyError:
                raise AttributeError("Attribute {} does not exist".format(key))
        else:
            if key in self._updatable_attributes:
                return self._del_attribute_db('_{}'.format(key))
            else:
                raise ModificationNotAllowed("Cannot delete an attribute after saving a node")


    def get_attr(self, key):
        if self._to_be_stored:
            try:
                return self._attrs_cache["_{}".format(key)]
            except KeyError:
                raise AttributeError("Attribute {} does not exist".format(key))
        else:
            return self._get_attribute_db('_{}'.format(key))

    def set_metadata(self,key,value):
        """
        Immediately sets a metadata of a calculation, in the DB!
        No .store() to be called.
        Can be used *only* after saving.

        Metadata keys cannot start with an underscore.
        """
        if key.startswith('_'):
            raise ValueError("An metadata key cannot start with an underscore")
        if self._to_be_stored:
            raise ModificationNotAllowed("The metadata of a node can be set only after "
                                         "storing the node")
        self._set_attribute_db(key,value)
            
    def get_metadata(self,key):
        """
        Get the value of a metadata, reading directly from the DB!
        Since metadata can be added only after storing the node, this
        function is meaningful to be called only after the .store() method.

        Metadata keys cannot start with an underscore.
        """
        if key.startswith('_'):
            raise AttributeError("An metadata key cannot start with an underscore")
        return self._get_attribute_db(key)

    def del_metadata(self,key):
        """
        Delete a metadata, acting directly on the DB!
        The action is immediately performed on the DB.
        Since metadata can be added only after storing the node, this
        function is meaningful to be called only after the .store() method.

        Metadata keys cannot start with an underscore.
        """
        if key.startswith('_'):
            raise ValueError("An metadata key cannot start with an underscore")
        if self._to_be_stored:
            raise ModificationNotAllowed("The metadata of a node can be set and deleted "
                                         "only after storing the node")
        self._del_attribute_db(key)

    def metadata(self):
        """
        Returns the keys of the metadata
        """
        from django.db.models import Q
        # I return the list of keys
        return self._list_all_attributes_db().filter(
            ~Q(key__startswith='_')).distinct().values_list('key', flat=True)

    def itermetadata(self):
        """
        Iterator over the metadata, returning tuples (key, value)
        """
        from django.db.models import Q
        metadatalist = self._list_all_attributes_db().filter(
            ~Q(key__startswith='_'))
        for md in metadatalist:
            yield (md.key, md.getvalue())
            
    def iterattrs(self):
        """
        Iterator over the attributes, returning tuples (key, value)

        TODO: check what happens if someone stores the object while the iterator is
        being used!
        """
        if self._to_be_stored:
            for k, v in self._attrs_cache.iteritems():
                # I strip the underscore
                yield (k[1:],v)
        else:          
            attrlist = self._list_all_attributes_db().filter(
                key__startswith='_')
            for attr in attrlist:
                # I strip the initial underscore
                yield (attr.key[1:], attr.getvalue())

    def attrs(self):
        """
        Returns the keys of the attributes
        """

        if self._to_be_stored:
            return [k[1:] for k in self._attrs_cache.keys()]
        else:
            # I return the list of keys of 
            # attributes, stripping the initial underscore
            return [k[1:] for k in self._list_all_attributes_db().filter(
                key__startswith='_').distinct().values_list('key', flat=True)]

    def _list_all_attributes_db(self):
        """
        Return a django queryset with the attributes of this node
        """
        from aida.djsite.db.models import Attribute
        
        return Attribute.objects.filter(dbnode=self.dbnode)

    def add_comment(self,content):
        """
        Add a new comment.
        """
        from aida.djsite.db.models import Comment
        from aida.djsite.utils import get_automatic_user

        if self._to_be_stored:
            raise ModificationNotAllowed("Comments can be added only after "
                                         "storing the node")

        Comment.objects.create(dbnode=self._dbnode, user=get_automatic_user(), content=content)

    def get_comments(self):
        """
        Return the list of comments, sorted by date; each element of the list is a tuple
        containing (username, username_email, date, content)
        """
        from aida.djsite.db.models import Comment

        return list(Comment.objects.filter(dbnode=self._dbnode).order_by('time').values_list(
            'user__username', 'user__email', 'time', 'content'))

    def _get_attribute_db(self, key):
        """
        This is the raw-level method that accesses the DB. To be used only internally,
        after saving self.dbnode. Both saves attributes and metadata, in the same way.
        The calling function must check that the key of attributes is prepended with
        an underscore and the key of metadata is not.
        """
        from aida.djsite.db.models import Attribute

        try:
            attr = Attribute.objects.get(dbnode=self.dbnode, key=key)
        except ObjectDoesNotExist:
            raise AttributeError("Key {} not found in db".format(key))
        return attr.getvalue()

    def _del_attribute_db(self,key):
        """
        This is the raw-level method that accesses the DB. No checks are done
        to prevent the user from deleting a valid key.  To be used only internally,
        after saving self.dbnode. Both saves attributes and metadata, in the same way.
        The calling function must check that the key of attributes is prepended with
        an underscore and the key of metadata is not.
        """
        from aida.djsite.db.models import Attribute

        self._increment_version_number_db()
        try:
            Attribute.objects.get(dbnode=self.dbnode, key=key).delete()
        except ObjectDoesNotExist:
            raise AttributeError("Cannot delete attribute {}, not found in db".format(key))

    def _increment_version_number_db(self):
        """
        This function increments the version number in the DB.
        This should be called every time you need to increment the version (e.g. on adding a
        metadata or attribute). 
        """
        from django.db.models import F
        from aida.djsite.db.models import DbNode

        # I increment the node number using a filter (this should be the right way of doing it;
        # dbnode.nodeversion  = F('nodeversion') + 1
        # will do weird stuff, returning Django Objects instead of numbers, and incrementing at
        # every save; moreover in this way I should do the right thing for concurrent writings
        # I use self._dbnode because this will not do a query to update the node; here I only
        # need to get its pk
        DbNode.objects.filter(pk=self._dbnode.pk).update(nodeversion = F('nodeversion') + 1)

        # Note: I have to reload the ojbect. I don't do it here because it is done at every call
        # to self.dbnode
        #self._dbnode = DbNode.objects.get(pk=self._dbnode.pk)

    def _set_attribute_db(self,key,value,incrementversion=True):
        """
        This is the raw-level method that accesses the DB. No checks are done
        to prevent the user from (re)setting a valid key.  To be used only internally,
        after saving self.dbnode. Both saves attributes and metadata, in the same way.
        The calling function must check that the key of attributes is prepended with
        an underscore and the key of metadata is not.

        TODO: there may be some error on concurrent write; not checked in this unlucky case!

        If incrementversion is True (default), each attribute set will udpate the version.
        This can be set to False during the store() so that the version does not get increased for each
        attribute.
        """
        from aida.djsite.db.models import Attribute
                
        if incrementversion:
             self._increment_version_number_db()
        attr, created = Attribute.objects.get_or_create(dbnode=self.dbnode, key=key)
        ## TODO: create a get_or_create_with_value method in the djsite.db.models.Attribute class
        attr.setvalue(value)

    def copy(self):
        """
        Return a copy of the current object to work with, not stored yet.

        This is a completely new entry in the DB, with its own UUID.
        Works both on stored instances and with not-stored ones.

        Copies files and attributes, but not the metadata.
        Does not store the Node to allow modification of attributes.
        """
        newobject = self.__class__()
        newobject.dbnode.type = self.dbnode.type # Inherit type
        newobject.dbnode.label = self.dbnode.label # Inherit label
        # TODO: add to the description the fact that this was a copy?
        newobject.dbnode.description = self.dbnode.description # Inherit description
        newobject.dbnode.computer = self.dbnode.computer # Inherit computer
        
        for k, v in self.iterattrs():
            newobject.set_attr(k,v)

        for filename in self.get_file_list():
            newobject.add_file(self.current_folder.get_file_path(filename),filename)

        return newobject

    @property
    def uuid(self):
        return unicode(self.dbnode.uuid)

    @property
    def dbnode(self):
        from aida.djsite.db.models import DbNode
        
        # I also update the internal _dbnode variable, if it was saved
        if not self._to_be_stored:
            self._dbnode = DbNode.objects.get(pk=self._dbnode.pk)
        return self._dbnode

    @property
    def repo_folder(self):
        return self._repo_folder

    @property
    def current_folder(self):
        if self._to_be_stored:
            return self.get_temp_folder()
        else:
            return self.repo_folder

    def get_file_list(self):
        return self.current_folder.get_file_list()

    def get_temp_folder(self):
        if self._temp_folder is None:
            raise InternalError("The temp_folder was asked for node {}, but it is "
                                "not set!".format(self.uuid))
        return self._temp_folder

    def remove_file(self,filename):
        """
        Remove a file from the repository directory.

        Can be called only before storing.
        """
        if not self._to_be_stored:
            raise ValueError("Cannot delete a file after storing the node")
        
        if os.path.split(filename)[0]:
            raise ValueError("The destination file in add_file must be a filename without any subfolder")
        self.get_temp_folder().remove_file(filename)

    def add_file(self,src_abs,dst_filename):
        """
        Copy a file from a local file inside the repository directory.
        The file cannot be put in a subfolder.

        Copy to a cache directory if the entry has not been saved yet.
        src_abs: the absolute path of the file to copy.
        dst_filename: the filename on which to copy.

        TODO: in the future, add an add_attachment() that has the same meaning of a metadata file.
        Decide also how to store. If in two separate subfolders, remember to reset the limit.
        """
        if not self._to_be_stored:
            raise ValueError("Cannot insert file after storing the node")
        
        if not os.path.isabs(src_abs):
            raise ValueError("The source file in add_file must be an absolute path")
        if os.path.split(dst_filename)[0]:
            raise ValueError("The destination file in add_file must be a filename without any subfolder")
        self.get_temp_folder().insert_file(src_abs,dst_filename)


    def get_file_path(self,filename):
        """
        TODO: For the moment works only for one kind of files, 'internal'
        """
        return self.current_folder.get_file_path(filename,check_existence=True)

    def store(self):
        """
        Store a new node in the DB, also saving its repository directory and attributes.

        Can be called only once. Afterwards, attributes cannot be changed anymore!
        Instead, metadata can be changed only AFTER calling this store() function.
        
        TODO: This needs to be generalized, allowing for flexible methods for storing data and its attributes.
        """
        from django.db import transaction

        if self._to_be_stored:

            # As a first thing, I check if the data is valid
            self.validate()
            # I save the corresponding django entry
            with transaction.commit_on_success():
                # Save the row
                self._dbnode.save()
                # Save its attributes
                for k, v in self._attrs_cache.iteritems():
                    self._set_attribute_db(k,v,incrementversion=False)

                # I set the folder
                self.repo_folder.replace_with_folder(self.get_temp_folder().abspath, move=True, overwrite=True)
            
            self._temp_folder = None            
            self._to_be_stored = False
        else:
            self.logger.error("Trying to store an already saved node: {}".format(self.uuid))
            raise ModificationNotAllowed("Node with uuid={} was already stored".format(self.uuid))

        # This is useful because in this way I can do
        # n = Node().store()
        return self

    
    def retrieve(self):
        '''
        Retrieve info from DB and files, and recreate the Aiida node object.
        '''
        pass


    def __del__(self):
        """
        Called only upon real object destruction from memory
        I just try to remove junk, whenever possible; do not trust too much this function!
        """
        if getattr(self,'_temp_folder',None) is not None:
            self._temp_folder.erase()

