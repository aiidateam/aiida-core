from __future__ import annotations

import datetime
import typing as t

import pydantic as pdt
from pydantic import create_model
from pydantic_core import PydanticUndefined

from aiida.common.exceptions import EntryPointError, NotExistent
from aiida.common.pydantic import AiiDABaseModel, MetadataField, get_metadata

if t.TYPE_CHECKING:
    from aiida.orm import Entity

__all__ = ('OrmModel',)


class OrmModel(AiiDABaseModel):
    """Base class for Read/Write/Attributes models."""

    model_config = pdt.ConfigDict(
        extra='forbid',
        json_encoders={
            datetime.datetime: lambda dt: dt.isoformat().replace('Z', '+00:00'),
        },
    )

    def _to_orm_field_values(self) -> dict[str, t.Any]:
        """Return the field values for ORM instantiation."""
        from aiida.plugins.factories import BaseFactory

        fields: dict[str, t.Any] = {}
        for key, field in self.__class__.model_fields.items():
            field_name = field.alias or key
            field_value = getattr(self, key, field.default)

            if field_value is None:
                continue

            if isinstance(field_value, OrmModel):
                fields[field_name] = field_value._to_orm_field_values()
            elif orm_class := get_metadata(field, 'orm_class'):
                if isinstance(orm_class, str):
                    try:
                        orm_class = BaseFactory('aiida.orm', orm_class)
                    except EntryPointError as exception:
                        raise EntryPointError(f'invalid `orm_class` on `{key}`: {exception}') from exception
                try:
                    fields[field_name] = orm_class.collection.get(id=field_value)
                except NotExistent as exception:
                    raise NotExistent(f'no `{orm_class}` found with pk={field_value}') from exception
            elif model_to_orm := get_metadata(field, 'model_to_orm'):
                fields[field_name] = model_to_orm(self)
            else:
                fields[field_name] = field_value

        return fields

    @classmethod
    def _as_minimal_model(cls: t.Type[OrmModel]) -> type[OrmModel]:
        """Return a derived model class excluding fields marked as "may_be_large"."""
        cached = cls.__dict__.get('_AIIDA_MINIMAL_MODEL')
        if isinstance(cached, type) and issubclass(cached, OrmModel):
            return cached
        try:
            orm_class_name, model_name = cls.__qualname__.split('.')
        except ValueError as exception:
            raise ValueError(f"expected 'OrmClass.ModelName' format, got '{cls.__qualname__}'") from exception
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


class OrmFieldsAsModelDump(OrmModel):
    """Mixin to override the default ORM field value extraction with a simple call to `model_dump`."""

    def _to_orm_field_values(self) -> dict[str, t.Any]:
        """Return the field values for ORM instantiation as a simple call to `model_dump`."""
        return self.model_dump(exclude_none=True)


def OrmMetadataField(  # noqa: N802
    default: t.Any = PydanticUndefined,
    *,
    orm_class: type[Entity[t.Any, t.Any]] | str | None = None,
    orm_to_model: (
        t.Callable[[Entity[t.Any, t.Any]], t.Any] | t.Callable[[Entity[t.Any, t.Any], dict[str, t.Any]], t.Any] | None
    ) = None,
    model_to_orm: t.Callable[[OrmModel], t.Any] | None = None,
    **kwargs: t.Any,
) -> t.Any:
    """Extend `MetadataField` with ORM specific options.

    :param orm_class: The class, or entry point name thereof, to which the field should be converted. If this field is
        defined, the value of this field should accept an integer which will automatically be converted to an instance
        of said ORM class using ``orm_class.collection.get(id={field_value})``. This is useful, for example, where a
        field represents an instance of a different entity, such as an instance of ``User``. The serialized data would
        store the ``pk`` of the user, but the ORM entity instance would receive the actual ``User`` instance with that
        primary key.
    :param orm_to_model: Optional callable to convert the value of a field from an ORM instance to a model instance.
        It optionally accepts a second argument, which is a dictionary of context values that may be used during the
        conversion.
    :param model_to_orm: Optional callable to convert the value of a field from a model instance to an ORM instance.
    """

    field_info = MetadataField(default, **kwargs)

    for key, value in (
        ('orm_class', orm_class),
        ('orm_to_model', orm_to_model),
        ('model_to_orm', model_to_orm),
    ):
        if value is not None:
            field_info.metadata.append({key: value})

    return field_info
