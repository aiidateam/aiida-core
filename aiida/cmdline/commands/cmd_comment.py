# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi comment` command."""

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments, options
from aiida.cmdline.utils import decorators


@verdi.group('comment')
@decorators.deprecated_command("This command has been deprecated. Please use 'verdi node comment' instead.")
def verdi_comment():
    """Inspect, create and manage node comments."""


@verdi_comment.command()
@decorators.deprecated_command("This command has been deprecated. Please use 'verdi node comment add' instead.")
@options.NODES(required=True)
@click.argument('content', type=click.STRING, required=False)
@click.pass_context
@decorators.with_dbenv()
def add(ctx, nodes, content):  # pylint: disable=too-many-arguments, unused-argument
    """Add a comment to one or more nodes."""
    from aiida.cmdline.commands.cmd_node import comment_add
    ctx.forward(comment_add)


@verdi_comment.command()
@decorators.deprecated_command("This command has been deprecated. Please use 'verdi node comment update' instead.")
@click.argument('comment_id', type=int, metavar='COMMENT_ID')
@click.argument('content', type=click.STRING, required=False)
@click.pass_context
@decorators.with_dbenv()
def update(ctx, comment_id, content):  # pylint: disable=too-many-arguments, unused-argument
    """Update a comment of a node."""
    from aiida.cmdline.commands.cmd_node import comment_update
    ctx.forward(comment_update)


@verdi_comment.command()
@decorators.deprecated_command("This command has been deprecated. Please use 'verdi node comment show' instead.")
@options.USER()
@arguments.NODES()
@click.pass_context
@decorators.with_dbenv()
def show(ctx, user, nodes):  # pylint: disable=too-many-arguments, unused-argument
    """Show the comments of one or multiple nodes."""
    from aiida.cmdline.commands.cmd_node import comment_show
    ctx.forward(comment_show)


@verdi_comment.command()
@decorators.deprecated_command("This command has been deprecated. Please use 'verdi node comment remove' instead.")
@options.FORCE()
@click.argument('comment', type=int, required=True, metavar='COMMENT_ID')
@click.pass_context
@decorators.with_dbenv()
def remove(ctx, force, comment):  # pylint: disable=too-many-arguments, unused-argument
    """Remove a comment of a node."""
    from aiida.cmdline.commands.cmd_node import comment_remove
    ctx.forward(comment_remove)
