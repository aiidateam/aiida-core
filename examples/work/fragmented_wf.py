# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.backends.utils import load_dbenv, is_dbenv_loaded


if not is_dbenv_loaded():
    load_dbenv()

from aiida.work.workchain import *
from aiida.work.run import run


class W(WorkChain):
    @classmethod
    def define(cls, spec):
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


    def start(self):
        print "s1"
        self.ctx.v = 1

        return 1, 2, 3, 4

    def s2(self):
        print "s2"
        self.ctx.v = 2
        self.ctx.w = 2

    def cond1(self):
        return self.ctx.v == 3

    def s3(self):
        print "s3"

    def s4(self):
        print "s4"

    def s5(self):
        print "s5"

    def s6(self):
        print "s6"

    #        f = async(slow)
    #        return Wait(f)

    def cond2(self):
        return self.ctx.w < 10

    def cond3(self):
        return True

    def s7(self):
        print " s7"
        self.ctx.w += 1
        print "w=", self.ctx.w

    def s8(self):
        print "s8"

    def s9(self):
        print "s9, end"

    def s11(self):
        pass


if __name__ == '__main__':
    run(W)
