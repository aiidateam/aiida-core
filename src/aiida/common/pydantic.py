"""Utilities related to ``pydantic``."""

from __future__ import annotations

import typing as t

from pydantic import BaseModel, ConfigDict, Field
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

if t.TYPE_CHECKING:
    from aiida.orm import Entity


def get_metadata(field_info: FieldInfo, key: str, default: t.Any | None = None) -> t.Any:
    """Return a the metadata of the given field for a particular key.

    :param field_info: The field from which to retrieve the metadata.
    :param key: The metadata name.
    :param default: Optional default value to return in case the metadata is not defined on the field.
    :returns: The metadata if defined, otherwise the default.
    """
    for element in field_info.metadata:
        if isinstance(element, dict) and key in element:
            return element[key]
    return default


class AiiDABaseModel(BaseModel, defer_build=True):
    """Base class for all AiiDA pydantic models."""

    model_config = ConfigDict(
        serialize_by_alias=True,
        validate_by_alias=True,
        validate_by_name=True,
    )

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: t.Any) -> None:
        super().__pydantic_init_subclass__(**kwargs)
        cls._set_json_schema_title()

    @classmethod
    def __pydantic_on_complete__(cls, **kwargs: t.Any) -> None:
        # For Node subclasses, `__pydantic_init_subclass__` is run too early due to patching.
        # However, we can't only use `__pydantic_on_complete__` due to `defer_build=True`.
        # Therefore, we set the JSON schema title in both to guarantee the title is set correctly.
        super().__pydantic_on_complete__(**kwargs)
        cls._set_json_schema_title()

    @classmethod
    def _set_json_schema_title(cls) -> None:
        """Derive the JSON schema title.

        The title is derived from the `__qualname__`, for example, `Int.Model` -> `IntModel`
        """
        cls.model_config['title'] = cls.__qualname__.replace('.', '')


def MetadataField(  # noqa: N802
    default: t.Any = PydanticUndefined,
    *,
    priority: int = 0,
    short_name: str | None = None,
    option_cls: t.Any | None = None,
    orm_class: type[Entity[t.Any, t.Any]] | str | None = None,
    orm_to_model: (
        t.Callable[[Entity[t.Any, t.Any]], t.Any] | t.Callable[[Entity[t.Any, t.Any], dict[str, t.Any]], t.Any] | None
    ) = None,
    model_to_orm: t.Callable[[AiiDABaseModel], t.Any] | None = None,
    read_only: bool = False,
    write_only: bool = False,
    may_be_large: bool = False,
    **kwargs: t.Any,
) -> t.Any:
    """Return a :class:`pydantic.fields.Field` instance with additional metadata.

    .. code-block:: python

        class Model(AiiDABaseModel):

            field: MetadataField('default', priority=1000, short_name='-A')

    This is a utility function that constructs a ``Field`` instance with an easy interface to add additional metadata.
    It is possible to add metadata using ``Annotated``::

        class Model(AiiDABaseModel):

            field: Annotated[str, {'metadata': 'value'}] = Field(...)

    However, when requiring multiple metadata, this notation can make the model difficult to read. Since this utility
    is only used to automatically build command line interfaces from the model definition, it is possible to restrict
    which metadata are accepted.

    :param priority: Used to order the list of all fields in the model. Ordering is done from small to large priority.
    :param short_name: Optional short name to use for an option on a command line interface.
    :param option_cls: The :class:`click.Option` class to use to construct the option.
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
    :param read_only: When set to ``True``, this field value will not be passed to the ORM entity constructor
        through ``Entity.from_model``.
    :param write_only: When set to ``True``, this field value will not be populated when constructing the model from an
        ORM entity through ``Entity.to_model``.
    :param may_be_large: Whether the field value may be large. This is used to determine whether to include the field
        when serializing the entity for various purposes, such as exporting or logging.
    """

    extra = kwargs.pop('json_schema_extra', {})

    if read_only and write_only:
        raise ValueError('A field cannot be both read-only and write-only.')

    if read_only:
        extra.update({'readOnly': True})

    if write_only:
        extra.update({'writeOnly': True})

    kwargs['json_schema_extra'] = extra

    field_info = Field(default, **kwargs)

    for key, value in (
        ('priority', priority),
        ('short_name', short_name),
        ('option_cls', option_cls),
        ('orm_class', orm_class),
        ('orm_to_model', orm_to_model),
        ('model_to_orm', model_to_orm),
        ('read_only', read_only),
        ('write_only', write_only),
        ('may_be_large', may_be_large),
    ):
        if value is not None:
            field_info.metadata.append({key: value})

    return field_info
