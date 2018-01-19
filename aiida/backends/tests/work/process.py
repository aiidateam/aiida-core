# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
import threading
import aiida.work.utils as util
from aiida.backends.testbase import AiidaTestCase
from aiida.common.lang import override
from aiida.orm import load_node
from aiida.orm.data.base import Int, Str
from aiida.work.persistence import Persistence
from aiida.work.processes import Process, FunctionProcess
from aiida.work.run import run, submit
from aiida.work.workfunctions import workfunction
from aiida.work.test_utils import DummyProcess, BadOutput
from aiida.orm.data.frozendict import FrozenDict
from aiida import work
from aiida.work.launch import run, run_get_pid
from . import utils

# Create a test runner
runner = utils.create_test_runner()

class ProcessStackTest(work.Process):
    @override
    def _run(self):
        pass

    @override
    def on_create(self):
        super(ProcessStackTest, self).on_create()
        self._thread_id = threading.current_thread().ident

    @override
    def on_stop(self):
        # The therad must match the one used in on_create because process
        # stack is using thread local storage to keep track of who called who
        super(ProcessStackTest, self).on_stop()
        assert self._thread_id is threading.current_thread().ident


class TestProcess(AiidaTestCase):
    def setUp(self):
        super(TestProcess, self).setUp()

        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def tearDown(self):
        super(TestProcess, self).tearDown()

        self.assertEquals(len(util.ProcessStack.stack()), 0)

    def test_process_stack(self):
        run(ProcessStackTest)

    def test_inputs(self):
        with self.assertRaises(TypeError):
            run(BadOutput)

    def test_input_link_creation(self):
        dummy_inputs = ["1", "2", "3", "4"]

        inputs = {l: Int(l) for l in dummy_inputs}
        inputs['_store_provenance'] = True
        p = DummyProcess(inputs)

        for label, value in p._calc.get_inputs_dict().iteritems():
            self.assertTrue(label in inputs)
            self.assertEqual(int(label), int(value.value))
            dummy_inputs.remove(label)

        # Make sure there are no other inputs
        self.assertFalse(dummy_inputs)

    def test_none_input(self):
        # Check that if we pass no input the process runs fine
        run(DummyProcess)

    def test_seal(self):
        pid = run_get_pid(DummyProcess).pid
        self.assertTrue(load_node(pk=pid).is_sealed)

    def test_description(self):
        dp = DummyProcess(inputs={'_description': "Rockin' process"})
        self.assertEquals(dp.calc.description, "Rockin' process")

        with self.assertRaises(ValueError):
            DummyProcess(inputs={'_description': 5})

    def test_label(self):
        dp = DummyProcess(inputs={'_label': 'My label'})
        self.assertEquals(dp.calc.label, 'My label')

        with self.assertRaises(ValueError):
            DummyProcess(inputs={'_label': 5})

    def test_work_calc_finish(self):
        p = DummyProcess()
        self.assertFalse(p.calc.has_finished_ok())
        run(p)
        self.assertTrue(p.calc.has_finished_ok())

    def test_calculation_input(self):
        @work.workfunction
        def simple_wf():
            return {'a': Int(6), 'b': Int(7)}

        outputs, pid = run_get_pid(simple_wf)
        calc = load_node(pid)

        dp = DummyProcess(inputs={'calc': calc})
        run(dp)

        input_calc = dp.calc.get_inputs_dict()['calc']
        self.assertTrue(isinstance(input_calc, FrozenDict))
        self.assertEqual(input_calc['a'], outputs['a'])

    def test_save_instance_state(self):
        proc = DummyProcess()
        # Save the instance state
        bundle = work.Bundle(proc)

        proc2 = bundle.unbundle()


class TestFunctionProcess(AiidaTestCase):
    def test_fixed_inputs(self):
        def wf(a, b, c):
            return {'a': a, 'b': b, 'c': c}

        inputs = {'a': Int(4), 'b': Int(5), 'c': Int(6)}
        function_process_class = work.FunctionProcess.build(wf)
        self.assertEqual(run(function_process_class, **inputs), inputs)

    def test_kwargs(self):
        def wf_with_kwargs(**kwargs):
            return kwargs

        def wf_without_kwargs():
            return Int(4)

        def wf_fixed_args(a):
            return {'a': a}

        a = Int(4)
        inputs = {'a': a}

        function_process_class = work.FunctionProcess.build(wf_with_kwargs)
        outs = run(function_process_class, **inputs)
        self.assertEqual(outs, inputs)

        function_process_class = work.FunctionProcess.build(wf_without_kwargs)
        with self.assertRaises(ValueError):
            run(function_process_class, **inputs)

        function_process_class = work.FunctionProcess.build(wf_fixed_args)
        outs = run(function_process_class, **inputs)
        self.assertEqual(outs, inputs)


class TestExposeProcess(AiidaTestCase):

    def setUp(self):
        super(TestExposeProcess, self).setUp()

        class SimpleProcess(Process):
            @classmethod
            def define(cls, spec):
                super(SimpleProcess, cls).define(spec)
                spec.input('a', valid_type=Int, required=True)
                spec.input('b', valid_type=Int, required=True)

            @override
            def _run(self, **kwargs):
                pass

        self.SimpleProcess = SimpleProcess

    def test_expose_duplicate_unnamespaced(self):
        """
        As long as separate namespaces are used, the same Process should be
        able to be exposed more than once
        """
        SimpleProcess = self.SimpleProcess

        class ExposeProcess(Process):
            @classmethod
            def define(cls, spec):
                super(ExposeProcess, cls).define(spec)
                spec.expose_inputs(SimpleProcess)
                spec.expose_inputs(SimpleProcess, namespace='beta')

            @override
            def _run(self, **kwargs):
                assert 'a' in self.inputs
                assert 'b' in self.inputs
                assert 'a' in self.inputs.beta
                assert 'b' in self.inputs.beta
                assert self.inputs['a'] == Int(1)
                assert self.inputs['b'] == Int(2)
                assert self.inputs.beta['a'] == Int(3)
                assert self.inputs.beta['b'] == Int(4)
                self.submit(SimpleProcess, **self.exposed_inputs(SimpleProcess))
                self.submit(SimpleProcess, **self.exposed_inputs(SimpleProcess, namespace='beta'))

        run(ExposeProcess, **{'a': Int(1), 'b': Int(2), 'beta': {'a': Int(3), 'b': Int(4)}})

    def test_expose_duplicate_namespaced(self):
        """
        As long as separate namespaces are used, the same Process should be
        able to be exposed more than once
        """
        SimpleProcess = self.SimpleProcess

        class ExposeProcess(Process):
            @classmethod
            def define(cls, spec):
                super(ExposeProcess, cls).define(spec)
                spec.expose_inputs(SimpleProcess, namespace='alef')
                spec.expose_inputs(SimpleProcess, namespace='beta')

            @override
            def _run(self, **kwargs):
                assert 'a' in self.inputs.alef
                assert 'b' in self.inputs.alef
                assert 'a' in self.inputs.beta
                assert 'b' in self.inputs.beta
                assert self.inputs.alef['a'] == Int(1)
                assert self.inputs.alef['b'] == Int(2)
                assert self.inputs.beta['a'] == Int(3)
                assert self.inputs.beta['b'] == Int(4)
                self.submit(SimpleProcess, **self.exposed_inputs(SimpleProcess, namespace='alef'))
                self.submit(SimpleProcess, **self.exposed_inputs(SimpleProcess, namespace='beta'))

        run(ExposeProcess, **{'alef': {'a': Int(1), 'b': Int(2)}, 'beta': {'a': Int(3), 'b': Int(4)}})

    def test_expose_pass_same_dict(self):
        """
        Pass the same dict to two different namespaces.
        """
        SimpleProcess = self.SimpleProcess

        class ExposeProcess(Process):
            @classmethod
            def define(cls, spec):
                super(ExposeProcess, cls).define(spec)
                spec.expose_inputs(SimpleProcess, namespace='alef')
                spec.expose_inputs(SimpleProcess, namespace='beta')

            @override
            def _run(self, **kwargs):
                assert 'a' in self.inputs.alef
                assert 'b' in self.inputs.alef
                assert 'a' in self.inputs.beta
                assert 'b' in self.inputs.beta
                assert self.inputs.alef['a'] == Int(1)
                assert self.inputs.alef['b'] == Int(2)
                assert self.inputs.beta['a'] == Int(1)
                assert self.inputs.beta['b'] == Int(2)
                self.submit(SimpleProcess, **self.exposed_inputs(SimpleProcess, namespace='alef'))
                self.submit(SimpleProcess, **self.exposed_inputs(SimpleProcess, namespace='beta'))

        sub_inputs = {'a': Int(1), 'b': Int(2)}
        run(ExposeProcess, **{'alef': sub_inputs, 'beta': sub_inputs})

class TestNestedUnnamespacedExposedProcess(AiidaTestCase):

    def setUp(self):
        super(TestNestedUnnamespacedExposedProcess, self).setUp()

        class BaseProcess(Process):
            @classmethod
            def define(cls, spec):
                super(BaseProcess, cls).define(spec)
                spec.input('a', valid_type=Int, required=True)
                spec.input('b', valid_type=Int, default=Int(0))

            @override
            def _run(self, **kwargs):
                pass

        class SubProcess(Process):
            @classmethod
            def define(cls, spec):
                super(SubProcess, cls).define(spec)
                spec.expose_inputs(BaseProcess)
                spec.input('c', valid_type=Int, required=True)
                spec.input('d', valid_type=Int, default=Int(0))

            @override
            def _run(self, **kwargs):
                self.submit(BaseProcess, **self.exposed_inputs(BaseProcess))

        class ParentProcess(Process):
            @classmethod
            def define(cls, spec):
                super(ParentProcess, cls).define(spec)
                spec.expose_inputs(SubProcess)
                spec.input('e', valid_type=Int, required=True)
                spec.input('f', valid_type=Int, default=Int(0))

            @override
            def _run(self, **kwargs):
                self.submit(SubProcess, **self.exposed_inputs(SubProcess))

        self.BaseProcess = BaseProcess
        self.SubProcess = SubProcess
        self.ParentProcess = ParentProcess

    def test_base_process_valid_input(self):
        run(self.BaseProcess, **{'a': Int(0), 'b': Int(1)})

    def test_sub_process_valid_input(self):
        run(self.SubProcess, **{'a': Int(0), 'b': Int(1), 'c': Int(2), 'd': Int(3)})

    def test_parent_process_valid_input(self):
        run(self.ParentProcess, **{'a': Int(0), 'b': Int(1), 'c': Int(2), 'd': Int(3), 'e': Int(4), 'f': Int(5)})

    def test_base_process_missing_input(self):
        with self.assertRaises(ValueError):
            run(self.BaseProcess, **{'b': Int(1)})

    def test_sub_process_missing_input(self):
        with self.assertRaises(ValueError):
            run(self.SubProcess, **{'b': Int(1)})

    def test_parent_process_missing_input(self):
        with self.assertRaises(ValueError):
            run(self.ParentProcess, **{'b': Int(1)})

    def test_base_process_invalid_type_input(self):
        with self.assertRaises(ValueError):
            run(self.BaseProcess, **{'a': Int(0), 'b': Str(1)})

    def test_sub_process_invalid_type_input(self):
        with self.assertRaises(ValueError):
            run(self.SubProcess, **{'a': Int(0), 'b': Int(1), 'c': Int(2), 'd': Str(3)})

    def test_parent_process_invalid_type_input(self):
        with self.assertRaises(ValueError):
            run(self.ParentProcess, **{'a': Int(0), 'b': Int(1), 'c': Int(2), 'd': Int(3), 'e': Int(4), 'f': Str(5)})


class TestNestedNamespacedExposedProcess(AiidaTestCase):

    def setUp(self):
        super(TestNestedNamespacedExposedProcess, self).setUp()

        class BaseProcess(Process):
            @classmethod
            def define(cls, spec):
                super(BaseProcess, cls).define(spec)
                spec.input('a', valid_type=Int, required=True)
                spec.input('b', valid_type=Int, default=Int(0))

            @override
            def _run(self, **kwargs):
                pass

        class SubProcess(Process):
            @classmethod
            def define(cls, spec):
                super(SubProcess, cls).define(spec)
                spec.expose_inputs(BaseProcess, namespace='base')
                spec.input('c', valid_type=Int, required=True)
                spec.input('d', valid_type=Int, default=Int(0))

            @override
            def _run(self, **kwargs):
                self.submit(BaseProcess, **self.exposed_inputs(BaseProcess, namespace='base'))

        class ParentProcess(Process):
            @classmethod
            def define(cls, spec):
                super(ParentProcess, cls).define(spec)
                spec.expose_inputs(SubProcess, namespace='sub')
                spec.input('e', valid_type=Int, required=True)
                spec.input('f', valid_type=Int, default=Int(0))

            @override
            def _run(self, **kwargs):
                self.submit(SubProcess, **self.exposed_inputs(SubProcess, namespace='sub'))

        self.BaseProcess = BaseProcess
        self.SubProcess = SubProcess
        self.ParentProcess = ParentProcess

    def test_sub_process_valid_input(self):
        run(self.SubProcess, **{'base': {'a': Int(0), 'b': Int(1)}, 'c': Int(2)})

    def test_parent_process_valid_input(self):
        run(self.ParentProcess, **{'sub': {'base': {'a': Int(0), 'b': Int(1)}, 'c': Int(2)}, 'e': Int(4)})

    def test_sub_process_missing_input(self):
        with self.assertRaises(ValueError):
            run(self.SubProcess, **{'c': Int(2)})

    def test_parent_process_missing_input(self):
        with self.assertRaises(ValueError):
            run(self.ParentProcess, **{'e': Int(4)})

class TestIncludeExposeProcess(AiidaTestCase):

    def setUp(self):
        super(TestIncludeExposeProcess, self).setUp()

        class SimpleProcess(Process):
            @classmethod
            def define(cls, spec):
                super(SimpleProcess, cls).define(spec)
                spec.input('a', valid_type=Int, required=True)
                spec.input('b', valid_type=Int, required=False)

            @override
            def _run(self, **kwargs):
                pass

        self.SimpleProcess = SimpleProcess

    def test_include_none(self):
        SimpleProcess = self.SimpleProcess

        class ExposeProcess(Process):
            @classmethod
            def define(cls, spec):
                super(ExposeProcess, cls).define(spec)
                spec.expose_inputs(SimpleProcess, include=[])
                spec.input('c', valid_type=Int, required=True)

            @override
            def _run(self, **kwargs):
                self.submit(SimpleProcess, a=Int(1), b=Int(2), **self.exposed_inputs(SimpleProcess))

    def test_include_one(self):
        SimpleProcess = self.SimpleProcess

        class ExposeProcess(Process):
            @classmethod
            def define(cls, spec):
                super(ExposeProcess, cls).define(spec)
                spec.expose_inputs(SimpleProcess, include=['a'])
                spec.input('c', valid_type=Int, required=True)

            @override
            def _run(self, **kwargs):
                self.submit(SimpleProcess, b=Int(2), **self.exposed_inputs(SimpleProcess))

        run(ExposeProcess, **{'a': Int(1), 'c': Int(3)})

class TestExcludeExposeProcess(AiidaTestCase):

    def setUp(self):
        super(TestExcludeExposeProcess, self).setUp()

        class SimpleProcess(Process):
            @classmethod
            def define(cls, spec):
                super(SimpleProcess, cls).define(spec)
                spec.input('a', valid_type=Int, required=True)
                spec.input('b', valid_type=Int, required=False)

            @override
            def _run(self, **kwargs):
                pass

        self.SimpleProcess = SimpleProcess

    def test_exclude_valid(self):
        SimpleProcess = self.SimpleProcess

        class ExposeProcess(Process):
            @classmethod
            def define(cls, spec):
                super(ExposeProcess, cls).define(spec)
                spec.expose_inputs(SimpleProcess, exclude=('b',))
                spec.input('c', valid_type=Int, required=True)

            @override
            def _run(self, **kwargs):
                self.submit(SimpleProcess, **self.exposed_inputs(SimpleProcess))

        run(ExposeProcess, **{'a': Int(1), 'c': Int(3)})

    def test_exclude_invalid(self):
        SimpleProcess = self.SimpleProcess

        class ExposeProcess(Process):
            @classmethod
            def define(cls, spec):
                super(ExposeProcess, cls).define(spec)
                spec.expose_inputs(SimpleProcess, exclude=('a',))

            @override
            def _run(self, **kwargs):
                self.submit(SimpleProcess, **self.exposed_inputs(SimpleProcess))

        with self.assertRaises(ValueError):
            run(ExposeProcess, **{'b': Int(2), 'c': Int(3)})


class TestUnionInputsExposeProcess(AiidaTestCase):

    def setUp(self):
        super(TestUnionInputsExposeProcess, self).setUp()

        class SubOneProcess(Process):
            @classmethod
            def define(cls, spec):
                super(SubOneProcess, cls).define(spec)
                spec.input('common', valid_type=Int, required=True)
                spec.input('sub_one', valid_type=Int, required=True)

            @override
            def _run(self, **kwargs):
                assert self.inputs['common'] == Int(1)
                assert self.inputs['sub_one'] == Int(2)

        class SubTwoProcess(Process):
            @classmethod
            def define(cls, spec):
                super(SubTwoProcess, cls).define(spec)
                spec.input('common', valid_type=Int, required=True)
                spec.input('sub_two', valid_type=Int, required=True)

            @override
            def _run(self, **kwargs):
                assert self.inputs['common'] == Int(1)
                assert self.inputs['sub_two'] == Int(3)

        class ExposeProcess(Process):
            @classmethod
            def define(cls, spec):
                super(ExposeProcess, cls).define(spec)
                spec.expose_inputs(SubOneProcess)
                spec.expose_inputs(SubTwoProcess)

            @override
            def _run(self, **kwargs):
                self.submit(SubOneProcess, **self.exposed_inputs(SubOneProcess))
                self.submit(SubTwoProcess, **self.exposed_inputs(SubTwoProcess))

        self.SubOneProcess = SubOneProcess
        self.SubTwoProcess = SubTwoProcess
        self.ExposeProcess = ExposeProcess

    def test_inputs_union_valid(self):
        run(self.ExposeProcess, **{'common': Int(1), 'sub_one': Int(2), 'sub_two': Int(3)})

    def test_inputs_union_invalid(self):
        inputs = {'sub_one': Int(2), 'sub_two': Int(3)}
        with self.assertRaises(ValueError):
            run(self.ExposeProcess, **inputs)


class TestAgglomerateExposeProcess(AiidaTestCase):
    """
    Often one wants to run multiple instances of a certain Process, where some but
    not all the inputs will be the same or "common". By using a combination of include and
    exclude on the same Process, the user can define separate namespaces for the specific
    inputs, while exposing the shared or common inputs on the base level namespace. The
    method exposed_inputs will by default agglomerate inputs that belong to the SubProcess
    starting from the base level and moving down the specified namespaces, overriding duplicate
    inputs as they are found.

    The exposed_inputs provides the flag 'agglomerate' which can be set to False to turn off
    this behavior and only return the inputs in the specified namespace
    """

    def setUp(self):
        super(TestAgglomerateExposeProcess, self).setUp()

        class SubProcess(Process):
            @classmethod
            def define(cls, spec):
                super(SubProcess, cls).define(spec)
                spec.input('common', valid_type=Int, required=True)
                spec.input('specific_a', valid_type=Int, required=True)
                spec.input('specific_b', valid_type=Int, required=True)

            @override
            def _run(self, **kwargs):
                pass

        class ExposeProcess(Process):
            @classmethod
            def define(cls, spec):
                super(ExposeProcess, cls).define(spec)
                spec.expose_inputs(SubProcess, include=('common',))
                spec.expose_inputs(SubProcess, namespace='sub_a', exclude=('common',))
                spec.expose_inputs(SubProcess, namespace='sub_b', exclude=('common',))

            @override
            def _run(self, **kwargs):
                self.submit(SubProcess, **self.exposed_inputs(SubProcess, namespace='sub_a'))
                self.submit(SubProcess, **self.exposed_inputs(SubProcess, namespace='sub_b'))

        self.SubProcess = SubProcess
        self.ExposeProcess = ExposeProcess

    def test_inputs_union_valid(self):
        inputs = {
            'common': Int(1),
            'sub_a': {
                'specific_a': Int(2),
                'specific_b': Int(3)
            },
            'sub_b': {
                'specific_a': Int(4),
                'specific_b': Int(5)
            }
        }
        run(self.ExposeProcess, **inputs)

    def test_inputs_union_invalid(self):
        inputs = {
            'sub_a': {
                'specific_a': Int(2),
                'specific_b': Int(3)
            },
            'sub_b': {
                'specific_a': Int(4),
                'specific_b': Int(5)
            }
        }
        with self.assertRaises(ValueError):
            run(self.ExposeProcess, **inputs)


class TestNonAgglomerateExposeProcess(AiidaTestCase):
    """
    Example where the default agglomerate behavior of exposed_inputs is undesirable and can be
    switched off by setting the flag agglomerate to False. The SubProcess shares an input with
    the parent processs, but unlike for the ExposeProcess, for the SubProcess it is not required.
    A user might for that reason not want to pass the common input to the SubProcess.
    """

    def setUp(self):
        super(TestNonAgglomerateExposeProcess, self).setUp()

        class SubProcess(Process):
            @classmethod
            def define(cls, spec):
                super(SubProcess, cls).define(spec)
                spec.input('specific_a', valid_type=Int, required=True)
                spec.input('specific_b', valid_type=Int, required=True)
                spec.input('common', valid_type=Int, required=False)

            @override
            def _run(self, **kwargs):
                assert 'common' not in self.inputs

        class ExposeProcess(Process):
            @classmethod
            def define(cls, spec):
                super(ExposeProcess, cls).define(spec)
                spec.expose_inputs(SubProcess, namespace='sub')
                spec.input('common', valid_type=Int, required=True)

            @override
            def _run(self, **kwargs):
                self.submit(SubProcess, **self.exposed_inputs(SubProcess, namespace='sub', agglomerate=False))

        self.SubProcess = SubProcess
        self.ExposeProcess = ExposeProcess

    def test_valid_input_non_agglomerate(self):
        inputs = {
            'common': Int(1),
            'sub': {
                'specific_a': Int(2),
                'specific_b': Int(3)
            },
        }
        run(self.ExposeProcess, **inputs)
