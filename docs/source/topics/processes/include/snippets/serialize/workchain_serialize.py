# -*- coding: utf-8 -*-
from aiida.engine import WorkChain
from aiida.orm import to_aiida_type


class SerializeWorkChain(WorkChain):

    @classmethod
    def define(cls, spec):
        super().define(spec)

        spec.input('a', serializer=to_aiida_type)
        spec.input('b', serializer=to_aiida_type)
        spec.input('c', serializer=to_aiida_type)

        spec.outline(cls.echo)

    def echo(self):
        self.out('a', self.inputs.a)
        self.out('b', self.inputs.b)
        self.out('c', self.inputs.c)
