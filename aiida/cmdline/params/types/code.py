# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Module to define the custom click type for code."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import click
from .identifier import IdentifierParamType


class CodeParamType(IdentifierParamType):
    """
    The ParamType for identifying Code entities or its subclasses
    """

    name = 'Code'

    def __init__(self, sub_classes=None, entry_point=None):
        """Construct the param type

        :param sub_classes: specify a tuple of Code sub classes to narrow the query set
        :param entry_point: specify an optional calculation entry point that the Code's input plugin should match
        """
        super(CodeParamType, self).__init__(sub_classes)
        self._entry_point = entry_point

    @property
    def orm_class_loader(self):
        """
        Return the orm entity loader class, which should be a subclass of OrmEntityLoader. This class is supposed
        to be used to load the entity for a given identifier

        :return: the orm entity loader class for this ParamType
        """
        from aiida.orm.utils.loaders import CodeEntityLoader
        return CodeEntityLoader

    def convert(self, value, param, ctx):
        code = super(CodeParamType, self).convert(value, param, ctx)

        if code and self._entry_point is not None:
            entry_point = code.get_input_plugin_name()
            if entry_point != self._entry_point:
                raise click.BadParameter('the retrieved Code<{}> has plugin type "{}" while "{}" is required'.format(
                    code.pk, entry_point, self._entry_point))

        return code
