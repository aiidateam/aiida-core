# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tools to operate on `TrajectoryData` nodes."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.engine import calcfunction


@calcfunction
def _get_aiida_structure_inline(trajectory, parameters):
    """
    Creates :py:class:`aiida.orm.nodes.data.structure.StructureData` using ASE.

    .. note:: requires ASE module.
    """
    kwargs = {}
    if parameters is not None:
        kwargs = parameters.get_dict()
    if 'index' not in kwargs.keys() or kwargs['index'] is None:
        raise ValueError("Step index is not supplied for TrajectoryData")
    return {'structure': trajectory.get_step_structure(**kwargs)}
