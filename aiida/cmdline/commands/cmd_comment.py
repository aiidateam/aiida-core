# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`verdi comment` command."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments, options
from aiida.cmdline.utils import decorators, echo, multi_line_input
from aiida.common import exceptions


@verdi.group('comment')
def verdi_comment():
    """Inspect, create and manage node comments."""


@verdi_comment.command()
@options.NODES()
@click.argument('content', type=click.STRING, required=False)
@decorators.with_dbenv()
def add(nodes, content):
    """Add a comment to one or multiple nodes."""
    if not content:
        content = multi_line_input.edit_comment()

    for node in nodes:
        node.add_comment(content)

    echo.echo_success('comment added to {} nodes'.format(len(nodes)))


@verdi_comment.command()
@click.argument('comment_id', type=int, metavar='COMMENT_ID')
@click.argument('content', type=click.STRING, required=False)
@decorators.with_dbenv()
def update(comment_id, content):
    """Update a comment."""
    from aiida.orm.comments import Comment

    try:
        comment = Comment.objects.get(comment_id)
    except (exceptions.NotExistent, exceptions.MultipleObjectsError):
        echo.echo_critical('comment<{}> not found'.format(comment_id))

    if content is None:
        content = multi_line_input.edit_comment(comment.content)

    comment.set_content(content)

    echo.echo_success('comment<{}> updated'.format(comment_id))


@verdi_comment.command()
@options.USER()
@arguments.NODES()
@decorators.with_dbenv()
def show(user, nodes):
    """Show the comments for one or multiple nodes."""
    for node in nodes:

        all_comments = node.get_comments()

        if user is not None:
            comments = [comment for comment in all_comments if comment.user.email == user.email]

            if not comments:
                valid_users = ', '.join(set(comment.user.email for comment in all_comments))
                echo.echo_warning('no comments found for user {}'.format(user))
                echo.echo_info('valid users found for Node<{}>: {}'.format(node.pk, valid_users))

        else:
            comments = all_comments

        for comment in comments:
            comment_msg = [
                '***********************************************************',
                'Comment<{}> for Node<{}> by {}'.format(comment.id, node.pk, comment.user.email),
                'Created on {}'.format(comment.ctime.strftime('%Y-%m-%d %H:%M')),
                'Last modified on {}'.format(comment.mtime.strftime('%Y-%m-%d %H:%M')),
                '\n{}\n'.format(comment.content),
            ]
            echo.echo('\n'.join(comment_msg))

        if not comments:
            echo.echo_info('no comments found')


@verdi_comment.command()
@options.FORCE()
@click.argument('comment', type=int, required=False, metavar='COMMENT_ID')
@decorators.with_dbenv()
def remove(force, comment):
    """Remove a comment."""
    from aiida.orm.comments import Comment

    if not force:
        click.confirm('Are you sure you want to remove comment<{}>'.format(comment), abort=True)

    try:
        Comment.objects.delete(comment)
    except exceptions.NotExistent as exception:
        echo.echo_critical('failed to remove comment<{}>: {}'.format(comment, exception))
    else:
        echo.echo_success('removed comment<{}>'.format(comment))
