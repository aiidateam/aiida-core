###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utilities for loading and processing Jinja2-templated YAML configuration files."""

from __future__ import annotations

import dataclasses
import typing as t

import click

_URL_SCHEMES: t.Final = ('http://', 'https://')

TemplateValues: t.TypeAlias = t.Mapping[str, t.Any]
"""Values for a configuration file's template variables, keyed by variable name."""


@dataclasses.dataclass(frozen=True)
class _TemplateVariable:
    """A template variable to ask the user for.

    Built by :meth:`from_metadata` from one entry of a configuration file's ``metadata.template_variables`` section.
    Every field of such an entry is optional, so normalising it here keeps the fallbacks in one place rather than on
    every lookup in the prompting loop.
    """

    name: str
    key_display: str
    description: str
    default: str | None = None
    choices: tuple[str, ...] = ()

    @classmethod
    def from_metadata(cls, name: str, spec: t.Mapping[str, t.Any]) -> _TemplateVariable:
        """Build from one ``metadata.template_variables`` entry, or from ``{}`` for a variable nothing describes.

        :param name: the variable name as it appears in the template.
        :param spec: the entry describing it, empty when the file declares none.
        """
        default = spec.get('default')
        return cls(
            name=name,
            key_display=spec.get('key_display') or name,
            description=spec.get('description') or f'Value for {name}',
            # Rendering substitutes text, so a numeric YAML default must not reach ``click.prompt`` as an ``int``:
            # it would infer the type from it and hand back an ``int``.
            default=None if default is None else str(default),
            # The registry marks a variable whose value is constrained with ``type: list`` beside its ``options``.
            choices=tuple(str(option) for option in spec.get('options') or ()) if spec.get('type') == 'list' else (),
        )


def _template_variable_specs(metadata: t.Any) -> t.Mapping[str, t.Mapping[str, t.Any]]:
    """Validate and return a configuration file's ``metadata.template_variables`` section.

    :param metadata: the file's ``metadata`` section, which is whatever the YAML happened to contain.
    :return: the section, empty when the file describes no variable.
    :raises click.BadParameter: if the section, or any entry in it, is not a mapping.
    """
    if not isinstance(metadata, dict):
        msg = f'The `metadata` section must be a mapping, got {type(metadata).__name__}'
        raise click.BadParameter(msg)

    specs = metadata.get('template_variables') or {}
    if not isinstance(specs, dict):
        msg = f'`metadata.template_variables` must be a mapping, got {type(specs).__name__}'
        raise click.BadParameter(msg)

    for name, spec in specs.items():
        if not isinstance(spec, dict):
            msg = f'`metadata.template_variables.{name}` must be a mapping, got {type(spec).__name__}'
            raise click.BadParameter(msg)

    return specs


def _prompt_for_template_variables(variables: t.Sequence[_TemplateVariable]) -> dict[str, str]:
    """Interactively prompt for the value of each variable."""
    from aiida.cmdline.utils import echo

    values: dict[str, str] = {}

    echo.echo_report('Template variables detected. Please provide values:')
    echo.echo('')

    for variable in variables:
        echo.echo(f'{click.style(variable.key_display, fg="yellow")}')
        echo.echo(f'  {variable.description}')

        prompt_type: click.ParamType = click.Choice(variable.choices) if variable.choices else click.STRING
        values[variable.name] = click.prompt(
            '  Enter value',
            type=prompt_type,
            default=variable.default,
            show_default=variable.default is not None,
        )

        echo.echo('')

    return values


def _detect_template_variables(template_content: str) -> list[str]:
    """Detect undeclared Jinja2 variables in template content, in alphabetical order."""
    from jinja2 import meta
    from jinja2.sandbox import SandboxedEnvironment

    ast = SandboxedEnvironment().parse(template_content)
    # ``find_undeclared_variables`` returns a set, whose iteration order varies between processes.
    return sorted(meta.find_undeclared_variables(ast))


def _render_template(content: str, template_values: TemplateValues) -> dict[str, t.Any]:
    """Render a Jinja2 template string with the given values and parse as YAML."""
    import yaml
    from jinja2 import StrictUndefined, UndefinedError
    from jinja2.exceptions import SecurityError
    from jinja2.sandbox import SandboxedEnvironment

    # Configuration files are routinely fetched from a URL, so the template is untrusted input. A plain
    # ``jinja2.Environment`` grants a template Python attribute access, which is enough to execute code.
    env = SandboxedEnvironment(undefined=StrictUndefined)
    try:
        rendered = env.from_string(content).render(**template_values)
    except UndefinedError as exc:
        msg = f'Missing template variable: {exc}'
        raise click.BadParameter(msg) from exc
    except SecurityError as exc:
        msg = f'The template tried to perform an operation that is not allowed: {exc}'
        raise click.BadParameter(msg) from exc

    try:
        config = yaml.safe_load(rendered)
    except yaml.YAMLError as exc:
        msg = f'Invalid YAML after template rendering: {exc}'
        raise click.BadParameter(msg) from exc

    if not isinstance(config, dict):
        msg = f'Expected a YAML mapping after template rendering, got {type(config).__name__}'
        raise click.BadParameter(msg)

    config.pop('metadata', None)
    return config


def _load_content(file_path_or_url: str) -> str:
    """Load raw content from a local file path or URL."""
    if file_path_or_url.startswith(_URL_SCHEMES):
        import requests

        try:
            response = requests.get(file_path_or_url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            msg = f'Failed to fetch URL {file_path_or_url}: {exc}'
            raise click.BadParameter(msg) from exc
        return response.text

    try:
        with open(file_path_or_url, encoding='utf-8') as fhandle:
            return fhandle.read()
    except OSError as exc:
        msg = f'Failed to read file {file_path_or_url}: {exc}'
        raise click.BadParameter(msg) from exc


def process_template_content(
    content: str,
    *,
    interactive: bool = True,
    template_vars: TemplateValues | None = None,
) -> dict[str, t.Any]:
    """Process raw YAML content that may contain Jinja2 template placeholders.

    Values given in ``template_vars`` take precedence; in interactive mode the remaining placeholders are prompted
    for, using the descriptions in the ``metadata.template_variables`` section where the content provides them.

    :param content: raw YAML content, optionally containing Jinja2 placeholders.
    :param interactive: whether placeholders without a value may be prompted for.
    :param template_vars: values for template variables, keyed by variable name.
    :return: the configuration with placeholders substituted and the ``metadata`` section stripped.
    :raises click.BadParameter: if the content is not a YAML mapping, or if any placeholder is left without a value.
    """
    import yaml

    try:
        full_config = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        msg = f'Invalid YAML: {exc}'
        raise click.BadParameter(msg) from exc

    if not isinstance(full_config, dict):
        msg = f'Expected a YAML mapping, got {type(full_config).__name__}'
        raise click.BadParameter(msg)

    metadata = full_config.pop('metadata', {})
    detected_vars = _detect_template_variables(content)

    if not detected_vars:
        return full_config

    # Only validated once a placeholder actually needs describing, so a plain config whose ``metadata`` holds
    # something unexpected keeps being stripped and accepted as before.
    specs = _template_variable_specs(metadata)
    values: dict[str, t.Any] = dict(template_vars) if template_vars is not None else {}
    missing = [name for name in detected_vars if name not in values]

    if missing and interactive:
        variables = [_TemplateVariable.from_metadata(name, specs.get(name) or {}) for name in missing]
        values.update(_prompt_for_template_variables(variables))
        missing = [name for name in detected_vars if name not in values]

    if missing:
        msg = (
            f'No value provided for the template variables: {", ".join(missing)}. '
            'Provide them with --template-vars (inline JSON, a local YAML/JSON file path, or a URL).'
        )
        raise click.BadParameter(msg)

    return _render_template(content, values)


def parse_template_vars(value: str) -> dict[str, t.Any]:
    """Parse template variables from a file path, URL, or inline JSON string.

    Resolution order: local file path (if it exists) -> URL -> JSON string.
    Files and URLs may be YAML or JSON (``yaml.safe_load`` handles both).
    """
    import json
    import pathlib

    import yaml

    def _ensure_mapping(parsed: t.Any, source: str) -> dict[str, t.Any]:
        if not isinstance(parsed, dict):
            msg = f'{source} must contain a YAML/JSON mapping, got {type(parsed).__name__}'
            raise click.BadParameter(msg)
        # These become keyword arguments to the Jinja2 render, which accepts nothing but strings. YAML turns an
        # unquoted `1:` or `true:` into an int or a bool, so catch it here rather than as a ``TypeError`` later.
        non_strings = sorted(repr(key) for key in parsed if not isinstance(key, str))
        if non_strings:
            msg = (
                f'{source} must use string keys for the variable names, but {", ".join(non_strings)} '
                f'{"is" if len(non_strings) == 1 else "are"} not a string. Quote them in the file.'
            )
            raise click.BadParameter(msg)
        return parsed

    path = pathlib.Path(value)
    if path.is_file():
        try:
            parsed = yaml.safe_load(path.read_text(encoding='utf-8'))
        except yaml.YAMLError as exc:
            msg = f'Invalid YAML/JSON in template-vars file {value}: {exc}'
            raise click.BadParameter(msg) from exc
        return _ensure_mapping(parsed, f'Template-vars file {value}')

    if value.startswith(_URL_SCHEMES):
        content = _load_content(value)
        try:
            parsed = yaml.safe_load(content)
        except yaml.YAMLError as exc:
            msg = f'Invalid YAML/JSON from template-vars URL: {exc}'
            raise click.BadParameter(msg) from exc
        return _ensure_mapping(parsed, 'Template-vars URL')

    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        # A mistyped path lands here, and "invalid JSON" on its own would send the user looking in the
        # wrong place, so name all three forms that are accepted.
        msg = (
            f'`{value}` is not an existing file, a URL, or a valid inline JSON mapping. '
            f'Parsing it as inline JSON failed with: {exc}'
        )
        raise click.BadParameter(msg) from exc
    return _ensure_mapping(parsed, '--template-vars JSON')
