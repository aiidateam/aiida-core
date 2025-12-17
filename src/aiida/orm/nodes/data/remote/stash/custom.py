###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Data plugin that models a stashed folder on a remote computer."""

from typing import List, Optional, Tuple, Union

from aiida.common.datastructures import StashMode
from aiida.common.lang import type_check
from aiida.common.pydantic import MetadataField

from .base import RemoteStashData

__all__ = ('RemoteStashCustomData',)


class RemoteStashCustomData(RemoteStashData):
    """Data plugin that models stashed data on a remote computer, which was done via a custom script."""

    _storable = True

    class AttributesModel(RemoteStashData.AttributesModel):
        target_basepath: str = MetadataField(
            description='The the target basepath',
        )
        source_list: List[str] = MetadataField(
            description='The list of source files that were stashed',
        )

    def __init__(
        self,
        stash_mode: Optional[StashMode] = None,
        target_basepath: Optional[str] = None,
        source_list: Optional[List] = None,
        **kwargs,
    ):
        """Construct a new instance

        :param stash_mode: the stashing mode with which the data was stashed on the remote.
        :param target_basepath: the target basepath.
        :param source_list: the list of source files.
        """

        attributes = kwargs.get('attributes', {})
        stash_mode = stash_mode or attributes.pop('stash_mode', None)
        target_basepath = target_basepath or attributes.pop('target_basepath', None)
        source_list = source_list or attributes.pop('source_list', None)

        if stash_mode is None:
            raise ValueError('the `stash_mode` parameter must be specified.')
        if target_basepath is None:
            raise ValueError('the `target_basepath` parameter must be specified.')
        if source_list is None:
            raise ValueError('the `source_list` parameter must be specified.')

        super().__init__(stash_mode, **kwargs)

        self.target_basepath = target_basepath
        self.source_list = source_list

        if stash_mode != StashMode.SUBMIT_CUSTOM_CODE:
            raise ValueError('`RemoteStashCustomData` can only be used with `stash_mode == StashMode.COPY`.')

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
