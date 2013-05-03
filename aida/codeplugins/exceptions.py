from aida.common.exceptions import ValidationError

class OutputParsingError(ValidationError):
    pass

class FailedJobError(ValidationError):
    pass        
