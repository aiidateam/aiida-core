import json
from typing import Any, Dict, List, Optional

import requests

# Direct URL to the database.json file
DATABASE_URL = 'https://aiidateam.github.io/aiida-code-registry/database.json'


def fetch_aiida_registry_data() -> Dict[str, Any]:
    """
    Fetch the complete AiiDA code registry database from the published JSON file.

    Returns:
        Dictionary containing the complete registry database
    """
    try:
        response = requests.get(DATABASE_URL)
        response.raise_for_status()

        registry_data = response.json()
        print('✅ Successfully fetched AiiDA registry data')
        print(f'📊 Found {len(registry_data)} computer systems')

        return registry_data

    except requests.exceptions.RequestException as e:
        raise Exception(f'Failed to fetch registry data from {DATABASE_URL}: {e}')
    except json.JSONDecodeError as e:
        raise Exception(f'Failed to parse JSON data: {e}')


def list_available_systems(registry_data: Dict[str, Any]) -> List[str]:
    """
    List all available computer systems in the registry.

    Args:
        registry_data: The registry data from fetch_aiida_registry_data()

    Returns:
        List of system names
    """
    return list(registry_data.keys())


def list_system_variants(registry_data: Dict[str, Any], system_name: str) -> List[str]:
    """
    List all available variants for a given system.

    Args:
        registry_data: The registry data from fetch_aiida_registry_data()
        system_name: Name of the system (e.g., 'daint.cscs.ch')

    Returns:
        List of variant names
    """
    if system_name not in registry_data:
        raise ValueError(f"System '{system_name}' not found in registry")

    system_data = registry_data[system_name]
    variants = [key for key in system_data.keys() if key != 'default']
    return variants


def get_computer_setup_config(registry_data: Dict[str, Any], system_name: str, variant: str) -> Dict[str, Any]:
    """
    Get the computer setup configuration for a specific system and variant.

    Args:
        registry_data: The registry data from fetch_aiida_registry_data()
        system_name: Name of the system (e.g., 'daint.cscs.ch')
        variant: Name of the variant (e.g., 'gpu', 'mc')

    Returns:
        Computer setup configuration dictionary
    """
    if system_name not in registry_data:
        raise ValueError(f"System '{system_name}' not found in registry")

    system_data = registry_data[system_name]

    if variant not in system_data:
        available_variants = list_system_variants(registry_data, system_name)
        raise ValueError(
            f"variant '{variant}' not found for system '{system_name}'. Available: {available_variants}"
        )

    return system_data[variant]['computer']['computer-setup']


def get_computer_configure_config(registry_data: Dict[str, Any], system_name: str, variant: str) -> Dict[str, Any]:
    """
    Get the computer configure configuration for a specific system and variant.

    Args:
        registry_data: The registry data from fetch_aiida_registry_data()
        system_name: Name of the system (e.g., 'daint.cscs.ch')
        variant: Name of the variant (e.g., 'gpu', 'mc')

    Returns:
        Computer configure configuration dictionary
    """
    if system_name not in registry_data:
        raise ValueError(f"System '{system_name}' not found in registry")

    system_data = registry_data[system_name]

    if variant not in system_data:
        available_variants = list_system_variants(registry_data, system_name)
        raise ValueError(
            f"variant '{variant}' not found for system '{system_name}'. Available: {available_variants}"
        )

    return system_data[variant]['computer']['computer-configure']


def get_available_codes(registry_data: Dict[str, Any], system_name: str, variant: str) -> Dict[str, Any]:
    """
    Get all available codes for a specific system and variant.

    Args:
        registry_data: The registry data from fetch_aiida_registry_data()
        system_name: Name of the system (e.g., 'daint.cscs.ch')
        variant: Name of the variant (e.g., 'gpu', 'mc')

    Returns:
        Dictionary of available codes
    """
    if system_name not in registry_data:
        raise ValueError(f"System '{system_name}' not found in registry")

    system_data = registry_data[system_name]

    if variant not in system_data:
        available_variants = list_system_variants(registry_data, system_name)
        raise ValueError(
            f"variant '{variant}' not found for system '{system_name}'. Available: {available_variants}"
        )

    return system_data[variant].get('codes', {})


def find_computer_configs_by_pattern(registry_data: Dict[str, Any], pattern: str) -> List[Dict[str, Any]]:
    """
    Find computer configurations across all systems that match a given pattern.

    Args:
        registry_data: The registry data from fetch_aiida_registry_data()
        pattern: Pattern to match against system names (case-insensitive)

    Returns:
        List of matching computer configurations with system and variant info
    """
    matching_configs = []

    for system_name, system_data in registry_data.items():
        if pattern.lower() in system_name.lower():
            for variant_name, variant_data in system_data.items():
                if variant_name == 'default':
                    continue

                computer_setup = variant_data.get('computer', {}).get('computer-setup', {})
                computer_configure = variant_data.get('computer', {}).get('computer-configure', {})

                matching_configs.append(
                    {
                        'system': system_name,
                        'variant': variant_name,
                        'computer_setup': computer_setup,
                        'computer_configure': computer_configure,
                    }
                )

    return matching_configs


def find_codes_by_name(registry_data: Dict[str, Any], code_pattern: str) -> List[Dict[str, Any]]:
    """
    Find codes across all systems that match a given pattern.

    Args:
        registry_data: The registry data from fetch_aiida_registry_data()
        code_pattern: Pattern to match against code names (case-insensitive)

    Returns:
        List of matching codes with system and variant info
    """
    matching_codes = []

    for system_name, system_data in registry_data.items():
        for variant_name, variant_data in system_data.items():
            if variant_name == 'default':
                continue

            codes = variant_data.get('codes', {})
            for code_name, code_config in codes.items():
                if code_pattern.lower() in code_name.lower():
                    matching_codes.append(
                        {
                            'system': system_name,
                            'variant': variant_name,
                            'code_name': code_name,
                            'config': code_config,
                        }
                    )

    return matching_codes


def interactive_system_selector(registry_data: Dict[str, Any]) -> Optional[tuple]:
    """
    Interactively prompt user to select a system and variant.

    Args:
        registry_data: The registry data from fetch_aiida_registry_data()

    Returns:
        Tuple of (system_name, variant_name) or None if cancelled
    """
    systems = list_available_systems(registry_data)

    if not systems:
        print('No systems found in registry.')
        return None

    print('\n🖥️  Available Systems:')
    print('=' * 50)

    for i, system in enumerate(systems, 1):
        default_variant = registry_data[system].get('default', 'N/A')
        variants = list_system_variants(registry_data, system)
        print(f'{i:2d}. {system} (default: {default_variant}, variants: {", ".join(variants)})')

    print(f'{len(systems) + 1:2d}. Cancel')
    print('=' * 50)

    while True:
        try:
            choice = input(f'\nSelect a system (1-{len(systems) + 1}): ').strip()

            if not choice:
                continue

            choice_num = int(choice)

            if choice_num == len(systems) + 1:
                print('Selection cancelled.')
                return None
            elif 1 <= choice_num <= len(systems):
                selected_system = systems[choice_num - 1]

                # Now select variant
                variants = list_system_variants(registry_data, selected_system)

                print(f'\n🔧 Available variants for {selected_system}:')
                print('=' * 50)

                for i, variant in enumerate(variants, 1):
                    print(f'{i:2d}. {variant}')

                print(f'{len(variants) + 1:2d}. Back to system selection')
                print('=' * 50)

                while True:
                    try:
                        part_choice = input(f'\nSelect a variant (1-{len(variants) + 1}): ').strip()

                        if not part_choice:
                            continue

                        part_choice_num = int(part_choice)

                        if part_choice_num == len(variants) + 1:
                            break  # Go back to system selection
                        elif 1 <= part_choice_num <= len(variants):
                            selected_variant = variants[part_choice_num - 1]
                            print(f'\n✅ Selected: {selected_system} / {selected_variant}')
                            return (selected_system, selected_variant)
                        else:
                            print(f'Invalid choice. Please enter a number between 1 and {len(variants) + 1}.')

                    except ValueError:
                        print('Invalid input. Please enter a number.')
                    except KeyboardInterrupt:
                        print('\n\nSelection cancelled.')
                        return None

            else:
                print(f'Invalid choice. Please enter a number between 1 and {len(systems) + 1}.')

        except ValueError:
            print('Invalid input. Please enter a number.')
        except KeyboardInterrupt:
            print('\n\nSelection cancelled.')
            return None


def generate_verdi_commands(registry_data: Dict[str, Any], system_name: str, variant: str) -> Dict[str, str]:
    """
    Generate verdi commands for computer setup and configure based on the registry data.

    Args:
        registry_data: The registry data from fetch_aiida_registry_data()
        system_name: Name of the system
        variant: Name of the variant

    Returns:
        Dictionary with 'setup' and 'configure' command templates
    """
    try:
        setup_config = get_computer_setup_config(registry_data, system_name, variant)
        configure_config = get_computer_configure_config(registry_data, system_name, variant)

        # For now, return the configs as JSON that could be saved to files
        # In practice, you'd want to create YAML files from these
        commands = {
            'setup_config': json.dumps(setup_config, indent=2),
            'configure_config': json.dumps(configure_config, indent=2),
            'setup_command': '# Save setup config to computer-setup.yaml and run:\n# verdi computer setup --config computer-setup.yaml',
            'configure_command': '# Save configure config to computer-configure.yaml and run:\n# verdi computer configure --config computer-configure.yaml',
        }

        return commands

    except Exception as e:
        return {'error': f'Failed to generate commands: {e}'}


# Example usage equivalent to your original code
if __name__ == '__main__':
    try:
        # Fetch the registry data (replaces all the GitHub API calls)
        registry_data = fetch_aiida_registry_data()

        # List all available systems
        systems = list_available_systems(registry_data)
        print(f'\n🖥️  Available systems: {", ".join(systems)}')

        # Find computer configurations (replaces find_files_by_pattern for computer-setup.yaml)
        computer_configs = find_computer_configs_by_pattern(registry_data, 'daint')  # Example: find daint configs
        print(f"\n🔧 Found {len(computer_configs)} computer configurations for 'daint':")
        for config in computer_configs:
            print(f'  - {config["system"]} / {config["variant"]}')

        # Interactive selection (replaces interactive_file_selector)
        selection = interactive_system_selector(registry_data)

        if selection:
            system_name, variant_name = selection

            # Generate the equivalent of the verdi commands
            commands = generate_verdi_commands(registry_data, system_name, variant_name)

            if 'error' not in commands:
                print(f'\n✅ Configuration for {system_name} / {variant_name}:')
                print('\n📝 Computer Setup Configuration:')
                print(commands['setup_config'])
                print(f'\n{commands["setup_command"]}')

                print('\n📝 Computer Configure Configuration:')
                print(commands['configure_config'])
                print(f'\n{commands["configure_command"]}')
            else:
                print(f'❌ {commands["error"]}')

        # Example: Find all QuantumESPRESSO codes (replaces searching for specific files)
        qe_codes = find_codes_by_name(registry_data, 'QuantumESPRESSO')
        print(f'\n🔍 Found {len(qe_codes)} QuantumESPRESSO installations:')
        for code in qe_codes[:5]:  # Show first 5
            print(f'  - {code["system"]} / {code["variant"]} / {code["code_name"]}')
        if len(qe_codes) > 5:
            print(f'  ... and {len(qe_codes) - 5} more')

    except Exception as e:
        print(f'❌ Error: {e}')
