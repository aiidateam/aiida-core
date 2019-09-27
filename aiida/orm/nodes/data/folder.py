# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""`Data` sub class to represent a folder on a file system."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from .data import Data

__all__ = ('FolderData',)


class FolderData(Data):
    """`Data` sub class to represent a folder on a file system."""

    def __init__(self, **kwargs):
        """Construct a new `FolderData` to which any files and folders can be added.

        To add files to a new node use the various repository methods:

            folder = FolderData()
            folder.put_object_from_tree('/absolute/path/to/directory')
            folder.put_object_from_filepath('/absolute/path/to/file.txt')
            folder.put_object_from_filelike(filelike_object)

        Alternatively, in order to simply wrap a directory, the `path` keyword can be used in the constructor:

            folder = FolderData(tree='/absolute/path/to/directory')
        """
        tree = kwargs.pop('tree', None)
        super(FolderData, self).__init__(**kwargs)
        if tree:
            self.put_object_from_tree(tree)
