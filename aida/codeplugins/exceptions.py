from aidalib.exceptions import ValidationError

class InputValidationError(ValidationError):
    """
    The input data for a calculation did not validate (e.g., missing
    required input data, wrong data, ...)
    """
    pass
