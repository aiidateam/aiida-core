# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.orm.data.base import Int
from aiida.work.workchain import WorkChain, ToContext, append_

class ParentWorkChain(WorkChain):

    @classmethod
    def define(cls, spec):
        super(ParentWorkChain, cls).define(spec)
        spec.input('inp', valid_type=Int)
        spec.outline(
            cls.run_step,
            cls.results
        )
        spec.output('output', valid_type=Int, required=True)

    def run_step(self):
        inputs = {
            'inp': self.inputs.inp
        }
        running = self.submit(SubWorkChain, **inputs)
        self.report('launching SubWorkChain<{}>'.format(running.pk))

        return ToContext(workchains=append_(running))

    def results(self):
        subworkchain = self.ctx.workchains[0]
        self.out('output', subworkchain.out.output)

class SubWorkChain(WorkChain):

    @classmethod
    def define(cls, spec):
        super(SubWorkChain, cls).define(spec)
        spec.input('inp', valid_type=Int)
        spec.outline(
            cls.run_step
        )
        spec.output('output', valid_type=Int, required=True)

    def run_step(self):
        self.out('output', Int(self.inputs.inp.value * 2))