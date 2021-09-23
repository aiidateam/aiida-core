# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
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

from aiida.common.exceptions import FeatureNotAvailable, InputValidationError, ValidationError


class RestValidationError(ValidationError):
    """
    If validation error in code
    E.g. more than one node available for given uuid
    """


class RestInputValidationError(InputValidationError):
    """
    If inputs passed in query strings are wrong
    """


class RestFeatureNotAvailable(FeatureNotAvailable):
    """
    If endpoint is not emplemented for given node type
    """
