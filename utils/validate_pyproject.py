#!/usr/bin/env python
# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import click
import os
import sys
import toml
import json

FILENAME_TOML = 'pyproject.toml'
FILENAME_SETUP_JSON = 'setup.json'
SCRIPT_PATH = os.path.split(os.path.realpath(__file__))[0]
ROOT_DIR = os.path.join(SCRIPT_PATH, os.pardir)
FILEPATH_SETUP_JSON = os.path.join(ROOT_DIR, FILENAME_SETUP_JSON)
FILEPATH_TOML = os.path.join(ROOT_DIR, FILENAME_TOML)


def get_install_requires():
    """Return the list of installation requirements from the `setup.json`"""
    with open(FILEPATH_SETUP_JSON, 'r') as info:
        setup_json = json.load(info)

    return setup_json['install_requires']


@click.group()
def cli():
    pass


@click.command('version')
def validate_pyproject():
    """
    Ensure that the version of reentry in setup.json and pyproject.toml are identical
    """
    reentry_requirement = None
    for requirement in get_install_requires():
        if 'reentry' in requirement:
            reentry_requirement = requirement
            break

    if reentry_requirement is None:
        click.echo('Could not find the reentry requirement in {}'.format(FILEPATH_SETUP_JSON), err=True)
        sys.exit(1)

    try:
        with open(FILEPATH_TOML, 'r') as handle:
            toml_string = handle.read()
    except IOError as exception:
        click.echo('Could not read the required file: {}'.format(FILEPATH_TOML), err=True)
        sys.exit(1)

    try:
        parsed_toml = toml.loads(toml_string)
    except Exception as exception:
        click.echo('Could not parse {}: {}'.format(FILEPATH_TOML, exception), err=True)
        sys.exit(1)

    try:
        pyproject_toml_requires = parsed_toml['build-system']['requires']
    except KeyError as exception:
        click.echo('Could not retrieve the build-system requires list from {}'.format(FILEPATH_TOML), err=True)
        sys.exit(1)

    if reentry_requirement not in pyproject_toml_requires:
        click.echo('Reentry requirement from {} {} is not mirrored in {}'.format(
            FILEPATH_SETUP_JSON, reentry_requirement, FILEPATH_TOML), err=True)
        sys.exit(1)


@click.command('conda')
def update_environment_yml():
    """
    Updates environment.yml file for conda.
    """
    import yaml

    # fix incompatibilities between conda and pypi
    replacements = {
        'psycopg2-binary': 'psycopg2',
        'validate-email': 'validate_email',
    }
    sep = '%'  # use something forbidden in conda package names
    install_requires = get_install_requires()
    pkg_string = sep.join(install_requires)
    for (pypi_pkg_name, conda_pkg_name) in iter(replacements.items()):
        pkg_string = pkg_string.replace(pypi_pkg_name, conda_pkg_name)
    install_requires = pkg_string.split(sep)
    environment = dict(
        name='aiida',
        channels=['defaults', 'conda-forge', 'etetoolkit'],
        dependencies=install_requires,
    )

    environment_filename = 'environment.yml'
    file_path = os.path.join(ROOT_DIR, environment_filename)
    with open(file_path, 'w') as env_file:
        env_file.write('# Usage: conda env create -f environment.yml\n')
        yaml.dump(environment, env_file, explicit_start=True, default_flow_style=False)


cli.add_command(validate_pyproject)
cli.add_command(update_environment_yml)

if __name__ == '__main__':
    cli()  # pylint: disable=no-value-for-parameter
