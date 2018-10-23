# -*- coding: utf-8 -*-
from aiida.orm.data.bool import Bool
from aiida.orm.data.float import Float
from aiida.orm.data.int import Int
from aiida.work import WorkChain 

class ChildWorkChain(WorkChain):
    @classmethod
    def define(cls, spec):
        super(ChildWorkChain, cls).define(spec)
        spec.input('a', valid_type=Int)
        spec.input('b', valid_type=Float)
        spec.input('c', valid_type=Bool)
        spec.outline(cls.do_run)
        spec.output('d', valid_type=Int)
        spec.output('e', valid_type=Float)
        spec.output('f', valid_type=Bool)

    def do_run(self):
        self.out('d', self.inputs.a)
        self.out('e', self.inputs.b)
        self.out('f', self.inputs.c)
