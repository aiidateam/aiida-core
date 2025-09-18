###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module for the workflow parameter type"""

import typing as t

if t.TYPE_CHECKING:
    from aiida.orm.utils.loaders import WorkflowEntityLoader

from .identifier import IdentifierParamType

__all__ = ('WorkflowParamType',)


class WorkflowParamType(IdentifierParamType):
    """The ParamType for identifying WorkflowNode entities or its subclasses"""

    name = 'WorkflowNode'

    @property
    def orm_class_loader(self) -> 'type[WorkflowEntityLoader]':
        """Return the orm entity loader class, which should be a subclass of OrmEntityLoader. This class is supposed
        to be used to load the entity for a given identifier

        :return: the orm entity loader class for this ParamType
        """
        from aiida.orm.utils.loaders import WorkflowEntityLoader

        return WorkflowEntityLoader
