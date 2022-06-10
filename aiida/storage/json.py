# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Customized JSON encoders/decoders to be used for reading/writing to the database."""
from functools import partial
import json

__all__ = ('loads', 'dumps')


def _as_complex(dct):
    """
    Reconstruct complex numbers if the `__complex__` key
    is found
    """
    if '__complex__' in dct:
        return complex(dct['real'], dct['imag'])
    return dct


class ComplexEncoder(json.JSONEncoder):
    """
    Json Encoder with support for complex numbers.
    These are encoded as a dictionary with the reserved
    key `__complex__` used to identify them
    """

    def default(self, obj):  #pylint: disable=arguments-renamed
        if isinstance(obj, complex):
            return {'__complex__': True, 'real': obj.real, 'imag': obj.imag}
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


dumps = partial(json.dumps, cls=ComplexEncoder)
loads = partial(json.loads, object_hook=_as_complex)
