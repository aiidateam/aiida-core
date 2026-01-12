#!/usr/bin/env python
"""Pre-commit hook to add ``__all__`` imports to ``__init__`` files."""

import ast
import re
import sys
from collections import Counter
from pathlib import Path
from pprint import pprint
from typing import Optional

AUTO_GENERATED = 'AUTO-GENERATED'
# Four-space indentation level (must be compatible with the formatter!)
INDENT = '    '


def isort_alls(alls: set[str]) -> list[str]:
    """Sort module according to 'isort style' as used by RUF022 rule

    An isort-style sort orders items first according to their casing:
    SCREAMING_SNAKE_CASE names (conventionally used for global constants)
    come first, followed by CamelCase names (conventionally used for
    classes), followed by anything else. Within each category,
    a [natural sort](https://en.wikipedia.org/wiki/Natural_sort_order)
    is used to order the elements.
    """

    constants = set(mod for mod in alls if re.match(r'^[A-Z][A-Z_]*$', mod))
    # TODO: This doesn't represent cammel-case, only things that start with capital letters
    # and are not screaming case.
    classes = set(mod for mod in alls.difference(constants) if re.match(r'^[A-Z].*', mod))
    others = alls.difference(classes, constants)
    return sorted(constants) + sorted(classes) + sorted(others)


def parse_all(folder_path: Path) -> tuple[dict, dict]:
    """Walk through all files in folder, and parse the ``__all__`` variable.

    :return: (all dict, dict of unparsable)
    """
    all_dict: dict = {}
    bad_all: dict[str, list] = {}

    def is_ast_str(el: ast.AST) -> bool:
        """Replacement for deprecated ast.Str"""
        return isinstance(el, ast.Constant) and isinstance(el.value, str)

    for path in folder_path.glob('**/*.py'):
        # skip module files
        if path.name == '__init__.py':
            continue

        # parse the file
        parsed = ast.parse(path.read_text(encoding='utf8'))

        # find __all__ assignment
        all_token = None
        for token in parsed.body:
            if not isinstance(token, ast.Assign):
                continue
            if token.targets and getattr(token.targets[0], 'id', '') == '__all__':
                all_token = token
                break

        # If the module doesn't define __all__, skip it
        if all_token is None:
            continue

        # Warn if private module contains __all__
        if path.name.startswith('_'):
            bad_all.setdefault('__all__ in private module', []).append(str(path.relative_to(folder_path)))

        if not isinstance(all_token.value, (ast.List, ast.Tuple)):
            bad_all.setdefault('__all__ is not list/tuple', []).append(str(path.relative_to(folder_path)))
            continue

        if not all(is_ast_str(el) for el in all_token.value.elts):
            bad_all.setdefault('__all__ contains non-string elements', []).append(str(path.relative_to(folder_path)))
            continue

        names = [n.value for n in all_token.value.elts]  # type: ignore[attr-defined]
        if not names:
            continue

        path_dict = all_dict
        for part in path.parent.relative_to(folder_path).parts:
            if part.startswith('_'):
                bad_all.setdefault('__all__ in private package', []).append(str(path.relative_to(folder_path)))
                continue
            path_dict = path_dict.setdefault(part, {})
        path_dict.setdefault(path.name[:-3], {})['__all__'] = names

    return all_dict, bad_all


def gather_all(
    cur_path: list[str], cur_dict: dict, skip_children: dict, all_list: Optional[list[str]] = None
) -> list[str]:
    """Recursively gather __all__ names."""
    all_list = [] if all_list is None else all_list
    for key, val in cur_dict.items():
        if key == '__all__':
            all_list.extend(val)
        elif key not in skip_children.get('/'.join(cur_path), []):
            gather_all(cur_path + [key], val, skip_children, all_list)
    return all_list


def write_inits(folder_path: Path, all_dict: dict, skip_children: dict[str, list[str]]) -> dict[str, list[str]]:
    """Write __init__.py files for all subfolders.

    :return: folders with non-unique imports
    """
    non_unique = {}
    for path in folder_path.glob('**/__init__.py'):
        if path.parent == folder_path:
            # skip top level __init__.py
            continue

        rel_path = path.parent.relative_to(folder_path).as_posix()

        # get sub_dict for this folder
        path_all_dict = all_dict
        mod_path = path.parent.relative_to(folder_path).parts
        try:
            for part in mod_path:
                path_all_dict = path_all_dict[part]
        except KeyError:
            # there is nothing to import
            continue

        if '*' in skip_children.get(rel_path, []):
            path_all_dict = {}
            alls = []
            auto_content = ['', f'# {AUTO_GENERATED}', '', '__all__ = ()', '']
        else:
            path_all_dict = {
                key: val for key, val in path_all_dict.items() if key not in skip_children.get(rel_path, [])
            }
            alls = gather_all(list(mod_path), path_all_dict, skip_children)

            # check for non-unique imports
            if len(alls + list(path_all_dict)) != len(set(alls + list(path_all_dict))):
                non_unique[rel_path] = [k for k, v in Counter(alls + list(path_all_dict)).items() if v > 1]

            auto_content = (
                ['', f'# {AUTO_GENERATED}']
                + ['', '# fmt: off', '']
                + [f'from .{mod} import *' for mod in sorted(path_all_dict.keys())]
                + ['', '__all__ = (']
                + [f'{INDENT}{a!r},' for a in isort_alls(set(alls))]
                + [')', '', '# fmt: on', '']
            )

        start_content = []
        end_content = []
        in_docstring = in_end_content = False
        in_start_content = True
        for line in path.read_text(encoding='utf8').splitlines():
            if not in_start_content and line.startswith(f'# END {AUTO_GENERATED}'):
                in_end_content = True
            if in_end_content:
                end_content.append(line)
                continue
            # Only keep initial comments and docstring
            # TODO: Support __future__ imports, for which we will also
            # need to retain any empty lines since ruff formatter automatically
            # injects empty line between a module docstring and __future__ import
            if not (
                (line.startswith('#') and not line.startswith(f'# {AUTO_GENERATED}'))
                or line.startswith('"""')
                or in_docstring
            ):
                in_start_content = False
                continue
            if line.startswith('"""'):
                if (not in_docstring) and not (line.endswith('"""') and not line.strip() == '"""'):
                    in_docstring = True
                else:
                    in_docstring = False
            if in_start_content:
                start_content.append(line)

        new_content = start_content + auto_content + end_content

        path.write_text('\n'.join(new_content).rstrip() + '\n', encoding='utf8')

    return non_unique


if __name__ == '__main__':
    _folder = Path(__file__).parent.parent.joinpath('src', 'aiida')
    if not _folder.is_dir():
        sys.exit(f"Did not find aiida source in '{_folder}'")
    _skip = {
        # skipped since some arguments and options share the same name
        'cmdline/params': ['arguments', 'options'],
        # skipped since this is for testing only not general use
        'manage': ['tests'],
        # skipped since we don't want to expose the implementation at the top-level
        'storage': ['psql_dos', 'sqlite_zip', 'sqlite_temp'],
        'orm': ['implementation'],
        # skip all since the module requires extra requirements
        'restapi': ['*'],
    }
    _all_dict, _bad_all = parse_all(_folder)
    assert _all_dict, 'Did not find any aiida modules!'
    _non_unique = write_inits(_folder, _all_dict, _skip)
    if _bad_all:
        print('ERROR: found unparsable __all__:')
        for reason in _bad_all:
            print(f'{reason} in modules:', _bad_all[reason])
    if _non_unique:
        print('ERROR: non-unique imports:')
        pprint(_non_unique)
    if _bad_all or _non_unique:
        sys.exit(1)
