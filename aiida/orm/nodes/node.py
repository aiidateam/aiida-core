# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=too-many-lines
"""Package for node ORM classes."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import copy
import importlib
import six

from aiida.backends.utils import validate_attribute_key
from aiida.common import exceptions
from aiida.common.escaping import sql_string_match
from aiida.common.hashing import make_hash, _HASH_EXTRA_KEY
from aiida.common.lang import classproperty, type_check
from aiida.common.links import LinkType
from aiida.manage.manager import get_manager
from aiida.orm.utils.links import LinkManager, LinkTriple
from aiida.orm.utils.repository import Repository
from aiida.orm.utils.node import AbstractNodeMeta, clean_value

from ..comments import Comment
from ..computers import Computer
from ..entities import Entity
from ..entities import Collection as EntityCollection
from ..querybuilder import QueryBuilder
from ..users import User

__all__ = ('Node',)

_NO_DEFAULT = tuple()


@six.add_metaclass(AbstractNodeMeta)
class Node(Entity):
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

    class Collection(EntityCollection):
        """The collection of AuthInfo entries."""

        def delete(self, node_id):
            """Delete a `Node` from the collection with the given id

            :param node_id: the node id
            """
            node = self.get(id=node_id)

            if not node.is_stored:
                return

            if node.get_outgoing().all():
                raise exceptions.InvalidOperation('cannot delete Node<{}> because it has output links'.format(node.pk))

            repository = node._repository  # pylint: disable=protected-access
            self._backend.nodes.delete(node_id)
            repository.erase(force=True)

    # This will be set by the metaclass call
    _logger = None

    # A tuple of attribute names that can be updated even after node is stored
    # Requires Sealable mixin, but needs empty tuple for base class
    _updatable_attributes = tuple()

    # A tuple of attribute names that will be ignored when creating the hash.
    _hash_ignored_attributes = tuple()

    # Flag that determines whether the class can be cached.
    _cachable = True

    # Base path within the repository where to put objects by default
    _repository_base_path = 'path'

    # Flag that determines whether the class can be stored.
    _storable = False
    _unstorable_message = 'only Data, WorkflowNode, CalculationNode or their subclasses can be stored'

    # These are to be initialized in the `initialization` method
    _incoming_cache = None
    _attrs_cache = None
    _repository = None

    @classmethod
    def from_backend_entity(cls, backend_entity):
        entity = super(Node, cls).from_backend_entity(backend_entity)
        return entity

    def __init__(self, backend=None, user=None, computer=None, **kwargs):
        backend = backend or get_manager().get_backend()

        if computer and not computer.is_stored:
            raise ValueError('the computer is not stored')

        computer = computer.backend_entity if computer else None
        user = user.backend_entity if user else User.objects(backend).get_default().backend_entity

        if user is None:
            raise ValueError('the user cannot be None')

        backend_entity = backend.nodes.create(node_type=self.class_node_type, user=user, computer=computer, **kwargs)
        super(Node, self).__init__(backend_entity)

    def __repr__(self):
        return '<{}: {}>'.format(self.__class__.__name__, str(self))

    def __str__(self):
        if not self.is_stored:
            return 'uuid: {} (unstored)'.format(self.uuid)

        return 'uuid: {} (pk: {})'.format(self.uuid, self.pk)

    def __copy__(self):
        """Copying a Node is not supported in general, but only for the Data sub class."""
        raise exceptions.InvalidOperation('copying a base Node is not supported')

    def __deepcopy__(self, memo):
        """Deep copying a Node is not supported in general, but only for the Data sub class."""
        raise exceptions.InvalidOperation('deep copying a base Node is not supported')

    def initialize(self):
        """
        Initialize internal variables for the backend node

        This needs to be called explicitly in each specific subclass implementation of the init.
        """
        super(Node, self).initialize()
        self._attrs_cache = {}

        # A cache of incoming links represented as a list of LinkTriples instances
        self._incoming_cache = list()

        # Calls the initialisation from the RepositoryMixin
        self._repository = Repository(uuid=self.uuid, is_stored=self.is_stored, base_path=self._repository_base_path)

    def _validate(self):
        """Check if the attributes and files retrieved from the database are valid.

        Must be able to work even before storing: therefore, use the `get_attr` and similar methods that automatically
        read either from the DB or from the internal attribute cache.

        For the base class, this is always valid. Subclasses will reimplement this.
        In the subclass, always call the super()._validate() method first!
        """
        # pylint: disable=no-self-use
        return True

    @classproperty
    def class_node_type(cls):
        """Returns the node type of this node (sub) class."""
        # pylint: disable=no-self-argument,no-member
        return cls._plugin_type_string

    @property
    def logger(self):
        """Return the logger configured for this Node.

        :return: Logger object
        """
        return self._logger

    @property
    def uuid(self):
        """Return the node UUID.

        :return: the string representation of the UUID
        :rtype: str
        """
        return self.backend_entity.uuid

    @property
    def node_type(self):
        """Return the node type.

        :return: the node type
        """
        return self.backend_entity.node_type

    @property
    def process_type(self):
        """Return the node process type.

        :return: the process type
        """
        return self.backend_entity.process_type

    @process_type.setter
    def process_type(self, value):
        """Set the node process type.

        :param value: the new value to set
        """
        self.backend_entity.process_type = value

    @property
    def label(self):
        """Return the node label.

        :return: the label
        """
        return self.backend_entity.label

    @label.setter
    def label(self, value):
        """Set the label.

        :param value: the new value to set
        """
        self.backend_entity.label = value

    @property
    def description(self):
        """Return the node description.

        :return: the description
        """
        return self.backend_entity.description

    @description.setter
    def description(self, value):
        """Set the description.

        :param value: the new value to set
        """
        self.backend_entity.description = value

    @property
    def computer(self):
        """Return the computer of this node.

        :return: the computer or None
        :rtype: `Computer` or None
        """
        if self.backend_entity.computer:
            return Computer.from_backend_entity(self.backend_entity.computer)

        return None

    @computer.setter
    def computer(self, computer):
        """Set the computer of this node.

        :param computer: a `Computer`
        """
        if self.is_stored:
            raise exceptions.ModificationNotAllowed('cannot set the computer on a stored node')

        type_check(computer, Computer, allow_none=True)

        if computer is not None:
            computer = computer.backend_entity

        self.backend_entity.computer = computer

    @property
    def user(self):
        """Return the user of this node.

        :return: the user
        :rtype: `User`
        """
        return User.from_backend_entity(self.backend_entity.user)

    @user.setter
    def user(self, user):
        """Set the user of this node.

        :param user: a `User`
        """
        if self.is_stored:
            raise exceptions.ModificationNotAllowed('cannot set the user on a stored node')

        type_check(user, User)
        self.backend_entity.user = user.backend_entity

    @property
    def ctime(self):
        """Return the node ctime.

        :return: the ctime
        """
        return self.backend_entity.ctime

    @property
    def mtime(self):
        """Return the node mtime.

        :return: the mtime
        """
        return self.backend_entity.mtime

    @property
    def version(self):
        """Return the node version.

        :return: the version
        """
        return self.backend_entity.version

    @property
    def public(self):
        """Return the node public attribute.

        :return: the public attribute
        """
        return self.backend_entity.public

    @property
    def attributes(self):
        """Return the attributes dictionary.

        .. note:: This will fetch all the attributes from the database which can be a heavy operation. If you only need
            the keys or some values, use the iterators `attributes_keys` and `attributes_items`, or the getters
            `get_attribute` and `get_attributes` instead.

        :return: the attributes as a dictionary
        """
        if self.is_stored:
            return self.backend_entity.attributes

        return self._attrs_cache

    def get_attribute(self, key, default=_NO_DEFAULT):
        """Return an attribute.

        :param key: name of the attribute
        :param default: return this value instead of raising if the extra does not exist
        :return: the value of the attribute
        :raises AttributeError: if the attribute does not exist
        """
        try:
            if self.is_stored:
                attribute = self.backend_entity.get_attribute(key=key)
            else:
                attribute = self._attrs_cache[key]
        except (AttributeError, KeyError):
            if default is _NO_DEFAULT:
                raise AttributeError('attribute {} does not exist'.format(key))
            attribute = default

        return attribute

    def get_attributes(self, keys):
        """Return a set of attributes.

        :param keys: names of the attributes
        :return: the values of the attributes
        :raises AttributeError: if at least one attribute does not exist
        """
        return self.backend_entity.get_attributes(keys)

    def set_attribute(self, key, value, clean=True, stored_check=True):
        """Set an attribute to the given value.

        Setting attributes on a stored node is forbidden unless `stored_check` is set to False.

        :param key: name of the attribute
        :param value: value of the attribute
        :param clean: boolean, when True will clean the value before passing it to the backend
        :param stored_check: boolean, if True skips the check whether the node is stored
        :raise aiida.common.ModificationNotAllowed: if the node is stored and `stored_check=False`
        """
        if stored_check and self.is_stored:
            raise exceptions.ModificationNotAllowed('cannot set an attribute on a stored node')

        validate_attribute_key(key)

        if clean:
            value = clean_value(value)

        if self.is_stored:
            self.backend_entity.set_attribute(key, value)
        else:
            self._attrs_cache[key] = value

    def set_attributes(self, attributes):
        """Set attributes.

        .. note:: This will override any existing attributes that are present in the new dictionary.

        :param attributes: the new attributes to set
        """
        if self.is_stored:
            raise exceptions.ModificationNotAllowed('cannot set attributes of a stored node')

        for key, value in attributes.items():
            self._attrs_cache[key] = clean_value(value)

    def reset_attributes(self, attributes):
        """Reset the attributes.

        .. note:: This will completely reset any existing attributes and replace them with the new dictionary.

        :param attributes: the new attributes to set
        """
        if self.is_stored:
            raise exceptions.ModificationNotAllowed('cannot reset the attributes of a stored node')

        self.clear_attributes()
        self.set_attributes(attributes)

    def delete_attribute(self, key, stored_check=True):
        """Delete an attribute.

        Deleting attributes on a stored node is forbidden unless `stored_check` is set to False.

        :param key: name of the attribute
        :param stored_check: boolean, if True skips the check whether the node is stored
        :raises AttributeError: if the attribute does not exist
        :raise aiida.common.ModificationNotAllowed: if the node is stored and `stored_check=False`
        """
        if stored_check and self.is_stored:
            raise exceptions.ModificationNotAllowed('cannot delete an attribute on a stored node')

        if self.is_stored:
            self.backend_entity.delete_attribute(key)
        else:
            try:
                del self._attrs_cache[key]
            except KeyError:
                raise AttributeError('attribute {} does not exist'.format(key))

    def delete_attributes(self, keys):
        """Delete multiple attributes.

        :param keys: names of the attributes to delete
        :raises AttributeError: if at least on of the attribute does not exist
        """
        if self.is_stored:
            raise exceptions.ModificationNotAllowed('cannot delete attributes of a stored node')

        attributes_backup = copy.deepcopy(self._attrs_cache)

        for key in keys:
            try:
                self._attrs_cache.pop(key)
            except KeyError:
                self._attrs_cache = attributes_backup
                raise AttributeError('attribute {} does not exist'.format(key))

    def clear_attributes(self):
        """Delete all attributes."""
        if self.is_stored:
            raise exceptions.ModificationNotAllowed('cannot clear the attributes of a stored node')

        self._attrs_cache = {}

    def attributes_items(self):
        """Return an iterator over the attribute items.

        :return: an iterator with attribute key value pairs
        """
        if self.is_stored:
            for key, value in self.backend_entity.attributes_items():
                yield key, value
        else:
            for key, value in self._attrs_cache.items():
                yield key, value

    def attributes_keys(self):
        """Return an iterator over the attribute keys.

        :return: an iterator with attribute keys
        """
        if self.is_stored:
            for key in self.backend_entity.attributes_keys():
                yield key
        else:
            for key in self._attrs_cache.keys():
                yield key

    @property
    def extras(self):
        """Return the extras dictionary.

        .. note:: This will fetch all the extras from the database which can be a heavy operation. If you only need
            the keys or some values, use the iterators `extras_keys` and `extras_items`, or the getters `get_extra`
            and `get_extras` instead.

        :return: the extras as a dictionary
        """
        return self.backend_entity.extras

    def get_extra(self, key, default=_NO_DEFAULT):
        """Return an extra.

        :param key: name of the extra
        :param default: return this value instead of raising if the extra does not exist
        :return: the value of the extra
        :raises AttributeError: if the extra does not exist
        """
        try:
            return self.backend_entity.get_extra(key)
        except AttributeError:
            if default is not _NO_DEFAULT:
                return default
            raise

    def get_extras(self, keys):
        """Return a set of extras.

        :param keys: names of the extras
        :return: the values of the extras
        :raises AttributeError: if at least one extra does not exist
        """
        return self.backend_entity.get_extras(keys)

    def set_extra(self, key, value):
        """Set an extra to the given value.

        Setting extras on unstored nodes is forbidden.

        :param key: name of the extra
        :param value: value of the extra
        :raise aiida.common.ModificationNotAllowed: if the node is not stored
        """
        if not self.is_stored:
            raise exceptions.ModificationNotAllowed('cannot set extras on unstored nodes')

        self.backend_entity.set_extra(key, clean_value(value))

    def set_extras(self, extras):
        """Set extras.

        .. note:: This will override any existing extras that are present in the new dictionary.

        :param extras: the new extras to set
        """
        if not self.is_stored:
            raise exceptions.ModificationNotAllowed('cannot set extras on unstored nodes')

        self.backend_entity.set_extras(clean_value(extras))

    def reset_extras(self, extras):
        """Reset the extras.

        .. note:: This will completely reset any existing extras and replace them with the new dictionary.

        :param extras: the new extras to set
        """
        if not self.is_stored:
            raise exceptions.ModificationNotAllowed('cannot set extras on unstored nodes')

        if not isinstance(extras, dict):
            raise TypeError('extras has to be a dictionary')

        self.backend_entity.reset_extras(clean_value(extras))

    def delete_extra(self, key):
        """Delete an extra.

        Deleting extras on unstored nodes is forbidden.

        :param key: name of the extra
        :raises AttributeError: if the extra does not exist
        """
        if not self.is_stored:
            raise exceptions.ModificationNotAllowed('cannot delete extras on unstored nodes')

        self.backend_entity.delete_extra(key)

    def delete_extras(self, keys):
        """Delete multiple extras.

        :param keys: names of the extras to delete
        :raises AttributeError: if at least on of the extra does not exist
        """
        if not self.is_stored:
            raise exceptions.ModificationNotAllowed('cannot delete extras on unstored nodes')

        self.backend_entity.delete_extras(keys)

    def clear_extras(self):
        """Delete all extras."""
        if not self.is_stored:
            raise exceptions.ModificationNotAllowed('cannot clear the extras of unstored nodes')

        self.backend_entity.clear_extras()

    def extras_items(self):
        """Return an iterator over the extra items.

        :return: an iterator with extra key value pairs
        """
        for key, value in self.backend_entity.extras():
            yield key, value

    def extras_keys(self):
        """Return an iterator over the attribute keys.

        :return: an iterator with attribute keys
        """
        for key in self.backend_entity.extras():
            yield key

    def append_to_attr(self, key, value, clean=True):
        """
        Append value to an attribute of the Node (in the DbAttribute table).

        :param key: key name of "list-type" attribute
            If attribute doesn't exist, it is created.
        :param value: the value to append to the list
        :param clean: whether to clean the value
            WARNING: when set to False, storing will throw errors
            for any data types not recognized by the db backend
        :raise aiida.common.ValidationError: if the key is not valid, e.g. it contains the separator symbol
        """
        if self.is_stored:
            raise exceptions.ModificationNotAllowed('can only call `append_to_attr` on unstored nodes')

        validate_attribute_key(key)

        self._attrs_cache.setdefault(key, list())

        try:
            if clean:
                self._attrs_cache[key].append(clean_value(value))
            else:
                self._attrs_cache[key].append(value)
        except AttributeError:
            raise AttributeError('can only call `append_to_attr` for attributes that are lists')

    def list_objects(self, key=None):
        """Return a list of the objects contained in this repository, optionally in the given sub directory.

        :param key: fully qualified identifier for the object within the repository
        :return: a list of `File` named tuples representing the objects present in directory with the given key
        """
        return self._repository.list_objects(key)

    def list_object_names(self, key=None):
        """Return a list of the object names contained in this repository, optionally in the given sub directory.

        :param key: fully qualified identifier for the object within the repository
        :return: a list of `File` named tuples representing the objects present in directory with the given key
        """
        return self._repository.list_object_names(key)

    def open(self, key, mode='r'):
        """Open a file handle to an object stored under the given key.

        :param key: fully qualified identifier for the object within the repository
        :param mode: the mode under which to open the handle
        """
        return self._repository.open(key, mode)

    def get_object(self, key):
        """Return the object identified by key.

        :param key: fully qualified identifier for the object within the repository
        :return: a `File` named tuple representing the object located at key
        """
        return self._repository.get_object(key)

    def get_object_content(self, key):
        """Return the content of a object identified by key.

        :param key: fully qualified identifier for the object within the repository
        """
        return self._repository.get_object_content(key)

    def put_object_from_tree(self, path, key=None, contents_only=True, force=False):
        """Store a new object under `key` with the contents of the directory located at `path` on this file system.

        .. warning:: If the repository belongs to a stored node, a `ModificationNotAllowed` exception will be raised.
            This check can be avoided by using the `force` flag, but this should be used with extreme caution!

        :param path: absolute path of directory whose contents to copy to the repository
        :param key: fully qualified identifier for the object within the repository
        :param contents_only: boolean, if True, omit the top level directory of the path and only copy its contents.
        :param force: boolean, if True, will skip the mutability check
        :raises aiida.common.ModificationNotAllowed: if repository is immutable and `force=False`
        """
        self._repository.put_object_from_tree(path, key, contents_only, force)

    def put_object_from_file(self, path, key, mode='w', encoding='utf8', force=False):
        """Store a new object under `key` with contents of the file located at `path` on this file system.

        .. warning:: If the repository belongs to a stored node, a `ModificationNotAllowed` exception will be raised.
            This check can be avoided by using the `force` flag, but this should be used with extreme caution!

        :param path: absolute path of file whose contents to copy to the repository
        :param key: fully qualified identifier for the object within the repository
        :param mode: the file mode with which the object will be written
        :param encoding: the file encoding with which the object will be written
        :param force: boolean, if True, will skip the mutability check
        :raises aiida.common.ModificationNotAllowed: if repository is immutable and `force=False`
        """
        self._repository.put_object_from_file(path, key, mode, encoding, force)

    def put_object_from_filelike(self, handle, key, mode='w', encoding='utf8', force=False):
        """Store a new object under `key` with contents of filelike object `handle`.

        .. warning:: If the repository belongs to a stored node, a `ModificationNotAllowed` exception will be raised.
            This check can be avoided by using the `force` flag, but this should be used with extreme caution!

        :param handle: filelike object with the content to be stored
        :param key: fully qualified identifier for the object within the repository
        :param mode: the file mode with which the object will be written
        :param encoding: the file encoding with which the object will be written
        :param force: boolean, if True, will skip the mutability check
        :raises aiida.common.ModificationNotAllowed: if repository is immutable and `force=False`
        """
        self._repository.put_object_from_filelike(handle, key, mode, encoding, force)

    def delete_object(self, key, force=False):
        """Delete the object from the repository.

        .. warning:: If the repository belongs to a stored node, a `ModificationNotAllowed` exception will be raised.
            This check can be avoided by using the `force` flag, but this should be used with extreme caution!

        :param key: fully qualified identifier for the object within the repository
        :param force: boolean, if True, will skip the mutability check
        :raises aiida.common.ModificationNotAllowed: if repository is immutable and `force=False`
        """
        self._repository.delete_object(key, force)

    def add_comment(self, content, user=None):
        """Add a new comment.

        :param content: string with comment
        :param user: the user to associate with the comment, will use default if not supplied
        :return: the newly created comment
        """
        user = user or User.objects.get_default()
        return Comment(node=self, user=user, content=content).store()

    def get_comment(self, identifier):
        """Return a comment corresponding to the given identifier.

        :param identifier: the comment pk
        :raise aiida.common.NotExistent: if the comment with the given id does not exist
        :raise aiida.common.MultipleObjectsError: if the id cannot be uniquely resolved to a comment
        :return: the comment
        """
        return Comment.objects.get(dbnode_id=self.pk, pk=identifier)

    def get_comments(self):
        """Return a sorted list of comments for this node.

        :return: the list of comments, sorted by pk
        """
        return Comment.objects.find(filters={'dbnode_id': self.pk}, order_by=[{'id': 'asc'}])

    def update_comment(self, identifier, content):
        """Update the content of an existing comment.

        :param identifier: the comment pk
        :param content: the new comment content
        :raise aiida.common.NotExistent: if the comment with the given id does not exist
        :raise aiida.common.MultipleObjectsError: if the id cannot be uniquely resolved to a comment
        """
        comment = Comment.objects.get(dbnode_id=self.pk, pk=identifier)
        comment.set_content(content)

    def remove_comment(self, identifier):
        """Delete an existing comment.

        :param identifier: the comment pk
        """
        Comment.objects.delete(dbnode_id=self.pk, comment=identifier)

    def add_incoming(self, source, link_type, link_label):
        """Add a link of the given type from a given node to ourself.

        :param source: the node from which the link is coming
        :param link_type: the link type
        :param link_label: the link label
        :raise TypeError: if `source` is not a Node instance or `link_type` is not a `LinkType` enum
        :raise ValueError: if the proposed link is invalid
        """
        self.validate_incoming(source, link_type, link_label)
        source.validate_outgoing(self, link_type, link_label)

        if self.is_stored and source.is_stored:
            self.backend_entity.add_incoming(source.backend_entity, link_type, link_label)
        else:
            self._add_incoming_cache(source, link_type, link_label)

    def validate_incoming(self, source, link_type, link_label):
        """Validate adding a link of the given type from a given node to ourself.

        This function will first validate the types of the inputs, followed by the node and link types and validate
        whether in principle a link of that type between the nodes of these types is allowed.the

        Subsequently, the validity of the "degree" of the proposed link is validated, which means validating the
        number of links of the given type from the given node type is allowed.

        :param source: the node from which the link is coming
        :param link_type: the link type
        :param link_label: the link label
        :raise TypeError: if `source` is not a Node instance or `link_type` is not a `LinkType` enum
        :raise ValueError: if the proposed link is invalid
        """
        from aiida.orm.utils.links import validate_link

        type_check(link_type, LinkType, 'the link_type should be a value from the LinkType enum but got: {}'.format(
            type(link_type)))
        type_check(source, Node, 'the source should be a Node instance but got: {}'.format(type(source)))

        validate_link(source, self, link_type, link_label)

        # Check for cycles. This works if the transitive closure is enabled; if it isn't, this test will never fail,
        # but then having a circular link is not meaningful but does not pose a huge threat. I am linking source -> self
        # a loop would be created if a DbPath exists already in the TC table from self to source.
        if link_type in [LinkType.CREATE, LinkType.INPUT_CALC, LinkType.INPUT_WORK]:  # yapf:disable
            if QueryBuilder().append(
                    Node, filters={
                        'id': self.pk
                    }, tag='parent').append(
                        Node, filters={
                            'id': source.pk
                        }, tag='child', with_ancestors='parent').count() > 0:
                raise ValueError('the link you are attempting to create would generate a cycle in the graph')

    def validate_outgoing(self, target, link_type, link_label):  # pylint: disable=unused-argument,no-self-use
        """Validate adding a link of the given type from ourself to a given node.

        The validity of the triple (source, link, target) should be validated in the `validate_incoming` call.
        This method will be called afterwards and can be overriden by subclasses to add additional checks that are
        specific to that subclass.

        :param target: the node to which the link is going
        :param link_type: the link type
        :param link_label: the link label
        :raise TypeError: if `target` is not a Node instance or `link_type` is not a `LinkType` enum
        :raise ValueError: if the proposed link is invalid
        """
        type_check(link_type, LinkType, 'the link_type should be a value from the LinkType enum but got: {}'.format(
            type(link_type)))
        type_check(target, Node, 'the target should be a Node instance but got: {}'.format(type(target)))

    def _add_incoming_cache(self, source, link_type, link_label):
        """Add an incoming link to the cache.

        .. note: the proposed link is not validated in this function, so this should not be called directly
            but it should only be called by `Node.add_incoming`.

        :param source: the node from which the link is coming
        :param link_type: the link type
        :param link_label: the link label
        :raise aiida.common.UniquenessError: if the given link triple already exists in the cache
        """
        link_triple = LinkTriple(source, link_type, link_label)

        if link_triple in self._incoming_cache:
            raise exceptions.UniquenessError('the link triple {} is already present in the cache'.format(link_triple))

        self._incoming_cache.append(link_triple)

    def get_stored_link_triples(self, node_class=None, link_type=(), link_label_filter=None, link_direction='incoming'):
        """Return the list of stored link triples directly incoming to or outgoing of this node.

        Note this will only return link triples that are stored in the database. Anything in the cache is ignored.

        :param node_class: If specified, should be a class, and it filters only elements of that (subclass of) type
        :param link_type: Only get inputs of this link type, if empty tuple then returns all inputs of all link types.
        :param link_label_filter: filters the incoming nodes by its link label. This should be a regex statement as
            one would pass directly to a QuerBuilder filter statement with the 'like' operation.
        :param link_direction: `incoming` or `outgoing` to get the incoming or outgoing links, respectively.
        """
        if not isinstance(link_type, tuple):
            link_type = (link_type,)

        if link_type and not all([isinstance(t, LinkType) for t in link_type]):
            raise TypeError('link_type should be a LinkType or tuple of LinkType: got {}'.format(link_type))

        node_class = node_class or Node
        node_filters = {'id': {'==': self.id}}
        edge_filters = {}

        if link_type:
            edge_filters['type'] = {'in': [t.value for t in link_type]}

        if link_label_filter:
            edge_filters['label'] = {'like': link_label_filter}

        builder = QueryBuilder()
        builder.append(Node, filters=node_filters, tag='main')

        if link_direction == 'outgoing':
            builder.append(
                node_class,
                with_incoming='main',
                project=['*'],
                edge_project=['type', 'label'],
                edge_filters=edge_filters)
        else:
            builder.append(
                node_class,
                with_outgoing='main',
                project=['*'],
                edge_project=['type', 'label'],
                edge_filters=edge_filters)

        return [LinkTriple(entry[0], LinkType(entry[1]), entry[2]) for entry in builder.all()]

    def get_incoming(self, node_class=None, link_type=(), link_label_filter=None):
        """Return a list of link triples that are (directly) incoming into this node.

        :param node_class: If specified, should be a class or tuple of classes, and it filters only
            elements of that specific type (or a subclass of 'type')
        :param link_type: If specified should be a string or tuple to get the inputs of this
            link type, if None then returns all inputs of all link types.
        :param link_label_filter: filters the incoming nodes by its link label.
            Here wildcards (% and _) can be passed in link label filter as we are using "like" in QB.
        """
        if not isinstance(link_type, tuple):
            link_type = (link_type,)

        if self.is_stored:
            link_triples = self.get_stored_link_triples(node_class, link_type, link_label_filter, 'incoming')
        else:
            link_triples = []

        # Get all cached link triples
        for link_triple in self._incoming_cache:

            if link_triple in link_triples:
                raise exceptions.InternalError('Node<{}> has both a stored and cached link triple {}'.format(
                    self.pk, link_triple))

            if not link_type or link_triple.link_type in link_type:
                if link_label_filter is not None:
                    if sql_string_match(string=link_triple.link_label, pattern=link_label_filter):
                        link_triples.append(link_triple)
                else:
                    link_triples.append(link_triple)

        return LinkManager(link_triples)

    def get_outgoing(self, node_class=None, link_type=(), link_label_filter=None):
        """Return a list of link triples that are (directly) outgoing of this node.

        :param node_class: If specified, should be a class or tuple of classes, and it filters only
            elements of that specific type (or a subclass of 'type')
        :param link_type: If specified should be a string or tuple to get the inputs of this
            link type, if None then returns all outputs of all link types.
        :param link_label_filter: filters the outgoing nodes by its link label.
            Here wildcards (% and _) can be passed in link label filter as we are using "like" in QB.
        """
        link_triples = self.get_stored_link_triples(node_class, link_type, link_label_filter, 'outgoing')
        return LinkManager(link_triples)

    def has_cached_links(self):
        """Feturn whether there are unstored incoming links in the cache.

        :return: boolean, True when there are links in the incoming cache, False otherwise
        """
        return bool(self._incoming_cache)

    def store_all(self, with_transaction=True, use_cache=None):
        """Store the node, together with all input links.

        Unstored nodes from cached incoming linkswill also be stored.

        :parameter with_transaction: if False, do not use a transaction because the caller will already have opened one.
        """
        if self.is_stored:
            raise exceptions.ModificationNotAllowed('Node<{}> is already stored'.format(self.id))

        # For each node of a cached incoming link, check that all its incoming links are stored
        for link_triple in self._incoming_cache:
            link_triple.node.verify_are_parents_stored()

        for link_triple in self._incoming_cache:
            if not link_triple.node.is_stored:
                link_triple.node.store(with_transaction=False, use_cache=use_cache)

        return self.store(with_transaction, use_cache=use_cache)

    def store(self, with_transaction=True, use_cache=None):
        """Store the node in the database while saving its attributes and repository directory.

        After being called attributes cannot be changed anymore! Instead, extras can be changed only AFTER calling
        this store() function.

        :note: After successful storage, those links that are in the cache, and for which also the parent node is
            already stored, will be automatically stored. The others will remain unstored.

        :parameter with_transaction: if False, do not use a transaction because the caller will already have opened one.
        """
        # pylint: disable=arguments-differ
        from aiida.manage.caching import get_use_cache

        if not self._storable:
            raise exceptions.StoringNotAllowed(self._unstorable_message)

        if not self.is_stored:

            self._validate()

            # Verify that parents are already stored. Raises if this is not the case.
            self.verify_are_parents_stored()

            # Get default for use_cache if it's not set explicitly.
            if use_cache is None:
                use_cache = get_use_cache(type(self))

            # Retrieve the cached node.
            same_node = self._get_same_node() if use_cache else None

            if same_node is not None:
                self._store_from_cache(same_node, with_transaction=with_transaction)
            else:
                self._store(with_transaction=with_transaction)

            # Set up autogrouping used by verdi run
            from aiida.orm.autogroup import current_autogroup, Autogroup, VERDIAUTOGROUP_TYPE
            from aiida.orm import Group

            if current_autogroup is not None:
                if not isinstance(current_autogroup, Autogroup):
                    raise exceptions.ValidationError('`current_autogroup` is not of type `Autogroup`')

                if current_autogroup.is_to_be_grouped(self):
                    group_label = current_autogroup.get_group_name()
                    if group_label is not None:
                        group = Group.objects.get_or_create(label=group_label, type_string=VERDIAUTOGROUP_TYPE)[0]
                        group.add_nodes(self)

        return self

    def _store(self, with_transaction=True):
        """Store the node in the database while saving its attributes and repository directory.

        :parameter with_transaction: if False, do not use a transaction because the caller will already have opened one.
        """
        # First store the repository folder such that if this fails, there won't be an incomplete node in the database.
        # On the flipside, in the case that storing the node does fail, the repository will now have an orphaned node
        # directory which will have to be cleaned manually sometime.
        self._repository.store()

        try:
            attributes = self._attrs_cache
            links = self._incoming_cache
            self._backend_entity.store(attributes, links, with_transaction=with_transaction)
        except Exception:
            # I put back the files in the sandbox folder since the transaction did not succeed
            self._repository.restore()
            raise

        self._attrs_cache = {}
        self._incoming_cache = list()
        self._backend_entity.set_extra(_HASH_EXTRA_KEY, self.get_hash(), increase_version=False)

        return self

    def verify_are_parents_stored(self):
        """Verify that all `parent` nodes are already stored.

        :raise aiida.common.ModificationNotAllowed: if one of the source nodes of incoming links is not stored.
        """
        for link_triple in self._incoming_cache:
            if not link_triple.node.is_stored:
                raise exceptions.ModificationNotAllowed(
                    'Cannot store because source node of link triple {} is not stored'.format(link_triple))

    def _store_from_cache(self, cache_node, with_transaction):
        """Store this node from an existing cache node."""
        from aiida.orm.utils.mixins import Sealable
        assert self.node_type == cache_node.node_type

        # Make sure the node doesn't have any RETURN links
        if cache_node.get_outgoing(link_type=LinkType.RETURN).all():
            raise ValueError('Cannot use cache from nodes with RETURN links.')

        self.label = cache_node.label
        self.description = cache_node.description

        for key, value in cache_node.attributes.items():
            if key != Sealable.SEALED_KEY:
                self.set_attribute(key, value)

        self.put_object_from_tree(cache_node._repository._get_base_folder().abspath)  # pylint: disable=protected-access

        self._store(with_transaction=with_transaction)
        self._add_outputs_from_cache(cache_node)
        self.set_extra('_aiida_cached_from', cache_node.uuid)

    def _add_outputs_from_cache(self, cache_node):
        """Replicate the output links and nodes from the cached node onto this node."""
        for entry in cache_node.get_outgoing(link_type=LinkType.CREATE):
            new_node = entry.node.clone()
            new_node.add_incoming(self, link_type=LinkType.CREATE, link_label=entry.link_label)
            new_node.store()

    def get_hash(self, ignore_errors=True, **kwargs):
        """Return the hash for this node based on its attributes."""
        try:
            return make_hash(self._get_objects_to_hash(), **kwargs)
        except Exception:  # pylint: disable=broad-except
            if not ignore_errors:
                raise

    def _get_objects_to_hash(self):
        """Return a list of objects which should be included in the hash."""
        objects = [
            importlib.import_module(self.__module__.split('.', 1)[0]).__version__,
            {
                key: val
                for key, val in self.attributes_items()
                if (key not in self._hash_ignored_attributes and
                    key not in getattr(self, '_updatable_attributes', tuple()))
            },
            self._repository._get_base_folder(),  # pylint: disable=protected-access
            self.computer.uuid if self.computer is not None else None
        ]
        return objects

    def rehash(self):
        """Regenerate the stored hash of the Node."""
        self.set_extra(_HASH_EXTRA_KEY, self.get_hash())

    def clear_hash(self):
        """Sets the stored hash of the Node to None."""
        self.set_extra(_HASH_EXTRA_KEY, None)

    def get_cache_source(self):
        """Return the UUID of the node that was used in creating this node from the cache, or None if it was not cached.

        :return: source node UUID or None
        """
        return self.get_extra('_aiida_cached_from', None)

    @property
    def is_created_from_cache(self):
        """Return whether this node was created from a cached node.

        :return: boolean, True if the node was created by cloning a cached node, False otherwise
        """
        return self.get_cache_source() is not None

    def _get_same_node(self):
        """Returns a stored node from which the current Node can be cached or None if it does not exist

        If a node is returned it is a valid cache, meaning its `_aiida_hash` extra matches `self.get_hash()`.
        If there are multiple valid matches, the first one is returned.
        If no matches are found, `None` is returned.

        :return: a stored `Node` instance with the same hash as this code or None
        """
        try:
            return next(self._iter_all_same_nodes())
        except StopIteration:
            return None

    def get_all_same_nodes(self):
        """Return a list of stored nodes which match the type and hash of the current node.

        All returned nodes are valid caches, meaning their `_aiida_hash` extra matches `self.get_hash()`.
        """
        return list(self._iter_all_same_nodes())

    def _iter_all_same_nodes(self):
        """Returns an iterator of all same nodes."""
        node_hash = self.get_hash()

        if not node_hash or not self._cachable:
            return iter(())

        builder = QueryBuilder()
        builder.append(self.__class__, filters={'extras._aiida_hash': node_hash}, project='*', subclassing=False)
        nodes_identical = (n[0] for n in builder.iterall())

        return (node for node in nodes_identical if node.is_valid_cache)

    @property
    def is_valid_cache(self):
        """Hook to exclude certain `Node` instances from being considered a valid cache."""
        # pylint: disable=no-self-use
        return True

    def get_description(self):
        """Return a string with a description of the node.

        :return: a description string
        :rtype: str
        """
        # pylint: disable=no-self-use
        return ''

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
            "node_type": {
                "display_name": "Type",
                "help_text": "Node type",
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
