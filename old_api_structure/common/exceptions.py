"""
Exceptions used by aida.
"""

class AidaError(StandardError):
    """
    A base exception for other aida-related errors.

    It depends on StandardError rather than on Exception to explicitly
    state that this is an error and not a warning.
    """
    pass

class SubmissionError(AidaError):
    """
    Raised when there is an error in the job submission phase.
    """
    pass

class ValidationError(AidaError):
    """
    Raised when there is an error in a validation phase (e.g. of input, etc.)
    """
    pass
