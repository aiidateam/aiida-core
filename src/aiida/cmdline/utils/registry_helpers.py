"""Registry helpers for AiiDA computer discovery with clean, modern architecture."""

# TODO: Replace `echo` by logger calls

import copy
import json
import logging
import re
import typing as t
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import click
import requests
import yaml

from aiida.cmdline.utils.common import tabulate

LOGGER = logging.getLogger(__name__)

__all__ = (
    'CodeRegistryFetcher',
    'ComputerSearchService',
    'ComputerSelector',
    'ComputerSetupHandler',
    'ComputerSource',
    'ConfigFileManager',
    'RegistryConfig',
    'RegistryDataFetcher',
    'ResourceRegistryFetcher',
    'SSHConfigParser',
    'TemplateProcessor',
)


class ComputerSource(Enum):
    """Enumeration of computer sources."""

    CODE_REGISTRY = 'code-registry'
    RESOURCE_REGISTRY = 'resource-registry'
    SSH_CONFIG = 'ssh-config'


@dataclass
class RegistryConfig:
    """Configuration for registry operations."""

    code_registry_url: str = 'https://aiidateam.github.io/aiida-code-registry/database.json'
    resource_registry_url: str = 'https://aiidateam.github.io/aiida-resource-registry/database.json'
    request_timeout: int = 10
    ssh_config_path: t.Optional[Path] = None

    def __post_init__(self):
        if self.ssh_config_path is None:
            self.ssh_config_path = Path.home() / '.ssh' / 'config'


class RegistryDataFetcher(ABC):
    """Abstract base class for registry data fetchers."""

    def __init__(self, config: RegistryConfig):
        self.config = config

    @abstractmethod
    def fetch(self) -> t.Dict[str, t.Any]:
        """Fetch registry data."""
        pass

    def _make_request(self, url: str) -> t.Dict[str, t.Any]:
        """Make HTTP request with error handling."""
        try:
            response = requests.get(url, timeout=self.config.request_timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise click.ClickException(f'Failed to fetch data from {url}: {e}')
        except json.JSONDecodeError as e:
            raise click.ClickException(f'Failed to parse JSON data from {url}: {e}')


class CodeRegistryFetcher(RegistryDataFetcher):
    """Fetcher for AiiDA code registry."""

    def fetch(self) -> t.Dict[str, t.Any]:
        """Fetch and normalize code registry data."""
        registry_data = self._make_request(self.config.code_registry_url)
        return self._normalize_data(registry_data)

    def _normalize_data(self, registry_data: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
        """Convert to normalized format with 'computer' and 'codes' sub-keys."""
        categorized_data = {}

        for hostname, host_data in registry_data.items():
            categorized_data[hostname] = {}

            for variant_name, variant_data in host_data.items():
                if variant_name == 'default':
                    categorized_data[hostname]['default'] = variant_data
                    continue

                # Initialize new structure for this variant
                categorized_data[hostname][variant_name] = {'computer': {}, 'codes': {}}

                # Separate computer and code configurations
                for key, value in variant_data.items():
                    if key.startswith('computer-'):
                        categorized_data[hostname][variant_name]['computer'][key] = value
                    else:
                        categorized_data[hostname][variant_name]['codes'][key] = value

        return categorized_data


class ResourceRegistryFetcher(RegistryDataFetcher):
    """Fetcher for AiiDA resource registry."""

    def fetch(self) -> t.Dict[str, t.Any]:
        """Fetch and clean resource registry data."""
        registry_data = self._make_request(self.config.resource_registry_url)
        return self._remove_metadata_sections(registry_data)

    def _remove_metadata_sections(self, registry_data: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
        """Remove 'metadata' keys from the registry data structure."""
        cleaned = {}

        for hostname, host_data in registry_data.items():
            cleaned[hostname] = {}

            for variant, variant_data in host_data.items():
                if variant == 'default':
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


class SSHConfigParser:
    """Parser for SSH configuration files."""

    def __init__(self, config_path: t.Optional[Path] = None):
        self.config_path = config_path or Path.home() / '.ssh' / 'config'

    def parse(self) -> t.Dict[str, t.Any]:
        """Parse SSH config and convert to registry format."""
        if not self.config_path.exists():
            raise click.ClickException(f'SSH config file not found at {self.config_path}')

        try:
            ssh_hosts = self._parse_ssh_config()
            return self._convert_to_registry_format(ssh_hosts)
        except Exception as e:
            raise click.ClickException(f'Failed to parse SSH config file: {e}')

    def _parse_ssh_config(self) -> t.Dict[str, t.Dict[str, str]]:
        """Parse SSH config file and extract host configurations."""
        hosts = {}
        current_host = None

        with open(self.config_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue

                # Parse Host directive
                if line.lower().startswith('host '):
                    host_pattern = line.split(None, 1)[1]
                    host_names = re.split(r'[,\s]+', host_pattern)

                    for host_name in host_names:
                        host_name = host_name.strip()
                        if host_name and not ('*' in host_name or '?' in host_name):
                            current_host = host_name
                            hosts[current_host] = {}
                    continue

                # Parse configuration options
                if current_host and ' ' in line:
                    try:
                        key, value = line.split(None, 1)
                        hosts[current_host][key.lower()] = value
                    except ValueError:
                        # Skip malformed lines
                        continue

        return hosts

    def _convert_to_registry_format(self, ssh_hosts: t.Dict[str, t.Dict[str, str]]) -> t.Dict[str, t.Any]:
        """Convert parsed SSH config to registry format."""
        registry_data = {}

        for host_alias, host_config in ssh_hosts.items():
            # Skip git hosting services
            if any(pattern in host_alias.lower() for pattern in ['github.com', 'gitlab.com', 'bitbucket']):
                continue

            hostname = host_config.get('hostname', host_alias)

            # Create minimal setup configuration
            setup_config = {
                'label': hostname.split('.')[0] if '.' in hostname else hostname,
                'hostname': hostname,
                'transport': 'core.ssh_async',
            }

            # Structure in registry format
            registry_data[host_alias] = {
                'default': 'ssh_config',
                'ssh_config': {'computer': {'computer-setup': setup_config, 'computer-configure': {}}, 'codes': {}},
            }

        return registry_data


class TemplateProcessor:
    """Processor for template variables in configurations."""

    def process(self, config: t.Dict[str, t.Any]) -> t.Optional[t.Dict[str, t.Any]]:
        """Process template variables in configuration."""
        processed_config = copy.deepcopy(config)
        template_vars = self._find_template_variables(processed_config)

        if not template_vars:
            return processed_config

        LOGGER.info(f'Found {len(template_vars)} template variable(s) to configure:')

        # Prompt user for each template variable
        var_values = {}
        for var_name in template_vars:
            LOGGER.info(f'Template variable: {var_name}')

            # Show usage examples
            usage_examples = self._get_template_usage_examples(processed_config, var_name)
            if usage_examples:
                LOGGER.info(f'Template variable: {{{{ {var_name} }}}}')
                LOGGER.info('Used in:')
                for example in usage_examples:
                    LOGGER.info(f'  {example}')

            try:
                value = click.prompt(f"Enter value for '{var_name}'", type=str)
                var_values[var_name] = value
                LOGGER.info('=' * 40)
            except click.Abort:
                return None

        # Replace all template variables
        for var_name, value in var_values.items():
            self._replace_template_var(processed_config, var_name, value)

        return processed_config

    def _find_template_variables(self, obj: t.Any, template_vars: t.Optional[t.Set[str]] = None) -> t.Set[str]:
        """Recursively find all Jinja2 template variables."""
        if template_vars is None:
            template_vars = set()

        pattern = r'\{\{\s*([^}]+)\s*\}\}'

        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str):
                    matches = re.findall(pattern, value)
                    for match in matches:
                        template_vars.add(match.strip())
                elif isinstance(value, (dict, list)):
                    self._find_template_variables(value, template_vars)
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, str):
                    matches = re.findall(pattern, item)
                    for match in matches:
                        template_vars.add(match.strip())
                elif isinstance(item, (dict, list)):
                    self._find_template_variables(item, template_vars)

        return template_vars

    def _get_template_usage_examples(
        self, obj: t.Any, var_name: str, examples: t.Optional[t.List[str]] = None, path: str = ''
    ) -> t.List[str]:
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
                    self._get_template_usage_examples(value, var_name, examples, current_path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                current_path = f'{path}[{i}]'
                if isinstance(item, str) and template_pattern in item:
                    examples.append(f'{current_path}: {item}')
                elif isinstance(item, (dict, list)):
                    self._get_template_usage_examples(item, var_name, examples, current_path)

        return examples

    def _replace_template_var(self, obj: t.Any, var_name: str, value: str):
        """Recursively replace template variables."""
        template_pattern = f'{{{{ {var_name} }}}}'

        if isinstance(obj, dict):
            for key, val in obj.items():
                if isinstance(val, str) and template_pattern in val:
                    obj[key] = val.replace(template_pattern, str(value))
                elif isinstance(val, (dict, list)):
                    self._replace_template_var(val, var_name, value)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, str) and template_pattern in item:
                    obj[i] = item.replace(template_pattern, str(value))
                elif isinstance(item, (dict, list)):
                    self._replace_template_var(item, var_name, value)


class ComputerSelector:
    """Interactive computer and variant selection."""

    def __init__(self, registry_data: t.Dict[str, t.Any]):
        self.registry_data = registry_data

    def select_computer(self) -> t.Optional[str]:
        """Show a table of computers with row numbers and prompt for selection in a single step, including all info."""
        computers = list(self.registry_data.keys())

        if not computers:
            LOGGER.error('No systems found in registry.')
            return None

        # Prepare table with row numbers and all info
        table = []
        for i, computer in enumerate(computers, 1):
            default_variant = self.registry_data[computer].get('default', 'N/A')
            computer_data = self.registry_data[computer]
            # Hostname
            try:
                hostname = computer_data[default_variant]['computer']['computer-setup']['hostname']
            except Exception:
                hostname = 'N/A'
            # Codes: show up to 5 code keys for the default variant, regardless of suffix
            codes = []
            try:
                codes_dict = computer_data[default_variant].get('codes', {})
                codes = list(codes_dict.keys())
            except Exception:
                codes = []
            # Limit to 5 codes, append '...' if more
            if len(codes) > 5:
                codes_str = ', '.join(codes[:5]) + ', ...'
            else:
                codes_str = ', '.join(codes) if codes else 'None'
            # Variants
            variants = self._get_variants(computer)
            # Mark default variant
            variant_strs = []
            for v in variants:
                if v == default_variant:
                    variant_strs.append(f'{v} (default)')
                else:
                    variant_strs.append(v)
            variant_str = ', '.join(variant_strs)
            table.append([f'{i}', computer, variant_str, hostname, codes_str])
        # No Cancel row in the table

        # Print table
        print(tabulate(table, headers=['#', 'System', 'Variants', 'Hostname', 'Codes'], tablefmt='grid'))
        LOGGER.info('\nEnter the number of the system to select, or 0 to cancel.')

        # Prompt for selection
        while True:
            try:
                choice = click.prompt(f'Select a system (1-{len(computers)}, or 0 to cancel)', type=int)

                if choice == 0:
                    LOGGER.info('Selection cancelled.')
                    return None
                elif 1 <= choice <= len(computers):
                    selected_system = computers[choice - 1]
                    LOGGER.info(f'Selected computer: {selected_system}')
                    return selected_system
                else:
                    LOGGER.error(
                        f'Invalid choice. Please enter a number between 1 and {len(computers)}, or 0 to cancel.'
                    )

            except click.Abort:
                LOGGER.info('Selection cancelled.')
                return None

    def select_variant(self, computer_name: str) -> t.Optional[str]:
        """Interactively prompt user to select a variant for a specific computer."""
        if computer_name not in self.registry_data:
            LOGGER.error(f"Computer '{computer_name}' not found in registry.")
            return None

        variants = self._get_variants(computer_name)
        default_variant = self.registry_data[computer_name].get('default', None)
        # Move default variant to the front if present
        if default_variant in variants:
            variants = [default_variant] + [v for v in variants if v != default_variant]

        if not variants:
            LOGGER.error(f"No variants found for computer '{computer_name}'.")
            return None

        # If only one variant, return it directly
        if len(variants) == 1:
            print(f'Only one variant available for {computer_name}: {variants[0]}')
            if click.confirm(f'Use variant "{variants[0]}"?', default=True):
                return variants[0]
            else:
                return None

        print(f'⚙️  Available variants for {computer_name}:')
        print('=' * 50)

        for i, variant in enumerate(variants, 1):
            # Show description if available
            try:
                setup_config = self.get_setup_config(computer_name, variant)
                description = setup_config.get('description', 'No description available')
                label = f'{variant} (default)' if variant == default_variant else variant
                print(f'{i:2d}. {label}')
                print(f'     {description}')
            except Exception:
                label = f'{variant} (default)' if variant == default_variant else variant
                print(f'{i:2d}. {label}')

        print('=' * 50)
        print('Enter the number of the variant to select, or 0 to cancel.')

        while True:
            try:
                variant_choice = click.prompt(f'Select a variant (1-{len(variants)}, or 0 to cancel)', type=int)

                if variant_choice == 0:
                    print('Selection cancelled.')
                    return None
                elif 1 <= variant_choice <= len(variants):
                    selected_variant = variants[variant_choice - 1]
                    print(f'Selected variant: {selected_variant}')
                    return selected_variant
                else:
                    LOGGER.error(
                        f'Invalid choice. Please enter a number between 1 and {len(variants)}, or 0 to cancel.'
                    )

            except click.Abort:
                print('Selection cancelled.')
                return None

    def _get_variants(self, computer_name: str) -> t.List[str]:
        """List all available variants for a given system."""
        if computer_name not in self.registry_data:
            return []

        computer_data = self.registry_data[computer_name]
        return [key for key in computer_data.keys() if key != 'default']

    def get_setup_config(self, computer_name: str, variant: str) -> t.Dict[str, t.Any]:
        """Get the computer setup configuration for a specific system and variant."""
        if computer_name not in self.registry_data:
            raise ValueError(f"System '{computer_name}' not found in registry")

        computer_data = self.registry_data[computer_name]

        if variant not in computer_data:
            available_variants = self._get_variants(computer_name)
            raise ValueError(
                f"Variant '{variant}' not found for system '{computer_name}'. Available: {available_variants}"
            )

        return computer_data[variant]['computer']['computer-setup']

    def get_configure_config(self, computer_name: str, variant: str) -> t.Dict[str, t.Any]:
        """Get the computer configure configuration for a specific system and variant."""
        if computer_name not in self.registry_data:
            raise ValueError(f"Computer '{computer_name}' not found in registry")

        computer_data = self.registry_data[computer_name]

        if variant not in computer_data:
            available_variants = self._get_variants(computer_name)
            raise ValueError(
                f"Variant '{variant}' not found for system '{computer_name}'. Available: {available_variants}"
            )

        return computer_data[variant]['computer']['computer-configure']


class ConfigFileManager:
    """Manager for configuration file operations."""

    @staticmethod
    def save_config(config: t.Dict[str, t.Any], config_type: str, computer_name: str, variant: str) -> Path:
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

        LOGGER.info(f'{config_type} configuration saved to {filepath}')
        return filepath

    @staticmethod
    def create_computers_table(registry_data: t.Dict[str, t.Any]) -> t.List[t.List[str]]:
        """Create a formatted table of computer systems."""
        table = []

        for computer_name, computer_data in registry_data.items():
            default_variant = computer_data['default']
            variant_list = [key for key in computer_data.keys() if key not in ('default', default_variant)]
            variant_str = f'{default_variant} (default)'
            if variant_list:
                variant_str += ', ' + ', '.join(variant_list)

            default_config = computer_data[default_variant]

            # Handle hostname - might be empty for SSH config entries
            try:
                hostname = default_config['computer']['computer-setup']['hostname']
            except KeyError:
                # For SSH config entries, extract hostname from the key
                if computer_name.startswith('ssh:'):
                    hostname = computer_name.replace('ssh:', '')
                else:
                    hostname = 'N/A'

            # Handle codes
            if default_config.get('codes'):
                default_codes = [
                    code.removesuffix(f'-{default_variant}')
                    for code in default_config['codes']
                    if code.endswith(f'-{default_variant}')
                ]
                if not default_codes:
                    default_codes = list(default_config['codes'].keys())
                codes_str = ', '.join(default_codes)
            else:
                codes_str = 'None'

            table.append([computer_name, variant_str, hostname, codes_str])

        return table


class ComputerSearchService:
    """Service class to handle computer search operations."""

    def __init__(self):
        self.registry_data = {}
        self.source_counts = {}

    def fetch_data(self, source: ComputerSource) -> t.Dict[str, t.Any]:
        """Fetch data from the specified source(s)."""
        registry_data = {}
        config = RegistryConfig()

        if source == ComputerSource.CODE_REGISTRY:
            try:
                LOGGER.info('Fetching AiiDA code registry...')
                fetcher = CodeRegistryFetcher(config)
                code_data = fetcher.fetch()
                registry_data.update(code_data)
                self.source_counts['code-registry'] = len(code_data)
                LOGGER.info(f'Code registry: {len(code_data)} computers found')
            except Exception as e:
                LOGGER.warning(f'Failed to fetch code registry: {e}')

        if source == ComputerSource.RESOURCE_REGISTRY:
            try:
                LOGGER.info('Fetching AiiDA resource registry...')
                fetcher = ResourceRegistryFetcher(config)
                resource_data = fetcher.fetch()
                # Merge with priority to resource registry
                for key, value in resource_data.items():
                    if key in registry_data:
                        LOGGER.debug(f'Computer {key} found in both registries, using resource registry version')
                    registry_data[key] = value
                self.source_counts['resource-registry'] = len(resource_data)
                LOGGER.info(f'Resource registry: {len(resource_data)} computers found')
            except Exception as e:
                LOGGER.warning(f'Failed to fetch resource registry: {e}')

        if source == ComputerSource.SSH_CONFIG:
            try:
                LOGGER.info('Parsing SSH config file (~/.ssh/config)...')
                parser = SSHConfigParser()
                ssh_data = parser.parse()
                # Add SSH config data with prefix to avoid conflicts
                for key, value in ssh_data.items():
                    ssh_key = f'ssh:{key}'
                    registry_data[ssh_key] = value
                self.source_counts['ssh-config'] = len(ssh_data)
                LOGGER.info(f'SSH config: {len(ssh_data)} computers found')
            except Exception as e:
                LOGGER.warning(f'Failed to parse SSH config: {e}')

        self.registry_data = registry_data
        return registry_data

    def filter_by_pattern(self, pattern: str) -> t.Dict[str, t.Any]:
        """Filter computers by pattern."""
        matching_systems = [system for system in self.registry_data.keys() if pattern in system]
        if matching_systems:
            return {match: self.registry_data[match] for match in matching_systems}
        return {}


class ComputerSetupHandler:
    """Handler for computer setup operations."""

    @staticmethod
    def handle_ssh_config_setup(system_name: str, hostname: str):
        """Handle setup for SSH config computers."""
        LOGGER.info(
            f'\n💡 SSH Config computer "{system_name}" can be set up using the core.ssh_async transport plugin.'
        )
        LOGGER.info('This transport plugin automatically uses your SSH configuration (~/.ssh/config)')
        LOGGER.info('for connection settings including ProxyJump, IdentityFile, and other SSH options.')
        LOGGER.info('To set up this computer:')
        label = hostname.split('.')[0] if '.' in hostname else hostname
        LOGGER.info(f'  verdi computer setup --transport core.ssh_async --hostname {hostname} --label {label}')
        LOGGER.info('For more information, see the AiiDA documentation on SSH transport plugins.')

    @staticmethod
    def _auto_setup(
        ctx,
        setup_config: t.Dict[str, t.Any],
        computer_label: str,
        transport_type: str,
    ) -> bool:
        """Perform automatic setup only (creation)."""
        try:
            LOGGER.info('Automatically setting up computer...')

            from aiida.cmdline.commands.cmd_computer import computer_setup
            from aiida.plugins import SchedulerFactory, TransportFactory

            # Convert strings to entry point objects
            setup_config_copy = setup_config.copy()

            if 'scheduler' in setup_config_copy:
                scheduler_ep = SchedulerFactory(setup_config_copy['scheduler'], load=False)
                setup_config_copy['scheduler'] = scheduler_ep

            if 'transport' in setup_config_copy:
                transport_ep = TransportFactory(setup_config_copy['transport'], load=False)
                setup_config_copy['transport'] = transport_ep

            # Invoke setup command
            ctx.invoke(computer_setup, non_interactive=True, **setup_config_copy)
            LOGGER.info('✅ Computer setup completed successfully!')
            return True

        except Exception as e:
            LOGGER.error(f'Auto-setup failed: {e}')
            LOGGER.info('You can try manual setup using the generated configuration files.')
            return False

    @staticmethod
    def _auto_configure(
        ctx,
        configure_config: t.Optional[t.Dict[str, t.Any]],
        computer_label: str,
        transport_type: str,
        configure_file: t.Optional[Path],
    ) -> bool:
        """Stub for automatic configuration: just log that it's not supported."""
        LOGGER.warning('Automatic configuration of computers is not yet supported.')
        return False

    @staticmethod
    def handle_registry_setup(ctx, selector: 'ComputerSelector', system_name: str, variant: str, auto_setup: bool):
        """Handle setup for registry computers."""
        LOGGER.info(f'📋 Processing configuration for {system_name} ({variant})')

        # Get configurations
        setup_config = selector.get_setup_config(system_name, variant)
        configure_config = selector.get_configure_config(system_name, variant)

        # Process template variables
        processor = TemplateProcessor()

        LOGGER.info('Processing computer setup configuration...')
        processed_setup_config = processor.process(setup_config)
        if processed_setup_config is None:
            LOGGER.info('Configuration processing was cancelled.')
            return False

        LOGGER.info('Processing computer configure configuration...')
        processed_configure_config = processor.process(configure_config)
        if processed_configure_config is None:
            LOGGER.info('Configuration processing was cancelled.')
            return False

        file_manager = ConfigFileManager()
        setup_file = None
        configure_file = None

        computer_label = processed_setup_config.get('label', f'{system_name}_{variant}')
        transport_type = processed_setup_config.get('transport', 'core.ssh')

        # Try auto-setup if requested (only setup/creation, not configuration)
        if auto_setup:
            LOGGER.info('Attempting automatic computer setup...')
            setup_success = False
            try:
                setup_success = ComputerSetupHandler._auto_setup(
                    ctx, processed_setup_config, computer_label, transport_type
                )
            except Exception as e:
                LOGGER.error(f'Automatic setup failed: {e}')
                setup_success = False
            if not setup_success:
                LOGGER.warning('Automatic setup failed. Writing setup YAML file to disk for manual setup.')
                setup_file = file_manager.save_config(processed_setup_config, 'setup', system_name, variant)
                LOGGER.info(f'Setup YAML file written to: {setup_file}')
        else:
            setup_file = file_manager.save_config(processed_setup_config, 'setup', system_name, variant)
            LOGGER.info(f'Setup YAML file written to: {setup_file}')

        # Always write configuration YAML and log that auto-configuration is not supported
        LOGGER.warning(
            'Automatic configuration of computers is not yet supported. Writing configuration YAML file to disk.'
        )
        configure_file = file_manager.save_config(processed_configure_config, 'configure', system_name, variant)
        LOGGER.info(f'Configuration YAML file written to: {configure_file}')
        ComputerSetupHandler._auto_configure(
            ctx, processed_configure_config, computer_label, transport_type, configure_file
        )

        return True

    @staticmethod
    def _show_manual_instructions(setup_file: Path, configure_file: Path, transport_type: str, computer_label: str):
        """Show manual setup instructions."""
        LOGGER.info('To set up the computer, run:')
        LOGGER.info(f'  verdi computer setup --config {setup_file}')
        LOGGER.info('\nTo configure the computer, run:')
        LOGGER.info(f'  verdi computer configure {transport_type} {computer_label} --config {configure_file}')
