import os

from django.core.exceptions import ObjectDoesNotExist

#from aiida.djsite.db.models import DbNode, Attribute
from aiida.common.exceptions import (
    DbContentError, InternalError, ModificationNotAllowed,
    NotExistent, UniquenessError, ValidationError )
from aiida.common.folders import RepositoryFolder, SandboxFolder

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
    class __metaclass__(type):
        """
        Some python black magic to set correctly the logger also in subclasses.
        """
        def __new__(cls, name, bases, attrs):
            import logging
            newcls = type.__new__(cls, name, bases, attrs)
            newcls._logger = logging.getLogger(
                '{:s}.{:s}'.format(attrs['__module__'], name))
            
            prefix = "aiida.orm."
            if attrs['__module__'].startswith(prefix):
                # Strip aiida.orm.
                # Append a dot at the end, always
                newcls._plugin_type_string = "{}.{}.".format(
                    attrs['__module__'][len(prefix):], name)
                if newcls._plugin_type_string == 'node.Node.':
                    newcls._plugin_type_string = ''
            else:
                raise InternalError("Class {} is not in a module under "
                                    "aiida.orm.".format(name))
            
            return newcls

    # A tuple with attributes that can be updated even after the call of the store() method
    _updatable_attributes = tuple() 
    
    @property
    def logger(self):
        """
        Get the logger of the Node object.
        
        :return: Logger object
        """
        return self._logger
    
    @classmethod
    def get_subclass_from_uuid(cls,uuid):
        """
        Get a node object from the uuid, with the proper subclass of Node.
        (if Node(uuid=...) is called, only the Node class is loaded).
        
        :param uuid: a string with the uuid of the object to be loaded.
        :return: the object of the proper subclass.
        :raise: NotExistent: if there is no entry of the desired 
                             object kind with the given uuid.
        """
        from aiida.djsite.db.models import DbNode
        try:
            node = DbNode.objects.get(uuid=uuid).get_aiida_class()
        except ObjectDoesNotExist:
            raise NotExistent("No entry with UUID={} found".format(uuid))
        if not isinstance(node, cls):
            raise NotExistent("UUID={} is not an instance of {}".format(
                uuid,cls.__name__))
        return node

    @classmethod
    def get_subclass_from_pk(cls,pk):
        """
        Get a node object from the pk, with the proper subclass of Node.
        (integer primary key used in this database), 
        but loading the proper subclass where appropriate.
                
        :param pk: a string with the pk of the object to be loaded.
        :return: the object of the proper subclass.
        :raise: NotExistent: if there is no entry of the desired 
                             object kind with the given pk.
        """
        from aiida.djsite.db.models import DbNode
        try:
            node = DbNode.objects.get(pk=pk).get_aiida_class()
        except ObjectDoesNotExist:
            raise NotExistent("No entry with pk={} found".format(pk))
        if not isinstance(node, cls):
            raise NotExistent("pk={} is not an instance of {}".format(
                pk,cls.__name__))        
        return node
    
    @property
    def ctime(self):
        """
        Return the creation time of the node.
        """
        return self.dbnode.ctime

    @property
    def mtime(self):
        """
        Return the modification time of the node.
        """
        return self.dbnode.mtime
        
    def __int__(self):
        """
        Convert the class to an integer. This is needed to allow querying with Django.
        Be careful, though, not to pass it to a wrong field! This only returns the
        local DB principal key value.
        
        :return: the integer pk of the node or None if not stored.
        """
        if self._to_be_stored:
            return None
        else:
            return self._dbnode.pk
    
    def __init__(self,**kwargs):
        """
        Initialize the object Node.
        
        :param optional uuid: if present, the Node with given uuid is loaded from the database.
                  (It is not possible to assign a uuid to a new Node.)
        """
        from aiida.djsite.utils import get_automatic_user
        from aiida.djsite.db.models import DbNode

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
        Map to the aiidaobjects manager of the DbNode, that returns
        Node objects (or their subclasses) instead of DbNode entities.
        
        # TODO: VERY IMPORTANT: the recognition of a subclass from the type
        #       does not work if the modules defining the subclasses are not
        #       put in subfolders.
        #       In the future, fix it either to make a cache and to store the
        #       full dependency tree, or save also the path.
        """
        from aiida.djsite.db.models import DbNode

        if cls._plugin_type_string:
            if not cls._plugin_type_string.endswith('.'):
                raise InternalError("The plugin type string does not finish with a dot??")
            
            # If it is 'calculation.Calculation.', we want to filter
            # for things that start with 'calculation.' and so on
            pre, sep, _ = cls._plugin_type_string[:-1].rpartition('.')
            superclass_string = "".join([pre,sep])
            return DbNode.aiidaobjects.filter(
                *args,type__startswith=superclass_string,**kwargs)
        else:
            # Base Node class, with empty string
            return DbNode.aiidaobjects.filter(*args,**kwargs)

    @property
    def computer(self):
        """
        Get the Computer associated to this node, or None if no computer
        is associated.
        
        :return: a computer object
        """
        from aiida.orm import Computer
        
        if self.dbnode.computer is None:
            return None
        else:
            return Computer(dbcomputer=self.dbnode.computer)


    @property
    def label(self):
        """
        Get the label of the node.
        
        :return: a string.
        """
        return self.dbnode.label

    @label.setter
    def label(self,label):
        """
        Set the label of the node.
        
        :param label: a string
        """
        self._update_db_label_field(label)
            
    def _update_db_label_field(self, field_value):
        from django.db import transaction        

        self.dbnode.label = field_value
        if not self._to_be_stored:
            with transaction.commit_on_success():
                self._dbnode.save()
                self._increment_version_number_db()
            
    @property
    def description(self):
        """
        Get the description of the node.
        
        :return: a string
        """
        return self.dbnode.description

    @description.setter
    def description(self,desc):
        """
        Set the description of the node
        
        :param desc: a string
        """
        self._update_db_description_field(desc)

    def _update_db_description_field(self, field_value):
        from django.db import transaction        

        self.dbnode.description = field_value
        if not self._to_be_stored:
            with transaction.commit_on_success():
                self._dbnode.save()
                self._increment_version_number_db()


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
        """
        Get the user.
        
        :return: a Django User object
        """
        return self.dbnode.user

    def replace_link_from(self,src,label):
        """
        Replace an input link with the given label, or simply creates it
        if it does not exist.
        
        :param str src: the source object.
        :param str label: the label of the link from src to the current Node
        """
        from django.db import transaction        
        from aiida.djsite.db.models import Link
        
        try:
            self.add_link_from(src, label)
        except UniquenessError:
            # I have to replace the link; I do it within a transaction
            with transaction.commit_on_success():
                Link.objects.filter(output=self.dbnode,
                                    label=label).delete()
                self.add_link_from(src, label)


    def add_link_from(self,src,label=None):
        """
        Add a link to the current node from the 'src' node.
        Both nodes must be a Node instance (or a subclass of Node)
        (In subclasses, change only this.)
        
        :param src: the source object
        :param str label: the name of the label to set the link from src.
                    Default = None.
        """
        from aiida.djsite.db.models import Link, Path
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
        (Do not change in subclasses, subclass the add_link_from class only.)
        
        :param dest: destination Node object to set the link to.
        :param str label: the name of the link. Default=None
        """
        if not isinstance(dest,Node):
            raise ValueError("dest must be a Node instance")
        dest.add_link_from(self,label)

    def can_link_as_output(self,dest):
        """
        Raise a ValueError if a link from self to dest is not allowed.
        Implement in subclasses.
        
        :param dest: the destination output Node
        :return: a boolean (True)
        """
        return True

    def get_inputs_dict(self):
        """
        Return a dictionary where the key is the label of the input link, and
        the value is the input node.
        
        :return: a dictionary {label:object}
        """
        return dict(self.get_inputs(also_labels=True))

    def get_inputdata_dict(self):
        """
        Return a dictionary where the key is the label of the input link, and
        the value is the input node. Includes only the data nodes, no
        calculations or codes.
        
        :return: a dictionary {label:object}
        """
        from aiida.orm import Data
        return dict(self.get_inputs(type=Data, also_labels=True))

    def get_input(self, name):
        """
        Return the input with a given name, or None if no input with that name
        is set.

        :param str name: the label of the input object
        :return: the input object
        """
        return self.get_inputdata_dict().get(name, None)

    def get_inputs(self,type=None,also_labels=False):
        """
        Return a list of nodes that enter (directly) in this node

        :param type: If specified, should be a class, and it filters only elements of that
                     specific type (or a subclass of 'type')
        :param also_labels: If False (default) only return a list of input nodes.
                If True, return a list of tuples, where each tuple has the following
                format: ('label', Node)
                with 'label' the link label, and Node a Node instance or subclass
        """
        from aiida.djsite.db.models import Link

        inputs_list = ((i.label, i.input.get_aiida_class()) for i in
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

        :param type: if specified, should be a class, and it filters only elements of that
                specific type (or a subclass of 'type')
        :param also_labels: if False (default) only return a list of input nodes.
                If True, return a list of tuples, where each tuple has the following
                format: ('label', Node)
                with 'label' the link label, and Node a Node instance or subclass
        """
        from aiida.djsite.db.models import Link

        outputs_list = ((i.label, i.output.get_aiida_class()) for i in
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
        """
        Set a new attribute to the Node.
        
        :param str key: key name
        :param value: its value
        :raise: ModificationNotAllowed if cannot add such attribute.
        """
        if self._to_be_stored:
            self._attrs_cache["_{}".format(key)] = value
        else:
            if key in self._updatable_attributes:
                return self._set_attribute_db('_{}'.format(key),value)
            else:
                raise ModificationNotAllowed("Cannot set an attribute after saving a node")

    def del_attr(self, key):
        """
        Delete an attribute.

        :param key: attribute to delete.
        :raise AttributeError: if key does not exist.
        :raise ModificationNotAllowed: if the Node was already stored.
        """
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
        """
        Get the attribute.

        :param key: name of the attribute
        :param optional *value: if no attribute key is found, returns value
        
        :return: attribute value
        
        :raise IndexError: If no attribute is found and there is no default
        :raise ValueError: If more than two arguments are passed to get_attr
        """
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
        
        :param string key: key name
        :param value: key value
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
        
        :param str key: key name
        :return: the key value
        :raise: AttributeError: if key starts with underscore
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
        
        :param str key: key name
        :raise: AttributeError: if key starts with underscore
        :raise: ModificationNotAllowed: if the node has already been stored
        """
        if key.startswith('_'):
            raise ValueError("An metadata key cannot start with an underscore")
        if self._to_be_stored:
            raise ModificationNotAllowed("The metadata of a node can be set and deleted "
                                         "only after storing the node")
        self._del_attribute_db(key)

    def metadata(self):
        """
        Get the keys of the metadata.
        
        :return: a list of strings
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

        :param bool also_updatable: if False, does not iterate over 
                      attributes that are updatable
        """
#        TODO: check what happens if someone stores the object while the iterator is
#              being used!
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
        Returns the keys of the attributes.
        
        :return: a list of strings
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
        from aiida.djsite.db.models import Attribute
        
        return Attribute.objects.filter(dbnode=self.dbnode)

    def add_comment(self,content):
        """
        Add a new comment.
        
        :param content: string with comment
        """
        from aiida.djsite.db.models import Comment
        from aiida.djsite.utils import get_automatic_user

        if self._to_be_stored:
            raise ModificationNotAllowed("Comments can be added only after "
                                         "storing the node")

        Comment.objects.create(dbnode=self._dbnode, user=get_automatic_user(), content=content)

    def get_comments(self):
        """
        
        :return: the list of comments, sorted by date; each element of the list is a tuple
            containing (username, username_email, date, content)
        """
        from aiida.djsite.db.models import Comment

        return list(Comment.objects.filter(dbnode=self._dbnode).order_by('time').values_list(
            'user__username', 'user__email', 'time', 'content'))

    def _get_attribute_db(self, key):
        """
        This is the raw-level method that accesses the DB. To be used only internally,
        after saving self.dbnode. Both saves attributes and metadata, in the same way.
        The calling function must check that the key of attributes is prepended with
        an underscore and the key of metadata is not.
        """
        from aiida.djsite.db.models import Attribute

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
        from aiida.djsite.db.models import Attribute

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
        from aiida.djsite.db.models import DbNode

        # I increment the node number using a filter (this should be the right way of doing it;
        # dbnode.nodeversion  = F('nodeversion') + 1
        # will do weird stuff, returning Django Objects instead of numbers, and incrementing at
        # every save; moreover in this way I should do the right thing for concurrent writings
        # I use self._dbnode because this will not do a query to update the node; here I only
        # need to get its pk
        DbNode.objects.filter(pk=self._dbnode.pk).update(nodeversion = F('nodeversion') + 1)

        # This reload internally the node of self._dbworkflowinstance
        self.dbnode

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
        from aiida.djsite.db.models import Attribute
                
        if incrementversion:
            self._increment_version_number_db()
        attr, _ = Attribute.objects.get_or_create(dbnode=self.dbnode, key=key)
        ## TODO: create a get_or_create_with_value method in the djsite.db.models.Attribute class
        attr.setvalue(value)

    def copy(self):
        """
        Return a copy of the current object to work with, not stored yet.

        This is a completely new entry in the DB, with its own UUID.
        Works both on stored instances and with not-stored ones.

        Copies files and attributes, but not the metadata.
        Does not store the Node to allow modification of attributes.
        
        :return: an object copy
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
        """
        
        :return: a string with the uuid
        """
        return unicode(self.dbnode.uuid)

    @property
    def pk(self):
        """
        
        :return: a string with the principle key
        """
        return unicode(self.dbnode.pk)


    @property
    def dbnode(self):
        """
        
        :return: the DbNode object.
        """
        from aiida.djsite.db.models import DbNode
        
        # I also update the internal _dbnode variable, if it was saved
        if not self._to_be_stored:
            self._dbnode = DbNode.objects.get(pk=self._dbnode.pk)
        return self._dbnode

    @property
    def repo_folder(self):
        """
        Get the permanent repository folder.
        Use preferentially the current_folder method.
        
        :return: the permanent RepositoryFolder object
        """
        return self._repo_folder

    @property
    def current_folder(self):
        """
        Get the current repository folder, 
        whether the temporary or the permanent.
        
        :return: the RepositoryFolder object.
        """
        if self._to_be_stored:
            return self.get_temp_folder()
        else:
            return self.repo_folder

    @property
    def path_subfolder(self):
        """
        Get the subfolder in the repository.
        
        :return: a Folder object.
        """
        return self.current_folder.get_subfolder(
            _path_subfolder_name,reset_limit=True)

    def get_path_list(self, subfolder='.'):
        """
        Get the the list of files/directory in the repository of the object.
        
        :param str,optional subfolder: get the list of a subfolder
        :return: a list of strings.
        """
        return self.path_subfolder.get_subfolder(subfolder).get_content_list()

    def get_temp_folder(self):
        """
        Get the folder of the Node in the temporary repository.
        
        :return: a SandboxFolder object mapping the node in the repository.
        """
        if self._temp_folder is None:
            raise InternalError("The temp_folder was asked for node {}, but it is "
                                "not set!".format(self.uuid))
        return self._temp_folder

    def remove_path(self,path):
        """
        Remove a file or directory from the repository directory.
        Can be called only before storing.
        
        :param str path: relative path to file/directory.
        """
        if not self._to_be_stored:
            raise ModificationNotAllowed("Cannot delete a path after storing the node")
        
        if os.path.isabs(path):
            raise ValueError("The destination path in remove_path must be a relative path")
        self.path_subfolder.remove_path(path)

    def add_path(self,src_abs,dst_path):
        """
        Copy a file or folder from a local file inside the repository directory.
        If there is a subpath, folders will be created.

        Copy to a cache directory if the entry has not been saved yet.
        
        :param str src_abs: the absolute path of the file to copy.
        :param str dst_filename: the (relative) path on which to copy.
        
        TODO: in the future, add an add_attachment() that has the same meaning of a metadata file.
        Decide also how to store. If in two separate subfolders, remember to reset the limit.
        """
        if not self._to_be_stored:
            raise ModificationNotAllowed("Cannot insert a path after storing the node")
        
        if not os.path.isabs(src_abs):
            raise ValueError("The source path in add_path must be absolute")
        if os.path.isabs(dst_path):
            raise ValueError("The destination path in add_path must be a filename without any subfolder")
        self.path_subfolder.insert_path(src_abs,dst_path)


    def get_abs_path(self,path,section=_path_subfolder_name):
        """
        Get the absolute path to the folder associated with the Node in the AiiDA repository.
        
        :param str path: the name of the subfolder inside the section.
        :param section: the name of the subfolder ('path' by default).
        :return: a string with the absolute path
        
        For the moment works only for one kind of files, 'path' (internal files)
        """
        #TODO: For the moment works only for one kind of files, 'path' (internal files)
        if os.path.isabs(path):
            raise ValueError("The path in get_abs_path must be relative")
        return self.current_folder.get_subfolder(section,reset_limit=True).get_abs_path(path,check_existence=True)

    def store(self):
        """
        Store a new node in the DB, also saving its repository directory and attributes.

        Can be called only once. Afterwards, attributes cannot be changed anymore!
        Instead, metadata can be changed only AFTER calling this store() function.
        """
        #TODO: This needs to be generalized, allowing for flexible methods for storing data and its attributes.
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

