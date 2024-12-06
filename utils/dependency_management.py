#!/usr/bin/env python
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utility CLI to manage dependencies for aiida-core."""

import os
import re
import subprocess
import sys
from collections import OrderedDict, defaultdict
from pathlib import Path

import click
import requests
import tomli
import yaml
from packaging.requirements import Requirement
from packaging.version import parse

ROOT = Path(__file__).resolve().parent.parent  # repository root

SETUPTOOLS_CONDA_MAPPINGS = {
    'graphviz': 'python-graphviz',
    'docstring-parser': 'docstring_parser',
}

CONDA_IGNORE = []

GITHUB_ACTIONS = os.environ.get('GITHUB_ACTIONS') == 'true'


class DependencySpecificationError(click.ClickException):
    """Indicates an issue in a dependency specification."""


def _load_pyproject():
    """Load the setup configuration from the 'pyproject.toml' file."""
    try:
        with open(ROOT / 'pyproject.toml', 'rb') as handle:
            return tomli.load(handle)
    except tomli.TOMLDecodeError as error:
        raise DependencySpecificationError(f"Error while parsing 'pyproject.toml' file: {error}")
    except FileNotFoundError:
        raise DependencySpecificationError("The 'pyproject.toml' file is missing!")


def _load_environment_yml():
    """Load the conda environment specification from the 'environment.yml' file."""
    try:
        with open(ROOT / 'environment.yml', encoding='utf8') as file:
            return yaml.load(file, Loader=yaml.SafeLoader)
    except yaml.error.YAMLError as error:
        raise DependencySpecificationError(f"Error while parsing 'environment.yml':\n{error}")
    except FileNotFoundError as error:
        raise DependencySpecificationError(str(error))


def _setuptools_to_conda(req):
    """Map package names from setuptools to conda where necessary.

    In case that the same underlying dependency is listed under different names
    on PyPI and conda-forge.
    """
    for pattern, replacement in SETUPTOOLS_CONDA_MAPPINGS.items():
        if re.match(pattern, str(req)):
            req = Requirement(re.sub(pattern, replacement, str(req)))
            break

    # markers are not supported by conda
    req.marker = None

    # We need to parse the modified required again, to ensure consistency.
    return Requirement(str(req))


def _find_linenos_of_requirements_in_pyproject(requirements):
    """Determine the line numbers of requirements specified in 'pyproject.toml'.

    Returns a dict that maps a requirement, e.g., `numpy~=1.15.0` to the
    line numbers at which said requirement is defined within the 'pyproject.toml'
    file.
    """
    linenos = defaultdict(list)

    with open(ROOT / 'pyproject.toml', encoding='utf8') as setup_json_file:
        lines = list(setup_json_file)

    # Determine the lines that correspond to affected requirements in pyproject.toml.
    for requirement in requirements:
        for lineno, line in enumerate(lines):
            if str(requirement) in line:
                linenos[requirement].append(lineno)
    return linenos


def parse_requirements(requirements):
    """Parse requirements from a file or list of strings."""
    results = []
    for requirement in requirements:
        stripped = requirement.strip()
        if stripped and not stripped.startswith('#'):
            results.append(Requirement(stripped))
    return results


@click.group()
def cli():
    """Manage dependencies of the aiida-core package."""


@cli.command('generate-environment-yml')
def generate_environment_yml():
    """Generate 'environment.yml' file."""
    # needed for ordered dict, see https://stackoverflow.com/a/52621703
    yaml.add_representer(
        OrderedDict,
        lambda self, data: yaml.representer.SafeRepresenter.represent_dict(self, data.items()),
        Dumper=yaml.SafeDumper,
    )

    # Read the requirements from 'pyproject.toml'
    pyproject = _load_pyproject()
    install_requirements = [Requirement(r) for r in pyproject['project']['dependencies']]

    # python version cannot be overriden from outside environment.yml
    # (even if it is not specified at all in environment.yml)
    # https://github.com/conda/conda/issues/9506
    conda_requires = ['python~=3.9']
    for req in install_requirements:
        if req.name == 'python' or any(re.match(ignore, str(req)) for ignore in CONDA_IGNORE):
            continue
        conda_requires.append(str(_setuptools_to_conda(req)))

    environment = OrderedDict(
        [
            ('name', 'aiida'),
            ('channels', ['conda-forge', 'defaults']),
            ('dependencies', conda_requires),
        ]
    )

    with open(ROOT / 'environment.yml', 'w', encoding='utf8') as env_file:
        env_file.write('# Usage: conda env create -n myenvname -f environment.yml\n')
        yaml.safe_dump(
            environment, env_file, explicit_start=True, default_flow_style=False, encoding='utf-8', allow_unicode=True
        )


@cli.command('validate-environment-yml', help="Validate 'environment.yml'.")
def validate_environment_yml():
    """Validate that 'environment.yml' is consistent with 'pyproject.toml'."""
    # Read the requirements from 'pyproject.toml' and 'environment.yml'.
    pyproject = _load_pyproject()
    install_requirements = [Requirement(r) for r in pyproject['project']['dependencies']]
    python_requires = Requirement('python' + pyproject['project']['requires-python'])

    environment_yml = _load_environment_yml()
    try:
        assert environment_yml['name'] == 'aiida', "environment name should be 'aiida'."
        assert environment_yml['channels'] == [
            'conda-forge',
            'defaults',
        ], "channels should be 'conda-forge', 'defaults'."
    except AssertionError as error:
        raise DependencySpecificationError(f"Error in 'environment.yml': {error}")

    try:
        conda_dependencies = {Requirement(d) for d in environment_yml['dependencies']}
    except TypeError as error:
        raise DependencySpecificationError(f"Error while parsing requirements from 'environment_yml': {error}")

    # Attempt to find the specification of Python among the 'environment.yml' dependencies.
    for dependency in conda_dependencies:
        if dependency.name == 'python':  # Found the Python dependency specification
            conda_python_dependency = dependency
            conda_dependencies.remove(dependency)
            break
    else:  # Failed to find Python dependency specification
        raise DependencySpecificationError("Did not find specification of Python version in 'environment.yml'.")

    # The Python version specified in 'pyproject.toml' should be listed as trove classifiers.
    for spec in conda_python_dependency.specifier:
        expected_classifier = 'Programming Language :: Python :: ' + spec.version
        if expected_classifier not in pyproject['project']['classifiers']:
            raise DependencySpecificationError(
                f"Trove classifier '{expected_classifier}' missing from 'pyproject.toml'."
            )

        # The Python version should be specified as supported in 'pyproject.toml'.
        if not any(spec.version >= other_spec.version for other_spec in python_requires.specifier):
            raise DependencySpecificationError(
                f"Required Python version {spec.version} from 'environment.yaml' is not consistent with "
                + "required version in 'pyproject.toml'."
            )

        break
    else:
        raise DependencySpecificationError(f"Missing specifier: '{conda_python_dependency}'.")

    # Check that all requirements specified in the pyproject.toml file are found in the
    # conda environment specification.
    for req in install_requirements:
        if any(re.match(ignore, str(req)) for ignore in CONDA_IGNORE):
            continue  # skip explicitly ignored packages

        try:
            conda_dependencies.remove(_setuptools_to_conda(req))
        except KeyError:
            raise DependencySpecificationError(f"Requirement '{req}' not specified in 'environment.yml'.")

    # The only dependency left should be the one for Python itself, which is not part of
    # the install_requirements for setuptools.
    if conda_dependencies:
        raise DependencySpecificationError(
            "The 'environment.yml' file contains dependencies that are missing " "in 'pyproject.toml':\n- {}".format(
                '\n- '.join(map(str, conda_dependencies))
            )
        )

    click.secho('Conda dependency specification is consistent.', fg='green')


@cli.command()
@click.argument('extras', nargs=-1)
@click.option('--format', 'fmt', type=click.Choice(['pip', 'pipfile']), default='pip')
def show_requirements(extras, fmt):
    """Show the installation requirements.

    For example:

        show-requirements --format=pipfile all

    This will show all reqiurements including *all* extras in Pipfile format.
    """
    # Read the requirements from 'pyproject.toml''
    pyproject = _load_pyproject()

    if 'all' in extras:
        extras = list(pyproject['project']['optional-dependencies'])

    to_install = {Requirement(r) for r in pyproject['project']['dependencies']}
    for key in extras:
        to_install.update(Requirement(r) for r in pyproject['project']['optional-dependencies'][key])

    if fmt == 'pip':
        click.echo('\n'.join(sorted(map(str, to_install))))
    elif fmt == 'pipfile':
        click.echo('[packages]')
        for requirement in sorted(to_install, key=str):
            click.echo(f'{requirement.name} = "{requirement.specifier}"')


@cli.command()
@click.argument('extras', nargs=-1)
def pip_install_extras(extras):
    """Install extra requirements.

    For example:

        pip-install-extras docs

    This will install *only* the extra the requirements for docs, but without triggering
    the installation of the main installations requirements of the aiida-core package.
    """
    # Read the requirements from 'pyproject.toml''
    pyproject = _load_pyproject()

    to_install = set()
    for key in extras:
        to_install.update(Requirement(r) for r in pyproject['project']['optional-dependencies'][key])

    cmd = [sys.executable, '-m', 'pip', 'install'] + [str(r) for r in to_install]
    subprocess.run(cmd, check=True)


@cli.command()
@click.argument('extras', nargs=-1)
@click.option('--pre-releases', is_flag=True, help='Include pre-releases.')
def identify_outdated(extras, pre_releases):
    """Identify outdated dependencies.

    For example:

        identify-outdated all

    This command will analyze the current dependencies and compare them against
    the latest versions released on PyPI. It then lists all dependencies where
    the latest release is not compatible with the dependency specification.
    This function can thus be used to identify dependencies where the
    specification must be loosened.
    """
    # Read the requirements from 'pyproject.toml''
    pyproject = _load_pyproject()

    to_install = {Requirement(r) for r in pyproject['project']['dependencies']}
    for key in extras:
        to_install.update(Requirement(r) for r in pyproject['project']['optional-dependencies'][key])

    def get_package_data(name):
        req = requests.get(f'https://pypi.python.org/pypi/{name}/json', timeout=5)
        req.raise_for_status()
        return req.json()

    release_data = {requirement: get_package_data(requirement.name)['releases'] for requirement in to_install}
    for requirement, releases in release_data.items():
        releases_ = list(sorted(map(parse, releases)))
        latest_release = [r for r in releases_ if pre_releases or not r.is_prerelease][-1]

        if str(latest_release) not in requirement.specifier:
            print(requirement, latest_release)


if __name__ == '__main__':
    cli()
