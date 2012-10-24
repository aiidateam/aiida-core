"""
Exceptions used by aida.
"""

class AidaError(Exception):
    """
    A base exception for other aida-related errors.
    """
    pass

class SubmissionError(AidaError):
    """
    Raised when there is an error in the job submission phase.
    """
    pass
