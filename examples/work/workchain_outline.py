#!/usr/bin/env runaiida
# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""
This WorkChain example is a very contrived implementation of the infamous FizzBuzz problem, that serves to illustrate
the various logical blocks that one can incorporate into the outline of the workchain's spec.
"""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

from aiida.engine import WorkChain, run, while_, if_
from aiida.orm import Int


class OutlineWorkChain(WorkChain):

    @classmethod
    def define(cls, spec):
        super(OutlineWorkChain, cls).define(spec)
        spec.input('a', valid_type=Int)
        spec.outline(
            cls.setup,
            while_(cls.not_finished)(
                if_(cls.if_multiple_of_three_and_five)(
                    cls.report_fizz_buzz
                ).elif_(cls.if_multiple_of_five)(
                    cls.report_buzz
                ).elif_(cls.if_multiple_of_three)(
                    cls.report_fizz
                ).else_(
                    cls.report_number
                ),
                cls.decrement
            )
        )

    def setup(self):
        self.ctx.counter = abs(self.inputs.a.value)

    def not_finished(self):
        return self.ctx.counter > 0

    def if_multiple_of_three_and_five(self):
        return (self.ctx.counter % 3 == 0 and self.ctx.counter % 5 == 0)

    def if_multiple_of_five(self):
        return self.ctx.counter % 5 == 0

    def if_multiple_of_three(self):
        return self.ctx.counter % 3 == 0

    def report_fizz_buzz(self):
        print('FizzBuzz')

    def report_fizz(self):
        print('Fizz')

    def report_buzz(self):
        print('Buzz')

    def report_number(self):
        print(self.ctx.counter)

    def decrement(self):
        self.ctx.counter -= 1


def main():
    run(OutlineWorkChain, a=Int(16))


if __name__ == '__main__':
    main()
