from __future__ import annotations

import abc
import dataclasses
import functools
import typing as t

import pydantic as pdt
from pydantic_core import PydanticUndefined

from aiida.cmdline.spec import CliParameter
from aiida.common.lang import classproperty
from aiida.common.utils import is_nullable, make_nullable, make_required
from aiida.orm.decorators.attributes import NodeAttribute, iter_attributes
from aiida.orm.decorators.columns import iter_columns

if t.TYPE_CHECKING:
    from aiida.cmdline.params.options.interactive import TemplateInteractiveOption
    from aiida.orm import Entity
    from aiida.orm.decorators.base import BaseField
    from aiida.orm.models.entity import EntityModel

__all__ = (
    'CliAdapter',
    'CliFieldInfo',
    'EntityCliCreateSpec',
)


_CliValueT = t.TypeVar('_CliValueT')
_ModelValueT = t.TypeVar('_ModelValueT')


class CliAdapter(abc.ABC, t.Generic[_CliValueT, _ModelValueT]):
    """Abstract base class for adapters between CLI/external and model-side representations."""

    _cli_type: t.ClassVar[t.Any] = None

    @classproperty
    def cli_type(cls: type[CliAdapter]) -> t.Any:  # noqa: N805
        """Return the CLI-side type inferred from the `to_model` value annotation."""
        if cls._cli_type is None:
            try:
                cls._cli_type = t.get_type_hints(cls.to_model)['value']
            except KeyError:
                raise TypeError(f'{cls.__name__}.to_model must annotate its `value` parameter') from None

        return cls._cli_type

    @abc.abstractmethod
    def to_model(self, value: _CliValueT) -> _ModelValueT:
        """Convert a CLI/external value to its model-side representation."""

    @abc.abstractmethod
    def to_cli(self, value: _ModelValueT) -> _CliValueT:
        """Convert a model-side value to its CLI/external representation."""


@dataclasses.dataclass(frozen=True)
class CliFieldInfo:
    """Optional Click-specific configuration for an ORM field."""

    prompt: str | bool | None = None
    help: str = ''
    priority: int = 0
    short_name: str = ''
    option_cls: functools.partial[TemplateInteractiveOption] | None = None


@dataclasses.dataclass(frozen=True)
class _CliField:
    """Resolved ORM field participating in CLI creation."""

    name: str
    field: BaseField
    model_field: pdt.fields.FieldInfo


class EntityCliCreateSpec:
    """CLI creation specification backed by an Entity create model."""

    def __init__(self, entity_type: type[Entity]) -> None:
        self.entity_type = entity_type

    def parameters(self) -> list[CliParameter]:
        """Return the resolved CLI parameters."""
        parameters: list[CliParameter] = []

        for cli_field in self._iter_fields():
            field = cli_field.field
            model_field = cli_field.model_field
            cli_info = field.cli_field_info or CliFieldInfo()

            annotation = make_required(
                self._cli_field_annotation(
                    field,
                    model_field.annotation,
                )
            )

            if model_field.default is not PydanticUndefined:
                default = model_field.default
            elif model_field.default_factory is not None:
                default = model_field.default_factory
            else:
                default = None

            prompt = cli_info.prompt if cli_info.prompt is not None else field.title

            parameters.append(
                CliParameter(
                    name=cli_field.name,
                    annotation=annotation,
                    required=model_field.is_required(),
                    default=default,
                    prompt=prompt,
                    help=cli_info.help or field.spec.description,
                    priority=cli_info.priority,
                    short_name=cli_info.short_name,
                    option_cls=cli_info.option_cls,
                )
            )

        return parameters

    def validate(self, values: dict[str, t.Any]) -> EntityModel:
        """Convert flat CLI values and validate them through the entity create model."""
        model_values: dict[str, t.Any] = {}
        attribute_values: dict[str, t.Any] = {}

        cli_fields = {cli_field.name: cli_field.field for cli_field in self._iter_fields()}

        for name, value in values.items():
            field = cli_fields.get(name)

            if field is None:
                continue

            value = self._cli_to_model_value(field, value)  # noqa: PLW2901

            if isinstance(field, NodeAttribute):
                attribute_values[name] = value
            else:
                model_values[name] = value

        if attribute_values:
            model_values['attributes'] = attribute_values

        return self.entity_type.models.create(**model_values)

    def serialize(
        self,
        entity: Entity,
        *,
        context: dict[str, t.Any] | None = None,
        exclude_none: bool = False,
    ) -> dict[str, t.Any]:
        """Serialize an entity to its flat CLI/external representation."""
        if not isinstance(entity, self.entity_type):
            raise TypeError(f'expected {self.entity_type.__name__}, got {type(entity).__name__}')

        values: dict[str, t.Any] = {}

        for cli_field in self._iter_fields():
            field = cli_field.field
            value = getattr(entity, cli_field.name)

            if value is None:
                if not exclude_none:
                    values[cli_field.name] = None
                continue

            if field.model_adapter is not None:
                value = field.model_adapter.to_model(
                    value,
                    context=context,
                )

            if field.cli_adapter is not None:
                value = field.cli_adapter.to_cli(value)

            values[cli_field.name] = value

        return values

    def _iter_fields(self) -> t.Iterator[_CliField]:
        """Yield all CLI-exposed fields in their flat external namespace."""
        create_model = self.entity_type.models.create

        for name, column in iter_columns(self.entity_type).items():
            if column.cli_exclude:
                continue

            model_field = create_model.model_fields.get(name)

            if model_field is None:
                continue

            yield _CliField(
                name=name,
                field=column,
                model_field=model_field,
            )

        models_namespace = self.entity_type.models

        if not hasattr(models_namespace, 'attributes'):
            return

        attributes_model = models_namespace.attributes

        for name, attribute in iter_attributes(self.entity_type).items():
            if attribute.cli_exclude:
                continue

            model_field = attributes_model.model_fields.get(name)

            if model_field is None:
                continue

            yield _CliField(
                name=name,
                field=attribute,
                model_field=model_field,
            )

    @staticmethod
    def _cli_field_annotation(
        field: BaseField,
        model_annotation: t.Any,
    ) -> t.Any:
        """Return the CLI-side annotation for a model field."""
        if field.cli_adapter is None:
            return model_annotation

        annotation = field.cli_adapter.cli_type

        if is_nullable(model_annotation):
            annotation = make_nullable(annotation)

        return annotation

    @staticmethod
    def _cli_to_model_value(
        field: BaseField,
        value: t.Any,
    ) -> t.Any:
        """Convert a CLI-side value to its model-side representation."""
        if value is None or field.cli_adapter is None:
            return value

        return field.cli_adapter.to_model(value)
