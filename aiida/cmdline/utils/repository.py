# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utility functions for command line commands operating on the repository."""
from __future__ import absolute_import
from aiida.cmdline.utils import echo


def cat_repo_files(node, path):
    """
    Given a Node and a relative path to a file in the Node repository directory,
    prints in output the content of the file.

    :param node: a Node instance
    :param path: a string with the relative path to list. Must be a file.
    :raise ValueError: if the file is not found, or is a directory.
    """
    import os
    import sys

    fldr = node.folder

    is_dir = False
    parts = path.split(os.path.sep)
    # except the last item
    for item in parts[:-1]:
        fldr = fldr.get_subfolder(item)
    if parts:
        if fldr.isdir(parts[-1]):
            fldr = fldr.get_subfolder(parts[-1])
            is_dir = True
        else:
            fname = parts[-1]
    else:
        is_dir = True

    if is_dir:
        if not fldr.isdir('.'):
            raise ValueError("No directory '{}' in the repo".format(path))
        else:
            raise ValueError("'{}' is a directory".format(path))
    else:
        if not fldr.isfile(fname):
            raise ValueError("No file '{}' in the repo".format(path))

        absfname = fldr.get_abs_path(fname)
        with open(absfname) as repofile:
            for line in repofile:
                sys.stdout.write(line)


def list_repo_files(node, path, color):
    """
    Given a Node and a relative path prints in output the list of files
    in the given path in the Node repository directory.

    :param node: a Node instance
    :param path: a string with the relative path to list. Can be a file.
    :param color: boolean, if True prints with the codes to show colors.
    :raise ValueError: if the file or directory is not found.
    """
    import os

    fldr = node.folder

    is_dir = False
    parts = path.split(os.path.sep)
    # except the last item
    for item in parts[:-1]:
        fldr = fldr.get_subfolder(item)
    if parts:
        if fldr.isdir(parts[-1]):
            fldr = fldr.get_subfolder(parts[-1])
            is_dir = True
        else:
            fname = parts[-1]
    else:
        is_dir = True

    if is_dir:
        if not fldr.isdir('.'):
            raise ValueError("{}: No such file or directory in the repo".format(path))

        for elem, elem_is_file in sorted(fldr.get_content_list(only_paths=False)):
            if elem_is_file or not color:
                echo.echo(elem)
            else:
                # BOLD("1;") and color 34=blue
                outstr = "\x1b[1;{color_id}m{elem}\x1b[0m".format(color_id=34, elem=elem)
                echo.echo(outstr)
    else:
        if not fldr.isfile(fname):
            raise ValueError("{}: No such file or directory in the repo".format(path))

        echo.echo(fname)
