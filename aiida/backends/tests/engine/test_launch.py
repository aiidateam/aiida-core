# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida.backends.testbase import AiidaTestCase
from aiida.engine import run, run_get_node, run_get_pk, Process, WorkChain, calcfunction
from aiida.orm import Int, WorkChainNode, CalcFunctionNode


@calcfunction
def add(a, b):
    return a + b


class AddWorkChain(WorkChain):

    @classmethod
    def define(cls, spec):
        super(AddWorkChain, cls).define(spec)
        spec.input('a', valid_type=Int)
        spec.input('b', valid_type=Int)
        spec.outline(cls.add)
        spec.output('result', valid_type=Int)

    def add(self):
        self.out('result', self.inputs.a + self.inputs.b)


class TestLaunchers(AiidaTestCase):

    def setUp(self):
        super(TestLaunchers, self).setUp()
        self.assertIsNone(Process.current())
        self.a = Int(1)
        self.b = Int(2)
        self.result = 3

    def tearDown(self):
        super(TestLaunchers, self).tearDown()
        self.assertIsNone(Process.current())

    def test_calcfunction_run(self):
        result = run(add, a=self.a, b=self.b)
        self.assertEquals(result, self.result)

    def test_calcfunction_run_get_node(self):
        result, node = run_get_node(add, a=self.a, b=self.b)
        self.assertEquals(result, self.result)
        self.assertTrue(isinstance(node, CalcFunctionNode))

    def test_calcfunction_run_get_pk(self):
        result, pk = run_get_pk(add, a=self.a, b=self.b)
        self.assertEquals(result, self.result)
        self.assertTrue(isinstance(pk, int))

    def test_workchain_run(self):
        result = run(AddWorkChain, a=self.a, b=self.b)
        self.assertEquals(result['result'], self.result)

    def test_workchain_run_get_node(self):
        result, node = run_get_node(AddWorkChain, a=self.a, b=self.b)
        self.assertEquals(result['result'], self.result)
        self.assertTrue(isinstance(node, WorkChainNode))

    def test_workchain_run_get_pk(self):
        result, pk = run_get_pk(AddWorkChain, a=self.a, b=self.b)
        self.assertEquals(result['result'], self.result)
        self.assertTrue(isinstance(pk, int))

    def test_workchain_builder_run(self):
        builder = AddWorkChain.get_builder()
        builder.a = self.a
        builder.b = self.b
        result = run(builder)
        self.assertEquals(result['result'], self.result)

    def test_workchain_builder_run_get_node(self):
        builder = AddWorkChain.get_builder()
        builder.a = self.a
        builder.b = self.b
        result, node = run_get_node(builder)
        self.assertEquals(result['result'], self.result)
        self.assertTrue(isinstance(node, WorkChainNode))

    def test_workchain_builder_run_get_pk(self):
        builder = AddWorkChain.get_builder()
        builder.a = self.a
        builder.b = self.b
        result, pk = run_get_pk(builder)
        self.assertEquals(result['result'], self.result)
        self.assertTrue(isinstance(pk, int))
