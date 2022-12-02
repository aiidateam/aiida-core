# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=too-many-arguments
"""Package for node ORM classes."""
import datetime
from functools import cached_property
from logging import Logger
from typing import TYPE_CHECKING, Any, ClassVar, Generic, Iterator, List, Optional, Tuple, Type, TypeVar
from uuid import UUID

from aiida.common import exceptions
from aiida.common.lang import classproperty, type_check
from aiida.common.links import LinkType
from aiida.common.warnings import warn_deprecation
from aiida.manage import get_manager
from aiida.orm.utils.node import AbstractNodeMeta

from ..computers import Computer
from ..entities import Collection as EntityCollection
from ..entities import Entity
from ..extras import EntityExtras
from ..querybuilder import QueryBuilder
from ..users import User
from .attributes import NodeAttributes
from .caching import NodeCaching
from .comments import NodeComments
from .links import NodeLinks
from .repository import NodeRepository

if TYPE_CHECKING:
    from aiida.plugins.entry_point import EntryPoint  # type: ignore

    from ..implementation import BackendNode, StorageBackend

__all__ = ('Node',)

NodeType = TypeVar('NodeType', bound='Node')


class NodeCollection(EntityCollection[NodeType], Generic[NodeType]):
    """The collection of nodes."""

    @staticmethod
    def _entity_base_cls() -> Type['Node']:  # type: ignore
        return Node

    def delete(self, pk: int) -> None:
        """Delete a `Node` from the collection with the given id

        :param pk: the node id
        """
        node = self.get(id=pk)

        if not node.is_stored:
            return

        if node.base.links.get_incoming().all():
            raise exceptions.InvalidOperation(f'cannot delete Node<{node.pk}> because it has incoming links')

        if node.base.links.get_outgoing().all():
            raise exceptions.InvalidOperation(f'cannot delete Node<{node.pk}> because it has outgoing links')

        self._backend.nodes.delete(pk)

    def iter_repo_keys(self,
                       filters: Optional[dict] = None,
                       subclassing: bool = True,
                       batch_size: int = 100) -> Iterator[str]:
        """Iterate over all repository object keys for this ``Node`` class

        .. note:: keys will not be deduplicated, wrap in a ``set`` to achieve this

        :param filters: Filters for the node query
        :param subclassing: Whether to include subclasses of the given class
        :param batch_size: The number of nodes to fetch data for at once
        """
        from aiida.repository import Repository
        query = QueryBuilder(backend=self.backend)
        query.append(self.entity_type, subclassing=subclassing, filters=filters, project=['repository_metadata'])
        for metadata, in query.iterall(batch_size=batch_size):
            for key in Repository.flatten(metadata).values():
                if key is not None:
                    yield key


class NodeBase:
    """A namespace for node related functionality, that is not directly related to its user-facing properties."""

    def __init__(self, node: 'Node') -> None:
        """Construct a new instance of the base namespace."""
        self._node: 'Node' = node

    @cached_property
    def repository(self) -> 'NodeRepository':
        """Return the repository for this node."""
        return NodeRepository(self._node)

    @cached_property
    def caching(self) -> 'NodeCaching':
        """Return an interface to interact with the caching of this node."""
        return self._node._CLS_NODE_CACHING(self._node)  # pylint: disable=protected-access

    @cached_property
    def comments(self) -> 'NodeComments':
        """Return an interface to interact with the comments of this node."""
        return NodeComments(self._node)

    @cached_property
    def attributes(self) -> 'NodeAttributes':
        """Return an interface to interact with the attributes of this node."""
        return NodeAttributes(self._node)

    @cached_property
    def extras(self) -> 'EntityExtras':
        """Return an interface to interact with the extras of this node."""
        return EntityExtras(self._node)

    @cached_property
    def links(self) -> 'NodeLinks':
        """Return an interface to interact with the links of this node."""
        return self._node._CLS_NODE_LINKS(self._node)  # pylint: disable=protected-access


class Node(Entity['BackendNode', NodeCollection], metaclass=AbstractNodeMeta):
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

    _CLS_COLLECTION = NodeCollection
    _CLS_NODE_LINKS = NodeLinks
    _CLS_NODE_CACHING = NodeCaching

    # added by metaclass
    _plugin_type_string: ClassVar[str]
    _query_type_string: ClassVar[str]

    # This will be set by the metaclass call
    _logger: Optional[Logger] = None

    # A tuple of attribute names that can be updated even after node is stored
    # Requires Sealable mixin, but needs empty tuple for base class
    _updatable_attributes: Tuple[str, ...] = tuple()

    # A tuple of attribute names that will be ignored when creating the hash.
    _hash_ignored_attributes: Tuple[str, ...] = tuple()

    # Flag that determines whether the class can be cached.
    _cachable = False

    # Flag that determines whether the class can be stored.
    _storable = False
    _unstorable_message = 'only Data, WorkflowNode, CalculationNode or their subclasses can be stored'

    def __init__(
        self,
        backend: Optional['StorageBackend'] = None,
        user: Optional[User] = None,
        computer: Optional[Computer] = None,
        **kwargs: Any
    ) -> None:
        backend = backend or get_manager().get_profile_storage()

        if computer and not computer.is_stored:
            raise ValueError('the computer is not stored')

        backend_computer = computer.backend_entity if computer else None
        user = user if user else backend.default_user

        if user is None:
            raise ValueError('the user cannot be None')

        backend_entity = backend.nodes.create(
            node_type=self.class_node_type, user=user.backend_entity, computer=backend_computer, **kwargs
        )
        super().__init__(backend_entity)

    @cached_property
    def base(self) -> NodeBase:
        """Return the node base namespace."""
        return NodeBase(self)

    def _check_mutability_attributes(self, keys: Optional[List[str]] = None) -> None:  # pylint: disable=unused-argument
        """Check if the entity is mutable and raise an exception if not.

        This is called from `NodeAttributes` methods that modify the attributes.

        :param keys: the keys that will be mutated, or all if None
        """
        if self.is_stored:
            raise exceptions.ModificationNotAllowed('the attributes of a stored entity are immutable')

    def __eq__(self, other: Any) -> bool:
        """Fallback equality comparison by uuid (can be overwritten by specific types)"""
        if isinstance(other, Node) and self.uuid == other.uuid:
            return True
        return super().__eq__(other)

    def __hash__(self) -> int:
        """Python-Hash: Implementation that is compatible with __eq__"""
        return UUID(self.uuid).int

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}: {str(self)}>'

    def __str__(self) -> str:
        if not self.is_stored:
            return f'uuid: {self.uuid} (unstored)'

        return f'uuid: {self.uuid} (pk: {self.pk})'

    def __copy__(self):
        """Copying a Node is not supported in general, but only for the Data sub class."""
        raise exceptions.InvalidOperation('copying a base Node is not supported')

    def __deepcopy__(self, memo):
        """Deep copying a Node is not supported in general, but only for the Data sub class."""
        raise exceptions.InvalidOperation('deep copying a base Node is not supported')

    def _validate(self) -> bool:
        """Validate information stored in Node object.

        For the :py:class:`~aiida.orm.Node` base class, this check is always valid.
        Subclasses can override this method to perform additional checks
        and should usually call ``super()._validate()`` first!

        This method is called automatically before storing the node in the DB.
        Therefore, use :py:meth:`~aiida.orm.nodes.attributes.NodeAttributes.get()` and similar methods that
        automatically read either from the DB or from the internal attribute cache.
        """
        # pylint: disable=no-self-use
        return True

    def _validate_storability(self) -> None:
        """Verify that the current node is allowed to be stored.

        :raises `aiida.common.exceptions.StoringNotAllowed`: if the node does not match all requirements for storing
        """
        from aiida.plugins.entry_point import is_registered_entry_point

        if not self._storable:
            raise exceptions.StoringNotAllowed(self._unstorable_message)

        if not is_registered_entry_point(self.__module__, self.__class__.__name__, groups=('aiida.node', 'aiida.data')):
            raise exceptions.StoringNotAllowed(
                f'class `{self.__module__}:{self.__class__.__name__}` does not have a registered entry point. '
                'Check that the corresponding plugin is installed '
                'and that the entry point shows up in `verdi plugin list`.'
            )

    @classproperty
    def class_node_type(cls) -> str:
        """Returns the node type of this node (sub) class."""
        # pylint: disable=no-self-argument,no-member
        return cls._plugin_type_string

    @classproperty
    def entry_point(cls) -> Optional['EntryPoint']:
        """Return the entry point associated this node class.

        :return: the associated entry point or ``None`` if it isn't known.
        """
        # pylint: disable=no-self-argument
        from aiida.plugins.entry_point import get_entry_point_from_class
        return get_entry_point_from_class(cls.__module__, cls.__name__)[1]

    @property
    def logger(self) -> Optional[Logger]:
        """Return the logger configured for this Node.

        :return: Logger object
        """
        return self._logger

    @property
    def uuid(self) -> str:
        """Return the node UUID.

        :return: the string representation of the UUID
        """
        return self.backend_entity.uuid

    @property
    def node_type(self) -> str:
        """Return the node type.

        :return: the node type
        """
        return self.backend_entity.node_type

    @property
    def process_type(self) -> Optional[str]:
        """Return the node process type.

        :return: the process type
        """
        return self.backend_entity.process_type

    @process_type.setter
    def process_type(self, value: str) -> None:
        """Set the node process type.

        :param value: the new value to set
        """
        self.backend_entity.process_type = value

    @property
    def label(self) -> str:
        """Return the node label.

        :return: the label
        """
        return self.backend_entity.label

    @label.setter
    def label(self, value: str) -> None:
        """Set the label.

        :param value: the new value to set
        """
        self.backend_entity.label = value

    @property
    def description(self) -> str:
        """Return the node description.

        :return: the description
        """
        return self.backend_entity.description

    @description.setter
    def description(self, value: str) -> None:
        """Set the description.

        :param value: the new value to set
        """
        self.backend_entity.description = value

    @property
    def computer(self) -> Optional[Computer]:
        """Return the computer of this node."""
        if self.backend_entity.computer:
            return Computer.from_backend_entity(self.backend_entity.computer)

        return None

    @computer.setter
    def computer(self, computer: Optional[Computer]) -> None:
        """Set the computer of this node.

        :param computer: a `Computer`
        """
        if self.is_stored:
            raise exceptions.ModificationNotAllowed('cannot set the computer on a stored node')

        type_check(computer, Computer, allow_none=True)

        self.backend_entity.computer = None if computer is None else computer.backend_entity

    @property
    def user(self) -> User:
        """Return the user of this node."""
        return User.from_backend_entity(self.backend_entity.user)

    @user.setter
    def user(self, user: User) -> None:
        """Set the user of this node.

        :param user: a `User`
        """
        if self.is_stored:
            raise exceptions.ModificationNotAllowed('cannot set the user on a stored node')

        type_check(user, User)
        self.backend_entity.user = user.backend_entity

    @property
    def ctime(self) -> datetime.datetime:
        """Return the node ctime.

        :return: the ctime
        """
        return self.backend_entity.ctime

    @property
    def mtime(self) -> datetime.datetime:
        """Return the node mtime.

        :return: the mtime
        """
        return self.backend_entity.mtime

    def store_all(self, with_transaction: bool = True) -> 'Node':
        """Store the node, together with all input links.

        Unstored nodes from cached incoming linkswill also be stored.

        :parameter with_transaction: if False, do not use a transaction because the caller will already have opened one.
        """
        if self.is_stored:
            raise exceptions.ModificationNotAllowed(f'Node<{self.pk}> is already stored')

        # For each node of a cached incoming link, check that all its incoming links are stored
        for link_triple in self.base.links.incoming_cache:
            link_triple.node._verify_are_parents_stored()  # pylint: disable=protected-access

        for link_triple in self.base.links.incoming_cache:
            if not link_triple.node.is_stored:
                link_triple.node.store(with_transaction=with_transaction)

        return self.store(with_transaction)

    def store(self, with_transaction: bool = True) -> 'Node':  # pylint: disable=arguments-differ
        """Store the node in the database while saving its attributes and repository directory.

        After being called attributes cannot be changed anymore! Instead, extras can be changed only AFTER calling
        this store() function.

        :note: After successful storage, those links that are in the cache, and for which also the parent node is
            already stored, will be automatically stored. The others will remain unstored.

        :parameter with_transaction: if False, do not use a transaction because the caller will already have opened one.
        """
        from aiida.manage.caching import get_use_cache

        if not self.is_stored:

            # Call `_validate_storability` directly and not in `_validate` in case sub class forgets to call the super.
            self._validate_storability()
            self._validate()

            # Verify that parents are already stored. Raises if this is not the case.
            self._verify_are_parents_stored()

            # Determine whether the cache should be used for the process type of this node.
            use_cache = get_use_cache(identifier=self.process_type)

            # Clean the values on the backend node *before* computing the hash in `_get_same_node`. This will allow
            # us to set `clean=False` if we are storing normally, since the values will already have been cleaned
            self._backend_entity.clean_values()

            # Retrieve the cached node.
            same_node = self.base.caching._get_same_node() if use_cache else None  # pylint: disable=protected-access

            if same_node is not None:
                self._store_from_cache(same_node, with_transaction=with_transaction)
            else:
                self._store(with_transaction=with_transaction, clean=True)

            if self.backend.autogroup.is_to_be_grouped(self):
                group = self.backend.autogroup.get_or_create_group()
                group.add_nodes(self)

        return self

    def _store(self, with_transaction: bool = True, clean: bool = True) -> 'Node':
        """Store the node in the database while saving its attributes and repository directory.

        :param with_transaction: if False, do not use a transaction because the caller will already have opened one.
        :param clean: boolean, if True, will clean the attributes and extras before attempting to store
        """
        self.base.repository._store()  # pylint: disable=protected-access

        links = self.base.links.incoming_cache
        self._backend_entity.store(links, with_transaction=with_transaction, clean=clean)

        self.base.links.incoming_cache = []
        self.base.caching.rehash()

        return self

    def _verify_are_parents_stored(self) -> None:
        """Verify that all `parent` nodes are already stored.

        :raise aiida.common.ModificationNotAllowed: if one of the source nodes of incoming links is not stored.
        """
        for link_triple in self.base.links.incoming_cache:
            if not link_triple.node.is_stored:
                raise exceptions.ModificationNotAllowed(
                    f'Cannot store because source node of link triple {link_triple} is not stored'
                )

    def _store_from_cache(self, cache_node: 'Node', with_transaction: bool) -> None:
        """Store this node from an existing cache node.

        .. note::

            With the current implementation of the backend repository, which automatically deduplicates the content that
            it contains, we do not have to copy the contents of the source node. Since the content should be exactly
            equal, the repository will already contain it and there is nothing to copy. We simply replace the current
            ``repository`` instance with a clone of that of the source node, which does not actually copy any files.

        """
        from aiida.orm.utils.mixins import Sealable
        assert self.node_type == cache_node.node_type

        # Make sure the node doesn't have any RETURN links
        if cache_node.base.links.get_outgoing(link_type=LinkType.RETURN).all():
            raise ValueError('Cannot use cache from nodes with RETURN links.')

        self.label = cache_node.label
        self.description = cache_node.description

        # Make sure to reinitialize the repository instance of the clone to that of the source node.
        self.base.repository._copy(cache_node.base.repository)  # pylint: disable=protected-access

        for key, value in cache_node.base.attributes.all.items():
            if key != Sealable.SEALED_KEY:
                self.base.attributes.set(key, value)

        self._store(with_transaction=with_transaction, clean=False)
        self._add_outputs_from_cache(cache_node)
        self.base.extras.set('_aiida_cached_from', cache_node.uuid)

    def _add_outputs_from_cache(self, cache_node: 'Node') -> None:
        """Replicate the output links and nodes from the cached node onto this node."""
        for entry in cache_node.base.links.get_outgoing(link_type=LinkType.CREATE):
            new_node = entry.node.clone()
            new_node.base.links.add_incoming(self, link_type=LinkType.CREATE, link_label=entry.link_label)
            new_node.store()

    def get_description(self) -> str:
        """Return a string with a description of the node.

        :return: a description string
        """
        # pylint: disable=no-self-use
        return ''

    @property
    def is_valid_cache(self) -> bool:
        """Hook to exclude certain ``Node`` classes from being considered a valid cache.

        The base class assumes that all node instances are valid to cache from, unless the ``_VALID_CACHE_KEY`` extra
        has been set to ``False`` explicitly. Subclasses can override this property with more specific logic, but should
        probably also consider the value returned by this base class.
        """
        kls = self.__class__.__name__
        warn_deprecation(
            f'`{kls}.is_valid_cache` is deprecated, use `{kls}.base.caching.is_valid_cache` instead.',
            version=3,
            stacklevel=2
        )
        return self.base.caching.is_valid_cache

    @is_valid_cache.setter
    def is_valid_cache(self, valid: bool) -> None:
        """Set whether this node instance is considered valid for caching or not.

        If a node instance has this property set to ``False``, it will never be used in the caching mechanism, unless
        the subclass overrides the ``is_valid_cache`` property and ignores it implementation completely.

        :param valid: whether the node is valid or invalid for use in caching.
        """
        kls = self.__class__.__name__
        warn_deprecation(
            f'`{kls}.is_valid_cache` is deprecated, use `{kls}.base.caching.is_valid_cache` instead.',
            version=3,
            stacklevel=2
        )
        self.base.caching.is_valid_cache = valid

    _deprecated_repo_methods = {
        'copy_tree': 'copy_tree',
        'delete_object': 'delete_object',
        'get_object': 'get_object',
        'get_object_content': 'get_object_content',
        'glob': 'glob',
        'list_objects': 'list_objects',
        'list_object_names': 'list_object_names',
        'open': 'open',
        'put_object_from_filelike': 'put_object_from_filelike',
        'put_object_from_file': 'put_object_from_file',
        'put_object_from_tree': 'put_object_from_tree',
        'walk': 'walk',
        'repository_metadata': 'metadata',
    }

    _deprecated_attr_methods = {
        'attributes': 'all',
        'get_attribute': 'get',
        'get_attribute_many': 'get_many',
        'set_attribute': 'set',
        'set_attribute_many': 'set_many',
        'reset_attributes': 'reset',
        'delete_attribute': 'delete',
        'delete_attribute_many': 'delete_many',
        'clear_attributes': 'clear',
        'attributes_items': 'items',
        'attributes_keys': 'keys',
    }

    _deprecated_extra_methods = {
        'extras': 'all',
        'get_extra': 'get',
        'get_extra_many': 'get_many',
        'set_extra': 'set',
        'set_extra_many': 'set_many',
        'reset_extras': 'reset',
        'delete_extra': 'delete',
        'delete_extra_many': 'delete_many',
        'clear_extras': 'clear',
        'extras_items': 'items',
        'extras_keys': 'keys',
    }

    _deprecated_comment_methods = {
        'add_comment': 'add',
        'get_comment': 'get',
        'get_comments': 'all',
        'remove_comment': 'remove',
        'update_comment': 'update',
    }

    _deprecated_caching_methods = {
        'get_hash': 'get_hash',
        '_get_hash': '_get_hash',
        '_get_objects_to_hash': '_get_objects_to_hash',
        'rehash': 'rehash',
        'clear_hash': 'clear_hash',
        'get_cache_source': 'get_cache_source',
        'is_created_from_cache': 'is_created_from_cache',
        '_get_same_node': '_get_same_node',
        'get_all_same_nodes': 'get_all_same_nodes',
        '_iter_all_same_nodes': '_iter_all_same_nodes',
    }

    _deprecated_links_methods = {
        'add_incoming': 'add_incoming',
        'validate_incoming': 'validate_incoming',
        'validate_outgoing': 'validate_outgoing',
        'get_stored_link_triples': 'get_stored_link_triples',
        'get_incoming': 'get_incoming',
        'get_outgoing': 'get_outgoing',
    }

    @classproperty
    def Collection(cls):  # pylint: disable=invalid-name,no-self-use
        """Return the collection type for this class.

        This used to be a class argument with the value ``NodeCollection``. The argument is deprecated and this property
        is here for backwards compatibility to print the deprecation warning.
        """
        warn_deprecation(
            'This attribute is deprecated, use `aiida.orm.nodes.node.NodeCollection` instead.', version=3, stacklevel=2
        )
        return NodeCollection

    def __getattr__(self, name: str) -> Any:
        """This method is called when an attribute is not found in the instance.

        It allows for the handling of deprecated mixin methods.
        """
        if name in self._deprecated_extra_methods:
            new_name = self._deprecated_extra_methods[name]
            kls = self.__class__.__name__
            warn_deprecation(
                f'`{kls}.{name}` is deprecated, use `{kls}.base.extras.{new_name}` instead.', version=3, stacklevel=3
            )
            return getattr(self.base.extras, new_name)

        if name in self._deprecated_attr_methods:
            new_name = self._deprecated_attr_methods[name]
            kls = self.__class__.__name__
            warn_deprecation(
                f'`{kls}.{name}` is deprecated, use `{kls}.base.attributes.{new_name}` instead.',
                version=3,
                stacklevel=3
            )
            return getattr(self.base.attributes, new_name)

        if name in self._deprecated_repo_methods:
            new_name = self._deprecated_repo_methods[name]
            kls = self.__class__.__name__
            warn_deprecation(
                f'`{kls}.{name}` is deprecated, use `{kls}.base.repository.{new_name}` instead.',
                version=3,
                stacklevel=3
            )
            return getattr(self.base.repository, new_name)

        if name in self._deprecated_comment_methods:
            new_name = self._deprecated_comment_methods[name]
            kls = self.__class__.__name__
            warn_deprecation(
                f'`{kls}.{name}` is deprecated, use `{kls}.base.comments.{new_name}` instead.', version=3, stacklevel=3
            )
            return getattr(self.base.comments, new_name)

        if name in self._deprecated_caching_methods:
            new_name = self._deprecated_caching_methods[name]
            kls = self.__class__.__name__
            warn_deprecation(
                f'`{kls}.{name}` is deprecated, use `{kls}.base.caching.{new_name}` instead.', version=3, stacklevel=3
            )
            return getattr(self.base.caching, new_name)

        if name in self._deprecated_links_methods:
            new_name = self._deprecated_links_methods[name]
            kls = self.__class__.__name__
            warn_deprecation(
                f'`{kls}.{name}` is deprecated, use `{kls}.base.links.{new_name}` instead.', version=3, stacklevel=3
            )
            return getattr(self.base.links, new_name)

        raise AttributeError(name)
