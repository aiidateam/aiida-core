# -*- coding: utf-8 -*-
"""
This allows to setup and configure a code from command line.

TODO: think if we want to allow to change path and prepend/append text.
"""
import sys

from aiida.cmdline.baseclass import VerdiCommandWithSubcommands
from aiida import load_dbenv

__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = u"Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

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
            'show' : (self.comment_show, self.complete_none),
            'update' : (self.comment_update, self.complete_none),
            'remove' : (self.comment_remove, self.complete_none),
            }
    
    def comment_add(self, *args):
        """
        Add comment to a node
        """
        import argparse
        from aiida.djsite.utils import get_automatic_user
        from aiida.orm.node import Node as AiidaOrmNode
        load_dbenv()
        user = get_automatic_user()
        
        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Add a comment to a node in the database.')
        parser.add_argument('pk', metavar='PK', type=int,
                            help='The pk (an integer) of the node')
        parser.add_argument('-c','--comment', type=str, default="", 
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
                #Ctrl+D pressed: end of input.
                pass            
            comment = "\n".join(newlines)
        
        node = AiidaOrmNode.get_subclass_from_pk(parsed_args.pk)
        node.add_comment( comment,user )
        
    def comment_show(self, *args):
        """
        Show the comments of a node
        """
        import argparse
        from aiida.djsite.utils import get_automatic_user
        from aiida.orm.node import Node as AiidaOrmNode
        load_dbenv()
        user = get_automatic_user()
        
        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Show the comments of a node in the database.')
        parser.add_argument('pk', metavar='PK', type=int,
                            help='The pk (an integer) of the node.')
        parser.add_argument('-u','--user', type=str, default=None, 
                            help='Show only the comments of a given user (optional).')
        parsed_args = parser.parse_args(args)
        
        node = AiidaOrmNode.get_subclass_from_pk(parsed_args.pk)
        all_comments = node.get_comments_tuple()
        
        if parsed_args.user is not None:
            to_print = [ i for i in all_comments if i[0]==parsed_args.user ]
            if not to_print:
                print "Nothing found for user '{}'."
                print "Valid users are {}.".format( 
                        ", ".join(set(["'"+i[0]+"'" for i in all_comments])))
        else:
            to_print = all_comments 

        for i in to_print:
            print "***********************************************************"
            print "Comment of user '{}' on {}".format(i[0],i[1].strftime("%Y-%m-%d %H:%M:%S"))
            print "Comment last modified on {}".format(i[2].strftime("%Y-%m-%d %H:%M:%S"))
            print ""
            print "{}".format(i[3])
            print ""
        
    def comment_remove(self, *args):
        """
        Remove comments. The user can only remove its own comments
        """
        # Note: in fact, the user can still manually delete any comment
        import argparse
        from aiida.djsite.utils import get_automatic_user
        from aiida.orm.node import Node as AiidaOrmNode
        from aiida.common.exceptions import ModificationNotAllowed
        load_dbenv()
        user = get_automatic_user()
        
        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Remove comments of a node.')
        parser.add_argument('pk', metavar='PK', type=int,
                            help='The pk (an integer) of the node')
        parser.add_argument('-i','--index', type=int,default=None,
                            help='To remove comment at position #index of the list of all comments')
        parser.add_argument('-a','--all', action='store_true', default=False, 
                            help='If used, deletes all the comments of the active user attached to the node')
        parsed_args = parser.parse_args(args)
        
        node = AiidaOrmNode.get_subclass_from_pk(parsed_args.pk)
        all_comments = node.get_comments_tuple()

        if parsed_args.index is None and not parsed_args.all:
            print "Only one between -a and index arguments should be provided"
            sys.exit(1)
            
        if parsed_args.index is not None and parsed_args.all:
            print "Only one between -a and index arguments should be provided"
            sys.exit(1)

        if parsed_args.index is not None:
            try:
                all_comments[parsed_args.index]
            except IndexError:
                print "Index exceeding the maximum allowed ({})".format(len(all_comments)-1)
                sys.exit(1)
        
        allowed_trues = ['1','t','true','y','yes']
        
        if parsed_args.all:
            sys.stdout.write("Delete all comments of user {}? ".format(user))
            inpread = sys.stdin.readline()
            do_I_delete = True if inpread.strip().lower() in allowed_trues else False
            
            if not do_I_delete:
                print "Not deleting comment"
                sys.exit(1)
            else:
                one_found = False
                for i,_ in enumerate(all_comments):
                    try:
                        node._remove_comment(i,user)
                        one_found = True
                    except ModificationNotAllowed:
                        pass
                if not one_found:
                    print "No comments of user {} found".format(user)
        else:
            sys.stdout.write("Delete comment? ")
            inpread = sys.stdin.readline()
            do_I_delete = True if inpread.strip().lower() in allowed_trues else False
            
            if not do_I_delete:
                print "Not deleting comment"
                sys.exit(1)
            else:
                try:
                    node._remove_comment(parsed_args.index,user)
                except ModificationNotAllowed:
                    print "User is not proprietary of the comment, cannot delete it"
        
    def comment_update(self, *args):
        """
        Update a comment
        """
        import argparse
        from aiida.djsite.utils import get_automatic_user
        from aiida.orm.node import Node as AiidaOrmNode
        load_dbenv()
        user = get_automatic_user()
        
        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Add a comment to a node in the database.')
        parser.add_argument('pk', metavar='PK', type=int,
                            help='The pk (an integer) of the node')
        parser.add_argument('index', type=int, 
                            help='To update comment at position #index of the list of all comments')
        parser.add_argument('-c','--comment', type=str, default=None, 
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
                #Ctrl+D pressed: end of input.
                pass            
            the_comment = "\n".join(newlines)
        else:
            the_comment = parsed_args.comment

        
        node = AiidaOrmNode.get_subclass_from_pk(parsed_args.pk)

        try:        
            node._update_comment(the_comment,
                                 parsed_args.index,
                                 user)
        except IndexError:
            print "Index {} exceeding the length of comments (max allowed: {})".format(
                             parsed_args.index,len(node.get_comments_tuple())-1)
            sys.exit(1)
        