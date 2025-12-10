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

__all__ = ('RemoteStashCompressedData',)


class RemoteStashCompressedData(RemoteStashData):
    """Data plugin that models a compressed stashed file on a remote computer."""

    _storable = True

    class Model(RemoteStashData.Model):
        target_basepath: str = MetadataField(
            description='The the target basepath',
        )
        source_list: List[str] = MetadataField(
            description='The list of source files that were stashed',
        )
        dereference: bool = MetadataField(
            description='The format of the compression used when stashed',
        )

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

    def _clean(self, transport=None):
        """Remove stashed compressed file on the remote computer.

        When the cleaning operation is successful, the extra with the key ``RemoteStashData.KEY_EXTRA_CLEANED`` is set.

        :param transport: Provide an optional transport that is already open. If not provided, a transport will be
            automatically opened, based on the current default user and the computer of this data node.
        :raises ValueError: If the hostname of the provided transport does not match that of the node's computer.
        """
        from aiida.orm import AuthInfo

        target_basepath = self.target_basepath

        if transport is None:
            authinfo = AuthInfo.get_collection(self.backend).get(dbcomputer=self.computer, aiidauser=self.user)
            with authinfo.get_transport() as _transport:
                try:
                    _transport.remove(target_basepath)
                except OSError:
                    pass
        else:
            if transport.hostname != self.computer.hostname:
                raise ValueError(
                    f'Transport hostname `{transport.hostname}` does not equal `{self.computer.hostname}` of {self}.'
                )
            try:
                transport.remove(target_basepath)
            except OSError:
                pass

        self.base.extras.set(self.KEY_EXTRA_CLEANED, True)
