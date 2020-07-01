# -*- coding: utf-8 -*-
from aiida.engine import CalcJob

class ArithmeticAddCalculation(CalcJob):
    """Implementation of CalcJob to add two numbers for testing and demonstration purposes."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('x', valid_type=orm.Int, help='The left operand.')
        spec.input('y', valid_type=orm.Int, help='The right operand.')
