"""Utilities related to ``pydantic``."""

from __future__ import annotations

import typing as t

from pydantic import Field


def MetadataField(  # noqa: N802
    default: t.Any | None = None,
    *,
    priority: int = 0,
    short_name: str | None = None,
    option_cls: t.Any | None = None,
    **kwargs,
):
    """Return a :class:`pydantic.fields.Field` instance with additional metadata.

    .. code-block:: python

        class Model(BaseModel):

            attribute: MetadataField('default', priority=1000, short_name='-A')

    This is a utility function that constructs a ``Field`` instance with an easy interface to add additional metadata.
    It is possible to add metadata using ``Annotated``::

        class Model(BaseModel):

            attribute: Annotated[str, {'metadata': 'value'}] = Field(...)

    However, when requiring multiple metadata, this notation can make the model difficult to read. Since this utility
    is only used to automatically build command line interfaces from the model definition, it is possible to restrict
    which metadata are accepted.

    :param priority: Used to order the list of all fields in the model. Ordering is done from small to large priority.
    :param short_name: Optional short name to use for an option on a command line interface.
    :param option_cls: The :class:`click.Option` class to use to construct the option.
    """
    field_info = Field(default, **kwargs)

    for key, value in (('priority', priority), ('short_name', short_name), ('option_cls', option_cls)):
        if value is not None:
            field_info.metadata.append({key: value})

    return field_info
