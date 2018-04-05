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
"""
Whenever the requirements in ../setup_requirements.py are updated,
run also this script to update the requirements for Read the Docs.
"""
import sys
import os
import click


@click.command()
@click.option('--pre-commit', is_flag=True)
def update_req_for_rtd(pre_commit):
    """Update the separate requirements file for Read the Docs"""
    docs_dir = os.path.abspath(os.path.dirname(__file__))
    sys.path.append(os.path.join(docs_dir, os.pardir))

    import setup_requirements

    reqs = set(setup_requirements.extras_require['docs'] +
               setup_requirements.extras_require['rest'] +
               setup_requirements.extras_require['testing'] +
               setup_requirements.extras_require[':python_version < "3"'] +
               # To avoid that it requires also the postgres libraries
               [
                   p for p in setup_requirements.install_requires
                   if not p.startswith('psycopg2')
               ])
    reqs_str = "\n".join(sorted(reqs))

    basename = 'requirements_for_rtd.txt'

    # pylint: disable=bad-continuation
    with open(os.path.join(docs_dir, basename), 'w') as reqs_file:
        reqs_file.write(reqs_str)

    click.echo("File '{}' written.".format(basename))

    if pre_commit:
        msg = 'Some requirements for Read the Docs have changed, {}'
        local_help = 'please add the changes and commit again'
        travis_help = 'please run aiida/docs/update_req_for_rtd.py locally and commit the changes it makes'
        help_msg = msg.format(
            travis_help if os.environ.get('TRAVIS') else local_help)
        click.echo(help_msg, err=True)


if __name__ == '__main__':
    update_req_for_rtd()  # pylint: disable=no-value-for-parameter
