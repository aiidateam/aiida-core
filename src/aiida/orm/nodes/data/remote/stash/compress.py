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
from aiida.orm.fields import add_field

from .base import RemoteStashData

__all__ = ('RemoteStashCompressedData',)


class RemoteStashCompressedData(RemoteStashData):
    """Data plugin that models a compressed stashed file on a remote computer."""

    _storable = True

    __qb_fields__ = [
        add_field(
            'target_basepath',
            dtype=str,
            doc='The the target basepath',
        ),
        add_field(
            'source_list',
            dtype=List[str],
            doc='The list of source files that were stashed',
        ),
        add_field(
            'dereference',
            dtype=bool,
            doc='The format of the compression used when stashed',
        ),
    ]

    def __init__(
        self,
        stash_mode: StashMode,
        target_basepath: str,
        source_list: List,
        dereference: bool,
        **kwargs,
    ):
        """Construct a new instance

        :param stash_mode: the stashing mode with which the data was stashed on the remote.
        :param target_basepath: absolute path to place the compressed file (path+filename).
        :param source_list: the list of source files.
        """
        super().__init__(stash_mode, **kwargs)
        self.target_basepath = target_basepath
        self.source_list = source_list
        self.dereference = dereference

        if stash_mode not in [
            StashMode.COMPRESS_TAR,
            StashMode.COMPRESS_TARBZ2,
            StashMode.COMPRESS_TARGZ,
            StashMode.COMPRESS_TARXZ,
        ]:
            raise ValueError(
                '`RemoteStashCompressedData` can only be used with `stash_mode` being either '
                '`StashMode.COMPRESS_TAR`, `StashMode.COMPRESS_TARGZ`, '
                '`StashMode.COMPRESS_TARBZ2` or `StashMode.COMPRESS_TARXZ`.'
            )

    @property
    def dereference(self) -> bool:
        """Return the dereference boolean.

        :return: the dereference boolean.
        """
        return self.base.attributes.get('dereference')

    @dereference.setter
    def dereference(self, value: bool):
        """Set the dereference boolean.

        :param value: the dereference boolean.
        """
        type_check(value, bool)
        self.base.attributes.set('dereference', value)

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
