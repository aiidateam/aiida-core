# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
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

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from aiida.common.exceptions import ValidationError, InputValidationError, \
    FeatureNotAvailable


class RestValidationError(ValidationError):
    """
    document with an example
    """


class RestInputValidationError(InputValidationError):
    """
    document with an example
    """


class RestFeatureNotAvailable(FeatureNotAvailable):
    pass
