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

import difflib
import click

from aiida.cmdline.params import options, types


class MostSimilarCommandGroup(click.Group):
    """
    Overloads the get_command to display a list of possible command
    candidates if the command could not be found with an exact match.
    """

    def get_command(self, ctx, cmd_name):
        """
        Override the default click.Group get_command with one giving the user
        a selection of possible commands if the exact command name could not be found.
        """
        cmd = click.Group.get_command(self, ctx, cmd_name)

        # return the exact match
        if cmd is not None:
            return cmd

        # we might get better results with the Levenshtein distance
        # or more advanced methods implemented in FuzzyWuzzy or similar libs,
        # but this is an easy win for now
        matches = difflib.get_close_matches(cmd_name, self.list_commands(ctx), cutoff=0.5)

        if not matches:
            # single letters are sometimes not matched, try with a simple startswith
            matches = [c for c in sorted(self.list_commands(ctx)) if c.startswith(cmd_name)][:3]

        if matches:
            ctx.fail(
                "'{cmd}' is not a verdi command.\n\n"
                'The most similar commands are: \n'
                '{matches}'.format(cmd=cmd_name, matches='\n'.join('\t{}'.format(m) for m in sorted(matches)))
            )
        else:
            ctx.fail("'{cmd}' is not a verdi command.\n\nNo similar commands found.".format(cmd=cmd_name))

        return None


@click.command(cls=MostSimilarCommandGroup, context_settings={'help_option_names': ['-h', '--help']})
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
