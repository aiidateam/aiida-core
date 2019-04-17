# -*- coding: utf-8 -*-
from aiida.engine import WorkChain
from aiida.orm.nodes.data import to_aiida_type
# The basic types need to be loaded such that they are registered with
# the 'to_aiida_type' function.
from aiida.orm.nodes.data.base import *


class SerializeWorkChain(WorkChain):

    @classmethod
    def define(cls, spec):
        super(SerializeWorkChain, cls).define(spec)

        spec.input('a', serializer=to_aiida_type)
        spec.input('b', serializer=to_aiida_type)
        spec.input('c', serializer=to_aiida_type)

        spec.outline(cls.echo)

    def echo(self):
        self.out('a', self.inputs.a)
        self.out('b', self.inputs.b)
        self.out('c', self.inputs.c)
