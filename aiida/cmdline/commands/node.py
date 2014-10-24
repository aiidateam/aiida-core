# -*- coding: utf-8 -*-
import sys

from aiida.cmdline.baseclass import (
    VerdiCommandRouter, VerdiCommandWithSubcommands)
from aiida import load_dbenv


__author__ = "Giovanni Pizzi, Andrea Cepellotti, Riccardo Sabatini, Nicola Marzari, and Boris Kozinsky"
__copyright__ = u"Copyright (c), 2012-2014, École Polytechnique Fédérale de Lausanne (EPFL), Laboratory of Theory and Simulation of Materials (THEOS), MXC - Station 12, 1015 Lausanne, Switzerland. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.2.0"

class Node(VerdiCommandRouter):
    """
    Manage operations on AiiDA nodes
    
    There is a list of subcommands for managing specific types of data.
    For instance, 'node repo' manages the files in the local repository.
    """
    def __init__(self):
        """
        A dictionary with valid commands and functions to be called.
        """        
        ## Add here the classes to be supported.
        self.routed_subcommands = {
            'repo': _Repo,
            }

# Note: this class should not be exposed directly in the main module,
# otherwise it becomes a command of 'verdi'. Instead, we want it to be a 
# subcommand of verdi data.
class _Repo(VerdiCommandWithSubcommands):
    """
    Show files and their contents in the local repository
    """
    def __init__(self):
        """
        A dictionary with valid commands and functions to be called.
        """
        self.valid_subcommands = {
            'ls': (self.ls, self.complete_none),
            'cat': (self.cat, self.complete_none),
            }
    
    def ls(self, *args):
        """
        List the files in the repository folder.
        """
        import argparse
        import os
        
        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='List files in the repository folder.')

        parser.add_argument('-c','--color', action='store_true',
                            help="Color folders with a different color")
        parser.add_argument('-p', '--pk', type=int, required=True, 
                            help='The pk of the node')
        parser.add_argument('path', type=str, default='.', nargs='?',
                            help='The relative path of the file you '
                            'want to show')
        #parser.add_argument('-d', '--with-description',
        #                    dest='with_description',action='store_true',
        #                    help="Show also the description for the UPF family")
        #parser.set_defaults(with_description=False)
        
        args = list(args)
        parsed_args = parser.parse_args(args)

        load_dbenv()
        from aiida.orm import Node as OrmNode        
        
        n = OrmNode.get_subclass_from_pk(parsed_args.pk)
        f = n.folder
        
        is_dir = False
        parts = parsed_args.path.split(os.path.sep)
        # except the last item
        for item in parts[:-1]:
            f = f.get_subfolder(item)
        if parts:
            if f.isdir(parts[-1]):
                f = f.get_subfolder(parts[-1])
                is_dir = True
            else:
                fname = parts[-1]
        else:
            is_dir = True

        if is_dir:
            if not f.isdir('.'):
                print >> sys.stderr, "{}: No such file or directory in the repo".format(parsed_args.path)
                sys.exit(1)
        
            for elem, elem_is_file in sorted(f.get_content_list(only_paths=False)):
                if elem_is_file or not parsed_args.color:
                    print elem
                else:
                    # BOLD("1;") and color 34=blue
                    outstr = "\x1b[1;{color_id}m{elem}\x1b[0m".format(color_id=34,
                                                                      elem=elem)
                    print outstr
        else:
            if not f.isfile(fname):
                print >> sys.stderr, "{}: No such file or directory in the repo".format(parsed_args.path)
                sys.exit(1)
            
            print fname
        
    def cat(self, *args):
        """
        Output the content of a file in the repository folder.
        """
        import argparse
        import os
        
        parser = argparse.ArgumentParser(
            prog=self.get_full_command_name(),
            description='Output the content of a file in the repository folder.')
        parser.add_argument('-p', '--pk', type=int, required=True, 
                            help='The pk of the node')
        parser.add_argument('path', type=str, 
                            help='The relative path of the file you '
                            'want to show')
        
        args = list(args)
        parsed_args = parser.parse_args(args)

        load_dbenv()
        from aiida.orm import Node as OrmNode        
        
        n = OrmNode.get_subclass_from_pk(parsed_args.pk)
        f = n.folder
        
        is_dir = False
        parts = parsed_args.path.split(os.path.sep)
        # except the last item
        for item in parts[:-1]:
            f = f.get_subfolder(item)
        if parts:
            if f.isdir(parts[-1]):
                f = f.get_subfolder(parts[-1])
                is_dir = True
            else:
                fname = parts[-1]
        else:
            is_dir = True

        if is_dir:
            if not f.isdir('.'):
                print >> sys.stderr, "{}: No such file or directory in the repo".format(parsed_args.path)
                sys.exit(1)
            else:
                print >> sys.stderr, "{}: is a directory".format(parsed_args.path)
                sys.exit(1)                

        else:
            if not f.isfile(fname):
                print >> sys.stderr, "{}: No such file or directory in the repo".format(parsed_args.path)
                sys.exit(1)
                
            absfname = f.get_abs_path(fname)
            with open(absfname) as f:
                for l in f:
                    sys.stdout.write(l)
           
            
