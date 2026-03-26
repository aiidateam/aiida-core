from __future__ import annotations

import typing as t

import pydantic as pdt
from pydantic import create_model

from aiida.common.pydantic import AiiDABaseModel, get_metadata

__all__ = ('OrmModel',)


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
