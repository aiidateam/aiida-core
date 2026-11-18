"""CLI-owned projection of the ORM declarations. Private: a user never imports this.

The layer that round-trips: ``verdi computer export`` writes a YAML file and
``verdi computer import`` reads it back, so this is the one place the parsing direction is needed.

Today ``cmd_computer.py`` builds the payload as a dict literal that renames two fields and joins a
third. Each of those is a ``cli_`` option on ``Computer``'s own declarations, and this module only
assembles what the class already states.
"""

from __future__ import annotations

import typing as t
from collections.abc import Mapping

from poc.common._core.pydantic import AiidaBaseModel, build_model, published_values
from poc.orm._core.entities import Entity

__all__ = ('CliModel', 'build_cli_model', 'cli_deserialize', 'cli_serialize')

EntityType = t.TypeVar('EntityType', bound=Entity)


class CliModel(AiidaBaseModel):
    """Base for the models the CLI exports and imports."""


def build_cli_model(cls: type[t.Any]) -> type[AiidaBaseModel]:
    """Return the model class the CLI exports and imports an entity as.

    Public because the model *class* is useful on its own -- it is what a command would generate
    its options and its ``--help`` from, and what a JSON schema would come from.
    """
    return build_model(
        f'{cls.__name__}Cli',
        cls._field_declarations,
        {name: declaration.cli for name, declaration in cls._field_declarations.items()},
        base=CliModel,
    )


def cli_serialize(entity: Entity) -> dict[str, t.Any]:
    """Return what ``verdi <entity> export`` writes: ORM object -> model -> payload."""
    cls = type(entity)
    model = build_cli_model(cls)(
        **published_values(entity, {name: declaration.cli for name, declaration in cls._field_declarations.items()})
    )
    return model.model_dump()


def cli_deserialize(cls: type[EntityType], payload: Mapping[str, t.Any]) -> EntityType:
    """Return what ``verdi <entity> import`` constructs: payload -> validated model -> ORM object.

    The class is passed rather than read from the payload. ``verdi computer import`` is already a
    computer command, so the type is never in question, and the files double as the hand-written
    ``--config`` input to ``verdi computer setup`` -- a required type key would be noise a user
    has to write, and would break every config file that predates it.
    """
    model = build_cli_model(cls).model_validate(payload)
    from_cli_model = getattr(cls, 'from_cli_model', None)
    return from_cli_model(model) if from_cli_model is not None else cls.from_model(model)
