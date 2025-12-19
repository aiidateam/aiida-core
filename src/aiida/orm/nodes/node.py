###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Package for node ORM classes."""

from __future__ import annotations

import datetime
from copy import deepcopy
from functools import cached_property
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Dict,
    Generic,
    Iterator,
    List,
    NoReturn,
    Optional,
    Tuple,
    Type,
    TypeVar,
    cast,
)
from uuid import UUID

from typing_extensions import Self

from aiida.common import exceptions
from aiida.common.lang import classproperty, type_check
from aiida.common.links import LinkType
from aiida.common.log import AIIDA_LOGGER
from aiida.common.pydantic import MetadataField, OrmModel
from aiida.common.warnings import warn_deprecation
from aiida.manage import get_manager
from aiida.orm.utils.node import (
    AbstractNodeMeta,
    get_query_type_from_type_string,
    get_type_string_from_class,
)

from ..computers import Computer
from ..entities import Collection as EntityCollection
from ..entities import Entity, from_backend_entity
from ..extras import EntityExtras
from ..querybuilder import QueryBuilder
from ..users import User
from .attributes import NodeAttributes
from .caching import NodeCaching
from .comments import NodeComments
from .links import NodeLinks

if TYPE_CHECKING:
    from importlib_metadata import EntryPoint

    from aiida.common.log import AiidaLoggerType

    from ..implementation import StorageBackend
    from ..implementation.nodes import BackendNode
    from .repository import NodeRepository

__all__ = ('Node', 'NodeLinks')

NodeType = TypeVar('NodeType', bound='Node')


class NodeCollection(EntityCollection[NodeType], Generic[NodeType]):
    """The collection of nodes."""

    @staticmethod
    def _entity_base_cls() -> Type[Node]:  # type: ignore[override]
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

    def iter_repo_keys(
        self, filters: Optional[dict] = None, subclassing: bool = True, batch_size: int = 100
    ) -> Iterator[str]:
        """Iterate over all repository object keys for this ``Node`` class

        .. note:: keys will not be deduplicated, wrap in a ``set`` to achieve this

        :param filters: Filters for the node query
        :param subclassing: Whether to include subclasses of the given class
        :param batch_size: The number of nodes to fetch data for at once
        """
        from aiida.repository import Repository

        query = QueryBuilder(backend=self.backend)
        query.append(self.entity_type, subclassing=subclassing, filters=filters, project=['repository_metadata'])
        for (metadata,) in query.iterall(batch_size=batch_size):
            for key in Repository.flatten(metadata).values():
                if key is not None:
                    yield key


class NodeBase:
    """A namespace for node related functionality, that is not directly related to its user-facing properties."""

    def __init__(self, node: Node) -> None:
        """Construct a new instance of the base namespace."""
        self._node = node

    @cached_property
    def repository(self) -> NodeRepository:
        """Return the repository for this node."""
        from .repository import NodeRepository

        return NodeRepository(self._node)

    @cached_property
    def caching(self) -> NodeCaching:
        """Return an interface to interact with the caching of this node."""
        return self._node._CLS_NODE_CACHING(self._node)

    @cached_property
    def comments(self) -> NodeComments:
        """Return an interface to interact with the comments of this node."""
        return NodeComments(self._node)

    @cached_property
    def attributes(self) -> NodeAttributes:
        """Return an interface to interact with the attributes of this node."""
        return NodeAttributes(self._node)

    @cached_property
    def extras(self) -> EntityExtras:
        """Return an interface to interact with the extras of this node."""
        return EntityExtras(self._node)

    @cached_property
    def links(self) -> NodeLinks:
        """Return an interface to interact with the links of this node."""
        return self._node._CLS_NODE_LINKS(self._node)


class Node(Entity['BackendNode', NodeCollection['Node']], metaclass=AbstractNodeMeta):
    """Base class for all nodes in AiiDA.

    Stores attributes starting with an underscore.

    Caches files and attributes before the first save, and saves everything
    only on store(). After the call to store(), attributes cannot be changed.

    Only after storing (or upon loading from uuid) extras can be modified
    and in this case they are directly set on the db.

    In the plugin, also set the _plugin_type_string, to be set in the DB in
    the 'type' field.
    """

    _CLS_COLLECTION = NodeCollection['Node']
    _CLS_NODE_LINKS = NodeLinks
    _CLS_NODE_CACHING = NodeCaching

    __plugin_type_string: ClassVar[str]
    __query_type_string: ClassVar[str]

    @classproperty
    def _plugin_type_string(cls) -> str:  # noqa: N805
        """Return the plugin type string of this node class."""
        if not hasattr(cls, '__plugin_type_string'):
            cls.__plugin_type_string = get_type_string_from_class(cls.__module__, cls.__name__)  # type: ignore[misc]
        return cls.__plugin_type_string

    @classproperty
    def _query_type_string(cls) -> str:  # noqa: N805
        """Return the query type string of this node class."""
        if not hasattr(cls, '__query_type_string'):
            cls.__query_type_string = get_query_type_from_type_string(cls._plugin_type_string)  # type: ignore[misc]
        return cls.__query_type_string

    # This will be set by the metaclass call but we set default
    _logger: AiidaLoggerType = AIIDA_LOGGER

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

    class AttributesModel(OrmModel):
        """The node attributes."""

    class Model(Entity.Model):
        uuid: UUID = MetadataField(
            description='The UUID of the node',
            read_only=True,
        )
        node_type: str = MetadataField(
            description='The type of the node',
            read_only=True,
        )
        process_type: Optional[str] = MetadataField(
            None,
            description='The process type of the node',
            read_only=True,
        )
        repository_metadata: Dict[str, Any] = MetadataField(
            default_factory=dict,
            description='Virtual hierarchy of the file repository',
            orm_to_model=lambda node, _: cast(Node, node).base.repository.metadata,
            read_only=True,
            may_be_large=True,
        )
        ctime: datetime.datetime = MetadataField(
            description='The creation time of the node',
            read_only=True,
        )
        mtime: datetime.datetime = MetadataField(
            description='The modification time of the node',
            read_only=True,
        )
        label: str = MetadataField(
            '',
            description='The node label',
        )
        description: str = MetadataField(
            '',
            description='The node description',
        )
        attributes: Node.AttributesModel = MetadataField(
            description='The node attributes',
            orm_to_model=lambda node, _: cast(Node, node).base.attributes.all,
            may_be_large=True,
        )
        extras: Dict[str, Any] = MetadataField(
            default_factory=dict,
            description='The node extras',
            orm_to_model=lambda node, _: cast(Node, node).base.extras.all,
            may_be_large=True,
        )
        computer: Optional[str] = MetadataField(
            None,
            description='The label of the computer',
            orm_to_model=lambda node, _: cast(Node, node).get_computer_label_if_exists(),
            model_to_orm=lambda model: cast(Node.Model, model).load_computer(),
            read_only=True,
        )
        user: int = MetadataField(
            description='The PK of the user who owns the node',
            orm_to_model=lambda node, _: cast(Node, node).user.pk,
            orm_class=User,
            read_only=True,
        )

        def load_computer(self) -> Computer:
            """Load the computer instance.

            :return: The computer instance.
            :raises ValueError: If the computer does not exist.
            """
            from aiida.orm import load_computer

            try:
                return load_computer(self.computer)
            except exceptions.NotExistent as exception:
                raise ValueError(exception) from exception

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)

        Model = cast(type[Node.Model], getattr(cls, 'Model'))  # noqa N806
        Attrs = cast(type[Node.AttributesModel], getattr(cls, 'AttributesModel'))  # noqa N806

        if 'Model' not in cls.__dict__:
            parent_model = Model
            Model = cast(  # noqa N806
                type[Node.Model],
                type(
                    'Model',
                    (parent_model,),
                    {
                        '__module__': cls.__module__,
                        '__qualname__': f'{cls.__qualname__}.Model',
                    },
                ),
            )
            cls.Model = Model  # type: ignore[misc]

        base_field = Model.model_fields['attributes']
        new_field = deepcopy(base_field)
        new_field.annotation = Attrs
        Model.model_fields['attributes'] = new_field
        Model.model_rebuild(force=True)

    def __init__(
        self,
        backend: Optional['StorageBackend'] = None,
        user: Optional[User] = None,
        computer: Optional[Computer] = None,
        extras: Optional[Dict[str, Any]] = None,
        attributes: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
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

        if attributes is not None:
            self.base.attributes.set_many(attributes)

        if extras is not None:
            self.base.extras.set_many(extras)

    @cached_property
    def base(self) -> NodeBase:
        """Return the node base namespace."""
        return NodeBase(self)

    def _check_mutability_attributes(self, keys: Optional[List[str]] = None) -> None:
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
        return f'<{self.__class__.__name__}: {self!s}>'

    def __str__(self) -> str:
        if not self.is_stored:
            return f'uuid: {self.uuid} (unstored)'

        return f'uuid: {self.uuid} (pk: {self.pk})'

    def __copy__(self) -> NoReturn:
        """Copying a Node is not supported in general, but only for the Data sub class."""
        raise exceptions.InvalidOperation('copying a base Node is not supported')

    def __deepcopy__(self, memo: Any) -> NoReturn:
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
    def class_node_type(cls) -> str:  # noqa: N805
        """Returns the node type of this node (sub) class."""
        return cls._plugin_type_string

    @classproperty
    def entry_point(cls) -> Optional['EntryPoint']:  # noqa: N805
        """Return the entry point associated this node class.

        :return: the associated entry point or ``None`` if it isn't known.
        """
        from aiida.plugins.entry_point import get_entry_point_from_class

        return get_entry_point_from_class(cls.__module__, cls.__name__)[1]

    @property
    def logger(self) -> AiidaLoggerType:
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
            return from_backend_entity(Computer, self.backend_entity.computer)

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
        return from_backend_entity(User, self._backend_entity.user)

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

    def store_all(self) -> Self:
        """Store the node, together with all input links.

        Unstored nodes from cached incoming linkswill also be stored.
        """
        if self.is_stored:
            raise exceptions.ModificationNotAllowed(f'Node<{self.pk}> is already stored')

        # For each node of a cached incoming link, check that all its incoming links are stored
        for link_triple in self.base.links.incoming_cache:
            link_triple.node._verify_are_parents_stored()

        for link_triple in self.base.links.incoming_cache:
            if not link_triple.node.is_stored:
                link_triple.node.store()

        return self.store()

    def store(self) -> Self:
        """Store the node in the database while saving its attributes and repository directory.

        After being called attributes cannot be changed anymore! Instead, extras can be changed only AFTER calling
        this store() function.

        :note: After successful storage, those links that are in the cache, and for which also the parent node is
            already stored, will be automatically stored. The others will remain unstored.
        """
        if not self.is_stored:
            # Call `_validate_storability` directly and not in `_validate` in case sub class forgets to call the super.
            self._validate_storability()
            self._validate()

            # Verify that parents are already stored. Raises if this is not the case.
            self._verify_are_parents_stored()

            # Clean the values on the backend node *before* computing the hash in `_get_same_node`. This will allow
            # us to set `clean=False` if we are storing normally, since the values will already have been cleaned
            self._backend_entity.clean_values()

            # Retrieve the cached node if ``should_use_cache`` returns True
            same_node = self.base.caching._get_same_node() if self.base.caching.should_use_cache() else None

            if same_node is not None:
                self._store_from_cache(same_node)
            else:
                self._store(clean=True)

            if self.backend.autogroup.is_to_be_grouped(self):
                group = self.backend.autogroup.get_or_create_group()
                group.add_nodes(self)

        return self

    def _store(self, clean: bool = True) -> Self:
        """Store the node in the database while saving its attributes and repository directory.

        :param clean: boolean, if True, will clean the attributes and extras before attempting to store
        """
        self.base.repository._store()

        links = self.base.links.incoming_cache
        self._backend_entity.store(links, clean=clean)

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

    def _store_from_cache(self, cache_node: Node) -> None:
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
        self.base.repository._copy(cache_node.base.repository)

        for key, value in cache_node.base.attributes.all.items():
            if key != Sealable.SEALED_KEY:
                self.base.attributes.set(key, value)

        self._store(clean=False)
        self._add_outputs_from_cache(cache_node)
        self.base.extras.set(self.base.caching.CACHED_FROM_KEY, cache_node.uuid)

    def _add_outputs_from_cache(self, cache_node: Node) -> None:
        """Replicate the output links and nodes from the cached node onto this node."""
        for entry in cache_node.base.links.get_outgoing(link_type=LinkType.CREATE):
            new_node = entry.node.clone()
            new_node.base.links.add_incoming(self, link_type=LinkType.CREATE, link_label=entry.link_label)
            new_node.store()

    def get_description(self) -> str:
        """Return a string with a description of the node.

        :return: a description string
        """
        return ''

    def get_computer_label_if_exists(self) -> Optional[str]:
        """Get the label of the computer of this node.

        :return: The computer label or None if no computer is set.
        """
        return self.computer.label if self.computer else None

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
            stacklevel=2,
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
            stacklevel=2,
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
    def Collection(cls) -> type[NodeCollection]:  # noqa: N802, N805
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
                stacklevel=3,
            )
            return getattr(self.base.attributes, new_name)

        if name in self._deprecated_repo_methods:
            new_name = self._deprecated_repo_methods[name]
            kls = self.__class__.__name__
            warn_deprecation(
                f'`{kls}.{name}` is deprecated, use `{kls}.base.repository.{new_name}` instead.',
                version=3,
                stacklevel=3,
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
