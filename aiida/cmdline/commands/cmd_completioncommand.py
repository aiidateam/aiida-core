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
`verdi completioncommand` command, to return the string to insert
into the bash script to activate completion.
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import click
from aiida.cmdline.commands.cmd_verdi import verdi


@verdi.command('completioncommand')
def verdi_completioncommand():
    """
    Return the bash code to activate completion.

    :note: this command is mainly for back-compatibility.
        You should rather use:;

            eval "$(_VERDI_COMPLETE=source verdi)"
    """
    from click_completion import get_auto_shell, get_code
    click.echo(get_code(shell=get_auto_shell()))
