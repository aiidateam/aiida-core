###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# start-marker for docs
"""Code snippets for the "How to extend workflows" section."""

from aiida.engine import ToContext, WorkChain, calcfunction
from aiida.orm import AbstractCode, Bool, Int
from aiida.plugins.factories import CalculationFactory

ArithmeticAddCalculation = CalculationFactory('core.arithmetic.add')


@calcfunction
def multiply(x, y):
    return x * y


@calcfunction
def is_even(number):
    """Check if a number is even."""
    return Bool(number % 2 == 0)


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

        return ToContext(addition=future)

    def validate_result(self):
        """Make sure the result is not negative."""
        result = self.ctx.addition.outputs.sum

        if result.value < 0:
            return self.exit_codes.ERROR_NEGATIVE_NUMBER

    def result(self):
        """Add the result to the outputs."""
        self.out('result', self.ctx.addition.outputs.sum)


class BadMultiplyAddIsEvenWorkChain(WorkChain):
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
            cls.is_even,
        )
        spec.output('is_even', valid_type=Bool)
        spec.exit_code(400, 'ERROR_NEGATIVE_NUMBER', message='The result is a negative number.')

    def multiply(self):
        """Multiply two integers."""
        self.ctx.product = multiply(self.inputs.x, self.inputs.y)

    def add(self):
        """Add two numbers using the `ArithmeticAddCalculation` calculation job plugin."""
        inputs = {'x': self.ctx.product, 'y': self.inputs.z, 'code': self.inputs.code}
        future = self.submit(ArithmeticAddCalculation, **inputs)

        return ToContext(addition=future)

    def validate_result(self):
        """Make sure the result is not negative."""
        result = self.ctx.addition.outputs.sum

        if result.value < 0:
            return self.exit_codes.ERROR_NEGATIVE_NUMBER

    def is_even(self):
        """Check if the result is even."""
        result_is_even = is_even(self.ctx.addition.outputs.sum)

        self.out('is_even', result_is_even)


class BetterMultiplyAddIsEvenWorkChain(WorkChain):
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
            cls.multiply_add,
            cls.is_even,
        )
        spec.output('is_even', valid_type=Bool)

    def multiply_add(self):
        """Multiply two integers and add a third."""
        inputs = {'x': self.inputs.x, 'y': self.inputs.y, 'z': self.inputs.z, 'code': self.inputs.code}
        future = self.submit(MultiplyAddWorkChain, **inputs)

        return ToContext(multi_addition=future)

    def is_even(self):
        """Check if the result is even."""
        result_is_even = is_even(self.ctx.multi_addition.outputs.result)

        self.out('is_even', result_is_even)


class MultiplyAddIsEvenWorkChain(WorkChain):
    """WorkChain to multiply two numbers and add a third, for testing and demonstration purposes."""

    @classmethod
    def define(cls, spec):
        """Specify inputs and outputs."""
        super().define(spec)
        spec.expose_inputs(MultiplyAddWorkChain, namespace='multiply_add')
        spec.outline(
            cls.multiply_add,
            cls.is_even,
        )
        spec.output('is_even', valid_type=Bool)

    def multiply_add(self):
        """Multiply two integers and add a third."""
        future = self.submit(MultiplyAddWorkChain, **self.exposed_inputs(MultiplyAddWorkChain, 'multiply_add'))
        return ToContext(multi_addition=future)

    def is_even(self):
        """Check if the result is even."""
        result_is_even = is_even(self.ctx.multi_addition.outputs.result)

        self.out('is_even', result_is_even)


class ResultMultiplyAddIsEvenWorkChain(WorkChain):
    """WorkChain to multiply two numbers and add a third, for testing and demonstration purposes."""

    @classmethod
    def define(cls, spec):
        """Specify inputs and outputs."""
        super().define(spec)
        spec.expose_inputs(MultiplyAddWorkChain, namespace='multiply_add')
        spec.outline(
            cls.multiply_add,
            cls.is_even,
        )
        spec.expose_outputs(MultiplyAddWorkChain)
        spec.output('is_even', valid_type=Bool)

    def multiply_add(self):
        """Multiply two integers and add a third."""
        future = self.submit(MultiplyAddWorkChain, **self.exposed_inputs(MultiplyAddWorkChain, 'multiply_add'))

        return ToContext(multi_addition=future)

    def is_even(self):
        """Check if the result is even."""
        result_is_even = is_even(self.ctx.multi_addition.outputs.result)

        self.out_many(self.exposed_outputs(self.ctx.multi_addition, MultiplyAddWorkChain))
        self.out('is_even', result_is_even)
