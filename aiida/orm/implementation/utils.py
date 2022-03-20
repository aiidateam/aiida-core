# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utility methods for backend non-specific implementations."""
from collections.abc import Iterable, Mapping
from decimal import Decimal
import math
import numbers

from aiida.common import exceptions
from aiida.common.constants import AIIDA_FLOAT_PRECISION

# This separator character is reserved to indicate nested fields in node attribute and extras dictionaries and
# therefore is not allowed in individual attribute or extra keys.
FIELD_SEPARATOR = '.'

__all__ = ('validate_attribute_extra_key', 'clean_value')


def validate_attribute_extra_key(key):
    """Validate the key for an entity attribute or extra.

    :raise aiida.common.ValidationError: if the key is not a string or contains reserved separator character
    """
    if not key or not isinstance(key, str):
        raise exceptions.ValidationError('key for attributes or extras should be a string')

    if FIELD_SEPARATOR in key:
        raise exceptions.ValidationError(
            f'key for attributes or extras cannot contain the character `{FIELD_SEPARATOR}`'
        )


def clean_value(value):
    """
    Get value from input and (recursively) replace, if needed, all occurrences
    of BaseType AiiDA data nodes with their value, and List with a standard list.
    It also makes a deep copy of everything
    The purpose of this function is to convert data to a type which can be serialized and deserialized
    for storage in the DB without its value changing.

    Note however that there is no logic to avoid infinite loops when the
    user passes some perverse recursive dictionary or list.
    In any case, however, this would not be storable by AiiDA...

    :param value: A value to be set as an attribute or an extra
    :return: a "cleaned" value, potentially identical to value, but with
        values replaced where needed.
    """
    # Must be imported in here to avoid recursive imports
    from aiida.orm import BaseType

    def clean_builtin(val):
        """
        A function to clean build-in python values (`BaseType`).

        It mainly checks that we don't store NaN or Inf.
        """
        # This is a whitelist of all the things we understand currently
        if val is None or isinstance(val, (bool, str)):
            return val

        # This fixes #2773 - in python3, ``numpy.int64(-1)`` cannot be json-serialized
        # Note that `numbers.Integral` also match booleans but they are already returned above
        if isinstance(val, numbers.Integral):
            return int(val)

        if isinstance(val, numbers.Real) and (math.isnan(val) or math.isinf(val)):
            # see https://www.postgresql.org/docs/current/static/datatype-json.html#JSON-TYPE-MAPPING-TABLE
            raise exceptions.ValidationError('nan and inf/-inf can not be serialized to the database')

        # This is for float-like types, like ``numpy.float128`` that are not json-serializable
        # Note that `numbers.Real` also match booleans but they are already returned above
        if isinstance(val, (numbers.Real, Decimal)):
            string_representation = f'{{:.{AIIDA_FLOAT_PRECISION}g}}'.format(val)
            new_val = float(string_representation)
            if 'e' in string_representation and new_val.is_integer():
                # This is indeed often quite unexpected, because it is going to change the type of the data
                # from float to int. But anyway clean_value is changing some types, and we are also bound to what
                # our current backends do.
                # Currently, in both Django and SQLA (with JSONB attributes), if we store 1.e1, ..., 1.e14, 1.e15,
                # they will be stored as floats; instead 1.e16, 1.e17, ... will all be stored as integer anyway,
                # even if we don't run this clean_value step.
                # So, for consistency, it's better if we do the conversion ourselves here, and we do it for a bit
                # smaller numbers than python+[SQL+JSONB] would do (the AiiDA float precision is here 14), so the
                # results are consistent, and the hashing will work also after a round trip as expected.
                return int(new_val)
            return new_val

        # Anything else we do not understand and we refuse
        raise exceptions.ValidationError(f'type `{type(val)}` is not supported as it is not json-serializable')

    if isinstance(value, BaseType):
        return clean_builtin(value.value)

    if isinstance(value, Mapping):
        # Check dictionary before iterables
        return {k: clean_value(v) for k, v in value.items()}

    if (isinstance(value, Iterable) and not isinstance(value, str)):
        # list, tuple, ... but not a string
        # This should also properly take care of dealing with the
        # basedatatypes.List object
        return [clean_value(v) for v in value]

    # If I don't know what to do I just return the value
    # itself - it's not super robust, but relies on duck typing
    # (e.g. if there is something that behaves like an integer
    # but is not an integer, I still accept it)

    return clean_builtin(value)
