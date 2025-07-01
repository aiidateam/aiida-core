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
from aiida.common.exceptions import ValidationError

# Direct URL to the database.json file

__all__ = (
    'get_computers_table',
    'handle_computer_configuration',
    'process_template_variables',
    'replace_template_var',
    'apply_computer_config',
    'fetch_resource_registry_data',
    'get_available_codes',
    'get_computer_configure_config',
    'get_computer_setup_config',
    'interactive_config_handling',
    'interactive_computer_selector',
    'list_computer_variants',
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


def interactive_computer_selector(registry_data: t.Dict[str, t.Any]) -> t.Optional[t.Tuple[str, str]]:
    """Interactively prompt user to select a system and variant."""
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

                # Now select variant
                variants = list_computer_variants(registry_data, selected_system)

                echo.echo_info(f'\n⚙️  Available variants for {selected_system}:')
                echo.echo('=' * 50)

                for i, variant in enumerate(variants, 1):
                    # Show description if available
                    try:
                        setup_config = get_computer_setup_config(registry_data, selected_system, variant)
                        description = setup_config.get('description', 'No description available')
                        echo.echo(f'{i:2d}. {variant}')
                        echo.echo(f'     {description}')
                    except:
                        echo.echo(f'{i:2d}. {variant}')

                echo.echo(f'{len(variants) + 1:2d}. Back to system selection')
                echo.echo('=' * 50)

                while True:
                    try:
                        variant_choice = click.prompt(f'\nSelect a variant (1-{len(variants) + 1})', type=int)

                        if variant_choice == len(variants) + 1:
                            break  # Go back to system selection
                        elif 1 <= variant_choice <= len(variants):
                            selected_variant = variants[variant_choice - 1]
                            echo.echo_success(f'Selected: {selected_system} / {selected_variant}')
                            return (selected_system, selected_variant)
                        else:
                            echo.echo_error(f'Invalid choice. Please enter a number between 1 and {len(variants) + 1}.')

                    except click.Abort:
                        echo.echo_info('Selection cancelled.')
                        return None

            else:
                echo.echo_error(f'Invalid choice. Please enter a number between 1 and {len(computers) + 1}.')

        except click.Abort:
            echo.echo_info('Selection cancelled.')
            return None



#
def interactive_config_handling(computer_name: str, variant: str) -> t.Optional[bool]:
    """Ask user whether to apply computer configuration directly or save to file."""
    echo.echo_info(f'\nConfiguration found for {computer_name} / {variant}')
    echo.echo('What would you like to do?')
    echo.echo('1. Setup computer in AiiDA directly')
    echo.echo('2. Save configuration to YAML files')
    echo.echo('3. Cancel')

    while True:
        try:
            choice = click.prompt('Select an option (1-3)', type=int)

            if choice == 1:
                return True  # Apply directly
            elif choice == 2:
                return False  # Save to file
            elif choice == 3:
                return None  # Cancel
            else:
                echo.echo_error('Invalid choice. Please enter 1, 2, or 3.')

        except click.Abort:
            return None


# NOTE: Check if this function necessary or functionality already exists, e.g.,
# via pydantic serialization
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

    echo.echo_success(f'Configuration saved to {filepath}')
    return filepath


def complete_computer_spec_with_defaults(setup_config: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
    """
    Complete a computer specification by adding missing optional fields with defaults.

    Args:
        setup_config: The initial computer setup configuration from the registry

    Returns:
        A complete configuration dictionary with all fields needed by ComputerBuilder
    """
    # Define default values for optional fields that ComputerBuilder expects
    defaults = {
        'description': '',  # Default empty description
        'use_double_quotes': False,
        'prepend_text': '',
        'append_text': '',
        'work_dir': '/scratch/{username}/aiida/',
        'shebang': '/#!/bin/bash',
        'mpirun_command': 'mpirun -np {tot_num_mpiprocs}',
        'mpiprocs_per_machine': None,
        'default_memory_per_machine': None,
    }

    # Create a copy to avoid modifying the original
    complete_config = setup_config.copy()

    # Add defaults for any missing optional fields
    missing_fields = []
    for field, default_value in defaults.items():
        if field not in complete_config:
            complete_config[field] = default_value
            missing_fields.append(field)

    # Log what defaults were applied
    if missing_fields:
        echo.echo_info(f'Applied defaults for missing fields: {", ".join(missing_fields)}')

    return complete_config


def apply_computer_config(setup_config: t.Dict[str, t.Any], configure_config: t.Dict[str, t.Any]) -> bool:
    """Apply computer configuration directly to AiiDA."""
    from aiida.orm.utils.builders.computer import ComputerBuilder

    try:
        # Complete the setup configuration with defaults
        complete_setup_config = complete_computer_spec_with_defaults(setup_config)

        # Create computer using ComputerBuilder
        echo.echo_info('Creating computer...')
        computer_builder = ComputerBuilder(**complete_setup_config)
        computer = computer_builder.new()
        computer.store()

        echo.echo_success(f"Computer '{computer.label}' created successfully")

        # Configure the computer for the current user
        # TODO: Check if the configure options/default are fine
        if configure_config:
            echo.echo_info('Configuring computer for current user...')
            try:
                from aiida.orm import User

                user = User.collection.get_default()

                authinfo = computer.configure(user=user, **configure_config)
                echo.echo_success(f"Computer '{computer.label}' configured successfully for user '{user.email}'")

            except Exception as e:
                echo.echo_warning(f'Computer created but configuration failed: {e}')
                echo.echo_info('You can configure it manually with:')
                echo.echo_info(
                    f'  verdi computer configure {complete_setup_config.get("transport", "core.ssh")} {computer.label}'
                )

        return True

    except ComputerBuilder.ComputerValidationError as e:
        echo.echo_critical(f'Computer validation error: {e}')
        return False
    except ValidationError as e:
        echo.echo_critical(f'Validation error: {e}')
        return False
    except Exception as e:
        echo.echo_critical(f'Unexpected error: {e}')
        return False


def get_computers_table(registry_data) -> t.List[t.List]:
    """Print a formatted table of computer systems."""

    table = []
    systems = list(registry_data.keys())
    variants = []
    hostnames = []
    codes = []

    for computer_key, computer_data in registry_data.items():
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
        usage_examples = _get_template_usage_examples(processed_config, var_name)
        if usage_examples:
            echo.echo(f"Template variable: {{{{ {var_name} }}}}")
            echo.echo('Used in:')
            for example in usage_examples:
                echo.echo(f'  {example}')

        try:
            value = click.prompt(f"Enter value for '{var_name}'", type=str)
            var_values[var_name] = value
            echo.echo('='*40)

        except click.Abort:
            return None

    # Replace all template variables with user values
    for var_name, value in var_values.items():
        _replace_template_var(processed_config, var_name, value)

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
                _find_template_variables(item, template_vars)

    return template_vars


def _get_template_usage_examples(obj, var_name, examples=None, path=''):
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
                _get_template_usage_examples(value, var_name, examples, current_path)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            current_path = f'{path}[{i}]'
            if isinstance(item, str) and template_pattern in item:
                examples.append(f'{current_path}: {item}')
            elif isinstance(item, (dict, list)):
                _get_template_usage_examples(item, var_name, examples, current_path)

    return examples


def _replace_template_var(obj, var_name, value):
    """Recursively replace template variables in a nested dictionary/list."""
    template_pattern = f'{{{{ {var_name} }}}}'

    if isinstance(obj, dict):
        for key, val in obj.items():
            if isinstance(val, str) and template_pattern in val:
                obj[key] = val.replace(template_pattern, str(value))
            elif isinstance(val, (dict, list)):
                _replace_template_var(val, var_name, value)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, str) and template_pattern in item:
                obj[i] = item.replace(template_pattern, str(value))
            elif isinstance(item, (dict, list)):
                _replace_template_var(item, var_name, value)


def handle_computer_configuration(registry_data, computer_name, variant):
    """Handle the configuration of a computer from the registry."""
    setup_config = get_computer_setup_config(registry_data, computer_name, variant)
    configure_config = get_computer_configure_config(registry_data, computer_name, variant)

    # Process template variables
    setup_config = process_template_variables(setup_config)
    configure_config = process_template_variables(configure_config)

    # Decide what to do with the configuration
    apply_config = interactive_config_handling(computer_name, variant)
    if apply_config is None:
        return

    if apply_config:
        # TODO: Check here if a computer with the same label already exists.
        success = apply_computer_config(setup_config, configure_config)
    else:
        setup_file = save_config_to_file(setup_config, 'setup', computer_name, variant)
        configure_file = save_config_to_file(configure_config, 'configure', computer_name, variant)

        echo.echo_info('\nTo apply these configurations, run:')
        echo.echo_info(f'  verdi computer setup --config {setup_file}')
        echo.echo_info(
            f'  verdi computer configure {setup_config.get("transport", "core.ssh")} {setup_config["label"]} --config {configure_file}'
        )
