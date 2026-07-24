###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Extract and diff the public AiiDA Python API.

By AiiDA convention, anything importable directly from ``aiida`` or from a
second-level package such as ``aiida.orm`` is considered public API.

The script inspects ``src/aiida/__init__.py`` and every second-level package
``src/aiida/*/__init__.py`` without importing AiiDA. If a module defines
``__all__``, that is used as the authoritative list of public names.
Otherwise, public names are inferred from top-level definitions and imports.

For public classes, the extractor also recurses into their public members and
nested classes, returning dotted paths for the full class API.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from importlib.util import resolve_name
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ApiResource:
    """A public API resource."""

    path: str
    kind: str
    signature: str | None = None


@dataclass(frozen=True)
class ModuleApi:
    """Public API exported by a module."""

    exports: list[str]
    resources: list[ApiResource]


@dataclass(frozen=True)
class ResolvedSymbol:
    """A resolved symbol in the source tree."""

    module_name: str
    name: str
    kind: str
    node: ast.AST | None = None


@dataclass(frozen=True)
class ApiDiff:
    """The diff between two API snapshots."""

    added: list[ApiResource]
    removed: list[ApiResource]
    changed: list[dict[str, ApiResource]]


class SourceResolver:
    """Resolve symbols and class members from the source tree."""

    def __init__(self, src_root: Path) -> None:
        """Initialize the resolver."""
        self.src_root = src_root.resolve()
        self._module_paths: dict[str, Path | None] = {}
        self._module_trees: dict[str, ast.Module | None] = {}
        self._module_exports: dict[str, list[str]] = {}
        self._symbol_cache: dict[tuple[str, str], ResolvedSymbol | None] = {}

    def get_module_path(self, module_name: str) -> Path | None:
        """Return the source file for a module, if it is part of the tree."""
        if module_name in self._module_paths:
            return self._module_paths[module_name]

        parts = module_name.split('.')

        if not parts or parts[0] != 'aiida':
            self._module_paths[module_name] = None
            return None

        relative_parts = parts[1:]
        package_path = self.src_root.joinpath(*relative_parts) / '__init__.py'

        if package_path.is_file():
            self._module_paths[module_name] = package_path
            return package_path

        module_path = self.src_root.joinpath(*relative_parts).with_suffix('.py')

        if module_path.is_file():
            self._module_paths[module_name] = module_path
            return module_path

        self._module_paths[module_name] = None
        return None

    def module_exists(self, module_name: str) -> bool:
        """Return whether a module exists in the source tree."""
        return self.get_module_path(module_name) is not None

    def is_package(self, module_name: str) -> bool:
        """Return whether a module is a package."""
        module_path = self.get_module_path(module_name)
        return module_path is not None and module_path.name == '__init__.py'

    def get_package_name(self, module_name: str) -> str:
        """Return the package name to use for relative import resolution."""
        if self.is_package(module_name):
            return module_name
        return module_name.rpartition('.')[0]

    def get_module_tree(self, module_name: str) -> ast.Module | None:
        """Return the parsed AST for a module in the source tree."""
        if module_name in self._module_trees:
            return self._module_trees[module_name]

        module_path = self.get_module_path(module_name)

        if module_path is None:
            self._module_trees[module_name] = None
            return None

        self._module_trees[module_name] = ast.parse(module_path.read_text(encoding='utf8'))
        return self._module_trees[module_name]

    def get_module_exports(self, module_name: str) -> list[str]:
        """Return the public exports for a module."""
        if module_name in self._module_exports:
            return self._module_exports[module_name]

        tree = self.get_module_tree(module_name)

        if tree is None:
            self._module_exports[module_name] = []
            return []

        exports = _extract___all__(tree)

        if exports is None:
            exports = _infer_exports_from_module(tree)

        self._module_exports[module_name] = sorted(set(exports))
        return self._module_exports[module_name]

    def resolve_imported_module(self, module_name: str, statement: ast.ImportFrom) -> str | None:
        """Resolve the target module of an import-from statement."""
        if statement.level == 0:
            return statement.module

        relative_name = '.' * statement.level

        if statement.module:
            relative_name += statement.module

        package_name = self.get_package_name(module_name)

        if not package_name:
            return None

        return resolve_name(relative_name, package_name)

    def resolve_symbol(
        self, module_name: str, symbol_name: str, seen: set[tuple[str, str]] | None = None
    ) -> ResolvedSymbol | None:
        """Resolve a public symbol to its source definition."""
        cache_key = (module_name, symbol_name)

        if cache_key in self._symbol_cache:
            return self._symbol_cache[cache_key]

        if seen is None:
            seen = set()

        if cache_key in seen:
            return None

        seen.add(cache_key)
        tree = self.get_module_tree(module_name)

        if tree is None:
            self._symbol_cache[cache_key] = None
            return None

        for statement in tree.body:
            if isinstance(statement, ast.ClassDef) and statement.name == symbol_name:
                resolved = ResolvedSymbol(module_name=module_name, name=symbol_name, kind='class', node=statement)
                self._symbol_cache[cache_key] = resolved
                return resolved

            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)) and statement.name == symbol_name:
                resolved = ResolvedSymbol(module_name=module_name, name=symbol_name, kind='function', node=statement)
                self._symbol_cache[cache_key] = resolved
                return resolved

            if isinstance(statement, ast.Assign):
                for target in statement.targets:
                    if isinstance(target, ast.Name) and target.id == symbol_name:
                        resolved = ResolvedSymbol(
                            module_name=module_name, name=symbol_name, kind='attribute', node=statement
                        )
                        self._symbol_cache[cache_key] = resolved
                        return resolved

            if (
                isinstance(statement, ast.AnnAssign)
                and isinstance(statement.target, ast.Name)
                and statement.target.id == symbol_name
            ):
                resolved = ResolvedSymbol(module_name=module_name, name=symbol_name, kind='attribute', node=statement)
                self._symbol_cache[cache_key] = resolved
                return resolved

        for statement in tree.body:
            if isinstance(statement, ast.ImportFrom):
                imported_module = self.resolve_imported_module(module_name, statement)

                if imported_module is None:
                    continue

                for alias in statement.names:
                    if alias.name == '*':
                        if symbol_name not in self.get_module_exports(imported_module):
                            continue

                        resolved = self.resolve_symbol(imported_module, symbol_name, seen=seen)

                        if resolved is not None:
                            self._symbol_cache[cache_key] = resolved
                            return resolved

                        continue

                    exported_name = alias.asname or alias.name

                    if exported_name != symbol_name:
                        continue

                    if statement.module is None:
                        imported_submodule = f'{imported_module}.{alias.name}'

                        if self.module_exists(imported_submodule):
                            resolved = ResolvedSymbol(
                                module_name=imported_submodule,
                                name=alias.name,
                                kind='module',
                            )
                            self._symbol_cache[cache_key] = resolved
                            return resolved

                    resolved = self.resolve_symbol(imported_module, alias.name, seen=seen)

                    if resolved is not None:
                        self._symbol_cache[cache_key] = resolved
                        return resolved

                    if self.module_exists(imported_module):
                        resolved = ResolvedSymbol(module_name=imported_module, name=alias.name, kind='imported')
                        self._symbol_cache[cache_key] = resolved
                        return resolved

            elif isinstance(statement, ast.Import):
                for alias in statement.names:
                    exported_name = alias.asname or alias.name.split('.')[0]

                    if exported_name != symbol_name:
                        continue

                    resolved = ResolvedSymbol(module_name=alias.name, name=alias.name, kind='module')
                    self._symbol_cache[cache_key] = resolved
                    return resolved

        resolved = ResolvedSymbol(module_name=module_name, name=symbol_name, kind='unknown')
        self._symbol_cache[cache_key] = resolved
        return resolved

    def extract_class_resources(self, class_node: ast.ClassDef, path: str) -> list[ApiResource]:
        """Extract the public API resources from a class definition."""
        resources: dict[str, ApiResource] = {path: ApiResource(path=path, kind='class')}

        for statement in class_node.body:
            if isinstance(statement, ast.ClassDef):
                if statement.name.startswith('_'):
                    continue

                nested_path = f'{path}.{statement.name}'

                for resource in self.extract_class_resources(statement, nested_path):
                    resources[resource.path] = resource

            elif isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if statement.name.startswith('_'):
                    continue

                kind = _get_class_member_kind(statement)
                signature = None if kind == 'property' else _get_callable_signature(statement)
                method_path = f'{path}.{statement.name}'
                resources[method_path] = ApiResource(path=method_path, kind=kind, signature=signature)

            elif isinstance(statement, ast.Assign):
                for target in statement.targets:
                    if not isinstance(target, ast.Name) or target.id.startswith('_'):
                        continue

                    attribute_path = f'{path}.{target.id}'
                    resources[attribute_path] = ApiResource(path=attribute_path, kind='attribute')

            elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
                if statement.target.id.startswith('_'):
                    continue

                attribute_path = f'{path}.{statement.target.id}'
                resources[attribute_path] = ApiResource(path=attribute_path, kind='attribute')

        return sorted(resources.values(), key=lambda resource: resource.path)

    def extract_resources(self, module_name: str, export_name: str) -> list[ApiResource]:
        """Extract the full public API resources for an exported name."""
        symbol = self.resolve_symbol(module_name, export_name)
        resource_path = f'{module_name}.{export_name}'

        if symbol is None:
            return [ApiResource(path=resource_path, kind='unknown')]

        if symbol.kind == 'class' and isinstance(symbol.node, ast.ClassDef):
            return self.extract_class_resources(symbol.node, resource_path)

        if symbol.kind == 'function' and isinstance(symbol.node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return [ApiResource(path=resource_path, kind='function', signature=_get_callable_signature(symbol.node))]

        return [ApiResource(path=resource_path, kind=symbol.kind)]


def _get_default_src_root() -> Path:
    """Return the default source root."""
    return Path(__file__).resolve().parents[1] / 'src' / 'aiida'


def _get_default_output() -> Path:
    """Return the default output path."""
    return Path(__file__).resolve().parents[1] / 'public_api.json'


def parse_arguments() -> argparse.Namespace:
    """Return the parsed command line arguments."""
    parser = argparse.ArgumentParser(
        prog='python utils/public_api.py',
        usage='python utils/public_api.py {diff|extract} ...',
        description=__doc__,
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    diff_parser = subparsers.add_parser('diff', help='Diff two public API snapshots.')
    diff_parser.add_argument('file1', type=Path, help='The baseline public API snapshot.')
    diff_parser.add_argument('file2', nargs='?', type=Path, help='The public API snapshot to compare against.')
    diff_parser.add_argument(
        '--src-root',
        type=Path,
        default=_get_default_src_root(),
        help='Path to the aiida source package when diffing against the current checkout (default: %(default)s).',
    )
    diff_parser.add_argument(
        '--exit-code',
        action='store_true',
        help='Exit with status 1 if differences are found, similar to `git diff --exit-code`.',
    )

    extract_parser = subparsers.add_parser('extract', help='Extract the public API snapshot.')
    extract_parser.add_argument(
        '--src-root',
        type=Path,
        default=_get_default_src_root(),
        help='Path to the aiida source package (default: %(default)s).',
    )
    extract_parser.add_argument(
        '--output',
        type=Path,
        default=_get_default_output(),
        help='Path of the JSON file to write (default: %(default)s).',
    )

    return parser.parse_args()


def _parse_string_list(node: ast.AST) -> list[str] | None:
    """Return a literal list of strings if ``node`` represents one."""
    if not isinstance(node, (ast.List, ast.Tuple)):
        return None

    values: list[str] = []

    for element in node.elts:
        if not isinstance(element, ast.Constant) or not isinstance(element.value, str):
            return None
        values.append(element.value)

    return values


def _extract___all__(tree: ast.Module) -> list[str] | None:
    """Extract the literal ``__all__`` definition from a module, if present."""
    for statement in tree.body:
        if not isinstance(statement, ast.Assign):
            continue

        for target in statement.targets:
            if isinstance(target, ast.Name) and target.id == '__all__':
                return _parse_string_list(statement.value)

    return None


def _add_name(names: set[str], name: str) -> None:
    """Add a public name to the collection."""
    if not name.startswith('_'):
        names.add(name)


def _infer_exports_from_module(tree: ast.Module) -> list[str]:
    """Infer public exports from the top-level module body."""
    names: set[str] = set()

    for statement in tree.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            _add_name(names, statement.name)
        elif isinstance(statement, ast.Import):
            for alias in statement.names:
                _add_name(names, alias.asname or alias.name.split('.')[0])
        elif isinstance(statement, ast.ImportFrom):
            for alias in statement.names:
                if alias.name == '*':
                    continue
                _add_name(names, alias.asname or alias.name)
        elif isinstance(statement, ast.Assign):
            for target in statement.targets:
                if isinstance(target, ast.Name):
                    _add_name(names, target.id)
        elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
            _add_name(names, statement.target.id)

    return sorted(names)


def _get_class_member_kind(statement: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Return the public API kind for a class function definition."""
    for decorator in statement.decorator_list:
        if isinstance(decorator, ast.Name) and decorator.id == 'property':
            return 'property'

        if isinstance(decorator, ast.Attribute) and decorator.attr in {'getter', 'setter', 'deleter'}:
            return 'property'

    return 'method'


def _get_callable_signature(statement: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Return a callable signature."""
    return ast.unparse(statement.args)


class ApiExtractor:
    """Extract public API snapshots from the source tree."""

    def __init__(self, src_root: Path) -> None:
        """Initialize the extractor."""
        self.src_root = src_root
        self.resolver = SourceResolver(src_root)

    def extract_module_api(self, init_file: Path, module_name: str) -> ModuleApi:
        """Extract the public API for a module from its ``__init__.py`` file."""
        tree = ast.parse(init_file.read_text(encoding='utf8'))
        exports = _extract___all__(tree)

        if exports is None:
            exports = _infer_exports_from_module(tree)

        exports = sorted(set(exports))
        resources = sorted(
            {
                resource.path: resource
                for export_name in exports
                for resource in self.resolver.extract_resources(module_name, export_name)
            }.values(),
            key=lambda resource: resource.path,
        )
        return ModuleApi(exports=exports, resources=resources)

    def get_second_level_packages(self) -> list[Path]:
        """Return the second-level AiiDA packages."""
        return sorted(
            path
            for path in self.src_root.iterdir()
            if path.is_dir() and not path.name.startswith('_') and (path / '__init__.py').is_file()
        )

    def build_payload(self) -> dict[str, Any]:
        """Build the JSON payload."""
        modules: dict[str, ModuleApi] = {}

        top_level_module = 'aiida'
        modules[top_level_module] = self.extract_module_api(self.src_root / '__init__.py', top_level_module)

        for package in self.get_second_level_packages():
            module_name = f'aiida.{package.name}'
            modules[module_name] = self.extract_module_api(package / '__init__.py', module_name)

        resources = {
            resource.path: {'kind': resource.kind, 'signature': resource.signature}
            for module in modules.values()
            for resource in module.resources
        }

        return {'resources': dict(sorted(resources.items()))}


class SnapshotDiffer:
    """Diff public API snapshots."""

    @staticmethod
    def load_payload(path: Path) -> dict[str, Any]:
        """Load a JSON payload from disk."""
        return json.loads(path.read_text(encoding='utf8'))

    @staticmethod
    def build_resource_map(payload: dict[str, Any]) -> dict[str, ApiResource]:
        """Build a normalized resource map from a snapshot payload."""
        resource_map: dict[str, ApiResource] = {}

        raw_resources = payload.get('resources')

        if isinstance(raw_resources, dict):
            for path, metadata in raw_resources.items():
                if isinstance(metadata, dict):
                    resource_map[path] = ApiResource(
                        path=path,
                        kind=metadata.get('kind', 'unknown'),
                        signature=metadata.get('signature'),
                    )
                else:
                    resource_map[path] = ApiResource(path=path, kind='unknown')

            return dict(sorted(resource_map.items()))

        raw_resource_map = payload.get('resource_map')

        if isinstance(raw_resource_map, dict):
            for path, metadata in raw_resource_map.items():
                if isinstance(metadata, dict):
                    resource_map[path] = ApiResource(
                        path=path,
                        kind=metadata.get('kind', 'unknown'),
                        signature=metadata.get('signature'),
                    )
                else:
                    resource_map[path] = ApiResource(path=path, kind='unknown')

            return dict(sorted(resource_map.items()))

        raw_modules = payload.get('modules')

        if isinstance(raw_modules, dict):
            for module_name, module_data in raw_modules.items():
                if not isinstance(module_data, dict):
                    continue

                module_resources = module_data.get('resources')

                if isinstance(module_resources, list):
                    for resource in module_resources:
                        if isinstance(resource, dict):
                            path = resource['path']
                            resource_map[path] = ApiResource(
                                path=path,
                                kind=resource.get('kind', 'unknown'),
                                signature=resource.get('signature'),
                            )
                        elif isinstance(resource, str):
                            resource_map[resource] = ApiResource(path=resource, kind='unknown')

                    continue

                raw_exports = module_data.get('exports')

                if isinstance(raw_exports, list):
                    for export_name in raw_exports:
                        path = f'{module_name}.{export_name}'
                        resource_map[path] = ApiResource(path=path, kind='unknown')

        if not resource_map and isinstance(raw_resources, list):
            for resource in raw_resources:
                if isinstance(resource, str):
                    resource_map[resource] = ApiResource(path=resource, kind='unknown')
                elif isinstance(resource, dict):
                    path = resource['path']
                    resource_map[path] = ApiResource(
                        path=path,
                        kind=resource.get('kind', 'unknown'),
                        signature=resource.get('signature'),
                    )

        return dict(sorted(resource_map.items()))

    @staticmethod
    def is_changed_resource(old: ApiResource, new: ApiResource) -> bool:
        """Return whether the new resource is incompatible with the old one."""
        if old.kind not in {'', 'unknown'} and old.kind != new.kind:
            return True

        if old.signature is not None and old.signature != new.signature:
            return True

        return False

    @classmethod
    def diff_payloads(cls, old_payload: dict[str, Any], new_payload: dict[str, Any]) -> ApiDiff:
        """Diff two API snapshot payloads."""
        old_resources = cls.build_resource_map(old_payload)
        new_resources = cls.build_resource_map(new_payload)

        added = [new_resources[path] for path in sorted(new_resources.keys() - old_resources.keys())]
        removed = [old_resources[path] for path in sorted(old_resources.keys() - new_resources.keys())]
        changed = [
            {'old': old_resources[path], 'new': new_resources[path]}
            for path in sorted(old_resources.keys() & new_resources.keys())
            if cls.is_changed_resource(old_resources[path], new_resources[path])
        ]

        return ApiDiff(added=added, removed=removed, changed=changed)

    @staticmethod
    def format_diff(diff: ApiDiff, baseline: Path) -> str:
        """Return a human-readable API diff summary."""
        lines = [f'Compared public API against: {baseline}']

        if not diff.added and not diff.removed and not diff.changed:
            lines.append('No public API changes detected.')
            return '\n'.join(lines) + '\n'

        if diff.added:
            lines.append(f'Added ({len(diff.added)}):')
            lines.extend(_colorize(f'  + {resource.path} [{resource.kind}]', 'green') for resource in diff.added)

        if diff.removed:
            lines.append(f'Removed ({len(diff.removed)}):')
            lines.extend(_colorize(f'  - {resource.path} [{resource.kind}]', 'red') for resource in diff.removed)

        if diff.changed:
            lines.append(f'Changed ({len(diff.changed)}):')
            for change in diff.changed:
                old = change['old']
                new = change['new']
                lines.append(f'  ~ {old.path}:')
                lines.append(_colorize(f'    - {old.kind}{f" ({old.signature})" if old.signature else ""}', 'red'))
                lines.append(_colorize(f'    + {new.kind}{f" ({new.signature})" if new.signature else ""}', 'green'))

        if diff.removed or diff.changed:
            lines.append('Breaking public API changes detected.')
        else:
            lines.append('Public API extensions only.')

        return '\n'.join(lines) + '\n'

    @classmethod
    def print_diff(cls, diff: ApiDiff, baseline: Path) -> None:
        """Print a human-readable API diff summary."""
        _emit_output(cls.format_diff(diff, baseline))


def _supports_color() -> bool:
    """Return whether colored terminal output should be used."""
    return sys.stdout.isatty() and 'NO_COLOR' not in os.environ


def _should_page(text: str) -> bool:
    """Return whether the output should be shown through a pager."""
    if not sys.stdout.isatty() or 'TERM' not in os.environ:
        return False

    terminal_lines = shutil.get_terminal_size(fallback=(80, 24)).lines
    output_lines = text.count('\n')
    return output_lines > terminal_lines


def _emit_output(text: str) -> None:
    """Emit output directly or through a pager depending on terminal size."""
    if not _should_page(text):
        sys.stdout.write(text)
        return

    pager = shlex.split(os.environ.get('PAGER', 'less -R'))

    try:
        subprocess.run(pager, input=text, text=True, check=False)
    except FileNotFoundError:
        sys.stdout.write(text)


def _colorize(text: str, color: str) -> str:
    """Return colored terminal output if supported."""
    if not _supports_color():
        return text

    colors = {
        'red': '\033[31m',
        'green': '\033[32m',
    }
    reset = '\033[0m'
    return f'{colors[color]}{text}{reset}'


def _validate_src_root(src_root: Path) -> None:
    """Validate that the source root exists."""
    if not src_root.is_dir():
        msg = f'The source root does not exist: {src_root}'
        raise FileNotFoundError(msg)


def _extract_snapshot(src_root: Path, output: Path) -> None:
    """Extract the public API snapshot to a file."""
    _validate_src_root(src_root)
    payload = ApiExtractor(src_root).build_payload()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf8')


def _diff_snapshots(file1: Path, file2: Path | None, src_root: Path) -> ApiDiff:
    """Diff two snapshots or a snapshot against the current checkout."""
    if not file1.is_file():
        msg = f'The snapshot does not exist: {file1}'
        raise FileNotFoundError(msg)

    baseline = SnapshotDiffer.load_payload(file1)

    if file2 is None:
        _validate_src_root(src_root)
        payload = ApiExtractor(src_root).build_payload()
        diff = SnapshotDiffer.diff_payloads(baseline, payload)
        SnapshotDiffer.print_diff(diff, file1)
        return diff

    if not file2.is_file():
        msg = f'The snapshot does not exist: {file2}'
        raise FileNotFoundError(msg)

    comparison = SnapshotDiffer.load_payload(file2)
    diff = SnapshotDiffer.diff_payloads(baseline, comparison)
    SnapshotDiffer.print_diff(diff, file1)
    return diff


def _has_differences(diff: ApiDiff) -> bool:
    """Return whether a diff contains any changes."""
    return bool(diff.added or diff.removed or diff.changed)


def main() -> None:
    """Run the script."""
    arguments = parse_arguments()

    if arguments.command == 'extract':
        _extract_snapshot(arguments.src_root, arguments.output)
        return

    if arguments.command == 'diff':
        diff = _diff_snapshots(arguments.file1, arguments.file2, arguments.src_root)

        if arguments.exit_code and _has_differences(diff):
            sys.exit(1)
        return

    msg = f'Unknown command: {arguments.command}'
    raise ValueError(msg)


if __name__ == '__main__':
    main()
