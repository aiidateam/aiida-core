from __future__ import annotations

import typing as t

import pydantic as pdt
from pydantic import create_model

from aiida.common.pydantic import AiiDABaseModel, get_metadata

__all__ = ('OrmModel', 'WritableOrmModel')


class OrmModel(AiiDABaseModel):
    """Base class for Read/Write/Attributes models."""

    model_config = pdt.ConfigDict(extra='forbid')

    @classmethod
    def _as_minimal_model(cls: t.Type[OrmModel]) -> type[OrmModel]:
        """Return a derived model class with fields marked as "may_be_large" excluded from the model schema."""
        cached = cls.__dict__.get('_AIIDA_MINIMAL_MODEL')
        if isinstance(cached, type) and issubclass(cached, OrmModel):
            return cached
        try:
            orm_class_name, model_name = cls.__qualname__.split('.')
        except ValueError as exception:
            raise ValueError(
                f'Expected class name in format "OrmClass.ModelName", got "{cls.__qualname__}"; '
                'It is likely the ORM model was not correctly nested within its ORM class.'
            ) from exception
        MinimalModel = create_model(  # noqa: N806
            f'Minimal{model_name}',
            __base__=OrmModel,
            __module__=cls.__module__,
        )
        MinimalModel.__qualname__ = f'{orm_class_name}.Minimal{model_name}'
        MinimalModel.model_config['extra'] = 'ignore'

        for key, field in cls.model_fields.items():
            annotation = field.annotation
            if get_metadata(field, 'may_be_large'):
                continue
            if isinstance(annotation, type) and issubclass(annotation, OrmModel):
                sub_minimal_model = annotation._as_minimal_model()
                field.annotation = sub_minimal_model
                if any(f.is_required() for f in sub_minimal_model.model_fields.values()):
                    field.default_factory = None
            MinimalModel.model_fields[key] = field

        MinimalModel.model_rebuild(force=True)

        # Make subsequent calls idempotent for this specific class and the derived model
        cls._AIIDA_MINIMAL_MODEL = MinimalModel  # type: ignore[attr-defined]
        MinimalModel._AIIDA_MINIMAL_MODEL = MinimalModel  # type: ignore[attr-defined]

        return MinimalModel


class WritableOrmModel(OrmModel):
    """Base class for models that have writable versions, i.e., `ReadModel` and its `AttributesModel`."""

    @classmethod
    def _as_write_model(cls: type[WritableOrmModel], suffix: str = 'ReadModel') -> type[WritableOrmModel]:
        """Return a derived creation model class with read-only fields removed.

        This also removes any serializers/validators defined on those fields.

        :return: The derived creation model class.
        """

        cached = cls.__dict__.get('_AIIDA_WRITE_MODEL')
        if isinstance(cached, type) and issubclass(cached, WritableOrmModel):
            return cached

        qualname = cls.__qualname__.replace(suffix, 'WriteModel')
        WriteModel = pdt.create_model(  # noqa: N806
            qualname.split('.')[-1],
            __base__=cls,
            __module__=cls.__module__,
        )
        WriteModel.__qualname__ = qualname

        # Convert nested models to their 'write' variants
        for field in WriteModel.model_fields.values():
            annotation = field.annotation
            if isinstance(annotation, type) and issubclass(annotation, WritableOrmModel):
                field.annotation = annotation._as_write_model(suffix='Model')

        readonly_fields: list[str] = []
        for key, field in WriteModel.model_fields.items():
            if get_metadata(field, 'read_only'):
                readonly_fields.append(key)

        # Remove read-only fields
        for key in readonly_fields:
            WriteModel.model_fields.pop(key, None)
            if hasattr(WriteModel, key):
                delattr(WriteModel, key)

        # Prune field validators/serializers referring to read-only fields
        decorators = WriteModel.__pydantic_decorators__

        def prune_field_decorators(field_decorators: dict[str, t.Any]) -> dict[str, t.Any]:
            return {
                key: decorator
                for key, decorator in field_decorators.items()
                if all(field not in readonly_fields for field in decorator.info.fields)
            }

        decorators.field_validators = prune_field_decorators(decorators.field_validators)
        decorators.field_serializers = prune_field_decorators(decorators.field_serializers)

        WriteModel.model_rebuild(force=True)

        # Make subsequent calls idempotent for this specific class and the derived model
        cls._AIIDA_WRITE_MODEL = WriteModel  # type: ignore[attr-defined]
        WriteModel._AIIDA_WRITE_MODEL = WriteModel  # type: ignore[attr-defined]

        return WriteModel
