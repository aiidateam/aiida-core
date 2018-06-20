# -*- coding: utf-8 -*-
"""Exceptions that can be thrown by parts of the workflow engine."""
from aiida.common.exceptions import AiidaException

__all__ = ['PastException']


class PastException(AiidaException):
    """
    Raised when an attempt is made to continue a Process that has already excepted before
    """
    pass
