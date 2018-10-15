# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Legacy workflow parameter type."""
from __future__ import absolute_import
from .identifier import IdentifierParamType


class LegacyWorkflowParamType(IdentifierParamType):
    """The ParamType for identifying legacy workflows."""

    name = 'LegacyWorkflow'

    @property
    def orm_class_loader(self):
        """Return the orm entity loader class which should be a subclass of OrmEntityLoader."""
        from aiida.orm.utils.loaders import LegacyWorkflowLoader
        return LegacyWorkflowLoader
