"""Helper functions for AiiDA code registry integration."""

import json
import tempfile
import typing as t
from pathlib import Path

import click
import requests
import yaml

from aiida.cmdline.utils import echo
from aiida.common.exceptions import EntryPointError, ValidationError

# Direct URL to the database.json file

__all__ = (
    '_handle_computer_configuration',
    '_get_computers_table',
    '_process_template_variables',
    '_replace_template_var',
    'apply_computer_config',
    'fetch_resource_registry_data',
    'find_codes_by_name',
    'get_available_codes',
    'get_computer_configure_config',
    'get_computer_setup_config',
    'interactive_code_selector',
    'interactive_computer_selector',
    'interactive_system_selector',
    'list_available_systems',
    'list_system_variants',
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
                    # Preserve default partition as-is
                    categorized_data[hostname]['default'] = variant_data
                    continue

                # Initialize new structure for this partition
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


def remove_metadata_sections(data: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
    """
    Recursively remove 'metadata' keys from nested dictionaries.

    Args:
        data: Dictionary that may contain metadata sections

    Returns:
        Dictionary with metadata sections removed
    """
    if not isinstance(data, dict):
        return data

    cleaned = {}
    for key, value in data.items():
        if key == 'metadata':
            # Skip metadata sections entirely
            continue
        elif isinstance(value, dict):
            # Recursively clean nested dictionaries
            cleaned[key] = remove_metadata_sections(value)
        else:
            # Keep non-dict values as-is
            cleaned[key] = value

    return cleaned


def list_available_systems(registry_data: t.Dict[str, t.Any]) -> t.List[str]:
    """List all available computer systems in the registry."""
    return list(registry_data.keys())


def list_system_variants(registry_data: t.Dict[str, t.Any], system_name: str) -> t.List[str]:
    """List all available variants for a given system."""
    if system_name not in registry_data:
        raise ValueError(f"System '{system_name}' not found in registry")

    system_data = registry_data[system_name]
    variants = [key for key in system_data.keys() if key != 'default']
    return variants


def get_computer_setup_config(registry_data: t.Dict[str, t.Any], system_name: str, variant: str) -> t.Dict[str, t.Any]:
    """Get the computer setup configuration for a specific system and variant."""
    if system_name not in registry_data:
        raise ValueError(f"System '{system_name}' not found in registry")

    system_data = registry_data[system_name]

    if variant not in system_data:
        available_variants = list_system_variants(registry_data, system_name)
        raise ValueError(f"Variant '{variant}' not found for system '{system_name}'. Available: {available_variants}")

    return system_data[variant]['computer']['computer-setup']


def get_computer_configure_config(
    registry_data: t.Dict[str, t.Any], system_name: str, variant: str
) -> t.Dict[str, t.Any]:
    """Get the computer configure configuration for a specific system and variant."""
    if system_name not in registry_data:
        raise ValueError(f"System '{system_name}' not found in registry")

    system_data = registry_data[system_name]

    if variant not in system_data:
        available_variants = list_system_variants(registry_data, system_name)
        raise ValueError(f"Variant '{variant}' not found for system '{system_name}'. Available: {available_variants}")

    return system_data[variant]['computer']['computer-configure']


def get_available_codes(registry_data: t.Dict[str, t.Any], system_name: str, variant: str) -> t.Dict[str, t.Any]:
    """Get all available codes for a specific system and variant."""
    if system_name not in registry_data:
        raise ValueError(f"System '{system_name}' not found in registry")

    system_data = registry_data[system_name]

    if variant not in system_data:
        available_variants = list_system_variants(registry_data, system_name)
        raise ValueError(f"Variant '{variant}' not found for system '{system_name}'. Available: {available_variants}")

    return system_data[variant].get('codes', {})


def find_codes_by_name(registry_data: t.Dict[str, t.Any], code_pattern: str) -> t.List[t.Dict[str, t.Any]]:
    """Find codes across all systems that match a given pattern."""
    matching_codes = []

    for system_name, system_data in registry_data.items():
        for variant_name, variant_data in system_data.items():
            if variant_name == 'default':
                continue

            codes = variant_data.get('codes', {})
            for code_name, code_config in codes.items():
                if code_pattern.lower() in code_name.lower():
                    matching_codes.append(
                        {'system': system_name, 'variant': variant_name, 'code_name': code_name, 'config': code_config}
                    )

    return matching_codes


def interactive_system_selector(registry_data: t.Dict[str, t.Any]) -> t.Optional[t.Tuple[str, str]]:
    """Interactively prompt user to select a system and variant."""
    systems = list_available_systems(registry_data)

    if not systems:
        echo.echo_error('No systems found in registry.')
        return None

    echo.echo_info('\n🖥️  Available Systems:')
    echo.echo('=' * 80)

    for i, system in enumerate(systems, 1):
        default_variant = registry_data[system].get('default', 'N/A')
        variants = list_system_variants(registry_data, system)
        variant_str = ', '.join(variants)
        echo.echo(f'{i:2d}. {system}')
        echo.echo(f'     Default: {default_variant} | Variants: {variant_str}')

    echo.echo(f'{len(systems) + 1:2d}. Cancel')
    echo.echo('=' * 80)

    while True:
        try:
            choice = click.prompt(f'\nSelect a system (1-{len(systems) + 1})', type=int)

            if choice == len(systems) + 1:
                echo.echo_info('Selection cancelled.')
                return None
            elif 1 <= choice <= len(systems):
                selected_system = systems[choice - 1]

                # Now select variant
                variants = list_system_variants(registry_data, selected_system)

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
                echo.echo_error(f'Invalid choice. Please enter a number between 1 and {len(systems) + 1}.')

        except click.Abort:
            echo.echo_info('Selection cancelled.')
            return None


def interactive_computer_selector(system_name: str, variant: str) -> t.Optional[bool]:
    """Ask user whether to apply computer configuration directly or save to file."""
    echo.echo_info(f'\nConfiguration found for {system_name} / {variant}')
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


def interactive_code_selector(
    registry_data: t.Dict[str, t.Any], system_name: str, variant: str
) -> t.Optional[t.Dict[str, t.Any]]:
    """Interactively select a code from the available codes for a system/variant."""
    codes = get_available_codes(registry_data, system_name, variant)

    if not codes:
        echo.echo_warning(f'No codes found for {system_name} / {variant}')
        return None

    echo.echo_info(f'\n📦 Available codes for {system_name} / {variant}:')
    echo.echo('=' * 50)

    code_list = list(codes.items())
    for i, (code_name, code_config) in enumerate(code_list, 1):
        description = code_config.get('description', 'No description available')
        echo.echo(f'{i:2d}. {code_name}')
        echo.echo(f'     {description}')

    echo.echo(f'{len(code_list) + 1:2d}. Cancel')
    echo.echo('=' * 50)

    while True:
        try:
            choice = click.prompt(f'\nSelect a code (1-{len(code_list) + 1})', type=int)

            if choice == len(code_list) + 1:
                return None
            elif 1 <= choice <= len(code_list):
                selected_code = code_list[choice - 1]
                return {'name': selected_code[0], 'config': selected_code[1], 'system': system_name, 'variant': variant}
            else:
                echo.echo_error(f'Invalid choice. Please enter a number between 1 and {len(code_list) + 1}.')

        except click.Abort:
            return None


def save_config_to_file(config: t.Dict[str, t.Any], config_type: str, system_name: str, variant: str) -> Path:
    """Save configuration to a YAML file."""
    filename = f'{system_name.replace(".", "_")}_{variant}_{config_type}.yaml'
    filepath = Path.cwd() / filename

    # Handle file existence
    if filepath.exists():
        if not click.confirm(f'File {filename} already exists. Overwrite?'):
            counter = 1
            while True:
                new_filename = f'{system_name.replace(".", "_")}_{variant}_{config_type}_{counter}.yaml'
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
    from aiida.orm import Computer
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

                # Process configure_config to remove any metadata
                clean_configure_config = {k: v for k, v in configure_config.items() if k != 'metadata'}

                authinfo = computer.configure(user=user, **clean_configure_config)
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


def _handle_computer_configuration(registry_data, system_name, variant, save_only=False):
    """Handle the configuration of a computer from the registry."""
    try:
        setup_config = get_computer_setup_config(registry_data, system_name, variant)
        configure_config = get_computer_configure_config(registry_data, system_name, variant)

        # Process template variables
        setup_config = _process_template_variables(setup_config)
        configure_config = _process_template_variables(configure_config)

        # Decide what to do with the configuration
        if save_only:
            apply_config = False
        else:
            apply_config = interactive_computer_selector(system_name, variant)
            if apply_config is None:
                return

        if apply_config:
            success = apply_computer_config(setup_config, configure_config)
            if success:
                echo.echo_success('Computer configuration applied successfully!')
        else:
            # Complete the configuration with defaults for saving
            complete_config = complete_computer_spec_with_defaults(setup_config)
            setup_file = save_config_to_file(complete_config, 'setup', system_name, variant)
            configure_file = save_config_to_file(configure_config, 'configure', system_name, variant)

            echo.echo_info('\nTo apply these configurations, run:')
            echo.echo_info(f'  verdi computer setup --config {setup_file}')
            echo.echo_info(
                f'  verdi computer configure {complete_config.get("transport", "core.ssh")} {complete_config["label"]} --config {configure_file}'
            )

    except Exception as e:
        echo.echo_error(f'Failed to handle computer configuration: {e}')
        import traceback

        traceback.print_exc()


def search_computers_in_aiida(pattern: str) -> t.List[t.Any]:
    """Search for computers in AiiDA database that match the pattern."""
    try:
        from aiida.orm import Computer, QueryBuilder

        qb = QueryBuilder()
        qb.append(Computer, filters={'label': {'ilike': f'%{pattern}%'}})

        return [computer for [computer] in qb.all()]

    except Exception:
        return []


def _get_computers_table(registry_data) -> t.List[t.List]:
    """Print a formatted table of computer systems."""

    table = []
    systems = list(registry_data.keys())
    variants = []
    hostnames = []
    codes = []

    for system_key, system_data in registry_data.items():
        default_variant = system_data['default']
        variant_list = [key for key in system_data.keys() if key not in ('default', default_variant)]
        variant_str = f'{default_variant} (default)'
        if len(variant_list) > 0:
            variant_str += ', ' + ', '.join(variant_list)
        variants.append(variant_str)
        default_config = system_data[default_variant]
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


def _handle_computer_configuration(registry_data, system_name, variant, save_only=False):
    """Handle the configuration of a computer from the registry."""
    try:
        setup_config = get_computer_setup_config(registry_data, system_name, variant)
        configure_config = get_computer_configure_config(registry_data, system_name, variant)

        # Process template variables
        # FIXME: These two currently don't work. Placeholders are still in the created Computer
        setup_config = _process_template_variables(setup_config)
        configure_config = _process_template_variables(configure_config)

        # Decide what to do with the configuration
        apply_config = interactive_computer_selector(system_name, variant)
        if apply_config is None:
            return

        if apply_config:
            # TODO: Check here if a computer with the same label already exists.
            success = apply_computer_config(setup_config, configure_config)
        else:
            setup_file = save_config_to_file(setup_config, 'setup', system_name, variant)
            configure_file = save_config_to_file(configure_config, 'configure', system_name, variant)

            echo.echo_info('\nTo apply these configurations, run:')
            echo.echo_info(f'  verdi computer setup --config {setup_file}')
            echo.echo_info(
                f'  verdi computer configure {setup_config.get("transport", "core.ssh")} {setup_config["label"]} --config {configure_file}'
            )

    except Exception as e:
        echo.echo_error(f'Failed to handle computer configuration: {e}')


def _process_template_variables(config):
    """Process template variables in configuration."""
    import copy

    processed_config = copy.deepcopy(config)

    # Get template variables from metadata if available
    metadata = processed_config.get('metadata', {})
    template_variables = metadata.get('template_variables', {})

    # Remove metadata from the final config
    if 'metadata' in processed_config:
        del processed_config['metadata']

    # Prompt for template variables
    for var_name, var_info in template_variables.items():
        description = var_info.get('description', f'Value for {var_name}')
        var_type = var_info.get('type', 'text')
        default = var_info.get('default')
        options_list = var_info.get('options', [])

        if var_type == 'list' and options_list:
            echo.echo_info(f'\nAvailable options for {var_name}:')
            for i, option in enumerate(options_list, 1):
                echo.echo(f'  {i}. {option}')

            while True:
                try:
                    choice = click.prompt(f'Select {description} (1-{len(options_list)})', type=int)
                    if 1 <= choice <= len(options_list):
                        value = options_list[choice - 1]
                        break
                    else:
                        echo.echo_error(f'Please enter a number between 1 and {len(options_list)}')
                except click.Abort:
                    return None
        else:
            value = click.prompt(description, default=default, show_default=bool(default))

        # Replace template variables in the config
        _replace_template_var(processed_config, var_name, value)

    return processed_config


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
