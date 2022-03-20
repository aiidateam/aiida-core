# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=too-many-lines,too-many-arguments
"""Package for node ORM classes."""
import copy
import datetime
import importlib
from logging import Logger
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Dict,
    Generic,
    Iterator,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from uuid import UUID

from aiida.common import exceptions
from aiida.common.escaping import sql_string_match
from aiida.common.hashing import make_hash
from aiida.common.lang import classproperty, type_check
from aiida.common.links import LinkType
from aiida.manage import get_manager
from aiida.orm.utils.links import LinkManager, LinkTriple
from aiida.orm.utils.node import AbstractNodeMeta

from ..comments import Comment
from ..computers import Computer
from ..entities import Collection as EntityCollection
from ..entities import Entity, EntityAttributesMixin, EntityExtrasMixin
from ..querybuilder import QueryBuilder
from ..users import User
from .repository import NodeRepositoryMixin

if TYPE_CHECKING:
    from ..implementation import BackendNode, StorageBackend

__all__ = ('Node',)

NodeType = TypeVar('NodeType', bound='Node')


class NodeCollection(EntityCollection[NodeType], Generic[NodeType]):
    """The collection of nodes."""

    @staticmethod
    def _entity_base_cls() -> Type['Node']:
        return Node

    def delete(self, pk: int) -> None:
        """Delete a `Node` from the collection with the given id

        :param pk: the node id
        """
        node = self.get(id=pk)

        if not node.is_stored:
            return

        if node.get_incoming().all():
            raise exceptions.InvalidOperation(f'cannot delete Node<{node.pk}> because it has incoming links')

        if node.get_outgoing().all():
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


class Node(
    Entity['BackendNode'], NodeRepositoryMixin, EntityAttributesMixin, EntityExtrasMixin, metaclass=AbstractNodeMeta
):
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

    # The keys in the extras that are used to store the hash of the node and whether it should be used in caching.
    _HASH_EXTRA_KEY: str = '_aiida_hash'
    _VALID_CACHE_KEY: str = '_aiida_valid_cache'

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

    # These are to be initialized in the `initialization` method
    _incoming_cache: Optional[List[LinkTriple]] = None

    Collection = NodeCollection

    @classproperty
    def objects(cls: Type[NodeType]) -> NodeCollection[NodeType]:  # pylint: disable=no-self-argument
        return NodeCollection.get_cached(cls, get_manager().get_profile_storage())  # type: ignore[arg-type]

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

        computer = computer.backend_entity if computer else None
        user = user if user else User.objects(backend).get_default()

        if user is None:
            raise ValueError('the user cannot be None')

        backend_entity = backend.nodes.create(
            node_type=self.class_node_type, user=user.backend_entity, computer=computer, **kwargs
        )
        super().__init__(backend_entity)

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

    def initialize(self) -> None:
        """
        Initialize internal variables for the backend node

        This needs to be called explicitly in each specific subclass implementation of the init.
        """
        super().initialize()

        # A cache of incoming links represented as a list of LinkTriples instances
        self._incoming_cache = []

    def _validate(self) -> bool:
        """Validate information stored in Node object.

        For the :py:class:`~aiida.orm.Node` base class, this check is always valid.
        Subclasses can override this method to perform additional checks
        and should usually call ``super()._validate()`` first!

        This method is called automatically before storing the node in the DB.
        Therefore, use :py:meth:`~aiida.orm.entities.EntityAttributesMixin.get_attribute()` and similar methods that
        automatically read either from the DB or from the internal attribute cache.
        """
        # pylint: disable=no-self-use
        return True

    def validate_storability(self) -> None:
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
    def repository_metadata(self) -> Dict[str, Any]:
        """Return the node repository metadata.

        :return: the repository metadata
        """
        return self.backend_entity.repository_metadata

    @repository_metadata.setter
    def repository_metadata(self, value: Dict[str, Any]) -> None:
        """Set the repository metadata.

        :param value: the new value to set
        """
        self.backend_entity.repository_metadata = value

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

    def add_comment(self, content: str, user: Optional[User] = None) -> Comment:
        """Add a new comment.

        :param content: string with comment
        :param user: the user to associate with the comment, will use default if not supplied
        :return: the newly created comment
        """
        user = user or User.objects(self.backend).get_default()
        return Comment(node=self, user=user, content=content).store()

    def get_comment(self, identifier: int) -> Comment:
        """Return a comment corresponding to the given identifier.

        :param identifier: the comment pk
        :raise aiida.common.NotExistent: if the comment with the given id does not exist
        :raise aiida.common.MultipleObjectsError: if the id cannot be uniquely resolved to a comment
        :return: the comment
        """
        return Comment.objects(self.backend).get(dbnode_id=self.pk, id=identifier)

    def get_comments(self) -> List[Comment]:
        """Return a sorted list of comments for this node.

        :return: the list of comments, sorted by pk
        """
        return Comment.objects(self.backend).find(filters={'dbnode_id': self.pk}, order_by=[{'id': 'asc'}])

    def update_comment(self, identifier: int, content: str) -> None:
        """Update the content of an existing comment.

        :param identifier: the comment pk
        :param content: the new comment content
        :raise aiida.common.NotExistent: if the comment with the given id does not exist
        :raise aiida.common.MultipleObjectsError: if the id cannot be uniquely resolved to a comment
        """
        comment = Comment.objects(self.backend).get(dbnode_id=self.pk, id=identifier)
        comment.set_content(content)

    def remove_comment(self, identifier: int) -> None:  # pylint: disable=no-self-use
        """Delete an existing comment.

        :param identifier: the comment pk
        """
        Comment.objects(self.backend).delete(identifier)

    def add_incoming(self, source: 'Node', link_type: LinkType, link_label: str) -> None:
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

    def validate_incoming(self, source: 'Node', link_type: LinkType, link_label: str) -> None:
        """Validate adding a link of the given type from a given node to ourself.

        This function will first validate the types of the inputs, followed by the node and link types and validate
        whether in principle a link of that type between the nodes of these types is allowed.

        Subsequently, the validity of the "degree" of the proposed link is validated, which means validating the
        number of links of the given type from the given node type is allowed.

        :param source: the node from which the link is coming
        :param link_type: the link type
        :param link_label: the link label
        :raise TypeError: if `source` is not a Node instance or `link_type` is not a `LinkType` enum
        :raise ValueError: if the proposed link is invalid
        """
        from aiida.orm.utils.links import validate_link

        validate_link(source, self, link_type, link_label, backend=self.backend)

        # Check if the proposed link would introduce a cycle in the graph following ancestor/descendant rules
        if link_type in [LinkType.CREATE, LinkType.INPUT_CALC, LinkType.INPUT_WORK]:
            builder = QueryBuilder(backend=self.backend).append(
                Node, filters={'id': self.pk}, tag='parent').append(
                Node, filters={'id': source.pk}, tag='child', with_ancestors='parent')  # yapf:disable
            if builder.count() > 0:
                raise ValueError('the link you are attempting to create would generate a cycle in the graph')

    def validate_outgoing(self, target: 'Node', link_type: LinkType, link_label: str) -> None:  # pylint: disable=unused-argument,no-self-use
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
        type_check(link_type, LinkType, f'link_type should be a LinkType enum but got: {type(link_type)}')
        type_check(target, Node, f'target should be a `Node` instance but got: {type(target)}')

    def _add_incoming_cache(self, source: 'Node', link_type: LinkType, link_label: str) -> None:
        """Add an incoming link to the cache.

        .. note: the proposed link is not validated in this function, so this should not be called directly
            but it should only be called by `Node.add_incoming`.

        :param source: the node from which the link is coming
        :param link_type: the link type
        :param link_label: the link label
        :raise aiida.common.UniquenessError: if the given link triple already exists in the cache
        """
        assert self._incoming_cache is not None, 'incoming_cache not initialised'

        link_triple = LinkTriple(source, link_type, link_label)

        if link_triple in self._incoming_cache:
            raise exceptions.UniquenessError(f'the link triple {link_triple} is already present in the cache')

        self._incoming_cache.append(link_triple)

    def get_stored_link_triples(
        self,
        node_class: Type['Node'] = None,
        link_type: Union[LinkType, Sequence[LinkType]] = (),
        link_label_filter: Optional[str] = None,
        link_direction: str = 'incoming',
        only_uuid: bool = False
    ) -> List[LinkTriple]:
        """Return the list of stored link triples directly incoming to or outgoing of this node.

        Note this will only return link triples that are stored in the database. Anything in the cache is ignored.

        :param node_class: If specified, should be a class, and it filters only elements of that (subclass of) type
        :param link_type: Only get inputs of this link type, if empty tuple then returns all inputs of all link types.
        :param link_label_filter: filters the incoming nodes by its link label. This should be a regex statement as
            one would pass directly to a QueryBuilder filter statement with the 'like' operation.
        :param link_direction: `incoming` or `outgoing` to get the incoming or outgoing links, respectively.
        :param only_uuid: project only the node UUID instead of the instance onto the `NodeTriple.node` entries
        """
        if not isinstance(link_type, tuple):
            link_type = (link_type,)

        if link_type and not all(isinstance(t, LinkType) for t in link_type):
            raise TypeError(f'link_type should be a LinkType or tuple of LinkType: got {link_type}')

        node_class = node_class or Node
        node_filters: Dict[str, Any] = {'id': {'==': self.id}}
        edge_filters: Dict[str, Any] = {}

        if link_type:
            edge_filters['type'] = {'in': [t.value for t in link_type]}

        if link_label_filter:
            edge_filters['label'] = {'like': link_label_filter}

        builder = QueryBuilder(backend=self.backend)
        builder.append(Node, filters=node_filters, tag='main')

        node_project = ['uuid'] if only_uuid else ['*']
        if link_direction == 'outgoing':
            builder.append(
                node_class,
                with_incoming='main',
                project=node_project,
                edge_project=['type', 'label'],
                edge_filters=edge_filters
            )
        else:
            builder.append(
                node_class,
                with_outgoing='main',
                project=node_project,
                edge_project=['type', 'label'],
                edge_filters=edge_filters
            )

        return [LinkTriple(entry[0], LinkType(entry[1]), entry[2]) for entry in builder.all()]

    def get_incoming(
        self,
        node_class: Type['Node'] = None,
        link_type: Union[LinkType, Sequence[LinkType]] = (),
        link_label_filter: Optional[str] = None,
        only_uuid: bool = False
    ) -> LinkManager:
        """Return a list of link triples that are (directly) incoming into this node.

        :param node_class: If specified, should be a class or tuple of classes, and it filters only
            elements of that specific type (or a subclass of 'type')
        :param link_type: If specified should be a string or tuple to get the inputs of this
            link type, if None then returns all inputs of all link types.
        :param link_label_filter: filters the incoming nodes by its link label.
            Here wildcards (% and _) can be passed in link label filter as we are using "like" in QB.
        :param only_uuid: project only the node UUID instead of the instance onto the `NodeTriple.node` entries
        """
        assert self._incoming_cache is not None, 'incoming_cache not initialised'

        if not isinstance(link_type, tuple):
            link_type = (link_type,)

        if self.is_stored:
            link_triples = self.get_stored_link_triples(
                node_class, link_type, link_label_filter, 'incoming', only_uuid=only_uuid
            )
        else:
            link_triples = []

        # Get all cached link triples
        for link_triple in self._incoming_cache:

            if only_uuid:
                link_triple = LinkTriple(link_triple.node.uuid, link_triple.link_type, link_triple.link_label)

            if link_triple in link_triples:
                raise exceptions.InternalError(
                    f'Node<{self.pk}> has both a stored and cached link triple {link_triple}'
                )

            if not link_type or link_triple.link_type in link_type:
                if link_label_filter is not None:
                    if sql_string_match(string=link_triple.link_label, pattern=link_label_filter):
                        link_triples.append(link_triple)
                else:
                    link_triples.append(link_triple)

        return LinkManager(link_triples)

    def get_outgoing(
        self,
        node_class: Type['Node'] = None,
        link_type: Union[LinkType, Sequence[LinkType]] = (),
        link_label_filter: Optional[str] = None,
        only_uuid: bool = False
    ) -> LinkManager:
        """Return a list of link triples that are (directly) outgoing of this node.

        :param node_class: If specified, should be a class or tuple of classes, and it filters only
            elements of that specific type (or a subclass of 'type')
        :param link_type: If specified should be a string or tuple to get the inputs of this
            link type, if None then returns all outputs of all link types.
        :param link_label_filter: filters the outgoing nodes by its link label.
            Here wildcards (% and _) can be passed in link label filter as we are using "like" in QB.
        :param only_uuid: project only the node UUID instead of the instance onto the `NodeTriple.node` entries
        """
        link_triples = self.get_stored_link_triples(node_class, link_type, link_label_filter, 'outgoing', only_uuid)
        return LinkManager(link_triples)

    def has_cached_links(self) -> bool:
        """Feturn whether there are unstored incoming links in the cache.

        :return: boolean, True when there are links in the incoming cache, False otherwise
        """
        assert self._incoming_cache is not None, 'incoming_cache not initialised'
        return bool(self._incoming_cache)

    def store_all(self, with_transaction: bool = True) -> 'Node':
        """Store the node, together with all input links.

        Unstored nodes from cached incoming linkswill also be stored.

        :parameter with_transaction: if False, do not use a transaction because the caller will already have opened one.
        """
        assert self._incoming_cache is not None, 'incoming_cache not initialised'

        if self.is_stored:
            raise exceptions.ModificationNotAllowed(f'Node<{self.id}> is already stored')

        # For each node of a cached incoming link, check that all its incoming links are stored
        for link_triple in self._incoming_cache:
            link_triple.node.verify_are_parents_stored()

        for link_triple in self._incoming_cache:
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

            # Call `validate_storability` directly and not in `_validate` in case sub class forgets to call the super.
            self.validate_storability()
            self._validate()

            # Verify that parents are already stored. Raises if this is not the case.
            self.verify_are_parents_stored()

            # Determine whether the cache should be used for the process type of this node.
            use_cache = get_use_cache(identifier=self.process_type)

            # Clean the values on the backend node *before* computing the hash in `_get_same_node`. This will allow
            # us to set `clean=False` if we are storing normally, since the values will already have been cleaned
            self._backend_entity.clean_values()

            # Retrieve the cached node.
            same_node = self._get_same_node() if use_cache else None

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
        from aiida.repository import Repository
        from aiida.repository.backend import SandboxRepositoryBackend

        # Only if the backend repository is a sandbox do we have to clone its contents to the permanent repository.
        if isinstance(self._repository.backend, SandboxRepositoryBackend):
            repository_backend = self.backend.get_repository()
            repository = Repository(backend=repository_backend)
            repository.clone(self._repository)
            # Swap the sandbox repository for the new permanent repository instance which should delete the sandbox
            self._repository_instance = repository

        self.repository_metadata = self._repository.serialize()

        links = self._incoming_cache
        self._backend_entity.store(links, with_transaction=with_transaction, clean=clean)

        self._incoming_cache = []
        self._backend_entity.set_extra(self._HASH_EXTRA_KEY, self.get_hash())

        return self

    def verify_are_parents_stored(self) -> None:
        """Verify that all `parent` nodes are already stored.

        :raise aiida.common.ModificationNotAllowed: if one of the source nodes of incoming links is not stored.
        """
        assert self._incoming_cache is not None, 'incoming_cache not initialised'

        for link_triple in self._incoming_cache:
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
        from aiida.repository import Repository
        assert self.node_type == cache_node.node_type

        # Make sure the node doesn't have any RETURN links
        if cache_node.get_outgoing(link_type=LinkType.RETURN).all():
            raise ValueError('Cannot use cache from nodes with RETURN links.')

        self.label = cache_node.label
        self.description = cache_node.description

        # Make sure to reinitialize the repository instance of the clone to that of the source node.
        self._repository: Repository = copy.copy(cache_node._repository)  # pylint: disable=protected-access

        for key, value in cache_node.attributes.items():
            if key != Sealable.SEALED_KEY:
                self.set_attribute(key, value)

        self._store(with_transaction=with_transaction, clean=False)
        self._add_outputs_from_cache(cache_node)
        self.set_extra('_aiida_cached_from', cache_node.uuid)

    def _add_outputs_from_cache(self, cache_node: 'Node') -> None:
        """Replicate the output links and nodes from the cached node onto this node."""
        for entry in cache_node.get_outgoing(link_type=LinkType.CREATE):
            new_node = entry.node.clone()
            new_node.add_incoming(self, link_type=LinkType.CREATE, link_label=entry.link_label)
            new_node.store()

    def get_hash(self, ignore_errors: bool = True, **kwargs: Any) -> Optional[str]:
        """Return the hash for this node based on its attributes.

        :param ignore_errors: return ``None`` on ``aiida.common.exceptions.HashingError`` (logging the exception)
        """
        if not self.is_stored:
            raise exceptions.InvalidOperation('You can get the hash only after having stored the node')

        return self._get_hash(ignore_errors=ignore_errors, **kwargs)

    def _get_hash(self, ignore_errors: bool = True, **kwargs: Any) -> Optional[str]:
        """
        Return the hash for this node based on its attributes.

        This will always work, even before storing.

        :param ignore_errors: return ``None`` on ``aiida.common.exceptions.HashingError`` (logging the exception)
        """
        try:
            return make_hash(self._get_objects_to_hash(), **kwargs)
        except exceptions.HashingError:
            if not ignore_errors:
                raise
            if self.logger:
                self.logger.exception('Node hashing failed')
            return None

    def _get_objects_to_hash(self) -> List[Any]:
        """Return a list of objects which should be included in the hash."""
        assert self._repository is not None, 'repository not initialised'
        top_level_module = self.__module__.split('.', 1)[0]
        try:
            version = importlib.import_module(top_level_module).__version__
        except (ImportError, AttributeError) as exc:
            raise exceptions.HashingError("The node's package version could not be determined") from exc
        objects = [
            version,
            {
                key: val
                for key, val in self.attributes_items()
                if key not in self._hash_ignored_attributes and key not in self._updatable_attributes  # pylint: disable=unsupported-membership-test
            },
            self._repository.hash(),
            self.computer.uuid if self.computer is not None else None
        ]
        return objects

    def rehash(self) -> None:
        """Regenerate the stored hash of the Node."""
        self.set_extra(self._HASH_EXTRA_KEY, self.get_hash())

    def clear_hash(self) -> None:
        """Sets the stored hash of the Node to None."""
        self.set_extra(self._HASH_EXTRA_KEY, None)

    def get_cache_source(self) -> Optional[str]:
        """Return the UUID of the node that was used in creating this node from the cache, or None if it was not cached.

        :return: source node UUID or None
        """
        return self.get_extra('_aiida_cached_from', None)

    @property
    def is_created_from_cache(self) -> bool:
        """Return whether this node was created from a cached node.

        :return: boolean, True if the node was created by cloning a cached node, False otherwise
        """
        return self.get_cache_source() is not None

    def _get_same_node(self) -> Optional['Node']:
        """Returns a stored node from which the current Node can be cached or None if it does not exist

        If a node is returned it is a valid cache, meaning its `_aiida_hash` extra matches `self.get_hash()`.
        If there are multiple valid matches, the first one is returned.
        If no matches are found, `None` is returned.

        :return: a stored `Node` instance with the same hash as this code or None

        Note: this should be only called on stored nodes, or internally from .store() since it first calls
        clean_value() on the attributes to normalise them.
        """
        try:
            return next(self._iter_all_same_nodes(allow_before_store=True))
        except StopIteration:
            return None

    def get_all_same_nodes(self) -> List['Node']:
        """Return a list of stored nodes which match the type and hash of the current node.

        All returned nodes are valid caches, meaning their `_aiida_hash` extra matches `self.get_hash()`.

        Note: this can be called only after storing a Node (since at store time attributes will be cleaned with
        `clean_value` and the hash should become idempotent to the action of serialization/deserialization)
        """
        return list(self._iter_all_same_nodes())

    def _iter_all_same_nodes(self, allow_before_store=False) -> Iterator['Node']:
        """
        Returns an iterator of all same nodes.

        Note: this should be only called on stored nodes, or internally from .store() since it first calls
        clean_value() on the attributes to normalise them.
        """
        if not allow_before_store and not self.is_stored:
            raise exceptions.InvalidOperation('You can get the hash only after having stored the node')

        node_hash = self._get_hash()

        if not node_hash or not self._cachable:
            return iter(())

        builder = QueryBuilder(backend=self.backend)
        builder.append(self.__class__, filters={f'extras.{self._HASH_EXTRA_KEY}': node_hash}, subclassing=False)

        return (node for node in builder.all(flat=True) if node.is_valid_cache)  # type: ignore[misc,union-attr]

    @property
    def is_valid_cache(self) -> bool:
        """Hook to exclude certain ``Node`` classes from being considered a valid cache.

        The base class assumes that all node instances are valid to cache from, unless the ``_VALID_CACHE_KEY`` extra
        has been set to ``False`` explicitly. Subclasses can override this property with more specific logic, but should
        probably also consider the value returned by this base class.
        """
        return self.get_extra(self._VALID_CACHE_KEY, True)

    @is_valid_cache.setter
    def is_valid_cache(self, valid: bool) -> None:
        """Set whether this node instance is considered valid for caching or not.

        If a node instance has this property set to ``False``, it will never be used in the caching mechanism, unless
        the subclass overrides the ``is_valid_cache`` property and ignores it implementation completely.

        :param valid: whether the node is valid or invalid for use in caching.
        """
        type_check(valid, bool)
        self.set_extra(self._VALID_CACHE_KEY, valid)

    def get_description(self) -> str:
        """Return a string with a description of the node.

        :return: a description string
        """
        # pylint: disable=no-self-use
        return ''
