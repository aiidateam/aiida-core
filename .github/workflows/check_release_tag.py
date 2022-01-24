# -*- coding: utf-8 -*-
"""Check that the GitHub release tag matches the package version."""
import argparse
import ast
from pathlib import Path


def get_version_from_module(content: str) -> str:
    """Get the __version__ value from a module."""
    # adapted from setuptools/config.py
    try:
        module = ast.parse(content)
    except SyntaxError as exc:
        raise IOError(f'Unable to parse module: {exc}')
    try:
        return next(
            ast.literal_eval(statement.value) for statement in module.body if isinstance(statement, ast.Assign)
            for target in statement.targets if isinstance(target, ast.Name) and target.id == '__version__'
        )
    except StopIteration:
        raise IOError('Unable to find __version__ in module')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('GITHUB_REF', help='The GITHUB_REF environmental variable')
    args = parser.parse_args()
    assert args.GITHUB_REF.startswith('refs/tags/v'), f'GITHUB_REF should start with "refs/tags/v": {args.GITHUB_REF}'
    tag_version = args.GITHUB_REF[11:]
    pypi_version = get_version_from_module(Path('aiida/__init__.py').read_text(encoding='utf-8'))
    assert tag_version == pypi_version, f'The tag version {tag_version} != {pypi_version} specified in `pyproject.toml`'
