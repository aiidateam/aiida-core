# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six

from aiida.common.exceptions import ValidationError
from aiida.common.exceptions import NotExistent

# The separator for sub-fields (for JSON stored values).Keys are not allowed
# to contain the separator even if the
_sep = "."


def validate_key(key):
    """
    Validate the key string to check if it is valid (e.g., if it does not
    contain the separator symbol.).

    :return: None if the key is valid
    :raise aiida.common.ValidationError: if the key is not valid
    """
    if not isinstance(key, six.string_types):
        raise ValidationError("The key must be a string.")
    if not key:
        raise ValidationError("The key cannot be an empty string.")
    if _sep in key:
        raise ValidationError("The separator symbol '{}' cannot be present "
                              "in the key of this field.".format(_sep))


def get_value_of_sub_field(key, original_get_value):
    """
    Get the value that corresponds to sub-fields of dictionaries stored in a
    JSON. For example, if there is a dictionary {'b': 'c'} stored as value of
    the key 'a'
    value 'a'
    :param key: The key that can be simple, a string, or complex, a set of keys
    separated by the separator value.
    :param original_get_value: The function that should be called to get the
    original value (which can be a dictionary too).
    :return: The value that correspond to the complex (or not) key.
    :raise aiida.common.NotExistent: If the key doesn't correspond to a value
    """
    keys = list()
    if _sep in key:
        keys.extend(key.split(_sep))
    else:
        keys.append(key)

    if len(keys) == 1:
        return original_get_value(keys[0])
    else:
        try:
            curr_val = original_get_value(keys[0])
            curr_pos = 1
            while curr_pos < len(keys):
                curr_val = curr_val[keys[curr_pos]]
                curr_pos += 1

            return curr_val
        except TypeError as KeyError:
            raise NotExistent("The sub-field {} doesn't correspond "
                              "to a value.".format(key))
