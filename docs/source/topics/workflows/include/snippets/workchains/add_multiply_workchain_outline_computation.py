# -*- coding: utf-8 -*-
from aiida.engine import WorkChain
from aiida.orm import Int


class AddAndMultiplyWorkChain(WorkChain):

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('x')
        spec.input('y')
        spec.input('z')
        spec.outline(
            cls.add,
            cls.multiply,
            cls.results,
        )
        spec.output('result')

    def add(self):
        self.ctx.sum = self.inputs.x + self.inputs.y

    def multiply(self):
        self.ctx.product = self.ctx.sum * self.inputs.z

    def results(self):
        self.out('result', Int(self.ctx.product))
