#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utility CLI to manage dependencies for aiida-core."""

import sys
import re
import json
import subprocess
from pathlib import Path
from collections import OrderedDict
from pkg_resources import Requirement, parse_requirements
from packaging.utils import canonicalize_name

import click
import yaml
import toml

ROOT = Path(__file__).resolve().parent.parent  # repository root

SETUPTOOLS_CONDA_MAPPINGS = {
    'psycopg2-binary': 'psycopg2',
    'graphviz': 'python-graphviz',
}

CONDA_IGNORE = ['pyblake2', r'.*python_version == \"3\.5\"']


class DependencySpecificationError(click.ClickException):
    """Indicates an issue in a dependency specification."""


def _load_setup_cfg():
    """Load the setup configuration from the 'setup.json' file."""
    try:
        with open(ROOT / 'setup.json') as setup_json_file:
            return json.load(setup_json_file)
    except json.decoder.JSONDecodeError as error:  # pylint: disable=no-member
        raise DependencySpecificationError("Error while parsing 'setup.json' file: {}".format(error))
    except FileNotFoundError:
        raise DependencySpecificationError("The 'setup.json' file is missing!")


def _load_environment_yml():
    """Load the conda environment specification from the 'environment.yml' file."""
    try:
        with open(ROOT / 'environment.yml') as file:
            return yaml.load(file, Loader=yaml.SafeLoader)
    except yaml.error.YAMLError as error:
        raise DependencySpecificationError("Error while parsing 'environment.yml':\n{}".format(error))
    except FileNotFoundError as error:
        raise DependencySpecificationError(str(error))


def _setuptools_to_conda(req):
    """Map package names from setuptools to conda where necessary.

    In case that the same underlying dependency is listed under different names
    on PyPI and conda-forge.
    """

    for pattern, replacement in SETUPTOOLS_CONDA_MAPPINGS.items():
        if re.match(pattern, str(req)):
            req = Requirement.parse(re.sub(pattern, replacement, str(req)))
            break

    # markers are not supported by conda
    req.marker = None

    # We need to parse the modified required again, to ensure consistency.
    return Requirement.parse(str(req))


class _Entry:
    """Helper class to check whether a given distribution fulfills a requirement."""

    def __init__(self, requirement):
        self._req = requirement

    def fulfills(self, requirement):
        """Returns True if this entry fullfills the requirement."""

        return canonicalize_name(self._req.name) == canonicalize_name(requirement.name) \
            and self._req.specs[0][1] in requirement.specifier


def _parse_working_set(entries):
    for req in parse_requirements(entries):
        yield _Entry(req)


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
        Dumper=yaml.SafeDumper
    )

    # Read the requirements from 'setup.json'
    setup_cfg = _load_setup_cfg()
    install_requirements = [Requirement.parse(r) for r in setup_cfg['install_requires']]

    # python version cannot be overriden from outside environment.yml
    # (even if it is not specified at all in environment.yml)
    # https://github.com/conda/conda/issues/9506
    conda_requires = ['python~=3.7']
    for req in install_requirements:
        if req.name == 'python' or any(re.match(ignore, str(req)) for ignore in CONDA_IGNORE):
            continue
        conda_requires.append(str(_setuptools_to_conda(req)))

    environment = OrderedDict([
        ('name', 'aiida'),
        ('channels', ['conda-forge', 'defaults']),
        ('dependencies', conda_requires),
    ])

    with open(ROOT / 'environment.yml', 'w') as env_file:
        env_file.write('# Usage: conda env create -n myenvname -f environment.yml\n')
        yaml.safe_dump(
            environment, env_file, explicit_start=True, default_flow_style=False, encoding='utf-8', allow_unicode=True
        )


@cli.command('generate-rtd-reqs')
def generate_requirements_for_rtd():
    """Generate 'docs/requirements_for_rtd.txt' file."""

    # Read the requirements from 'setup.json'
    setup_cfg = _load_setup_cfg()
    install_requirements = {Requirement.parse(r) for r in setup_cfg['install_requires']}
    for key in ('testing', 'docs', 'rest', 'atomic_tools'):
        install_requirements.update({Requirement.parse(r) for r in setup_cfg['extras_require'][key]})

    # pylint: disable=bad-continuation
    with open(ROOT / Path('docs', 'requirements_for_rtd.txt'), 'w') as reqs_file:
        reqs_file.write('\n'.join(sorted(map(str, install_requirements))))


@cli.command()
def generate_pyproject_toml():
    """Generate 'pyproject.toml' file."""

    # Read the requirements from 'setup.json'
    setup_cfg = _load_setup_cfg()
    install_requirements = [Requirement.parse(r) for r in setup_cfg['install_requires']]

    for requirement in install_requirements:
        if requirement.name == 'reentry':
            reentry_requirement = requirement
            break
    else:
        raise DependencySpecificationError("Failed to find reentry requirement in 'setup.json'.")

    pyproject = {
        'build-system': {
            'requires': ['setuptools>=40.8.0', 'wheel', str(reentry_requirement)],
            'build-backend': 'setuptools.build_meta:__legacy__',
        }
    }
    with open(ROOT / 'pyproject.toml', 'w') as file:
        toml.dump(pyproject, file)


@cli.command()
@click.pass_context
def generate_all(ctx):
    """Generate all dependent requirement files."""
    ctx.invoke(generate_environment_yml)
    ctx.invoke(generate_requirements_for_rtd)
    ctx.invoke(generate_pyproject_toml)


@cli.command('validate-environment-yml', help="Validate 'environment.yml'.")
def validate_environment_yml():  # pylint: disable=too-many-branches
    """Validate that 'environment.yml' is consistent with 'setup.json'."""

    # Read the requirements from 'setup.json' and 'environment.yml'.
    setup_cfg = _load_setup_cfg()
    install_requirements = [Requirement.parse(r) for r in setup_cfg['install_requires']]
    python_requires = Requirement.parse('python' + setup_cfg['python_requires'])

    environment_yml = _load_environment_yml()
    try:
        assert environment_yml['name'] == 'aiida', "environment name should be 'aiida'."
        assert environment_yml['channels'] == [
            'conda-forge', 'defaults'
        ], "channels should be 'conda-forge', 'defaults'."
    except AssertionError as error:
        raise DependencySpecificationError("Error in 'environment.yml': {}".format(error))

    try:
        conda_dependencies = {Requirement.parse(d) for d in environment_yml['dependencies']}
    except TypeError as error:
        raise DependencySpecificationError("Error while parsing requirements from 'environment_yml': {}".format(error))

    # Attempt to find the specification of Python among the 'environment.yml' dependencies.
    for dependency in conda_dependencies:
        if dependency.name == 'python':  # Found the Python dependency specification
            conda_python_dependency = dependency
            conda_dependencies.remove(dependency)
            break
    else:  # Failed to find Python dependency specification
        raise DependencySpecificationError("Did not find specification of Python version in 'environment.yml'.")

    # The Python version specified in 'setup.json' should be listed as trove classifiers.
    for spec in conda_python_dependency.specifier:
        expected_classifier = 'Programming Language :: Python :: ' + spec.version
        if expected_classifier not in setup_cfg['classifiers']:
            raise DependencySpecificationError(
                "Trove classifier '{}' missing from 'setup.json'.".format(expected_classifier)
            )

        # The Python version should be specified as supported in 'setup.json'.
        if not any(spec.version >= other_spec.version for other_spec in python_requires.specifier):
            raise DependencySpecificationError(
                "Required Python version between 'setup.json' and 'environment.yml' not consistent."
            )

        break
    else:
        raise DependencySpecificationError("Missing specifier: '{}'.".format(conda_python_dependency))

    # Check that all requirements specified in the setup.json file are found in the
    # conda environment specification.
    for req in install_requirements:
        if any(re.match(ignore, str(req)) for ignore in CONDA_IGNORE):
            continue  # skip explicitly ignored packages

        try:
            conda_dependencies.remove(_setuptools_to_conda(req))
        except KeyError:
            raise DependencySpecificationError("Requirement '{}' not specified in 'environment.yml'.".format(req))

    # The only dependency left should be the one for Python itself, which is not part of
    # the install_requirements for setuptools.
    if conda_dependencies:
        raise DependencySpecificationError(
            "The 'environment.yml' file contains dependencies that are missing "
            "in 'setup.json':\n- {}".format('\n- '.join(map(str, conda_dependencies)))
        )

    click.secho('Conda dependency specification is consistent.', fg='green')


@cli.command('validate-rtd-reqs', help="Validate 'docs/requirements_for_rtd.txt'.")
def validate_requirements_for_rtd():
    """Validate that 'docs/requirements_for_rtd.txt' is consistent with 'setup.json'."""

    # Read the requirements from 'setup.json'
    setup_cfg = _load_setup_cfg()
    install_requirements = {Requirement.parse(r) for r in setup_cfg['install_requires']}
    for key in ('testing', 'docs', 'rest', 'atomic_tools'):
        install_requirements.update({Requirement.parse(r) for r in setup_cfg['extras_require'][key]})

    with open(ROOT / Path('docs', 'requirements_for_rtd.txt')) as reqs_file:
        reqs = {Requirement.parse(r) for r in reqs_file}

    if reqs != install_requirements:
        raise DependencySpecificationError("The requirements for RTD are inconsistent with 'setup.json'.")

    click.secho('RTD requirements specification is consistent.', fg='green')


@cli.command('validate-pyproject-toml', help="Validate 'pyproject.toml'.")
def validate_pyproject_toml():
    """Validate that 'pyproject.toml' is consistent with 'setup.json'."""

    # Read the requirements from 'setup.json'
    setup_cfg = _load_setup_cfg()
    install_requirements = [Requirement.parse(r) for r in setup_cfg['install_requires']]

    for requirement in install_requirements:
        if requirement.name == 'reentry':
            reentry_requirement = requirement
            break
    else:
        raise DependencySpecificationError("Failed to find reentry requirement in 'setup.json'.")

    try:
        with open(ROOT / 'pyproject.toml') as file:
            pyproject = toml.load(file)
            pyproject_requires = [Requirement.parse(r) for r in pyproject['build-system']['requires']]

        if reentry_requirement not in pyproject_requires:
            raise DependencySpecificationError(
                "Missing requirement '{}' in 'pyproject.toml'.".format(reentry_requirement)
            )

    except FileNotFoundError:
        raise DependencySpecificationError("The 'pyproject.toml' file is missing!")

    click.secho('Pyproject.toml dependency specification is consistent.', fg='green')


@cli.command('validate-all', help='Validate consistency of all requirements.')
@click.pass_context
def validate_all(ctx):
    """Validate consistency of all requirement specifications of the package.

    Validates that the specification of requirements/dependencies is consistent across
    the following files:

    - setup.py
    - setup.json
    - environment.yml
    - pyproject.toml
    - docs/requirements_for_rtd.txt
    """

    ctx.invoke(validate_environment_yml)
    ctx.invoke(validate_requirements_for_rtd)
    ctx.invoke(validate_pyproject_toml)


@cli.command()
@click.argument('extras', nargs=-1)
def check_requirements(extras):
    """Check the 'requirements/*.txt' files.

    Checks that the environments specified in the requirements files
    match all the dependencies specified in 'setup.json.

    The arguments allow to specify which 'extra' requirements to expect.
    Use 'DEFAULT' to select 'atomic_tools', 'docs', 'notebook', 'rest', and 'testing'.

    """

    if len(extras) == 1 and extras[0] == 'DEFAULT':
        extras = ['atomic_tools', 'docs', 'notebook', 'rest', 'testing']

    # Read the requirements from 'setup.json'
    setup_cfg = _load_setup_cfg()
    install_requires = setup_cfg['install_requires']
    for extra in extras:
        install_requires.extend(setup_cfg['extras_require'][extra])
    install_requires = set(parse_requirements(install_requires))

    for fn_req in (ROOT / 'requirements').iterdir():
        env = {'python_version': re.match(r'.*-py-(.*)\.txt', str(fn_req)).groups()[0]}
        required = {r for r in install_requires if r.marker is None or r.marker.evaluate(env)}

        with open(fn_req) as req_file:
            working_set = list(_parse_working_set(req_file))
            installed = {req for req in required for entry in working_set if entry.fulfills(req)}

        not_installed = required.difference(installed)
        if not_installed:  # switch to assignment expression after yapf supports 3.8
            raise DependencySpecificationError(
                f"Environment specified in '{fn_req.relative_to(ROOT)}' misses matches for:\n" +
                '\n'.join(' - ' + str(f) for f in not_installed)
            )

    click.secho("Requirements files appear to be in sync with specifications in 'setup.json'.", fg='green')


@cli.command()
@click.argument('extras', nargs=-1)
def pip_install_extras(extras):
    """Install extra requirements.

    For example:

        pip-install-extras docs

    This will install *only* the extra the requirements for docs, but without triggering
    the installation of the main installations requirements of the aiida-core package.
    """
    # Read the requirements from 'setup.json'
    setup_cfg = _load_setup_cfg()

    to_install = set()
    for key in extras:
        to_install.update(Requirement.parse(r) for r in setup_cfg['extras_require'][key])

    cmd = [sys.executable, '-m', 'pip', 'install'] + [str(r) for r in to_install]
    subprocess.run(cmd, check=True)


if __name__ == '__main__':
    cli()  # pylint: disable=no-value-for-parameter
