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
from os import path
import sys
import toml
import json

@click.command()
def validate_pyproject():
    """
    Ensure that the version of reentry in setup.json and pyproject.toml are identical
    """
    filename_pyproject = 'pyproject.toml'
    filename_requirements = 'setup.json'

    this_path = path.split(path.realpath(__file__))[0]
    root_dir = path.join(this_path, os.pardir)
    toml_file = path.join(root_dir, filename_pyproject)

    reentry_requirement = None
    with open(path.join(root_dir, 'setup.json'), 'r') as info:
        setup_json = json.load(info)

    for requirement in setup_json['install_requires']:
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


if __name__ == '__main__':
    validate_pyproject()  # pylint: disable=no-value-for-parameter
