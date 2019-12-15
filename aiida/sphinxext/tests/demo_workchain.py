# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""This module defines an example workchain for the aiida-workchain documentation directive."""

# This import is here to test an error which is triggered if
# can_document_member raises an exception.

from aiida.engine import WorkChain, if_, while_
from aiida.orm import Bool, Float, Int


class DemoWorkChain(WorkChain):  # pylint: disable=abstract-method
    """
    A demo workchain to show how the workchain auto-documentation works.
    """

    @classmethod
    def define(cls, spec):
        super().define(spec)

        spec.input('x', valid_type=Float, help='First input argument.')
        spec.input('y.z', valid_type=Int, help='Input in a separate namespace.')
        spec.input_namespace('y.nested', help='A nested namespace.')
        spec.input('y.nested.a', valid_type=Int, help='An input in the nested namespace.')
        spec.input_namespace('nsp', help='A separate namespace, ``nsp``.')
        spec.input_namespace('nsp2',)
        spec.output('z', valid_type=Bool, help='Output of the demoworkchain.')

        spec.outline(  # yapf: disable
            cls.start,
            while_(cls.some_check)(
                cls.do_something,
                if_(cls.another_check)(
                    cls.do_something_else
                )),
            cls.finalize
        )

    def start(self):
        pass

    def some_check(self):
        pass

    def another_check(self):
        pass

    def do_something(self):
        pass

    def do_something_else(self):
        pass

    def finalize(self):
        pass


class NormalClass:  # pylint: disable=too-few-public-methods
    """This is here to check that we didn't break the regular autoclass."""
