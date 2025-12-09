###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Data plugin that models an archived folder on a remote computer."""

from aiida.common.datastructures import StashMode
from aiida.common.lang import type_check
from aiida.common.pydantic import MetadataField

from ...data import Data

__all__ = ('RemoteStashData',)


class RemoteStashData(Data):
    """Data plugin that models an archived folder on a remote computer.

    A stashed folder is essentially an instance of ``RemoteData`` that has been archived. Archiving in this context can
    simply mean copying the content of the folder to another location on the same or another filesystem as long as it is
    on the same machine. In addition, the folder may have been compressed into a single file for efficiency or even
    written to tape. The ``stash_mode`` attribute will distinguish how the folder was stashed which will allow the
    implementation to also `unstash` it and transform it back into a ``RemoteData`` such that it can be used as an input
    for new ``CalcJobs``.

    This class is a non-storable base class that merely registers the ``stash_mode`` attribute. Only its subclasses,
    that actually implement a certain stash mode, can be instantiated and therefore stored. The reason for this design
    is that because the behavior of the class can change significantly based on the mode employed to stash the files and
    implementing all these variants in the same class will lead to an unintuitive interface where certain properties or
    methods of the class will only be available or function properly based on the ``stash_mode``.
    """

    _storable = False

    class AttributesModel(Data.AttributesModel):
        stash_mode: StashMode = MetadataField(description='The mode with which the data was stashed')

    def __init__(self, stash_mode: StashMode, **kwargs):
        """Construct a new instance

        :param stash_mode: the stashing mode with which the data was stashed on the remote.
        """
        super().__init__(**kwargs)
        self.stash_mode = stash_mode

    @property
    def stash_mode(self) -> StashMode:
        """Return the mode with which the data was stashed on the remote.

        :return: the stash mode.
        """
        return StashMode(self.base.attributes.get('stash_mode'))

    @stash_mode.setter
    def stash_mode(self, value: StashMode):
        """Set the mode with which the data was stashed on the remote.

        :param value: the stash mode.
        """
        type_check(value, StashMode)
        self.base.attributes.set('stash_mode', value.value)
