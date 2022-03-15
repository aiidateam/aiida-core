#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=simplifiable-if-statement,too-many-branches
"""Pre-commit hook to add ``__all__`` imports to ``__init__`` files."""
import ast
from collections import Counter
from pathlib import Path
from pprint import pprint
import sys
from typing import Dict, List, Optional, Tuple


def parse_all(folder_path: str) -> Tuple[dict, dict]:
    """Walk through all files in folder, and parse the ``__all__`` variable.

    :return: (all dict, dict of unparsable)
    """
    folder_path = Path(folder_path)
    all_dict = {}
    bad_all = {}

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

        if all_token is None:
            bad_all.setdefault('missing', []).append(str(path.relative_to(folder_path)))
            continue

        if not isinstance(all_token.value, (ast.List, ast.Tuple)):
            bad_all.setdefault('value not list/tuple', []).append(str(path.relative_to(folder_path)))
            continue

        if not all(isinstance(el, ast.Str) for el in all_token.value.elts):
            bad_all.setdefault('child not strings', []).append(str(path.relative_to(folder_path)))
            continue

        names = [n.s for n in all_token.value.elts]
        if not names:
            continue

        path_dict = all_dict
        for part in path.parent.relative_to(folder_path).parts:
            path_dict = path_dict.setdefault(part, {})
        path_dict.setdefault(path.name[:-3], {})['__all__'] = names

    return all_dict, bad_all


def gather_all(cur_path: List[str],
               cur_dict: dict,
               skip_children: dict,
               all_list: Optional[List[str]] = None) -> List[str]:
    """Recursively gather __all__ names."""
    all_list = [] if all_list is None else all_list
    for key, val in cur_dict.items():
        if key == '__all__':
            all_list.extend(val)
        elif key not in skip_children.get('/'.join(cur_path), []):
            gather_all(cur_path + [key], val, skip_children, all_list)
    return all_list


def write_inits(folder_path: str, all_dict: dict, skip_children: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Write __init__.py files for all subfolders.

    :return: folders with non-unique imports
    """
    folder_path = Path(folder_path)
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
            auto_content = ['', '# AUTO-GENERATED', '', '__all__ = ()', '']
        else:
            path_all_dict = {
                key: val for key, val in path_all_dict.items() if key not in skip_children.get(rel_path, [])
            }
            alls = gather_all(list(mod_path), path_all_dict, skip_children)

            # check for non-unique imports
            if len(alls + list(path_all_dict)) != len(set(alls + list(path_all_dict))):
                non_unique[rel_path] = [k for k, v in Counter(alls + list(path_all_dict)).items() if v > 1]

            auto_content = (['', '# AUTO-GENERATED'] +
                            ['', '# yapf: disable', '# pylint: disable=wildcard-import', ''] +
                            [f'from .{mod} import *' for mod in sorted(path_all_dict.keys())] + ['', '__all__ = ('] +
                            [f'    {a!r},' for a in sorted(set(alls))] + [')', '', '# yapf: enable', ''])

        start_content = []
        end_content = []
        in_docstring = in_end_content = False
        in_start_content = True
        for line in path.read_text(encoding='utf8').splitlines():
            if not in_start_content and line.startswith('# END AUTO-GENERATED'):
                in_end_content = True
            if in_end_content:
                end_content.append(line)
                continue
            # only use initial comments and docstring
            if not (line.startswith('#') or line.startswith('"""') or in_docstring):
                in_start_content = False
                continue
            if line.startswith('"""'):
                if (not in_docstring) and not (line.endswith('"""') and not line.strip() == '"""'):
                    in_docstring = True
                else:
                    in_docstring = False
            if in_start_content and not line.startswith('# pylint'):
                start_content.append(line)

        new_content = start_content + auto_content + end_content

        path.write_text('\n'.join(new_content).rstrip() + '\n', encoding='utf8')

    return non_unique


if __name__ == '__main__':
    _folder = Path(__file__).parent.parent.joinpath('aiida')
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
        # keep at aiida.tools.archive level
        'tools': ['archive'],
    }
    _all_dict, _bad_all = parse_all(_folder)
    _non_unique = write_inits(_folder, _all_dict, _skip)
    _bad_all.pop('missing', '')  # allow missing __all__
    if _bad_all:
        print('unparsable __all__:')
        pprint(_bad_all)
    if _non_unique:
        print('non-unique imports:')
        pprint(_non_unique)
    if _bad_all or _non_unique:
        sys.exit(1)
