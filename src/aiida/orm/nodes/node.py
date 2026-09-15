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
import typing as t
from collections.abc import Iterator
from functools import cached_property
from uuid import UUID

import pydantic as pdt
from typing_extensions import Self

from aiida.common import exceptions
from aiida.common.lang import classproperty, type_check
from aiida.common.links import LinkType
from aiida.common.log import AIIDA_LOGGER
from aiida.manage import get_manager
from aiida.orm.computers import Computer
from aiida.orm.decorators import column
from aiida.orm.decorators.attributes import attributes_column
from aiida.orm.entities import Entity, EntityCollection, from_backend_entity
from aiida.orm.extras import EntityExtras
from aiida.orm.models.adapters import EntityPkAdapter, StrUuidAdapter
from aiida.orm.models.node import NodeModelsNamespace
from aiida.orm.nodes.attributes import NodeAttributes
from aiida.orm.nodes.caching import NodeCaching
from aiida.orm.nodes.comments import NodeComments
from aiida.orm.nodes.links import NodeLinks
from aiida.orm.querybuilder import QueryBuilder
from aiida.orm.users import User
from aiida.orm.utils.node import (
    AbstractNodeMeta,
    get_query_type_from_type_string,
    get_type_string_from_class,
)

if t.TYPE_CHECKING:
    from importlib_metadata import EntryPoint

    from aiida.common.log import AiidaLoggerType
    from aiida.orm.implementation import StorageBackend
    from aiida.orm.implementation.nodes import BackendNode
    from aiida.orm.nodes.repository import NodeRepository

__all__ = ('Node',)

_NodeT = t.TypeVar('_NodeT', bound='Node')


class NodeCollection(EntityCollection[_NodeT], t.Generic[_NodeT]):
    """The collection of nodes."""

    collection_type: t.ClassVar[str] = 'nodes'

    def get_one_by_id(self, identifier: object) -> _NodeT:
        """Get a single node by its identifier.

        :param identifier: the primary key or label of the node to get
        :return: the node instance
        """
        if isinstance(identifier, int):
            return self.get(pk=identifier)
        if isinstance(identifier, str):
            return self.get(label=identifier)
        raise TypeError('Identifier must be an int or str')

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
        self, filters: dict | None = None, subclassing: bool = True, batch_size: int = 100
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

    @staticmethod
    def _entity_base_cls() -> type[Node]:  # type: ignore[override]
        return Node


class NodeBase:
    """A namespace for node related functionality, that is not directly related to its user-facing properties."""

    def __init__(self, node: Node) -> None:
        """Construct a new instance of the base namespace."""
        self._node = node

    @cached_property
    def repository(self) -> NodeRepository:
        """Return the repository for this node."""
        from aiida.orm.nodes.repository import NodeRepository

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

    identity_field = 'uuid'

    models: NodeModelsNamespace[Self] = NodeModelsNamespace()

    _attributes_model_config: pdt.ConfigDict

    _CLS_COLLECTION = NodeCollection['Node']
    _CLS_NODE_LINKS = NodeLinks
    _CLS_NODE_CACHING = NodeCaching

    __plugin_type_string: t.ClassVar[str]
    __query_type_string: t.ClassVar[str]

    # This will be set by the metaclass call but we set default
    _logger: AiidaLoggerType = AIIDA_LOGGER

    # A tuple of attribute names that can be updated even after node is stored
    # Requires Sealable mixin, but needs empty tuple for base class
    _updatable_attributes: tuple[str, ...] = tuple()

    # A tuple of attribute names that will be ignored when creating the hash.
    _hash_ignored_attributes: tuple[str, ...] = tuple()

    # Flag that determines whether the class can be cached.
    _cachable = False

    # Flag that determines whether the class can be stored.
    _storable = False
    _unstorable_message = 'only Data, WorkflowNode, CalculationNode or their subclasses can be stored'

    def __init__(
        self,
        label: str = '',
        description: str = '',
        extras: dict | None = None,
        attributes: dict | None = None,
        computer: Computer | None = None,
        user: User | None = None,
        node_type: str | None = None,
        process_type: str | None = None,
        repository_metadata: dict | None = None,
        files: dict[str, t.Callable[[], t.BinaryIO | None]] | None = None,
        backend: StorageBackend | None = None,
        **attribute_kwargs,
    ) -> None:
        backend = backend or get_manager().get_profile_storage()

        if computer is not None and not computer.is_stored:
            raise ValueError('the computer is not stored')

        backend_computer = computer.backend_entity if computer else None
        user = user if user else backend.default_user

        if user is None:
            raise ValueError('the user cannot be None')

        if node_type is not None and node_type != self.class_node_type:
            raise ValueError(
                f'provided node_type `{node_type}` does not match the class node type `{self.class_node_type}`'
            )

        backend_entity = backend.nodes.create(
            label=label,
            description=description,
            node_type=self.class_node_type,
            process_type=process_type,
            user=user.backend_entity,
            computer=backend_computer,
        )

        super().__init__(backend_entity)

        attributes = attributes or {}

        overlap = attributes.keys() & attribute_kwargs.keys()
        if overlap:
            raise TypeError(f'attributes specified multiple times: {sorted(overlap)}')

        attributes.update(attribute_kwargs)
        self.base.attributes.set_many(attributes)

        if extras:
            self.base.extras.set_many(extras)

        self._validate_and_attach_files(files, repository_metadata)

    def __init_subclass__(cls, **kwargs: t.Any) -> None:
        super().__init_subclass__(**kwargs)

        if '__init__' in cls.__dict__:
            raise TypeError(
                f'{cls.__name__} cannot override Node.__init__. '
                'Define a named class method such as `from_*` for custom construction instead.'
            )

    def __eq__(self, other: t.Any) -> bool:
        """Fallback equality comparison by uuid (can be overwritten by specific types)"""
        if isinstance(other, Node) and self.uuid == other.uuid:
            return True
        return super().__eq__(other)

    def __hash__(self) -> int:
        """Python-Hash: Implementation that is compatible with __eq__"""
        return int(UUID(self.uuid))

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}: {self!s}>'

    def __str__(self) -> str:
        if not self.is_stored:
            return f'uuid: {self.uuid} (unstored)'

        return f'uuid: {self.uuid} (pk: {self.pk})'

    def __copy__(self) -> t.NoReturn:
        """Copying a Node is not supported in general, but only for the Data sub class."""
        raise exceptions.InvalidOperation('copying a base Node is not supported')

    def __deepcopy__(self, memo: t.Any) -> t.NoReturn:
        """Deep copying a Node is not supported in general, but only for the Data sub class."""
        raise exceptions.InvalidOperation('deep copying a base Node is not supported')

    @column(
        updatable=True,
        model_field_info=pdt.fields.FieldInfo(default=''),
    )
    def label(self) -> str:
        """The label of the node."""
        return self._backend_entity.label

    @label.setter
    def label(self, value: str) -> None:
        self._backend_entity.label = value

    @column(
        updatable=True,
        model_field_info=pdt.fields.FieldInfo(default=''),
    )
    def description(self) -> str:
        """The description of the node."""
        return self._backend_entity.description

    @description.setter
    def description(self, value: str) -> None:
        self._backend_entity.description = value

    @column(
        updatable=True,
        may_be_large=True,
        model_field_info=pdt.fields.FieldInfo(default_factory=dict),
        cli_exclude=True,
    )
    def extras(self) -> dict[str, t.Any]:
        """The extras of the node."""
        return self.base.extras.all

    @extras.setter
    def extras(self, value: dict[str, t.Any]) -> None:
        self.base.extras.reset(value)

    @attributes_column
    def attributes(self) -> dict[str, t.Any]:
        """The attributes of the node."""
        return self.base.attributes.all

    @attributes.setter
    def attributes(self, value: dict[str, t.Any]) -> None:
        self.base.attributes.reset(value)

    @column(
        may_be_large=True,
        model_field_info=pdt.fields.FieldInfo(default_factory=dict),
        cli_exclude=True,
    )
    def repository_metadata(self) -> dict[str, t.Any]:
        """The repository metadata of the node."""
        return self.base.repository.metadata

    @column(
        readonly=True,
        model_adapter=StrUuidAdapter(),
    )
    def uuid(self) -> str:
        """The UUID of the node."""
        return self._backend_entity.uuid

    @column(
        required_once_stored=True,
        cli_exclude=True,
    )
    def node_type(self) -> str | None:
        """The type of the node."""
        return self._backend_entity.node_type

    @node_type.setter
    def node_type(self, value: str | None) -> None:
        self._backend_entity.node_type = value

    @column(cli_exclude=True)
    def process_type(self) -> str | None:
        """The process type of the node."""
        return self._backend_entity.process_type

    @process_type.setter
    def process_type(self, value: str) -> None:
        """Set the node process type."""
        self._backend_entity.process_type = value

    @column(readonly=True)
    def ctime(self) -> datetime.datetime:
        """The creation time of the node."""
        return self._backend_entity.ctime

    @column(readonly=True)
    def mtime(self) -> datetime.datetime:
        """The last modification time of the node."""
        return self._backend_entity.mtime

    @column(
        model_field_info=pdt.fields.FieldInfo(
            default=None,
            description='The PK of the associated computer.',
        ),
        model_adapter=EntityPkAdapter(Computer),
    )
    def computer(self) -> Computer | None:
        """The computer associated with the node."""
        if self.backend_entity.computer:
            return from_backend_entity(Computer, self.backend_entity.computer)

        return None

    @computer.setter
    def computer(self, computer: Computer | None) -> None:
        if self.is_stored:
            raise exceptions.ModificationNotAllowed('cannot set the computer on a stored node')

        type_check(computer, Computer, allow_none=True)
        self.backend_entity.computer = None if computer is None else computer.backend_entity

    @column(
        readonly=True,
        model_field_info=pdt.fields.FieldInfo(description='The PK of the associated user.'),
        model_adapter=EntityPkAdapter(User),
    )
    def user(self) -> User:
        """The user associated with the node."""
        return from_backend_entity(User, self._backend_entity.user)

    @cached_property
    def base(self) -> NodeBase:
        """Return the node base namespace."""
        return NodeBase(self)

    @property
    def logger(self) -> AiidaLoggerType:
        """Return the logger configured for this Node."""
        return self._logger

    @classproperty
    def class_node_type(cls: type[Node]) -> str:  # noqa: N805
        """Returns the node type of this node (sub) class."""
        return cls._plugin_type_string

    @classproperty
    def entry_point(cls: type[Node]) -> EntryPoint | None:  # noqa: N805
        """Return the entry point associated this node class."""
        from aiida.plugins.entry_point import get_entry_point_from_class

        return get_entry_point_from_class(cls.__module__, cls.__name__)[1]

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

    def attach_file(self, filepath: str, fileobj: t.BinaryIO) -> None:
        """Attach a file to the repository of this node.

        Subclasses of `Node` may override this method, providing custom file handling that includes validation
        and/or attribute derivation, e.g., `ArrayData.set_array`, `SinglefileData.set_file`, etc.

        :param filepath: the path within the repository to store the file at
        :param fileobj: the file-like object to store
        """
        self.base.repository.put_object_from_filelike(fileobj, filepath)  # type: ignore[arg-type]

    @classproperty
    def _plugin_type_string(cls: type[Node]) -> str:  # noqa: N805
        """Return the plugin type string of this node class."""
        if not hasattr(cls, '__plugin_type_string'):
            cls.__plugin_type_string = get_type_string_from_class(cls.__module__, cls.__name__)
        return cls.__plugin_type_string

    @classproperty
    def _query_type_string(cls: type[Node]) -> str:  # noqa: N805
        """Return the query type string of this node class."""
        if not hasattr(cls, '__query_type_string'):
            cls.__query_type_string = get_query_type_from_type_string(cls._plugin_type_string)
        return cls.__query_type_string

    def _validate_and_attach_files(
        self,
        files: dict[str, t.Callable[[], t.BinaryIO | None]] | None = None,
        repository_metadata: dict | None = None,
    ) -> None:
        """Attach repository files, optionally validated against expected repository metadata."""
        if repository_metadata:
            import hashlib

            from aiida.common.hashing import chunked_file_hash
            from aiida.repository import Repository

            if not files:
                raise exceptions.ValidationError('got `repository_metadata` but no files provided')

            flattened_repo = Repository.flatten(repository_metadata)

        for filepath, fileobj_callable in (files or {}).items():
            fileobj = fileobj_callable()
            if fileobj is None:
                self.base.repository._repository.create_directory(filepath)  # empty directory
            else:
                if repository_metadata:
                    expected_hash = flattened_repo.get(filepath)
                    if expected_hash:
                        actual_hash = chunked_file_hash(fileobj, hashlib.sha256)
                        fileobj.seek(0)
                        if expected_hash != actual_hash:
                            raise exceptions.ValidationError(
                                f'file hash mismatch for `{filepath}`; expected {expected_hash}, computed {actual_hash}'
                            )
                self.attach_file(filepath, fileobj)
                fileobj.close()

    def _check_mutability_attributes(self, keys: list[str] | None = None) -> None:
        """Check if the entity is mutable and raise an exception if not.

        This is called from `NodeAttributes` methods that modify the attributes.

        :param keys: the keys that will be mutated, or all if None
        """
        if self.is_stored:
            raise exceptions.ModificationNotAllowed('the attributes of a stored entity are immutable')

    def _validate(self) -> None:
        """Validate information stored in Node object.

        For the :py:class:`~aiida.orm.Node` base class, this check is always valid.
        Subclasses can override this method to perform additional checks
        and should usually call ``super()._validate()`` first!

        This method is called automatically before storing the node in the DB.
        Therefore, use :py:meth:`~aiida.orm.nodes.attributes.NodeAttributes.get()` and similar methods that
        automatically read either from the DB or from the internal attribute cache.
        """
        return None

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
            # TODO Node has no clone method, but Data does. Are we only expecting Data here?
            new_node = entry.node.clone()  # type: ignore[attr-defined]
            new_node.base.links.add_incoming(self, link_type=LinkType.CREATE, link_label=entry.link_label)
            new_node.store()
