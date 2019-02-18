# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Test module parameter type for click."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import click


class TestModuleParamType(click.ParamType):
    """Parameter type to represent a unittest module."""

    name = 'test module'

    @staticmethod
    def get_test_modules():
        """Returns a list of known test modules."""
        from aiida.backends.tests import get_db_test_names

        prefix_db = 'db'
        modules_db = get_db_test_names()
        modules_base = ['aiida.cmdline', 'aiida.common', 'aiida.schedulers', 'aiida.transports']

        test_modules = {}

        for module in modules_base:
            test_modules[module] = None

        for module in modules_db:
            test_modules['{}.{}'.format(prefix_db, module)] = [module]

        test_modules[prefix_db] = modules_db

        return test_modules

    def complete(self, ctx, incomplete):  # pylint: disable=unused-argument,no-self-use
        """
        Return possible completions based on an incomplete value

        :returns: list of tuples of valid entry points (matching incomplete) and a description
        """
        return [(test_module, '') for test_module in self.get_test_modules() if test_module.startswith(incomplete)]
