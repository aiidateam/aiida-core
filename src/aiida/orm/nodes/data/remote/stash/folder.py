###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Data plugin that models a stashed folder on a remote computer."""

from typing import List, Tuple, Union

from aiida.common import AIIDA_LOGGER
from aiida.common.datastructures import StashMode
from aiida.common.lang import type_check
from aiida.common.pydantic import MetadataField

from .base import RemoteStashData

FOLDER_LOGGER = AIIDA_LOGGER.getChild('folder')


class RemoteStashFolderData(RemoteStashData):
    """
    .. warning::
        **Deprecated!** Use `RemoteStashCopyData` instead.
        The plugin is kept for backwards compatibility (to load already stored nodes, only)
        and will be removed in AiiDA 3.0

    Data plugin that models a folder with files of a completed calculation job that has been stashed through a copy.
    This data plugin can and should be used to stash files if and only if the stash mode is `StashMode.COPY`.
    """

    _storable = True

    class Model(RemoteStashData.Model):
        target_basepath: str = MetadataField(description='The the target basepath')
        source_list: List[str] = MetadataField(description='The list of source files that were stashed')

    def __init__(self, stash_mode: StashMode, target_basepath: str, source_list: List[str], **kwargs):
        FOLDER_LOGGER.warning(
            '`RemoteStashFolderData` is deprecated, it can only be used to load already stored data. '
            'Not possible to make any new instance of it. Use `RemoteStashCopyData` instead.',
        )
        raise RuntimeError('`RemoteStashFolderData` instantiation is not allowed. Use `RemoteStashCopyData` instead.')

    @property
    def target_basepath(self) -> str:
        """Return the target basepath.

        :return: the target basepath.
        """
        return self.base.attributes.get('target_basepath')

    @target_basepath.setter
    def target_basepath(self, value: str):
        """Set the target basepath.

        :param value: the target basepath.
        """
        type_check(value, str)
        self.base.attributes.set('target_basepath', value)

    @property
    def source_list(self) -> Union[List, Tuple]:
        """Return the list of source files that were stashed.

        :return: the list of source files.
        """
        return self.base.attributes.get('source_list')

    @source_list.setter
    def source_list(self, value: Union[List, Tuple]):
        """Set the list of source files that were stashed.

        :param value: the list of source files.
        """
        type_check(value, (list, tuple))
        self.base.attributes.set('source_list', value)
