from __future__ import annotations

import json
import typing as t

from aiida.cmdline.spec import CliParameter
from aiida.orm.cli.entity import EntityCliCreateSpec
from aiida.orm.cli.utils import CliField, CliFieldInfo
from aiida.orm.decorators.attributes import NodeAttribute, iter_attributes
from aiida.orm.decorators.repo import RepoFiles, iter_repo_sources

if t.TYPE_CHECKING:
    from click import Context

    from aiida.orm import Node
    from aiida.orm.decorators.base import BaseField


class NodeCliCreateSpec(EntityCliCreateSpec):
    """CLI creation specification backed by a Node create model."""

    entity_type: type[Node]

    def __init__(self, entity_type: type[Node]) -> None:
        self.entity_type = entity_type

    def parameters(self) -> list[CliParameter]:
        """Return ordinary fields and repository-source input forms."""
        parameters = super().parameters()
        existing_names = {parameter.name for parameter in parameters}

        for source in iter_repo_sources(self.entity_type).values():
            for cli_input in source.cli_inputs:
                if cli_input.name in existing_names:
                    msg = f'duplicate CLI parameter name `{cli_input.name}`'
                    raise ValueError(msg)

                existing_names.add(cli_input.name)
                cli_info = cli_input.cli_field_info or CliFieldInfo()
                prompt: str | bool = cli_info.prompt if cli_info.prompt is not None else source.name.title()

                if source.interactive_collector is not None:
                    prompt = False

                annotation = cli_input.annotation
                if annotation is None:
                    if cli_input.adapter is None:
                        msg = f'CLI input `{cli_input.name}` has no Click type'
                        raise RuntimeError(msg)
                    annotation = cli_input.adapter.cli_type

                parameters.append(
                    CliParameter(
                        name=cli_input.name,
                        annotation=annotation,
                        required=cli_input.required,
                        default=() if cli_input.multiple else None,
                        prompt=prompt,
                        help=cli_info.help or (source.__doc__ or '').strip().split('\n')[0],
                        priority=cli_info.priority,
                        short_name=cli_info.short_name,
                        option_cls=cli_info.option_cls,
                        multiple=cli_input.multiple,
                        nargs=cli_input.nargs,
                    )
                )

        if self.entity_type._cli_expose_extra_attributes:
            if 'attribute' in existing_names:
                raise ValueError('`attribute` is reserved for additional Node attributes')

            parameters.append(
                CliParameter(
                    name='attribute',
                    annotation=str,
                    required=False,
                    default=(),
                    prompt=False,
                    help='Set an additional Node attribute using a key and JSON value. Can be repeated.',
                    short_name='-A',
                    multiple=True,
                    nargs=2,
                )
            )

        return parameters

    def collect_interactive(
        self,
        ctx: Context,
        values: dict[str, t.Any],
        *,
        non_interactive: bool,
    ) -> dict[str, t.Any]:
        """Collect grouped repository inputs when the user has supplied none on the command line."""
        if non_interactive:
            return values

        values = dict(values)

        for source in iter_repo_sources(self.entity_type).values():
            collector = source.interactive_collector
            if collector is None:
                continue

            source_values = [values.get(cli_input.name) for cli_input in source.cli_inputs]
            if any(value not in (None, (), []) for value in source_values):
                continue

            collected = collector()
            input_names = {cli_input.name for cli_input in source.cli_inputs}
            unexpected = set(collected) - input_names
            if unexpected:
                msg = f'interactive collector for `{source.name}` returned unknown inputs: {sorted(unexpected)}'
                raise ValueError(msg)

            values.update(collected)

        if self.entity_type._cli_expose_extra_attributes and values.get('attribute') in (None, (), []):
            values['attribute'] = self._collect_extra_attributes()

        return values

    def _model_values(self, values: dict[str, t.Any]) -> dict[str, t.Any]:
        """Convert CLI fields and repository-source forms into create-model values."""
        model_values = super()._model_values(values)
        sources = iter_repo_sources(self.entity_type)

        if sources:
            files: RepoFiles = {}

            for source in sources.values():
                for cli_input in source.cli_inputs:
                    value = values.get(cli_input.name)
                    if value is None or value == ():
                        continue

                    entries = value if cli_input.multiple else (value,)
                    for entry in entries:
                        contribution = cli_input.to_files(entry, context=model_values)
                        overlap = files.keys() & contribution.keys()
                        if overlap:
                            msg = f'repository inputs produce duplicate paths: {sorted(overlap)}'
                            raise ValueError(msg)

                        files.update(contribution)

                source.validate_files(files)

            model_values['files'] = files

        extra_attributes = values.get('attribute', ())
        if extra_attributes:
            if not self.entity_type._cli_expose_extra_attributes:
                msg = f'{self.entity_type.__name__} does not accept additional attributes'
                raise ValueError(msg)

            attributes = model_values.setdefault('attributes', {})
            for name, serialized in extra_attributes:
                if not name:
                    raise ValueError('attribute names cannot be empty')

                if name in attributes:
                    msg = f'attribute `{name}` was provided more than once'
                    raise ValueError(msg)

                try:
                    attributes[name] = json.loads(serialized)
                except json.JSONDecodeError as exception:
                    msg = f'attribute `{name}` must be valid JSON: {exception}'
                    raise ValueError(msg) from exception

        return model_values

    @staticmethod
    def _collect_extra_attributes() -> tuple[tuple[str, str], ...]:
        """Prompt for optional additional Node attributes."""
        import click

        attributes: list[tuple[str, str]] = []

        while True:
            action = click.prompt(
                'Add attribute',
                type=click.Choice(('yes', 'done')),
                default='yes',
            )
            if action == 'done':
                break

            name = click.prompt('Key', type=str)
            value = click.prompt('Value (JSON)', type=str)
            attributes.append((name, value))

        return tuple(attributes)

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
