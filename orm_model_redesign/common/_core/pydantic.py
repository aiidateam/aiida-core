"""Building a pydantic model from field declarations. Mirrors ``aiida.common.pydantic``.

This is the piece with a genuine claim on a shared home. Three layers project the same
declarations -- REST and the CLI's export/import -- and each was hand-rolling a dict literal
over the same field names. What they share is the *builder*; what
stays theirs is which fields, under which names, serialised how.

In ``aiida`` this module already exists and already holds ``AiidaBaseModel``; the builder is
currently in ``aiida.restapi.models._builder``, where the CLI cannot reach it.
"""

from __future__ import annotations

import typing as t
from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict, Field, create_model
from pydantic.functional_validators import AfterValidator

from poc.common._core.fields import LayerField
from poc.orm._core.fields import MISSING, BaseField, ColumnField

__all__ = ('AiidaBaseModel', 'build_model', 'published_values')


class AiidaBaseModel(BaseModel):
    """Base class for models built over the ORM declarations."""

    model_config = ConfigDict(extra='forbid')


def _annotation(declaration: BaseField) -> t.Any:
    """Return the annotation for a field, carrying whatever the declaration says it must satisfy.

    Rendering and parsing are pydantic's, not ours: every declared type is one it already handles,
    and a value has to be database-serialisable before it gets here.
    """
    if declaration.validator is None:
        return declaration.dtype
    return t.Annotated[declaration.dtype, AfterValidator(declaration.validator)]


#: What a declaration with no layer entry gets: published under its own name, value untouched.
_PUBLISH_AS_IS: t.Final = LayerField()


def build_model(
    name: str,
    declarations: Mapping[str, BaseField],
    layer_options: Mapping[str, LayerField],
    *,
    base: type[AiidaBaseModel] = AiidaBaseModel,
) -> type[AiidaBaseModel]:
    """Build a model from the declarations and one layer's view of them.

    :param declarations: what the backend stores, from ``Entity._field_declarations``.
    :param layer_options: what this layer does with each, keyed by declared name. A declaration
        with no entry is published as it stands.
    """
    definitions: dict[str, t.Any] = {}

    for key, declaration in declarations.items():
        options = layer_options.get(key, _PUBLISH_AS_IS)
        if options.exclude:
            continue
        # `Field()` is typed to return the default's own type, so pin this or the first branch
        # decides what the other two may assign.
        info: t.Any
        default = declaration.default if isinstance(declaration, ColumnField) else MISSING
        factory = declaration.default_factory if isinstance(declaration, ColumnField) else None
        if factory is not None:
            info = Field(default_factory=factory, description=declaration.doc)
        elif default is MISSING:
            info = Field(description=declaration.doc)
        else:
            info = Field(default, description=declaration.doc)
        definitions[key] = (_annotation(declaration), info)

    return t.cast('type[AiidaBaseModel]', create_model(name, __base__=base, **definitions))


def published_values(entity: t.Any, layer_options: Mapping[str, LayerField]) -> dict[str, t.Any]:
    """Return the stored values a layer publishes, ready to hand to its model.

    Just the stored values of the fields the layer keeps; rendering them is pydantic's job.
    """
    declarations = type(entity)._field_declarations
    return {
        name: declaration.read(entity)
        for name, declaration in declarations.items()
        if not layer_options.get(name, _PUBLISH_AS_IS).exclude
    }
