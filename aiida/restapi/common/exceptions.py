# -*- coding: utf-8 -*-
"""
This file contains the exceptions that are raised by the RESTapi at the
highest level, namely that of the interaction with the client. Their
specificity resides into the fact that they return a message that is embedded
into the HTTP response.
Example:
    .../api/v1/nodes/ ... (TODO compete this with an actual example)

Other errors arising at deeper level, e.g. those raised by the QueryBuilder
or internal errors, are not embedded into the HTTP response.
"""

from aiida.common.exceptions import ValidationError, InputValidationError

class RestValidationError(ValidationError):
    """
    document with an example
    """
    pass

class RestInputValidationError(InputValidationError):
    """
    document with an example
    """
    pass