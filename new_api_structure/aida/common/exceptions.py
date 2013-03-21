class AidaException(Exception):
    """
    Base class for all aida exceptions.
    
    Each module will have its own subclass, inherited from this
    (e.g. ExecManagerException, TransportException, ...)
    """
    pass

class InternalError(AidaException):
    """
    Error raised when there is an internal error of Aida.
    """
    pass
