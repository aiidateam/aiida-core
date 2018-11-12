# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=superfluous-parens
"""
This allows to manage comments from command line.
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import click

from aiida.cmdline.commands.cmd_verdi import verdi
from aiida.cmdline.params import arguments, options
from aiida.cmdline.utils import decorators, echo, multi_line_input


@verdi.group('comment')
def verdi_comment():
    """Inspect, create and manage comments."""
    pass


@verdi_comment.command()
@click.option('--comment', '-c', type=str, required=False)
@arguments.NODES(required=True)
@decorators.with_dbenv()
def add(comment, nodes):
    """
    Add comment to one or more nodes in the database
    """
    from aiida import orm

    user = orm.User.objects.get_default()

    if not comment:
        comment = multi_line_input.edit_comment()

    for node in nodes:
        node.add_comment(comment, user)

    echo.echo_info("Comment added to node(s) '{}'".format(", ".join([str(node.pk) for node in nodes])))


@verdi_comment.command()
@options.USER()
@arguments.NODES()
@decorators.with_dbenv()
def show(user, nodes):
    """
    Show the comments of (a) node(s) in the database
    """
    for node in nodes:
        all_comments = node.get_comments()

        if user is not None:
            to_print = [i for i in all_comments if i['user__email'] == user.email]
            if not to_print:
                valid_users = ", ".join(set(["'" + i['user__email'] + "'" for i in all_comments]))
                echo.echo_info("Nothing found for user '{}'.\n"
                               "Valid users found for Node {} are: {}.".format(user, node.pk, valid_users))

        else:
            to_print = all_comments

        for i in to_print:
            comment_msg = [
                "***********************************************************", "Comment of '{}' on {}".format(
                    i['user__email'], i['ctime'].strftime("%Y-%m-%d %H:%M")), "PK {} ID {}. Last modified on {}".format(
                        node.pk, i['pk'], i['mtime'].strftime("%Y-%m-%d %H:%M")), "", "{}".format(i['content']), ""
            ]
            echo.echo_info("\n".join(comment_msg))

        # If there is nothing to print, print a message
        if not to_print:
            echo.echo_info("No comments found.")


@verdi_comment.command()
@click.option(
    '--all',
    '-a',
    'remove_all',
    default=False,
    is_flag=True,
    help='If used, deletes all the comments of the active user attached to the node')
@options.FORCE()
@arguments.NODE()
@click.argument('comment_id', type=int, required=False, metavar='COMMENT_ID')
@decorators.with_dbenv()
def remove(remove_all, force, node, comment_id):
    """
    Remove comment(s) of a node. The user can only remove their own comments.

    pk = The pk (an integer) of the node

    id = #ID of the comment to be removed from node #PK
    """
    # Note: in fact, the user can still manually delete any comment
    from aiida import orm

    user = orm.User.objects.get_default()

    if comment_id is None and not remove_all:
        echo.echo_error("One argument between -a and ID must be provided")
        return 101

    if comment_id is not None and remove_all:
        echo.echo_error("Cannot use -a together with a comment id")
        return 102

    if remove_all:
        comment_id = None

    if not force:
        if remove_all:
            click.confirm("Delete all comments of user {} on node <{}>? ".format(user, node.pk), abort=True)
        else:
            click.confirm("Delete comment? ", abort=True)

    comments = node.get_comment_obj(comment_id=comment_id, user=user)
    for comment in comments:
        comment.delete()
    echo.echo_info("Deleted {} comments.".format(len(comments)))

    return 0


@verdi_comment.command()
@click.option('--comment', '-c', type=str, required=False)
@arguments.NODE()
@click.argument('comment_id', type=int, metavar='COMMENT_ID')
@decorators.with_dbenv()
def update(comment, node, comment_id):
    """
    Update a comment.

    id      = The id of the comment
    comment = The comment (a string) to be added to the node(s)
    """
    from aiida import orm

    user = orm.User.objects.get_default()

    # read the comment from terminal if it is not on command line
    if comment is None:
        try:
            current_comment = node.get_comments(comment_id)[0]
        except IndexError:
            echo.echo_error("Comment with id '{}' not found".format(comment_id))
            return 1

        comment = multi_line_input.edit_comment(current_comment['content'])

    # pylint: disable=protected-access
    node._update_comment(comment, comment_id, user)

    return 0
