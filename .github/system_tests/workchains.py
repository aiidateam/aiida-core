# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
# pylint: disable=invalid-name
"""Work chain implementations for testing purposes."""
from aiida.common import AttributeDict
from aiida.engine import (
    BaseRestartWorkChain,
    ExitCode,
    ProcessHandlerReport,
    ToContext,
    WorkChain,
    append_,
    calcfunction,
    process_handler,
    while_,
    workfunction,
)
from aiida.engine.persistence import ObjectLoader
from aiida.orm import Int, List, Str
from aiida.plugins import CalculationFactory

ArithmeticAddCalculation = CalculationFactory('core.arithmetic.add')


class ArithmeticAddBaseWorkChain(BaseRestartWorkChain):
    """Ridiculous work chain around `AritmethicAddCalculation` with automated sanity checks and error handling."""

    _process_class = ArithmeticAddCalculation

    @classmethod
    def define(cls, spec):
        """Define the process specification."""
        super().define(spec)
        spec.expose_inputs(ArithmeticAddCalculation, namespace='add')
        spec.expose_outputs(ArithmeticAddCalculation)
        spec.outline(
            cls.setup,
            while_(cls.should_run_process)(
                cls.run_process,
                cls.inspect_process,
            ),
            cls.results,
        )
        spec.exit_code(100, 'ERROR_TOO_BIG', message='The sum was too big.')
        spec.exit_code(110, 'ERROR_ENABLED_DOOM', message='You should not have done that.')

    def setup(self):
        """Call the `setup` of the `BaseRestartWorkChain` and then create the inputs dictionary in `self.ctx.inputs`.

        This `self.ctx.inputs` dictionary will be used by the `BaseRestartWorkChain` to submit the process in the
        internal loop.
        """
        super().setup()
        self.ctx.inputs = AttributeDict(self.exposed_inputs(ArithmeticAddCalculation, 'add'))

    @process_handler(priority=500)
    def sanity_check_not_too_big(self, node):
        """My puny brain cannot deal with numbers that I cannot count on my hand."""
        if node.is_finished_ok and node.outputs.sum > 10:
            return ProcessHandlerReport(True, self.exit_codes.ERROR_TOO_BIG)  # pylint: disable=no-member

    @process_handler(priority=460, enabled=False)
    def disabled_handler(self, node):  # pylint: disable=unused-argument
        """By default this is not enabled and so should never be called, irrespective of exit codes of sub process."""
        return ProcessHandlerReport(True, self.exit_codes.ERROR_ENABLED_DOOM)  # pylint: disable=no-member

    @process_handler(priority=450, exit_codes=ExitCode(1000, 'Unicorn encountered'))
    def a_magic_unicorn_appeared(self, node):  # pylint: disable=no-self-argument,no-self-use
        """As we all know unicorns do not exist so we should never have to deal with it."""
        raise RuntimeError('this handler should never even have been called')

    @process_handler(priority=400, exit_codes=ArithmeticAddCalculation.exit_codes.ERROR_NEGATIVE_NUMBER)
    def error_negative_sum(self, node):
        """What even is a negative number, how can I have minus three melons?!."""
        self.ctx.inputs.x = Int(abs(node.inputs.x.value))
        self.ctx.inputs.y = Int(abs(node.inputs.y.value))
        return ProcessHandlerReport(True)


class NestedWorkChain(WorkChain):
    """
    Nested workchain which creates a workflow where the nesting level is equal to its input.
    """

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input('inp', valid_type=Int)
        spec.outline(cls.do_submit, cls.finalize)
        spec.output('output', valid_type=Int, required=True)

    def do_submit(self):
        if self.should_submit():
            self.report('Submitting nested workchain.')
            return ToContext(workchain=append_(self.submit(NestedWorkChain, inp=self.inputs.inp - 1)))

    def should_submit(self):
        return int(self.inputs.inp) > 0

    def finalize(self):
        """Attach the outputs."""
        if self.should_submit():
            self.report('Getting sub-workchain output.')
            sub_workchain = self.ctx.workchain[0]
            self.out('output', Int(sub_workchain.outputs.output + 1).store())
        else:
            self.report('Bottom-level workchain reached.')
            self.out('output', Int(0).store())


class SerializeWorkChain(WorkChain):
    """Work chain that serializes inputs."""

    @classmethod
    def define(cls, spec):
        super().define(spec)

        spec.input('test', valid_type=Str, serializer=lambda x: Str(ObjectLoader().identify_object(x)))

        spec.outline(cls.echo)
        spec.outputs.dynamic = True

    def echo(self):
        self.out('output', self.inputs.test)


class NestedInputNamespace(WorkChain):
    """Work chain with nested namespace."""

    @classmethod
    def define(cls, spec):
        super().define(spec)

        spec.input('foo.bar.baz', valid_type=Int)
        spec.output('output', valid_type=Int)
        spec.outline(cls.do_echo)

    def do_echo(self):
        self.out('output', self.inputs.foo.bar.baz)


class ListEcho(WorkChain):
    """Work chain that simply echos a `List` input."""

    @classmethod
    def define(cls, spec):
        super().define(spec)

        spec.input('list', valid_type=List)
        spec.output('output', valid_type=List)

        spec.outline(cls.do_echo)

    def do_echo(self):
        self.out('output', self.inputs.list)


class DynamicNonDbInput(WorkChain):
    """Work chain with dynamic non_db inputs."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input_namespace('namespace', dynamic=True)
        spec.output('output', valid_type=List)
        spec.outline(cls.do_test)

    def do_test(self):
        input_list = self.inputs.namespace.input
        assert isinstance(input_list, list)
        assert not isinstance(input_list, List)
        self.out('output', List(list=list(input_list)).store())


class DynamicDbInput(WorkChain):
    """Work chain with dynamic input namespace."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input_namespace('namespace', dynamic=True)
        spec.output('output', valid_type=Int)
        spec.outline(cls.do_test)

    def do_test(self):
        input_value = self.inputs.namespace.input
        assert isinstance(input_value, Int)
        self.out('output', input_value)


class DynamicMixedInput(WorkChain):
    """Work chain with dynamic mixed input."""

    @classmethod
    def define(cls, spec):
        super().define(spec)
        spec.input_namespace('namespace', dynamic=True)
        spec.output('output', valid_type=Int)
        spec.outline(cls.do_test)

    def do_test(self):
        """Run the test."""
        input_non_db = self.inputs.namespace.inputs['input_non_db']
        input_db = self.inputs.namespace.inputs['input_db']
        assert isinstance(input_non_db, int)
        assert not isinstance(input_non_db, Int)
        assert isinstance(input_db, Int)
        self.out('output', Int(input_db + input_non_db).store())


class CalcFunctionRunnerWorkChain(WorkChain):
    """
    WorkChain which calls an InlineCalculation in its step.
    """

    @classmethod
    def define(cls, spec):
        super().define(spec)

        spec.input('input', valid_type=Int)
        spec.output('output', valid_type=Int)

        spec.outline(cls.do_run)

    def do_run(self):
        self.out('output', increment(self.inputs.input))


class WorkFunctionRunnerWorkChain(WorkChain):
    """
    WorkChain which calls a workfunction in its step
    """

    @classmethod
    def define(cls, spec):
        super().define(spec)

        spec.input('input', valid_type=Str)
        spec.output('output', valid_type=Str)

        spec.outline(cls.do_run)

    def do_run(self):
        self.out('output', echo(self.inputs.input))


@workfunction
def echo(value):
    return value


@calcfunction
def increment(data):
    return Int(data + 1)
