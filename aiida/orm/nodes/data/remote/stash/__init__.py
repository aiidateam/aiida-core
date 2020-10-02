# -*- coding: utf-8 -*-
"""Module with data plugins that represent files of completed calculations jobs that have been stashed."""
from .base import RemoteStashData
from .folder import RemoteStashFolderData

__all__ = ('RemoteStashData', 'RemoteStashFolderData')
