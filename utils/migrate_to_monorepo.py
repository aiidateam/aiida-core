#!/usr/bin/env python
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Migrate the ``aiida-core`` repository to a monorepo layout.

The idea is to move the ``aiida-core`` package (sources, tests, docs and
packaging metadata) into an ``aiida-core/`` subdirectory, while developer
tooling (``.github/``, ``.docker/``, ``utils/``, ``pixi.toml``,
``.pre-commit-config.yaml``, ...) stays at the repository root.  Additional
subpackages (e.g. ``aiida-plugin-template/``) can then be added next to
``aiida-core/`` without interfering with each other.

Usage:
    python utils/migrate_to_monorepo.py            # dry run, only prints the plan
    python utils/migrate_to_monorepo.py --execute  # perform the move with ``git mv``
    python utils/migrate_to_monorepo.py --full     # move, commit, verify and amend fixes

The script is idempotent: already-moved paths are skipped and text patches
are written to not match twice, so re-running it is safe.

What it does:
    1. ``git mv`` package paths (``src/``, ``tests/``, ``docs/``,
       ``pyproject.toml``, ``uv.lock``, ``README.md``, ...) to ``aiida-core/``.
    2. Rewrites repo-relative path references in developer tooling
       (pre-commit config, CI workflows, install action, ReadTheDocs config,
       codecov config, Dockerfiles, ``utils/*.py`` helpers).
    3. Adjusts ``aiida-core/pyproject.toml`` (sdist excludes that pointed at
       repo-root files, changelog URL) and leaves a stub ``README.md`` at the
       root pointing at the new package location.
    4. Restructures ``.github/`` for per-package CI: the install action becomes
       package-agnostic (``install-package``) so new subpackages reuse it, a
       reusable pytest workflow is added as a template for package CI, and
       ``CODEOWNERS`` follows the moved packaging files.
    5. Extracts ``[tool.mypy]`` into a shared root ``mypy.toml`` (referenced
       explicitly since mypy does not auto-discover it) and points the hook
       at it.

Only the standard library is used on purpose, so the script also runs on a
bare checkout without dependencies installed.
"""

from __future__ import annotations

import argparse
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Paths relative to the repository root that belong to the ``aiida-core``
# package and therefore move into the ``<package-dir>/`` subdirectory.
PACKAGE_PATHS = [
    'src',
    'tests',
    'docs',
    'pyproject.toml',
    'uv.lock',
    'README.md',
    'LICENSE.txt',
    'AUTHORS.txt',
    'CHANGELOG.md',
    'open_source_licenses.txt',
    'environment.yml',
]

# Workflow files that run with ``working-directory: .docker``: a bare
# ``tests/`` there refers to ``.docker/tests/`` (which stays put) and must
# not be rewritten; only ``paths:``/``paths-ignore:`` filters are touched.
DOCKER_WORKDIR_WORKFLOWS = {'docker-build-test.yml', 'docker-test.yml'}

# Matches a bare ``docs/`` or ``tests/`` path segment that is *not* already
# prefixed with ``aiida-core/`` (or part of a URL / longer word).
BARE_PACKAGE_DIR = re.compile(r'(?<![\w/.-])(docs|tests)/')

ROOT_RUFF_TOML = """\
# Monorepo root ruff config for developer tooling that stays outside `aiida-core/`
# (`utils/`, `.github/`, `.docker/`, `.molecule/`).
#
# Ruff discovers its configuration by walking up from each linted file, so once
# the package `pyproject.toml` moves into `aiida-core/`, root-level files would
# silently fall back to ruff defaults (e.g. double quotes). Instead, the style
# settings are shared from the package config (single source of truth) and only
# `target-version` is repeated here: unlike the package, root files have no
# `requires-python` to infer it from.
#
# A second subpackage reuses this pattern with its own extends (or root file).

extend = 'aiida-core/pyproject.toml'
target-version = 'py310'

# `aiida` stays first-party even though no `src/` layout is visible from here.
[lint.isort]
known-first-party = ["aiida"]
"""

ROOT_README_STUB = """\
# AiiDA monorepo

This repository hosts multiple Python subpackages, each in its own
directory with its own `pyproject.toml`.

## Packages

- [`aiida-core/`](aiida-core/) — the AiiDA workflow manager
  ([README](aiida-core/README.md), [changelog](aiida-core/CHANGELOG.md)).

## Development

Developer tooling (CI workflows, pre-commit config, Docker setups and helper
scripts) stays at the repository root:

- `pixi.toml` — development environment definition
- `.pre-commit-config.yaml` — linting / formatting hooks
- `utils/` — helper scripts (dependency management, consistency checks)
- `.github/` — CI workflows and issue templates
- `.docker/` — container images for testing and development

See [`aiida-core/README.md`](aiida-core/README.md) for package-specific
documentation.
"""

REUSABLE_PYTEST_YML = """\
# Reusable workflow running a subpackage's pytest suite in the shared test
# environment (PostgreSQL + RabbitMQ services, SSH, AiiDA test profile).
#
# A new subpackage gets its own CI with a thin caller workflow, e.g.:
#
# ```yaml
# name: my-package-ci
#
# on:
#   push:
#     branches-ignore: [gh-pages]
#   pull_request:
#     paths: ['my-package/**']
#
# jobs:
#   pytest:
#     uses: ./.github/workflows/reusable-pytest.yml
#     with:
#       package: my-package
#       python-version: '3.11'
#       test-path: tests/  # relative to the package dir; the test step
#                          # runs with `working-directory: <package>` so
#                          # `tests/conftest.py` options resolve
# ```
#
# Jobs needing extra services (e.g. Slurm) or custom steps stay in the
# package's own workflow file, reusing the `install-package` action.

name: reusable-pytest

on:
  workflow_call:
    inputs:
      package:
        description: Subpackage directory containing the project
        default: aiida-core
        required: false
        type: string
      python-version:
        description: Python version
        default: '3.10'
        required: false
        type: string
      test-path:
        description: Test path (relative to the package directory) passed to pytest
        default: ''
        required: false
        type: string
      pytest-args:
        description: Extra pytest arguments
        default: -m 'not nightly'
        required: false
        type: string
      extras:
        description: Optional dependencies to install
        default: ''
        required: false
        type: string
      from-lock:
        description: Install dependencies from the uv lock file
        default: 'true'
        required: false
        type: string
      warn-v3:
        description: Value of the AIIDA_WARN_v3 environment variable
        default: '1'
        required: false
        type: string
      setup-profile:
        description: Provision the full AiiDA test profile instead of SSH only
        default: false
        required: false
        type: boolean
      test-profile:
        description: Value of AIIDA_TEST_PROFILE (empty for jobs without a profile, e.g. presto)
        default: test_aiida
        required: false
        type: string

jobs:

  pytest:

    runs-on: ubuntu-24.04
    timeout-minutes: 45

    services:
      postgres:
        image: postgres:10
        env:
          POSTGRES_DB: test_aiida
          POSTGRES_PASSWORD: ''
          POSTGRES_HOST_AUTH_METHOD: trust
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
        - 5432:5432
      rabbitmq:
        image: rabbitmq:3.8.14-management
        ports:
        - 5672:5672
        - 15672:15672

    steps:
    - uses: actions/checkout@v7

    - name: Install system dependencies
      run: sudo apt update && sudo apt install postgresql graphviz

    - name: Install package
      uses: ./.github/actions/install-package
      with:
        package: ${{ inputs.package }}
        python-version: ${{ inputs.python-version }}
        extras: ${{ inputs.extras }}
        from-lock: ${{ inputs.from-lock }}

    - name: Setup SSH on localhost
      if: ${{ !inputs.setup-profile }}
      run: .github/workflows/setup_ssh.sh

    - name: Install aiida-atomistic into package venv for shims
      # Core suites import moved types via shims (see ci-code.yml).
      # No-op for other packages. Explicit `--python` + `--no-deps`:
      # plain installs ignore `tool.uv.sources` and overwrite local core
      # with PyPI; core test venv already provides ase etc., only
      # upf_to_json (dropped from core) is added explicitly.
      if: ${{ inputs.package == 'aiida-core' }}
      run: |
        uv pip install --python ${{ inputs.package }}/.venv/bin/python --no-deps -e ./aiida-atomistic
        uv pip install --python ${{ inputs.package }}/.venv/bin/python 'upf_to_json~=0.9.2'
      shell: bash

    - name: Setup environment
      if: ${{ inputs.setup-profile }}
      run: .github/workflows/setup.sh

    - name: Run test suite
      # Run from the package directory: `tests/conftest.py` registers
      # custom options (`--db-backend`, `--broker-backend`) via
      # `pytest_addoption`, which pytest only picks up when `tests` is
      # importable at option-parsing time (cwd on `sys.path`).
      working-directory: ${{ inputs.package }}
      env:
        AIIDA_TEST_PROFILE: ${{ inputs.test-profile }}
        AIIDA_WARN_v3: ${{ inputs.warn-v3 }}
      run: pytest -n auto ${{ inputs.pytest-args }} ${{ inputs.test-path }}
"""


@dataclass
class PatchResult:
    """Outcome of patching a single file."""

    path: str
    replacements: int = 0
    skipped: bool = False
    note: str = ''


@dataclass
class Migration:
    """State and helpers for the monorepo migration."""

    root: Path
    package_dir: str
    dry_run: bool
    results: list[PatchResult] = field(default_factory=list)

    @property
    def package_path(self) -> Path:
        """Absolute path of the ``aiida-core/`` subdirectory."""
        return self.root / self.package_dir

    @staticmethod
    def _is_stub(path: Path) -> bool:
        """Check whether ``path`` holds the generated monorepo stub README."""
        return path.is_file() and path.read_text(encoding='utf8') == ROOT_README_STUB

    def run_git(self, *args: str) -> subprocess.CompletedProcess[str]:
        """Run a git command in the repository root."""
        return subprocess.run(['git', *args], cwd=self.root, capture_output=True, text=True, check=False)

    def move_package_paths(self) -> None:
        """Move package paths into the subdirectory using ``git mv``."""
        for rel in PACKAGE_PATHS:
            src = self.root / rel
            dst = self.package_path / rel
            if not src.exists() and dst.exists():
                print(f'skip (already moved): {rel} -> {self.package_dir}/{rel}')
                continue
            if not src.exists():
                print(f'skip (not present, nothing to do): {rel}')
                continue
            if dst.exists():
                if rel == 'README.md' and dst.is_file() and self._is_stub(src):
                    print('skip (already moved, monorepo stub in place): README.md')
                    continue
                if dst.is_dir() and not any(dst.iterdir()):
                    # Leftover empty directory (e.g. from a reverted migration); safe to remove.
                    print(f'removing leftover empty directory: {self.package_dir}/{rel}')
                    if not self.dry_run:
                        dst.rmdir()
                else:
                    print(f'ABORT: destination {self.package_dir}/{rel} already exists.')
                    print(f"Remove it first (e.g. 'rm -rf {self.package_dir}/{rel}') and re-run.")
                    sys.exit(1)
            print(f'{"would move" if self.dry_run else "moving"}: {rel} -> {self.package_dir}/{rel}')
            if not self.dry_run:
                dst.parent.mkdir(parents=True, exist_ok=True)
                proc = self.run_git('mv', rel, f'{self.package_dir}/{rel}')
                if proc.returncode != 0:
                    print(f'ABORT: `git mv {rel}` failed:\n{proc.stderr}')
                    sys.exit(1)

    def resolve_content(self, rel: str) -> tuple[Path, str | None, str]:
        """Return ``(path, content, note)`` for ``rel``, previewing moved files in dry runs.

        In dry-run mode a post-move path (e.g. ``aiida-core/pyproject.toml``)
        does not exist yet, so fall back to its legacy root location purely
        to count the replacements that ``--execute`` would apply after the move.
        """
        path = self.root / rel
        if path.is_file():
            return path, path.read_text(encoding='utf8'), ''
        prefix = f'{self.package_dir}/'
        if self.dry_run and rel.startswith(prefix):
            legacy = self.root / rel[len(prefix) :]
            if legacy.is_file():
                return legacy, legacy.read_text(encoding='utf8'), f'previewed from legacy {legacy.name}'
        return path, None, ''

    def patch_file(self, rel: str, old: str, new: str, *, use_regex: bool = False) -> int:
        """Replace ``old`` with ``new`` in ``rel``; return number of replacements.

        In dry-run mode the file is left untouched but replacements are counted.
        """
        path, content, note = self.resolve_content(rel)
        if content is None:
            self.results.append(PatchResult(path=rel, skipped=True, note='file not found'))
            return 0
        if use_regex:
            content_new, count = re.subn(old, new, content, flags=re.MULTILINE)
        else:
            count = content.count(old)
            content_new = content.replace(old, new)
        if count and not self.dry_run:
            path.write_text(content_new, encoding='utf8')
        self.results.append(PatchResult(path=rel, replacements=count, note=note))
        return count

    def patch_lines(self, rel: str, pattern: str, replacement: str, *, only_list_items: bool = False) -> int:
        """Regex-replace per line; with ``only_list_items`` touch YAML list items only."""
        path, content, note = self.resolve_content(rel)
        if content is None:
            self.results.append(PatchResult(path=rel, skipped=True, note='file not found'))
            return 0
        compiled = re.compile(pattern)
        total = 0
        lines = content.splitlines(keepends=True)
        for index, line in enumerate(lines):
            stripped = line.lstrip()
            if only_list_items and not stripped.startswith('-'):
                continue
            lines[index], count = compiled.subn(replacement, line)
            total += count
        if total and not self.dry_run:
            path.write_text(''.join(lines), encoding='utf8')
        self.results.append(PatchResult(path=rel, replacements=total, note=note))
        return total

    def patch_flit_sdist_excludes(self) -> None:
        """Drop repo-root-only entries from ``[tool.flit.sdist] exclude``.

        After the move, files that stay at the repository root are automatically
        excluded from the sdist (they live outside the package directory), so
        listing them is misleading. Entries for files/dirs that moved along
        with the package (``docs/``, ``tests/``, ...) are kept.
        """
        rel = f'{self.package_dir}/pyproject.toml'
        path, content, note = self.resolve_content(rel)
        if content is None:
            self.results.append(PatchResult(path=rel, skipped=True, note='file not found'))
            return
        # These stay at the repo root and hence need no sdist exclusion anymore.
        drop = {
            '.claude/',
            '.devcontainer/',
            '.docker/',
            '.git-blame-ignore-revs',
            '.github/',
            '.gitignore',
            '.molecule/',
            '.pre-commit-config.yaml',
            '.readthedocs.yml',
            'AGENTS.md',
            'AI_POLICY.md',
            'CLAUDE.md',
            'CODE_OF_CONDUCT.md',
            'codecov.yml',
            'utils/',
        }
        lines = content.splitlines(keepends=True)
        total = 0
        in_exclude = False
        for index, line in enumerate(lines):
            if '[tool.flit.sdist]' in line:
                in_exclude = False
            if 'exclude = [' in line:
                in_exclude = True
                continue
            if in_exclude:
                if ']' in line:
                    in_exclude = False
                    continue
                if any(token in line for token in drop):
                    lines[index] = ''
                    total += 1
        if total and not self.dry_run:
            path.write_text(''.join(lines), encoding='utf8')
        self.results.append(PatchResult(path=rel, replacements=total, note=note))

    def write_root_ruff_config(self) -> None:
        """Write the fallback root ``ruff.toml`` sharing the package style.

        Never overwrites an existing file: if the tree already carries a root
        ruff config (e.g. extracted from the package), it is left untouched.
        The fallback only covers trees whose package still owns ``[tool.ruff]``.
        """
        path = self.root / 'ruff.toml'
        if path.is_file():
            print('skip ruff.toml (already exists, left untouched)')
            return
        content = ROOT_RUFF_TOML.replace('aiida-core', self.package_dir)
        print(f'{"would write" if self.dry_run else "writing"}: ruff.toml (root style config)')
        if not self.dry_run:
            path.write_text(content, encoding='utf8')
        self.results.append(PatchResult(path='ruff.toml', replacements=1))

    def prefix_ruff_excludes(self) -> None:
        """Keep root ``ruff.toml`` correct for the moved tree.

        Shared-config excludes are repo-root-relative, so paths that move into
        the subpackage (e.g. sphinx snippets) must follow. Only list entries
        are touched (lines starting with a quote); comments are left alone.
        Already-prefixed entries do not match twice. Also ensures
        ``known-first-party`` so ``aiida`` keeps its import grouping now that
        no ``src/`` layout is visible from the repository root.
        """
        pkg = self.package_dir
        self.patch_lines('ruff.toml', rf"^(\s*['\"])(?!{pkg}/)docs/", rf'\1{pkg}/docs/')
        path = self.root / 'ruff.toml'
        if not path.is_file():
            self.results.append(PatchResult(path='ruff.toml', skipped=True, note='file not found'))
            return
        content = path.read_text(encoding='utf8')
        if 'known-first-party' in content:
            return
        anchor = '# Mark some classes as generic'
        block = '[lint.isort]\nknown-first-party = ["aiida"]\n\n'
        if anchor in content:
            content_new = content.replace(anchor, block + anchor, 1)
        else:
            content_new = content.rstrip('\n') + '\n\n' + block
        if not self.dry_run:
            path.write_text(content_new, encoding='utf8')
        self.results.append(PatchResult(path='ruff.toml', replacements=1))

    def write_root_readme_stub(self) -> None:
        """Replace the moved root ``README.md`` with a monorepo pointer."""
        path = self.root / 'README.md'
        if path.exists():
            print('skip root README stub (README.md still at root, move did not happen yet?)')
            return
        print(f'{"would write" if self.dry_run else "writing"}: README.md (monorepo stub)')
        if not self.dry_run:
            path.write_text(ROOT_README_STUB, encoding='utf8')
        self.results.append(PatchResult(path='README.md', replacements=1))

    def patch_action_file(self, old_text: str, new_text: str) -> int:
        """Replace ``old_text`` in the install action (old or new location)."""
        new_rel = '.github/actions/install-package/action.yml'
        old_rel = '.github/actions/install-aiida-core/action.yml'
        new_path = self.root / new_rel
        src_path = new_path if new_path.is_file() else self.root / old_rel
        if not src_path.is_file():
            self.results.append(PatchResult(path=new_rel, skipped=True, note='file not found'))
            return 0
        content = src_path.read_text(encoding='utf8')
        count = content.count(old_text)
        if count and not self.dry_run:
            new_path.write_text(content.replace(old_text, new_text), encoding='utf8')
        note = 'previewed pre-rename' if src_path != new_path else ''
        self.results.append(PatchResult(path=new_rel, replacements=count, note=note))
        return count

    def extract_mypy_config(self) -> None:
        """Move ``[tool.mypy]`` sections from the package into root ``mypy.toml``.

        Mypy accepts any config file via ``--config-file`` (standalone ``.toml``
        files use ``[tool.mypy]`` sections verbatim), but it does not
        auto-discover ``mypy.toml``; the pre-commit hook passes the path
        explicitly. Overrides stay module-keyed, so every subpackage graduates
        in this single file. The block holds no path-valued settings, which
        would resolve against the working directory instead of this file.
        """
        header = (
            '# Shared mypy configuration for the AiiDA monorepo.\n'
            '#\n'
            '# Referenced explicitly (mypy does not auto-discover `mypy.toml`):\n'
            '#   mypy --config-file mypy.toml <files>\n'
            '# The pre-commit hook passes `--config-file=mypy.toml`.\n'
            '#\n'
            '# Strictness is shared; per-package adaptation happens through\n'
            '# `[[tool.mypy.overrides]]` sections below, which are keyed by module name,\n'
            '# so every subpackage graduates in this single file.\n'
            '#\n'
            '# Keep this file free of path-valued settings (`mypy_path`, `files`, ...):\n'
            '# those resolve relative to the invoking working directory, not this file.\n'
            '\n'
        )
        target = self.root / 'mypy.toml'
        if target.is_file():
            print('skip mypy extraction (mypy.toml already exists)')
            return
        rel = f'{self.package_dir}/pyproject.toml'
        _, content, note = self.resolve_content(rel)
        if content is None:
            self.results.append(PatchResult(path=rel, skipped=True, note='file not found'))
            return
        lines = content.splitlines(keepends=True)
        try:
            start = lines.index('[tool.mypy]\n')
        except ValueError:
            self.results.append(PatchResult(path=rel, skipped=True, note='no [tool.mypy] section'))
            return
        end = next(index for index, line in enumerate(lines[start + 1 :], start + 1) if re.match(r'^\[[^\[]', line))
        block = lines[start:end]
        # Drop one surrounding blank line so no double blank remains.
        first = start - 1 if start > 0 and lines[start - 1].strip() == '' else start
        remaining = lines[:first] + lines[end:]
        moved = end - start
        if not self.dry_run:
            target.write_text(header + ''.join(block), encoding='utf8')
            (self.root / rel).write_text(''.join(remaining), encoding='utf8')
        print(f'{"would move" if self.dry_run else "moving"}: {moved} mypy config lines to mypy.toml')
        self.results.append(PatchResult(path='mypy.toml', replacements=moved, note=note))
        # Point the hook at the shared config (runs after the generic prefix rule).
        self.patch_file(
            '.pre-commit-config.yaml',
            f'args: [--config-file={self.package_dir}/pyproject.toml, --pretty]',
            'args: [--config-file=mypy.toml, --pretty]',
        )

    def restructure_github(self) -> None:
        """Restructure ``.github/`` for per-package CI with reusable actions.

        The install action becomes package-agnostic (``install-package``) so new
        subpackages reuse it, a reusable pytest workflow is added as a template
        for package CI, and ``CODEOWNERS`` follows the moved packaging files.
        """
        pkg = self.package_dir
        old_action = '.github/actions/install-aiida-core'
        new_action = '.github/actions/install-package'
        old_path, new_path = self.root / old_action, self.root / new_action
        if new_path.is_dir():
            print(f'skip (already moved): {old_action} -> {new_action}')
        elif not old_path.is_dir():
            print(f'skip (not present, nothing to do): {old_action}')
        else:
            print(f'{"would move" if self.dry_run else "moving"}: {old_action} -> {new_action}')
            if not self.dry_run:
                proc = self.run_git('mv', old_action, new_action)
                if proc.returncode != 0:
                    print(f'ABORT: `git mv {old_action}` failed:\n{proc.stderr}')
                    sys.exit(1)

        pkg_expr = '${{ inputs.package }}'
        self.patch_action_file('name: Install aiida-core', 'name: Install Python package')
        self.patch_action_file(
            'description: Install aiida-core package and its Python dependencies',
            'description: Install a Python subpackage and its Python dependencies',
        )
        # Match the pristine strings so this works with or without any earlier path-prefix pass.
        self.patch_action_file('uv sync --locked', f'uv sync --project {pkg_expr} --locked')
        self.patch_action_file('-e .${{', '-e ./' + pkg_expr + '${{')
        # `uv sync --project <pkg>` creates `<pkg>/.venv`, while `setup-uv`
        # with `activate-environment` only puts the root `.venv` on `PATH`.
        # Put the package venv first so bare `pytest`/`pre-commit`/`verdi`
        # resolve to the right environment in later steps (idempotent: skip
        # when the step is already present).
        new_rel_path = '.github/actions/install-package/action.yml'
        new_action_path = self.root / new_rel_path
        if new_action_path.is_file():
            action_text = new_action_path.read_text(encoding='utf8')
            venv_marker = 'Add package venv to PATH'
            if venv_marker not in action_text:
                anchor_line = (
                    f'    run: uv sync --project {pkg_expr} --locked'
                    + " ${{ inputs.extras && format('--extra {0}', inputs.extras) || '' }}"
                )
                if anchor_line in action_text:
                    step_block = (
                        anchor_line + '\n'
                        '  - name: Add package venv to PATH\n'
                        "    if: ${{ inputs.from-lock == 'true' }}\n"
                        f'    run: echo "${{GITHUB_WORKSPACE}}/{pkg_expr}/.venv/bin" >> $GITHUB_PATH\n'
                    )
                    action_new = action_text.replace(anchor_line + '\n', step_block)
                    if not self.dry_run:
                        new_action_path.write_text(action_new, encoding='utf8')
                    self.results.append(PatchResult(path=new_rel_path, replacements=1))

        # Insert the `package` input once, before the `extras` block.
        new_rel = '.github/actions/install-package/action.yml'
        new_path = self.root / new_rel
        src_path = new_path if new_path.is_file() else self.root / '.github/actions/install-aiida-core/action.yml'
        if src_path.is_file():
            content = src_path.read_text(encoding='utf8')
            marker = 'description: Subpackage directory containing the project'
            anchor = '  extras:\n    description: list of optional dependencies'
            count = 0
            if marker not in content and anchor in content:
                block = (
                    '  package:\n'
                    '    description: Subpackage directory containing the project\n'
                    f'    default: {pkg}\n'
                    '    required: false\n'
                )
                content_new = content.replace(anchor, block + anchor)
                count = 1
                if not self.dry_run:
                    new_path.write_text(content_new, encoding='utf8')
            note = 'previewed pre-rename' if src_path != new_path else ''
            self.results.append(PatchResult(path=new_rel, replacements=count, note=note))

        # Rewire the presto job (no services needed) through the template; the
        # environment and pytest invocation stay identical to the current job.
        # NOTE: this runs before the caller rename below, so the old block still
        # references `install-aiida-core`. Dry-run counts may overlap by one with
        # the rename (each patch is evaluated against the pristine file); the
        # executed result is exact.
        self.patch_file(
            '.github/workflows/ci-code.yml',
            '  tests-presto:\n\n    runs-on: ubuntu-24.04\n    timeout-minutes: 25\n\n    steps:\n'
            '    - uses: actions/checkout@v7\n\n    - name: Install graphviz\n'
            '      run: sudo apt update && sudo apt install graphviz\n\n    - name: Install aiida-core\n'
            "      uses: ./.github/actions/install-aiida-core\n      with:\n        python-version: '3.14'\n\n"
            '    - name: Setup SSH on localhost\n      run: .github/workflows/setup_ssh.sh\n\n'
            '    - name: Run test suite\n      env:\n        AIIDA_WARN_v3: 0\n'
            f"      run: pytest -n auto --broker-backend zmq -m 'presto' {pkg}/tests/\n",
            '  tests-presto:\n    # Presto tests need no external services; they run through the shared template.\n'
            '    uses: ./.github/workflows/reusable-pytest.yml\n    with:\n      package: '
            f'{pkg}\n'
            "      python-version: '3.14'\n"
            f'      test-path: tests/\n      pytest-args: "--broker-backend zmq -m \'presto\'"\n'
            "      warn-v3: '0'\n      test-profile: ''\n",
        )

        # Point all callers at the generalized action.
        for workflow in sorted((self.root / '.github' / 'workflows').glob('*.yml')):
            self.patch_file(
                str(Path('.github/workflows') / workflow.name),
                'uses: ./.github/actions/install-aiida-core',
                'uses: ./.github/actions/install-package',
            )

        # Add the reusable pytest template for package CI.
        reusable = self.root / '.github' / 'workflows' / 'reusable-pytest.yml'
        if reusable.is_file() and reusable.read_text(encoding='utf8') == REUSABLE_PYTEST_YML:
            pass
        else:
            print(f'{"would write" if self.dry_run else "writing"}: .github/workflows/reusable-pytest.yml')
            if not self.dry_run:
                reusable.write_text(REUSABLE_PYTEST_YML, encoding='utf8')
            self.results.append(PatchResult(path='.github/workflows/reusable-pytest.yml', replacements=1))

        # CODEOWNERS follows the moved packaging files.
        self.patch_lines('.github/CODEOWNERS', r'^environment\.yml', f'{pkg}/environment.yml')
        self.patch_lines('.github/CODEOWNERS', r'^pyproject\.toml', f'{pkg}/pyproject.toml')
        self.patch_lines('.github/CODEOWNERS', r'^uv\.lock', f'{pkg}/uv.lock')

    def patch_all_references(self) -> None:
        """Rewrite repo-relative path references in developer tooling."""
        pkg = self.package_dir

        # --- pre-commit config: hook file filters and mypy excludes ---
        # NOTE: keep the generic `pyproject.toml` replacement below as the only
        # rule for that token: the mypy `--config-file=` path is covered by it,
        # and an additional explicit rule would prefix it twice.
        # All rules below use a negative lookbehind so re-running is a no-op.
        self.patch_file('.pre-commit-config.yaml', rf'(?<!{pkg}/)src/aiida/', f'{pkg}/src/aiida/', use_regex=True)
        # The uv-lock hook manifest anchors `files:` to the repo root and runs
        # `uv lock` in the current directory, so scope both to the subpackage.
        new_uv_lock = (
            f'  - id: uv-lock\n    args: [--project, {pkg}]\n    files: ^{pkg}/(uv\\.lock|pyproject\\.toml)$\n'
        )
        self.patch_file(
            '.pre-commit-config.yaml',
            '  - id: uv-lock\n\n',
            new_uv_lock + '\n',
        )
        self.patch_file(
            '.pre-commit-config.yaml',
            rf'(?<!{pkg}/)pyproject\.toml',
            f'{pkg}/pyproject.toml',
            use_regex=True,
        )
        self.patch_file(
            '.pre-commit-config.yaml',
            rf'(?<!{pkg}/)environment\.yml',
            f'{pkg}/environment.yml',
            use_regex=True,
        )
        self.patch_lines('.pre-commit-config.yaml', r'(?<![\w/.-])(docs|tests)/', f'{pkg}/\\1/')

        # --- package metadata (post-move location) ---
        self.patch_flit_sdist_excludes()
        self.patch_file(
            f'{pkg}/pyproject.toml',
            'https://github.com/aiidateam/aiida-core/blob/main/CHANGELOG.md',
            f'https://github.com/aiidateam/aiida-core/blob/main/{pkg}/CHANGELOG.md',
        )

        # --- repo-level configs ---
        self.patch_file('codecov.yml', rf'(?<!{pkg}/)src/aiida/', f'{pkg}/src/aiida/', use_regex=True)
        self.patch_file('.readthedocs.yml', '    path: .', f'    path: {pkg}')
        self.patch_file(
            '.readthedocs.yml',
            'configuration: docs/source/conf.py',
            f'configuration: {pkg}/docs/source/conf.py',
        )

        # --- CI workflows ---
        for workflow in sorted((self.root / '.github' / 'workflows').glob('*.yml')):
            name = workflow.name
            # `make -C docs` builds the moved docs tree.
            self.patch_file(str(Path('.github/workflows') / name), 'make -C docs', f'make -C {pkg}/docs')
            # `pip install -e .` must target the moved package directory.
            self.patch_lines(str(Path('.github/workflows') / name), r'-e \.(?=[\s\[$]|$)', f'-e ./{pkg}')
            # Bare `docs/` / `tests/` path filters and pytest targets.
            self.patch_lines(
                str(Path('.github/workflows') / name),
                r'(?<![\w/.-])(docs|tests)/',
                f'{pkg}/\\1/',
                only_list_items=name in DOCKER_WORKDIR_WORKFLOWS,
            )

        # --- test-install workflow: trigger paths and conda env file location ---
        test_install = str(Path('.github/workflows') / 'test-install.yml')
        self.patch_file(test_install, '    - environment.yml', f'    - {pkg}/environment.yml')
        self.patch_file(test_install, '    - pyproject.toml', f'    - {pkg}/pyproject.toml')
        self.patch_file(test_install, '-f environment.yml', f'-f {pkg}/environment.yml')

        # --- devcontainer: install the package from its new location ---
        self.patch_file(
            '.devcontainer/devcontainer.json',
            'pip install -e /workspaces/aiida-core[',
            f'pip install -e /workspaces/aiida-core/{pkg}[',
        )

        # --- release tag check reads the version from the moved source tree ---
        self.patch_file(
            '.github/workflows/check_release_tag.py',
            "Path('src/aiida/__init__.py')",
            f"Path('{pkg}/src/aiida/__init__.py')",
        )

        # --- Docker build installs the package from its new location ---
        self.patch_file(
            '.docker/aiida-core-base/Dockerfile',
            'pip install /tmp/aiida-core --no-cache-dir',
            f'pip install /tmp/aiida-core/{pkg} --no-cache-dir',
        )

        # --- utils/ helpers stay at the root but must find the moved files ---
        self.patch_file(
            'utils/dependency_management.py',
            r'^ROOT = Path\(__file__\)\.resolve\(\)\.parent\.parent  # repository root$',
            'REPO_ROOT = Path(__file__).resolve().parent.parent  # repository root\n'
            f"ROOT = REPO_ROOT / '{pkg}' if (REPO_ROOT / '{pkg}' / 'pyproject.toml').exists() else REPO_ROOT"
            '  # package dir (monorepo) or repository root (legacy layout)',
            use_regex=True,
        )
        self.patch_file(
            'utils/autogenerate_all_imports.py',
            "_folder = Path(__file__).parent.parent.joinpath('src', 'aiida')",
            '_repo_root = Path(__file__).parent.parent\n'
            f"    _package_root = _repo_root / '{pkg}'\n"
            "    if not (_package_root / 'pyproject.toml').is_file():  # legacy flat layout\n"
            '        _package_root = _repo_root\n'
            "    _folder = _package_root.joinpath('src', 'aiida')",
        )
        self.patch_file(
            'utils/validate_consistency.py',
            'ROOT_DIR = os.path.join(SCRIPT_PATH, os.pardir)',
            'REPO_ROOT = os.path.join(SCRIPT_PATH, os.pardir)\n'
            '# Monorepo layout: package files live under `aiida-core/`, dev tools stay at the repo root\n'
            f"ROOT_DIR = os.path.join(REPO_ROOT, '{pkg}') if os.path.exists(os.path.join(REPO_ROOT, '{pkg}',\n"
            "    'pyproject.toml')) else REPO_ROOT",
        )

    def report(self) -> None:
        """Print a summary of all (planned) text patches."""
        print('\n--- text patches ---')
        for result in self.results:
            if result.skipped:
                print(f'skip ({result.note}): {result.path}')
            elif result.replacements:
                verb = 'would replace' if self.dry_run else 'replaced'
                suffix = f' ({result.note})' if result.note else ''
                print(f'{verb} {result.replacements}x in {result.path}{suffix}')
        if self.dry_run and not any(r.replacements for r in self.results):
            print('(no references found - files may already be migrated)')


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Migrate the repo to a monorepo layout (dry run by default).')
    parser.add_argument(
        '--package-dir',
        default='aiida-core',
        help='subdirectory receiving the aiida-core package (default: %(default)s)',
    )
    parser.add_argument(
        '--root',
        default=None,
        help='repository root (default: `git rev-parse --show-toplevel`)',
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='perform the move and rewrite files (default is a dry run)',
    )
    parser.add_argument(
        '--full',
        action='store_true',
        help='run the complete end-to-end migration: move, stage, commit, verify '
        'with uv/pytest/pre-commit, and amend the autofixes into the commit (implies --execute)',
    )
    return parser.parse_args(argv)


def rename_commit_message(package_dir: str) -> str:
    """Commit title for the package move."""
    return f'Move {package_dir} package into {package_dir}/ subdirectory'


def autofix_commit_message() -> str:
    """Commit title for the pre-commit autofixes."""
    return 'Apply pre-commit autofixes for the new layout'


def run_step(cmd: list[str], cwd: Path, *, allow_failure: bool = False) -> int:
    """Run ``cmd`` in ``cwd`` streaming output; abort unless ``allow_failure``."""
    print(f'+ {shlex.join(cmd)}', flush=True)
    proc = subprocess.run(cmd, cwd=cwd, check=False)
    if proc.returncode != 0:
        if allow_failure:
            print(f'(continuing despite exit code {proc.returncode})')
            return proc.returncode
        msg = f'ABORT: command exited with code {proc.returncode}: {shlex.join(cmd)}'
        print(msg)
        sys.exit(1)
    return proc.returncode


def staged_paths(root: Path, diff_filter: str) -> list[str]:
    """Return staged paths matching ``git diff --cached --diff-filter``."""
    proc = subprocess.run(
        ['git', 'diff', '--cached', '--name-only', f'--diff-filter={diff_filter}'],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return []
    return [line for line in proc.stdout.splitlines() if line]


def has_staged_renames(migration: Migration) -> bool:
    """Check whether the package move is staged (renames/adds under the package dir)."""
    return any(path.startswith(f'{migration.package_dir}/') for path in staged_paths(migration.root, 'AR'))


def has_staged_changes(root: Path) -> bool:
    """Check whether anything is staged at all."""
    proc = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=root, check=False)
    return proc.returncode != 0


def stage_migration(migration: Migration) -> None:
    """Stage exactly what the migration creates: tracked edits, the subtree, new root files."""
    root, pkg = migration.root, migration.package_dir
    run_step(['git', 'add', '-u'], root)
    if (root / pkg).is_dir():
        run_step(['git', 'add', pkg], root)
    for name in ('ruff.toml', 'README.md', 'mypy.toml'):
        if (root / name).is_file():
            run_step(['git', 'add', name], root)
    if (root / '.github').is_dir():
        run_step(['git', 'add', '.github'], root)


def head_commit_subject(root: Path) -> str:
    """Return the subject line of ``HEAD``, or ``''`` when unavailable."""
    proc = subprocess.run(
        ['git', 'log', '-1', '--pretty=%s'],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.stdout.strip() if proc.returncode == 0 else ''


def run_full_flow(migration: Migration) -> None:
    """Execute the complete end-to-end migration: stage, commit, verify, amend fixes."""
    root, pkg = migration.root, migration.package_dir
    rename_msg = rename_commit_message(pkg)
    autofix_msg = autofix_commit_message()
    run_step(['git', 'status', '--short'], root)
    stage_migration(migration)
    rename_committed = False
    if has_staged_renames(migration):
        # Bypass the hooks exactly once: `check-added-large-files` cannot see
        # renames and flags the moved (byte-identical) binaries.
        run_step(['git', 'commit', '--no-verify', '-m', rename_msg], root)
        rename_committed = True
    else:
        print('skip rename commit (no staged package move found)')
    run_step(['uv', 'sync', '--project', pkg], root)
    run_step(['uv', 'run', '--project', pkg, 'python', '-c', 'import aiida; print(aiida.__version__)'], root)
    run_step(
        ['uv', 'run', '--project', pkg, 'pytest', f'{pkg}/tests/common/test_extendeddicts.py', '-x', '-q'],
        root,
    )
    # The first full pre-commit pass is allowed to fail: hooks with autofix
    # (ruff format/check, whitespace) modify files and report failure.
    run_step(['uv', 'run', '--project', pkg, 'pre-commit', 'run', '--all-files'], root, allow_failure=True)
    stage_migration(migration)
    if has_staged_changes(root):
        # Squash the autofixes into the migration commit so the move stays
        # reviewable as a single commit; the second paragraph records the fixup.
        # `--no-verify` is still needed: the amended commit contains the renames.
        if rename_committed or head_commit_subject(root) == rename_msg:
            run_step(['git', 'commit', '--amend', '--no-verify', '-m', rename_msg, '-m', autofix_msg], root)
        else:
            run_step(['git', 'commit', '-m', autofix_msg], root)
    else:
        print('skip autofix amend (working tree clean)')
    run_step(['uv', 'run', '--project', pkg, 'pre-commit', 'run', '--all-files'], root)
    run_step(['git', 'status', '--short'], root)
    print('\nMonorepo migration complete and verified.')


def detect_root(explicit: str | None) -> Path:
    """Determine the repository root."""
    if explicit:
        return Path(explicit).resolve()
    proc = subprocess.run(['git', 'rev-parse', '--show-toplevel'], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        print('ABORT: not inside a git repository and no --root given.')
        sys.exit(1)
    return Path(proc.stdout.strip())


def main(argv: list[str] | None = None) -> None:
    """Entry point: plan (or perform) the monorepo migration."""
    args = parse_args(argv)
    root = detect_root(args.root)
    execute = args.execute or args.full
    migration = Migration(root=root, package_dir=args.package_dir, dry_run=not execute)

    mode = 'DRY RUN (pass --execute to apply changes)' if migration.dry_run else 'EXECUTING'
    print(f'{mode}: repo root is {root}, package dir is {args.package_dir}/')

    if not migration.dry_run:
        status = migration.run_git('status', '--porcelain')
        if status.stdout.strip():
            print('warning: working tree has uncommitted changes; commit or stash first to keep review simple.')

    migration.move_package_paths()
    migration.patch_all_references()
    migration.restructure_github()
    # Extract after the generic prefix rule so the hook line below matches.
    migration.extract_mypy_config()
    migration.write_root_ruff_config()
    migration.prefix_ruff_excludes()
    migration.write_root_readme_stub()
    migration.report()

    if migration.dry_run:
        print('\nDry run complete, nothing was changed. Review the plan above, then re-run with --execute.')
        return

    if args.full:
        run_full_flow(migration)
        return

    print('\n--- git status ---')
    status = migration.run_git('status', '--short')
    print(status.stdout or '(clean)')
    # Print plain shell lines (no numbering, no backticks) so the block can be
    # copied directly into a terminal at the repository root. The rename commit
    # needs `--no-verify`: `check-added-large-files` cannot see renames and so
    # flags the moved (byte-identical) binaries exactly once.
    commands = [
        'git status --short',
        'python utils/migrate_to_monorepo.py',
        'python utils/migrate_to_monorepo.py --execute',
        'git add -u',
        'git add aiida-core',
        'git add ruff.toml README.md mypy.toml',
        'git add .github',
        '# Renames trip check-added-large-files (it cannot see renames), bypass hooks once:',
        f'git commit --no-verify -m "{rename_commit_message(args.package_dir)}"',
        f'uv sync --project {args.package_dir}',
        f'uv run --project {args.package_dir} python -c "import aiida; print(aiida.__version__)"',
        f'uv run --project {args.package_dir} pytest {args.package_dir}/tests/common/test_extendeddicts.py -x -q',
        f'uv run --project {args.package_dir} pre-commit run --all-files',
        'git add -u',
        'git add aiida-core',
        'git add ruff.toml README.md mypy.toml',
        'git add .github',
        '# Squash the autofixes into the migration commit (amended commit still holds renames, so bypass hooks again):',
        f'git commit --amend --no-verify -m "{rename_commit_message(args.package_dir)}"'
        f' -m "{autofix_commit_message()}"',
    ]
    print('\nCopy and run these from the repository root:')
    print('------------------------------------------------------------')
    print('\n'.join(commands))
    print('------------------------------------------------------------')


if __name__ == '__main__':
    main()
