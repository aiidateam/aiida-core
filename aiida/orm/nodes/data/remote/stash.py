# -*- coding: utf-8 -*-
"""Data plugin that models an archived folder on a remote computer."""
from .base import RemoteData


class RemoteStashData(RemoteData):
    """Data plugin that models an archived folder on a remote computer.

    A stashed folder is essentially an instance of ``RemoteFolderData`` that has been archived. Archiving in this
    context can simply mean copying the content of the folder to another location on the same or another filesystem as
    long as it is on the same machine. In addition, the folder may have been compressed into a single file for
    efficiency or even written to tape. The ``mode`` attribute will distinguish how the folder was stashed which will
    allow the implementation to also `unstash` it and transform it back into a ``RemoteFolderData`` such that it can
    be used as an input for new ``CalcJobs``.
    """
