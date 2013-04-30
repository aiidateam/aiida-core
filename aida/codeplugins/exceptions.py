from aida.common.exceptions import ValidationError

class InputValidationError(ValidationError):
    """
    The input data for a calculation did not validate (e.g., missing
    required input data, wrong data, ...)
    """
    def __init__(self,message):
        super(InputValidationError,self).__init__(message)
        self.message = message

class OutputParsingError(ValidationError):
    def __init__(self,message):
        super(OutputParsingError,self).__init__(message)
        self.message = message
        self.module = "generic"

class FailedJobError(ValidationError):
    def __init__(self,message=''):
        super(FailedJobError,self).__init__(message)
        self.message = message
        self.module = "generic"
        
