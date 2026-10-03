from __future__ import annotations

import typing as t

from aiida.orm.cli.entity import EntityCliCreateSpec
from aiida.orm.cli.utils import CliField
from aiida.orm.decorators.attributes import NodeAttribute, iter_attributes

if t.TYPE_CHECKING:
    from aiida.orm import Node
    from aiida.orm.decorators.base import BaseField


class NodeCliCreateSpec(EntityCliCreateSpec):
    """CLI creation specification backed by a Node create model."""

    def __init__(self, entity_type: type[Node]) -> None:
        self.entity_type = entity_type

    def _set_model_value(
        self,
        model_values: dict[str, t.Any],
        name: str,
        field: BaseField,
        value: t.Any,
    ) -> None:
        """Set a CLI field value on the node model input."""
        if isinstance(field, NodeAttribute):
            attributes = model_values.setdefault('attributes', {})
            attributes[name] = value
        else:
            super()._set_model_value(model_values, name, field, value)

    def _iter_fields(self) -> t.Iterator[CliField]:
        """Yield all CLI-exposed fields in their flat external namespace."""
        yield from super()._iter_fields()

        attributes_model = self.entity_type.models._create_attributes

        for name, attribute in iter_attributes(self.entity_type).items():
            if attribute.cli_exclude:
                continue

            model_field = attributes_model.model_fields.get(name)

            if model_field is None:
                continue

            yield CliField(
                name=name,
                field=attribute,
                model_field=model_field,
            )
