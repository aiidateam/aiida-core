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
Module for custom click param type group
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import click

from aiida.cmdline.utils.decorators import with_dbenv

from .identifier import IdentifierParamType


class GroupParamType(IdentifierParamType):
    """The ParamType for identifying Group entities or its subclasses."""

    name = 'Group'

    def __init__(self, create_if_not_exist=False):
        self._create_if_not_exist = create_if_not_exist
        super(GroupParamType, self).__init__()

    @property
    def orm_class_loader(self):
        """
        Return the orm entity loader class, which should be a subclass of OrmEntityLoader. This class is supposed
        to be used to load the entity for a given identifier

        :return: the orm entity loader class for this ParamType
        """
        from aiida.orm.utils.loaders import GroupEntityLoader
        return GroupEntityLoader

    @with_dbenv()
    def convert(self, value, param, ctx):
        from aiida.orm import Group, GroupTypeString
        try:
            group = super(GroupParamType, self).convert(value, param, ctx)
        except click.BadParameter:
            if self._create_if_not_exist:
                group = Group(label=value, type_string=GroupTypeString.USER.value)
            else:
                raise

        return group
