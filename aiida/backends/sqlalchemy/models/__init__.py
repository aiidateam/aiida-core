# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module to define the database models for the SqlAlchemy backend."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from sqlalchemy_utils import force_instant_defaults

# SqlAlchemy does not set default values for table columns upon construction of a new instance, but will only do so
# when storing the instance. Any attributes that do not have a value but have a defined default, will be populated with
# this default. This does mean however, that before the instance is stored, these attributes are undefined, for example
# the UUID of a new instance. In Django this behavior is the opposite and more in intuitive because when one creates for
# example a `Node` instance in memory, it will already have a UUID. The following function call will force SqlAlchemy to
# behave the same as Django and set model attribute defaults upon instantiation.
force_instant_defaults()
