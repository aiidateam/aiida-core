# -*- coding: utf-8 -*-
"""Exceptions that can be thrown by parts of the workflow engine."""
from aiida.common.exceptions import AiidaException

__all__ = ['Exit', 'PastException']


class Exit(AiidaException):
    """
    This can be raised from within a FunctionProcess to tell it to exit immediately, but as opposed to all other
    exceptions will not cause the workflow engine to mark the FunctionProcess as excepted. Rather it will take
    the exit status and message defined for the exception and set that as attributes of the FunctionProcess.
    """

    def __init__(self, status=0, message=None):
        """
        Construct the exception with a given exit status and message

        :param status: the integer exit code, default is 0
        :param message: the exit message, default is None
        """
        self._status = status
        self._message = message

    @property
    def status(self):
        return self._status

    @property
    def message(self):
        return self._message


class PastException(AiidaException):
    """
    Raised when an attempt is made to continue a Process that has already excepted before
    """
    pass
