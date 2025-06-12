from typing import Any, Dict, List, Optional

import click
import requests
import yaml
from jinja2 import BaseLoader, Environment, meta

from aiida.cmdline.utils import echo


class StringTemplateLoader(BaseLoader):
    """Jinja2 loader that loads templates from strings."""

    def __init__(self, template_string: str):
        self.template_string = template_string

    def get_source(self, environment, template):
        return self.template_string, None, lambda: True


def prompt_for_template_variables(template_variables: Dict[str, Any]) -> Dict[str, Any]:
    """Prompt user for template variables based on metadata definitions."""
    values = {}

    echo.echo_report('Template variables detected. Please provide values:')
    echo.echo('')

    for var_name, var_config in template_variables.items():
        key_display = var_config.get('key_display', var_name)
        description = var_config.get('description', f'Value for {var_name}')
        var_type = var_config.get('type', 'text')
        default = var_config.get('default')
        options = var_config.get('options', [])

        # Display help text
        echo.echo(f'{click.style(key_display, fg="yellow")}')
        echo.echo(f'  {description}')

        if var_type == 'list' and options:
            echo.echo(f'  Options: {", ".join(options)}')
            while True:
                value = click.prompt('  Enter value', default=default, show_default=True if default else False)
                if value in options:
                    values[var_name] = value
                    break
                else:
                    echo.echo_error(f'Invalid option. Please choose from: {", ".join(options)}')
        else:
            value = click.prompt('  Enter value', default=default, show_default=True if default else False)
            values[var_name] = value

        echo.echo('')

    return values


def detect_template_variables(template_content: str) -> List[str]:
    """Detect Jinja2 variables in template content."""
    env = Environment(loader=StringTemplateLoader(template_content))
    ast = env.parse(template_content)
    return list(meta.find_undeclared_variables(ast))


def load_and_process_template(
    file_path_or_url: str, interactive: bool = True, template_vars: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Load and process a template configuration file."""

    # Load content
    if file_path_or_url.startswith(('http://', 'https://')):
        try:
            response = requests.get(file_path_or_url, timeout=10)
            response.raise_for_status()
            content = response.text
        except requests.RequestException as e:
            raise click.BadParameter(f'Failed to fetch URL {file_path_or_url}: {e}')
    else:
        try:
            with open(file_path_or_url, 'r', encoding='utf-8') as f:
                content = f.read()
        except IOError as e:
            raise click.BadParameter(f'Failed to read file {file_path_or_url}: {e}')

    # Parse YAML to get metadata
    try:
        full_config = yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise click.BadParameter(f'Invalid YAML: {e}')

    # Extract metadata and template variables (if they exist)
    metadata = full_config.pop('metadata', {})
    template_variables = metadata.get('template_variables', {})

    # Detect variables that need values
    detected_vars = detect_template_variables(content)

    # If no template variables detected, just return the config
    if not detected_vars:
        return full_config

    # Filter to only prompt for variables that are actually used and defined in metadata
    vars_to_prompt = {var: config for var, config in template_variables.items() if var in detected_vars}

    if vars_to_prompt:
        if interactive:
            # Interactive prompting for template variables
            template_values = prompt_for_template_variables(vars_to_prompt)
        else:
            # Non-interactive mode
            if not template_vars:
                raise click.BadParameter(
                    f'Template variables detected ({", ".join(detected_vars)}) but no values provided. '
                    'Use --template-vars to provide values in JSON format.'
                )
            template_values = template_vars

        # Render the template with provided values
        env = Environment(loader=StringTemplateLoader(content))
        template = env.from_string(content)
        rendered_content = template.render(**template_values)

        # Parse the rendered YAML
        try:
            config = yaml.safe_load(rendered_content)
        except yaml.YAMLError as e:
            raise click.BadParameter(f'Invalid YAML after template rendering: {e}')
    else:
        # Template variables detected but none defined in metadata
        # This could happen with simple Jinja variables like {{ username }}
        if interactive:
            echo.echo_warning(f'Template variables detected ({", ".join(detected_vars)}) but no metadata found.')
            echo.echo_warning('You may need to provide values manually or the template may not render correctly.')

        if template_vars:
            # Try to render with provided vars
            env = Environment(loader=StringTemplateLoader(content))
            template = env.from_string(content)
            rendered_content = template.render(**template_vars)
            try:
                config = yaml.safe_load(rendered_content)
            except yaml.YAMLError as e:
                raise click.BadParameter(f'Invalid YAML after template rendering: {e}')
        else:
            # Return original config and hope for the best
            config = full_config

    # Remove metadata section if it exists
    config.pop('metadata', None)

    return config
