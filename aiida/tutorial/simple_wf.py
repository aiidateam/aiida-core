# -*- coding: utf-8 -*-
from aiida.workflows2.fragmented_wf import (FragmentedWorkfunction,
                                            ResultToContext)
from aiida.orm.data.parameter import ParameterData

__copyright__ = u"Copyright (c), This file is part of the AiiDA platform. For further information please visit http://www.aiida.net/. All rights reserved."
__license__ = "MIT license, see LICENSE.txt file."
__authors__ = "The AiiDA team."
__version__ = "0.7.1.1"




class SimpleWF(FragmentedWorkfunction):
    @classmethod
    def _define(cls, spec):
        spec.input("params", valid_type=ParameterData)
        spec.outline(
            cls.square,
            cls.get_results
        )
        spec.dynamic_output()

    def square(self, ctx):
        print "squaring"
        number = self.inputs.params.dict.number
        ctx.result = number ** 2

    def get_results(self, ctx):
        print "The result is", ctx.result
