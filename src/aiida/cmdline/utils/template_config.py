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

import typing as t

import click


def _prompt_for_template_variables(template_variables: dict[str, t.Any]) -> dict[str, str]:
    """Interactively prompt for template variable values based on metadata definitions."""
    from aiida.cmdline.utils import echo

    values: dict[str, str] = {}

    echo.echo_report('Template variables detected. Please provide values:')
    echo.echo('')

    for var_name, var_config in template_variables.items():
        key_display = var_config.get('key_display', var_name)
        description = var_config.get('description', f'Value for {var_name}')
        default = var_config.get('default')
        options = var_config.get('options', [])

        echo.echo(f'{click.style(key_display, fg="yellow")}')
        echo.echo(f'  {description}')

        prompt_kwargs: dict[str, t.Any] = {'default': default, 'show_default': default is not None}
        if var_config.get('type') == 'list' and options:
            prompt_kwargs['type'] = click.Choice(options)
        values[var_name] = click.prompt('  Enter value', **prompt_kwargs)

        echo.echo('')

    return values


def _detect_template_variables(template_content: str) -> list[str]:
    """Detect undeclared Jinja2 variables in template content."""
    from jinja2 import BaseLoader, Environment, meta

    env = Environment(loader=BaseLoader())
    ast = env.parse(template_content)
    return list(meta.find_undeclared_variables(ast))


def _render_template(content: str, template_values: dict[str, str]) -> dict[str, t.Any]:
    """Render a Jinja2 template string with the given values and parse as YAML."""
    import yaml
    from jinja2 import BaseLoader, Environment, StrictUndefined, UndefinedError

    env = Environment(loader=BaseLoader(), undefined=StrictUndefined)
    try:
        rendered = env.from_string(content).render(**template_values)
    except UndefinedError as exc:
        msg = f'Missing template variable: {exc}'
        raise click.BadParameter(msg)
    try:
        config = yaml.safe_load(rendered)
    except yaml.YAMLError as exc:
        msg = f'Invalid YAML after template rendering: {exc}'
        raise click.BadParameter(msg)
    if isinstance(config, dict):
        config.pop('metadata', None)
    return config


def _load_content(file_path_or_url: str) -> str:
    """Load raw content from a local file path or URL."""
    if file_path_or_url.startswith(('http://', 'https://')):
        import requests

        try:
            response = requests.get(file_path_or_url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            msg = f'Failed to fetch URL {file_path_or_url}: {exc}'
            raise click.BadParameter(msg)
        return response.text

    try:
        with open(file_path_or_url, encoding='utf-8') as fhandle:
            return fhandle.read()
    except OSError as exc:
        msg = f'Failed to read file {file_path_or_url}: {exc}'
        raise click.BadParameter(msg)


def _process_content(
    content: str,
    *,
    interactive: bool = True,
    template_vars: dict[str, t.Any] | None = None,
) -> dict[str, t.Any]:
    """Process raw YAML content that may contain Jinja2 templates.

    Parses YAML, detects template variables, resolves them (interactively or
    from ``template_vars``), renders, and returns the config dict with the
    ``metadata`` section stripped.
    """
    import yaml

    from aiida.cmdline.utils import echo

    try:
        full_config = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        msg = f'Invalid YAML: {exc}'
        raise click.BadParameter(msg)

    if not isinstance(full_config, dict):
        msg = f'Expected a YAML mapping, got {type(full_config).__name__}'
        raise click.BadParameter(msg)

    metadata = full_config.pop('metadata', {})
    template_variable_defs = metadata.get('template_variables', {})

    detected_vars = _detect_template_variables(content)

    if not detected_vars:
        return full_config

    # Only prompt for variables that are both used in the template and defined in metadata
    vars_to_prompt = {name: cfg for name, cfg in template_variable_defs.items() if name in detected_vars}

    if vars_to_prompt:
        if template_vars:
            template_values = template_vars
        elif interactive:
            template_values = _prompt_for_template_variables(vars_to_prompt)
        else:
            msg = (
                f'Template variables detected ({", ".join(detected_vars)}) but no values provided. '
                'Use --template-vars to provide values in JSON format.'
            )
            raise click.BadParameter(msg)
        return _render_template(content, template_values)

    # Variables detected but none defined in metadata — try to use provided vars or warn
    if template_vars:
        return _render_template(content, template_vars)

    if interactive:
        echo.echo_warning(f'Template variables detected ({", ".join(detected_vars)}) but no metadata found.')
        echo.echo_warning('You may need to provide values manually or the template may not render correctly.')

    return full_config


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
        return parsed

    path = pathlib.Path(value)
    if path.is_file():
        try:
            parsed = yaml.safe_load(path.read_text(encoding='utf-8'))
        except yaml.YAMLError as exc:
            msg = f'Invalid YAML/JSON in template-vars file {value}: {exc}'
            raise click.BadParameter(msg)
        return _ensure_mapping(parsed, f'Template-vars file {value}')

    if value.startswith(('http://', 'https://')):
        content = _load_content(value)
        try:
            parsed = yaml.safe_load(content)
        except yaml.YAMLError as exc:
            msg = f'Invalid YAML/JSON from template-vars URL: {exc}'
            raise click.BadParameter(msg)
        return _ensure_mapping(parsed, 'Template-vars URL')

    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        msg = f'Invalid JSON in --template-vars: {exc}'
        raise click.BadParameter(msg)
    return _ensure_mapping(parsed, '--template-vars JSON')


def load_and_process_template(
    content_or_path: str,
    *,
    interactive: bool = True,
    template_vars: dict[str, t.Any] | None = None,
    is_content: bool = False,
) -> dict[str, t.Any]:
    """Load and process a (possibly templated) YAML configuration.

    :param content_or_path: raw YAML content, local file path, or URL.
    :param is_content: if ``True``, treat ``content_or_path`` as raw YAML content.
    """
    content = content_or_path if is_content else _load_content(content_or_path)
    return _process_content(content, interactive=interactive, template_vars=template_vars)
