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

from .data import Data

__all__ = ('FolderData',)


class FolderData(Data):
    """`Data` sub class to represent a folder on a file system."""

    def __init__(self, **kwargs):
        """Construct a new `FolderData` to which any files and folders can be added.

        Use the `tree` keyword to simply wrap a directory:

            folder = FolderData(tree='/absolute/path/to/directory')

        Alternatively, one can construct the node first and then use the various repository methods to add objects:

            folder = FolderData()
            folder.put_object_from_tree('/absolute/path/to/directory')
            folder.put_object_from_filepath('/absolute/path/to/file.txt')
            folder.put_object_from_filelike(filelike_object)

        :param tree: absolute path to a folder to wrap
        :type tree: str
        """
        tree = kwargs.pop('tree', None)
        super().__init__(**kwargs)
        if tree:
            self.base.repository.put_object_from_tree(tree)
