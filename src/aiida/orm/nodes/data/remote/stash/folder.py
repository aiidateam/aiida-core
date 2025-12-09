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

from aiida.common.datastructures import StashMode
from aiida.common.lang import type_check
from aiida.common.pydantic import MetadataField

from .base import RemoteStashData

__all__ = ('RemoteStashFolderData',)


class RemoteStashFolderData(RemoteStashData):
    """Data plugin that models a folder with files of a completed calculation job that has been stashed through a copy.

    This data plugin can and should be used to stash files if and only if the stash mode is `StashMode.COPY`.
    """

    _storable = True

    class AttributesModel(RemoteStashData.AttributesModel):
        target_basepath: str = MetadataField(description='The the target basepath')
        source_list: List[str] = MetadataField(description='The list of source files that were stashed')
        fail_on_missing: bool = MetadataField(
            description='Whether stashing should fail if any files are missing', default=False
        )

    def __init__(
        self, stash_mode: StashMode, target_basepath: str, source_list: List, fail_on_missing: bool = False, **kwargs
    ):
        """Construct a new instance

        :param stash_mode: the stashing mode with which the data was stashed on the remote.
        :param target_basepath: the target basepath.
        :param source_list: the list of source files.
        :param fail_on_missing: whether stashing should fail if any files are missing.
        """
        super().__init__(stash_mode, **kwargs)
        self.target_basepath = target_basepath
        self.source_list = source_list
        self.fail_on_missing = fail_on_missing

        if stash_mode != StashMode.COPY:
            raise ValueError('`RemoteStashFolderData` can only be used with `stash_mode == StashMode.COPY`.')

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

    @property
    def fail_on_missing(self) -> bool:
        """Return whether stashing should fail if any files are missing.

        :return: the fail_on_missing flag.
        """
        # The default is set for backward compatibility
        return self.base.attributes.get('fail_on_missing', False)

    @fail_on_missing.setter
    def fail_on_missing(self, value: bool):
        """Set whether stashing should fail if any files are missing.

        :param value: the fail_on_missing flag.
        """
        type_check(value, bool)
        self.base.attributes.set('fail_on_missing', value)
