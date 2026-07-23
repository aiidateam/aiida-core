###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Regression tests for ``utils/public_api.py``.

These tests exercise the tool exclusively through its command-line contract
(``extract`` and ``diff``), asserting only on observable outputs: the extracted
JSON snapshot, the diff summary printed to stdout, and the process exit code.
They deliberately avoid the internal extraction classes so the suite pins
*behaviour* rather than *implementation* -- swapping the AST-based extractor for
an import-based one only needs to keep the same CLI contract passing.

The handful of assertions on exact signature strings (e.g. ``value: int=1``)
reflect the current renderer; an import-based backend renders signatures with
slightly different spacing, so those expected strings are the intended point of
adaptation when the backend changes.
"""

from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _aiida_path(monkeypatch, tmp_path):
    """Point ``AIIDA_PATH`` at an isolated directory for the duration of each test."""
    monkeypatch.setenv('AIIDA_PATH', str(tmp_path))


def load_public_api_module() -> dict[str, object]:
    """Load the public_api utility module."""
    module_path = Path(__file__).resolve().parents[2] / 'utils' / 'public_api.py'
    return runpy.run_path(str(module_path))


def _write_package(src_root: Path, files: dict[str, str]) -> None:
    """Write a synthetic ``aiida`` source package from a ``relative path -> content`` mapping."""
    for relative_path, content in files.items():
        path = src_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf8')


@pytest.fixture
def cli(monkeypatch, capsys):
    """Return a helper that runs ``public_api.py`` as if from the command line.

    The helper returns ``(exit_code, stdout)`` for each invocation and can be
    called multiple times within a test (e.g. extract then diff).
    """
    module = load_public_api_module()

    def run(*argv: str) -> tuple[int, str]:
        monkeypatch.setattr(sys, 'argv', ['public_api.py', *argv])
        exit_code = 0
        try:
            module['main']()
        except SystemExit as exc:
            if exc.code is None:
                exit_code = 0
            elif isinstance(exc.code, int):
                exit_code = exc.code
            else:
                exit_code = 1
        return exit_code, capsys.readouterr().out

    return run


def test_extract_writes_snapshot_with_recursive_class_api(tmp_path, cli):
    """``extract`` records public classes, their members and nested classes, excluding privates."""
    src_root = tmp_path / 'src' / 'aiida'
    _write_package(
        src_root,
        {
            '__init__.py': (
                "from .submodule import PublicClass, public_function\n__all__ = ('PublicClass', 'public_function')\n"
            ),
            'submodule.py': (
                'class PublicClass:\n'
                "    CLASS_ATTRIBUTE = 'value'\n"
                '\n'
                '    class Nested:\n'
                '        def nested_method(self):\n'
                '            return None\n'
                '\n'
                '    @property\n'
                '    def label(self):\n'
                '        return None\n'
                '\n'
                '    def public_method(self, value: str, /, flag: bool = False):\n'
                '        return None\n'
                '\n'
                '    def _private_method(self):\n'
                '        return None\n'
                '\n'
                'def public_function(value: int, label: str | None = None):\n'
                '    return None\n'
            ),
        },
    )
    output = tmp_path / 'api.json'

    exit_code, _ = cli('extract', '--src-root', str(src_root), '--output', str(output))

    assert exit_code == 0
    resources = json.loads(output.read_text(encoding='utf8'))['resources']
    assert resources['aiida.PublicClass']['kind'] == 'class'
    assert resources['aiida.PublicClass.CLASS_ATTRIBUTE']['kind'] == 'attribute'
    assert resources['aiida.PublicClass.Nested']['kind'] == 'class'
    assert resources['aiida.PublicClass.Nested.nested_method']['kind'] == 'method'
    assert resources['aiida.PublicClass.label']['kind'] == 'property'
    assert resources['aiida.PublicClass.label']['signature'] is None
    assert resources['aiida.PublicClass.public_method']['kind'] == 'method'
    assert resources['aiida.public_function']['kind'] == 'function'
    assert 'aiida.PublicClass._private_method' not in resources


def test_extract_resolves_reexported_classes_from_star_imports(tmp_path, cli):
    """``extract`` follows star-imports in second-level packages and recurses into the class API."""
    src_root = tmp_path / 'src' / 'aiida'
    _write_package(
        src_root,
        {
            '__init__.py': '__all__ = ()\n',
            'orm/__init__.py': "from .nodes import *\n__all__ = ('Node',)\n",
            'orm/nodes.py': (
                'class Node:\n'
                '    class Manager:\n'
                '        def all(self):\n'
                '            return []\n'
                '\n'
                '    def store(self):\n'
                '        return self\n'
            ),
        },
    )
    output = tmp_path / 'api.json'

    exit_code, _ = cli('extract', '--src-root', str(src_root), '--output', str(output))

    assert exit_code == 0
    resources = json.loads(output.read_text(encoding='utf8'))['resources']
    assert resources['aiida.orm.Node']['kind'] == 'class'
    assert resources['aiida.orm.Node.Manager']['kind'] == 'class'
    assert resources['aiida.orm.Node.Manager.all']['kind'] == 'method'
    assert resources['aiida.orm.Node.store']['kind'] == 'method'


def test_diff_reports_additions_and_breaking_changes(tmp_path, cli):
    """``diff`` distinguishes an added member from a breaking signature change."""
    src_root = tmp_path / 'src' / 'aiida'
    _write_package(
        src_root,
        {
            '__init__.py': "from .submodule import PublicClass\n__all__ = ('PublicClass',)\n",
            'submodule.py': ('class PublicClass:\n    def method(self, value):\n        return value\n'),
        },
    )
    baseline = tmp_path / 'baseline.json'
    cli('extract', '--src-root', str(src_root), '--output', str(baseline))

    _write_package(
        src_root,
        {
            'submodule.py': (
                'class PublicClass:\n'
                '    def method(self, value, extra=None):\n'
                '        return value\n'
                '\n'
                '    def new_method(self):\n'
                '        return self\n'
            ),
        },
    )
    comparison = tmp_path / 'comparison.json'
    cli('extract', '--src-root', str(src_root), '--output', str(comparison))

    exit_code, output = cli('diff', str(baseline), str(comparison))

    assert exit_code == 0
    assert 'Added (1):' in output
    assert '+ aiida.PublicClass.new_method' in output
    assert 'Changed (1):' in output
    assert '~ aiida.PublicClass.method' in output
    assert 'Changes possibly break the public API.' in output


def test_diff_against_current_checkout_reports_extension(tmp_path, cli):
    """Omitting the second snapshot diffs the baseline against the current ``--src-root`` tree."""
    src_root = tmp_path / 'src' / 'aiida'
    _write_package(
        src_root,
        {
            '__init__.py': "from .submodule import PublicClass\n__all__ = ('PublicClass',)\n",
            'submodule.py': 'class PublicClass:\n    def method(self):\n        return None\n',
        },
    )
    baseline = tmp_path / 'baseline.json'
    cli('extract', '--src-root', str(src_root), '--output', str(baseline))

    _write_package(
        src_root,
        {
            'submodule.py': (
                'class PublicClass:\n'
                '    def method(self):\n'
                '        return None\n'
                '\n'
                '    def new_method(self):\n'
                '        return None\n'
            ),
        },
    )

    exit_code, output = cli('diff', str(baseline), '--src-root', str(src_root))

    assert exit_code == 0
    assert '+ aiida.PublicClass.new_method' in output
    assert 'Changes extend the public API.' in output


def test_diff_exit_code_reflects_differences(tmp_path, cli):
    """``--exit-code`` returns 0 on an unchanged API and 1 once a difference appears."""
    src_root = tmp_path / 'src' / 'aiida'
    _write_package(
        src_root,
        {
            '__init__.py': "from .submodule import PublicClass\n__all__ = ('PublicClass',)\n",
            'submodule.py': 'class PublicClass:\n    def method(self):\n        return None\n',
        },
    )
    baseline = tmp_path / 'baseline.json'
    cli('extract', '--src-root', str(src_root), '--output', str(baseline))

    exit_code, output = cli('diff', '--exit-code', str(baseline), '--src-root', str(src_root))
    assert exit_code == 0
    assert 'No public API changes detected.' in output

    _write_package(
        src_root,
        {
            'submodule.py': (
                'class PublicClass:\n'
                '    def method(self):\n'
                '        return None\n'
                '\n'
                '    def new_method(self):\n'
                '        return None\n'
            ),
        },
    )

    exit_code, _ = cli('diff', '--exit-code', str(baseline), '--src-root', str(src_root))
    assert exit_code == 1


def test_diff_formats_changed_resource_lines(tmp_path, cli):
    """A changed member is rendered as a ``~`` header with paired ``-``/``+`` signature lines."""
    src_root = tmp_path / 'src' / 'aiida'
    _write_package(
        src_root,
        {
            '__init__.py': "from .submodule import PublicClass\n__all__ = ('PublicClass',)\n",
            'submodule.py': 'class PublicClass:\n    def method(self, value):\n        return value\n',
        },
    )
    baseline = tmp_path / 'baseline.json'
    cli('extract', '--src-root', str(src_root), '--output', str(baseline))

    _write_package(
        src_root,
        {'submodule.py': 'class PublicClass:\n    def method(self, value, extra=None):\n        return value\n'},
    )

    _, output = cli('diff', str(baseline), '--src-root', str(src_root))

    assert '  ~ aiida.PublicClass.method:' in output
    assert '    - method (self, value)' in output
    assert '    + method (self, value, extra=None)' in output


def test_diff_detects_constructor_signature_change(tmp_path, cli):
    """A changed public constructor signature is reported as a breaking change."""
    src_root = tmp_path / 'src' / 'aiida'
    _write_package(
        src_root,
        {
            '__init__.py': "from .submodule import PublicClass\n__all__ = ('PublicClass',)\n",
            'submodule.py': 'class PublicClass:\n    def __init__(self, value: int):\n        self.value = value\n',
        },
    )
    baseline = tmp_path / 'baseline.json'
    cli('extract', '--src-root', str(src_root), '--output', str(baseline))

    _write_package(
        src_root,
        {
            'submodule.py': (
                'class PublicClass:\n'
                '    def __init__(self, value: int, *, flag: bool = False):\n'
                '        self.value = value\n'
            ),
        },
    )

    exit_code, output = cli('diff', str(baseline), '--src-root', str(src_root))

    assert exit_code == 0
    assert '  ~ aiida.PublicClass:' in output
    assert '    - class (value: int)' in output
    assert '    + class (value: int, *, flag: bool=False)' in output


def test_diff_detects_added_constructor_on_previously_inherited_init(tmp_path, cli):
    """Gaining an own ``__init__`` (inherited before, so no recorded signature) is breaking."""
    src_root = tmp_path / 'src' / 'aiida'
    _write_package(
        src_root,
        {
            '__init__.py': "from .submodule import PublicClass\n__all__ = ('PublicClass',)\n",
            'submodule.py': 'class PublicClass:\n    pass\n',
        },
    )
    baseline = tmp_path / 'baseline.json'
    cli('extract', '--src-root', str(src_root), '--output', str(baseline))

    _write_package(
        src_root,
        {'submodule.py': 'class PublicClass:\n    def __init__(self, value: int):\n        self.value = value\n'},
    )

    exit_code, output = cli('diff', str(baseline), '--src-root', str(src_root))

    assert exit_code == 0
    assert '  ~ aiida.PublicClass:' in output
    assert '    - class' in output
    assert '    + class (value: int)' in output
    assert 'Changes possibly break the public API.' in output


def test_diff_accepts_older_export_only_snapshots(tmp_path, cli):
    """A legacy ``modules``/``exports`` baseline snapshot is still comparable via the CLI."""
    baseline = tmp_path / 'baseline.json'
    baseline.write_text(
        json.dumps({'modules': {'aiida': {'exports': ['PublicClass']}}}),
        encoding='utf8',
    )
    comparison = tmp_path / 'comparison.json'
    comparison.write_text(
        json.dumps(
            {
                'resources': {
                    'aiida.PublicClass': {'kind': 'class', 'signature': None},
                    'aiida.PublicClass.method': {'kind': 'method', 'signature': 'self'},
                }
            }
        ),
        encoding='utf8',
    )

    exit_code, output = cli('diff', str(baseline), str(comparison))

    assert exit_code == 0
    assert 'Added (1):' in output
    assert '+ aiida.PublicClass.method' in output
    assert 'Removed' not in output
