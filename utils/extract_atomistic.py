# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Split the atomistic (materials-science) modules out of ``aiida-core``.

Moves everything that requires the ``atomic_tools`` optional dependencies
(``StructureData``, ``CifData``, ``BandsData``, ``KpointsData``,
``TrajectoryData``, ``OrbitalData``, ``UpfData``, ``ProjectionData``, the
``aiida.tools.data`` / ``aiida.tools.dbimporters`` subtrees, the matching
``verdi data`` commands and REST translators, plus their tests) into a new
``aiida-atomistic/`` subpackage that depends on ``aiida-core``.

Usage:
    python utils/extract_atomistic.py                          # dry run, only prints the plan
    python utils/extract_atomistic.py --execute                # perform all automatable steps
    python utils/extract_atomistic.py --execute --phase move   # only one phase (scaffold|move|rewrite)
    python utils/extract_atomistic.py --execute --commit      # all phases, as a single commit

Phases (run in order scaffold -> move -> rewrite):
    1. ``scaffold`` -- create ``aiida-atomistic/`` packaging, README, CI caller, CODEOWNERS.
    2. ``move``     -- ``git mv`` sources and tests (pure renames, no edits).
    3. ``rewrite``  -- rewrite imports/entry points in the new package, add lazy
                       ``__getattr__`` shims in ``aiida-core`` (never the reverse:
                       core must not hard-import the subpackage, see MONOREPO.md).

The script is idempotent: already-moved paths are skipped and text patches
carry markers so re-running is safe. Only the standard library is used.

What is deliberately NOT automated (printed as a checklist at the end):
    - ``UpfFamily`` (shares ``aiida/orm/groups.py`` with core groups),
    - docs moves, mixed test files (``test_dataclasses.py``, ``test_data.py``),
      back-compat policy decisions, release registration/review
      (PyPI publisher, generated workflow), ``environment.yml``,
      entry-point group map decisions and full-suite validation.
"""

from __future__ import annotations

import argparse
import ast
import compileall
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CORE = REPO_ROOT / 'aiida-core'
CORE_SRC = CORE / 'src' / 'aiida'
CORE_TESTS = CORE / 'tests'
PKG = REPO_ROOT / 'aiida-atomistic'
PKG_SRC = PKG / 'src' / 'aiida_atomistic'
PKG_TESTS = PKG / 'tests'
MARKER = 'extract_atomistic.py'

# ---------------------------------------------------------------------------
# What moves
# ---------------------------------------------------------------------------

# Individual source files, relative to ``aiida-core/src/aiida``. The relative
# path is mirrored under ``aiida-atomistic/src/aiida_atomistic/`` so that
# ``aiida.orm.nodes.data.structure`` becomes
# ``aiida_atomistic.orm.nodes.data.structure`` and diffs stay readable.
SRC_FILES = [
    'orm/nodes/data/structure.py',
    'orm/nodes/data/cif.py',
    'orm/nodes/data/array/kpoints.py',
    'orm/nodes/data/array/bands.py',
    'orm/nodes/data/array/trajectory.py',
    'orm/nodes/data/array/projection.py',
    'orm/nodes/data/orbital.py',
    'orm/nodes/data/upf.py',
    'cmdline/commands/cmd_data/cmd_structure.py',
    'cmdline/commands/cmd_data/cmd_cif.py',
    'cmdline/commands/cmd_data/cmd_bands.py',
    'cmdline/commands/cmd_data/cmd_trajectory.py',
    'cmdline/commands/cmd_data/cmd_upf.py',
    'restapi/translator/nodes/data/structure.py',
    'restapi/translator/nodes/data/cif.py',
    'restapi/translator/nodes/data/kpoints.py',
    'restapi/translator/nodes/data/upf.py',
    'restapi/translator/nodes/data/array/bands.py',
]

# Whole source trees, relative to ``aiida-core/src/aiida`` (mirrored likewise).
SRC_DIRS = [
    'tools/data',
    'tools/dbimporters',
]

# Individual test files, relative to ``aiida-core/tests`` (mirrored under
# ``aiida-atomistic/tests``).
TEST_FILES = [
    'orm/nodes/data/test_structure.py',
    'orm/nodes/data/test_cif.py',
    'orm/nodes/data/test_kpoints.py',
    'orm/nodes/data/test_array_bands.py',
    'orm/nodes/data/test_trajectory.py',
    'orm/nodes/data/test_orbital.py',
    'orm/nodes/data/test_upf.py',
    'test_dbimporters.py',
]

# Whole test trees, relative to ``aiida-core/tests``.
TEST_DIRS = [
    'tools/data',
    'tools/dbimporters',
]

# Dotted ``aiida.*`` module prefixes that move. Used to (a) decide which
# ``[project.entry-points.*]`` rows relocate and (b) rewrite ``aiida.*``
# imports inside moved files to ``aiida_atomistic.*``. Everything else keeps
# importing from ``aiida-core``: the dependency direction is strictly
# ``aiida-atomistic -> aiida-core`` (see MONOREPO.md).
MOVED_DOTTED = sorted(
    {
        'aiida.orm.nodes.data.structure',
        'aiida.orm.nodes.data.cif',
        'aiida.orm.nodes.data.array.kpoints',
        'aiida.orm.nodes.data.array.bands',
        'aiida.orm.nodes.data.array.trajectory',
        'aiida.orm.nodes.data.array.projection',
        'aiida.orm.nodes.data.orbital',
        'aiida.orm.nodes.data.upf',
        'aiida.tools.data',
        'aiida.tools.dbimporters',
        'aiida.cmdline.commands.cmd_data.cmd_structure',
        'aiida.cmdline.commands.cmd_data.cmd_cif',
        'aiida.cmdline.commands.cmd_data.cmd_bands',
        'aiida.cmdline.commands.cmd_data.cmd_trajectory',
        'aiida.cmdline.commands.cmd_data.cmd_upf',
        'aiida.restapi.translator.nodes.data.structure',
        'aiida.restapi.translator.nodes.data.cif',
        'aiida.restapi.translator.nodes.data.kpoints',
        'aiida.restapi.translator.nodes.data.upf',
        'aiida.restapi.translator.nodes.data.array.bands',
    }
)

# Entry-point groups to relocate: group -> 'all' (whole group moves) or
# 'by-module' (only rows whose target module is in MOVED_DOTTED move).
# Entry-point *names* (e.g. ``core.structure``) are kept identical: node type
# strings stored in databases derive from them, so renaming would break
# provenance (see MONOREPO.md).
ENTRY_POINT_RULES = {
    'aiida.data': 'by-module',
    'aiida.cmdline.data': 'by-module',
    'aiida.groups': 'by-module',  # matches only ``core.upf`` via its module
    'aiida.tools.dbimporters': 'all',
    'aiida.tools.data.orbitals': 'all',
}

# Promoted from ``aiida-core[atomic_tools]`` (+ ``upf_to_json``, only used by
# ``UpfData``) to required dependencies of the new package.
ATOMIC_DEPS = [
    'PyCifRW~=4.4',
    'ase~=3.21',
    'matplotlib~=3.3,>=3.3.4',
    'pymatgen>=2024.3.1',
    'pymysql~=0.9.3',
    'seekpath~=1.9,>=1.9.3',
    'spglib>=1.14,<3.0',
    'upf_to_json~=0.9.2',
]

# Redirects for lazy ``__getattr__`` shims installed in ``aiida-core``:
# name -> new fully-qualified ``module:attr`` in ``aiida-atomistic``.
REDIRECTS_DATA_ARRAY = {
    'BandsData': 'aiida_atomistic.orm.nodes.data.array.bands:BandsData',
    'KpointsData': 'aiida_atomistic.orm.nodes.data.array.kpoints:KpointsData',
    'ProjectionData': 'aiida_atomistic.orm.nodes.data.array.projection:ProjectionData',
    'TrajectoryData': 'aiida_atomistic.orm.nodes.data.array.trajectory:TrajectoryData',
    'find_bandgap': 'aiida_atomistic.orm.nodes.data.array.bands:find_bandgap',
}
REDIRECTS_DATA = {
    'CifData': 'aiida_atomistic.orm.nodes.data.cif:CifData',
    'Kind': 'aiida_atomistic.orm.nodes.data.structure:Kind',
    'Site': 'aiida_atomistic.orm.nodes.data.structure:Site',
    'StructureData': 'aiida_atomistic.orm.nodes.data.structure:StructureData',
    'OrbitalData': 'aiida_atomistic.orm.nodes.data.orbital:OrbitalData',
    'UpfData': 'aiida_atomistic.orm.nodes.data.upf:UpfData',
    'cif_from_ase': 'aiida_atomistic.orm.nodes.data.cif:cif_from_ase',
    'has_pycifrw': 'aiida_atomistic.orm.nodes.data.cif:has_pycifrw',
    'pycifrw_from_cif': 'aiida_atomistic.orm.nodes.data.cif:pycifrw_from_cif',
}
REDIRECTS_TOOLS = {
    'Orbital': 'aiida_atomistic.tools.data.orbital.orbital:Orbital',
    'RealhydrogenOrbital': 'aiida_atomistic.tools.data.orbital.realhydrogen:RealhydrogenOrbital',
    'get_explicit_kpoints_path': 'aiida_atomistic.tools.data.array.kpoints.main:get_explicit_kpoints_path',
    'get_kpoints_path': 'aiida_atomistic.tools.data.array.kpoints.main:get_kpoints_path',
    'spglib_tuple_to_structure': 'aiida_atomistic.tools.data.structure:spglib_tuple_to_structure',
    'structure_to_spglib_tuple': 'aiida_atomistic.tools.data.structure:structure_to_spglib_tuple',
}

# Core aggregator ``__init__`` files to patch: path (relative to
# ``aiida-core/src/aiida``) -> (star-import lines to delete, ``__all__`` names
# to delete, redirects to install). ``orm/nodes/__init__.py`` and
# ``orm/__init__.py`` only re-export transitively, so no star-import line
# goes away there, just the ``__all__`` entries.
SHIM_PLAN = {
    'orm/nodes/data/array/__init__.py': (
        [
            'from aiida.orm.nodes.data.array.bands import *',
            'from aiida.orm.nodes.data.array.kpoints import *',
            'from aiida.orm.nodes.data.array.projection import *',
            'from aiida.orm.nodes.data.array.trajectory import *',
        ],
        list(REDIRECTS_DATA_ARRAY),
        REDIRECTS_DATA_ARRAY,
    ),
    'orm/nodes/data/__init__.py': (
        [
            'from aiida.orm.nodes.data.cif import *',
            'from aiida.orm.nodes.data.orbital import *',
            'from aiida.orm.nodes.data.structure import *',
            'from aiida.orm.nodes.data.upf import *',
        ],
        # `array` names stay re-exported transitively via
        # `from aiida.orm.nodes.data.array import *` (kept), so their
        # `__all__` entries must go too, like in `orm/nodes`/`orm`.
        list(REDIRECTS_DATA) + list(REDIRECTS_DATA_ARRAY),
        {**REDIRECTS_DATA_ARRAY, **REDIRECTS_DATA},
    ),
    'orm/nodes/__init__.py': (
        [],
        list(REDIRECTS_DATA_ARRAY) + list(REDIRECTS_DATA),
        {**REDIRECTS_DATA_ARRAY, **REDIRECTS_DATA},
    ),
    'orm/__init__.py': (
        [],
        list(REDIRECTS_DATA_ARRAY) + list(REDIRECTS_DATA),
        {**REDIRECTS_DATA_ARRAY, **REDIRECTS_DATA},
    ),
    'tools/__init__.py': (
        ['from aiida.tools.data import *'],
        list(REDIRECTS_TOOLS),
        REDIRECTS_TOOLS,
    ),
}

SHIM_TEMPLATE = """\
# Added by utils/{marker}: names that moved to the ``aiida-atomistic`` package.
# ``aiida-core`` must not hard-import the subpackage (see MONOREPO.md), so these
# resolve lazily and raise a helpful error when it is not installed.
import importlib as _importlib

_ATOMISTIC_REDIRECTS = {{
{redirects}
}}


def __getattr__(name: str):
    \"\"\"Lazily resolve names that moved to :mod:`aiida_atomistic`.\"\"\"
    if name in _ATOMISTIC_REDIRECTS:
        modpath, attr = _ATOMISTIC_REDIRECTS[name].split(':')
        try:
            module = _importlib.import_module(modpath)
        except ImportError as exc:
            msg = (
                f'{{name!r}} moved to the `aiida-atomistic` package, which is not installed. '
                'Install it with `pip install aiida-atomistic` (or `uv sync --project aiida-atomistic`).'
            )
            raise AttributeError(msg) from exc
        return getattr(module, attr)
    raise AttributeError(f'module {{__name__!r}} has no attribute {{name!r}}')
"""

COPYRIGHT_HEADER = """\
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""

CI_CALLER = """\
# Thin CI for the ``aiida-atomistic`` subpackage over the shared reusable
# pytest workflow. Package-specific jobs (e.g. extra services) belong here;
# the common test environment is maintained in ``reusable-pytest.yml``.
name: ci-atomistic

on:
  push:
    branches-ignore: [gh-pages]
    paths: [aiida-atomistic/**]
  pull_request:
    branches-ignore: [gh-pages]
    paths: [aiida-atomistic/**]

jobs:
  pytest:
    uses: ./.github/workflows/reusable-pytest.yml
    with:
      package: aiida-atomistic
      python-version: '3.10'
      test-path: tests/
"""
MANUAL_CHECKLIST = """\
Manual follow-ups (only what still needs a human; the script prints this):
  1. `UpfFamily` shares `aiida/orm/groups.py` with core groups: extract the class
     into `aiida-atomistic`, keeping the `aiida.groups:core.upf` entry-point name and the
     DB group-type string identical, and leave a lazy shim in core.
  2. Entry-point group *definitions* stay owned by core (MONOREPO.md): update
     `ENTRY_POINT_GROUP_TO_MODULE_PATH_MAP` / validation lists in
     `aiida/plugins/entry_point.py` for groups now served by `aiida-atomistic`.
  3. REST API: translators are registered under `aiida.restapi.translators` and core
     discovery loads that group (see `patch_rest_discovery`). Remaining: REST tests
     with a running profile for the moved translators, plus the
     `/nodes/download_formats/` endpoint check in CI.
  4. Mixed test files stay in core and must be split by hand:
     `tests/test_dataclasses.py`, `tests/cmdline/commands/test_data.py`,
     REST translator tests, archive/migration tests referencing moved types.
     Moved tests importing `from tests.static import ...` need their static
     assets copied to `aiida-atomistic/tests/static/` (see report above).
  5. Docs: move `topics/data_types.rst` atomistic sections, dbimporter pages,
     `verdi data` command docs and how-tos; fix cross-references.
  6. Release: `release-atomistic.yml` is generated from `release.yml` and the tag
     checker accepts `--tag-prefix`/`--init-module`. Remaining: human review of the
     generated workflow, PyPI trusted-publisher registration for `aiida-atomistic`,
     and CHANGELOG/version policy.
  7. Environments: `uv-lock` hook and pixi tasks are wired; `uv lock` runs
     best-effort inside the script. Remaining: `environment.yml` for the new package
     (`dependency_management.py` is hardcoded to core — parameterize it first).
  8. Decide back-compat policy: keep the lazy core shims (current) or turn them
     into `AiidaDeprecationWarning`s / hard errors; same for the `atomic_tools`
     extra in `aiida-core/pyproject.toml` (left untouched by this script).
  9. Dependencies: `upf_to_json` is pruned from core automatically once the
     zero-importer gate passes. `requests`/`numpy`/`pydantic` correctly stay: core
     still uses them (the gate keeps them).
 10. Re-run `pre-commit run --all-files`, `mypy` and the full test suites of
     both packages with `aiida-atomistic` installed alongside `aiida-core`.
"""


# A single commit keeps the extraction reviewable as one unit. With --commit,
# the first executed phase creates the commit and each later phase stages its
# paths and amends to it, extending the message with its own entry.
SINGLE_COMMIT_MSG = 'Extract atomistic modules to aiida-atomistic subpackage'

# Per-phase entries appended to the single commit message on each amend, so the
# final message records every phase that went into the commit.
PHASE_MSGS = {
    'scaffold': 'Scaffold aiida-atomistic subpackage',
    'move': 'Move atomistic modules/tests to aiida-atomistic (renames only)',
    'rewrite': 'Rewire imports/entry points for atomistic split, add core shims',
}


def build_commit_message(phases: list[str]) -> str:
    """Subject plus one `- <phase>` line per included phase, in phase order."""
    lines = [SINGLE_COMMIT_MSG, '']
    for name in ('scaffold', 'move', 'rewrite'):
        if name in phases:
            lines.append(f'- {PHASE_MSGS[name]}')
    return '\n'.join(lines)


def phases_in_head_message(body: str) -> list[str]:
    """Recover already-amended phases from an existing extraction commit message."""
    return [name for name in ('scaffold', 'move', 'rewrite') if PHASE_MSGS[name] in body]


# Paths staged for the scaffold commit (everything else stays untouched there).
SCAFFOLD_PATHS = ['aiida-atomistic', '.github/workflows/ci-atomistic.yml', '.github/CODEOWNERS']

# Extra root files the rewrite phase may touch (staged with its commit).
REWRITE_EXTRA_PATHS = [
    '.pre-commit-config.yaml',
    'pixi.toml',
    '.github/workflows/release-atomistic.yml',
    '.github/workflows/check_release_tag.py',
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
class Ctx:
    def __init__(self, execute: bool):
        self.execute = execute

    def git(self, *args: str, capture: bool = False) -> str | None:
        print(f'$ git {" ".join(args)}')
        if not self.execute:
            return None
        result = subprocess.run(['git', *args], cwd=REPO_ROOT, check=True, capture_output=True, text=True)
        return result.stdout.strip() if capture else None

    def stage_and_commit(self, paths: list[str], *, message: str, amend: bool) -> bool:
        """Stage `paths` and commit, amending (and extending the message) when `amend`.

        Returns True when a commit was created/amended (or would be in dry run),
        False when there was nothing staged (e.g. re-run) and so nothing was done.
        """
        for path in paths:
            if not (REPO_ROOT / path).exists():
                print(f'skip (missing): {path}')
                continue
            self.git('add', path)
        if not self.execute:
            cmd = '--amend -m "<accumulated>"' if amend else '-m "<accumulated>"'
            action = 'amend (extend message)' if amend else 'create'
            print(f'$ git commit {cmd} ({action} single commit)')
            return True
        # Nothing staged (e.g. re-run) -> skip instead of an empty commit.
        staged = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=REPO_ROOT, check=False).returncode
        if staged != 0:
            if amend:
                self.git('commit', '--amend', '-m', message)
            else:
                self.git('commit', '-m', message)
            return True
        print('skip (nothing staged): no changes to commit')
        return False

    def run(self, *cmd: str) -> None:
        print(f'$ {" ".join(cmd)}')
        if self.execute:
            subprocess.run(cmd, cwd=REPO_ROOT, check=True)

    def write(self, path: Path, content: str) -> None:
        rel = path.relative_to(REPO_ROOT)
        if path.exists():
            print(f'skip (exists): {rel}')
            return
        print(f'write: {rel}')
        if self.execute:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')

    def git_mv(self, src: Path, dst: Path) -> None:
        rel_s, rel_d = src.relative_to(REPO_ROOT), dst.relative_to(REPO_ROOT)
        if dst.exists():
            # Stale empty dirs (e.g. leftover __pycache__ from an earlier
            # run) are not a completed move: clear them and proceed.
            leftovers = [p for p in dst.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
            if src.is_dir() and not leftovers:
                print(f'clear stale empty dir: {rel_d}')
                if self.execute:
                    shutil.rmtree(dst)
            else:
                print(f'skip (moved already): {rel_s} -> {rel_d}')
                return
        if not src.exists():
            print(f'WARNING: missing, skipping: {rel_s}')
            return
        print(f'git mv {rel_s} {rel_d}')
        if self.execute:
            dst.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(['git', 'mv', str(rel_s), str(rel_d)], cwd=REPO_ROOT, check=True)


def working_tree_clean() -> bool:
    """Return True when no tracked modifications or staged changes exist."""
    result = subprocess.run(['git', 'status', '--porcelain'], cwd=REPO_ROOT, capture_output=True, text=True, check=True)
    return all(line.startswith('??') for line in result.stdout.splitlines() if line.strip())


def dotted_of(src_rel: str) -> str:
    """Map a source-relative path to its dotted ``aiida.*`` module name."""
    return 'aiida.' + src_rel.removesuffix('.py').replace('/', '.')


def should_rewrite(dotted: str) -> str | None:
    """Return the ``aiida_atomistic.*`` name if a dotted module moved, else None."""
    for prefix in MOVED_DOTTED:
        if dotted == prefix or dotted.startswith(prefix + '.'):
            return 'aiida_atomistic.' + dotted.removeprefix('aiida.')
    return None


def _moved_name_to_module() -> dict[str, str]:
    """Map each moved public name to its new ``aiida_atomistic`` module."""
    mapping: dict[str, str] = {}
    for table in (REDIRECTS_DATA_ARRAY, REDIRECTS_DATA, REDIRECTS_TOOLS):
        for name, target in table.items():
            mapping[name] = target.split(':')[0]
    return mapping


def rewrite_imports(text: str) -> tuple[str, int]:
    """Rewrite absolute ``aiida.*`` imports of moved modules to ``aiida_atomistic.*``."""
    count = 0

    def repl(match: re.Match) -> str:
        nonlocal count
        dotted = match.group(0)
        new = should_rewrite(dotted)
        if new is None:
            return dotted
        count += 1
        return new

    # Match longest dotted names first; the boundary guard avoids matching a
    # prefix of a longer, non-moved module (e.g. ``aiida.tools.dataX``).
    pattern = re.compile(r'\baiida(?:\.[A-Za-z_][A-Za-z0-9_]*)+')
    text = pattern.sub(repl, text)
    text, extra = rewrite_aggregator_imports(text)
    return text, count + extra


def rewrite_aggregator_imports(text: str) -> tuple[str, int]:
    """Split moved names out of ``from aiida.<aggregator> import ...``.

    First-party code must import moved names directly from ``aiida_atomistic``
    (explicit, typed, IDE-friendly); the lazy core shims and entry points
    remain only for third-party consumers and already-stored nodes.
    Only runs on moved files, so any ``aiida.*`` remainder is core-owned.
    """
    mapping = _moved_name_to_module()
    count = 0
    pattern = re.compile(
        r'(?P<indent>^[ \t]*)from (?P<mod>aiida(?:\.[A-Za-z_][A-Za-z0-9_]*)*) import \((?P<par>[^)]+)\)'
        r'|(?P<indent2>^[ \t]*)from (?P<mod2>aiida(?:\.[A-Za-z_][A-Za-z0-9_]*)*) import (?P<flat>[^\n]+)',
        re.MULTILINE,
    )

    def repl(match: re.Match) -> str:
        nonlocal count
        if match.group('mod') is not None:
            indent, mod, raw = match.group('indent'), match.group('mod'), match.group('par')
            comment = ''
        else:
            indent, mod, raw = match.group('indent2'), match.group('mod2'), match.group('flat')
            raw, hash_, comment = raw.partition('#')
            comment = (hash_ + comment.rstrip()) if hash_ else ''
        if 'aiida_atomistic' in mod or should_rewrite(mod) is not None:
            return match.group(0)
        staying: list[str] = []
        by_target: dict[str, list[str]] = {}
        for raw_item in raw.replace('\n', ' ').split(','):
            item = raw_item.strip()
            if not item:
                continue
            name, _sep, _alias = item.partition(' as ')
            if name.strip() in mapping:
                target = mapping[name.strip()]
                by_target.setdefault(target, []).append(item)
                count += 1
            else:
                staying.append(item)
        if not by_target:
            return match.group(0)
        lines = []
        if staying:
            lines.append(f'{indent}from {mod} import ' + ', '.join(staying))
        for target, items in by_target.items():
            lines.append(f'{indent}from {target} import ' + ', '.join(items))
        if comment:
            lines[-1] += ' ' + comment.strip()
        return '\n'.join(lines)

    return pattern.sub(repl, text), count


def parse_entry_point_sections(text: str) -> list[tuple[str, int, int, list[str]]]:
    """Split ``[project.entry-points.*]`` sections: (group, start, end, lines)."""
    header = re.compile(r"^\[project\.entry-points\.'([^']+)'\]\s*$")
    lines = text.splitlines(keepends=True)
    sections: list[tuple[str, int, int, list[str]]] = []
    current: str | None = None
    start = 0
    for i, line in enumerate(lines):
        match = header.match(line.rstrip('\n'))
        if match:
            if current is not None:
                sections.append((current, start, i, lines[start:i]))
            current, start = match.group(1), i
    if current is not None:
        sections.append((current, start, len(lines), lines[start : len(lines)]))
    return sections


def public_api() -> dict[str, str]:
    """Flat public names re-exported by ``aiida_atomistic`` -> defining module."""
    api: dict[str, str] = {}
    for table in (REDIRECTS_DATA_ARRAY, REDIRECTS_DATA, REDIRECTS_TOOLS):
        for _name, target in table.items():
            module, _, attr = target.partition(':')
            api[attr] = module
    return api


def render_top_init() -> str:
    """Render a *lazy* top-level ``__init__`` (eager star imports cause import cycles)."""
    api = public_api()
    all_block = ''.join(f'    {name!r},\n' for name in sorted(api))
    map_block = ''.join(f'    {name!r}: {mod!r},\n' for name, mod in sorted(api.items()))
    return (
        COPYRIGHT_HEADER
        + '"""Atomistic (materials-science) data types and tools for AiiDA.\n'
        + '\n'
        + 'Provenance contract: entry-point names (e.g. ``core.structure``) and class\n'
        + 'names are identical to the ones formerly shipped by ``aiida-core``; only the\n'
        + 'import paths changed from ``aiida.*`` to ``aiida_atomistic.*``.\n'
        + '"""\n'
        + '\n'
        + 'import importlib as _importlib\n'
        + '\n'
        + "__version__ = '0.1.0a0'\n"
        + '\n'
        + '# Flat public API (file layout is an implementation detail). Resolved lazily:\n'
        + '# leaf modules import back from ``aiida-core`` at module level, so eager\n'
        + '# star imports here would trigger circular imports.\n'
        + '__all__ = (\n'
        + all_block
        + ')\n'
        + '\n'
        + '_PUBLIC_API = {\n'
        + map_block
        + '}\n'
        + '\n'
        + '\n'
        + 'def __getattr__(name: str):\n'
        + '    """Lazily resolve flat public names to their defining submodules."""\n'
        + '    if name in _PUBLIC_API:\n'
        + '        return getattr(_importlib.import_module(_PUBLIC_API[name]), name)\n'
        + "    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')\n"
    )


def planned_intermediate_inits() -> list[Path]:
    """Intermediate ``__init__.py`` the new trees need (parent chains of the moves)."""
    inits: set[Path] = set()
    tables = ((PKG_SRC, SRC_FILES), (PKG_SRC, SRC_DIRS), (PKG_TESTS, TEST_FILES), (PKG_TESTS, TEST_DIRS))
    for base, rels in tables:
        for rel in rels:
            parent = (base / rel).parent
            while parent != base:
                inits.add(parent / '__init__.py')
                parent = parent.parent
    inits.add(PKG_TESTS / '__init__.py')
    return sorted(inits)


# ---------------------------------------------------------------------------
# Phases
# ---------------------------------------------------------------------------
def phase_scaffold(ctx: Ctx) -> None:
    """Create the ``aiida-atomistic/`` skeleton (no moves yet)."""
    deps = '\n'.join(f"  '{dep}'," for dep in ['aiida-core', *ATOMIC_DEPS])
    pyproject = f"""{COPYRIGHT_HEADER}# Packaging for the atomistic (materials-science) companion of AiiDA core.
# Template sections (markers, coverage, flit, requires-python) mirror
# `aiida-core/pyproject.toml`; dependencies and entry points are owned here.
[build-system]
build-backend = 'flit_core.buildapi'
requires = ["flit_core >=4.0.2,<5"]

[dependency-groups]
dev = [
  "aiida-atomistic[tests,pre-commit]",
]

[project]
authors = [{{ name = 'The AiiDA team', email = 'developers@aiida.net' }}]
classifiers = [
  'Development Status :: 3 - Alpha',
  'Framework :: AiiDA',
  'License :: OSI Approved :: MIT License',
  'Operating System :: POSIX :: Linux',
  'Operating System :: MacOS :: MacOS X',
  'Programming Language :: Python',
  'Programming Language :: Python :: 3.10',
  'Programming Language :: Python :: 3.11',
  'Programming Language :: Python :: 3.12',
  'Programming Language :: Python :: 3.13',
  'Programming Language :: Python :: 3.14',
  'Topic :: Scientific/Engineering',
]
dependencies = [
{deps}
]
description = 'Atomistic (materials-science) data types and tools for AiiDA.'
dynamic = ['version']  # read from aiida_atomistic/__init__.py
keywords = ['aiida', 'workflows', 'materials-science']
license = {{ file = 'LICENSE.txt' }}
name = 'aiida-atomistic'
readme = 'README.md'
requires-python = '>=3.10'

# NOTE: entry-point *names* (e.g. `core.structure`) are the provenance API
# contract and stay identical to `aiida-core` (see MONOREPO.md). The
# `[project.entry-points.*]` sections below are filled in by the `rewrite`
# phase of `utils/extract_atomistic.py`.

[project.optional-dependencies]
tests = [
  'aiida-atomistic',
  'ipykernel~=6.9',
  'pgtest~=1.3,>=1.3.1',
  'pytest~=7.0',
  'pytest-asyncio~=0.12,<0.17',
  'pytest-timeout~=2.0',
  'pytest-cov~=7.0',
  'pytest-rerunfailures~=12.0',
  'pytest-benchmark~=4.0',
  'pytest-regressions~=2.2',
  'pytest-instafail~=0.5',
  'pytest-xdist~=3.6',
  # Needed to run core suites from this venv for shim coverage
  # (core `tests/conftest.py` loads `sphinx.testing.fixtures`).
  'sphinx~=7.2.0',
  'docutils~=0.20'
]
pre-commit = [
  'aiida-atomistic[tests]',
  'mypy~=2.3.0',
  'pre-commit~=3.5',
]

[project.urls]
Changelog = 'https://github.com/aiidateam/aiida-core/blob/main/aiida-atomistic/CHANGELOG.md'
Documentation = 'https://aiida.readthedocs.io'
Home = 'http://www.aiida.net/'
Source = 'https://github.com/aiidateam/aiida-core'

[tool.coverage.run]
relative_files = true

[tool.flit.module]
name = 'aiida_atomistic'

[tool.flit.sdist]
exclude = [
  '**/.mypy_cache/',
  'docs/',
  'environment.yml',
  'mypy.toml',
  'ruff.toml',
  'tests/',
  'uv.lock',
  'uv.toml',
]

# Monorepo: test local `aiida-core` instead of PyPI (which still ships the
# moved entry points and would cause `MultipleEntryPointError` duplicates).
[tool.uv.sources]
aiida-core = {{ path = '../aiida-core', editable = true }}

[tool.pytest.ini_options]
addopts = '--benchmark-skip --durations=5 --durations-min=1 --strict-config --strict-markers -ra'
filterwarnings = [
  'ignore::DeprecationWarning:pymatgen:',
  'ignore::SyntaxWarning:CifFile',
  'ignore::pytest.PytestCollectionWarning',
  'ignore:Creating AiiDA configuration folder.*:UserWarning',
]
markers = [
  'nightly: long running tests that should rarely be affected and so only run nightly',
  'requires_rmq: requires RabbitMQ specifically (not compatible with ZeroMQ broker)',
  'requires_broker: requires a message broker (RabbitMQ or ZeroMQ)',
  'requires_psql: requires a connection to PostgreSQL DB',
  'presto: automatic marker for tests needing no external services (not requires_rmq, not requires_psql)',
  'sphinx: set parameters for the sphinx `app` fixture'
]
minversion = '7.0'
testpaths = [
  'tests'
]
timeout = 240
timeout_method = "thread"
xfail_strict = true
"""
    ctx.write(PKG / 'pyproject.toml', pyproject)
    ctx.write(PKG_SRC / '__init__.py', render_top_init())
    ctx.write(PKG_SRC / 'py.typed', '')
    ctx.write(
        PKG / 'README.md',
        '# aiida-atomistic\n\nAtomistic (materials-science) data types and tools for'
        ' [AiiDA](http://www.aiida.net/), extracted from `aiida-core`.\n\nRequires'
        ' `aiida-core` and the former `aiida-core[atomic_tools]` dependencies'
        ' (ASE, pymatgen, spglib, seekpath, PyCifRW, ...).\n',
    )
    ctx.write(PKG / 'CHANGELOG.md', '# Changelog\n\nSee `aiida-core/CHANGELOG.md` for history before the split.\n')
    ctx.write(
        PKG_TESTS / 'conftest.py',
        f'{COPYRIGHT_HEADER}"""Shared fixtures for the ``aiida-atomistic`` test suite."""\n'
        "\npytest_plugins = ['aiida.tools.pytest_fixtures']\n",
    )
    ctx.write(REPO_ROOT / '.github' / 'workflows' / 'ci-atomistic.yml', CI_CALLER)

    codeowners = REPO_ROOT / '.github' / 'CODEOWNERS'
    if codeowners.exists():
        text = codeowners.read_text(encoding='utf-8') if ctx.execute else ''
        # In dry-run mode we cannot know the content; print the intended lines instead.
        lines = (
            'aiida-atomistic/pyproject.toml              @agoscinski @GeigerJ2\n'
            'aiida-atomistic/uv.lock                     @agoscinski @GeigerJ2\n'
        )
        if not ctx.execute:
            print(f'append to .github/CODEOWNERS:\n{lines}')
        elif MARKER not in text:
            print('append to .github/CODEOWNERS')
            with codeowners.open('a', encoding='utf-8') as handle:
                handle.write(f'# Added by utils/{MARKER}\n{lines}')

    if (CORE / 'LICENSE.txt').exists() and not (PKG / 'LICENSE.txt').exists():
        print(f'copy: aiida-core/LICENSE.txt -> {PKG.relative_to(REPO_ROOT)}/LICENSE.txt')
        if ctx.execute:
            shutil.copy(CORE / 'LICENSE.txt', PKG / 'LICENSE.txt')


def phase_move(ctx: Ctx) -> None:
    """``git mv`` sources and tests (pure renames, no edits)."""
    for rel in SRC_FILES:
        ctx.git_mv(CORE_SRC / rel, PKG_SRC / rel)
    for rel in SRC_DIRS:
        src, dst = CORE_SRC / rel, PKG_SRC / rel
        if dst.exists():
            print(f'skip (moved already): {src.relative_to(REPO_ROOT)} -> {dst.relative_to(REPO_ROOT)}')
            continue
        if not src.exists():
            print(f'WARNING: missing, skipping: {src.relative_to(REPO_ROOT)}')
            continue
        print(f'git mv {src.relative_to(REPO_ROOT)} {dst.relative_to(REPO_ROOT)}')
        if ctx.execute:
            dst.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                ['git', 'mv', str(src.relative_to(REPO_ROOT)), str(dst.relative_to(REPO_ROOT))],
                cwd=REPO_ROOT,
                check=True,
            )
    for rel in TEST_FILES:
        ctx.git_mv(CORE_TESTS / rel, PKG_TESTS / rel)
    for rel in TEST_DIRS:
        src, dst = CORE_TESTS / rel, PKG_TESTS / rel
        if dst.exists() or not src.exists():
            ctx.git_mv(src, dst)  # prints the skip/warning
            continue
        print(f'git mv {src.relative_to(REPO_ROOT)} {dst.relative_to(REPO_ROOT)}')
        if ctx.execute:
            dst.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                ['git', 'mv', str(src.relative_to(REPO_ROOT)), str(dst.relative_to(REPO_ROOT))],
                cwd=REPO_ROOT,
                check=True,
            )
    # Ensure intermediate test packages stay importable (empty ``__init__.py``).
    seen: set[Path] = set()
    for rel in [*TEST_FILES, *TEST_DIRS]:
        parent = PKG_TESTS / Path(rel).parent
        init = parent / '__init__.py'
        if init in seen or init.exists():
            continue
        seen.add(init)
        print(f'write (empty): {init.relative_to(REPO_ROOT)}')
        if ctx.execute:
            parent.mkdir(parents=True, exist_ok=True)
            init.write_text('', encoding='utf-8')
    # Regular (non-namespace) packages everywhere: intermediate directories that
    # only gained leaf files need an ``__init__.py`` too, otherwise the new tree
    # relies on PEP 420 fallback and flit may omit files from wheels. Minimal
    # content only (no star imports: eager aggregation causes import cycles).
    for missing in planned_intermediate_inits():
        if PKG_SRC in missing.parents:
            dotted = 'aiida_atomistic.' + '.'.join(missing.parent.relative_to(PKG_SRC).parts)
        else:
            dotted = 'tests.' + '.'.join(missing.parent.relative_to(PKG_TESTS).parts).strip('.')
        ctx.write(missing, f"{COPYRIGHT_HEADER}'''{dotted}.'''\n")


def iter_moved_files() -> list[Path]:
    """All ``.py`` files now living in ``aiida-atomistic`` (sources + tests)."""
    files: list[Path] = []
    for base in (PKG_SRC, PKG_TESTS):
        if base.exists():
            files.extend(sorted(base.rglob('*.py')))
    return files


def files_for_rewrite() -> list[Path]:
    """Files whose imports get rewritten: new locations, else current sources (dry run)."""
    moved = iter_moved_files()
    if moved:
        return moved
    files = [CORE_SRC / rel for rel in SRC_FILES] + [CORE_TESTS / rel for rel in TEST_FILES]
    for rel in SRC_DIRS:
        base = CORE_SRC / rel
        if base.exists():
            files.extend(sorted(base.rglob('*.py')))
    for rel in TEST_DIRS:
        base = CORE_TESTS / rel
        if base.exists():
            files.extend(sorted(base.rglob('*.py')))
    return [f for f in files if f.exists()]


PRUNABLE_DEPS = {
    # requirement name in aiida-core main dependencies -> import top-levels it provides.
    # Removed from core iff no core source or test file imports it anymore (verified, not assumed).
    'upf_to_json': ('upf_to_json',),
}

REST_TRANSLATORS = {
    # entry name -> (module, class, expected ``_aiida_type`` contract, unchanged by the move)
    'bands': (
        'aiida_atomistic.restapi.translator.nodes.data.array.bands',
        'BandsDataTranslator',
        'data.core.array.bands.BandsData',
    ),
    'cif': ('aiida_atomistic.restapi.translator.nodes.data.cif', 'CifDataTranslator', 'data.core.cif.CifData'),
    'kpoints': (
        'aiida_atomistic.restapi.translator.nodes.data.kpoints',
        'KpointsDataTranslator',
        'data.core.array.kpoints.KpointsData',
    ),
    'structure': (
        'aiida_atomistic.restapi.translator.nodes.data.structure',
        'StructureDataTranslator',
        'data.core.structure.StructureData',
    ),
    'upf': ('aiida_atomistic.restapi.translator.nodes.data.upf', 'UpfDataTranslator', 'data.core.upf.UpfData'),
}

# Substitutions turning ``release.yml`` into ``release-atomistic.yml``. Each must
# match >=1 time (checked); review the diff, release flows only run on tags.
RELEASE_SUBSTITUTIONS = [
    ('name: release\n\n# Automate', 'name: release-atomistic\n\n# Automate'),
    ('paths-ignore: [aiida-core/docs/**]', "paths: ['aiida-atomistic/**']"),
    ('    - v[0-9]+.[0-9]+.[0-9]+*', '    - atomistic-v[0-9]+.[0-9]+.[0-9]+*'),
    ('# tag and aiida-core version and tag match.', '# tag and aiida-atomistic version and tag match.'),
    (
        'run: python .github/workflows/check_release_tag.py $GITHUB_REF',
        'run: python .github/workflows/check_release_tag.py $GITHUB_REF'
        ' --tag-prefix atomistic-v --init-module aiida-atomistic/src/aiida_atomistic/__init__.py',
    ),
    ('- name: Install aiida-core and pre-commit', '- name: Install aiida-atomistic and pre-commit'),
    ('- name: Install aiida-core\n', '- name: Install aiida-atomistic\n'),
    (
        "        python-version: '3.11'\n        extras: pre-commit",
        "        python-version: '3.11'\n        package: aiida-atomistic\n        extras: pre-commit",
    ),
    (
        "        python-version: '3.10'\n\n    - name: Run sub-set",
        "        python-version: '3.10'\n        package: aiida-atomistic\n\n    - name: Run sub-set",
    ),
    (
        'run: pytest -s -m requires_broker --broker-backend zmq --db-backend=sqlite aiida-core/tests/',
        'run: pytest -s -m requires_broker --broker-backend zmq --db-backend=sqlite aiida-atomistic/tests/',
    ),
    (
        '    - name: Build\n      run: flit build',
        '    - name: Build\n      working-directory: aiida-atomistic\n      run: flit build',
    ),
    (
        '    - name: Publish to PyPI\n      uses: pypa/gh-action-pypi-publish@release/v1\n',
        '    - name: Publish to PyPI\n      uses: pypa/gh-action-pypi-publish@release/v1\n'
        '      with:\n        packages-dir: aiida-atomistic/dist\n',
    ),
    (
        '        repository-url: https://test.pypi.org/legacy/',
        '        repository-url: https://test.pypi.org/legacy/\n        packages-dir: aiida-atomistic/dist',
    ),
]


def phase_rewrite(ctx: Ctx) -> None:
    """Rewrite imports/entry points in the new package; shim the core."""
    # 1. Rewrite ``aiida.*`` imports of moved modules inside moved files.
    # In dry-run mode the move has not happened yet, so preview against sources.
    for path in files_for_rewrite():
        text = path.read_text(encoding='utf-8')
        _, count = rewrite_imports(text)
        if count:
            action = 'rewrite' if ctx.execute else 'would rewrite'
            print(f'{action} {count} import(s): {path.relative_to(REPO_ROOT)}')
            if ctx.execute:
                path.write_text(rewrite_imports(text)[0], encoding='utf-8')

    # 2. Move entry-point rows from core to the new package, keeping names.
    core_pp = CORE / 'pyproject.toml'
    new_pp = PKG / 'pyproject.toml'
    if core_pp.exists() and (new_pp.exists() or not ctx.execute):
        print(f'move entry points: {core_pp.relative_to(REPO_ROOT)} -> {new_pp.relative_to(REPO_ROOT)}')
        preview_entry_point_move(core_pp)
        print('  note: aiida.groups:core.upf keeps its core target until UpfFamily moves (manual)')
        if ctx.execute:
            move_entry_points(core_pp, new_pp)
    else:
        print('WARNING: skipping entry-point move (missing pyproject.toml)')

    # 3. Patch core aggregator ``__init__`` files: drop star imports + names, add shims.
    for rel, (stars, all_names, redirects) in SHIM_PLAN.items():
        patch_core_init(ctx, CORE_SRC / rel, stars, all_names, redirects)

    # 4. Report moved tests that still depend on core-only test helpers.
    report_test_deps()

    # 5. Follow-ups with sound generic logic (no arbitrary code moving).
    prune_core_deps(ctx)
    comigrate_static_assets(ctx)
    update_shared_configs(ctx)
    register_rest_translators(ctx)
    patch_rest_discovery(ctx)
    template_release_flow(ctx)
    lock_atomistic(ctx)
    lock_core(ctx)

    # 6. Verify the result (compile, leftovers, contracts, smoke import).
    verify_migration(ctx)


def rewrite_entry_point_target(group: str, name: str, target: str) -> str:
    """Return the relocated entry-point target.

    ``aiida.groups:core.upf`` keeps pointing at core: ``UpfFamily`` still lives
    in ``aiida/orm/groups.py`` and its extraction is manual (see checklist).
    """
    if group == 'aiida.groups' and name == 'core.upf':
        return target
    module, _, attr = target.partition(':')
    new_module = should_rewrite(module)
    if new_module is None:  # whole-group move (dbimporters/orbitals): mirror package layout
        new_module = 'aiida_atomistic.' + module.removeprefix('aiida.')
    return f'{new_module}:{attr}'


def entry_row_moves(group: str, modpath: str) -> bool:
    """Whether an entry-point row relocates to the new package."""
    rule = ENTRY_POINT_RULES.get(group)
    if rule == 'all':
        return True
    if rule == 'by-module':
        # ``aiida.groups`` rows are resolved by name (``core.upf``) by the caller:
        # several groups share the ``aiida.orm.groups`` module.
        if group == 'aiida.groups':
            return False
        return should_rewrite(modpath.split(':', maxsplit=1)[0]) is not None
    return False


def collect_entry_point_moves(core_text: str) -> dict[str, list[str]]:
    """Parse core pyproject text; return group -> rewritten `name = target` rows to move."""
    moved: dict[str, list[str]] = {}
    for group, _, _, lines in parse_entry_point_sections(core_text):
        for row in lines[1:]:
            match = re.match(r"'([^']+)'\s*=\s*'([^']+)'", row.strip())
            if not match:
                continue
            name, target = match.group(1), match.group(2)
            move = entry_row_moves(group, target)
            if group == 'aiida.groups' and name == 'core.upf':
                move = True  # keep in sync with move_entry_points
            if move:
                new_target = rewrite_entry_point_target(group, name, target)
                moved.setdefault(group, []).append(f"'{name}' = '{new_target}'")
    return moved


def preview_entry_point_move(core_pp: Path) -> None:
    """Print the entry-point rows that would relocate."""
    for group, rows in collect_entry_point_moves(core_pp.read_text(encoding='utf-8')).items():
        print(f'  {group}: {len(rows)} row(s) -> ' + ', '.join(r.split(' = ')[0] for r in rows))


def move_entry_points(core_pp: Path, new_pp: Path) -> None:
    """Move entry-point rows, preserving non-section content byte-for-byte."""
    core_text = core_pp.read_text(encoding='utf-8')
    sections = parse_entry_point_sections(core_text)
    moved: dict[str, list[str]] = {}
    new_sections: list[str] = []

    for group, _start, _end, lines in sections:
        header, rows = lines[0], lines[1:]
        kept: list[str] = []
        for row in rows:
            stripped = row.strip()
            match = re.match(r"'([^']+)'\s*=\s*'([^']+)'", stripped)
            if not match:
                kept.append(row)
                continue
            name, target = match.group(1), match.group(2)
            move = entry_row_moves(group, target)
            if group == 'aiida.groups' and name == 'core.upf':
                move = True  # keep in sync with collect_entry_point_moves
            if move:
                new_target = rewrite_entry_point_target(group, name, target)
                moved.setdefault(group, []).append(f"'{name}' = '{new_target}'\n")
            else:
                kept.append(row)
        new_sections.append(header + ''.join(kept))

    # Splice transformed sections back, preserving everything else byte-for-byte.
    # (An earlier version rewrote the file from sections only, dropping all
    # non-entry-point content; never reconstruct packaging files from slices.)
    core_lines = core_text.splitlines(keepends=True)
    edits: list[tuple[int, int, str]] = []
    for (group, _start, _end, _lines), new_section in zip(sections, new_sections):
        body = ''.join(new_section.splitlines(keepends=True)[1:])
        if body.strip() == '' and (moved.get(group) or ENTRY_POINT_RULES.get(group) == 'all'):
            edits.append((_start, _end, ''))  # whole group relocated; drop the span
        else:
            edits.append((_start, _end, new_section))
    out: list[str] = []
    cursor = 0
    for start, end, new_text in edits:
        out.extend(core_lines[cursor:start])
        out.append(new_text)
        cursor = end
    out.extend(core_lines[cursor:])
    core_pp.write_text(''.join(out), encoding='utf-8')

    # Append only rows not already registered (idempotent re-runs).
    existing = new_pp.read_text(encoding='utf-8') if new_pp.exists() else ''
    present = {
        (group, match.group(1))
        for group, _, _, section_lines in parse_entry_point_sections(existing)
        for row in section_lines[1:]
        if (match := re.match(r"'([^']+)'\s*=", row.strip()))
    }
    fresh = {
        group: [row for row in rows if (group, row.split(' = ')[0].strip("'")) not in present]
        for group, rows in moved.items()
    }
    skipped = sum(len(rows) - len(fresh.get(group, [])) for group, rows in moved.items())
    if skipped:
        print(f'  skip {skipped} already-registered row(s)')
    addition = ''.join(f"\n[project.entry-points.'{group}']\n" + ''.join(rows) for group, rows in fresh.items() if rows)
    if addition:
        with new_pp.open('a', encoding='utf-8') as handle:
            handle.write(addition)
    print('  moved entry points: ' + ', '.join(f'{group} ({len(rows)})' for group, rows in fresh.items() if rows))


def core_importers(modules: tuple[str, ...]) -> list[str]:
    """Files under ``aiida-core`` importing any of the given top-level modules."""
    hits: list[str] = []
    roots = [CORE_SRC, CORE_TESTS] if CORE_TESTS.exists() else [CORE_SRC]
    for root in roots:
        for path in sorted(root.rglob('*.py')):
            text = path.read_text(encoding='utf-8')
            for mod in modules:
                if re.search(rf'^\s*(from|import)\s+{re.escape(mod)}(?=[\s.#])', text, re.MULTILINE):
                    hits.append(f'{path.relative_to(REPO_ROOT)} imports {mod}')
                    break
    return hits


def prune_core_deps(ctx: Ctx) -> None:
    """Drop core main dependencies with provably zero remaining core importers."""
    path = CORE / 'pyproject.toml'
    lines = path.read_text(encoding='utf-8').splitlines(keepends=True)
    try:
        start = next(i for i, line in enumerate(lines) if line.strip() == 'dependencies = [')
        end = next(i for i in range(start, len(lines)) if lines[i].strip() == ']')
    except StopIteration:
        print('WARNING: no main `dependencies` block found; skipping prune')
        return
    for dep, modules in PRUNABLE_DEPS.items():
        hits = core_importers(modules)
        if hits:
            print(f'keep {dep} in core (still used):')
            for hit in hits:
                print(f'  - {hit}')
            continue
        idx = next(
            (i for i in range(start, end) if (m := re.match(r"\s*'([^=<>~!\s\[]+)", lines[i])) and m.group(1) == dep),
            None,
        )
        if idx is None:
            print(f'skip (already pruned): {dep}')
            continue
        print(f'prune from aiida-core dependencies (no importers left): {dep}')
        if ctx.execute:
            del lines[idx]
            path.write_text(''.join(lines), encoding='utf-8')
            lines = path.read_text(encoding='utf-8').splitlines(keepends=True)
            start = next(i for i, line in enumerate(lines) if line.strip() == 'dependencies = [')
            end = next(i for i in range(start, len(lines)) if lines[i].strip() == ']')


def static_asset_roots() -> set[str]:
    """Top-level ``tests/static`` entries referenced by moved tests (via ``STATIC_DIR``)."""
    roots: set[str] = set()
    pattern = re.compile(r"STATIC_DIR\s*,\s*['\"]([^'\"]+)['\"]")
    for path in iter_moved_files():
        if PKG_TESTS in path.parents and path.suffix == '.py' and path.exists():
            roots.update(pattern.findall(path.read_text(encoding='utf-8')))
    return roots


def comigrate_static_assets(ctx: Ctx) -> None:
    """Copy static test data referenced by moved tests (core keeps its copy too).

    Copies, not moves: core tests (e.g. archive tests) still need the files.
    The ``check-added-large-files`` hook exclusion below covers the duplicate.
    """
    roots = static_asset_roots()
    if not roots:
        print('static assets: none referenced')
        return
    for root in sorted(roots):
        src, dst = CORE_TESTS / 'static' / root, PKG_TESTS / 'static' / root
        if dst.exists():
            print(f'skip (exists): {dst.relative_to(REPO_ROOT)}')
            continue
        if not src.exists():
            print(f'WARNING: missing, skipping: {src.relative_to(REPO_ROOT)}')
            continue
        size_mb = sum(f.stat().st_size for f in src.rglob('*') if f.is_file()) / 1e6
        print(f'copy: {src.relative_to(REPO_ROOT)} -> {dst.relative_to(REPO_ROOT)} ({size_mb:.1f} MB)')
        if ctx.execute:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src, dst)
    ctx.write(
        PKG_TESTS / 'static' / '__init__.py',
        f'{COPYRIGHT_HEADER}"""Collection of static test data for aiida-atomistic."""\n'
        '\nimport os\n\nSTATIC_DIR = os.path.dirname(__file__)\n',
    )
    print('note: `from tests.static import ...` resolves to the new package in its own pytest run')


def _migrate_mypy_excludes(lines: list[str], start: int, end: int) -> tuple[list[str], list[str]]:
    """Re-prefix mypy excludes of moved files; drop ones matching nothing in core."""
    added: list[str] = []
    dropped: list[str] = []
    kept: list[str] = []
    for line in lines[start:end]:
        match = re.match(r'^(\s*)(aiida-core/src/aiida/\S+?)\s*$', line.rstrip('\n'))
        if not match:
            kept.append(line)
            continue
        indent, entry = match.group(1), match.group(2)
        core_rel = entry.rstrip('|')
        is_regex = bool(re.search(r'[.*?\[\]()+]', core_rel))
        literal = core_rel.split('/.*')[0] if '/.*' in core_rel else core_rel
        rel_path = literal.removeprefix('aiida-core/src/aiida/')
        in_moved_tree = any(rel_path == rel or rel_path.startswith(rel + '/') for rel in [*SRC_FILES, *SRC_DIRS])
        if not in_moved_tree:
            kept.append(line)
            continue
        new_entry = entry.replace('aiida-core/src/aiida/', 'aiida-atomistic/src/aiida_atomistic/', 1)
        if is_regex:
            remains = [p for p in (CORE_SRC / literal).rglob('*.py')] if (CORE_SRC / literal).is_dir() else []
            if not remains:
                dropped.append(core_rel)
            else:
                kept.append(line)  # mixed content (e.g. translator nodes): keep core line too
            added.append(f'{indent}{new_entry}')
        elif (CORE_SRC / literal).exists():
            kept.append(line)  # not moved after all; be conservative
        else:
            dropped.append(core_rel)
            added.append(f'{indent}{new_entry}')
    return kept, added, dropped


def update_shared_configs(ctx: Ctx) -> None:
    """Update repo-root tooling configs for the new package (deterministic edits)."""
    precommit = REPO_ROOT / '.pre-commit-config.yaml'
    text = precommit.read_text(encoding='utf-8')
    lines = text.splitlines(keepends=True)
    start = next(i for i, line in enumerate(lines) if line.strip() == '- id: mypy')
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith('  - id: ')), len(lines))
    kept, added, dropped = _migrate_mypy_excludes(lines, start, end)
    if 'aiida-atomistic/tests/.*|' not in ''.join(kept + added):
        added.append('        aiida-atomistic/tests/.*|')
    # `kept` already covers lines[start:end] filtered; insert `added` before
    # its closing `)$` instead of appending after it (which yields `)$ ... )$`).
    close_in_kept = next(i for i, line in enumerate(kept) if line.strip() == ')$')
    new_lines = kept[:close_in_kept] + [f'{line}\n' for line in added] + kept[close_in_kept:]
    if dropped or added:
        print(f'mypy excludes: -{len(dropped)} dead core rows, +{len(added)} atomistic rows')
        for row in dropped:
            print(f'  - {row}')
        if ctx.execute:
            precommit.write_text(''.join(lines[:start] + new_lines + lines[end:]), encoding='utf-8')
            # Re-read: later blocks below must build on the updated content,
            # otherwise they silently wipe this change (stale `text`).
            text = precommit.read_text(encoding='utf-8')
    else:
        print('mypy excludes: OK (nothing to migrate)')
    # uv-lock hook: mirrored block for the new package.
    hook_old = (
        '  - id: uv-lock\n    args: [--project, aiida-core]\n    files: ^aiida-core/(uv\\.lock|pyproject\\.toml)$\n'
    )
    hook_new = hook_old + (
        '  - id: uv-lock\n    args: [--project, aiida-atomistic]\n'
        '    files: ^aiida-atomistic/(uv\\.lock|pyproject\\.toml)$\n'
    )
    if '--project, aiida-atomistic' in text:
        print('uv-lock hook: OK (already wired)')
    else:
        print('uv-lock hook: add aiida-atomistic block')
        if ctx.execute:
            precommit.write_text(text.replace(hook_old, hook_new), encoding='utf-8')
            text = precommit.read_text(encoding='utf-8')
    # Large test-data duplicates are intentional; keep the hook meaningful otherwise.
    large_old = '  - id: check-added-large-files\n    exclude: uv.lock\n'
    large_new = (
        '  - id: check-added-large-files\n    exclude: >-\n      (?x)(\n'
        '        uv.lock|\n        aiida-atomistic/tests/static/\n      )\n'
    )
    if 'aiida-atomistic/tests/static/' in text:
        print('large-files hook: OK (already wired)')
    else:
        print('large-files hook: exclude intentional test-data duplicates')
        if ctx.execute:
            precommit.write_text(text.replace(large_old, large_new), encoding='utf-8')
    # pixi tasks mirroring the core ones.
    pixi = REPO_ROOT / 'pixi.toml'
    pixi_text = pixi.read_text(encoding='utf-8')
    if 'sync-atomistic' in pixi_text:
        print('pixi tasks: OK (already wired)')
    else:
        anchor_key = 'test-smoke = {cmd = "uv run --project aiida-core pytest '
        task_idx = [i for i, line in enumerate(pixi_text.splitlines()) if anchor_key in line]
        assert len(task_idx) == 1, 'pixi anchor changed upstream'
        new_tasks = [
            'sync-atomistic = { cmd = "uv sync --project aiida-atomistic", '
            'description = "Sync the aiida-atomistic dev environment" }\n',
            'test-atomistic = { cmd = "uv run --project aiida-atomistic pytest '
            "aiida-atomistic/tests/ -x -q -m 'not nightly'\", "
            'description = "Full aiida-atomistic suite (needs PostgreSQL + RabbitMQ)" }\n',
            'test-smoke-atomistic = { cmd = "uv run --project aiida-atomistic pytest '
            'aiida-atomistic/tests/ -q --collect-only", '
            'description = "Collect aiida-atomistic tests (no services needed)" }\n',
        ]
        print('pixi tasks: add sync/test/test-smoke variants for aiida-atomistic')
        if ctx.execute:
            toml_lines = pixi_text.splitlines(keepends=True)
            toml_lines[task_idx[0] + 1 : task_idx[0] + 1] = new_tasks
            pixi.write_text(''.join(toml_lines), encoding='utf-8')


def register_rest_translators(ctx: Ctx) -> None:
    """Register moved REST translators under a new ``aiida.restapi.translators`` group."""
    group = 'aiida.restapi.translators'
    new_pp = PKG / 'pyproject.toml'
    if not new_pp.exists():
        print('WARNING: skipping translator registration (missing pyproject.toml)')
        return
    text = new_pp.read_text(encoding='utf-8')
    if f"[project.entry-points.'{group}']" in text:
        print(f'{group}: OK (already registered)')
        return
    rows = ''.join(f"'{name}' = '{module}:{cls}'\n" for name, (module, cls, _) in sorted(REST_TRANSLATORS.items()))
    print(f'{group}: register {len(REST_TRANSLATORS)} translators')
    for name in sorted(REST_TRANSLATORS):
        print(f'  {name}')
    if ctx.execute:
        with new_pp.open('a', encoding='utf-8') as handle:
            handle.write(f"\n[project.entry-points.'{group}']\n{rows}")


def patch_rest_discovery(ctx: Ctx) -> None:
    """Teach core translator discovery about entry-point-contributed translators.

    ``NodeTranslator._get_subclasses`` walks core's package directory, which no
    longer contains the moved translators. This generic extension additionally
    loads the ``aiida.restapi.translators`` group (empty when aiida-atomistic
    is absent), keeping the sanctioned direction: core discovers subpackages
    through entry points, never hard imports.
    """
    path = CORE_SRC / 'restapi' / 'translator' / 'nodes' / 'node.py'
    text = path.read_text(encoding='utf-8')
    if MARKER in text:
        print(f'skip (patched already): {path.relative_to(REPO_ROOT)}')
        return
    anchor = (
        '                results.update(self._get_subclasses(parent=app_module, parent_class=parent_class))\n'
        '\n        return results'
    )
    assert text.count(anchor) == 1, 'rest discovery anchor changed upstream'
    block = (
        '                results.update(self._get_subclasses(parent=app_module, parent_class=parent_class))\n'
        '\n        # Added by utils/extract_atomistic.py: translators contributed by\n'
        '        # distributions (e.g. ``aiida-atomistic``) via the\n'
        '        # ``aiida.restapi.translators`` entry-point group. An absent group\n'
        '        # simply contributes nothing.\n'
        '        if isinstance(parent_class, type):\n'
        '            from aiida.plugins.entry_point import get_entry_points\n'
        '\n'
        "            for translator_entry_point in get_entry_points('aiida.restapi.translators'):\n"
        '                try:\n'
        '                    translator = translator_entry_point.load()\n'
        '                except ImportError:\n'
        '                    continue\n'
        '                if inspect.isclass(translator) and issubclass(translator, parent_class):\n'
        '                    results[translator_entry_point.name] = translator\n'
        '\n        return results'
    )
    print(f'patch: {path.relative_to(REPO_ROOT)} (+entry-point translator discovery)')
    if ctx.execute:
        path.write_text(text.replace(anchor, block), encoding='utf-8')
        ast.parse(path.read_text(encoding='utf-8'))


def template_release_flow(ctx: Ctx) -> None:
    """Generate ``release-atomistic.yml`` from ``release.yml`` (needs human review)."""
    generalize_check_release_tag(ctx)
    src = REPO_ROOT / '.github' / 'workflows' / 'release.yml'
    dst = REPO_ROOT / '.github' / 'workflows' / 'release-atomistic.yml'
    if dst.exists():
        print(f'skip (exists): {dst.relative_to(REPO_ROOT)}')
        return
    text = src.read_text(encoding='utf-8')
    for old, new in RELEASE_SUBSTITUTIONS:
        if old not in text:
            print(f'WARNING: substitution anchor missing, skipping: {old[:60]!r}')
            continue
        text = text.replace(old, new)
    checks = [
        'name: release-atomistic' in text,
        'atomistic-v[0-9]' in text,
        'aiida-core/tests' not in text,
        '--tag-prefix atomistic-v' in text,
        text.count('packages-dir: aiida-atomistic/dist') == 2,
        text.count('package: aiida-atomistic') == 2,
    ]
    print(f'write: {dst.relative_to(REPO_ROOT)} (self-checks: {sum(checks)}/{len(checks)})')
    if not all(checks):
        print('WARNING: release template self-checks failed; inspect RELEASE_SUBSTITUTIONS')
    if ctx.execute:
        dst.write_text(text, encoding='utf-8')
    print('note: release workflow is generated, not tested; needs human review + PyPI trusted-publisher setup')


def generalize_check_release_tag(ctx: Ctx) -> None:
    """Parameterize the tag checker (defaults preserve core behavior exactly)."""
    path = REPO_ROOT / '.github' / 'workflows' / 'check_release_tag.py'
    text = path.read_text(encoding='utf-8')
    if '--tag-prefix' in text:
        print(f'skip (patched already): {path.relative_to(REPO_ROOT)}')
        return
    print(f'patch: {path.relative_to(REPO_ROOT)} (+--tag-prefix/--init-module, defaults unchanged)')
    old = """    parser.add_argument('GITHUB_REF', help='The GITHUB_REF environmental variable')"""
    new = """    parser.add_argument('GITHUB_REF', help='The GITHUB_REF environmental variable')
    parser.add_argument('--tag-prefix', default='v', help='Release tag prefix before the version')
    parser.add_argument(
        '--init-module',
        default='aiida-core/src/aiida/__init__.py',
        help='Package __init__.py carrying __version__ (relative to the repository root)',
    )"""
    assert text.count(old) == 1
    text = text.replace(old, new)
    old_core = (
        "    assert args.GITHUB_REF.startswith('refs/tags/v'), "
        'f\'GITHUB_REF should start with "refs/tags/v": {args.GITHUB_REF}\'\n'
        '    tag_version = args.GITHUB_REF[11:]\n'
        "    pypi_version = get_version_from_module(Path('aiida-core/src/aiida/__init__.py')"
        ".read_text(encoding='utf-8'))"
    )
    old_legacy = old_core.replace('aiida-core/src/aiida/__init__.py', 'src/aiida/__init__.py')
    old = old_core if text.count(old_core) == 1 else old_legacy
    new = """    expected_start = f'refs/tags/{args.tag_prefix}'
    assert args.GITHUB_REF.startswith(expected_start), (
        f'GITHUB_REF should start with "{expected_start}": {args.GITHUB_REF}'
    )
    tag_version = args.GITHUB_REF[len(expected_start) :]
    pypi_version = get_version_from_module(Path(args.init_module).read_text(encoding='utf-8'))"""
    assert text.count(old) == 1
    text = text.replace(old, new)
    if ctx.execute:
        path.write_text(text, encoding='utf-8')
        ast.parse(path.read_text(encoding='utf-8'))


def check_translator_contract() -> None:
    """Assert moved REST translators kept their ``_aiida_type`` contract (AST, no imports)."""
    errors: list[str] = []
    for name, (module, cls, aiida_type) in sorted(REST_TRANSLATORS.items()):
        path = PKG_SRC / ('/'.join(module.split('.')[1:]) + '.py')
        if not path.exists():
            errors.append(f'{name}: missing {path.relative_to(REPO_ROOT)}')
            continue
        found = None
        tree = ast.parse(path.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == cls:
                for stmt in node.body:
                    if (
                        isinstance(stmt, ast.Assign)
                        and any(isinstance(target, ast.Name) and target.id == '_aiida_type' for target in stmt.targets)
                        and isinstance(stmt.value, ast.Constant)
                    ):
                        found = stmt.value.value
        if found != aiida_type:
            errors.append(f'{name}: _aiida_type is {found!r}, expected {aiida_type!r}')
    if errors:
        print('ERROR: REST translator contract broken:')
        for line in errors:
            print(f'  - {line}')
    else:
        print(f'translator contract: OK ({len(REST_TRANSLATORS)} _aiida_type values unchanged)')


def lock_project(ctx: Ctx, project: str) -> None:
    """Regenerate ``<project>/uv.lock`` (best effort: needs network)."""
    if not ctx.execute:
        print(f'$ uv lock --project {project}')
        return
    uv = shutil.which('uv')
    if uv is None:
        print(f'WARNING: `uv` not found; run `uv lock --project {project}` manually')
        return
    print(f'$ uv lock --project {project}')
    result = subprocess.run(
        [uv, 'lock', '--project', project],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=600,
    )
    if result.returncode != 0:
        print('WARNING: `uv lock` failed (offline?); run it manually once online')
        print('\n'.join(result.stderr.strip().splitlines()[-3:]))
    else:
        print(f'wrote {project}/uv.lock')


def lock_atomistic(ctx: Ctx) -> None:
    """Generate ``aiida-atomistic/uv.lock`` (best effort: needs network)."""
    lock_project(ctx, 'aiida-atomistic')


def lock_core(ctx: Ctx) -> None:
    """Regenerate ``aiida-core/uv.lock`` after pruning (best effort)."""
    lock_project(ctx, 'aiida-core')


def patch_core_init(ctx: Ctx, path: Path, stars: list[str], all_names: list[str], redirects: dict[str, str]) -> None:
    """Drop moved star imports/names from a core aggregator and add a lazy shim."""
    rel = path.relative_to(REPO_ROOT)
    if not path.exists():
        print(f'WARNING: missing, skipping: {rel}')
        return
    text = path.read_text(encoding='utf-8')
    if MARKER in text:
        print(f'skip (patched already): {rel}')
        return
    print(f'patch: {rel} (-{len(stars)} star imports, -{len(all_names)} __all__ names, +shim)')
    if not ctx.execute:
        return
    lines = text.splitlines(keepends=True)
    lines = [line for line in lines if line.strip() not in stars]
    for name in all_names:
        lines = [line for line in lines if line.strip() != f"'{name}',"]
    redirect_block = ''.join(f"    {name!r}: '{target}',\n" for name, target in sorted(redirects.items()))
    shim = '\n' + SHIM_TEMPLATE.format(marker=MARKER, redirects=redirect_block.rstrip('\n'))
    # Keep `import importlib` deduplicated: the shim uses a private alias.
    path.write_text(''.join(lines).rstrip('\n') + '\n' + shim, encoding='utf-8')


def verify_migration(ctx: Ctx) -> None:
    """Compile moved files, scan for leftovers, and smoke-import the result."""
    if not PKG_SRC.exists():
        print('skip verification (package not moved yet)')
        return
    # 1. Byte-compile everything moved (no third-party deps needed).
    ok_src = compileall.compile_dir(PKG_SRC, quiet=1)
    ok_tests = compileall.compile_dir(PKG_TESTS, quiet=1) if PKG_TESTS.exists() else True
    print(f'compileall: {"OK" if ok_src and ok_tests else "FAILED"}')
    # 2. Moved files must not import moved names through core aggregators anymore.
    mapping = _moved_name_to_module()
    from_import = re.compile(r'^\s*from\s+(aiida(?:\.\w+)*)\s+import\s+([^\n]+)', re.MULTILINE)
    pending: list[str] = []
    for path in iter_moved_files():
        for match in from_import.finditer(path.read_text(encoding='utf-8')):
            mod, raw = match.group(1), match.group(2).split('#')[0]
            if 'aiida_atomistic' in mod or should_rewrite(mod) is not None:
                continue
            names = [item.partition(' as ')[0].strip().strip('() ') for item in raw.split(',')]
            hit = sorted({name for name in names if name in mapping})
            if hit:
                pending.append(f'{path.relative_to(REPO_ROOT)}: {mod} imports {", ".join(hit)}')
    if pending:
        print('WARNING: aggregator imports left for manual cleanup:')
        for line in pending:
            print(f'  - {line}')
    else:
        print('aggregator imports: OK (all direct)')
    check_translator_contract()
    # 3. Core must not hard-import the subpackage (forbidden direction).
    reverse = [
        str(path.relative_to(REPO_ROOT))
        for path in sorted(CORE_SRC.rglob('*.py'))
        if re.search(r'^\s*(from|import)\s+aiida_atomistic[\s.]', path.read_text(encoding='utf-8'), re.MULTILINE)
    ]
    if reverse:
        print('ERROR: core hard-imports aiida_atomistic (forbidden direction):')
        for line in reverse:
            print(f'  - {line}')
    else:
        print('core reverse imports: OK (none)')
    # 4. Smoke-import with the core venv when available (best effort).
    venv_python = CORE / '.venv' / 'bin' / 'python'
    if not ctx.execute:
        print('skip smoke import (dry run)')
    elif not venv_python.exists():
        print('skip smoke import (aiida-core/.venv not found)')
    else:
        # NOTE: `src` layout -> PYTHONPATH needs the `src/` parents, not the packages.
        env = {**os.environ, 'PYTHONPATH': f'{PKG / "src"}{os.pathsep}{CORE / "src"}'}
        cmd = [
            str(venv_python),
            '-c',
            'import aiida_atomistic;'
            'from aiida_atomistic.orm.nodes.data.structure import StructureData;'
            'from aiida.orm import StructureData as S2;'
            'assert S2 is StructureData, "core shim mismatch";'
            "print('smoke import: OK')",
        ]
        print('$ <venv-python> -c ... (top import, leaf import, core shim)')
        result = subprocess.run(cmd, cwd=REPO_ROOT, env=env, capture_output=True, text=True, check=False)
        output = result.stdout.strip() or result.stderr.strip()
        if output:
            print(output)
        if result.returncode != 0:
            print('ERROR: smoke import failed')


def report_test_deps() -> None:
    """List moved tests importing core-only helpers (need manual asset moves)."""
    offenders: list[str] = []
    for path in iter_moved_files():
        if PKG_TESTS not in path.parents or not path.exists():
            continue
        text = path.read_text(encoding='utf-8')
        if re.search(r'^\s*(from|import)\s+tests[\s.]', text, re.MULTILINE):
            offenders.append(str(path.relative_to(REPO_ROOT)))
    if offenders:
        print('Moved tests needing core test assets (manual: copy to aiida-atomistic/tests/static/):')
        for item in offenders:
            print(f'  - {item}')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--execute', action='store_true', help='perform the changes (default: dry run)')
    parser.add_argument(
        '--phase',
        choices=['scaffold', 'move', 'rewrite'],
        default=None,
        help='run only one phase (default: all, in order scaffold -> move -> rewrite)',
    )
    parser.add_argument(
        '--commit',
        action='store_true',
        help='commit all executed phases as a single commit (later phases amend the first)',
    )
    args = parser.parse_args()
    ctx = Ctx(execute=args.execute)

    if not args.execute:
        print('# DRY RUN -- pass --execute to apply\n')
    if args.commit and args.execute and not working_tree_clean():
        print('ERROR: working tree has uncommitted tracked changes; refusing --commit.')
        print('Commit or stash them first so the extraction lands as a single clean commit.')
        return 1

    phases = {'scaffold': phase_scaffold, 'move': phase_move, 'rewrite': phase_rewrite}
    stage_paths = {
        'scaffold': SCAFFOLD_PATHS,
        'move': ['aiida-core', 'aiida-atomistic'],
        'rewrite': ['aiida-core', 'aiida-atomistic', *REWRITE_EXTRA_PATHS],
    }
    selected = [args.phase] if args.phase else ['scaffold', 'move', 'rewrite']
    # Amend across invocations too: separate `--phase X --commit` runs keep
    # extending the same extraction commit instead of creating one per phase.
    # `in_commit` tracks which phase entries the single commit message has.
    committed = False
    in_commit: list[str] = []
    if args.commit and args.execute:
        head_subject = subprocess.run(
            ['git', 'log', '-1', '--format=%s'],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
        committed = head_subject == SINGLE_COMMIT_MSG
        if committed:
            head_body = subprocess.run(
                ['git', 'log', '-1', '--format=%B'],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            ).stdout
            in_commit = phases_in_head_message(head_body)
            print(f'(HEAD already is {SINGLE_COMMIT_MSG!r}; further phases will amend)')
    for name in selected:
        print(f'## phase: {name}')
        phases[name](ctx)
        if args.commit:
            pending = [p for p in ('scaffold', 'move', 'rewrite') if p in in_commit or p == name]
            message = build_commit_message(pending)
            if ctx.stage_and_commit(stage_paths[name], message=message, amend=committed):
                committed = True
                in_commit = pending

    print('\n' + MANUAL_CHECKLIST)
    if not args.execute:
        return 0
    # Sanity check: every moved dotted module resolves to an existing file.
    missing = []
    for rel in SRC_FILES:
        if not (PKG_SRC / rel).exists():
            missing.append(f'src/aiida_atomistic/{rel}')
    for rel in SRC_DIRS:
        if not (PKG_SRC / rel).is_dir():
            missing.append(f'src/aiida_atomistic/{rel}/')
    if missing:
        print('ERROR: expected moved paths missing:')
        for item in missing:
            print(f'  - {item}')
        return 1
    print('All moved paths present.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
