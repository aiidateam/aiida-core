# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The main `verdi` click group."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import click

from aiida.cmdline.params import options
from aiida.common.extendeddicts import AttributeDict


@click.group()
@options.PROFILE()
@click.option('--version', is_flag=True, default=False, help='Print the version of AiiDA that is currently installed.')
@click.pass_context
def verdi(ctx, profile, version):
    """The command line interface of AiiDA."""
    import sys
    import aiida
    from aiida.backends import settings
    from aiida.cmdline.utils import echo

    if version:
        echo.echo('AiiDA version {}'.format(aiida.__version__))
        sys.exit(0)

    if ctx.obj is None:
        ctx.obj = AttributeDict()

    if profile:
        settings.AIIDADB_PROFILE = profile.name
        ctx.obj.profile = profile

    ctx.help_option_names = ['-h', '--help']
