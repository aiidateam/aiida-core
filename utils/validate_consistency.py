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
""" Validate consistency of versions and dependencies.

Validates consistency of setup.json and

 * environment.yml
 * version in aiida/__init__.py
 * reentry dependency in pyproject.toml

"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import sys
import json
from collections import OrderedDict
import toml
import click

FILENAME_TOML = 'pyproject.toml'
FILENAME_SETUP_JSON = 'setup.json'
SCRIPT_PATH = os.path.split(os.path.realpath(__file__))[0]
ROOT_DIR = os.path.join(SCRIPT_PATH, os.pardir)
FILEPATH_SETUP_JSON = os.path.join(ROOT_DIR, FILENAME_SETUP_JSON)
FILEPATH_TOML = os.path.join(ROOT_DIR, FILENAME_TOML)


def get_setup_json():
    """Return the `setup.json` as a python dictionary """
    with open(FILEPATH_SETUP_JSON, 'r') as fil:
        setup_json = json.load(fil, object_pairs_hook=OrderedDict)

    return setup_json


@click.group()
def cli():
    pass


@click.command('version')
def validate_version():
    """Check that version numbers match.

    Check version number in setup.json and aiida_core/__init__.py and make sure
    they match.
    """
    # Get version from python package
    sys.path.insert(0, ROOT_DIR)
    import aiida  # pylint: disable=wrong-import-position
    version = aiida.__version__

    setup_content = get_setup_json()
    if version != setup_content['version']:
        print("Version number mismatch detected:")
        print("Version number in '{}': {}".format(FILENAME_SETUP_JSON, setup_content['version']))
        print("Version number in '{}/__init__.py': {}".format('aiida', version))
        print("Updating version in '{}' to: {}".format(FILENAME_SETUP_JSON, version))

        setup_content['version'] = version
        with open(FILEPATH_SETUP_JSON, 'w') as fil:
            # Write with indentation of two spaces and explicitly define separators to not have spaces at end of lines
            json.dump(setup_content, fil, indent=2, separators=(',', ': '))

        sys.exit(1)


@click.command('toml')
def validate_pyproject():
    """
    Ensure that the version of reentry in setup.json and pyproject.toml are identical
    """
    reentry_requirement = None
    for requirement in get_setup_json()['install_requires']:
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
    except Exception as exception:  # pylint: disable=broad-except
        click.echo('Could not parse {}: {}'.format(FILEPATH_TOML, exception), err=True)
        sys.exit(1)

    try:
        pyproject_toml_requires = parsed_toml['build-system']['requires']
    except KeyError as exception:
        click.echo('Could not retrieve the build-system requires list from {}'.format(FILEPATH_TOML), err=True)
        sys.exit(1)

    if reentry_requirement not in pyproject_toml_requires:
        click.echo(
            'Reentry requirement from {} {} is not mirrored in {}'.format(FILEPATH_SETUP_JSON, reentry_requirement,
                                                                          FILEPATH_TOML),
            err=True)
        sys.exit(1)


@click.command('conda')
def update_environment_yml():
    """
    Updates environment.yml file for conda.
    """
    import yaml
    import re

    # needed for ordered dict, see
    # https://stackoverflow.com/a/52621703
    yaml.add_representer(
        OrderedDict,
        lambda self, data: yaml.representer.SafeRepresenter.represent_dict(self, data.items()),
        Dumper=yaml.SafeDumper)

    # fix incompatibilities between conda and pypi
    replacements = {
        'psycopg2-binary': 'psycopg2',
    }
    install_requires = get_setup_json()['install_requires']

    conda_requires = []
    for req in install_requires:
        # skip packages required for specific python versions
        # (environment.yml aims at the latest python version)
        if req.find("python_version") != -1:
            continue

        for (regex, replacement) in iter(replacements.items()):
            conda_requires.append(re.sub(regex, replacement, req))

    environment = OrderedDict([
        ('name', 'aiida'),
        ('channels', ['defaults', 'conda-forge', 'etetoolkit']),
        ('dependencies', conda_requires),
    ])

    environment_filename = 'environment.yml'
    file_path = os.path.join(ROOT_DIR, environment_filename)
    with open(file_path, 'w') as env_file:
        env_file.write('# Usage: conda env create -f environment.yml python=3.6\n')
        yaml.safe_dump(
            environment, env_file, explicit_start=True, default_flow_style=False, encoding='utf-8', allow_unicode=True)


cli.add_command(validate_version)
cli.add_command(validate_pyproject)
cli.add_command(update_environment_yml)

if __name__ == '__main__':
    cli()  # pylint: disable=no-value-for-parameter
