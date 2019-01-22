# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for Node entities"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import importlib
import os
import typing
import warnings

import six

from aiida.orm.utils import links
from aiida.backends.utils import validate_attribute_key
from aiida.common.hashing import _HASH_EXTRA_KEY
from aiida.common.links import LinkType
from aiida.common.folders import RepositoryFolder, SandboxFolder
from aiida.common.warnings import AiidaDeprecationWarning as DeprecationWarning  # pylint: disable=redefined-builtin
from aiida.common import exceptions
from aiida.common.lang import combomethod, classproperty, type_check
from aiida.common.escaping import sql_string_match
from aiida.manage import get_manager
from aiida.manage.caching import get_use_cache
from aiida.orm.utils.node import AbstractNodeMeta
from aiida.orm.utils.managers import NodeInputManager, NodeOutputManager
from aiida.orm.implementation.nodes import _NO_DEFAULT
from . import comments
from . import convert
from . import entities
from . import groups
from . import computers
from . import querybuilder
from . import users

__all__ = ('Node',)

# pylint: disable=too-many-lines


@six.add_metaclass(AbstractNodeMeta)
class Node(entities.Entity):
    """
    Base class for all nodes in AiiDA.

    Stores attributes starting with an underscore.

    Caches files and attributes before the first save, and saves everything
    only on store(). After the call to store(), attributes cannot be changed.

    Only after storing (or upon loading from uuid) extras can be modified
    and in this case they are directly set on the db.

    In the plugin, also set the _plugin_type_string, to be set in the DB in
    the 'type' field.
    """

    # pylint: disable=too-many-public-methods

    # This will be set by the metaclass call
    _logger = None

    # A list of tuples, saying which attributes cannot be set at the same time
    # See documentation in the set() method.
    _set_incompatibilities = []

    # A tuple of attribute names that can be updated even after node is stored
    # Requires Sealable mixin, but needs empty tuple for base class
    _updatable_attributes = tuple()

    # A tuple of attribute names that will be ignored when creating the hash.
    _hash_ignored_attributes = tuple()

    # Flag that determines whether the class can be cached.
    _cacheable = True

    # region VariousMethods

    def get_desc(self):
        """
        Returns a string with infos retrieved from a node's properties.
        This method is actually overwritten by the inheriting classes

        :return: a description string
        :rtype: str
        """
        return ""

    @classmethod
    def from_backend_entity(cls, backend_entity):
        entity = super(Node, cls).from_backend_entity(backend_entity)
        entity._repo_folder = RepositoryFolder(section=entity._section_name, uuid=entity.uuid)
        # Set the internal parameters
        # Can be redefined in the subclasses
        entity._init_internal_params()

    @classproperty
    def plugin_type_string(cls):
        """Returns the plugin type string of the node class."""
        return cls._plugin_type_string

    @staticmethod
    def get_schema():
        """
        Every node property contains:
            - display_name: display name of the property
            - help text: short help text of the property
            - is_foreign_key: is the property foreign key to other type of the node
            - type: type of the property. e.g. str, dict, int

        :return: get schema of the node
        """
        return {
            "attributes": {
                "display_name": "Attributes",
                "help_text": "Attributes of the node",
                "is_foreign_key": False,
                "type": "dict"
            },
            "attributes.state": {
                "display_name": "State",
                "help_text": "AiiDA state of the calculation",
                "is_foreign_key": False,
                "type": ""
            },
            "ctime": {
                "display_name": "Creation time",
                "help_text": "Creation time of the node",
                "is_foreign_key": False,
                "type": "datetime.datetime"
            },
            "extras": {
                "display_name": "Extras",
                "help_text": "Extras of the node",
                "is_foreign_key": False,
                "type": "dict"
            },
            "id": {
                "display_name": "Id",
                "help_text": "Id of the object",
                "is_foreign_key": False,
                "type": "int"
            },
            "label": {
                "display_name": "Label",
                "help_text": "User-assigned label",
                "is_foreign_key": False,
                "type": "str"
            },
            "mtime": {
                "display_name": "Last Modification time",
                "help_text": "Last modification time",
                "is_foreign_key": False,
                "type": "datetime.datetime"
            },
            "type": {
                "display_name": "Type",
                "help_text": "Code type",
                "is_foreign_key": False,
                "type": "str"
            },
            "user_id": {
                "display_name": "Id of creator",
                "help_text": "Id of the user that created the node",
                "is_foreign_key": True,
                "related_column": "id",
                "related_resource": "_dbusers",
                "type": "int"
            },
            "uuid": {
                "display_name": "Unique ID",
                "help_text": "Universally Unique Identifier",
                "is_foreign_key": False,
                "type": "unicode"
            },
            "nodeversion": {
                "display_name": "Node version",
                "help_text": "Version of the node",
                "is_foreign_key": False,
                "type": "int"
            },
            "process_type": {
                "display_name": "Process type",
                "help_text": "Process type",
                "is_foreign_key": False,
                "type": "str"
            }
        }

    @property
    def logger(self):
        """
        Get the logger of the Node object.

        :return: Logger object
        """
        return self._logger

    def __init__(self, backend=None, **kwargs):
        """
        Initialize the object Node.

        :param uuid: if present, the Node with given uuid is
          loaded from the database.
          (It is not possible to assign a uuid to a new Node.)
        """
        backend = backend or get_manager().get_backend()
        model = backend.nodes.create()
        super(Node, self).__init__(model)

        # Set the internal parameters
        # Can be redefined in the subclasses
        self._init_internal_params()

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, str(self))

    def __str__(self):
        if not self.is_stored:
            return "uuid: {} (unstored)".format(self.uuid)

        return "uuid: {} (pk: {})".format(self.uuid, self.pk)

    def __copy__(self):
        """Copying a Node is not supported in general, but only for the Data sub class."""
        raise exceptions.InvalidOperation('copying a base Node is not supported')

    def __deepcopy__(self, memo):
        """Deep copying a Node is not supported in general, but only for the Data sub class."""
        raise exceptions.InvalidOperation('deep copying a base Node is not supported')

    @property
    def ctime(self):
        """
        Return the creation time of the node.
        """
        return self._backend_entity.ctime

    @property
    def mtime(self):
        """
        Return the modification time of the node.
        """
        return self._backend_entity.mtime

    # TODO: setting initial and internal parameters still to check
    # def _init_internal_params(self):
    #     """
    #     Set the default values for this class; this method is automatically called by the init.

    #     :note: if you inherit this function, ALWAYS remember to
    #       call super()._init_internal_params() as the first thing
    #       in your inherited function.
    #     """
    #     pass

    # @property
    # def _set_defaults(self):
    #     """
    #     Default values to set in the __init__, if no value is explicitly provided for the given key.
    #     It is a dictionary, with k=v; if the key k is not provided to the __init__, and a value is present here,
    #     this is set.
    #     """
    #     return {}

    # def _set_with_defaults(self, **kwargs):
    #     """
    #     Calls the set() method, but also adds the class-defined default
    #     values (defined in the self._set_defaults attribute),
    #     if they are not provided by the user.

    #     :note: for the default values, also allow to define 'hidden' methods,
    #         meaning that if a default value has a key "_state", it will not call
    #         the function "set__state" but rather "_set_state".
    #         This is not allowed, instead, for the standard set() method.
    #     """
    #     self._set_internal(arguments=self._set_defaults, allow_hidden=True)

    #     # Pass everything to 'set'
    #     self.set(**kwargs)

    # def set(self, **kwargs):
    #     """
    #     For each k=v pair passed as kwargs, call the corresponding
    #     set_k(v) method (e.g., calling self.set(property=5, mass=2) will
    #     call self.set_property(5) and self.set_mass(2).
    #     Useful especially in the __init__.

    #     :note: it uses the _set_incompatibilities list of the class to check
    #         that we are not setting methods that cannot be set at the same time.
    #         _set_incompatibilities must be a list of tuples, and each tuple
    #         specifies the elements that cannot be set at the same time.
    #         For instance, if _set_incompatibilities = [('property', 'mass')],
    #         then the call self.set(property=5, mass=2) will raise a ValueError.
    #         If a tuple has more than two values, it raises ValueError if *all*
    #         keys are provided at the same time, but it does not give any error
    #         if at least one of the keys is not present.

    #     :note: If one element of _set_incompatibilities is a tuple with only
    #         one element, this element will not be settable using this function
    #         (and in particular,

    #     :raise ValueError: if the corresponding set_k method does not exist
    #         in self, or if the methods cannot be set at the same time.
    #     """
    #     self._set_internal(arguments=kwargs, allow_hidden=False)

    # def _set_internal(self, arguments, allow_hidden=False):
    #     """
    #     Works as self.set(), but takes a dictionary as the 'arguments' variable,
    #     instead of reading it from the ``kwargs``; moreover, it allows to specify
    #     allow_hidden to True. In this case, if a a key starts with and
    #     underscore, as for instance ``_state``, it will not call
    #     the function ``set__state`` but rather ``_set_state``.
    #     """
    #     for incomp in self._set_incompatibilities:
    #         if all(k in arguments.keys() for k in incomp):
    #             if len(incomp) == 1:
    #                 raise ValueError("Cannot set {} directly when creating "
    #                                  "the node or using the .set() method; "
    #                                  "use the specific method instead.".format(incomp[0]))
    #             else:
    #                 raise ValueError("Cannot set {} at the same time".format(" and ".join(incomp)))

    #     for key, value in arguments.items():
    #         try:
    #             if allow_hidden and key.startswith("_"):
    #                 method = getattr(self, '_set_{}'.format(key[1:]))
    #             else:
    #                 method = getattr(self, 'set_{}'.format(key))
    #         except AttributeError:
    #             raise ValueError("Unable to set '{0}', no set_{0} method " "found".format(key))
    #         if not isinstance(method, typing.Callable):
    #             raise ValueError("Unable to set '{0}', set_{0} is not " "callable!".format(key))
    #         method(value)

    @property
    def type(self):
        """
        Get the type of the node.

        :return: a string.
        """
        return self._backend_entity.type

    @property
    def nodeversion(self):
        """
        Return the version of the node

        :return: A version integer
        :rtype: int
        """
        return self._backend_entity.nodeversion

    @property
    def label(self):
        """
        Get the label of the node.

        :return: a string.
        """
        return self._backend_entity.label

    @label.setter
    def label(self, label):
        """
        Set the label of the node.

        :param label: a string
        """
        self._backend_entity.label = label

    @property
    def description(self):
        """
        Get the description of the node.

        :return: a string
        :rtype: str
        """
        return self._backend_entity.description

    @description.setter
    def description(self, description):
        """
        Set the description of the node

        :param desc: a string
        """
        self._backend_entity.description = description

    def _validate(self):
        """
        Check if the attributes and files retrieved from the DB are valid.
        Raise a ValidationError if something is wrong.

        Must be able to work even before storing: therefore, use the get_attr
        and similar methods that automatically read either from the DB or
        from the internal attribute cache.

        For the base class, this is always valid. Subclasses will reimplement this.
        In the subclass, always call the super()._validate() method first!
        """
        return True

    def get_user(self):
        """
        Get the user.

        :return: a User model object
        :rtype: :class:`aiida.orm.User`
        """
        return users.User.from_backend_entity(self.backend_entity.get_user())

    def get_computer(self):
        """
        Get the computer associated to the node.
        For a CalcJobNode, this represents the computer on which the calculation was run.
        However, this can be used also for (some) data nodes, like RemoteData, to indicate
        on which computer the data is sitting.

        :return: the Computer object or None.
        """
        self._backend_entity.get_computer()

    # endregion

    # region Attributes

    @property
    def attrs_items(self):
        """
        Iterator over the Node attributes, returning tuples (key, value)

        .. deprecated:: 1.0.0b1
        """
        for item in self._backend_entity.attrs_items:
            yield item

    @property
    def attrs_keys(self):
        """
        Returns the keys of the attributes as a generator.

        :return: a generator of a strings
        """
        for item in self._backend_entity.attrs_keys:
            yield item

    def get_attrs(self):
        """
        Return a dictionary with all attributes of this node.
        """
        return dict(self.attrs_items)

    def get_attr(self, key, default=_NO_DEFAULT):
        """
        Get the attribute.

        :param key: name of the attribute
        :param default: if no attribute key is found, returns default

        :return: attribute value

        :raise AttributeError: If no attribute is found and there is no default
        """
        return self._backend_entity.get_attr(key=key, default=default)

    # endregion

    # region Extras

    def set_extra(self, key, value, exclusive=False):
        """
        Sets an extra of a calculation.
        No .store() to be called. Can be used *only* after saving.

        :param key: key name
        :param value: key value
        :param exclusive: (default=False).
            If exclusive is True, it raises a UniquenessError if an Extra with
            the same name already exists in the DB (useful e.g. to "lock" a
            node and avoid to run multiple times the same computation on it).

        :raise UniquenessError: if extra already exists and exclusive is True.
        """
        self._backend_entity.set_extra(key, value, exclusive)

    def set_extras(self, the_dict):
        """
        Immediately sets several extras of a calculation, in the DB!
        No .store() to be called.
        Can be used *only* after saving.

        :param the_dict: a dictionary of key:value to be set as extras        
        :param exclusive: (default=False).
            If exclusive is True, it raises a UniquenessError if an Extra with
            the same name already exists in the DB (useful e.g. to "lock" a
            node and avoid to run multiple times the same computation on it).
        """
        self._backend_entity.set_extras(the_dict)

    def reset_extras(self, new_extras):
        """
        Deletes existing extras and creates new ones.
        :param new_extras: dictionary with new extras
        :return: nothing, an exceptions is raised in several circumnstances
        """
        self._backend_entity.reset_extras(new_extras)

    def get_extra(self, key, *args):
        """
        Get the value of a extras, reading directly from the DB!
        Since extras can be added only after storing the node, this
        function is meaningful to be called only after the .store() method.

        :param key: key name
        :param value: if no attribute key is found, returns value

        :return: the key value

        :raise ValueError: If more than two arguments are passed to get_extra
        """
        self._backend_entity.get_extra(key, *args)

    def get_extras(self):
        """
        Get the value of extras, reading directly from the DB!
        Since extras can be added only after storing the node, this
        function is meaningful to be called only after the .store() method.

        :return: the dictionary of extras ({} if no extras)
        """
        self._backend_entity.get_extras()

    def del_extra(self, key):
        """
        Delete a extra, acting directly on the DB!
        The action is immediately performed on the DB.
        Since extras can be added only after storing the node, this
        function is meaningful to be called only after the .store() method.

        :param key: key name
        :raise: AttributeError: if key starts with underscore
        :raise: ModificationNotAllowed: if the node is not stored yet
        """
        self._backend_entity.del_extra(key)

    @property
    def extras_items(self):
        """
        Iterator over the node extras, returning tuples (key, value)

        .. deprecated:: 1.0.0b1
        """
        for item in self._backend_entity.extras_items:
            yield item

    @property
    def extras_keys(self):
        """
        Returns the keys of the nodes extras as a generator.

        :return: a generator of a strings
        """
        for item in self._backend_entity.extras_keys:
            yield item

    # endregion

    def add_comment(self, content, user=None):
        """
        Add a new comment.

        :param content: string with comment
        :param user: the user to associate with the comment, will use default if not supplied
        :return: the newly created comment
        """
        self._backend_entity.add_comment(content, user)

    def get_comment(self, identifier):
        """
        Return a comment corresponding to the given identifier.

        :param identifier: the comment pk
        :raise NotExistent: if the comment with the given id does not exist
        :raise MultipleObjectsError: if the id cannot be uniquely resolved to a comment
        :return: the comment
        """
        self._backend_entity.get_comment(identifier)

    def get_comments(self):
        """
        Return a sorted list of comments for this node.

        :return: the list of comments, sorted by pk
        """
        self._backend_entity.get_comment(identifier)

    def update_comment(self, identifier, content):
        """
        Update the content of an existing comment.

        :param identifier: the comment pk
        :param content: the new comment content
        :raise NotExistent: if the comment with the given id does not exist
        :raise MultipleObjectsError: if the id cannot be uniquely resolved to a comment
        """
        self._backend_entity.update_comment(identifier, content)

    def remove_comment(self, identifier):
        """
        Delete an existing comment.

        :param identifier: the comment pk
        """
        self._backend_entity.remove_comment(identifier)

    @property
    def uuid(self):
        """
        :return: a string with the uuid
        """
        return self.backend_entity.uuid

    # TODO: decide if we want to keep this or expose different functionality
    @property
    def folder(self):
        """
        Get the folder associated with the node,
        whether it is in the temporary or the permanent repository.

        :return: the RepositoryFolder object.
        """
        return self._backend_entity.folder

    def store_all(self, with_transaction=True, use_cache=None):
        """
        Store the node, together with all input links.

        Unstored nodes from cached incoming linkswill also be stored.

        :parameter with_transaction: if False, no transaction is used. This is meant to be used ONLY if the outer
            calling function has already a transaction open!
        """
        self._backend_entity.store_all(with_transaction=with_transaction, use_cache=use_cache)

    def store(self, with_transaction=True, use_cache=None):
        """
        Store a new node in the DB, also saving its repository directory
        and attributes.

        After being called attributes cannot be
        changed anymore! Instead, extras can be changed only AFTER calling
        this store() function.

        :note: After successful storage, those links that are in the cache, and
            for which also the parent node is already stored, will be
            automatically stored. The others will remain unstored.

        :parameter with_transaction: if False, no transaction is used. This
          is meant to be used ONLY if the outer calling function has already
          a transaction open!
        """
        self._backend_entity.store(with_transaction=with_transaction, use_cache=use_cache)

    # TODO: caching still to check
    # def _store_from_cache(self, cache_node, with_transaction):
    #     from aiida.orm.mixins import Sealable
    #     assert self.type == cache_node.type

    #     self.label = cache_node.label
    #     self.description = cache_node.description

    #     for key, value in cache_node.iterattrs():
    #         if key != Sealable.SEALED_KEY:
    #             self._set_attr(key, value)

    #     self.folder.replace_with_folder(cache_node.folder.abspath, move=False, overwrite=True)

    #     # Make sure the node doesn't have any RETURN links
    #     if cache_node.get_outgoing(link_type=LinkType.RETURN).all():
    #         raise ValueError('Cannot use cache from nodes with RETURN links.')

    #     self.store(with_transaction=with_transaction, use_cache=False)
    #     self.set_extra('_aiida_cached_from', cache_node.uuid)

    # def _add_outputs_from_cache(self, cache_node):
    #     # Add CREATE links
    #     for entry in cache_node.get_outgoing(link_type=LinkType.CREATE):
    #         new_node = entry.node.clone()
    #         new_node.add_incoming(self, link_type=LinkType.CREATE, link_label=entry.link_label)
    #         new_node.store()

    # def get_hash(self, ignore_errors=True, **kwargs):
    #     """
    #     Making a hash based on my attributes
    #     """
    #     from aiida.common.hashing import make_hash
    #     try:
    #         return make_hash(self._get_objects_to_hash(), **kwargs)
    #     except Exception:  # pylint: disable=broad-except
    #         if ignore_errors:
    #             return None
    #         else:
    #             raise

    # def _get_objects_to_hash(self):
    #     """
    #     Return a list of objects which should be included in the hash.
    #     """
    #     computer = self.get_computer()
    #     return [
    #         importlib.import_module(self.__module__.split('.', 1)[0]).__version__, {
    #             key: val
    #             for key, val in self.get_attrs().items()
    #             if (key not in self._hash_ignored_attributes and
    #                 key not in getattr(self, '_updatable_attributes', tuple()))
    #         }, self.folder, computer.uuid if computer is not None else None
    #     ]

    # def rehash(self):
    #     """
    #     Re-generates the stored hash of the Node.
    #     """
    #     self.set_extra(_HASH_EXTRA_KEY, self.get_hash())

    # def clear_hash(self):
    #     """
    #     Sets the stored hash of the Node to None.
    #     """
    #     self.set_extra(_HASH_EXTRA_KEY, None)

    # def get_cache_source(self):
    #     """
    #     Return the UUID of the node that was used in creating this node from the cache, or None if it was not cached

    #     :return: the UUID of the node from which this node was cached, or None if it was not created through the cache
    #     """
    #     return self.get_extra('_aiida_cached_from', None)

    # @property
    # def is_created_from_cache(self):
    #     """
    #     Return whether this node was created from a cached node.cached

    #     :return: boolean, True if the node was created by cloning a cached node, False otherwise
    #     """
    #     return self.get_cache_source() is not None

    # def _get_same_node(self):
    #     """
    #     Returns a stored node from which the current Node can be cached, meaning that the returned Node is a valid
    #     cache, and its ``_aiida_hash`` attribute matches ``self.get_hash()``.

    #     If there are multiple valid matches, the first one is returned. If no matches are found, ``None`` is returned.

    #     Note that after ``self`` is stored, this function can return ``self``.
    #     """
    #     try:
    #         return next(self._iter_all_same_nodes())
    #     except StopIteration:
    #         return None

    # def get_all_same_nodes(self):
    #     """
    #     Return a list of stored nodes which match the type and hash of the current node. For the stored nodes, the
    #     ``_aiida_hash`` extra is checked to determine the hash, while ``self.get_hash()`` is executed on the current
    #     node.

    #     Only nodes which are a valid cache are returned. If the current node is already stored, it can be included in
    #     the returned list if ``self.get_hash()`` matches its ``_aiida_hash``.
    #     """
    #     return list(self._iter_all_same_nodes())

    # def _iter_all_same_nodes(self):
    #     """
    #     Returns an iterator of all same nodes.
    #     """
    #     if not self._cacheable:
    #         return iter(())

    #     hash_ = self.get_hash()
    #     if not hash_:
    #         return iter(())

    #     builder = querybuilder.QueryBuilder()
    #     builder.append(self.__class__, filters={'extras._aiida_hash': hash_}, project='*', subclassing=False)
    #     same_nodes = (n[0] for n in builder.iterall())
    #     return (n for n in same_nodes if n._is_valid_cache())  # pylint: disable=protected-access

    # def _is_valid_cache(self):  # pylint: disable=no-self-use
    #     """
    #     Subclass hook to exclude certain Nodes (e.g. failed calculations) from being considered in the caching process.
    #     """
    #     return True

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
        first_descendant = querybuilder.QueryBuilder().append(
            Node, filters={
                'id': self.pk
            }, tag='self').append(
                Node, with_ancestors='self', project='id').first()
        return bool(first_descendant)

    @property
    def has_parents(self):
        """
        Property to understand if parents are attached to the node
        :return: a boolean
        """
        first_ancestor = querybuilder.QueryBuilder().append(
            Node, filters={
                'id': self.pk
            }, tag='self').append(
                Node, with_descendants='self', project='id').first()
        return bool(first_ancestor)

    # TODO: decide if we want to keep it in the frontend and if we want
    # to keep it with this name (or e.g. have simply .process, and
    # maybe define it only in the ProcessNode subclass)
    def load_process_class(self):
        """
        For nodes that were ran by a Process, the process_type will be set. This can either be an entry point
        string or a module path, which is the identifier for that Process. This method will attempt to load
        the Process class and return
        """
        from aiida.plugins.entry_point import load_entry_point_from_string, is_valid_entry_point_string

        if self.process_type is None:
            return None

        if is_valid_entry_point_string(self.process_type):
            process_class = load_entry_point_from_string(self.process_type)
        else:
            class_module, class_name = self.process_type.rsplit('.', 1)
            module = importlib.import_module(class_module)
            process_class = getattr(module, class_name)

        return process_class

    # region Links

    def get_incoming(self, node_class=None, link_type=(), link_label_filter=None):
        """
        Return a list of link triples that are (directly) incoming into this node.

        :param node_class: If specified, should be a class or tuple of classes, and it filters only
            elements of that specific type (or a subclass of 'type')
        :param link_type: If specified should be a string or tuple to get the inputs of this
            link type, if None then returns all inputs of all link types.
        :param link_label_filter: filters the incoming nodes by its link label.
            Here wildcards (% and _) can be passed in link label filter as we are using "like" in QB.
        """
        return self._backend_entity.get_incoming(
            node_class=node_class, link_type=link_type, link_label_filter=link_label_filter)

    def get_outgoing(self, node_class=None, link_type=(), link_label_filter=None):
        """
        Return a list of link triples that are (directly) outgoing of this node.

        :param node_class: If specified, should be a class or tuple of classes, and it filters only
            elements of that specific type (or a subclass of 'type')
        :param link_type: If specified should be a string or tuple to get the inputs of this
            link type, if None then returns all outputs of all link types.
        :param link_label_filter: filters the outgoing nodes by its link label.
            Here wildcards (% and _) can be passed in link label filter as we are using "like" in QB.
        """
        return self._backend_entity.get_outgoing(
            node_class=node_class, link_type=link_type, link_label_filter=link_label_filter)

    # endregion


#    @classmethod
#    def get_subclass_from_uuid(cls, uuid):
#        """
#        Get a node object from the uuid, with the proper subclass of Node.
#        (if Node(uuid=...) is called, only the Node class is loaded).
#
#        :param uuid: a string with the uuid of the object to be loaded.
#        :return: the object of the proper subclass.
#        :raise: NotExistent: if there is no entry of the desired
#                             object kind with the given uuid.
#
#        .. deprecated:: 1.0.0b1
#            Use :meth:`aiida.orm.Node.objects.get` instead.
#        """
#        warnings.warn("use aidia.orm.Node.objects.get instead", DeprecationWarning)
#        return cls.objects.get(uuid=uuid)
#
#    @classmethod
#    def get_subclass_from_pk(cls, pk):
#        """
#        Get a node object from the pk, with the proper subclass of Node.
#        (integer primary key used in this database),
#        but loading the proper subclass where appropriate.
#
#        :param pk: a string with the pk of the object to be loaded.
#        :return: the object of the proper subclass.
#        :raise: NotExistent: if there is no entry of the desired
#                             object kind with the given pk.
#
#        .. deprecated:: 1.0.0b1
#            Use :meth:`aiida.orm.Node.objects.get` instead.
#        """
#        warnings.warn("use aidia.orm.Node.objects.get instead", DeprecationWarning)
#        return cls.objects.get(id=pk)

#    def __int__(self):
#        """
#        .. deprecated:: 1.0.0b1
#            It will no longer be possible to get the ID this way, it's a dangerous method to have that
#            was only there for legacy query reasons
#        """
#        if not self.is_stored:
#            return None
#
#        return self.id

# region DeprecatedMethods

    @combomethod
    def querybuild(self_or_cls, **kwargs):  # pylint: disable=no-self-argument
        """
        Instantiates and
        :returns: a QueryBuilder instance.

        The QueryBuilder's path has one vertice so far, namely this class.
        Additional parameters (e.g. filters or a label),
        can be passes as keyword arguments.

        :param label: Label to give
        :param filters: filters to apply
        :param project: projections

        This class is a comboclass (see :func:`~aiida.common.utils.combomethod`)
        therefore the method can be called as class or instance method.
        If called as an instance method, adds a filter on the id.

        .. deprecated:: 1.0.0b1
            Use :meth:`aiida.orm.Node.objects.query` instead.
        """
        warnings.warn("use aiida.orm.Node.objects.query instead", DeprecationWarning)

        isclass = kwargs.pop('isclass')
        query = querybuilder.QueryBuilder()
        if isclass:
            query.append(self_or_cls, **kwargs)
        else:
            filters = kwargs.pop('filters', {})
            filters.update({'id': self_or_cls.pk})
            query.append(self_or_cls.__class__, filters=filters, **kwargs)
        return query

    @classmethod
    def query(cls, *_args, **_kwargs):
        """
        Query for nodes of this type

        .. deprecated:: 1.0.0b1
            Use :meth:`aiida.orm.Node.objects.query` instead.
        """
        warnings.warn("use aidia.orm.Node.objects.query instead", DeprecationWarning)
        raise NotImplementedError("This method is no longer available, use Node.objects.query()")

    def get_inputs_dict(self, only_in_db=False, link_type=None):
        """
        Return a dictionary where the key is the label of the input link, and
        the value is the input node.

        .. deprecated:: 1.0.0b1

        :param only_in_db: If true only get stored links, not cached
        :param link_type: Only get inputs of this link type, if None then
                returns all inputs of all link types.
        :return: a dictionary {label:object}
        """
        warnings.warn('get_inputs_dict method is deprecated, use get_incoming instead', DeprecationWarning)

        return dict(self.get_inputs(also_labels=True, only_in_db=only_in_db, link_type=link_type))

    def get_outputs_dict(self, link_type=None):
        """
        Return a dictionary where the key is the label of the output link, and
        the value is the input node.
        As some Nodes (Datas in particular) can have more than one output with
        the same label, all keys have the name of the link with appended the pk
        of the node in output.
        The key without pk appended corresponds to the oldest node.

        .. deprecated:: 1.0.0b1

        :return: a dictionary {linkname:object}
        """
        warnings.warn('get_outputs_dict method is deprecated, use get_outgoing instead', DeprecationWarning)

        if link_type is not None and not isinstance(link_type, LinkType):
            raise TypeError("link_type should be a LinkType object")

        all_outputs = self.get_outputs(also_labels=True, link_type=link_type)

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

    def get_inputs(self, node_type=None, also_labels=False, only_in_db=False, link_type=None):
        """
        Return a list of nodes that enter (directly) in this node

        :param node_type: If specified, should be a class, and it filters only
            elements of that specific type (or a subclass of 'type')
        :param also_labels: If False (default) only return a list of input nodes.
            If True, return a list of tuples, where each tuple has the
            following format: ('label', Node), with 'label' the link label,
            and Node a Node instance or subclass
        :param only_in_db: Return only the inputs that are in the database,
            ignoring those that are in the local cache. Otherwise, return
            all links.
        :param link_type: Only get inputs of this link type, if None then
            returns all inputs of all link types.

        .. deprecated:: 1.0.0b1
        """
        warnings.warn('get_inputs method is deprecated, use get_incoming instead', DeprecationWarning)

        if link_type is not None and not isinstance(link_type, LinkType):
            raise TypeError('link_type should be a LinkType object')

        inputs_list = self._backend_entity._get_db_input_links(link_type=link_type)

        if not only_in_db:
            # Needed for the check
            input_list_keys = [i[0] for i in inputs_list]

            for link_triple in self._incoming_cache:
                if link_triple.link_label in input_list_keys:
                    raise exceptions.InternalError(
                        "There exist a link with the same name '{}' both in the DB and in the internal "
                        "cache for node pk= {}!".format(link_triple.link_label, self.pk))

                if link_type is None or link_triple.link_type is link_type:
                    inputs_list.append((link_triple.link_label, link_triple.node))

        if node_type is None:
            filtered_list = inputs_list
        else:
            filtered_list = [i for i in inputs_list if isinstance(i[1], node_type)]

        if also_labels:
            return list(filtered_list)

        return [i[1] for i in filtered_list]

    def get_outputs(self, node_type=None, also_labels=False, link_type=None):
        """
        Return a list of nodes that exit (directly) from this node

        :param node_type: if specified, should be a class, and it filters only
            elements of that specific node_type (or a subclass of 'node_type')
        :param also_labels: if False (default) only return a list of input nodes.
            If True, return a list of tuples, where each tuple has the
            following format: ('label', Node), with 'label' the link label,
            and Node a Node instance or subclass
        :param link_type: Only return outputs connected by links of this type.

        .. deprecated:: 1.0.0b1
        """
        warnings.warn('get_outputs method is deprecated, use get_outgoing instead', DeprecationWarning)

        if link_type is not None and not isinstance(link_type, LinkType):
            raise TypeError('link_type should be a LinkType object')

        outputs_list = [
            convert.get_orm_entity(entity) for entity in self.backend_entity._get_db_output_links(link_type=link_type)
        ]

        if node_type is None:
            filtered_list = outputs_list
        else:
            filtered_list = (i for i in outputs_list if isinstance(i[1], node_type))

        if also_labels:
            return list(filtered_list)

        return [i[1] for i in filtered_list]

    def iterattrs(self):
        """
        Iterator over the Node attributes, returning tuples (key, value)

        .. deprecated:: 1.0.0b1
        """
        warnings.warn('iterattrs has been deprecated, use attrs_items instead', DeprecationWarning)

        for item in self._backend_entity.attrs_items:
            yield item

    def attrs(self):
        """
        Returns the keys of the attributes as a generator.

        .. deprecated:: 1.0.0b1
        :return: a generator of a strings
        """
        warnings.warn('iterattrs has been deprecated, use attrs_keys instead', DeprecationWarning)

        for item in self._backend_entity.attrs_keys:
            yield item

    def extras(self):
        """
        Get the keys of the extras.

        .. deprecated:: 1.0.0b1
        :return: a list of strings
        """
        warnings.warn('extras has been deprecated, use extras_keys instead', DeprecationWarning)

        for item in self._backend_entity.extras_items:
            yield item

    def iterextras(self):
        """
        Iterator over the extras, returning tuples (key, value)

        .. deprecated:: 1.0.0b1
        """
        warnings.warn('iterextras has been deprecated, use extras_items instead', DeprecationWarning)

        for item in self._backend_entity.extras_keys:
            yield item

    # endregion
