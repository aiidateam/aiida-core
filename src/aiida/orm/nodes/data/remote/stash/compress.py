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

from aiida.common import exceptions
from aiida.common.datastructures import StashMode
from aiida.common.lang import type_check
from aiida.orm.decorators.attributes import attribute
from aiida.orm.nodes.data.remote.stash.base import RemoteStashData

__all__ = ('RemoteStashCompressedData',)


class RemoteStashCompressedData(RemoteStashData):
    """Data plugin that models a compressed stashed file on a remote computer."""

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

    @attribute
    def dereference(self) -> bool:
        """Whether to follow symlinks while stashing."""
        return self.base.attributes.get('dereference')

    @dereference.setter
    def dereference(self, value: bool) -> None:
        type_check(value, bool)
        self.base.attributes.set('dereference', value)

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
        """Validate the compressed stash configuration."""
        super()._validate()

        if self.stash_mode not in {
            StashMode.COMPRESS_TAR,
            StashMode.COMPRESS_TARBZ2,
            StashMode.COMPRESS_TARGZ,
            StashMode.COMPRESS_TARXZ,
        }:
            raise exceptions.ValidationError(
                '`RemoteStashCompressedData` can only be used with `stash_mode` being either '
                '`StashMode.COMPRESS_TAR`, `StashMode.COMPRESS_TARGZ`, '
                '`StashMode.COMPRESS_TARBZ2` or `StashMode.COMPRESS_TARXZ`.'
            )

        try:
            self.target_basepath
        except AttributeError as exc:
            raise exceptions.ValidationError("attribute 'target_basepath' not set.") from exc

        try:
            self.source_list
        except AttributeError as exc:
            raise exceptions.ValidationError("attribute 'source_list' not set.") from exc

        try:
            self.dereference
        except AttributeError as exc:
            raise exceptions.ValidationError("attribute 'dereference' not set.") from exc
