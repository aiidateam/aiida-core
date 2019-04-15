# -*- coding: utf-8 -*-
from aiida.backends.utils import load_dbenv, is_dbenv_loaded

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.1.1"

if not is_dbenv_loaded():
    load_dbenv()

from aiida.workflows2.fragmented_wf import *
from aiida.workflows2.run import run


class W(FragmentedWorkfunction):
    @classmethod
    def _define(cls, spec):
        spec.outline(
            cls.start,
            cls.s2,
            if_(cls.cond1)(
                cls.s3,
                cls.s4,
            ).elif_(cls.cond3)(
                cls.s11
            ).else_(
                cls.s5,
                cls.s6
            ),
            while_(cls.cond2)(
                cls.s7,
                cls.s8
            ),
            cls.s9
        )


    def start(self, ctx):
        print "s1"
        ctx.v = 1

        return 1, 2, 3, 4

    def s2(self, ctx):
        print "s2"
        ctx.v = 2
        ctx.w = 2

    def cond1(self, ctx):
        return ctx.v == 3

    def s3(self, ctx):
        print "s3"

    def s4(self, ctx):
        print "s4"

    def s5(self, ctx):
        print "s5"

    def s6(self, ctx):
        print "s6"

    #        f = async(slow)
    #        return Wait(f)

    def cond2(self, ctx):
        return ctx.w < 10

    def cond3(self, ctx):
        return True

    def s7(self, ctx):
        print " s7"
        ctx.w += 1
        print "w=", ctx.w

    def s8(self, ctx):
        print "s8"

    def s9(self, ctx):
        print "s9, end"

    def s11(self, ctx):
        pass


if __name__ == '__main__':
    run(W)
