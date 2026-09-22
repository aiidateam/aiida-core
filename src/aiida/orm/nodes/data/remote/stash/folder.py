###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Data plugin that models a stashed folder on a remote computer."""

from __future__ import annotations

import pydantic as pdt

from aiida.common.datastructures import StashMode
from aiida.common.lang import type_check
from aiida.orm.decorators.attributes import attribute
from aiida.orm.nodes.data.remote.stash.base import RemoteStashData

__all__ = ('RemoteStashFolderData',)


class RemoteStashFolderData(RemoteStashData):
    """Data plugin that models a folder with files of a completed calculation job that has been stashed through a copy.

    This data plugin can and should be used to stash files if and only if the stash mode is `StashMode.COPY`.
    """

    _storable = True

    @attribute
    def target_basepath(self) -> str:
        """The target basepath."""
        return self.base.attributes.get('target_basepath')

    @target_basepath.setter
    def target_basepath(self, value: str) -> None:
        type_check(value, str)
        self.base.attributes.set('target_basepath', value)

    @attribute
    def source_list(self) -> list[str]:
        """The list of source files that were stashed."""
        return self.base.attributes.get('source_list')

    @source_list.setter
    def source_list(self, value: list[str] | tuple[str, ...]) -> None:
        type_check(value, (list, tuple))

        if not all(isinstance(source, str) for source in value):
            raise TypeError('`source_list` should contain only strings.')

        self.base.attributes.set('source_list', list(value))

    @attribute(model_field_info=pdt.fields.FieldInfo(default=False))
    def fail_on_missing(self) -> bool:
        """Whether stashing should fail if any files are missing."""
        # The default is set for backward compatibility.
        return self.base.attributes.get('fail_on_missing', False)

    @fail_on_missing.setter
    def fail_on_missing(self, value: bool) -> None:
        type_check(value, bool)
        self.base.attributes.set('fail_on_missing', value)

    def _validate(self) -> None:
        """Validate the stashed folder configuration."""
        from aiida.common.exceptions import ValidationError

        super()._validate()

        if self.stash_mode != StashMode.COPY:
            raise ValidationError('`RemoteStashFolderData` can only be used with `stash_mode == StashMode.COPY`.')

        try:
            self.target_basepath
        except AttributeError as exc:
            raise ValidationError("attribute 'target_basepath' not set.") from exc

        try:
            self.source_list
        except AttributeError as exc:
            raise ValidationError("attribute 'source_list' not set.") from exc
