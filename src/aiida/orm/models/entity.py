from __future__ import annotations

import functools
import typing as t
from copy import deepcopy

import pydantic as pdt
from pydantic_core import PydanticUndefined
from typing_extensions import Self

from aiida.common.utils import (
    is_nullable,
    make_annotated,
    make_nullable,
    make_required,
)
from aiida.orm.decorators.columns import iter_columns
from aiida.orm.models.modeling import (
    iter_model_serializers,
    iter_model_validators,
    make_model_serializer,
    make_model_validator,
)

if t.TYPE_CHECKING:
    from aiida.orm.decorators.base import BaseField
    from aiida.orm.decorators.columns import Column, ColumnSpec
    from aiida.orm.models.modeling import ModelMetadata, ModelProjection

__all__ = (
    'CreateModel',
    'EntityModel',
    'ModelsNamespace',
    'OrmModel',
    'ReadModel',
    'UpdateModel',
)


_OwnerT = t.TypeVar('_OwnerT')


class OrmModel(pdt.BaseModel, t.Generic[_OwnerT]):
    """Base class for ORM models."""

    model_config = pdt.ConfigDict(
        extra='forbid',
        serialize_by_alias=True,
        validate_by_alias=True,
        validate_by_name=True,
    )


_EntityT = t.TypeVar('_EntityT')


class EntityModel(OrmModel[_EntityT]):
    """Base class for dynamically generated ORM entity models."""

    _entity: t.ClassVar[type[_EntityT]]
    _entity_columns: t.ClassVar[dict[str, Column]]
    _models_namespace: t.ClassVar[ModelsNamespace[t.Any]]
    _minimal_model: t.ClassVar[type[EntityModel[_EntityT]] | None] = None

    @classmethod
    def field_spec(cls, name: str) -> ColumnSpec:
        """Return the canonical ORM column specification for a model field."""
        return cls._entity_columns[name].spec

    @classmethod
    def from_entity(
        cls,
        entity: _EntityT,
        *,
        context: dict[str, t.Any] | None = None,
        minimal: bool = False,
    ) -> Self:
        """Create a model from an ORM entity."""
        values = cls._from_entity_field_values(entity, context=context, minimal=minimal)
        return cls.model_validate(values)

    @classmethod
    def _from_entity_field_values(
        cls,
        entity: _EntityT,
        *,
        context: dict[str, t.Any] | None = None,
        minimal: bool = False,
    ) -> dict[str, t.Any]:
        """Convert ORM entity values to model-side representations."""
        return {
            name: cls._models_namespace._to_model_value(
                column,
                getattr(entity, name),
                context=context,
            )
            for name, column in cls._entity_columns.items()
            if not (column.spec.may_be_large and minimal)
        }

    def _to_entity_field_values(self, *, only_set: bool = False) -> dict[str, t.Any]:
        """Convert model values to entity-side representations."""
        names: t.Iterable[str] = self.model_fields_set if only_set else self.__class__.model_fields

        return {
            name: self.__class__._models_namespace._to_entity_value(
                self.__class__._entity_columns[name],
                getattr(self, name),
            )
            for name in names
        }

    @classmethod
    def minimize(cls) -> type[EntityModel[_EntityT]]:
        """Return a derived model excluding columns marked as `may_be_large`."""
        cached = cls.__dict__.get('_minimal_model')

        if cached is not None:
            return cached

        model_fields: dict[str, t.Any] = {}

        for name, model_field in cls.model_fields.items():
            column = cls._entity_columns.get(name)

            if column is not None and column.spec.may_be_large:
                continue

            annotation = model_field.annotation
            field_info = deepcopy(model_field)

            if isinstance(annotation, type) and issubclass(annotation, EntityModel):
                annotation = annotation.minimize()
                field_info.annotation = annotation

                if any(field.is_required() for field in annotation.model_fields.values()):
                    field_info.default_factory = None

            model_fields[name] = (annotation, field_info)

        minimal_model = t.cast(
            type[EntityModel[_EntityT]],
            pdt.create_model(
                f'Minimal{cls.__name__}',
                __config__=deepcopy(cls.model_config) | {'extra': 'ignore'},
                __base__=EntityModel,
                __module__=cls.__module__,
                __qualname__=f'{cls.__qualname__.rsplit(".", 1)[0]}.Minimal{cls.__name__}',
                **model_fields,
            ),
        )

        minimal_model._entity = cls._entity
        minimal_model._entity_columns = {
            name: column for name, column in cls._entity_columns.items() if name in model_fields
        }
        minimal_model._models_namespace = cls._models_namespace

        cls._minimal_model = minimal_model
        return minimal_model


class ReadModel(EntityModel[_EntityT]):
    """Read projection of an ORM entity."""


class CreateModel(EntityModel[_EntityT]):
    """Input projection for constructing an ORM entity."""

    def to_entity(self) -> _EntityT:
        """Construct an ORM entity from this model."""
        return self.__class__._entity(**self._to_entity_field_values())


class UpdateModel(EntityModel[_EntityT]):
    """PATCH-like projection for mutating an ORM entity."""

    def apply(self, entity: _EntityT) -> _EntityT:
        """Apply explicitly set values to an ORM entity."""
        for name, value in self._to_entity_field_values(only_set=True).items():
            setattr(entity, name, value)

        return entity


class ModelsNamespace(t.Generic[_EntityT]):
    """Lazily generated model projections for one entity class."""

    def __init__(self, *, entity: type[_EntityT] | None = None) -> None:
        self._entity = entity
        self._namespaces: dict[type[t.Any], Self] = {}

    @t.overload
    def __get__(self, instance: None, owner: type[_EntityT]) -> Self: ...

    @t.overload
    def __get__(self, instance: object, owner: type[_EntityT] | None = None) -> t.Never: ...

    def __get__(self, instance: object | None, owner: type[_EntityT] | None = None) -> Self:
        if owner is None:
            raise AttributeError('models must be accessed through an entity class')

        if instance is not None:
            raise AttributeError(f"'models' must be accessed through the entity class; use {owner.__name__}.models")

        namespace = self._namespaces.get(owner)

        if namespace is None:
            namespace = type(self)(entity=owner)
            self._namespaces[owner] = namespace

        return namespace

    @functools.cached_property
    def read(self) -> type[ReadModel[_EntityT]]:
        """Return the read projection."""
        return self._build_model('read')

    @functools.cached_property
    def create(self) -> type[CreateModel[_EntityT]]:
        """Return the create projection."""
        return self._build_model('create')

    @functools.cached_property
    def update(self) -> type[UpdateModel[_EntityT]]:
        """Return the update projection."""
        return self._build_model('update')

    def _model_field_annotation(self, column: Column, projection: ModelProjection) -> t.Any:
        """Return the model-side annotation for an entity column."""
        spec = column.spec

        field_info = column.model_field_info

        if field_info.annotation is not None:
            annotation = field_info.annotation
        elif column.model_adapter is not None:
            annotation = column.model_adapter.model_type
        else:
            annotation = spec.value_type

        if is_nullable(spec.value_type):
            annotation = make_nullable(annotation)

        if projection == 'read' and spec.required_once_stored:
            annotation = make_required(annotation)

        return annotation

    def _to_model_value(
        self,
        column: Column,
        value: t.Any,
        *,
        context: t.Any | None = None,
    ) -> t.Any:
        """Convert an entity column value to its model representation."""
        if value is not None and (adapter := column.model_adapter):
            return adapter.to_model(value, context=context)

        return value

    def _to_entity_value(self, column: Column, value: t.Any) -> t.Any:
        """Convert a model value to its entity representation."""
        if value is not None and (adapter := column.model_adapter):
            return adapter.to_orm(value)

        return value

    @t.overload
    def _build_model(self, projection: t.Literal['read']) -> type[ReadModel[_EntityT]]: ...

    @t.overload
    def _build_model(self, projection: t.Literal['create']) -> type[CreateModel[_EntityT]]: ...

    @t.overload
    def _build_model(self, projection: t.Literal['update']) -> type[UpdateModel[_EntityT]]: ...

    def _build_model(self, projection: ModelProjection) -> type[EntityModel[_EntityT]]:
        """Build a model projection."""
        if self._entity is None:
            raise RuntimeError('model namespace is not bound to an entity class')

        model_fields: dict[str, t.Any] = {}
        entity_columns: dict[str, Column] = {}

        for name, column in iter_columns(self._entity).items():
            spec = column.spec

            if not _include_column(spec, projection):
                continue

            model_fields[name] = _build_model_field(
                self._model_field_annotation(column, projection),
                description=spec.description,
                model_field_info=column.model_field_info,
                model_metadata=_model_metadata(column, projection),
                readonly=spec.readonly,
            )

            entity_columns[name] = column

        entity_model_decorators = self._model_decorators(projection)

        entity_model_base = _entity_model_base(projection)
        class_name = f'{projection.capitalize()}Model'

        config: pdt.ConfigDict = {**entity_model_base.model_config}

        if entity_model_config := self._entity.__dict__.get('_entity_model_config'):
            config.update(entity_model_config)

        model = t.cast(
            type[EntityModel[_EntityT]],
            pdt.create_model(
                f'{self._entity.__name__}{class_name}',
                __base__=entity_model_base,
                __config__=config,
                __module__=self._entity.__module__,
                __qualname__=f'{self._entity.__qualname__}.{class_name}',
                __validators__=entity_model_decorators,
                **model_fields,
            ),
        )

        model._entity = self._entity
        model._entity_columns = entity_columns
        model._models_namespace = self

        return model

    def _model_decorators(self, projection: ModelProjection) -> dict[str, t.Any]:
        """Return Pydantic-decorated model hooks for an entity projection."""
        if self._entity is None:
            raise RuntimeError('model namespace is not bound to an entity class')

        decorators: dict[str, t.Any] = {}

        for name, (function, validator) in iter_model_validators(self._entity).items():
            if validator.projections is not None and projection not in validator.projections:
                continue

            decorators[name] = make_model_validator(function, mode=validator.mode)

        for name, (function, serializer) in iter_model_serializers(self._entity).items():
            if serializer.projections is not None and projection not in serializer.projections:
                continue

            decorators[name] = make_model_serializer(function, mode=serializer.mode)

        return decorators


def _entity_model_base(projection: ModelProjection) -> type[EntityModel]:
    """Return the base class for a model projection."""
    if projection == 'read':
        return ReadModel

    if projection == 'create':
        return CreateModel

    if projection == 'update':
        return UpdateModel

    t.assert_never(projection)


def _include_column(spec: ColumnSpec, projection: ModelProjection) -> bool:
    """Return whether a column belongs to a model projection."""
    if projection == 'read':
        return True

    if projection == 'create':
        return not spec.readonly

    if projection == 'update':
        return spec.updatable

    t.assert_never(projection)


def _build_model_field(
    model_type: t.Any,
    *,
    description: str = '',
    model_field_info: pdt.fields.FieldInfo = pdt.fields.FieldInfo(),
    model_metadata: tuple[ModelMetadata, ...] = (),
    readonly: bool = False,
) -> tuple[t.Any, t.Any]:
    """Build the Pydantic declaration for a model field."""
    field_info = model_field_info
    field_dict = field_info.asdict()

    metadata = (*field_dict['metadata'], *model_metadata)
    attributes = dict(field_dict['attributes'])

    if field_info.default is not PydanticUndefined:
        attributes['default'] = field_info.default
    elif is_nullable(model_type):
        attributes['default'] = None

    if attributes['description'] is None and description:
        attributes['description'] = description

    if readonly:
        json_schema_extra = attributes['json_schema_extra']

        if json_schema_extra is None:
            json_schema_extra = {'readOnly': True}

        elif isinstance(json_schema_extra, dict):
            json_schema_extra = dict(json_schema_extra)
            json_schema_extra.setdefault('readOnly', True)

        else:
            original_json_schema_extra = json_schema_extra

            def json_schema_extra(schema: dict[str, t.Any], *args: t.Any) -> None:
                original_json_schema_extra(schema, *args)
                schema.setdefault('readOnly', True)

        attributes['json_schema_extra'] = json_schema_extra

    annotation = make_annotated(model_type, metadata)

    return annotation, pdt.fields.FieldInfo(**attributes)


def _model_metadata(field: BaseField, projection: ModelProjection) -> tuple[t.Any, ...]:
    """Return Pydantic metadata applicable to this projection."""
    return tuple(
        metadata
        for declaration in field.model_metadata
        if declaration.projections is None or projection in declaration.projections
        for metadata in declaration.metadata
    )
