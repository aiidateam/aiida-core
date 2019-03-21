# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the process_function decorator."""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from aiida import orm
from aiida.backends.testbase import AiidaTestCase
from aiida.engine import run, run_get_node, submit, calcfunction, workfunction, Process, ExitCode
from aiida.orm.nodes.data.bool import get_true_node

DEFAULT_INT = 256
DEFAULT_LABEL = 'Default label'
DEFAULT_DESCRIPTION = 'Default description'
CUSTOM_LABEL = 'Custom label'
CUSTOM_DESCRIPTION = 'Custom description'


class TestProcessFunction(AiidaTestCase):
    """
    Note that here we use `@workfunctions` and `@calculations`, the concrete versions of the
    `@process_function` decorator, even though we are testing only the shared functionality
    that is captured in the `@process_function` decorator, relating to the transformation
    of the wrapped function into a `FunctionProcess`.
    The reason we do not use the `@process_function` decorator itself, is because it
    does not have a node class by default. We could create one on the fly, but then
    anytime inputs or outputs would be attached to it in the tests, the `validate_link`
    function would complain as the dummy node class is not recognized as a valid process node.
    """

    # pylint: disable=too-many-public-methods

    def setUp(self):
        super(TestProcessFunction, self).setUp()
        self.assertIsNone(Process.current())

        @workfunction
        def function_return_input(data):
            return data

        @calcfunction
        def function_return_true():
            return get_true_node()

        @workfunction
        def function_args(data_a):
            return data_a

        @workfunction
        def function_args_with_default(data_a=orm.Int(DEFAULT_INT)):
            return data_a

        @calcfunction
        def function_with_none_default(int_a, int_b, int_c=None):
            if int_c is not None:
                return orm.Int(int_a + int_b + int_c)
            return orm.Int(int_a + int_b)

        @workfunction
        def function_kwargs(**kwargs):
            return kwargs

        @workfunction
        def function_args_and_kwargs(data_a, **kwargs):
            result = {'data_a': data_a}
            result.update(kwargs)
            return result

        @workfunction
        def function_args_and_default(data_a, data_b=orm.Int(DEFAULT_INT)):
            return {'data_a': data_a, 'data_b': data_b}

        @workfunction
        def function_defaults(
                data_a=orm.Int(DEFAULT_INT), metadata={
                    'label': DEFAULT_LABEL,
                    'description': DEFAULT_DESCRIPTION
                }):  # pylint: disable=unused-argument,dangerous-default-value,missing-docstring
            return data_a

        @workfunction
        def function_exit_code(exit_status, exit_message):
            return ExitCode(exit_status.value, exit_message.value)

        @workfunction
        def function_excepts(exception):
            raise RuntimeError(exception.value)

        self.function_return_input = function_return_input
        self.function_return_true = function_return_true
        self.function_args = function_args
        self.function_args_with_default = function_args_with_default
        self.function_with_none_default = function_with_none_default
        self.function_kwargs = function_kwargs
        self.function_args_and_kwargs = function_args_and_kwargs
        self.function_args_and_default = function_args_and_default
        self.function_defaults = function_defaults
        self.function_exit_code = function_exit_code
        self.function_excepts = function_excepts

    def tearDown(self):
        super(TestProcessFunction, self).tearDown()
        self.assertIsNone(Process.current())

    def test_process_state(self):
        """Test the process state for a process function."""
        _, node = self.function_args_with_default.run_get_node()

        self.assertEqual(node.is_terminated, True)
        self.assertEqual(node.is_excepted, False)
        self.assertEqual(node.is_killed, False)
        self.assertEqual(node.is_finished, True)
        self.assertEqual(node.is_finished_ok, True)
        self.assertEqual(node.is_failed, False)

    def test_exit_status(self):
        """A FINISHED process function has to have an exit status of 0"""
        _, node = self.function_args_with_default.run_get_node()
        self.assertEqual(node.exit_status, 0)
        self.assertEqual(node.is_finished_ok, True)
        self.assertEqual(node.is_failed, False)

    def test_source_code_attributes(self):
        """Verify function properties are properly introspected and stored in the nodes attributes and repository."""
        function_name = 'test_process_function'

        @calcfunction
        def test_process_function(data):
            return {'result': orm.Int(data.value + 1)}

        _, node = test_process_function.run_get_node(data=orm.Int(5))

        # Read the source file of the calculation function that should be stored in the repository
        function_source_code = node.get_function_source_code().split('\n')

        # Verify that the function name is correct and the first source code linenumber is stored
        self.assertEqual(node.function_name, function_name)
        self.assertIsInstance(node.function_starting_line_number, int)

        # Check that first line number is correct. Note that the first line should correspond
        # to the `@workfunction` directive, but since the list is zero-indexed we actually get the
        # following line, which should correspond to the function name i.e. `def test_process_function(data)`
        function_name_from_source = function_source_code[node.function_starting_line_number]
        self.assertTrue(node.function_name in function_name_from_source)

    def test_function_varargs(self):
        """Variadic arguments are not supported and should raise."""
        with self.assertRaises(ValueError):

            @workfunction
            def function_varargs(*args):  # pylint: disable=unused-variable
                return args

    def test_function_args(self):
        """Simple process function that defines a single positional argument."""
        arg = 1

        with self.assertRaises(ValueError):
            result = self.function_args()  # pylint: disable=no-value-for-parameter

        result = self.function_args(data_a=orm.Int(arg))
        self.assertTrue(isinstance(result, orm.Int))
        self.assertEqual(result, arg)

    def test_function_args_with_default(self):
        """Simple process function that defines a single argument with a default."""
        arg = 1

        result = self.function_args_with_default()
        self.assertTrue(isinstance(result, orm.Int))
        self.assertEqual(result, orm.Int(DEFAULT_INT))

        result = self.function_args_with_default(data_a=orm.Int(arg))
        self.assertTrue(isinstance(result, orm.Int))
        self.assertEqual(result, arg)

    def test_function_with_none_default(self):
        """Simple process function that defines a keyword with `None` as default value."""
        int_a = orm.Int(1)
        int_b = orm.Int(2)
        int_c = orm.Int(3)

        result = self.function_with_none_default(int_a, int_b)
        self.assertTrue(isinstance(result, orm.Int))
        self.assertEqual(result, orm.Int(3))

        result = self.function_with_none_default(int_a, int_b, int_c)
        self.assertTrue(isinstance(result, orm.Int))
        self.assertEqual(result, orm.Int(6))

    def test_function_kwargs(self):
        """Simple process function that defines keyword arguments."""
        kwargs = {'data_a': orm.Int(DEFAULT_INT)}

        result, node = self.function_kwargs.run_get_node()
        self.assertTrue(isinstance(result, dict))
        self.assertEqual(len(node.get_incoming().all()), 0)
        self.assertEqual(result, {})

        result, node = self.function_kwargs.run_get_node(**kwargs)
        self.assertTrue(isinstance(result, dict))
        self.assertEqual(len(node.get_incoming().all()), 1)
        self.assertEqual(result, kwargs)

        # Calling with any number of positional arguments should raise
        with self.assertRaises(TypeError):
            self.function_kwargs.run_get_node(orm.Int(1))

        with self.assertRaises(TypeError):
            self.function_kwargs.run_get_node(orm.Int(1), b=orm.Int(2))

    def test_function_args_and_kwargs(self):
        """Simple process function that defines a positional argument and keyword arguments."""
        arg = 1
        args = (orm.Int(DEFAULT_INT),)
        kwargs = {'data_b': orm.Int(arg)}

        result = self.function_args_and_kwargs(*args)
        self.assertTrue(isinstance(result, dict))
        self.assertEqual(result, {'data_a': args[0]})

        result = self.function_args_and_kwargs(*args, **kwargs)
        self.assertTrue(isinstance(result, dict))
        self.assertEqual(result, {'data_a': args[0], 'data_b': kwargs['data_b']})

        # Calling with more positional arguments than defined in the signature should raise
        with self.assertRaises(TypeError):
            self.function_kwargs.run_get_node(orm.Int(1), orm.Int(2))

        with self.assertRaises(TypeError):
            self.function_kwargs.run_get_node(orm.Int(1), orm.Int(2), b=orm.Int(2))

    def test_function_args_and_kwargs_default(self):
        """Simple process function that defines a positional argument and an argument with a default."""
        arg = 1
        args_input_default = (orm.Int(DEFAULT_INT),)
        args_input_explicit = (orm.Int(DEFAULT_INT), orm.Int(arg))

        result = self.function_args_and_default(*args_input_default)
        self.assertTrue(isinstance(result, dict))
        self.assertEqual(result, {'data_a': args_input_default[0], 'data_b': orm.Int(DEFAULT_INT)})

        result = self.function_args_and_default(*args_input_explicit)
        self.assertTrue(isinstance(result, dict))
        self.assertEqual(result, {'data_a': args_input_explicit[0], 'data_b': args_input_explicit[1]})

    def test_function_args_passing_kwargs(self):
        """Cannot pass kwargs if the function does not explicitly define it accepts kwargs."""
        arg = 1

        with self.assertRaises(ValueError):
            self.function_args(data_a=orm.Int(arg), data_b=orm.Int(arg))  # pylint: disable=unexpected-keyword-arg

    def test_function_set_label_description(self):
        """Verify that the label and description can be set for all process function variants."""
        metadata = {'label': CUSTOM_LABEL, 'description': CUSTOM_DESCRIPTION}

        _, node = self.function_args.run_get_node(data_a=orm.Int(DEFAULT_INT), metadata=metadata)
        self.assertEqual(node.label, CUSTOM_LABEL)
        self.assertEqual(node.description, CUSTOM_DESCRIPTION)

        _, node = self.function_args_with_default.run_get_node(metadata=metadata)
        self.assertEqual(node.label, CUSTOM_LABEL)
        self.assertEqual(node.description, CUSTOM_DESCRIPTION)

        _, node = self.function_kwargs.run_get_node(metadata=metadata)
        self.assertEqual(node.label, CUSTOM_LABEL)
        self.assertEqual(node.description, CUSTOM_DESCRIPTION)

        _, node = self.function_args_and_kwargs.run_get_node(data_a=orm.Int(DEFAULT_INT), metadata=metadata)
        self.assertEqual(node.label, CUSTOM_LABEL)
        self.assertEqual(node.description, CUSTOM_DESCRIPTION)

        _, node = self.function_args_and_default.run_get_node(data_a=orm.Int(DEFAULT_INT), metadata=metadata)
        self.assertEqual(node.label, CUSTOM_LABEL)
        self.assertEqual(node.description, CUSTOM_DESCRIPTION)

    def test_function_defaults(self):
        """Verify that a process function can define a default label and description but can be overriden."""
        metadata = {'label': CUSTOM_LABEL, 'description': CUSTOM_DESCRIPTION}

        _, node = self.function_defaults.run_get_node(data_a=orm.Int(DEFAULT_INT))
        self.assertEqual(node.label, DEFAULT_LABEL)
        self.assertEqual(node.description, DEFAULT_DESCRIPTION)

        _, node = self.function_defaults.run_get_node(metadata=metadata)
        self.assertEqual(node.label, CUSTOM_LABEL)
        self.assertEqual(node.description, CUSTOM_DESCRIPTION)

    def test_launchers(self):
        """Verify that the various launchers are working."""
        result = run(self.function_return_true)
        self.assertTrue(result)

        result, node = run_get_node(self.function_return_true)
        self.assertTrue(result)
        self.assertEqual(result, get_true_node())
        self.assertTrue(isinstance(node, orm.CalcFunctionNode))

        with self.assertRaises(AssertionError):
            submit(self.function_return_true)

    def test_return_exit_code(self):
        """
        A process function that returns an ExitCode namedtuple should have its exit status and message set FINISHED
        """
        exit_status = 418
        exit_message = 'I am a teapot'

        message = orm.Str(exit_message)
        _, node = self.function_exit_code.run_get_node(exit_status=orm.Int(exit_status), exit_message=message)

        self.assertTrue(node.is_finished)
        self.assertFalse(node.is_finished_ok)
        self.assertEqual(node.exit_status, exit_status)
        self.assertEqual(node.exit_message, exit_message)

    def test_normal_exception(self):
        """If a process, for example a FunctionProcess, excepts, the exception should be stored in the node."""
        exception = 'This process function excepted'

        with self.assertRaises(RuntimeError):
            _, node = self.function_excepts.run_get_node(exception=orm.Str(exception))
            self.assertTrue(node.is_excepted)
            self.assertEqual(node.exception, exception)

    def test_simple_workflow(self):
        """Test construction of simple workflow by chaining process functions."""

        @calcfunction
        def add(data_a, data_b):
            return data_a + data_b

        @calcfunction
        def mul(data_a, data_b):
            return data_a * data_b

        @workfunction
        def add_mul_wf(data_a, data_b, data_c):
            return mul(add(data_a, data_b), data_c)

        result, node = add_mul_wf.run_get_node(orm.Int(3), orm.Int(4), orm.Int(5))

        self.assertEqual(result, (3 + 4) * 5)
        self.assertIsInstance(node, orm.WorkFunctionNode)

    def test_hashes(self):
        """Test that the hashes generated for identical process functions with identical inputs are the same."""
        _, node1 = self.function_return_input.run_get_node(data=orm.Int(2))
        _, node2 = self.function_return_input.run_get_node(data=orm.Int(2))
        self.assertEqual(node1.get_hash(), node1.get_extra('_aiida_hash'))
        self.assertEqual(node2.get_hash(), node2.get_extra('_aiida_hash'))
        self.assertEqual(node1.get_hash(), node2.get_hash())

    def test_hashes_different(self):
        """Test that the hashes generated for identical process functions with different inputs are the different."""
        _, node1 = self.function_return_input.run_get_node(data=orm.Int(2))
        _, node2 = self.function_return_input.run_get_node(data=orm.Int(3))
        self.assertEqual(node1.get_hash(), node1.get_extra('_aiida_hash'))
        self.assertEqual(node2.get_hash(), node2.get_extra('_aiida_hash'))
        self.assertNotEqual(node1.get_hash(), node2.get_hash())
