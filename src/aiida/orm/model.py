from __future__ import annotations

import typing as t

from pydantic import create_model

from aiida.common.pydantic import AiiDABaseModel, get_metadata


class OrmModel(AiiDABaseModel):
    """Base class for Read/Write/Attributes models."""

    @classmethod
    def _as_minimal_model(cls: t.Type[OrmModel]) -> t.Type[OrmModel]:
        """Return a derived model class with fields marked as "may_be_large" excluded from the model schema."""
        cached = cls.__dict__.get('_AIIDA_MINIMAL_MODEL')
        if isinstance(cached, type) and issubclass(cached, OrmModel):
            return cached

        MinimalModel = create_model(  # noqa: N806
            'Minimal' + cls.__name__,
            __base__=OrmModel,
            __module__=cls.__module__,
        )
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

        # Make subsequent calls idempotent for this specific class
        cls._AIIDA_MINIMAL_MODEL = MinimalModel  # type: ignore[attr-defined]

        MinimalModel.model_rebuild(force=True)
        return MinimalModel

    @classmethod
    def _as_write_model(cls: t.Type[OrmModel], suffix: str = 'ReadModel') -> t.Type[OrmModel]:
        """Return a derived creation model class with read-only fields removed.

        This also removes any serializers/validators defined on those fields.

        :return: The derived creation model class.
        """

        cached = cls.__dict__.get('_AIIDA_WRITE_MODEL')
        if isinstance(cached, type) and issubclass(cached, OrmModel):
            return cached

        qualname = cls.__qualname__.replace(suffix, 'WriteModel')
        WriteModel = create_model(  # noqa: N806
            qualname.split('.')[-1],
            __base__=cls,
            __module__=cls.__module__,
            __qualname__=qualname,
        )

        # Convert nested models to their 'write' variants
        for field in WriteModel.model_fields.values():
            annotation = field.annotation
            if isinstance(annotation, type) and issubclass(annotation, OrmModel):
                field.annotation = annotation._as_write_model(suffix='Model')

        readonly_fields: t.List[str] = []
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

        # Make subsequent calls idempotent for this specific class
        cls._AIIDA_WRITE_MODEL = WriteModel  # type: ignore[attr-defined]

        WriteModel.model_rebuild(force=True)

        return WriteModel
