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
import click
import os
import sys
import toml

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(dir_path, os.pardir))
import setup_requirements


@click.group()
def cli():
    pass

@click.command('version')
def validate_pyproject():
    """
    Ensure that the version of reentry in setup_requirements.py and pyproject.toml are identical
    """
    filename_pyproject = 'pyproject.toml'
    filename_requirements = 'setup_requirements.py'

    toml_file = os.path.join(dir_path, os.pardir, filename_pyproject)

    reentry_requirement = None

    for requirement in setup_requirements.install_requires:
        if 'reentry' in requirement:
            reentry_requirement = requirement
            break

    if reentry_requirement is None:
        click.echo('Could not find the reentry requirement in {}'.format(filename_requirements), err=True)
        sys.exit(1)

    try:
        with open(toml_file, 'r') as handle:
            toml_string = handle.read()
    except IOError as exception:
        click.echo('Could not read the required file: {}'.format(toml_file), err=True)
        sys.exit(1)

    try:
        parsed_toml = toml.loads(toml_string)
    except Exception as exception:
        click.echo('Could not parse {}: {}'.format(toml_file, exception), err=True)
        sys.exit(1)

    try:
        pyproject_toml_requires = parsed_toml['build-system']['requires']
    except KeyError as exception:
        click.echo('Could not retrieve the build-system requires list from {}'.format(toml_file), err=True)
        sys.exit(1)

    if reentry_requirement not in pyproject_toml_requires:
        click.echo('Reentry requirement from {} {} is not mirrored in {}'.format(
            filename_requirements, reentry_requirement, toml_file), err=True)
        sys.exit(1)


@click.command('conda')
def update_environment_yml():
    """
    Updates environment.yml file for conda.
    """
    from setup_requirements import install_requires
    import yaml

    # fix incompatibilities between conda and pypi
    replacements = {
        'psycopg2-binary' : 'psycopg2',
        'validate-email' : 'validate_email',
    }
    sep = '%'  # use something forbidden in conda package names
    pkg_string = sep.join(install_requires)
    for (pypi_pkg_name, conda_pkg_name) in iter(replacements.items()):
        pkg_string = pkg_string.replace(pypi_pkg_name, conda_pkg_name)
    install_requires = pkg_string.split(sep)
    environment = dict(
        name = 'aiida',
        channels = ['anaconda', 'conda-forge', 'etetoolkit'],
        dependencies = install_requires,
    )

    environment_filename = 'environment.yml'
    file_path = os.path.join(dir_path, os.pardir, environment_filename)
    with open(file_path, 'w') as env_file:
        env_file.write('# Usage: conda env create -f environment.yml\n')
        yaml.dump(environment, env_file, explicit_start=True, 
                  default_flow_style=False)

cli.add_command(validate_pyproject)
cli.add_command(update_environment_yml)

if __name__ == '__main__':
    cli()  # pylint: disable=no-value-for-parameter
