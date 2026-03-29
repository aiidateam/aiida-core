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
import inspect
from copy import deepcopy
from enum import Enum
from functools import lru_cache
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Generic,
    List,
    Literal,
    NoReturn,
    Optional,
    Type,
    TypeVar,
    Union,
)

import pydantic as pdt
from plumpy.base.utils import call_with_super_check, super_check
from typing_extensions import Self

from aiida.common import exceptions, log
from aiida.common.exceptions import InvalidOperation
from aiida.common.lang import classproperty, type_check
from aiida.common.pydantic import get_metadata
from aiida.common.warnings import warn_deprecation
from aiida.manage import get_manager

from .fields import QbFields, add_field
from .pydantic import OrmFieldsAsModelDump, OrmMetadataField, OrmModel

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


class Entity(abc.ABC, Generic[BackendEntityType, CollectionType]):
    """An AiiDA entity"""

    _CLS_COLLECTION: Type[CollectionType] = Collection  # type: ignore[assignment]
    _logger = log.AIIDA_LOGGER.getChild('orm.entities')

    identity_field = 'pk'

    fields: ClassVar[QbFields]

    class ReadModel(OrmModel):
        """The absolute schema of the entity."""

        pk: int = OrmMetadataField(
            description='The primary key of the entity',
            read_only=True,
            examples=[42],
        )

    class WriteModel(OrmModel):
        """The write schema of this entity, derived from the absolute schema."""

    _MODEL_MAP: ClassVar[dict[str, type[OrmModel]]]

    def __init__(self, backend_entity: BackendEntityType) -> None:
        """:param backend_entity: the backend model supporting this entity"""
        self._backend_entity = backend_entity
        call_with_super_check(self.initialize)

    def __init_subclass__(cls, **kwargs: Any) -> None:
        cls._patch_write_model()
        cls._patch_qb_fields()
        super().__init_subclass__(**kwargs)
        cls._MODEL_MAP = {
            'read': cls.ReadModel,
            'write': cls.WriteModel,
        }

    def to_model(
        self,
        *,
        context: dict[str, Any] | None = None,
        minimal: bool = False,
        schema: Literal['read', 'write'] | None = None,
    ) -> OrmModel:
        """Return the entity instance as an instance of its model.

        :param context: Optional context dictionary to pass to `orm_to_model` callables.
        :param minimal: Whether to exclude potentially large value fields.
        :param schema: The schema to use for the instance. Defaults to 'read' if stored, 'write' otherwise.
        :return: An instance of the entity's model class.
        :raises UnsupportedSchemaError: if the provided schema is not supported for this entity.
        """
        schema = schema or ('read' if self.is_stored else 'write')
        if schema not in self._MODEL_MAP:
            raise exceptions.UnsupportedSchemaError(f"expected one of {list(self._MODEL_MAP)} schemas, got '{schema}'")
        if schema == 'read' and not self.is_stored:
            raise exceptions.UnsupportedSchemaError("cannot use 'read' schema for an unstored entity")
        Model = self._MODEL_MAP[schema]  # noqa: N806
        fields = self._to_model_field_values(context=context, minimal=minimal, schema=Model)
        if minimal:
            Model = Model._as_minimal_model()  # noqa: N806
        return Model(**fields)

    @classmethod
    def from_model(cls, model: OrmModel) -> Self:
        """Return an entity instance from an instance of its model.

        :param model: An instance of the entity's model class.
        :return: An instance of the entity class.
        """
        fields = model._to_orm_field_values()
        return cls(**fields)

    def serialize(
        self,
        *,
        context: dict[str, Any] | None = None,
        minimal: bool = False,
        schema: Literal['read', 'write'] | None = None,
        mode: Literal['json', 'python'] = 'python',
    ) -> dict[str, Any]:
        """Serialize the entity instance to JSON.

        :param context: Optional context dictionary to pass to `orm_to_model` callables.
        :param minimal: Whether to exclude potentially large value fields.
        :param schema: The schema to use for serialization. Defaults to 'read' if stored, 'write' otherwise.
        :param mode: The serialization mode, either 'json' or 'python' (default). JSON-based clients (e.g., REST APIs)
            should use 'json' mode.
        :return: A dictionary that can be serialized to JSON.
        :raises UnsupportedSchemaError: if the provided schema is not supported for this entity.
        """
        return self.to_model(context=context, minimal=minimal, schema=schema).model_dump(
            mode=mode,
            exclude_none=True,
            exclude_unset=minimal,
        )

    @classmethod
    def from_serialized(cls, serialized: dict[str, Any]) -> Self:
        """Construct an entity instance from JSON serialized data.

        :param serialized: The serialized data.
        :return: The constructed entity instance.
        """
        return cls.from_model(cls.WriteModel(**serialized))

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

    @classmethod
    def _patch_write_model(cls) -> None:
        """Patch the entity's `WriteModel` by deriving it from the entity's `ReadModel`.

        Recurse through nested models.
        """

        def as_write_model(
            model_cls: type[OrmModel],
            base_cls: type[OrmModel] = cls.WriteModel,
            suffix: str = 'ReadModel',
        ) -> type[OrmModel]:
            """Derive the write-version of a read model by recursively discarding read-only fields.

            This also discards any serializers/validators defined on read-only fields.

            :param model_cls: The read model class to derive the write model from.
            :param base_cls: The base class to use for the write model.
            :param suffix: The model name suffix to replace with 'WriteModel'.
            :return: The derived creation model class.
            """

            def copy_model_field(field: pdt.fields.FieldInfo) -> tuple[Any, pdt.fields.FieldInfo]:
                """Copy a model field, replacing any nested read models with their write model equivalent."""
                annotation = field.annotation
                if isinstance(annotation, type) and issubclass(annotation, OrmModel):
                    annotation = as_write_model(annotation, base_cls=OrmModel, suffix='Model')
                return annotation, deepcopy(field)

            bases: list[type[OrmModel]] = []
            if issubclass(model_cls, OrmFieldsAsModelDump):
                bases.append(OrmFieldsAsModelDump)  # write models should inherit the override
            bases.append(base_cls)

            model_fields: dict[str, Any] = {
                key: copy_model_field(field)
                for key, field in model_cls.model_fields.items()
                if not get_metadata(field, 'read_only', False)
            }

            serializers = {
                key: deepcopy(serializer)
                for key, serializer in model_cls.__pydantic_decorators__.field_serializers.items()
                if all(serializer_key in model_fields for serializer_key in serializer.info.fields)
            }

            validators = {
                key: deepcopy(validator)
                for key, validator in model_cls.__pydantic_decorators__.field_validators.items()
                if all(validator_key in model_fields for validator_key in validator.info.fields)
            }

            name = model_cls.__name__.replace(suffix, 'WriteModel')
            WriteModel = pdt.create_model(  # noqa: N806
                name,
                __base__=tuple(bases),
                __module__=model_cls.__module__,
                **model_fields,
            )
            WriteModel.__qualname__ = model_cls.__qualname__.replace(suffix, 'WriteModel')
            WriteModel.__pydantic_decorators__.field_serializers = serializers
            WriteModel.__pydantic_decorators__.field_validators = validators
            WriteModel.model_config = deepcopy(model_cls.model_config)

            WriteModel.model_rebuild(force=True)

            return WriteModel

        if 'WriteModel' not in cls.__dict__:
            cls.WriteModel = as_write_model(cls.ReadModel)  # type: ignore[assignment, misc]

    @classmethod
    def _patch_qb_fields(cls) -> None:
        """Patch the `fields` attribute of the class based on the `ReadModel` definition."""
        current_fields = getattr(cls, 'fields', None)
        if current_fields is not None and not isinstance(current_fields, QbFields):
            raise ValueError(f'fields already set on `{cls}`')

        fields: dict[str, Any] = {}

        if 'ReadModel' in cls.__dict__:
            cls._validate_model_inheritance('ReadModel')

        for key, field in cls.ReadModel.model_fields.items():
            fields[key] = add_field(
                key,
                alias=field.alias,
                dtype=field.annotation,
                doc=field.description or '',
            )

        cls.fields = QbFields(fields)

    @classmethod
    def _validate_model_inheritance(cls, model_name: str = 'ReadModel') -> None:
        """Validate that model class inherits from all necessary base classes.

        :param model_name: The name of the model class to validate, e.g., 'ReadModel' or 'WriteModel'.
        :raises RuntimeError: if the model class does not inherit from all necessary base classes.
        """
        if getattr(cls, '_SKIP_MODEL_INHERITANCE_CHECK', False):
            return

        expected_inheritance: set[type[OrmModel]] = set()
        for entity_class in cls.mro():
            if (
                # We skip ourselves
                entity_class is not cls
                # and only care if we have the requested model
                and (expected_model := getattr(entity_class, model_name, None))
                # and that the model is not extended by one we already picked
                and not any(issubclass(other_class, expected_model) for other_class in expected_inheritance)
            ):
                expected_inheritance.add(expected_model)

        actual_model: type[OrmModel] = getattr(cls, model_name)
        actual_inheritance: set[type[OrmModel]] = set()
        for model_class in actual_model.mro():
            if (
                # We skip ourselves
                model_class is not actual_model
                # and only care about ORM models
                and issubclass(model_class, OrmModel)
                # and only if we are expected
                and model_class in expected_inheritance
                # and that the model is not extended by one we already picked
                and not any(issubclass(other_class, model_class) for other_class in actual_inheritance)
            ):
                actual_inheritance.add(model_class)

        if actual_inheritance != expected_inheritance:
            bases = [f'{e.__module__}.{e.__qualname__}' for e in expected_inheritance]
            raise RuntimeError(
                f'`{cls.__name__}.{model_name}` does not subclass all necessary base classes. It should be: '
                f'`class {model_name}({", ".join(sorted(bases))}):`'
            )

    def _to_model_field_values(
        self,
        *,
        context: dict[str, Any] | None = None,
        minimal: bool = False,
        schema: type[OrmModel] | None = None,
    ) -> dict[str, Any]:
        """Collect values to populate the model.

        Centralizes mapping of ORM -> Model values, including handling of `orm_to_model`
        functions and optional filtering based on field metadata (e.g., excluding CLI-only fields).
        The process is recursive, applying metadata field rules to nested models as well.

        :param context: Optional context dictionary to pass to `orm_to_model` callables.
        :param minimal: Whether to exclude potentially large value fields.
        :param schema: The schema model to collect field values for. If not provided, defaults to the entity's `Model`.
        :return: Mapping of ORM field name to value.
        """

        def get_model_field_values(schema: type[OrmModel]) -> dict[str, Any]:
            fields: dict[str, Any] = {}

            for key, field in schema.model_fields.items():
                field_name = field.alias or key
                if get_metadata(field, 'may_be_large') and minimal:
                    continue

                if orm_to_model := get_metadata(field, 'orm_to_model'):
                    signature = inspect.signature(orm_to_model)
                    parameters = list(signature.parameters.values())
                    fields[field_name] = orm_to_model(self) if len(parameters) == 1 else orm_to_model(self, context)
                else:
                    annotation = field.annotation
                    if isinstance(annotation, type) and issubclass(annotation, OrmModel):
                        fields[field_name] = get_model_field_values(annotation)
                    else:
                        fields[field_name] = getattr(self, key, field.default)

            return fields

        return get_model_field_values(schema or self.ReadModel)


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
