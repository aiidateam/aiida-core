# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Implementation of the MultiplyAddWorkChain for testing and demonstration purposes."""
from aiida.orm import Code, Int
from aiida.engine import calcfunction, WorkChain, ToContext


@calcfunction
def multiply(x, y):
    return x * y


class MultiplyAddWorkChain(WorkChain):
    """WorkChain to perform basic arithmetic for testing and demonstration purposes."""

    @classmethod
    def define(cls, spec):
        """Specify inputs and outputs."""
        super(MultiplyAddWorkChain, cls).define(spec)
        spec.input('x', valid_type=Int)
        spec.input('y', valid_type=Int)
        spec.input('z', valid_type=Int)
        spec.input('code', valid_type=Code)
        spec.outline(
            cls.multiply,
            cls.add,
            cls.result
        )
        spec.output('result', valid_type=Int)

    def multiply(self):
        """Multiply two integers."""
        self.ctx.multiple = multiply(self.inputs.x, self.inputs.y)

    def add(self):
        """Add two numbers with the ArithmeticAddCalculation process."""

        builder = self.inputs.code.get_builder()

        builder.x = self.ctx.multiple
        builder.y = self.inputs.z

        future = self.submit(builder)

        return ToContext({"addition": future})

    def result(self):
        self.out('result', self.ctx["addition"].get_outgoing().get_node_by_label("sum"))
