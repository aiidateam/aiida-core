###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utilities for loading and processing Jinja2-templated YAML configuration files.

This enables using YAML config files from the ``aiida-resource-registry`` (which contain
Jinja2 placeholders and a ``metadata`` section) directly with ``verdi computer setup --config``
and similar commands.
"""

from __future__ import annotations

import typing as t

import click
import yaml
from jinja2 import BaseLoader, Environment, StrictUndefined, UndefinedError, meta

from aiida.cmdline.utils import echo

__all__ = ('load_and_process_template',)


def _prompt_for_template_variables(template_variables: dict[str, t.Any]) -> dict[str, str]:
    """Interactively prompt for template variable values based on metadata definitions.

    :param template_variables: mapping of variable names to their metadata (key_display, description,
        type, default, options).
    :return: mapping of variable names to user-provided values.
    """
    values: dict[str, str] = {}

    echo.echo_report('Template variables detected. Please provide values:')
    echo.echo('')

    for var_name, var_config in template_variables.items():
        key_display = var_config.get('key_display', var_name)
        description = var_config.get('description', f'Value for {var_name}')
        var_type = var_config.get('type', 'text')
        default = var_config.get('default')
        options = var_config.get('options', [])

        echo.echo(f'{click.style(key_display, fg="yellow")}')
        echo.echo(f'  {description}')

        if var_type == 'list' and options:
            echo.echo(f'  Options: {", ".join(options)}')
            while True:
                value = click.prompt('  Enter value', default=default, show_default=default is not None)
                if value in options:
                    values[var_name] = value
                    break
                echo.echo_error(f'Invalid option. Please choose from: {", ".join(options)}')
        else:
            value = click.prompt('  Enter value', default=default, show_default=default is not None)
            values[var_name] = value

        echo.echo('')

    return values


def _detect_template_variables(template_content: str) -> list[str]:
    """Detect undeclared Jinja2 variables in template content.

    :param template_content: raw template string.
    :return: list of undeclared variable names.
    """
    env = Environment(loader=BaseLoader())
    ast = env.parse(template_content)
    return list(meta.find_undeclared_variables(ast))


def _render_template(content: str, template_values: dict[str, str]) -> dict[str, t.Any]:
    """Render a Jinja2 template string with the given values and parse the result as YAML.

    :param content: raw Jinja2 template content.
    :param template_values: variable values to substitute.
    :return: parsed YAML config dict (with ``metadata`` removed if present).
    :raises click.BadParameter: if a template variable is missing or the rendered YAML is invalid.
    """
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
    """Load raw content from a local file path or URL.

    :param file_path_or_url: local path or ``http(s)://`` URL.
    :return: file content as string.
    :raises click.BadParameter: on I/O or network errors.
    """
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

    This is the core processing pipeline: parse YAML, detect template variables,
    resolve them (interactively or from ``template_vars``), render, and return
    the final config dict with the ``metadata`` section stripped.

    :param content: raw YAML content (possibly with Jinja2 placeholders).
    :param interactive: if ``True``, prompt the user for missing template variable values.
    :param template_vars: pre-supplied template variable values (used in non-interactive mode).
    :return: resolved config dict suitable for passing to a ``verdi`` command's ``default_map``.
    :raises click.BadParameter: on parse errors or missing template variables.
    """
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


def load_and_process_template(
    content_or_path: str,
    *,
    interactive: bool = True,
    template_vars: dict[str, t.Any] | None = None,
    is_content: bool = False,
) -> dict[str, t.Any]:
    """Load and process a (possibly templated) YAML configuration.

    Accepts either raw YAML content or a file path / URL. When ``is_content`` is ``False``
    (the default), ``content_or_path`` is treated as a file path or URL and loaded first.
    When ``is_content`` is ``True``, it is treated as raw YAML content directly.

    :param content_or_path: raw YAML content string, or a local file path / URL.
    :param interactive: if ``True``, prompt the user for missing template variable values.
    :param template_vars: pre-supplied template variable values (used in non-interactive mode).
    :param is_content: if ``True``, treat ``content_or_path`` as raw YAML content.
    :return: resolved config dict suitable for passing to a ``verdi`` command's ``default_map``.
    :raises click.BadParameter: on parse errors or missing template variables.
    """
    content = content_or_path if is_content else _load_content(content_or_path)
    return _process_content(content, interactive=interactive, template_vars=template_vars)
