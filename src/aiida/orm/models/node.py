from __future__ import annotations

import functools
import typing as t

import pydantic as pdt

from aiida.common.utils import (
    is_nullable,
    make_nullable,
    make_required,
)
from aiida.orm.decorators.attributes import (
    NodeAttribute,
    NodeAttributesColumn,
    iter_attributes,
)
from aiida.orm.models.entity import (
    CreateModel,
    EntityModel,
    ModelsNamespace,
    OrmModel,
    _build_field,
)

if t.TYPE_CHECKING:
    from aiida.orm.decorators.columns import Column
    from aiida.orm.models.modeling import ModelProjection


__all__ = ('NodeModelsNamespace',)

_OwnerT = t.TypeVar('_OwnerT')

_AttributesProjection = t.Literal['read', 'create']


class AttributesModel(OrmModel[_OwnerT]):
    """Base class for Node attributes models."""


class AttributesReadModel(AttributesModel[_OwnerT]):
    """Read projection of Node attributes."""


class AttributesCreateModel(AttributesModel[_OwnerT]):
    """Create projection of Node attributes."""


_NodeT = t.TypeVar('_NodeT')


class NodeCreateModel(CreateModel[_NodeT]):
    """Create model for Nodes, including non-column inputs."""

    files: pdt.json_schema.SkipJsonSchema[dict[str, t.Callable[[], t.BinaryIO | None]] | None] = None

    def _to_entity_field_values(self, *, only_set: bool = False) -> dict[str, t.Any]:
        return super()._to_entity_field_values(only_set=only_set) | {'files': self.files}


class NodeModelsNamespace(ModelsNamespace[_NodeT]):
    """Model namespace for Nodes with typed nested attributes."""

    @functools.cached_property
    def attributes(self) -> type[AttributesReadModel[_NodeT]]:
        """Return the canonical persisted/read attributes model."""
        return self._build_attributes_model('read')

    @functools.cached_property
    def _create_attributes(self) -> type[AttributesCreateModel[_NodeT]]:
        """Return the attributes model used by the Node create projection."""
        return self._build_attributes_model('create')

    def _entity_model_base(self, projection: ModelProjection) -> type[EntityModel]:
        """Return the base class for a Node model projection."""
        if projection == 'create':
            return NodeCreateModel

        return super()._entity_model_base(projection)

    def _model_field_annotation(self, column: Column, projection: ModelProjection) -> t.Any:
        """Return the model-side annotation for a Node column."""
        if isinstance(column, NodeAttributesColumn):
            if projection == 'update':
                raise RuntimeError('attributes are immutable and cannot have an update projection')

            return self._attributes_model_annotation(projection)

        return super()._model_field_annotation(column, projection)

    def _build_model_field(
        self,
        column: Column,
        projection: ModelProjection,
    ) -> tuple[t.Any, pdt.fields.FieldInfo]:
        """Build the Pydantic declaration for a Node model field."""
        annotation, field_info = super()._build_model_field(column, projection)

        if (
            projection == 'create'
            and isinstance(column, NodeAttributesColumn)
            and field_info.is_required()
            and not any(field.is_required() for field in self._create_attributes.model_fields.values())
        ):
            field_dict = field_info.asdict()
            attributes = dict(field_dict['attributes'])
            attributes['default_factory'] = dict
            field_info = pdt.fields.FieldInfo(**attributes)

        return annotation, field_info

    def _attributes_model_annotation(self, projection: _AttributesProjection) -> type[AttributesModel[_NodeT]]:
        """Return the attributes model for a Node projection."""
        if projection == 'read':
            return self.attributes

        return self._create_attributes

    def _to_model_value(
        self,
        column: Column,
        value: t.Any,
        *,
        context: t.Any | None = None,
    ) -> t.Any:
        """Convert a Node column value to its model representation."""
        if isinstance(column, NodeAttributesColumn):
            return self._attributes_to_model_value(value, context=context)

        return super()._to_model_value(column, value, context=context)

    def _to_entity_value(self, column: Column, value: t.Any) -> t.Any:
        """Convert a model value to its Node entity representation."""
        if isinstance(column, NodeAttributesColumn):
            return self._model_to_attributes_value(value)

        return super()._to_entity_value(column, value)

    @t.overload
    def _build_attributes_model(self, projection: t.Literal['read']) -> type[AttributesReadModel[_NodeT]]: ...

    @t.overload
    def _build_attributes_model(self, projection: t.Literal['create']) -> type[AttributesCreateModel[_NodeT]]: ...

    def _build_attributes_model(self, projection: _AttributesProjection) -> type[AttributesModel[_NodeT]]:
        """Build the typed attributes model for a Node projection."""
        if self._entity is None:
            raise RuntimeError('model namespace is not bound to a Node class')

        model_fields: dict[str, t.Any] = {}

        for name, attribute in iter_attributes(self._entity).items():
            spec = attribute.spec

            if projection == 'create' and spec.readonly:
                continue

            model_fields[name] = _build_field(
                self._attribute_model_annotation(attribute, projection),
                description=spec.description,
                model_field_info=attribute.model_field_info,
                model_metadata=attribute.model_metadata,
                readonly=spec.readonly,
            )

        attributes_base_model = self._attributes_model_base(projection)
        class_name = f'Attributes{projection.capitalize()}Model'

        config: pdt.ConfigDict = {**attributes_base_model.model_config}

        if attributes_model_config := self._entity.__dict__.get('_attributes_model_config'):
            config.update(attributes_model_config)

        return t.cast(
            type[AttributesModel[_NodeT]],
            pdt.create_model(
                f'{self._entity.__name__}{class_name}',
                __base__=attributes_base_model,
                __config__=config,
                __module__=self._entity.__module__,
                __qualname__=f'{self._entity.__qualname__}.{class_name}',
                **model_fields,
            ),
        )

    def _attribute_model_annotation(
        self,
        attribute: NodeAttribute,
        projection: _AttributesProjection,
    ) -> t.Any:
        """Return the model-side annotation for a typed Node attribute."""
        spec = attribute.spec
        field_info = attribute.model_field_info

        if field_info.annotation is not None:
            annotation = field_info.annotation
        elif attribute.model_adapter is not None:
            annotation = attribute.model_adapter.model_type
        else:
            annotation = spec.value_type

        if is_nullable(spec.value_type):
            annotation = make_nullable(annotation)

        if projection == 'read' and spec.required_once_stored:
            annotation = make_required(annotation)

        return annotation

    def _attributes_to_model_value(
        self,
        attributes: dict[str, t.Any],
        *,
        context: dict[str, t.Any] | None = None,
    ) -> dict[str, t.Any]:
        """Convert Node attributes to model-side representations."""
        if self._entity is None:
            raise RuntimeError('model namespace is not bound to a Node class')

        values = dict(attributes)

        for name, attribute in iter_attributes(self._entity).items():
            if name not in values:
                continue

            if values[name] is not None and (adapter := attribute.model_adapter):
                values[name] = adapter.to_model(values[name], context=context)

        return values

    def _model_to_attributes_value(self, model: AttributesModel[_NodeT] | dict[str, t.Any]) -> dict[str, t.Any]:
        """Convert model-side Node attributes to ORM representations."""
        if self._entity is None:
            raise RuntimeError('model namespace is not bound to a Node class')

        values = model.model_dump() if isinstance(model, AttributesModel) else dict(model)

        for name, attribute in iter_attributes(self._entity).items():
            if name not in values:
                continue

            if values[name] is not None and (adapter := attribute.model_adapter):
                values[name] = adapter.to_orm(values[name])

        return values

    def _attributes_model_base(self, projection: _AttributesProjection) -> type[AttributesModel]:
        """Return the base class for an attributes model projection."""
        if projection == 'read':
            return AttributesReadModel

        if projection == 'create':
            return AttributesCreateModel

        t.assert_never(projection)
