# -*- coding: utf-8 -*-
"""Data plugin that models a stashed folder on a remote computer."""
import typing

from aiida.common.datastructures import StashMode
from aiida.common.lang import type_check

from .base import RemoteStashData

__all__ = ('RemoteStashFolderData',)


class RemoteStashFolderData(RemoteStashData):
    """Data plugin that models a folder with files of a completed calculation job that has been stashed through a copy.

    This data plugin can and should be used to stash files if and only if the stash mode is `StashMode.COPY`.
    """

    _storable = True

    def __init__(self, stash_mode: StashMode, target_basepath: str, source_list: typing.List, **kwargs):
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
    def source_list(self) -> typing.Union[typing.List, typing.Tuple]:
        """Return the list of source files that were stashed.

        :return: the list of source files.
        """
        return self.base.attributes.get('source_list')

    @source_list.setter
    def source_list(self, value: typing.Union[typing.List, typing.Tuple]):
        """Set the list of source files that were stashed.

        :param value: the list of source files.
        """
        type_check(value, (list, tuple))
        self.base.attributes.set('source_list', value)
