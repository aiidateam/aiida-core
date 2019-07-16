# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The main `verdi` click group."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import click

from aiida.cmdline.params import options, types


@click.group(context_settings={'help_option_names': ['-h', '--help']})
@options.PROFILE(type=types.ProfileParamType(load_profile=True))
@click.version_option(None, '-v', '--version', message='AiiDA version %(version)s')
@click.pass_context
def verdi(ctx, profile):
    """The command line interface of AiiDA."""
    from aiida.common import extendeddicts
    from aiida.manage.configuration import get_config

    if ctx.obj is None:
        ctx.obj = extendeddicts.AttributeDict()

    ctx.obj.config = get_config()
    ctx.obj.profile = profile
