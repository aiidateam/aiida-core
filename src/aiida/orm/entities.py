###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for all common top level AiiDA entity classes and methods"""

from __future__ import annotations

import abc
import pathlib
from enum import Enum
from functools import lru_cache
from typing import TYPE_CHECKING, Any, ClassVar, Generic, List, Literal, NoReturn, Optional, Type, TypeVar, Union

from plumpy.base.utils import call_with_super_check, super_check
from typing_extensions import Self

from aiida.common import exceptions, log
from aiida.common.exceptions import EntryPointError, InvalidOperation, NotExistent
from aiida.common.lang import classproperty, type_check
from aiida.common.pydantic import MetadataField, OrmModel, get_metadata
from aiida.common.warnings import warn_deprecation
from aiida.manage import get_manager

from .fields import EntityFieldMeta

if TYPE_CHECKING:
    from aiida.orm.implementation import BackendEntity, StorageBackend
    from aiida.orm.querybuilder import FilterType, OrderByType, QueryBuilder

__all__ = ('Collection', 'Entity', 'EntityTypes')

CollectionType = TypeVar('CollectionType', bound='Collection[Any]')
EntityType = TypeVar('EntityType', bound='Entity[Any,Any]')
BackendEntityType = TypeVar('BackendEntityType', bound='BackendEntity')


class EntityTypes(Enum):
    """Enum for referring to ORM entities in a backend-agnostic manner."""

    AUTHINFO = 'authinfo'
    COMMENT = 'comment'
    COMPUTER = 'computer'
    GROUP = 'group'
    LOG = 'log'
    NODE = 'node'
    USER = 'user'
    LINK = 'link'
    GROUP_NODE = 'group_node'


class Collection(abc.ABC, Generic[EntityType]):
    """Container class that represents the collection of objects of a particular entity type."""

    collection_type: ClassVar[str] = 'entities'

    @staticmethod
    @abc.abstractmethod
    def _entity_base_cls() -> Type[EntityType]:
        """The allowed entity class or subclasses thereof."""

    @classmethod
    @lru_cache(maxsize=100)
    def get_cached(cls, entity_class: Type[EntityType], backend: 'StorageBackend') -> Self:
        """Get the cached collection instance for the given entity class and backend.

        :param backend: the backend instance to get the collection for
        """
        from aiida.orm.implementation import StorageBackend

        type_check(backend, StorageBackend)
        return cls(entity_class, backend=backend)

    def __init__(self, entity_class: Type[EntityType], backend: Optional['StorageBackend'] = None) -> None:
        """Construct a new entity collection.

        :param entity_class: the entity type e.g. User, Computer, etc
        :param backend: the backend instance to get the collection for, or use the default
        """
        from aiida.orm.implementation import StorageBackend

        type_check(backend, StorageBackend, allow_none=True)
        assert issubclass(entity_class, self._entity_base_cls())
        self._backend = backend or get_manager().get_profile_storage()
        self._entity_type = entity_class

    def __call__(self, backend: StorageBackend) -> Self:
        """Get or create a cached collection using a new backend."""
        if backend is self._backend:
            return self
        return self.get_cached(self.entity_type, backend=backend)

    @property
    def entity_type(self) -> Type[EntityType]:
        """The entity type for this instance."""
        return self._entity_type

    @property
    def backend(self) -> 'StorageBackend':
        """Return the backend."""
        return self._backend

    def query(
        self,
        filters: Optional['FilterType'] = None,
        order_by: Optional['OrderByType'] = None,
        project: Optional[Union[list[str], str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        subclassing: bool = True,
    ) -> 'QueryBuilder':
        """Get a query builder for the objects of this collection.

        :param filters: the keyword value pair filters to match
        :param order_by: a list of (key, direction) pairs specifying the sort order
        :param project: Optional projections.
        :param limit: the maximum number of results to return
        :param offset: number of initial results to be skipped
        :param subclassing: whether to match subclasses of the type as well.
        """
        from . import querybuilder

        filters = filters or {}
        order_by = {self.entity_type: order_by} if order_by else {}

        query = querybuilder.QueryBuilder(backend=self._backend, limit=limit, offset=offset)
        query.append(self.entity_type, project=project, filters=filters, subclassing=subclassing)
        query.order_by([order_by])
        return query

    def get(self, **filters: Any) -> EntityType:
        """Get a single collection entry that matches the filter criteria.

        :param filters: the filters identifying the object to get

        :return: the entry
        """
        res = self.query(filters=filters)
        return res.one()[0]

    def find(
        self,
        filters: Optional['FilterType'] = None,
        order_by: Optional['OrderByType'] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[EntityType]:
        """Find collection entries matching the filter criteria.

        :param filters: the keyword value pair filters to match
        :param order_by: a list of (key, direction) pairs specifying the sort order
        :param limit: the maximum number of results to return
        :param offset: number of initial results to be skipped

        :return: a list of resulting matches
        """
        query = self.query(filters=filters, order_by=order_by, limit=limit, offset=offset)
        return query.all(flat=True)

    def all(self) -> List[EntityType]:
        """Get all entities in this collection.

        :return: A list of all entities
        """
        return self.query().all(flat=True)

    def count(self, filters: Optional['FilterType'] = None) -> int:
        """Count entities in this collection according to criteria.

        :param filters: the keyword value pair filters to match

        :return: The number of entities found using the supplied criteria
        """
        return self.query(filters=filters).count()


class Entity(abc.ABC, Generic[BackendEntityType, CollectionType], metaclass=EntityFieldMeta):
    """An AiiDA entity"""

    _CLS_COLLECTION: Type[CollectionType] = Collection  # type: ignore[assignment]
    _logger = log.AIIDA_LOGGER.getChild('orm.entities')

    identity_field: ClassVar[str] = 'pk'

    class Model(OrmModel):
        pk: int = MetadataField(
            description='The primary key of the entity',
            read_only=True,
            examples=[42],
        )

    @classproperty
    def CreateModel(cls) -> Type[OrmModel]:  # noqa: N802, N805
        """Return the creation version of the model class for this entity.

        :return: The creation model class, with read-only fields removed.
        """
        return cls.Model._as_create_model()

    @classmethod
    def model_to_orm_field_values(cls, valid_model: OrmModel) -> dict[str, Any]:
        """Collect values for the ORM entity's fields from the given model instance.

        This method centralizes the mapping of Model -> ORM values, including handling of
        `orm_class` metadata and nested models. The process is recursive, applying metadata
        field rules to nested models as well.

        :param valid_model: An validated instance of the entity's model class.
        :return: Mapping of model field name to validated value.
        :raises EntryPointError: if an `orm_class` entry point could not be loaded.
        :raises NotExistent: if a referenced ORM entity could not be found.
        """
        from aiida.plugins.factories import BaseFactory

        def get_orm_field_values(model: OrmModel, schema: type[OrmModel] = cls.CreateModel) -> dict[str, Any]:
            """Recursive helper function to collect field values from a model instance.

            :param model: The model instance to extract field values from.
            :param schema: The model class.
            :return: Mapping of model field name to validated value.
            """

            fields: dict[str, Any] = {}
            for key, field in schema.model_fields.items():
                field_value = getattr(model, key, field.default)

                if field_value is None:
                    continue

                annotation = field.annotation
                if isinstance(annotation, type) and issubclass(annotation, OrmModel):
                    fields[key] = get_orm_field_values(field_value, annotation)
                elif orm_class := get_metadata(field, 'orm_class'):
                    if isinstance(orm_class, str):
                        try:
                            orm_class = BaseFactory('aiida.orm', orm_class)
                        except EntryPointError as exception:
                            raise EntryPointError(
                                f'The `orm_class` of `{cls.__name__}.Model.{key} is invalid: {exception}'
                            ) from exception
                    try:
                        fields[key] = orm_class.collection.get(id=field_value)
                    except NotExistent as exception:
                        raise NotExistent(f'No `{orm_class}` found with pk={field_value}') from exception
                elif model_to_orm := get_metadata(field, 'model_to_orm'):
                    fields[key] = model_to_orm(model)
                else:
                    fields[key] = field_value

            return fields

        return get_orm_field_values(valid_model)

    def orm_to_model_field_values(
        self,
        *,
        repository_path: Optional[pathlib.Path] = None,
        model: type[OrmModel] | None = None,
        minimal: bool = False,
    ) -> dict[str, Any]:
        """Collect values for the ``Model``'s fields from this entity.

        Centralizes mapping of ORM -> Model values, including handling of ``orm_to_model``
        functions and optional filtering based on field metadata (e.g., excluding CLI-only fields).
        The process is recursive, applying metadata field rules to nested models as well.

        :param repository_path: Optional path to use for repository-based fields.
        :param minimal: Whether to exclude potentially large value fields.
        :return: Mapping of ORM field name to value.
        """

        def get_model_field_values(model_cls: Type[OrmModel]) -> dict[str, Any]:
            """Recursive helper function to collect field values for a model class.

            :param model_cls: The model class to extract field values for.
            :return: Mapping of ORM field name to value.
            """
            fields: dict[str, Any] = {}

            for key, field in model_cls.model_fields.items():
                if get_metadata(field, 'may_be_large') and minimal:
                    continue

                annotation = field.annotation
                if isinstance(annotation, type) and issubclass(annotation, OrmModel):
                    fields[key] = get_model_field_values(annotation)
                    continue

                if orm_to_model := get_metadata(field, 'orm_to_model'):
                    kwargs = {'repository_path': repository_path}
                    fields[key] = orm_to_model(self, kwargs)
                else:
                    fields[key] = getattr(self, key, field.default)

            return fields

        return get_model_field_values(model or self.Model)

    def to_model(self, *, repository_path: Optional[pathlib.Path] = None, minimal: bool = False) -> OrmModel:
        """Return the entity instance as an instance of its model.

        :param repository_path: If the orm node has files in the repository, this path is used to read the repository
            files from. If no path is specified a temporary path is created using the entities pk.
            This field can be very large, so it is excluded by default.
        :param minimal: Whether to exclude potentially large value fields.
        :return: An instance of the entity's model class.
        """
        fields = self.orm_to_model_field_values(repository_path=repository_path, minimal=minimal)
        Model = self.Model if self.is_stored else self.CreateModel  # noqa: N806
        return Model(**fields)

    @classmethod
    def from_model(cls, model: OrmModel) -> Self:
        """Return an entity instance from an instance of its model.

        :param model: An instance of the entity's model class.
        :return: An instance of the entity class.
        """
        fields = cls.model_to_orm_field_values(model)
        return cls(**fields)

    def serialize(
        self,
        *,
        repository_path: Optional[pathlib.Path] = None,
        minimal: bool = False,
        mode: Literal['json', 'python'] = 'json',
    ) -> dict[str, Any]:
        """Serialize the entity instance to JSON.

        :param repository_path: If the orm node has files in the repository, this path is used to dump the repository
            files to. If no path is specified a temporary path is created using the entities pk.
        :param minimal: Whether to exclude potentially large value fields.
        :param mode: The serialization mode, either 'json' or 'python'. The 'json' mode is the most strict and ensures
            that the output is JSON serializable, whereas the 'python' mode allows for more complex Python types, such
            as `datetime` objects.
        :return: A dictionary that can be serialized to JSON.
        """
        if repository_path is None:
            import tempfile

            repository_path = pathlib.Path(tempfile.mkdtemp()) / f'./aiida_serialization/{self.pk}/'
            repository_path.mkdir(parents=True)
        else:
            if not repository_path.exists():
                raise ValueError(f'The repository_path `{repository_path}` does not exist.')
            if not repository_path.is_dir():
                raise ValueError(f'The repository_path `{repository_path}` is not a directory.')

        return self.to_model(
            repository_path=repository_path,
            minimal=minimal,
        ).model_dump(
            mode=mode,
            exclude_none=True,
            exclude_unset=minimal,
        )

    @classmethod
    def from_serialized(cls, serialized: dict[str, Any]) -> Self:
        """Construct an entity instance from JSON serialized data.

        :param serialized: A dictionary representing the serialized entity.
        :return: An instance of the entity class.
        """
        return cls.from_model(cls.CreateModel(**serialized))

    @classproperty
    def objects(cls) -> CollectionType:  # noqa: N805
        """Get a collection for objects of this type, with the default backend.

        .. deprecated:: This will be removed in v3, use ``collection`` instead.

        :return: an object that can be used to access entities of this type
        """
        warn_deprecation('`objects` property is deprecated, use `collection` instead.', version=3, stacklevel=4)
        return cls.collection

    @classproperty
    def collection(cls) -> CollectionType:  # noqa: N805
        """Get a collection for objects of this type, with the default backend.

        :return: an object that can be used to access entities of this type
        """
        return cls._CLS_COLLECTION.get_cached(cls, get_manager().get_profile_storage())

    @classmethod
    def get_collection(cls, backend: 'StorageBackend') -> CollectionType:
        """Get a collection for objects of this type for a given backend.

        .. note:: Use the ``collection`` class property instead if the currently loaded backend or backend of the
            default profile should be used.

        :param backend: The backend of the collection to use.
        :return: A collection object that can be used to access entities of this type.
        """
        return cls._CLS_COLLECTION.get_cached(cls, backend)

    @classmethod
    def get(cls, **kwargs: Any) -> Self:
        """Get an entity of the collection matching the given filters.

        .. deprecated: Will be removed in v3, use `Entity.collection.get` instead.

        """
        warn_deprecation(
            f'`{cls.__name__}.get` method is deprecated, use `{cls.__name__}.collection.get` instead.',
            version=3,
            stacklevel=2,
        )
        return cls.collection.get(**kwargs)

    def __init__(self, backend_entity: BackendEntityType) -> None:
        """:param backend_entity: the backend model supporting this entity"""
        self._backend_entity = backend_entity
        call_with_super_check(self.initialize)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False

        if hasattr(self, 'uuid'):
            return self.uuid == other.uuid  # type: ignore[attr-defined]

        return super().__eq__(other)

    def __getstate__(self) -> NoReturn:
        """Prevent an ORM entity instance from being pickled."""
        raise InvalidOperation('pickling of AiiDA ORM instances is not supported.')

    @super_check
    def initialize(self) -> None:
        """Initialize instance attributes.

        This will be called after the constructor is called or an entity is created from an existing backend entity.
        """

    @property
    def logger(self) -> log.AiidaLoggerType:
        """Return the internal logger."""
        try:
            return self._logger
        except AttributeError:
            raise exceptions.InternalError('No self._logger configured for {}!')

    @property
    def id(self) -> int | None:
        """Return the id for this entity.

        This identifier is guaranteed to be unique amongst entities of the same type for a single backend instance.

        .. deprecated: Will be removed in v3, use `pk` instead.

        :return: the entity's id
        """
        warn_deprecation('`id` property is deprecated, use `pk` instead.', version=3, stacklevel=2)
        return self._backend_entity.id

    @property
    def pk(self) -> int | None:
        """Return the primary key for this entity.

        This identifier is guaranteed to be unique amongst entities of the same type for a single backend instance.

        :return: the entity's principal key
        """
        return self._backend_entity.id

    def store(self) -> Self:
        """Store the entity."""
        self._backend_entity.store()
        return self

    @property
    def is_stored(self) -> bool:
        """Return whether the entity is stored."""
        return self._backend_entity.is_stored

    @property
    def backend(self) -> 'StorageBackend':
        """Get the backend for this entity"""
        return self._backend_entity.backend

    @property
    def backend_entity(self) -> BackendEntityType:
        """Get the implementing class for this object"""
        return self._backend_entity


def from_backend_entity(cls: Type[EntityType], backend_entity: BackendEntity) -> EntityType:
    """Construct an entity from a backend entity instance

    :param backend_entity: the backend entity

    :return: an AiiDA entity instance
    """
    from .implementation.entities import BackendEntity

    type_check(backend_entity, BackendEntity)
    entity = cls.__new__(cls)
    entity._backend_entity = backend_entity
    call_with_super_check(entity.initialize)
    return entity
