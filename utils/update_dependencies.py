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
"""Utility CLI to update dependency version requirements of the `setup.json`."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import copy
import os
import click

from validate_consistency import get_setup_json, write_setup_json

FILENAME_SETUP_JSON = 'setup.json'
SCRIPT_PATH = os.path.split(os.path.realpath(__file__))[0]
ROOT_DIR = os.path.join(SCRIPT_PATH, os.pardir)
FILEPATH_SETUP_JSON = os.path.join(ROOT_DIR, FILENAME_SETUP_JSON)
DEFAULT_EXCLUDE_LIST = ['django', 'circus', 'numpy', 'pymatgen', 'ase', 'monty', 'pyyaml']


@click.group()
def cli():
    """Utility to update dependency requirements for `aiida-core`.

    Since `aiida-core` fixes the versions of almost all of its dependencies, once in a while these need to be updated.
    This is a manual process, but this CLI attempts to simplify it somewhat. The idea is to remote all explicit version
    restrictions from the `setup.json`, except for those packages where it is known that a upper limit is necessary.
    This is accomplished by the command:

        python update_dependencies.py unrestrict

    The command will update the `setup.json` to remove all explicit limits, except for those packages specified by the
    `--exclude` option. After this step, install `aiida-core` through pip with the `[all]` flag to install all optional
    extra requirements as well. Since there are no explicit version requirements anymore, pip should install the latest
    available version for each dependency.

    Now run the unit test suite and reinstate dependency version requirements on packages that break the tests. Note
    that as long as we support python 2, this will have to be done for both python versions in separate virtual
    environments. Since the packages with special qualifiers relating to the python version are not handled by this CLI
    anyway, however, it often suffices to perform this method for one python version and then let the tests on Travis
    verify that it works for all versions. Once all the tests complete successfully, run the following command:

        pip freeze > requirements.txt

    This will now capture the exact versions of the packages installed in the virtual environment. Since the tests run
    for this setup, we can now set those versions as the new requirements in the `setup.json`. Note that this is why a
    clean virtual environment should be used for this entire procedure. Now execute the command:

        python update_dependencies.py update requirements.txt

    This will now update the `setup.json` to reinstate the exact version requirements for all dependencies. Commit the
    changes to `setup.json` and make a pull request.
    """


@cli.command('unrestrict')
@click.option('--exclude', multiple=True, help='List of package names to exclude from updating.')
def unrestrict_requirements(exclude):
    """Remove all explicit dependency version restrictions from `setup.json`.

    Warning, this currently only works for dependency requirements that use the `==` operator. Statements with different
    operators, additional filters after a semicolon, or with extra requirements (using `[]`) are not supported. The
    limits for these statements will have to be updated manually.
    """
    setup = get_setup_json()
    clone = copy.deepcopy(setup)
    clone['install_requires'] = []

    if exclude:
        exclude = list(exclude).extend(DEFAULT_EXCLUDE_LIST)
    else:
        exclude = DEFAULT_EXCLUDE_LIST

    for requirement in setup['install_requires']:
        if requirement in exclude or ';' in requirement or '==' not in requirement:
            clone['install_requires'].append(requirement)
        else:
            package = requirement.split('==')[0]
            clone['install_requires'].append(package)

    for extra, requirements in setup['extras_require'].items():
        clone['extras_require'][extra] = []

        for requirement in requirements:
            if requirement in exclude or ';' in requirement or '==' not in requirement:
                clone['extras_require'][extra].append(requirement)
            else:
                package = requirement.split('==')[0]
                clone['extras_require'][extra].append(package)

    write_setup_json(clone)


@cli.command('update')
@click.argument('requirements', type=click.File(mode='r'))
def update_requirements(requirements):
    """Apply version restrictions from REQUIREMENTS.

    The REQUIREMENTS file should contain the output of `pip freeze`.
    """
    setup = get_setup_json()

    package_versions = []

    for requirement in requirements.readlines():
        try:
            package, version = requirement.strip().split('==')
            package_versions.append((package, version))
        except ValueError:
            continue

    requirements = set()

    for requirement in setup['install_requires']:
        for package, version in package_versions:
            if requirement.lower() == package.lower():
                requirements.add('{}=={}'.format(package.lower(), version))
                break
        else:
            requirements.add(requirement)

    setup['install_requires'] = sorted(requirements)

    for extra, extra_requirements in setup['extras_require'].items():
        requirements = set()

        for requirement in extra_requirements:
            for package, version in package_versions:
                if requirement.lower() == package.lower():
                    requirements.add('{}=={}'.format(package.lower(), version))
                    break
            else:
                requirements.add(requirement)

        setup['extras_require'][extra] = sorted(requirements)

    write_setup_json(setup)


if __name__ == '__main__':
    cli()  # pylint: disable=no-value-for-parameter
