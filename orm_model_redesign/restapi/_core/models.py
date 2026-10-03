"""REST-owned projection of the ORM declarations. Private: a user never imports this.

Which fields a client may write is a decision of this layer, but it is *stated* on the entity, as
a ``rest_api_read_only`` option on the declaration. Nothing here is keyed by class name, so a class
this layer has never heard of is served as correctly as one it ships with.

The same three pieces as ``poc.cmdline._core.models``: a model builder, and a pair of functions taking
an entity to a payload and back. The asymmetry is that REST reads far more often than it writes,
so there are two model classes rather than one.
"""

from __future__ import annotations

import typing as t
from collections.abc import Mapping

from poc.common._core.fields import RestApiField
from poc.common._core.pydantic import AiidaBaseModel, build_model, published_values
from poc.orm._core.entities import Entity

__all__ = (
    'RestApiModel',
    'build_rest_read_model',
    'build_rest_write_model',
    'read_only_fields',
    'rest_deserialize',
    'rest_serialize',
    'rest_validate',
)

EntityType = t.TypeVar('EntityType', bound=Entity)


class RestApiModel(AiidaBaseModel):
    """Base for the models the REST API serves."""


def _fields(cls: type[t.Any]) -> dict[str, RestApiField]:
    """Return this layer's view of every declaration, as the declarations themselves state it."""
    return {name: declaration.rest_api for name, declaration in cls._field_declarations.items()}


def read_only_fields(cls: type[t.Any]) -> frozenset[str]:
    """Return the fields of an ORM class that a client may not write."""
    return frozenset({name for name, field in _fields(cls).items() if field.read_only})


def build_rest_read_model(cls: type[t.Any]) -> type[AiidaBaseModel]:
    """Return the model class a client reads an entity as.

    Public within this layer because the model *class* is what a JSON schema and the API docs
    come from, not only what a response is built with.
    """
    return build_model(f'{cls.__name__}Read', cls._field_declarations, _fields(cls), base=RestApiModel)


def build_rest_write_model(cls: type[t.Any]) -> type[AiidaBaseModel]:
    """Return the model class for the fields a client may set."""
    fields = dict(_fields(cls))
    for name in read_only_fields(cls):
        fields[name] = fields[name].replace(exclude=True)
    return build_model(f'{cls.__name__}Write', cls._field_declarations, fields, base=RestApiModel)


def rest_serialize(entity: Entity) -> dict[str, t.Any]:
    """Return what a ``GET`` returns: ORM object -> model -> payload."""
    cls = type(entity)
    model = build_rest_read_model(cls)(**published_values(entity, _fields(cls)))
    return model.model_dump()


def rest_validate(cls: type[t.Any], payload: Mapping[str, t.Any]) -> AiidaBaseModel:
    """Return the validated body of a ``PUT``, without constructing anything.

    A ``PUT`` replaces the values of an entity that already exists, so it never reaches
    ``__init__``. Whatever a declaration states in its ``validator`` runs here instead.
    """
    return build_rest_write_model(cls).model_validate(payload)


def rest_deserialize(cls: type[EntityType], payload: Mapping[str, t.Any]) -> EntityType:
    """Return what a ``POST`` constructs: payload -> validated model -> ORM object.

    The class is passed rather than read from the payload, as in the CLI: the route already names
    the entity type, so nothing is in question by the time this is reached.
    """
    model = build_rest_write_model(cls).model_validate(payload)
    from_rest_model = getattr(cls, 'from_rest_model', None)
    return from_rest_model(model) if from_rest_model is not None else cls.from_model(model)
