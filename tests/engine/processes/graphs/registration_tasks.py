###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Importable process tasks for testing source binding aliases."""

from aiida import orm
from aiida.calculations.arithmetic.add import ArithmeticAddCalculation
from aiida.engine import WorkChain, task_from_calcjob, task_from_workchain


class RegisteredWorkChain(WorkChain):
    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('pair.left', valid_type=orm.Int)
        spec.input('pair.right', valid_type=orm.Int, default=lambda: orm.Int(3))
        spec.input('pair.optional', valid_type=orm.Str, required=False, help='Optional label')
        spec.input_namespace('extra', dynamic=True, required=False, valid_type=orm.Int)
        spec.output('sums.total', valid_type=orm.Int)
        spec.outline(cls.combine)

    def combine(self):
        self.out('sums.total', orm.Int(self.inputs.pair.left + self.inputs.pair.right).store())


class RegisteredCalculation(ArithmeticAddCalculation):
    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.inputs['metadata']['options']['resources'].default = {'num_machines': 1}


combined = task_from_workchain(RegisteredWorkChain)
calculation = task_from_calcjob(RegisteredCalculation)
