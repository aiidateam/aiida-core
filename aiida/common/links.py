# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module to define valid link types."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from enum import Enum
import six

from .lang import isidentifier, type_check

__all__ = ('LinkType', 'validate_link_label')


class LinkType(Enum):
    """A simple enum of allowed link types."""

    CREATE = 'create'
    RETURN = 'return'
    INPUT_CALC = 'input_calc'
    INPUT_WORK = 'input_work'
    CALL_CALC = 'call_calc'
    CALL_WORK = 'call_work'


def validate_link_label(link_label):
    """Validate the given link label.

    Valid link labels adhere to the following restrictions:

        * Has to be a valid python identifier
        * Can only contain alphanumeric characters and underscores
        * Can not start or end with an underscore

    :raises TypeError: if the link label is not a string type
    :raises ValueError: if the link label is invalid
    """
    import re

    message = 'invalid link label `{}`: should be string type but is instead: {}'.format(link_label, type(link_label))
    type_check(link_label, six.string_types, message)

    allowed_character_set = '[a-zA-Z0-9_]'

    if link_label.endswith('_'):
        raise ValueError('cannot end with an underscore')

    if link_label.startswith('_'):
        raise ValueError('cannot start with an underscore')

    if re.sub(allowed_character_set, '', link_label):
        raise ValueError('only alphanumeric and underscores are allowed')

    if not isidentifier(link_label):
        raise ValueError('not a valid python identifier')
