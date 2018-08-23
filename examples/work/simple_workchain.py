# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import absolute_import
from __future__ import print_function
from aiida import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()


from aiida import work
from aiida.orm.data.int import Int
import aiida.work.globals as globals

persistence = globals.get_persistence()


class ProdSum(work.WorkChain):
    @classmethod
    def define(cls, spec):
        super(ProdSum, cls).define(spec)
        spec.input("a")
        spec.input("b")
        spec.input("c")
        spec.outline(cls.add, cls.prod)

    def add(self):
        self.ctx.sum = self.inputs.a + self.inputs.b

    def prod(self):
        result = self.ctx.sum * self.inputs.c
        self.out("result", result)


class ProdSumBroken(ProdSum):
    def prod(self):
        raise RuntimeError("Break")


p = ProdSumBroken(inputs={'a': Int(2), 'b': Int(3), 'c': Int(4)})
pid = p.pid
persistence.persist_process(p)
try:
    p.play()
except RuntimeError:
    pass

cp = persistence.load_checkpoint(pid)
p = ProdSum.recreate_from(cp)

p.play()

print(p.outputs)
