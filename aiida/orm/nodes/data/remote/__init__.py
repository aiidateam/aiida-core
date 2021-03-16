# -*- coding: utf-8 -*-
"""Module with data plugins that represent remote resources and so effectively are symbolic links."""
from .base import RemoteData
from .stash import RemoteStashData, RemoteStashFolderData

__all__ = ('RemoteData', 'RemoteStashData', 'RemoteStashFolderData')
