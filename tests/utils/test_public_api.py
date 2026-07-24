###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for ``utils/public_api.py``."""

from __future__ import annotations

import json
import os
import runpy
import sys
import tempfile
from pathlib import Path

os.environ.setdefault('AIIDA_PATH', tempfile.mkdtemp())


def load_public_api_module() -> dict[str, object]:
    """Load the public_api utility module."""
    module_path = Path(__file__).resolve().parents[2] / 'utils' / 'public_api.py'
    return runpy.run_path(str(module_path))


def test_extract_module_api_recurses_into_public_classes(tmp_path):
    """Public class members and nested classes should be included recursively."""
    src_root = tmp_path / 'src' / 'aiida'
    src_root.mkdir(parents=True)

    (src_root / '__init__.py').write_text(
        "from .submodule import PublicClass, public_function\n__all__ = ('PublicClass', 'public_function')\n",
        encoding='utf8',
    )
    (src_root / 'submodule.py').write_text(
        'class PublicClass:\n'
        "    CLASS_ATTRIBUTE = 'value'\n"
        '\n'
        '    class Nested:\n'
        "        NESTED_ATTRIBUTE = 'value'\n"
        '\n'
        '        def nested_method(self):\n'
        '            return None\n'
        '\n'
        '    @property\n'
        '    def label(self):\n'
        '        return None\n'
        '\n'
        '    @label.setter\n'
        '    def label(self, value):\n'
        '        return None\n'
        '\n'
        '    async def async_method(self, value: int | None = None):\n'
        '        return None\n'
        '\n'
        '    def public_method(self, value: str, /, flag: bool = False):\n'
        '        return None\n'
        '\n'
        '    def _private_method(self):\n'
        '        return None\n'
        '\n'
        'def public_function(value: int, label: str | None = None):\n'
        '    return None\n',
        encoding='utf8',
    )

    module = load_public_api_module()
    extractor = module['ApiExtractor'](src_root)
    api = extractor.extract_module_api(src_root / '__init__.py', 'aiida')

    resources = {resource.path: resource for resource in api.resources}

    assert resources['aiida.PublicClass'].kind == 'class'
    assert resources['aiida.PublicClass.CLASS_ATTRIBUTE'].kind == 'attribute'
    assert resources['aiida.PublicClass.Nested'].kind == 'class'
    assert resources['aiida.PublicClass.Nested.NESTED_ATTRIBUTE'].kind == 'attribute'
    assert resources['aiida.PublicClass.Nested.nested_method'].kind == 'method'
    assert resources['aiida.PublicClass.Nested.nested_method'].signature == 'self'
    assert resources['aiida.PublicClass.async_method'].kind == 'method'
    assert resources['aiida.PublicClass.async_method'].signature == 'self, value: int | None=None'
    assert resources['aiida.PublicClass.label'].kind == 'property'
    assert resources['aiida.PublicClass.label'].signature is None
    assert resources['aiida.PublicClass.public_method'].kind == 'method'
    assert resources['aiida.PublicClass.public_method'].signature == 'self, value: str, /, flag: bool=False'
    assert resources['aiida.public_function'].kind == 'function'
    assert resources['aiida.public_function'].signature == 'value: int, label: str | None=None'
    assert 'aiida.PublicClass._private_method' not in resources
    assert list(resources).count('aiida.PublicClass.label') == 1


def test_build_payload_resolves_reexported_classes_from_star_imports(tmp_path):
    """Re-exported classes should include their nested public API."""
    src_root = tmp_path / 'src' / 'aiida'
    orm_root = src_root / 'orm'
    orm_root.mkdir(parents=True)

    (src_root / '__init__.py').write_text('__all__ = ()\n', encoding='utf8')
    (orm_root / '__init__.py').write_text("from .nodes import *\n__all__ = ('Node',)\n", encoding='utf8')
    (orm_root / 'nodes.py').write_text(
        'class Node:\n'
        '    class Manager:\n'
        '        def all(self):\n'
        '            return []\n'
        '\n'
        '    def store(self):\n'
        '        return self\n',
        encoding='utf8',
    )

    module = load_public_api_module()
    payload = module['ApiExtractor'](src_root).build_payload()

    resources = payload['resources']

    assert len(resources) == 4
    assert resources['aiida.orm.Node']['kind'] == 'class'
    assert resources['aiida.orm.Node.Manager']['kind'] == 'class'
    assert resources['aiida.orm.Node.Manager.all']['kind'] == 'method'
    assert resources['aiida.orm.Node.Manager.all']['signature'] == 'self'
    assert resources['aiida.orm.Node.store']['kind'] == 'method'
    assert resources['aiida.orm.Node.store']['signature'] == 'self'


def test_diff_payloads_classifies_extensions_and_breaking_changes(tmp_path):
    """The diff should distinguish additions from breaking changes."""
    src_root = tmp_path / 'src' / 'aiida'
    src_root.mkdir(parents=True)

    (src_root / '__init__.py').write_text(
        "from .submodule import PublicClass, public_function\n__all__ = ('PublicClass', 'public_function')\n",
        encoding='utf8',
    )
    (src_root / 'submodule.py').write_text(
        'class PublicClass:\n'
        '    def method(self, value):\n'
        '        return value\n'
        '\n'
        'def public_function(value):\n'
        '    return value\n',
        encoding='utf8',
    )

    module = load_public_api_module()
    baseline = module['ApiExtractor'](src_root).build_payload()

    changed_payload = json.loads(json.dumps(baseline))
    changed_payload['resources']['aiida.PublicClass.method']['signature'] = 'self, value, extra=None'
    changed_payload['resources']['aiida.public_function'] = {'kind': 'function', 'signature': 'value'}
    changed_payload['resources']['aiida.PublicClass.new_method'] = {'kind': 'method', 'signature': 'self'}

    diff = module['SnapshotDiffer'].diff_payloads(baseline, changed_payload)

    assert [resource.path for resource in diff.added] == ['aiida.PublicClass.new_method']
    assert [resource.path for resource in diff.removed] == []
    assert len(diff.changed) == 1
    assert diff.changed[0]['old'].path == 'aiida.PublicClass.method'
    assert diff.changed[0]['new'].signature == 'self, value, extra=None'


def test_diff_payloads_accepts_older_export_only_snapshots():
    """Older snapshots without resource metadata should still be comparable."""
    module = load_public_api_module()
    old_payload = {
        'modules': {
            'aiida': {
                'exports': ['PublicClass'],
            }
        }
    }
    new_payload = {
        'modules': {
            'aiida': {
                'resources': [
                    {'path': 'aiida.PublicClass', 'kind': 'class', 'signature': None},
                    {'path': 'aiida.PublicClass.method', 'kind': 'method', 'signature': 'self'},
                ]
            }
        }
    }

    diff = module['SnapshotDiffer'].diff_payloads(old_payload, new_payload)

    assert [resource.path for resource in diff.added] == ['aiida.PublicClass.method']
    assert diff.removed == []
    assert diff.changed == []


def test_parse_arguments_extract_and_diff(monkeypatch, tmp_path):
    """The CLI should expose ``extract`` and ``diff`` subcommands."""
    module = load_public_api_module()
    output = tmp_path / 'public-api.json'
    baseline = tmp_path / 'baseline.json'
    comparison = tmp_path / 'comparison.json'

    monkeypatch.setattr(sys, 'argv', ['public_api.py', 'extract', '--src-root', 'src/aiida', '--output', str(output)])
    arguments = module['parse_arguments']()

    assert arguments.command == 'extract'
    assert arguments.src_root == Path('src/aiida')
    assert arguments.output == output

    monkeypatch.setattr(sys, 'argv', ['public_api.py', 'diff', str(baseline)])
    arguments = module['parse_arguments']()

    assert arguments.command == 'diff'
    assert arguments.file1 == baseline
    assert arguments.file2 is None
    assert arguments.exit_code is False

    monkeypatch.setattr(sys, 'argv', ['public_api.py', 'diff', '--exit-code', str(baseline)])
    arguments = module['parse_arguments']()

    assert arguments.command == 'diff'
    assert arguments.file1 == baseline
    assert arguments.file2 is None
    assert arguments.exit_code is True

    monkeypatch.setattr(sys, 'argv', ['public_api.py', 'diff', str(baseline), str(comparison)])
    arguments = module['parse_arguments']()

    assert arguments.command == 'diff'
    assert arguments.file1 == baseline
    assert arguments.file2 == comparison


def test_diff_snapshots_compares_baseline_with_current_checkout(tmp_path):
    """If the second file is omitted, diff against the current source tree."""
    src_root = tmp_path / 'src' / 'aiida'
    src_root.mkdir(parents=True)

    (src_root / '__init__.py').write_text(
        "from .submodule import PublicClass\n__all__ = ('PublicClass',)\n",
        encoding='utf8',
    )
    (src_root / 'submodule.py').write_text(
        'class PublicClass:\n    def method(self):\n        return None\n',
        encoding='utf8',
    )

    module = load_public_api_module()
    baseline_path = tmp_path / 'baseline.json'
    baseline_path.write_text(json.dumps(module['ApiExtractor'](src_root).build_payload()), encoding='utf8')

    (src_root / 'submodule.py').write_text(
        'class PublicClass:\n'
        '    def method(self):\n'
        '        return None\n'
        '\n'
        '    def new_method(self):\n'
        '        return None\n',
        encoding='utf8',
    )

    diff = module['_diff_snapshots'](baseline_path, None, src_root)

    assert [resource.path for resource in diff.added] == ['aiida.PublicClass.new_method']
    assert diff.removed == []
    assert diff.changed == []


def test_has_differences():
    """Return whether a diff contains any changes."""
    module = load_public_api_module()

    assert module['_has_differences'](module['ApiDiff'](added=[], removed=[], changed=[])) is False
    assert (
        module['_has_differences'](
            module['ApiDiff'](added=[module['ApiResource']('a', 'class')], removed=[], changed=[])
        )
        is True
    )


def test_print_diff_formats_changed_resources(capsys, tmp_path):
    """Changed resources should be printed on separate removed/added lines."""
    module = load_public_api_module()
    diff = module['ApiDiff'](
        added=[],
        removed=[],
        changed=[
            {
                'old': module['ApiResource'](
                    path='aiida.orm.ProcessNode.set_exit_status',
                    kind='method',
                    signature='self, status: enum.Enum | int | None',
                ),
                'new': module['ApiResource'](
                    path='aiida.orm.ProcessNode.set_exit_status',
                    kind='method',
                    signature='self, status: enum.Enum | int | None=None',
                ),
            }
        ],
    )

    module['SnapshotDiffer'].print_diff(diff, tmp_path / 'baseline.json')
    output = capsys.readouterr().out

    assert '  ~ aiida.orm.ProcessNode.set_exit_status:' in output
    assert '    - method (self, status: enum.Enum | int | None)' in output
    assert '    + method (self, status: enum.Enum | int | None=None)' in output
