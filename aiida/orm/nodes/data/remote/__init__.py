# -*- coding: utf-8 -*-
"""Module with data types that model data on remote machines and so are effectively symbolic links."""
from .base import RemoteData
from .folder import RemoteFolderData
from .stash import RemoteStashData

__all__ = ('RemoteData', 'RemoteFolderData', 'RemoteStashData')
