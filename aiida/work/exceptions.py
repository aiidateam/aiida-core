# -*- coding: utf-8 -*-
"""Exceptions that can be thrown by parts of the workflow engine."""
from aiida.common.exceptions import AiidaException

__all__ = ['Exit', 'PastException']


class Exit(AiidaException):
    """
    This can be raised from within a workfunction to tell it to exit immediately, but as opposed to all other
    exceptions will not cause the workflow engine to mark the workfunction as excepted. Rather it will take
    the exit code set for the exception and set that as the finish status of the workfunction.
    """

    def __init__(self, exit_code=0):
        """
        Construct the exception with a given exit code

        :param exit_code: the integer exit code, default is 0
        """
        super(Exit, self).__init__()
        self._exit_code = exit_code

    @property
    def exit_code(self):
        return self._exit_code


class PastException(AiidaException):
    """
    Raised when an attempt is made to continue a Process that has already excepted before
    """
    pass
