class AidaException(Exception):
    """
    Base class for all aida exceptions.
    
    Each module will have its own subclass, inherited from this
    (e.g. ExecManagerException, TransportException, ...)
    """
    pass

class NotExistent(AidaException):
    """
    Raised when the required entity does not exist.
    """
    pass

class ModificationNotAllowed(AidaException):
    """
    Raised when the user tries to modify a field, object, property, ... that should not
    be modified.
    """
    pass

class InvalidOperation(AidaException):
    """
    The allowed operation is not valid (e.g., when trying to add a non-internal attribute
    before saving the entry)
    """
    pass

class InternalError(AidaException):
    """
    Error raised when there is an internal error of Aida.
    """
    pass

class ValidationError(AidaException):
    """
    Error raised when there is an error during the validation phase
    of a property. 
    """
    pass

class ConfigurationError(AidaException):
    """
    Error raised when there is a configuration error in Aida.
    """
    pass

class DBContentError(AidaException):
    """
    Raised when the content of the DB is not valid.
    This should never happen if the user does not play directly
    with the DB.
    """
    pass

class AuthenticationError(AidaException):
    """
    Raised when a user tries to access a resource for which it is
    not authenticated, e.g. an aidauser tries to access a computer
    for which there is no entry in the AuthInfo table.
    """
    pass

