# -*- coding: utf-8 -*-
from aiida.engine.workchain import WorkChain
from aiida.orm import Int


class AddAndMultiplyWorkChain(WorkChain):

    @classmethod
    def define(cls, spec):
        super(AddAndMultiplyWorkChain, cls).define(spec)
        spec.input('a', valid_type=Int)
        spec.input('b', valid_type=Int)
        spec.input('c', valid_type=Int)
        spec.outline(
            cls.add,
            cls.multiply,
            cls.results,
        )
        spec.output('result', valid_type=Int)

    def add(self):
        self.ctx.sum = self.inputs.a + self.inputs.b

    def multiply(self):
        self.ctx.product = self.ctx.sum * self.inputs.c

    def results(self):
        self.out('result', Int(self.ctx.product))
