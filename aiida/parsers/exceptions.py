from aiida.common.exceptions import ValidationError, ParsingError

class OutputParsingError(ParsingError):
    pass

class FailedJobError(ValidationError):
    pass        
