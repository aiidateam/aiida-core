#!/usr/bin/env runaiida
# -*- coding: utf-8 -*-

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/.. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file"
__version__ = "0.6.0"
__authors__ = "The AiiDA team."

from aiida.backends.utils import load_dbenv, is_dbenv_loaded

if not is_dbenv_loaded():
    load_dbenv()

from aiida.workflows2.util import to_db_type
from aiida.workflows2.async import async, asyncd
from aiida.workflows2.wf import wf
from aiida.workflows2.fragmented_wf import FragmentedWorkfunction, ResultToContext


@wf
def f1(inp=None):
    p2 = async(f2, a=inp)
    a = 1
    r2 = p2.result()
    print("a={}".format(a))
    print("r2={}".format(r2))
    r1 = r2.copy()

    return {'r1': r1['r2']}


@wf
def f2(a):
    return {'r2': a}


class F1(FragmentedWorkfunction):
    @staticmethod
    def _define(spec):
        spec.input('inp')

    definition = """
s1
s2
"""

    def s1(self, ctx):
        p2 = asyncd(F2, a=self._inputs['inp'])
        ctx.a = 1
        ResultToContext(r2=p2)

    def s2(self, ctx):
        print("a={}".format(ctx.a))
        print("r2={}".format(ctx.r2))
        r1 = ctx.r2.copy()

        self._out("r1", r1['r2'])


class F2(FragmentedWorkfunction):
    @staticmethod
    def _define(spec):
        spec.input('a')

    definition = """
s1
"""

    def s1(self):
        self._out("r2", self._inputs.a)


if __name__ == '__main__':
    five = to_db_type(5)

    r1 = f1(five)
    R1 = F1().run(inputs={'inp': five})
