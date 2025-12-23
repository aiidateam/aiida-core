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

    class Model(RemoteStashData.Model):
        target_basepath: str = MetadataField(description='The the target basepath')
        source_list: List[str] = MetadataField(description='The list of source files that were stashed')

    def __init__(self, stash_mode: StashMode, target_basepath: str, source_list: List, **kwargs):
        """Construct a new instance

        :param stash_mode: the stashing mode with which the data was stashed on the remote.
        :param target_basepath: the target basepath.
        :param source_list: the list of source files.
        """
        super().__init__(stash_mode, **kwargs)
        self.target_basepath = target_basepath
        self.source_list = source_list

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

    def _clean(self, transport=None):
        """Remove stashed content on the remote computer.

        When the cleaning operation is successful, the extra with the key ``RemoteStashData.KEY_EXTRA_CLEANED`` is set.

        :param transport: Provide an optional transport that is already open. If not provided, a transport will be
            automatically opened, based on the current default user and the computer of this data node.
        :raises ValueError: If the hostname of the provided transport does not match that of the node's computer.
        """
        from aiida.orm.utils.remote import clean_remote

        target_basepath = self.target_basepath

        if transport is None:
            with self.get_authinfo().get_transport() as _transport:
                clean_remote(_transport, target_basepath)
        else:
            if transport.hostname != self.computer.hostname:
                raise ValueError(
                    f'Transport hostname `{transport.hostname}` does not equal `{self.computer.hostname}` of {self}.'
                )
            clean_remote(transport, target_basepath)

        self.base.extras.set(self.KEY_EXTRA_CLEANED, True)
