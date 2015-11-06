# -*- coding: utf-8 -*-
import os

from django.core.exceptions import ObjectDoesNotExist

# from aiida.djsite.db.models import DbNode, DbAttribute
from aiida.common.exceptions import (
    DbContentError, InternalError, ModificationNotAllowed,
    NotExistent, UniquenessError)
from aiida.common.folders import RepositoryFolder, SandboxFolder
from aiida.common.utils import classproperty

__copyright__ = u"Copyright (c), 2015, ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE (Theory and Simulation of Materials (THEOS) and National Centre for Computational Design and Discovery of Novel Materials (NCCR MARVEL)), Switzerland and ROBERT BOSCH LLC, USA. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.4.1"
__contributors__ = "Andrea Cepellotti, Giovanni Pizzi, Nicolas Mounet"


def from_type_to_pluginclassname(typestr):
    """
    Return the string to pass to the load_plugin function, starting from
    the 'type' field of a Node.
    """
    # Fix for base class
    if typestr == "":
        typestr = "node.Node."
    if not typestr.endswith("."):
        raise DbContentError("The type name '{}' is not valid!".format(
            typestr))
    return typestr[:-1]  # Strip final dot


class Node(object):
    """
    Base class to map a node in the DB + its permanent repository counterpart.

    Stores attributes starting with an underscore.

    Caches files and attributes before the first save, and saves everything
    only on store(). After the call to store(), in general attributes cannot
    be changed, except for those listed in the self._updatable_attributes
    tuple (empty for this class, can be extended in a subclass).

    Only after storing (or upon loading from uuid) extras can be modified
    and in this case they are directly set on the db.

    In the plugin, also set the _plugin_type_string, to be set in the DB in
    the 'type' field.
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

            # Note: the reverse logic (from type_string to name that can
            # be passed to the plugin loader) is implemented in 
            # aiida.common.pluginloader.
            prefix = "aiida.orm."
            if attrs['__module__'].startswith(prefix):
                # Strip aiida.orm.
                # Append a dot at the end, always
                newcls._plugin_type_string = "{}.{}.".format(
                    attrs['__module__'][len(prefix):], name)
                if newcls._plugin_type_string == 'node.Node.':
                    newcls._plugin_type_string = ''
                newcls._query_type_string = "{}.".format(
                    attrs['__module__'][len(prefix):])
                if newcls._query_type_string == 'node.':
                    newcls._query_type_string = ''
            else:
                raise InternalError("Class {} is not in a module under "
                                    "aiida.orm. (module is {})".format(
                    name, attrs['__module__']))

            return newcls

    # Name to be used for the Repository section
    _section_name = 'node'

    # The name of the subfolder in which to put the files/directories
    # added with add_path
    _path_subfolder_name = 'path'


    # A tuple with attributes that can be updated even after
    # the call of the store() method
    _updatable_attributes = tuple()

    # A list of tuples, saying which attributes cannot be set at the same time
    # See documentation in the set() method.
    _set_incompatibilities = []

    @property
    def logger(self):
        """
        Get the logger of the Node object.
        
        :return: Logger object
        """
        return self._logger

    @classmethod
    def get_subclass_from_uuid(cls, uuid):
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
                uuid, cls.__name__))
        return node

    @classmethod
    def get_subclass_from_pk(cls, pk):
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
            raise NotExistent("No entry with pk= {} found".format(pk))
        if not isinstance(node, cls):
            raise NotExistent("pk= {} is not an instance of {}".format(
                pk, cls.__name__))
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
        Convert the class to an integer. This is needed to allow querying
        with Django. Be careful, though, not to pass it to a wrong field!
        This only returns the local DB principal key (pk) value.
        
        :return: the integer pk of the node or None if not stored.
        """
        if self._to_be_stored:
            return None
        else:
            return self._dbnode.pk

    def __init__(self, **kwargs):
        """
        Initialize the object Node.
        
        :param optional uuid: if present, the Node with given uuid is
          loaded from the database.
          (It is not possible to assign a uuid to a new Node.)
        """
        from aiida.djsite.utils import get_automatic_user
        from aiida.djsite.db.models import DbNode
        from aiida.common.utils import get_new_uuid

        self._to_be_stored = False
        self._temp_folder = None

        dbnode = kwargs.pop('dbnode', None)

        # Empty cache of input links in any case
        self._inputlinks_cache = {}

        # Set the internal parameters
        # Can be redefined in the subclasses
        self._init_internal_params()

        if dbnode is not None:
            if not isinstance(dbnode, DbNode):
                raise TypeError("dbnode is not a DbNode instance")
            if dbnode.pk is None:
                raise ValueError("If cannot load an aiida.orm.Node instance "
                                 "from an unsaved Django DbNode object.")
            if kwargs:
                raise ValueError("If you pass a dbnode, you cannot pass any "
                                 "further parameter")

            # If I am loading, I cannot modify it
            self._to_be_stored = False

            self._dbnode = dbnode

            # If this is changed, fix also the importer
            self._repo_folder = RepositoryFolder(section=self._section_name,
                                                 uuid=self._dbnode.uuid)

        # NO VALIDATION ON __init__ BY DEFAULT, IT IS TOO SLOW SINCE IT OFTEN
        # REQUIRES MULTIPLE DB HITS
        # try:
        #                # Note: the validation often requires to load at least one
        #                # attribute, and therefore it will take a lot of time
        #                # because it has to cache every attribute.
        #                self._validate()
        #            except ValidationError as e:
        #                raise DbContentError("The data in the DB with UUID={} is not "
        #                                     "valid for class {}: {}".format(
        #                    uuid, self.__class__.__name__, e.message))
        else:
            # TODO: allow to get the user from the parameters
            user = get_automatic_user()
            self._dbnode = DbNode(user=user,
                                  uuid=get_new_uuid(),
                                  type=self._plugin_type_string)

            self._to_be_stored = True


            # As creating the temp folder may require some time on slow 
            # filesystems, we defer its creation
            self._temp_folder = None
            # Used only before the first save
            self._attrs_cache = {}
            # If this is changed, fix also the importer
            self._repo_folder = RepositoryFolder(section=self._section_name,
                                                 uuid=self.uuid)

            # Automatically set all *other* attributes, if possible, otherwise
            # stop
            self._set_with_defaults(**kwargs)

    @property
    def _is_stored(self):
        return not self._to_be_stored

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, str(self))

    def __str__(self):
        if self._to_be_stored:
            return "uuid: {} (unstored)".format(self.uuid)
        else:
            return "uuid: {} (pk: {})".format(self.uuid, self.pk)

    def _init_internal_params(self):
        """
        Set here the default values for this class; this method
        is automatically called by the init.
        
        :note: if you inherit this function, ALWAYS remember to
          call super()._init_internal_params() as the first thing
          in your inherited function.
        """
        pass

    @property
    def _set_defaults(self):
        """
        Default values to set in the __init__, if no value is explicitly provided
        for the given key.
        It is a dictionary, with k=v; if the key k is not provided to the __init__,
        and a value is present here, this is set.
        """
        return {}

    @classmethod
    def query(cls, *args, **kwargs):
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
                raise InternalError("The plugin type string does not "
                                    "finish with a dot??")


            # If it is 'calculation.Calculation.', we want to filter
            # for things that start with 'calculation.' and so on
            pre, sep, _ = cls._plugin_type_string[:-1].rpartition('.')
            superclass_string = "".join([pre, sep])
            return DbNode.aiidaobjects.filter(
                *args, type__startswith=superclass_string, **kwargs)
        else:
            # Base Node class, with empty string
            return DbNode.aiidaobjects.filter(*args, **kwargs)

#     @property
#     def computer(self):
#         """
#         Get the Computer associated to this node, or None if no computer
#         is associated.
        
#         :return: a computer object
#         """
#         from aiida.orm import Computer

#         if self.dbnode.dbcomputer is None:
#             return None
#         else:
#             return Computer(dbcomputer=self.dbnode.dbcomputer)

    def _set_with_defaults(self, **kwargs):
        """
        Calls the set() method, but also adds the class-defined default
        values (defined in the self._set_defaults attribute),
        if they are not provided by the user.
        
        :note: for the default values, also allow to define 'hidden' methods,
            meaning that if a default value has a key "_state", it will not call
            the function "set__state" but rather "_set_state".
            This is not allowed, instead, for the standard set() method.
        """
        self._set_internal(arguments=self._set_defaults, allow_hidden=True)

        # Pass everything to 'set'
        self.set(**kwargs)

    def set(self, **kwargs):
        """
        For each k=v pair passed as kwargs, call the corresponding 
        set_k(v) method (e.g., calling self.set(property=5, mass=2) will
        call self.set_property(5) and self.set_mass(2).   
        Useful especially in the __init__.
        
        :note: it uses the _set_incompatibilities list of the class to check
            that we are not setting methods that cannot be set at the same time.
            _set_incompatibilities must be a list of tuples, and each tuple
            specifies the elements that cannot be set at the same time.
            For instance, if _set_incompatibilities = [('property', 'mass')],
            then the call self.set(property=5, mass=2) will raise a ValueError.
            If a tuple has more than two values, it raises ValueError if *all*
            keys are provided at the same time, but it does not give any error
            if at least one of the keys is not present.
        
        :note: If one element of _set_incompatibilities is a tuple with only
            one element, this element will not be settable using this function
            (and in particular, 
        
        :raise ValueError: if the corresponding set_k method does not exist
            in self, or if the methods cannot be set at the same time.
        """
        self._set_internal(arguments=kwargs, allow_hidden=False)

    def _set_internal(self, arguments, allow_hidden=False):
        """
        Works as self.set(), but takes a dictionary as the 'arguments' variable,
        instead of reading it from the **kwargs; moreover, it allows to specify
        allow_hidden to True. In this case, if a a key starts with and 
        underscore, as for instance "_state", it will not call
        the function "set__state" but rather "_set_state".
        """
        import collections

        for incomp in self._set_incompatibilities:
            if all(k in arguments.keys() for k in incomp):
                if len(incomp) == 1:
                    raise ValueError("Cannot set {} directly when creating "
                                     "the node or using the .set() method; "
                                     "use the specific method instead.".format(
                        incomp[0]))
                else:
                    raise ValueError("Cannot set {} at the same time".format(
                        " and ".join(incomp)))

        for k, v in arguments.iteritems():
            try:
                if allow_hidden and k.startswith("_"):
                    method = getattr(self, '_set_{}'.format(k[1:]))
                else:
                    method = getattr(self, 'set_{}'.format(k))
            except AttributeError:
                raise ValueError("Unable to set '{0}', no set_{0} method "
                                 "found".format(k))
            if not isinstance(method, collections.Callable):
                raise ValueError("Unable to set '{0}', set_{0} is not "
                                 "callable!".format(k))
            method(v)


    @property
    def label(self):
        """
        Get the label of the node.
        
        :return: a string.
        """
        return self.dbnode.label

    @label.setter
    def label(self, label):
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
    def description(self, desc):
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

    def _validate(self):
        """
        Check if the attributes and files retrieved from the DB are valid.
        Raise a ValidationError if something is wrong.

        Must be able to work even before storing: therefore, use the get_attr
        and similar methods that automatically read either from the DB or
        from the internal attribute cache.

        For the base class, this is always valid. Subclasses will
        reimplement this.
        In the subclass, always call the super()._validate() method first!
        """
        return True

    def get_user(self):
        """
        Get the user.
        
        :return: a Django DbUser model object
        """
        return self.dbnode.user

    def _has_cached_links(self):
        """
        Return True if there is at least one cached (input) link, that is a
        link that is not stored yet in the database. False otherwise.
        """
        return len(self._inputlinks_cache) != 0

    def _add_link_from(self, src, label=None):
        """
        Add a link to the current node from the 'src' node.
        Both nodes must be a Node instance (or a subclass of Node)
        :note: In subclasses, change only this. Moreover, remember to call
           the super() method in order to properly use the caching logic!
        :note: There is no _add_link_to, in order to avoid that someone 
           redefines that method and forgets about using the caching mechanism.
           Given that it is not restrictive, always use the _add_link_from!
        
        :param src: the source object
        :param str label: the name of the label to set the link from src.
                    Default = None.
        """
        # Check that the label does not already exist

        # This can happen also if both nodes are stored, e.g. if one first
        # stores the output node and then the input node. Therefore I check
        # it here.
        if label in self._inputlinks_cache:
            raise UniquenessError("Input link with name '{}' already present "
                                  "in the internal cache".format(label))
        # See if I am pointing to already saved nodes and I am already
        # linking to a given node
        if src.uuid in [_.uuid for _ in
                        self._inputlinks_cache.values()]:
            raise UniquenessError("A link from node with UUID={} and "
                                  "the current node (UUID={}) already exists!".format(
                src.uuid, self.uuid))


        # If both are stored, write directly on the DB
        if not self._to_be_stored and not src._to_be_stored:
            self._add_dblink_from(src, label)
        else:  # at least one is not stored: add to the internal cache
            self._add_cachelink_from(src, label)

    def _add_cachelink_from(self, src, label):
        """
        Add a link in the cache.
        """
        if label is None:
            raise ModificationNotAllowed("Cannot store a link in the cache if "
                                         "no explicit label is provided. You can avoid "
                                         "to provide an input link name only if "
                                         "both nodes are already stored: in this case, "
                                         "the link will be directly stored in the DB "
                                         "and a default name will be provided")

        if label in self._inputlinks_cache:
            raise UniquenessError("Input link with name '{}' already present "
                                  "in the internal cache")

        self._inputlinks_cache[label] = src

    def _replace_link_from(self, src, label):
        """
        Replace an input link with the given label, or simply creates it
        if it does not exist.
        :note: In subclasses, change only this. Moreover, remember to call
           the super() method in order to properly use the caching logic!
        
        :param src: the source object
        :param str label: the name of the label to set the link from src.
        """
        # If both are stored, write directly on the DB
        if not self._to_be_stored and not src._to_be_stored:
            self._replace_dblink_from(src, label)
            # If the link was in the local cache, remove it
            # (this could happen if I first store the output node, then
            # the input node.
            try:
                del self._inputlinks_cache[label]
            except KeyError:
                pass
        else:  # at least one is not stored: set in the internal cache
            # See if I am pointing to already saved nodes and I am already
            # linking to a given node
            # It is similar to the 'add' method, but if I am replacing the 
            # same node, I will not complain (k!=label)
            if src.uuid in [v.uuid for k, v in
                            self._inputlinks_cache.iteritems() if k != label]:
                raise UniquenessError("A link from node with UUID={} and "
                                      "the current node (UUID={}) already exists!".format(
                    src.uuid, self.uuid))

            self._inputlinks_cache[label] = src

    def _remove_link_from(self, label):
        """
        Remove from the DB the input link with the given label.
        :note: In subclasses, change only this. Moreover, remember to call
           the super() method in order to properly use the caching logic!
        
        :note: No error is raised if the link does not exist.
        
        :param str label: the name of the label to set the link from src.
        """
        # Try to remove from the local cache, no problem if none is present
        try:
            del self._inputlinks_cache[label]
        except KeyError:
            pass

        # If both are stored, remove also from the DB
        if not self._to_be_stored:
            self._remove_dblink_from(label)

    def _replace_dblink_from(self, src, label):
        """
        Replace an input link with the given label, or simply creates it
        if it does not exist.
        
        :note: this function should not be called directly; it acts directly on
            the database.
        
        :param str src: the source object.
        :param str label: the label of the link from src to the current Node
        """
        from django.db import transaction
        from aiida.djsite.db.models import DbLink

        try:
            self._add_dblink_from(src, label)
        except UniquenessError:
            # I have to replace the link; I do it within a transaction
            with transaction.commit_on_success():
                self._remove_dblink_from(label)
                self._add_dblink_from(src, label)

    def _remove_dblink_from(self, label):
        """
        Remove from the DB the input link with the given label.
        
        :note: this function should not be called directly; it acts directly on
            the database.
            
        :note: No checks are done to verify that the link actually exists.
        
        :param str label: the label of the link from src to the current Node
        """
        from django.db import transaction
        from aiida.djsite.db.models import DbLink

        DbLink.objects.filter(output=self.dbnode,
                              label=label).delete()

    def _add_dblink_from(self, src, label=None):
        """
        Add a link to the current node from the 'src' node.
        Both nodes must be a Node instance (or a subclass of Node)
        
        :note: this function should not be called directly; it acts directly on
            the database.
        
        :param src: the source object
        :param str label: the name of the label to set the link from src.
                    Default = None.
        """
        from aiida.djsite.db.models import DbLink, DbPath
        from django.db import IntegrityError, transaction

        if not isinstance(src, Node):
            raise ValueError("src must be a Node instance")
        if self.uuid == src.uuid:
            raise ValueError("Cannot link to itself")

        # Check if the source allows output links from this node
        # (will raise ValueError if 
        # this is not the case)
        src._can_link_as_output(self)

        if self._to_be_stored:
            raise ModificationNotAllowed(
                "Cannot call the internal _add_dblink_from if the "
                "destination node is not stored")
        if src._to_be_stored:
            raise ModificationNotAllowed(
                "Cannot call the internal _add_dblink_from if the "
                "source node is not stored")

        # Check for cycles. This works if the transitive closure is enabled; if it 
        # isn't, this test will never fail, but then having a circular link is not
        # meaningful but does not pose a huge threat
        #
        # I am linking src->self; a loop would be created if a DbPath exists already
        # in the TC table from self to src
        if len(DbPath.objects.filter(parent=self.dbnode, child=src.dbnode)) > 0:
            raise ValueError(
                "The link you are attempting to create would generate a loop")

        if label is None:
            autolabel_idx = 1

            existing_from_autolabels = list(DbLink.objects.filter(
                output=self.dbnode,
                label__startswith="link_").values_list('label', flat=True))
            while "link_{}".format(autolabel_idx) in existing_from_autolabels:
                autolabel_idx += 1

            safety_counter = 0
            while True:
                safety_counter += 1
                if safety_counter > 100:
                    # Well, if you have more than 100 concurrent addings
                    # to the same node, you are clearly doing something wrong...
                    raise InternalError("Hey! We found more than 100 concurrent"
                                        " adds of links "
                                        "to the same nodes! Are you really doing that??")
                try:
                    # transactions are needed here for Postgresql:
                    # https://docs.djangoproject.com/en/1.5/topics/db/transactions/#handling-exceptions-within-postgresql-transactions
                    sid = transaction.savepoint()
                    DbLink.objects.create(input=src.dbnode, output=self.dbnode,
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
                DbLink.objects.create(input=src.dbnode, output=self.dbnode,
                                      label=label)
                transaction.savepoint_commit(sid)
            except IntegrityError as e:
                transaction.savepoint_rollback(sid)
                raise UniquenessError("There is already a link with the same "
                                      "name (raw message was {})"
                                      "".format(e.message))

    def _can_link_as_output(self, dest):
        """
        Raise a ValueError if a link from self to dest is not allowed.
        Implement in subclasses.
        
        :param dest: the destination output Node
        :return: a boolean (True)
        """
        return True

    def get_inputs_dict(self, only_in_db=False):
        """
        Return a dictionary where the key is the label of the input link, and
        the value is the input node.
        
        :return: a dictionary {label:object}
        """
        return dict(self.get_inputs(also_labels=True, only_in_db=only_in_db))

    def get_outputs_dict(self):
        """
        Return a dictionary where the key is the label of the output link, and
        the value is the input node.
        As some Nodes (Datas in particular) can have more than one output with 
        the same label, all keys have the name of the link with appended the pk
        of the node in output.
        The key without pk appended corresponds to the oldest node.
        
        :return: a dictionary {linkname:object}
        """
        all_outputs = self.get_outputs(also_labels=True)

        all_linknames = [i[0] for i in all_outputs]
        linknames_set = list(set(all_linknames))

        # prepare a new output list
        new_outputs = {}
        # first add the defaults
        for irreducible_linkname in linknames_set:
            this_elements = [i[1] for i in all_outputs if i[0] == irreducible_linkname]
            # select the oldest element
            last_element = sorted(this_elements, key=lambda x: x.ctime)[0]
            # for this one add the default value
            new_outputs[irreducible_linkname] = last_element

            # now for everyone append the string with the pk
            for i in this_elements:
                new_outputs[irreducible_linkname + "_{}".format(i.pk)] = i

        return new_outputs

    def get_inputs(self, type=None, also_labels=False, only_in_db=False):
        """
        Return a list of nodes that enter (directly) in this node

        :param type: If specified, should be a class, and it filters only
            elements of that specific type (or a subclass of 'type')
        :param also_labels: If False (default) only return a list of input nodes.
                If True, return a list of tuples, where each tuple has the
                following format: ('label', Node), with 'label' the link label,
                and Node a Node instance or subclass
        :param only_in_db: Return only the inputs that are in the database,
                ignoring those that are in the local cache. Otherwise, return
                all links.
        """
        from aiida.djsite.db.models import DbLink

        inputs_list = [(i.label, i.input.get_aiida_class()) for i in
                       DbLink.objects.filter(output=self.dbnode).distinct()]

        if not only_in_db:
            # Needed for the check
            input_list_keys = [i[0] for i in inputs_list]

            for k, v in self._inputlinks_cache.iteritems():
                if k in input_list_keys:
                    raise InternalError("There exist a link with the same name "
                                        "'{}' both in the DB and in the internal "
                                        "cache for node pk= {}!".format(k, self.pk))
                inputs_list.append((k, v))

        if type is None:
            filtered_list = inputs_list
        else:
            filtered_list = [i for i in inputs_list if isinstance(i[1], type)]

        if also_labels:
            return list(filtered_list)
        else:
            return [i[1] for i in filtered_list]

    def get_outputs(self, type=None, also_labels=False):
        """
        Return a list of nodes that exit (directly) from this node

        :param type: if specified, should be a class, and it filters only
                elements of that specific type (or a subclass of 'type')
        :param also_labels: if False (default) only return a list of input nodes.
                If True, return a list of tuples, where each tuple has the 
                following format: ('label', Node), with 'label' the link label,
                and Node a Node instance or subclass
        """
        from aiida.djsite.db.models import DbLink

        outputs_list = ((i.label, i.output.get_aiida_class()) for i in
                        DbLink.objects.filter(input=self.dbnode).distinct())

        if type is None:
            if also_labels:
                return list(outputs_list)
            else:
                return [i[1] for i in outputs_list]
        else:
            filtered_list = (i for i in outputs_list if isinstance(i[1], type))
            if also_labels:
                return list(filtered_list)
            else:
                return [i[1] for i in filtered_list]

    def get_computer(self):
        """
        Get the computer associated to the node.
        
        :return: the Computer object or None.
        """
        from aiida.orm import Computer

        if self.dbnode.dbcomputer is None:
            return None
        else:
            return Computer(dbcomputer=self.dbnode.dbcomputer)

    def set_computer(self, computer):
        """
        Set the computer to be used by the node.
        
        Note that the computer makes sense only for some nodes: Calculation,
        RemoteData, ...
        
        :param computer: the computer object
        """
        # TODO: probably this method should be in the base class, and
        #      check for the type
        from aiida.djsite.db.models import DbComputer

        if self._to_be_stored:
            self.dbnode.dbcomputer = DbComputer.get_dbcomputer(computer)
        else:
            raise ModificationNotAllowed(
                "Node with uuid={} was already stored".format(self.uuid))

    def _set_attr(self, key, value):
        """
        Set a new attribute to the Node (in the DbAttribute table).
        
        :param str key: key name
        :param value: its value
        :raise ModificationNotAllowed: if such attribute cannot be added (e.g.
            because the node was already stored, and the attribute is not listed
            as updatable).

        :raise ValidationError: if the key is not valid (e.g. it contains the
            separator symbol).        
        """
        from aiida.djsite.db.models import DbAttribute
        import copy

        DbAttribute.validate_key(key)

        if self._to_be_stored:
            self._attrs_cache[key] = copy.deepcopy(value)
        else:
            if key in self._updatable_attributes:
                DbAttribute.set_value_for_node(self.dbnode, key, value)
                self._increment_version_number_db()
            else:
                raise ModificationNotAllowed(
                    "Cannot set an attribute after saving a node")

    def _del_attr(self, key):
        """
        Delete an attribute.

        :param key: attribute to delete.
        :raise AttributeError: if key does not exist.
        :raise ModificationNotAllowed: if the Node was already stored.
        """
        from aiida.djsite.db.models import DbAttribute

        if self._to_be_stored:
            try:
                del self._attrs_cache[key]
            except KeyError:
                raise AttributeError(
                    "DbAttribute {} does not exist".format(key))
        else:
            if key in self._updatable_attributes:
                if not DbAttribute.has_key(self.dbnode, key):
                    raise AttributeError("DbAttribute {} does not exist".format(
                        key))
                DbAttribute.del_value_for_node(self.dbnode, key)
                self._increment_version_number_db()
            else:
                raise ModificationNotAllowed("Cannot delete an attribute after "
                                             "saving a node")

    def _del_all_attrs(self):
        """
        Delete all attributes associated to this node.

        :raise ModificationNotAllowed: if the Node was already stored.
        """
        # I have to convert the attrs in a list, because the list will change
        # while deleting elements
        for attr_name in list(self.attrs()):
            self._del_attr(attr_name)

    def get_attr(self, key, *args):
        """
        Get the attribute.

        :param key: name of the attribute
        :param optional value: if no attribute key is found, returns value
        
        :return: attribute value
        
        :raise IndexError: If no attribute is found and there is no default
        :raise ValueError: If more than two arguments are passed to get_attr
        """
        from aiida.djsite.db.models import DbAttribute

        if len(args) > 1:
            raise ValueError("After the key name you can pass at most one"
                             "value, that is the default value to be used "
                             "if no attribute is found.")
        try:
            if self._to_be_stored:
                try:
                    return self._attrs_cache[key]
                except KeyError:
                    raise AttributeError("DbAttribute '{}' does "
                                         "not exist".format(key))
            else:
                return DbAttribute.get_value_for_node(dbnode=self.dbnode,
                                                      key=key)
        except AttributeError as e:
            try:
                return args[0]
            except IndexError:
                raise e

    def set_extra(self, key, value):
        """
        Immediately sets an extra of a calculation, in the DB!
        No .store() to be called.
        Can be used *only* after saving.

        :param string key: key name
        :param value: key value
        """
        from aiida.djsite.db.models import DbExtra

        DbExtra.validate_key(key)

        if self._to_be_stored:
            raise ModificationNotAllowed(
                "The extras of a node can be set only after "
                "storing the node")
        DbExtra.set_value_for_node(self.dbnode, key, value)
        self._increment_version_number_db()

    def set_extra_exclusive(self, key, value):
        """
        Immediately sets an extra of a calculation, in the DB!
        No .store() to be called.
        Can be used *only* after saving.
        Moreover, it raises an UniquenessError if an Extra with the
        same name already exists in the DB (useful e.g. to "lock" a
        node and avoid to run multiple times the same computation on it).

        :param string key: key name
        :param value: key value
        :raise UniquenessError: if the extra already exists.
        """
        from aiida.djsite.db.models import DbExtra

        DbExtra.validate_key(key)

        if self._to_be_stored:
            raise ModificationNotAllowed(
                "The extras of a node can be set only after "
                "storing the node")
        DbExtra.set_value_for_node(self.dbnode, key, value,
                                   stop_if_existing=True)
        self._increment_version_number_db()


    def set_extras(self, the_dict):
        """
        Immediately sets several extras of a calculation, in the DB!
        No .store() to be called.
        Can be used *only* after saving.

        :param the_dict: a dictionary of key:value to be set as extras
        """

        try:
            for key, value in the_dict.iteritems():
                self.set_extra(key, value)
        except AttributeError:
            raise AttributeError("set_extras takes a dictionary as argument")

    def get_extra(self, key, *args):
        """
        Get the value of a extras, reading directly from the DB!
        Since extras can be added only after storing the node, this
        function is meaningful to be called only after the .store() method.
        
        :param str key: key name
        :param optional value: if no attribute key is found, returns value

        :return: the key value

        :raise ValueError: If more than two arguments are passed to get_extra
        """
        from aiida.djsite.db.models import DbExtra

        if len(args) > 1:
            raise ValueError("After the key name you can pass at most one"
                             "value, that is the default value to be used "
                             "if no extra is found.")

        try:
            if self._to_be_stored:
                raise AttributeError("DbExtra '{}' does not exist yet, the "
                                     "node is not stored".format(key))
            else:
                return DbExtra.get_value_for_node(dbnode=self.dbnode,
                                                  key=key)
        except AttributeError as e:
            try:
                return args[0]
            except IndexError:
                raise e

    def get_extras(self):
        """
        Get the value of extras.
        
        :return: the dictionary of extras ({} if no extras)
        """
        return dict(self.iterextras())

    def del_extra(self, key):
        """
        Delete a extra, acting directly on the DB!
        The action is immediately performed on the DB.
        Since extras can be added only after storing the node, this
        function is meaningful to be called only after the .store() method.
        
        :param str key: key name
        :raise: AttributeError: if key starts with underscore
        :raise: ModificationNotAllowed: if the node is not stored yet
        """
        from aiida.djsite.db.models import DbExtra

        if self._to_be_stored:
            raise ModificationNotAllowed(
                "The extras of a node can be set and deleted "
                "only after storing the node")
        if not DbExtra.has_key(self.dbnode, key):
            raise AttributeError("DbExtra {} does not exist".format(
                key))
        return DbExtra.del_value_for_node(self.dbnode, key)
        self._increment_version_number_db()

    def extras(self):
        """
        Get the keys of the extras.
        
        :return: a list of strings
        """
        from aiida.djsite.db.models import DbExtra

        if self._to_be_stored:
            return
        else:
            extraslist = DbExtra.list_all_node_elements(self.dbnode)
        for e in extraslist:
            yield e.key

    def iterextras(self):
        """
        Iterator over the extras, returning tuples (key, value)
        
        :todo: verify that I am not creating a list internally
        """
        from aiida.djsite.db.models import DbExtra

        if self._to_be_stored:
            # If it is not stored yet, there are no extras that can be
            # added (in particular, we do not even have an ID to use!)
            # Return without value, meaning that this is an empty generator
            return
        else:
            extraslist = DbExtra.list_all_node_elements(self.dbnode)
            for e in extraslist:
                yield (e.key, e.getvalue())

    def iterattrs(self, also_updatable=True):
        """
        Iterator over the attributes, returning tuples (key, value)

        :todo: optimize! At the moment, the call is very slow because it is 
            also calling attr.getvalue() for each attribute, that has to
            perform complicated queries to rebuild the object.

        :param bool also_updatable: if False, does not iterate over 
            attributes that are updatable
        """
        from aiida.djsite.db.models import DbAttribute
        # TODO: check what happens if someone stores the object while
        #        the iterator is being used!
        updatable_list = [attr for attr in self._updatable_attributes]

        if self._to_be_stored:
            for k, v in self._attrs_cache.iteritems():
                if not also_updatable and k in updatable_list:
                    continue
                yield (k, v)
        else:
            all_attrs = DbAttribute.get_all_values_for_node(self.dbnode)
            for attr in all_attrs:
                if not also_updatable and attr in updatable_list:
                    continue
                yield (attr, all_attrs[attr])

    def get_attrs(self):
        """
        Return a dictionary with all attributes of this node.      
        """
        return dict(self.iterattrs())

    def attrs(self):
        """
        Returns the keys of the attributes.
        
        :return: a list of strings
        """
        # Note: I "duplicate" the code from iterattrs, rather than
        # calling iterattrs from here, because iterattrs is slow on each call
        # since it has to call .getvalue(). To improve!
        from aiida.djsite.db.models import DbAttribute

        if self._to_be_stored:
            for k in self._attrs_cache.iterkeys():
                yield k
        else:
            attrlist = DbAttribute.list_all_node_elements(self.dbnode)
            for attr in attrlist:
                yield attr.key

    def add_comment(self, content, user=None):
        """
        Add a new comment.
        
        :param content: string with comment
        """
        from aiida.djsite.db.models import DbComment

        if self._to_be_stored:
            raise ModificationNotAllowed("Comments can be added only after "
                                         "storing the node")

        DbComment.objects.create(dbnode=self._dbnode,
                                 user=user,
                                 content=content)

    def get_comments(self, pk=None):
        """
        Return a sorted list of comment values, one for each comment associated
        to the node.
        
        :param pk: integer or list of integers. If it is specified, returns the 
            comment values with desired pks. (pk refers to DbComment.pk) 
        :return: the list of comments, sorted by pk; each element of the 
            list is a dictionary, containing (pk, email, ctime, mtime, content)
        """
        from aiida.djsite.db.models import DbComment

        if pk is not None:
            try:
                correct = all([isinstance(_, int) for _ in pk])
                if not correct:
                    raise ValueError('pk must be an integer or a list of integers')
            except TypeError:
                if not isinstance(pk, int):
                    raise ValueError('pk must be an integer or a list of integers')
            return list(DbComment.objects.filter(dbnode=self._dbnode, pk=pk
            ).order_by('pk').values('pk', 'user__email',
                                    'ctime', 'mtime', 'content'))

        return list(DbComment.objects.filter(dbnode=self._dbnode).order_by(
            'pk').values('pk', 'user__email', 'ctime', 'mtime', 'content'))

    def _get_dbcomments(self, pk=None):
        """
        Return a sorted list of DbComment associated with the Node.
        :param pk: integer or list of integers. If it is specified, returns the 
                   comment values with desired pks. (pk refers to DbComment.pk) 
        :return: the list of DbComment, sorted by pk.
        """
        from aiida.djsite.db.models import DbComment

        if pk is not None:
            try:
                correct = all([isinstance(_, int) for _ in pk])
                if not correct:
                    raise ValueError('pk must be an integer or a list of integers')
                return list(DbComment.objects.filter(dbnode=self._dbnode, pk__in=pk).order_by('pk'))
            except TypeError:
                if not isinstance(pk, int):
                    raise ValueError('pk must be an integer or a list of integers')
                return list(DbComment.objects.filter(dbnode=self._dbnode, pk=pk).order_by('pk'))

        return list(DbComment.objects.filter(dbnode=self._dbnode).order_by('pk'))

    def _update_comment(self, new_field, comment_pk, user):
        """
        Function called by verdi comment update
        """
        from aiida.djsite.db.models import DbComment

        comment = list(DbComment.objects.filter(dbnode=self._dbnode,
                                                pk=comment_pk, user=user))[0]

        if not isinstance(new_field, basestring):
            raise ValueError("Non string comments are not accepted")

        if not comment:
            raise NotExistent("Found no comment for user {} and pk {}".format(
                user, comment_pk))

        comment.content = new_field
        comment.save()

    def _remove_comment(self, comment_pk, user):
        """
        Function called by verdi comment remove
        """
        from aiida.djsite.db.models import DbComment

        comment = DbComment.objects.filter(dbnode=self._dbnode, pk=comment_pk)[0]
        comment.delete()

    def _increment_version_number_db(self):
        """
        This function increments the version number in the DB.
        This should be called every time you need to increment the version
        (e.g. on adding a extra or attribute). 
        
        :note: Do not manually increment the version number, because if
            two different threads are adding/changing an attribute concurrently,
            the version number would be incremented only once.
        """
        from aiida.djsite.db.models import DbNode
        from django.db.models import F

        # I increment the node number using a filter
        self._dbnode.nodeversion = F('nodeversion') + 1
        self._dbnode.save()

        # This reload internally the node of self._dbnode
        # Note: I have to reload the object (to have the right values in memory,
        # otherwise I only get the Django Field F object as a result!
        self._dbnode = DbNode.objects.get(pk=self._dbnode.pk)

    def copy(self):
        """
        Return a copy of the current object to work with, not stored yet.

        This is a completely new entry in the DB, with its own UUID.
        Works both on stored instances and with not-stored ones.

        Copies files and attributes, but not the extras.
        Does not store the Node to allow modification of attributes.
        
        :return: an object copy
        """
        newobject = self.__class__()
        newobject.dbnode.type = self.dbnode.type  # Inherit type
        newobject.dbnode.label = self.dbnode.label  # Inherit label
        # TODO: add to the description the fact that this was a copy?
        newobject.dbnode.description = self.dbnode.description  # Inherit description
        newobject.dbnode.dbcomputer = self.dbnode.dbcomputer  # Inherit computer

        for k, v in self.iterattrs(also_updatable=False):
            newobject._set_attr(k, v)

        for path in self.get_folder_list():
            newobject.add_path(self.get_abs_path(path), path)

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
        :return: the principal key (the ID) as an integer, or None if the
           node was not stored yet
        """
        return self.dbnode.pk

    @property
    def dbnode(self):
        """
        :return: the corresponding Django DbNode object.
        """
        # I also update the internal _dbnode variable, if it was saved
        # from aiida.djsite.db.models import DbNode
        #        if not self._to_be_stored:
        #            self._dbnode = DbNode.objects.get(pk=self._dbnode.pk)
        return self._dbnode

    @property
    def _repository_folder(self):
        """
        Get the permanent repository folder.
        Use preferentially the folder property.
        
        :return: the permanent RepositoryFolder object
        """
        return self._repo_folder

    @property
    def folder(self):
        """
        Get the folder associated with the node, 
        whether it is in the temporary or the permanent repository.
        
        :return: the RepositoryFolder object.
        """
        if self._to_be_stored:
            return self._get_temp_folder()
        else:
            return self._repository_folder

    @property
    def _get_folder_pathsubfolder(self):
        """
        Get the subfolder in the repository.
        
        :return: a Folder object.
        """
        return self.folder.get_subfolder(
            self._path_subfolder_name, reset_limit=True)

    def get_folder_list(self, subfolder='.'):
        """
        Get the the list of files/directory in the repository of the object.
        
        :param str,optional subfolder: get the list of a subfolder
        :return: a list of strings.
        """
        return self._get_folder_pathsubfolder.get_subfolder(subfolder).get_content_list()

    def _get_temp_folder(self):
        """
        Get the folder of the Node in the temporary repository.
        
        :return: a SandboxFolder object mapping the node in the repository.
        """
        # I create the temp folder only at is first usage
        if self._temp_folder is None:
            self._temp_folder = SandboxFolder()  # This is also created
            # Create the 'path' subfolder in the Sandbox
            self._get_folder_pathsubfolder.create()
        return self._temp_folder

    def remove_path(self, path):
        """
        Remove a file or directory from the repository directory.
        Can be called only before storing.
        
        :param str path: relative path to file/directory.
        """
        if not self._to_be_stored:
            raise ModificationNotAllowed(
                "Cannot delete a path after storing the node")

        if os.path.isabs(path):
            raise ValueError("The destination path in remove_path "
                             "must be a relative path")
        self._get_folder_pathsubfolder.remove_path(path)

    def add_path(self, src_abs, dst_path):
        """
        Copy a file or folder from a local file inside the repository directory.
        If there is a subpath, folders will be created.

        Copy to a cache directory if the entry has not been saved yet.
        
        :param str src_abs: the absolute path of the file to copy.
        :param str dst_filename: the (relative) path on which to copy.
        
        :todo: in the future, add an add_attachment() that has the same
            meaning of a extras file. Decide also how to store. If in two
            separate subfolders, remember to reset the limit.
        """
        if not self._to_be_stored:
            raise ModificationNotAllowed(
                "Cannot insert a path after storing the node")

        if not os.path.isabs(src_abs):
            raise ValueError("The source path in add_path must be absolute")
        if os.path.isabs(dst_path):
            raise ValueError("The destination path in add_path must be a"
                             "filename without any subfolder")
        self._get_folder_pathsubfolder.insert_path(src_abs, dst_path)

    def get_abs_path(self, path=None, section=None):
        """
        Get the absolute path to the folder associated with the
        Node in the AiiDA repository.
        
        :param str path: the name of the subfolder inside the section. If None
                         returns the abspath of the folder. Default = None.
        :param section: the name of the subfolder ('path' by default).
        :return: a string with the absolute path
        
        For the moment works only for one kind of files, 'path' (internal files)
        """
        if path is None:
            return self.folder.abspath
        if section is None:
            section = self._path_subfolder_name
        # TODO: For the moment works only for one kind of files,
        #      'path' (internal files)
        if os.path.isabs(path):
            raise ValueError("The path in get_abs_path must be relative")
        return self.folder.get_subfolder(section,
                                         reset_limit=True).get_abs_path(path, check_existence=True)

    def store_all(self, with_transaction=True):
        """
        Store the node, together with all input links, if cached, and also the
        linked nodes, if they were not stored yet.
        
        :parameter with_transaction: if False, no transaction is used. This
          is meant to be used ONLY if the outer calling function has already
          a transaction open!
        """
        from django.db import transaction
        from aiida.common.utils import EmptyContextManager

        if with_transaction:
            context_man = transaction.commit_on_success()
        else:
            context_man = EmptyContextManager()

        if not self._to_be_stored:
            raise ModificationNotAllowed(
                "Node with pk= {} was already stored".format(self.pk))

        # For each parent, check that all its inputs are stored
        for link in self._inputlinks_cache:
            try:
                parent_node = self._inputlinks_cache[link]
                parent_node._check_are_parents_stored()
            except ModificationNotAllowed:
                raise ModificationNotAllowed("Parent node (UUID={}) has "
                                             "unstored parents, cannot proceed (only direct parents "
                                             "can be unstored and will be stored by store_all, not "
                                             "grandparents or other ancestors".format(parent_node.uuid))

        with context_man:
            # Always without transaction: either it is the context_man here,
            # or it is managed outside
            self._store_input_nodes()
            self.store(with_transaction=False)
            self._store_cached_input_links(with_transaction=False)

        return self

    def _store_input_nodes(self):
        """
        Find all input nodes, and store them, checking that they do not
        have unstored inputs in turn.
        
        :note: this function stores all nodes without transactions; always
          call it from within a transaction!
        """
        if not self._to_be_stored:
            raise ModificationNotAllowed(
                "_store_input_nodes can be called only if the node is "
                "unstored (node {} is stored, instead)".format(self.pk))

        for link in self._inputlinks_cache:
            if self._inputlinks_cache[link]._to_be_stored:
                self._inputlinks_cache[link].store(with_transaction=False)

    def _check_are_parents_stored(self):
        """
        Check if all parents are already stored, otherwise raise.
        
        :raise ModificationNotAllowed: if one of the input nodes in not already
          stored.
        """
        # Preliminary check to verify that inputs are stored already
        for link in self._inputlinks_cache:
            if self._inputlinks_cache[link]._to_be_stored:
                raise ModificationNotAllowed(
                    "Cannot store the input link '{}' because the "
                    "source node is not stored. Either store it first, "
                    "or call _store_input_links with the store_parents "
                    "parameter set to True".format(link))


    def _store_cached_input_links(self, with_transaction=True):
        """
        Store all input links that are in the local cache, transferring them 
        to the DB.
        
        :note: This can be called only if all parents are already stored.
        
        :note: Links are stored only after the input nodes are stored. Moreover,
            link storage is done in a transaction, and if one of the links
            cannot be stored, an exception is raised and *all* links will remain
            in the cache. 
        
        :note: This function can be called only after the node is stored.
           After that, it can be called multiple times, and nothing will be
           executed if no links are still in the cache.
                
        :parameter with_transaction: if False, no transaction is used. This
          is meant to be used ONLY if the outer calling function has already
          a transaction open!
        """
        from django.db import transaction
        from aiida.common.utils import EmptyContextManager

        if with_transaction:
            context_man = transaction.commit_on_success()
        else:
            context_man = EmptyContextManager()

        if self._to_be_stored:
            raise ModificationNotAllowed(
                "Node with pk= {} is not stored yet".format(self.pk))

        with context_man:
            # This raises if there is an unstored node.
            self._check_are_parents_stored()
            # I have to store only those links where the source is already
            # stored
            links_to_store = list(self._inputlinks_cache.keys())

            for link in links_to_store:
                self._add_dblink_from(self._inputlinks_cache[link], link)
            # If everything went smoothly, clear the entries from the cache.
            # I do it here because I delete them all at once if no error
            # occurred; otherwise, links will not be stored and I 
            # should not delete them from the cache (but then an exception
            # would have been raised, and the following lines are not executed)
            for link in links_to_store:
                del self._inputlinks_cache[link]

    def store(self, with_transaction=True):
        """
        Store a new node in the DB, also saving its repository directory
        and attributes.

        Can be called only once. Afterwards, attributes cannot be
        changed anymore! Instead, extras can be changed only AFTER calling
        this store() function.
        
        :note: After successful storage, those links that are in the cache, and
            for which also the parent node is already stored, will be
            automatically stored. The others will remain unstored.
            
        :parameter with_transaction: if False, no transaction is used. This
          is meant to be used ONLY if the outer calling function has already
          a transaction open!
        """
        # TODO: This needs to be generalized, allowing for flexible methods
        # for storing data and its attributes.
        from django.db import transaction
        from aiida.common.utils import EmptyContextManager
        from aiida.common.exceptions import ValidationError
        from aiida.djsite.db.models import DbAttribute
        import aiida.orm.autogroup

        if with_transaction:
            context_man = transaction.commit_on_success()
        else:
            context_man = EmptyContextManager()

        if self._to_be_stored:

            # As a first thing, I check if the data is valid
            self._validate()

            # Verify that parents are already stored. Raises if this is not
            # the case.
            self._check_are_parents_stored()

            # I save the corresponding django entry
            # I set the folder
            # NOTE: I first store the files, then only if this is successful,
            # I store the DB entry. In this way,
            # I assume that if a node exists in the DB, its folder is in place.
            # On the other hand, periodically the user might need to run some
            # bookkeeping utility to check for lone folders.
            self._repository_folder.replace_with_folder(
                self._get_temp_folder().abspath, move=True, overwrite=True)

            # I do the transaction only during storage on DB to avoid timeout
            # problems, especially with SQLite
            try:
                with context_man:
                    # Save the row
                    self._dbnode.save()
                    # Save its attributes 'manually' without incrementing
                    # the version for each add.
                    DbAttribute.reset_values_for_node(self.dbnode,
                                                      attributes=self._attrs_cache,
                                                      with_transaction=False)
                    # This should not be used anymore: I delete it to
                    # possibly free memory
                    del self._attrs_cache

                    self._temp_folder = None
                    self._to_be_stored = False

                    # Here, I store those links that were in the cache and
                    # that are between stored nodes.
                    self._store_cached_input_links()

            # This is one of the few cases where it is ok to do a 'global'
            # except, also because I am re-raising the exception
            except:
                # I put back the files in the sandbox folder since the
                # transaction did not succeed
                self._get_temp_folder().replace_with_folder(
                    self._repository_folder.abspath, move=True, overwrite=True)
                raise

        else:
            raise ModificationNotAllowed(
                "Node with pk= {} was already stored".format(self.pk))

        # Set up autogrouping used be verdi run
        autogroup = aiida.orm.autogroup.current_autogroup
        grouptype = aiida.orm.autogroup.VERDIAUTOGROUP_TYPE
        if autogroup is not None:
            if not isinstance(autogroup, aiida.orm.autogroup.Autogroup):
                raise ValidationError("current_autogroup is not an AiiDA Autogroup")
            if autogroup.is_to_be_grouped(self):
                group_name = autogroup.get_group_name()
                if group_name is not None:
                    from aiida.orm.group import Group

                    g = Group.get_or_create(name=group_name, type_string=grouptype)[0]
                    g.add_nodes(self)

        # This is useful because in this way I can do
        # n = Node().store()
        return self

    def __del__(self):
        """
        Called only upon real object destruction from memory
        I just try to remove junk, whenever possible; do not trust
        too much this function!
        """
        if getattr(self, '_temp_folder', None) is not None:
            self._temp_folder.erase()

    @property
    def out(self):
        """
        Traverse the graph of the database.
        Returns a databaseobject, linked to the current node, by means of the linkname.
        Example:
        B = A.out.results: Returns the object B, with link from A to B, with linkname parameters 
        """
        return NodeOutputManager(self)

    @property
    def inp(self):
        """
        Traverse the graph of the database.
        Returns a databaseobject, linked to the current node, by means of the linkname.
        Example:
        B = A.inp.parameters: returns the object (B), with link from B to A, with linkname parameters
        C= A.inp: returns an InputManager, an object that is meant to be accessed as the previous example
        """
        return NodeInputManager(self)

    @property
    def has_children(self):
        """
        Property to understand if children are attached to the node
        :return: a boolean
        """
        # use the transitive closure
        from aiida.djsite.db.models import DbPath

        childrens = DbPath.objects.filter(parent=self.pk)
        return False if not childrens else True

    @property
    def has_parents(self):
        """
        Property to understand if parents are attached to the node
        :return: a boolean
        """
        # use the transitive closure
        from aiida.djsite.db.models import DbPath

        parents = DbPath.objects.filter(child=self.pk)
        return False if not parents else True


class NodeOutputManager(object):
    """
    To document
    """

    def __init__(self, node):
        """
        :param node: the node object.
        """
        # Possibly add checks here
        self._node = node

    def __dir__(self):
        """
        Allow to list all valid output links
        """
        node_attributes = self._node.get_outputs_dict().keys()
        return sorted(set(list(dir(type(self))) + list(node_attributes)))

    def __iter__(self):
        node_attributes = self._node.get_outputs_dict().keys()
        for k in node_attributes:
            yield k

    def __getattr__(self, name):
        """
        :param name: name of the attribute to be asked to the parser results.
        """
        try:
            return self._node.get_outputs_dict()[name]
        except KeyError:
            raise AttributeError("Node {} does not have an output with link {}"
                                 .format(self._node.pk, name))

    def __getitem__(self, name):
        """
        interface to get to the parser results as a dictionary.
        
        :param name: name of the attribute to be asked to the parser results.
        """
        try:
            return self._node.get_outputs_dict()[name]
        except KeyError:
            raise KeyError("Node {} does not have an output with link {}"
                           .format(self._node.pk, name))


class NodeInputManager(object):
    """
    To document
    """

    def __init__(self, node):
        """
        :param node: the node object.
        """
        # Possibly add checks here
        self._node = node

    def __dir__(self):
        """
        Allow to list all valid input links
        """
        node_attributes = self._node.get_inputs_dict().keys()
        return sorted(set(list(dir(type(self))) + list(node_attributes)))

    def __iter__(self):
        node_attributes = self._node.get_inputs_dict().keys()
        for k in node_attributes:
            yield k

    def __getattr__(self, name):
        """
        :param name: name of the attribute to be asked to the parser results.
        """
        try:
            return self._node.get_inputs_dict()[name]
        except KeyError:
            raise AttributeError("Node {} does not have an input with link {}"
                                 .format(self._node.pk, name))

    def __getitem__(self, name):
        """
        interface to get to the parser results as a dictionary.
        
        :param name: name of the attribute to be asked to the parser results.
        """
        try:
            return self._node.get_inputs_dict()[name]
        except KeyError:
            raise KeyError("Node {} does not have an input with link {}"
                           .format(self._node.pk, name))

class AttributeManager(object):
    """
    An object used internally to return the attributes as a dictionary.
    
    :note: Important! It cannot be used to change variables, just to read
      them. To change values (of unstored nodes), use the proper Node methods.
    """

    def __init__(self, node):
        """
        :param node: the node object.
        """
        # Possibly add checks here
        self._node = node

    def __dir__(self):
        """
        Allow to list the keys of the dictionary
        """
        return sorted(self._node.attrs())

    def __iter__(self):
        """
        Return the keys as an iterator
        """
        for k in self._node.attrs():
            yield k

    def _get_dict(self):
        """
        Return the internal dictionary
        """
        return dict(self._node.iterattrs())

    def __getattr__(self, name):
        """
        Interface to get to dictionary values, using the key as an attribute.
        
        :note: it works only for attributes that only contain letters, numbers
          and underscores, and do not start with a number.
        
        :param name: name of the key whose value is required.
        """
        return self._node.get_attr(name)

    def __getitem__(self, name):
        """
        Interface to get to dictionary values as a dictionary.
        
        :param name: name of the key whose value is required.
        """
        try:
            return self._node.get_attr(name)
        except AttributeError as e:
            raise KeyError(e.message)

