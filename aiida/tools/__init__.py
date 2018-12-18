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
Tools to operate on AiiDA ORM class instances

What functionality should go directly in the ORM class in `aiida.orm` and what in `aiida.tools`?

    - The ORM class should define basic functions to set and get data from the object
    - More advanced functionality to operate on the ORM class instances can be placed in `aiida.tools`
        to prevent the ORM namespace from getting too cluttered.

.. note:: Modules in this sub package may require the database environment to be loaded

"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.tools.dbimporters import DbImporter, DbImporterFactory
from aiida.tools.data.array.kpoints import get_kpoints_path, get_explicit_kpoints_path
from aiida.tools.data.structure import structure_to_spglib_tuple, spglib_tuple_to_structure
