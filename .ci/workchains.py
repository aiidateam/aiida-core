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
from aiida.orm.data.int import Int
from aiida.orm.data.list import List
from aiida.orm.data.str import Str
from aiida.orm.calculation.inline import make_inline
from aiida.work import submit
from aiida.work.persistence import ObjectLoader
from aiida.work.workfunctions import workfunction
from aiida.work.workchain import WorkChain, ToContext, append_

class NestedWorkChain(WorkChain):
    """
    Nested workchain which creates a workflow where the nesting level is equal to its input.
    """
    @classmethod
    def define(cls, spec):
        super(NestedWorkChain, cls).define(spec)
        spec.input('inp', valid_type=Int)
        spec.outline(
            cls.do_submit,
            cls.finalize
        )
        spec.output('output', valid_type=Int, required=True)

    def do_submit(self):
        if self.should_submit():
            self.report('Submitting nested workchain.')
            return ToContext(
                workchain=append_(self.submit(
                    NestedWorkChain,
                    inp=self.inputs.inp - 1
                ))
            )

    def should_submit(self):
        return int(self.inputs.inp) > 0

    def finalize(self):
        if self.should_submit():
            self.report('Getting sub-workchain output.')
            sub_workchain = self.ctx.workchain[0]
            self.out('output', sub_workchain.out.output + 1)
        else:
            self.report('Bottom-level workchain reached.')
            self.out('output', Int(0))

class SerializeWorkChain(WorkChain):
    @classmethod
    def define(cls, spec):
        super(SerializeWorkChain, cls).define(spec)

        spec.input(
            'test',
            valid_type=Str,
            serializer=lambda x: Str(ObjectLoader().identify_object(x))
        )

        spec.outline(cls.echo)

    def echo(self):
        self.out('output', self.inputs.test)

class NestedInputNamespace(WorkChain):
    @classmethod
    def define(cls, spec):
        super(NestedInputNamespace, cls).define(spec)

        spec.input('foo.bar.baz', valid_type=Int)
        spec.output('output', valid_type=Int)
        spec.outline(cls.do_echo)

    def do_echo(self):
        self.out('output', self.inputs.foo.bar.baz)

class ListEcho(WorkChain):
    @classmethod
    def define(cls, spec):
        super(ListEcho, cls).define(spec)

        spec.input('list', valid_type=List)
        spec.output('output', valid_type=List)

        spec.outline(cls.do_echo)

    def do_echo(self):
        self.out('output', self.inputs.list)

class DynamicNonDbInput(WorkChain):
    @classmethod
    def define(cls, spec):
        super(DynamicNonDbInput, cls).define(spec)
        spec.input_namespace('namespace', dynamic=True)
        spec.output('output', valid_type=List)
        spec.outline(cls.do_test)

    def do_test(self):
        input_list = self.inputs.namespace.input
        assert isinstance(input_list, list)
        assert not isinstance(input_list, List)
        self.out('output', List(list=list(input_list)))

class DynamicDbInput(WorkChain):
    @classmethod
    def define(cls, spec):
        super(DynamicDbInput, cls).define(spec)
        spec.input_namespace('namespace', dynamic=True)
        spec.output('output', valid_type=Int)
        spec.outline(cls.do_test)

    def do_test(self):
        input_value = self.inputs.namespace.input
        assert isinstance(input_value, Int)
        self.out('output', input_value)

class DynamicMixedInput(WorkChain):
    @classmethod
    def define(cls, spec):
        super(DynamicMixedInput, cls).define(spec)
        spec.input_namespace('namespace', dynamic=True)
        spec.output('output', valid_type=Int)
        spec.outline(cls.do_test)

    def do_test(self):
        input_non_db = self.inputs.namespace.inputs['input_non_db']
        input_db = self.inputs.namespace.inputs['input_db']
        assert isinstance(input_non_db, int)
        assert not isinstance(input_non_db, Int)
        assert isinstance(input_db, Int)
        self.out('output', input_db + input_non_db)

class InlineCalcRunnerWorkChain(WorkChain):
    """
    WorkChain which calls an InlineCalculation in its step.
    """
    @classmethod
    def define(cls, spec):
        super(InlineCalcRunnerWorkChain, cls).define(spec)

        spec.input('input', valid_type=Str)
        spec.output('output', valid_type=Str)

        spec.outline(cls.do_run)

    def do_run(self):
        self.out('output', echo_inline(input_string=self.inputs.input)[1]['output'])

class WorkFunctionRunnerWorkChain(WorkChain):
    """
    WorkChain which calls a workfunction in its step
    """
    @classmethod
    def define(cls, spec):
        super(WorkFunctionRunnerWorkChain, cls).define(spec)

        spec.input('input', valid_type=Str)
        spec.output('output', valid_type=Str)

        spec.outline(cls.do_run)

    def do_run(self):
        self.out('output', echo(self.inputs.input))

@workfunction
def echo(value):
    return value

@make_inline
def echo_inline(input_string):
    return {'output': input_string}
