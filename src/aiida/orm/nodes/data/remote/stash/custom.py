###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Data plugin that models a stashed folder on a remote computer."""

from aiida.common.datastructures import StashMode
from aiida.common.lang import type_check
from aiida.orm.fields import add_field

from .base import RemoteStashData

__all__ = ('RemoteStashCustomData',)


class RemoteStashCustomData(RemoteStashData):
    """ """

    _storable = True

    __qb_fields__ = [
        add_field(
            'custom_command',
            dtype=str,
            doc='The custom_command with which the data was stashed',
        ),
    ]

    def __init__(
        self,
        stash_mode: StashMode,
        custom_command: str,
        **kwargs,
    ):
        """Construct a new instance

        :param stash_mode: the stashing mode with which the data was stashed on the remote.
        """
        super().__init__(stash_mode, **kwargs)
        self.custom_command = custom_command

        if stash_mode != StashMode.CUSTOM_SCRIPT:
            raise ValueError('`RemoteStashCustomData` can only be used with `stash_mode == StashMode.COPY`.')

    @property
    def custom_command(self) -> str:
        """Return the custom_command.

        :return: the custom_command.
        """
        return self.base.attributes.get('custom_command')

    @custom_command.setter
    def custom_command(self, value: str):
        """Set the custom_command.

        :param value: the custom_command.
        """
        type_check(value, str)
        self.base.attributes.set('custom_command', value)
