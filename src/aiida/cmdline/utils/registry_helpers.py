"""Helper functions for AiiDA code registry integration."""

import copy
import json
import re
import typing as t
from pathlib import Path

import click
import requests
import yaml

from aiida.cmdline.utils import echo

__all__ = (
    'fetch_resource_registry_data',
    'get_computer_configure_config',
    'get_computer_setup_config',
    'get_computers_table',
    'interactive_computer_selector',
    'interactive_variant_selector',
    'list_computer_variants',
    'process_template_variables',
    'save_config_to_file',
)


def fetch_code_registry_data() -> t.Dict[str, t.Any]:
    """
    Fetch the complete AiiDA code registry database from the published JSON file.
    Converts old format to new format with 'computer' and 'codes' sub-keys.

    Returns:
        Dictionary containing the complete registry database in normalized format
    """
    database_url = 'https://aiidateam.github.io/aiida-code-registry/database_v2_1.json'

    try:
        response = requests.get(database_url, timeout=10)
        response.raise_for_status()
        registry_data = response.json()

        # Convert to new format with 'computer' and 'codes' sub-keys
        categorized_data = {}

        for hostname, host_data in registry_data.items():
            categorized_data[hostname] = {}

            for variant_name, variant_data in host_data.items():
                if variant_name == 'default':
                    # Preserve default variant as-is
                    categorized_data[hostname]['default'] = variant_data
                    continue

                # Initialize new structure for this variant
                categorized_data[hostname][variant_name] = {'computer': {}, 'codes': {}}

                # Separate computer and code configurations
                for key, value in variant_data.items():
                    if key.startswith('computer-'):
                        # Computer configuration (computer-setup, computer-configure)
                        categorized_data[hostname][variant_name]['computer'][key] = value
                    else:
                        # Code configuration
                        categorized_data[hostname][variant_name]['codes'][key] = value

        return categorized_data

    except requests.exceptions.RequestException as e:
        raise click.ClickException(f'Failed to fetch registry data from {database_url}: {e}')
    except json.JSONDecodeError as e:
        raise click.ClickException(f'Failed to parse JSON data: {e}')


def fetch_resource_registry_data() -> t.Dict[str, t.Any]:
    """
    Fetch the complete AiiDA code registry database from the published JSON file.
    Removes metadata sections from the registry data.

    Returns:
        Dictionary containing the complete registry database without metadata
    """
    database_url = 'https://aiidateam.github.io/aiida-resource-registry/database.json'
    try:
        response = requests.get(database_url, timeout=10)
        response.raise_for_status()

        registry_data = response.json()

        # Remove metadata sections recursively
        cleaned_data = remove_metadata_sections(registry_data)

        return cleaned_data

    except requests.exceptions.RequestException as e:
        raise click.ClickException(f'Failed to fetch registry data from {database_url}: {e}')
    except json.JSONDecodeError as e:
        raise click.ClickException(f'Failed to parse JSON data: {e}')


def remove_metadata_sections(registry_data: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
    """
    Remove 'metadata' keys from the registry data structure.

    The metadata appears at a consistent depth:
    hostname → variant → type → item → metadata

    Args:
        data: Registry dictionary

    Returns:
        Dictionary with metadata sections removed
    """
    cleaned = {}

    for hostname, host_data in registry_data.items():
        cleaned[hostname] = {}

        for variant, variant_data in host_data.items():
            if variant == 'default':
                # Keep default value as-is
                cleaned[hostname][variant] = variant_data
                continue

            cleaned[hostname][variant] = {}

            for section_type, section_data in variant_data.items():
                cleaned[hostname][variant][section_type] = {}

                for item_name, item_data in section_data.items():
                    # Copy all item data except metadata
                    cleaned[hostname][variant][section_type][item_name] = {
                        k: v for k, v in item_data.items() if k != 'metadata'
                    }

    return cleaned


def list_computer_variants(registry_data: t.Dict[str, t.Any], computer_name: str) -> t.List[str]:
    """List all available variants for a given system."""
    if computer_name not in registry_data:
        msg = f"Computer '{computer_name}' not found in registry"
        raise ValueError(msg)

    computer_data = registry_data[computer_name]
    variants = [key for key in computer_data.keys() if key != 'default']
    return variants


def get_computer_setup_config(
    registry_data: t.Dict[str, t.Any], computer_name: str, variant: str
) -> t.Dict[str, t.Any]:
    """Get the computer setup configuration for a specific system and variant."""
    if computer_name not in registry_data:
        raise ValueError(f"System '{computer_name}' not found in registry")

    computer_data = registry_data[computer_name]

    if variant not in computer_data:
        available_variants = list_computer_variants(registry_data, computer_name)
        raise ValueError(f"Variant '{variant}' not found for system '{computer_name}'. Available: {available_variants}")

    return computer_data[variant]['computer']['computer-setup']


def get_computer_configure_config(
    registry_data: t.Dict[str, t.Any], computer_name: str, variant: str
) -> t.Dict[str, t.Any]:
    """Get the computer configure configuration for a specific system and variant."""
    if computer_name not in registry_data:
        raise ValueError(f"Computer '{computer_name}' not found in registry")

    computer_data = registry_data[computer_name]

    if variant not in computer_data:
        available_variants = list_computer_variants(registry_data, computer_name)
        raise ValueError(f"Variant '{variant}' not found for system '{computer_name}'. Available: {available_variants}")

    return computer_data[variant]['computer']['computer-configure']


def interactive_computer_selector(registry_data: t.Dict[str, t.Any]) -> t.Optional[str]:
    """Interactively prompt user to select a computer system."""
    computers = list(registry_data.keys())

    if not computers:
        echo.echo_error('No systems found in registry.')
        return None

    echo.echo_info('\n🖥️  Available Computers:')
    echo.echo('=' * 80)

    for i, computer in enumerate(computers, 1):
        default_variant = registry_data[computer].get('default', 'N/A')
        variants = list_computer_variants(registry_data, computer)
        variant_str = ', '.join(variants)
        echo.echo(f'{i:2d}. {computer}')
        echo.echo(f'     Default: {default_variant} | Variants: {variant_str}')

    echo.echo(f'{len(computers) + 1:2d}. Cancel')
    echo.echo('=' * 80)

    while True:
        try:
            choice = click.prompt(f'\nSelect a system (1-{len(computers) + 1})', type=int)

            if choice == len(computers) + 1:
                echo.echo_info('Selection cancelled.')
                return None
            elif 1 <= choice <= len(computers):
                selected_system = computers[choice - 1]
                echo.echo_success(f'Selected computer: {selected_system}')
                return selected_system
            else:
                echo.echo_error(f'Invalid choice. Please enter a number between 1 and {len(computers) + 1}.')

        except click.Abort:
            echo.echo_info('Selection cancelled.')
            return None


def interactive_variant_selector(registry_data: t.Dict[str, t.Any], computer_name: str) -> t.Optional[str]:
    """Interactively prompt user to select a variant for a specific computer."""
    if computer_name not in registry_data:
        echo.echo_error(f"Computer '{computer_name}' not found in registry.")
        return None

    variants = list_computer_variants(registry_data, computer_name)

    if not variants:
        echo.echo_error(f"No variants found for computer '{computer_name}'.")
        return None

    # If only one variant, return it directly (optional: could still prompt for confirmation)
    if len(variants) == 1:
        echo.echo_info(f'Only one variant available for {computer_name}: {variants[0]}')
        if click.confirm(f'Use variant "{variants[0]}"?', default=True):
            return variants[0]
        else:
            return None

    echo.echo_info(f'\n⚙️  Available variants for {computer_name}:')
    echo.echo('=' * 50)

    for i, variant in enumerate(variants, 1):
        # Show description if available
        try:
            setup_config = get_computer_setup_config(registry_data, computer_name, variant)
            description = setup_config.get('description', 'No description available')
            echo.echo(f'{i:2d}. {variant}')
            echo.echo(f'     {description}')
        except Exception:
            echo.echo(f'{i:2d}. {variant}')

    echo.echo(f'{len(variants) + 1:2d}. Cancel')
    echo.echo('=' * 50)

    while True:
        try:
            variant_choice = click.prompt(f'\nSelect a variant (1-{len(variants) + 1})', type=int)

            if variant_choice == len(variants) + 1:
                echo.echo_info('Selection cancelled.')
                return None
            elif 1 <= variant_choice <= len(variants):
                selected_variant = variants[variant_choice - 1]
                echo.echo_success(f'Selected variant: {selected_variant}')
                return selected_variant
            else:
                echo.echo_error(f'Invalid choice. Please enter a number between 1 and {len(variants) + 1}.')

        except click.Abort:
            echo.echo_info('Selection cancelled.')
            return None


def save_config_to_file(config: t.Dict[str, t.Any], config_type: str, computer_name: str, variant: str) -> Path:
    """Save configuration to a YAML file."""
    filename = f'{computer_name.replace(".", "_")}_{variant}_{config_type}.yaml'
    filepath = Path.cwd() / filename

    # Handle file existence
    if filepath.exists():
        if not click.confirm(f'File {filename} already exists. Overwrite?'):
            counter = 1
            while True:
                new_filename = f'{computer_name.replace(".", "_")}_{variant}_{config_type}_{counter}.yaml'
                new_filepath = Path.cwd() / new_filename
                if not new_filepath.exists():
                    filepath = new_filepath
                    break
                counter += 1

    with filepath.open('w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    echo.echo_success(f'{config_type} configuration saved to {filepath}')
    return filepath


def get_computers_table(registry_data) -> t.List[t.List]:
    """Print a formatted table of computer systems."""

    table = []
    systems = list(registry_data.keys())
    variants = []
    hostnames = []
    codes = []

    for computer_data in registry_data.values():
        default_variant = computer_data['default']
        variant_list = [key for key in computer_data.keys() if key not in ('default', default_variant)]
        variant_str = f'{default_variant} (default)'
        if len(variant_list) > 0:
            variant_str += ', ' + ', '.join(variant_list)
        variants.append(variant_str)
        default_config = computer_data[default_variant]
        default_hostname = default_config['computer']['computer-setup']['hostname']
        default_codes = [
            code.removesuffix(f'-{default_variant}')
            for code in default_config['codes']
            if code.endswith(f'-{default_variant}')
        ]
        if not default_codes:
            default_codes = [code for code in default_config['codes']]

        hostnames.append(default_hostname)
        codes.append(', '.join(default_codes))

    table = list(zip(systems, variants, hostnames, codes))

    return table


def process_template_variables(config):
    """Process template variables in configuration by scanning for Jinja2 templates."""
    processed_config = copy.deepcopy(config)

    # Find all template variables in the config
    template_vars = find_template_variables(processed_config)

    if not template_vars:
        return processed_config

    echo.echo_report(f'Found {len(template_vars)} template variable(s) to configure:')

    # Prompt user for each template variable
    var_values = {}
    for var_name in template_vars:
        echo.echo_info(f'\nTemplate variable: {var_name}')

        # Show where this variable is used
        usage_examples = get_template_usage_examples(processed_config, var_name)
        if usage_examples:
            echo.echo(f'Template variable: {{{{ {var_name} }}}}')
            echo.echo('Used in:')
            for example in usage_examples:
                echo.echo(f'  {example}')

        try:
            value = click.prompt(f"Enter value for '{var_name}'", type=str)
            var_values[var_name] = value
            echo.echo('=' * 40)

        except click.Abort:
            return None

    # Replace all template variables with user values
    for var_name, value in var_values.items():
        replace_template_var(processed_config, var_name, value)

    return processed_config


def find_template_variables(obj, template_vars=None):
    """Recursively find all Jinja2 template variables in a nested structure."""
    if template_vars is None:
        template_vars = set()

    # Regex pattern to match {{ variable_name }}
    pattern = r'\{\{\s*([^}]+)\s*\}\}'

    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, str):
                matches = re.findall(pattern, value)
                for match in matches:
                    # Clean up the variable name (remove extra spaces)
                    var_name = match.strip()
                    template_vars.add(var_name)
            elif isinstance(value, (dict, list)):
                find_template_variables(value, template_vars)
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, str):
                matches = re.findall(pattern, item)
                for match in matches:
                    var_name = match.strip()
                    template_vars.add(var_name)
            elif isinstance(item, (dict, list)):
                find_template_variables(item, template_vars)

    return template_vars


def get_template_usage_examples(obj, var_name, examples=None, path=''):
    """Get examples of where a template variable is used."""
    if examples is None:
        examples = []

    template_pattern = f'{{{{ {var_name} }}}}'

    if isinstance(obj, dict):
        for key, value in obj.items():
            current_path = f'{path}.{key}' if path else key
            if isinstance(value, str) and template_pattern in value:
                examples.append(f'{current_path}: {value}')
            elif isinstance(value, (dict, list)):
                get_template_usage_examples(value, var_name, examples, current_path)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            current_path = f'{path}[{i}]'
            if isinstance(item, str) and template_pattern in item:
                examples.append(f'{current_path}: {item}')
            elif isinstance(item, (dict, list)):
                get_template_usage_examples(item, var_name, examples, current_path)

    return examples


def replace_template_var(obj, var_name, value):
    """Recursively replace template variables in a nested dictionary/list."""
    template_pattern = f'{{{{ {var_name} }}}}'

    if isinstance(obj, dict):
        for key, val in obj.items():
            if isinstance(val, str) and template_pattern in val:
                obj[key] = val.replace(template_pattern, str(value))
            elif isinstance(val, (dict, list)):
                replace_template_var(val, var_name, value)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, str) and template_pattern in item:
                obj[i] = item.replace(template_pattern, str(value))
            elif isinstance(item, (dict, list)):
                replace_template_var(item, var_name, value)
