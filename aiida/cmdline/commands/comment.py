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
This allows to manage comments from command line.
"""
import sys

from aiida.cmdline.baseclass import VerdiCommandWithSubcommands
from aiida.backends.utils import load_dbenv, is_dbenv_loaded
from aiida.cmdline import delayed_load_node as load_node



class Comment(VerdiCommandWithSubcommands):
    """
    Manage general properties of nodes in the database
    """

    def __init__(self):
        """
        A dictionary with valid commands and functions to be called.
        """
        self.valid_subcommands = {
            'add': (self.comment_add, self.complete_none),
            'remove': (self.comment_remove, self.complete_none),
            'show': (self.comment_show, self.complete_none),
            'update': (self.comment_update, self.complete_none),
        }

    def comment_add(self, *args):
        """
        Add comment to a node
        """
        import argparse
        from aiida.backends.utils import get_automatic_user

        if not is_dbenv_loaded():
            load_dbenv()

        user = get_automatic_user()

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Add a comment to a node in the database.')
        parser.add_argument('pk', metavar='PK', type=int,
                            help='The pk (an integer) of the node')
        parser.add_argument('-c', '--comment', type=str, default="",
                            help='The comment (a string) to be added to the node')
        parsed_args = parser.parse_args(args)

        comment = parsed_args.comment

        if not comment:
            print "Write below the comment to be added to the node."
            print "   # This is a multiline input, press CTRL+D on a"
            print "   # empty line when you finish"
            try:
                newlines = []
                while True:
                    input_txt = raw_input()
                    if input_txt.strip() == '?':
                        print "\n".join(["  > {}".format(descl) for descl
                                         in "HELP: {}".format(desc).split('\n')])
                        continue
                    else:
                        newlines.append(input_txt)
            except EOFError:
                # Ctrl+D pressed: end of input.
                pass
            comment = "\n".join(newlines)

        node = load_node(parsed_args.pk)
        node.add_comment(comment, user)

    def comment_show(self, *args):
        """
        Show the comments of a node
        """
        import argparse
        from aiida.backends.utils import get_automatic_user

        if not is_dbenv_loaded():
            load_dbenv()
        user = get_automatic_user()

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Show the comments of a node in the database.')
        parser.add_argument('-u', '--user', type=str, default=None,
                            help='Show only the comments of a given user (optional).')
        parser.add_argument('pk', metavar='PK', type=int,
                            help='The pk (an integer) of the node.')
        parser.add_argument('id', metavar='ID', type=int, default=None, nargs='?',
                            help='The id (an integer) of the comment.')
        # Note that this is a false description, I'm using the DBComment.pk
        parsed_args = parser.parse_args(args)

        node = load_node(parsed_args.pk)
        all_comments = node.get_comments(pk=parsed_args.id)

        if parsed_args.user is not None:
            to_print = [i for i in all_comments if i['user__email'] == parsed_args.user]
            if not to_print:
                print "Nothing found for user '{}'.".format(parsed_args.user)
                print "Valid users found for Node {} are: {}.".format(parsed_args.pk,
                                                                      ", ".join(set(
                                                                          ["'" + i['user__email'] + "'" for i in
                                                                           all_comments])))
        else:
            to_print = all_comments

        if parsed_args.id is not None:
            to_print = [i for i in to_print if i['pk'] == parsed_args.id]

        for i in to_print:
            print "***********************************************************"
            print "Comment of '{}' on {}".format(i['user__email'],
                                                 i['ctime'].strftime("%Y-%m-%d %H:%M"))
            print "ID: {}. Last modified on {}".format(i['pk'],
                                                       i['mtime'].strftime("%Y-%m-%d %H:%M"))
            print ""
            print "{}".format(i['content'])
            print ""

        # If there is nothing to print, print a message
        if not to_print:
            print "No comment found."

    def comment_remove(self, *args):
        """
        Remove comments. The user can only remove its own comments
        """
        # Note: in fact, the user can still manually delete any comment
        import argparse
        from aiida.backends.utils import get_automatic_user

        if not is_dbenv_loaded():
            load_dbenv()
        user = get_automatic_user()

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Remove comments of a node.')
        parser.add_argument('pk', metavar='PK', type=int,
                            help='The pk (an integer) of the node')
        parser.add_argument('id', metavar='ID', type=int, default=None, nargs='?',
                            help='#ID of the comment to be removed from node #PK')
        parser.add_argument('-a', '--all', action='store_true', default=False,
                            help='If used, deletes all the comments of the active user attached to the node')
        parsed_args = parser.parse_args(args)

        if parsed_args.id is None and not parsed_args.all:
            print "One argument between -a and ID must be provided"
            sys.exit(1)
        if parsed_args.id is not None and parsed_args.all:
            print "Only one between -a and ID should be provided"
            sys.exit(1)

        node = load_node(parsed_args.pk)

        allowed_trues = ['1', 't', 'true', 'y', 'yes']
        if parsed_args.all:
            sys.stdout.write("Delete all comments of user {}? ".format(user))
            inpread = sys.stdin.readline()
            do_I_delete = True if inpread.strip().lower() in allowed_trues else False

            if not do_I_delete:
                print "Not deleting comment. Aborting."
                sys.exit(1)
            else:
                comments = node.get_comment_obj(user=user)
                for comment in comments:
                    comment.delete()
                print("Deleted {} comments.".format(len(comments)))

        else:
            sys.stdout.write("Delete comment? ")
            inpread = sys.stdin.readline()
            do_I_delete = True if inpread.strip().lower() in allowed_trues else False

            if not do_I_delete:
                print "Not deleting comment. Aborting."
                sys.exit(1)
            else:
                from aiida.orm.implementation import Comment as CommentOrm
                c = CommentOrm(id=parsed_args.id, user=user)
                c.delete()

    def comment_update(self, *args):
        """
        Update a comment
        """
        import argparse
        from aiida.backends.utils import get_automatic_user

        if not is_dbenv_loaded():
            load_dbenv()
        user = get_automatic_user()

        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Add a comment to a node in the database.')
        parser.add_argument('pk', metavar='PK', type=int,
                            help='The pk (an integer) of the node')
        parser.add_argument('id', metavar='ID', type=int,
                            help='Identify the comment to update by ID')
        parser.add_argument('-c', '--comment', type=str, default=None,
                            help='The comment (a string) to be added to the node')
        parsed_args = parser.parse_args(args)

        # read the comment from terminal if it is not on command line
        if parsed_args.comment is None:
            print "Write below the comment that you want to save in the database."
            print "   # This is a multiline input, press CTRL+D on a"
            print "   # empty line when you finish"
            try:
                newlines = []
                while True:
                    input_txt = raw_input()
                    if input_txt.strip() == '?':
                        print "\n".join(["  > {}".format(descl) for descl
                                         in "HELP: {}".format(desc).split('\n')])
                        continue
                    else:
                        newlines.append(input_txt)
            except EOFError:
                # Ctrl+D pressed: end of input.
                pass
            the_comment = "\n".join(newlines)
        else:
            the_comment = parsed_args.comment

        node = load_node(parsed_args.pk)
        node._update_comment(the_comment, parsed_args.id, user)
