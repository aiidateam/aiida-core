import os

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

import aida.common
#from aida.djsite.db.models import DbNode, Attribute
from aida.common.exceptions import (
    DbContentError, InternalError, ModificationNotAllowed,
    NotExistent, UniquenessError, ValidationError )
from aida.common.folders import RepositoryFolder, SandboxFolder

# Name to be used for the section
_section_name = 'node'

# The name of the subfolder in which to put the files/directories added with add_path
_path_subfolder_name = 'path'

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
            raise NotExistent("No entry with UUID={} found".format(uuid))

    @classmethod
    def get_subclass_from_pk(cls,pk):
        """
        This class method will load an entry from the pk (integer primary key used in 
        this database), but loading the proper subclass where appropriate.
        """
        from aida.djsite.db.models import DbNode
        try:
            return DbNode.objects.get(pk=pk).get_aida_class()
        except ObjectDoesNotExist:
            raise NotExistent("No entry with pk={} found".format(pk))
        
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
            except ValidationError as e:
                raise DbContentError("The data in the DB with UUID={} is not valid for class {}: {}".format(
                    uuid, self.__class__.__name__, e.message))
        else:
            self._dbnode = DbNode.objects.create(user=get_automatic_user())
            self._dbnode.type = self._plugin_type_string
            self._to_be_stored = True
            self._temp_folder = SandboxFolder()
            # Create an empty folder, to avoid any problem in the future
            self.path_subfolder.create()
            # Used only before the first save
            self._attrs_cache = {}
            self._repo_folder = RepositoryFolder(section=_section_name, uuid=self.uuid)

    @classmethod
    def query(cls,*args,**kwargs):
        """
        Map to the aidaobjects manager of the DbNode, that returns
        Node objects (or their subclasses) instead of DbNode entities.
        """
        from aida.djsite.db.models import DbNode

        return DbNode.aidaobjects.filter(*args,type__startswith=cls._plugin_type_string,**kwargs)

    @property
    def logger(self):
        return self._logger

    def set_label(self,label):
        """
        Set the label of the calculation
        """
        if self._to_be_stored:
            self.dbnode.label = label
        else:
            self.logger.error("Trying to change the label of an already saved node: {}".format(
                self.uuid))
            raise ModificationNotAllowed("Node with uuid={} was already stored".format(self.uuid))

    @property
    def label(self):
        return self.dbnode.label

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

    def get_user(self):
        return self.dbnode.user

    def replace_link_from(self,src,label):
        """
        Replace an input link with the given label, or simply creates it
        if it does not exist.
        """
        from django.db import transaction        
        from aida.djsite.db.models import Link
        
        try:
            self.add_link_from(src, label)
        except UniquenessError:
            # I have to replace the link; I do it within a transaction
            try:
                sid = transaction.savepoint()
                Link.objects.filter(output=self.dbnode,
                                    label=label).delete()
                self.add_link_from(src, label)
                transaction.savepoint_commit(sid)
            except:
                transaction.savepoint_rollback(sid)
                raise

    def add_link_from(self,src,label=None):
        """
        Add a link to the current node from the 'src' node.
        Both nodes must be a Node instance (or a subclass of Node)

        In subclasses, change only this.
        """
        from aida.djsite.db.models import Link, Path
        from django.db import IntegrityError, transaction

        if self._to_be_stored:
            raise ModificationNotAllowed("You have to store the destination node to make link")
        if not isinstance(src,Node):
            raise ValueError("src must be a Node instance")
        if src._to_be_stored:
            raise ModificationNotAllowed("You have to store the source node to make a link")

        if self.uuid == src.uuid:
            raise ValueError("Cannot link to itself")

        # Check for cycles. This works if the transitive closure is enabled; if it 
        # isn't, this test will never fail, but then having a circular link is not
        # meaningful but does not pose a huge threat
        #
        # I am linking src->self; a loop would be created if a Path exists already
        # in the TC table from self to src
        if len(Path.objects.filter(parent=self.dbnode, child=src.dbnode))>0:
            raise ValueError("The link you are attempting to create would generate a loop")            

        # Check if the source allows output links from this node (will raise ValueError if 
        # this is not the case)
        src.can_link_as_output(self)

        if label is None:
            autolabel_idx = 1

            existing_from_autolabels = list(Link.objects.filter(
                output=self.dbnode,
                label__startswith="link_").values_list('label',flat=True))
            while "link_{}".format(autolabel_idx) in existing_from_autolabels:
                autolabel_idx += 1

            safety_counter = 0
            while True:
                safety_counter += 1
                if safety_counter > 100:
                    # Well, if you have more than 100 concurrent addings to the same 
                    # node, you are clearly doing something wrong...
                    raise InternalError("Hey! We found more than 100 concurrent adds of links "
                        "to the same nodes! Are you really doing that??")
                try:
                    # transactions are needed here for Postgresql:
                    # https://docs.djangoproject.com/en/1.5/topics/db/transactions/#handling-exceptions-within-postgresql-transactions
                    sid = transaction.savepoint()
                    Link.objects.create(input=src.dbnode, output=self.dbnode,
                        label="link_{}".format(autolabel_idx))
                    transaction.savepoint_commit(sid)
                    break
                except IntegrityError as e:
                    transaction.savepoint_rollback(sid)
                    # Retry loop until you find a new loop
                    autolabel_idx += 1
        else:
            try:
                # transactions are needed here for Postgresql:
                # https://docs.djangoproject.com/en/1.5/topics/db/transactions/#handling-exceptions-within-postgresql-transactions
                sid = transaction.savepoint()
                Link.objects.create(input=src.dbnode, output=self.dbnode, label=label)
                transaction.savepoint_commit(sid)
            except IntegrityError as e:
                transaction.savepoint_rollback(sid)
                raise UniquenessError("There is already a link with the same "
                                      "name (raw message was {})"
                                      "".format(e.message))

    def add_link_to(self,dest,label=None):
        """
        Add a link from the current node to the 'dest' node.
        Both nodes must be a Node instance (or a subclass of Node)

        Do not change in subclasses, subclass the add_link_from class only.
        """
        if not isinstance(dest,Node):
            raise ValueError("dest must be a Node instance")
        dest.add_link_from(self,label)

    def can_link_as_output(self,dest):
        """
        Raise a ValueError if a link from self to dest is not allowed.
        Implement in subclasses
        """
        return True


    def get_inputs(self,type=None,also_labels=False):
        """
        Return a list of nodes that enter (directly) in this node

        Args:
            type: if specified, should be a class, and it filters only elements of that
                specific type (or a subclass of 'type')
            also_labels: if False (default) only return a list of input nodes.
                If True, return a list of tuples, where each tuple has the following
                format: ('label', Node)
                with 'label' the link label, and Node a Node instance or subclass
        """
        from aida.djsite.db.models import Link

        inputs_list = ((i.label, i.input.get_aida_class()) for i in
                       Link.objects.filter(output=self.dbnode).distinct())
        
        if type is None:
            if also_labels:
                return list(inputs_list)
            else:
                return [i[1] for i in inputs_list]
        else:
            filtered_list = (i for i in inputs_list if isinstance(i[1],type))
            if also_labels:
                return list(filtered_list)
            else:
                return [i[1] for i in filtered_list]
            

    def get_outputs(self,type=None,also_labels=False):
        """
        Return a list of nodes that exit (directly) from this node

        Args:
            type: if specified, should be a class, and it filters only elements of that
                specific type (or a subclass of 'type')
            also_labels: if False (default) only return a list of input nodes.
                If True, return a list of tuples, where each tuple has the following
                format: ('label', Node)
                with 'label' the link label, and Node a Node instance or subclass
        """
        from aida.djsite.db.models import Link

        outputs_list = ((i.label, i.output.get_aida_class()) for i in
                       Link.objects.filter(input=self.dbnode).distinct())
        
        if type is None:
            if also_labels:
                return list(outputs_list)
            else:
                return [i[1] for i in outputs_list]
        else:
            filtered_list = (i for i in outputs_list if isinstance(i[1],type))
            if also_labels:
                return list(filtered_list)
            else:
                return [i[1] for i in filtered_list]

            
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


    def get_attr(self, key, *args):
        if len(args) > 1:
            raise ValueError("After the key name you can pass at most one value, that is "
                             "the default value to be used if no attribute is found.")
        try:
            if self._to_be_stored:
                try:
                    return self._attrs_cache["_{}".format(key)]
                except KeyError:
                    raise AttributeError("Attribute {} does not exist".format(key))
            else:
                return self._get_attribute_db('_{}'.format(key))
        except AttributeError as e:
            try:
                return args[0]
            except IndexError:
                raise e

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
            
    def iterattrs(self,also_updatable=True):
        """
        Iterator over the attributes, returning tuples (key, value)

        If also_updatable is False, does not iterate over attributes that are updatable

        TODO: check what happens if someone stores the object while the iterator is
        being used!
        """
        updatable_list = ["_{}".format(attr) for attr in self._updatable_attributes]
        
        if self._to_be_stored:
            for k, v in self._attrs_cache.iteritems():
                if not also_updatable and k in updatable_list:
                    continue
                # I strip the underscore
                yield (k[1:],v)
        else:          
            attrlist = self._list_all_attributes_db().filter(
                key__startswith='_')
            for attr in attrlist:
                if not also_updatable and attr.key in updatable_list:
                    continue
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
        
        for k, v in self.iterattrs(also_updatable=False):
            newobject.set_attr(k,v)

        for path in self.get_path_list():
            newobject.add_path(self.get_abs_path(path),path)

        return newobject

    @property
    def uuid(self):
        return unicode(self.dbnode.uuid)

    @property
    def pk(self):
        return unicode(self.dbnode.pk)


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

    @property
    def path_subfolder(self):
        return self.current_folder.get_subfolder(
            _path_subfolder_name,reset_limit=True)

    def get_path_list(self, subfolder='.'):
        return self.path_subfolder.get_subfolder(subfolder).get_content_list()

    def get_temp_folder(self):
        if self._temp_folder is None:
            raise InternalError("The temp_folder was asked for node {}, but it is "
                                "not set!".format(self.uuid))
        return self._temp_folder

    def remove_path(self,path):
        """
        Remove a file or directory from the repository directory.

        Can be called only before storing.
        """
        if not self._to_be_stored:
            raise ValueError("Cannot delete a path after storing the node")
        
        if os.path.isabs(path):
            raise ValueError("The destination path in remove_path must be a relative path")
        self.path_subfolder.remove_path(path)

    def add_path(self,src_abs,dst_path):
        """
        Copy a file or folder from a local file inside the repository directory.
        If there is a subpath, folders will be created.

        Copy to a cache directory if the entry has not been saved yet.
        src_abs: the absolute path of the file to copy.
        dst_filename: the (relative) path on which to copy.

        TODO: in the future, add an add_attachment() that has the same meaning of a metadata file.
        Decide also how to store. If in two separate subfolders, remember to reset the limit.
        """
        if not self._to_be_stored:
            raise ValueError("Cannot insert a path after storing the node")
        
        if not os.path.isabs(src_abs):
            raise ValueError("The source path in add_path must be absolute")
        if os.path.isabs(dst_path):
            raise ValueError("The destination path in add_path must be a filename without any subfolder")
        self.path_subfolder.insert_path(src_abs,dst_path)


    def get_abs_path(self,path,section=_path_subfolder_name):
        """
        TODO: For the moment works only for one kind of files, 'path' (internal files)
        """
        if os.path.isabs(path):
            raise ValueError("The path in get_abs_path must be relative")
        return self.current_folder.get_subfolder(section,reset_limit=True).get_abs_path(path,check_existence=True)

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
            # I set the folder
            self.repo_folder.replace_with_folder(self.get_temp_folder().abspath, move=True, overwrite=True)

            # I do the transaction only during storage on DB to avoid timeout problems, especially
            # with SQLite
            try:
                with transaction.commit_on_success():
                    # Save the row
                    self._dbnode.save()
                    # Save its attributes
                    for k, v in self._attrs_cache.iteritems():
                        self._set_attribute_db(k,v,incrementversion=False)
            # This is one of the few cases where it is ok to do a 'global' except,
            # also because I am re-raising the exception
            except:
                # I put back the files in the sandbox folder since the transaction did not succeed
                self.get_temp_folder().replace_with_folder(
                    self.repo_folder.abspath, move=True, overwrite=True)                
                raise

            
            self._temp_folder = None            
            self._to_be_stored = False
        else:
            self.logger.error("Trying to store an already saved node: {}".format(self.uuid))
            raise ModificationNotAllowed("Node with uuid={} was already stored".format(self.uuid))

        # This is useful because in this way I can do
        # n = Node().store()
        return self


    def __del__(self):
        """
        Called only upon real object destruction from memory
        I just try to remove junk, whenever possible; do not trust too much this function!
        """
        if getattr(self,'_temp_folder',None) is not None:
            self._temp_folder.erase()

