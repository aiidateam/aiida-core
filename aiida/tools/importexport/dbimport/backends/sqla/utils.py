# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
""" Utility functions for import of AiiDA entities using SQLAlchemy backend """

from uuid import UUID


def validate_uuid(given_uuid):
    """
    A simple check for the UUID validity.
    """
    try:
        parsed_uuid = UUID(given_uuid, version=4)
    except ValueError:
        # If not a valid UUID
        return False

    # Check if there was any kind of conversion of the hex during
    # the validation
    return str(parsed_uuid) == given_uuid
