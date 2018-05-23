# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
from aiida.common.links import LinkType
from aiida.backends.testbase import AiidaTestCase
from aiida.orm.data.bool import get_true_node
from aiida.orm.data.int import Int
from aiida.orm import load_node
from aiida.orm.calculation.function import FunctionCalculation
from aiida.work import run, run_get_node, submit, workfunction, Process

DEFAULT_INT = 256
DEFAULT_LABEL = 'Default label'
DEFAULT_DESCRIPTION = 'Default description'
CUSTOM_LABEL = 'Custom label'
CUSTOM_DESCRIPTION = 'Custom description'


class TestWf(AiidaTestCase):

    def setUp(self):
        super(TestWf, self).setUp()
        self.assertIsNone(Process.current())

        @workfunction
        def wf_return_input(inp):
            return {'result': inp}

        @workfunction
        def wf_return_true():
            return get_true_node()

        @workfunction
        def wf_args(a):
            return a

        @workfunction
        def wf_args_with_default(a=Int(DEFAULT_INT)):
            return a

        @workfunction
        def wf_kwargs(**kwargs):
            return kwargs

        @workfunction
        def wf_args_and_kwargs(a, **kwargs):
            result = {'a': a}
            result.update(kwargs)
            return result

        @workfunction
        def wf_args_and_default(a, b=Int(DEFAULT_INT)):
            return {'a': a, 'b': b}

        @workfunction
        def wf_default_label_description(a=Int(DEFAULT_INT), label=DEFAULT_LABEL, description=DEFAULT_DESCRIPTION):
            return a

        self.wf_return_input = wf_return_input
        self.wf_return_true = wf_return_true
        self.wf_args = wf_args
        self.wf_args_with_default = wf_args_with_default
        self.wf_kwargs = wf_kwargs
        self.wf_args_and_kwargs = wf_args_and_kwargs
        self.wf_args_and_default = wf_args_and_default
        self.wf_default_label_description = wf_default_label_description

    def tearDown(self):
        super(TestWf, self).tearDown()
        self.assertIsNone(Process.current())

    def test_wf_varargs(self):
        """
        Variadic arguments are not supported and should raise
        """
        with self.assertRaises(ValueError):
            @workfunction
            def wf_varargs(*args):
                return get_true_node()

    def test_wf_args(self):
        """
        Simple workfunction that defines a single positional argument
        """
        INPUT = 1

        with self.assertRaises(ValueError):
            result = self.wf_args()

        result = self.wf_args(a=Int(INPUT))
        self.assertTrue(isinstance(result, Int))
        self.assertEquals(result, INPUT)

    def test_wf_args_with_default(self):
        """
        Simple workfunction that defines a single argument with a default
        """
        INPUT = 1

        result = self.wf_args_with_default()
        self.assertTrue(isinstance(result, Int))
        self.assertEquals(result, Int(DEFAULT_INT))

        result = self.wf_args_with_default(a=Int(INPUT))
        self.assertTrue(isinstance(result, Int))
        self.assertEquals(result, INPUT)

    def test_wf_kwargs(self):
        """
        Simple workfunction that defines keyword arguments
        """
        INPUT = {'a': Int(DEFAULT_INT)}

        result = self.wf_kwargs()
        self.assertTrue(isinstance(result, dict))
        self.assertEquals(result, {})

        result = self.wf_kwargs(**INPUT)
        self.assertTrue(isinstance(result, dict))
        self.assertEquals(result, INPUT)

    def test_wf_args_and_kwargs(self):
        """
        Simple workfunction that defines a positional argument and keyword arguments
        """
        ARGS_INPUT = (Int(DEFAULT_INT),)
        KWARGS_INPUT = {'b': Int(INPUT)}

        result = self.wf_args_and_kwargs(*ARGS_INPUT)
        self.assertTrue(isinstance(result, dict))
        self.assertEquals(result, {'a': ARGS_INPUT[0]})

        result = self.wf_args_and_kwargs(*ARGS_INPUT, **KWARGS_INPUT)
        self.assertTrue(isinstance(result, dict))
        self.assertEquals(result, {'a': ARGS_INPUT[0], 'b': Int(DEFAULT_INT)})

    def test_wf_args_and_kwargs(self):
        """
        Simple workfunction that defines a positional argument and an argument with a default
        """
        INPUT = 1
        ARGS_INPUT_DEFAULT = (Int(DEFAULT_INT),)
        ARGS_INPUT_EXPLICIT = (Int(DEFAULT_INT), Int(INPUT))

        result = self.wf_args_and_default(*ARGS_INPUT_DEFAULT)
        self.assertTrue(isinstance(result, dict))
        self.assertEquals(result, {'a': ARGS_INPUT_DEFAULT[0], 'b': Int(DEFAULT_INT)})

        result = self.wf_args_and_default(*ARGS_INPUT_EXPLICIT)
        self.assertTrue(isinstance(result, dict))
        self.assertEquals(result, {'a': ARGS_INPUT_EXPLICIT[0], 'b': ARGS_INPUT_EXPLICIT[1]})

    def test_wf_args_passing_kwargs(self):
        """
        A function that does not explicitly define kwargs, should not be able to be called with
        keyword arguments that were not explicitly defined
        """
        INPUT = 1

        with self.assertRaises(ValueError):
            result = self.wf_args(a=Int(INPUT), b=Int(INPUT))

    def test_wf_set_label_description(self):
        """
        Verify that the label and description can be set for all workfunction variants
        """
        result, node = self.wf_args.run_get_node(a=Int(DEFAULT_INT), label=CUSTOM_LABEL, description=CUSTOM_DESCRIPTION)
        self.assertEquals(node.label, CUSTOM_LABEL)
        self.assertEquals(node.description, CUSTOM_DESCRIPTION)

        result, node = self.wf_args_with_default.run_get_node(label=CUSTOM_LABEL, description=CUSTOM_DESCRIPTION)
        self.assertEquals(node.label, CUSTOM_LABEL)
        self.assertEquals(node.description, CUSTOM_DESCRIPTION)

        result, node = self.wf_kwargs.run_get_node(label=CUSTOM_LABEL, description=CUSTOM_DESCRIPTION)
        self.assertEquals(node.label, CUSTOM_LABEL)
        self.assertEquals(node.description, CUSTOM_DESCRIPTION)

        result, node = self.wf_args_and_kwargs.run_get_node(a=Int(DEFAULT_INT), label=CUSTOM_LABEL,
                                                            description=CUSTOM_DESCRIPTION)
        self.assertEquals(node.label, CUSTOM_LABEL)
        self.assertEquals(node.description, CUSTOM_DESCRIPTION)

        result, node = self.wf_args_and_default.run_get_node(a=Int(DEFAULT_INT), label=CUSTOM_LABEL,
                                                             description=CUSTOM_DESCRIPTION)
        self.assertEquals(node.label, CUSTOM_LABEL)
        self.assertEquals(node.description, CUSTOM_DESCRIPTION)

    def test_wf_default_label_description(self):
        """
        Verify that a workfunction can define a default label and description but they can be overriden by the
        user by explicitly passing them as keyword arguments
        """
        result, node = self.wf_default_label_description.run_get_node(a=Int(DEFAULT_INT))
        self.assertEquals(node.label, DEFAULT_LABEL)
        self.assertEquals(node.description, DEFAULT_DESCRIPTION)

        result, node = self.wf_default_label_description.run_get_node(label=CUSTOM_LABEL,
                                                                      description=CUSTOM_DESCRIPTION)
        self.assertEquals(node.label, CUSTOM_LABEL)
        self.assertEquals(node.description, CUSTOM_DESCRIPTION)

    def test_finish_status(self):
        """
        If a workfunction reaches the FINISHED process state, it has to have been successful
        which means that the finish status always has to be 0
        """
        result, node = self.wf_args_with_default.run_get_node()
        self.assertEquals(node.finish_status, 0)
        self.assertEquals(node.is_finished_ok, True)
        self.assertEquals(node.is_failed, False)

    def test_launchers(self):
        """
        Verify that the various launchers are working
        """
        result = run(self.wf_return_true)
        self.assertTrue(result)

        result, node = run_get_node(self.wf_return_true)
        self.assertTrue(result)
        self.assertEqual(result, get_true_node())
        self.assertTrue(isinstance(node, FunctionCalculation))

        with self.assertRaises(AssertionError):
            submit(self.wf_return_true)

    def test_default_linkname(self):
        """
        Verify that a workfunction that returns a single Data node, a default link label
        will be used that can be accessed both through the getattr as through the getitem
        method of the OutputManager of the node
        """
        INPUT = 1

        result, node = run_get_node(self.wf_args, a=Int(INPUT))
        self.assertEquals(node.out.result, INPUT)
        self.assertEquals(getattr(node.out, Process.SINGLE_RETURN_LINKNAME), INPUT)
        self.assertEquals(node.out[Process.SINGLE_RETURN_LINKNAME], INPUT)

    def test_simple_workflow(self):
        @workfunction
        def add(a, b):
            return a + b

        @workfunction
        def mul(a, b):
            return a * b

        @workfunction
        def add_mul_wf(a, b, c):
            return mul(add(a, b), c)

        result = add_mul_wf(Int(3), Int(4), Int(5))

    def test_wf_links(self):
        @workfunction
        def a():
            pass

        @workfunction
        def b():
            return Int(5)

        @workfunction
        def c():
            a()
            return b()

        result, calc = run.get_node(c)

        self.assertIn(result.get_inputs(link_type=LinkType.CREATE)[0].pk, [c.pk for c in calc.called])
        self.assertEqual(calc.get_outputs(link_type=LinkType.RETURN)[0].pk, result.pk)

    def test_hashes(self):
        result, w1 = self.wf_return_input.run_get_node(inp=Int(2))
        result, w2 = self.wf_return_input.run_get_node(inp=Int(2))
        self.assertEqual(w1.get_hash(), w2.get_hash())

    def test_hashes_different(self):
        result, w1 = self.wf_return_input.run_get_node(inp=Int(2))
        result, w2 = self.wf_return_input.run_get_node(inp=Int(3))
        self.assertNotEqual(w1.get_hash(), w2.get_hash())

    def _check_hash_consistent(self, pid):
        wc = load_node(pid)
        self.assertEqual(wc.get_hash(), wc.get_extra('_aiida_hash'))
