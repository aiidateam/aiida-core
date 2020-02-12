# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Utility functions for AiiDA ORM implementations."""

__all__ = ('get_attr',)


def get_attr(attrs, key):
    """ Get the attribute that corresponds to the given key"""
    path = key.split('.')

    dict_ = attrs
    for part in path:
        if part.isdigit():
            part = int(part)
        # Let it raise the appropriate exception
        dict_ = dict_[part]

    return dict_
