###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# start-marker for docs
"""Implementation of the MultiplyAddWorkChain for testing and demonstration purposes."""

from aiida.calculations.arithmetic.add import ArithmeticAddCalculation
from aiida.engine import ToContext, WorkChain, calcfunction
from aiida.orm import AbstractCode, Int


@calcfunction
def multiply(x, y):
    return x * y


class MultiplyAddWorkChain(WorkChain):
    """WorkChain to multiply two numbers and add a third, for testing and demonstration purposes."""

    @classmethod
    def define(cls, spec):
        """Specify inputs and outputs."""
        super().define(spec)
        spec.input('x', valid_type=Int)
        spec.input('y', valid_type=Int)
        spec.input('z', valid_type=Int)
        spec.input('code', valid_type=AbstractCode)
        spec.outline(
            cls.multiply,
            cls.add,
            cls.validate_result,
            cls.result,
        )
        spec.output('result', valid_type=Int)
        spec.exit_code(400, 'ERROR_NEGATIVE_NUMBER', message='The result is a negative number.')

    def multiply(self):
        """Multiply two integers."""
        self.ctx.product = multiply(self.inputs.x, self.inputs.y)

    def add(self):
        """Add two numbers using the `ArithmeticAddCalculation` calculation job plugin."""
        inputs = {'x': self.ctx.product, 'y': self.inputs.z, 'code': self.inputs.code}
        future = self.submit(ArithmeticAddCalculation, **inputs)
        self.report(f'Submitted the `ArithmeticAddCalculation`: {future}')
        return ToContext(addition=future)

    def validate_result(self):
        """Make sure the result is not negative."""
        result = self.ctx.addition.outputs.sum

        if result.value < 0:
            return self.exit_codes.ERROR_NEGATIVE_NUMBER

    def result(self):
        """Add the result to the outputs."""
        self.out('result', self.ctx.addition.outputs.sum)
