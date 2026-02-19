###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Tests for the process_function decorator.

Note that here we use ``workfunction`` and ``calcfunction``, the concrete versions of the ``process_function`` decorator
even though we are testing only the shared functionality that is captured in the ``process_function`` decorator,
relating to the transformation of the wrapped function into a ``FunctionProcess``. The reason we do not use the
``process_function`` decorator itself, is because it does not have a node class by default. We could create one on the
fly, but then anytime inputs or outputs would be attached to it in the tests, the ``validate_link`` function would
complain as the dummy node class is not recognized as a valid process node.
"""

from __future__ import annotations

import enum
import re
import sys
import typing as t

import pytest

from aiida import orm
from aiida.engine import ExitCode, calcfunction, run, run_get_node, submit, workfunction
from aiida.orm.nodes.data.bool import get_true_node
from aiida.workflows.arithmetic.add_multiply import add_multiply

DEFAULT_INT = 256
DEFAULT_LABEL = 'Default label'
DEFAULT_DESCRIPTION = 'Default description'
CUSTOM_LABEL = 'Custom label'
CUSTOM_DESCRIPTION = 'Custom description'

pytest.mark.requires_rmq


@workfunction
def function_return_input(data):
    return data


@calcfunction
def function_variadic_arguments(str_a, str_b, *args):
    return orm.Str(' '.join([e.value for e in (str_a, str_b, *args)]))


@calcfunction
def function_variadic_arguments_and_keywords(*args, str_a, str_b):
    return orm.Str(' '.join([e.value for e in (*args, str_a, str_b)]))


@calcfunction
def function_variadic_arguments_label_overlap(args_0, *args):
    return args_0 + orm.Int(sum(args))


@calcfunction
def function_return_true():
    return get_true_node()


@workfunction
def function_args(data_a):
    return data_a


@workfunction
def function_args_with_default(data_a=lambda: orm.Int(DEFAULT_INT)):
    return data_a


@calcfunction
def function_with_none_default(int_a, int_b, int_c=None):
    if int_c is not None:
        return int_a + int_b + int_c
    return int_a + int_b


@workfunction
def function_kwargs(**kwargs):
    return kwargs


@workfunction
def function_varargs_kwargs(*args, **kwargs):
    """Return the positional and keyword arguments as is in a single dictionary."""
    results = dict(kwargs)
    for index, arg in enumerate(args):
        results[f'arg_{index}'] = arg
    return results


@workfunction
def function_args_and_kwargs(data_a, **kwargs):
    result = {'data_a': data_a}
    result.update(kwargs)
    return result


@workfunction
def function_args_and_default(data_a, data_b=lambda: orm.Int(DEFAULT_INT)):
    return {'data_a': data_a, 'data_b': data_b}


@workfunction
def function_defaults(
    data_a=lambda: orm.Int(DEFAULT_INT), metadata={'label': DEFAULT_LABEL, 'description': DEFAULT_DESCRIPTION}
):
    return data_a


@workfunction
def function_default_label():
    return


@workfunction
def function_exit_code(exit_status, exit_message):
    return ExitCode(exit_status.value, exit_message.value)


@workfunction
def function_excepts(exception):
    raise RuntimeError(exception.value)


@workfunction
def function_out_unstored():
    return orm.Int(DEFAULT_INT)


@workfunction
def function_return_nested():
    return {'nested.output': orm.Int(DEFAULT_INT).store()}


def test_properties():
    """Test that the `is_process_function` and `node_class` attributes are set."""
    assert function_return_input.is_process_function
    assert function_return_input.node_class == orm.WorkFunctionNode
    assert function_return_true.is_process_function
    assert function_return_true.node_class == orm.CalcFunctionNode


def test_plugin_version():
    """Test the version attributes of a process function."""
    from aiida import __version__ as version_core

    _, node = function_args_with_default.run_get_node()

    # Since the "plugin" i.e. the process function is defined in `aiida-core` the `version.plugin` is the same as
    # the version of `aiida-core` itself
    version_info = node.base.attributes.get('version')
    assert version_info['core'] == version_core
    assert version_info['plugin'] == version_core


def test_process_state():
    """Test the process state for a process function."""
    _, node = function_args_with_default.run_get_node()

    assert node.is_terminated
    assert not node.is_excepted
    assert not node.is_killed
    assert node.is_finished
    assert node.is_finished_ok
    assert not node.is_failed


def test_process_type():
    """Test that the process type correctly contains the module and name of original decorated function."""
    _, node = function_defaults.run_get_node()
    process_type = f'{function_defaults.__module__}.{function_defaults.__name__}'
    assert node.process_type == process_type


def test_exit_status():
    """A FINISHED process function has to have an exit status of 0"""
    _, node = function_args_with_default.run_get_node()
    assert node.exit_status == 0
    assert node.is_finished_ok
    assert not node.is_failed


def test_source_code_attributes():
    """Verify function properties are properly introspected and stored in the nodes attributes and repository."""
    import inspect

    function_name = 'test_process_function'

    @calcfunction
    def test_process_function(data):
        return {'result': orm.Int(data.value + 1)}

    _, node = test_process_function.run_get_node(data=orm.Int(5))

    # Read the source file of the calculation function that should be stored in the repository
    function_source_code = node.get_source_code_file().split('\n')

    # Verify that the function name is correct and the first source code linenumber is stored
    assert node.function_name == function_name
    assert isinstance(node.function_starting_line_number, int)

    # Check the source code of the function is stored
    assert node.get_source_code_function() == inspect.getsource(test_process_function)

    # Check that first line number is correct. Note that the first line should correspond
    # to the `@workfunction` directive, but since the list is zero-indexed we actually get the
    # following line, which should correspond to the function name i.e. `def test_process_function(data)`
    function_name_from_source = function_source_code[node.function_starting_line_number]
    assert node.function_name in function_name_from_source


def test_get_source_code_file():
    """Test that ``get_source_code_file`` returns ``None`` if no source code was stored.

    This is the case for example for functions defined in an interactive shell, where the retrieval of the source code
    upon storing the node fails and nothing is stored. The function should not except in this case.
    """
    from aiida.orm.utils.mixins import FunctionCalculationMixin

    _, node = function_return_true.run_get_node()

    # Delete the source file by going down to the ``RepositoryBackend`` to circumvent the immutability check.
    node.base.repository._repository.delete_object(FunctionCalculationMixin.FUNCTION_SOURCE_FILE_PATH)

    assert node.get_source_code_file() is None


def test_function_varargs():
    """Test a function with variadic arguments."""
    result, node = function_variadic_arguments.run_get_node(orm.Str('a'), orm.Str('b'), *(orm.Str('c'), orm.Str('d')))
    assert isinstance(result, orm.Str)
    assert result.value == 'a b c d'

    inputs = node.base.links.get_incoming().nested()
    assert inputs['str_a'].value == 'a'
    assert inputs['str_b'].value == 'b'
    assert inputs['args_0'].value == 'c'
    assert inputs['args_1'].value == 'd'
    assert node.inputs.args_0.value == 'c'
    assert node.inputs.args_1.value == 'd'


def test_function_varargs_label_overlap():
    """Test a function with variadic arguments where the automatic label overlaps with a declared argument.

    This should raise a ``RuntimeError``.
    """
    with pytest.raises(RuntimeError, match=r'variadic argument with index `.*` would get the label `.*` but this'):
        function_variadic_arguments_label_overlap.run_get_node(orm.Int(1), *(orm.Int(2), orm.Int(3)))


def test_function_variadic_arguments_and_keywords():
    """Test passing variable positional arguments before keyword arguments."""
    result = function_variadic_arguments_and_keywords(
        *(orm.Str('a'), orm.Str('b')), str_a=orm.Str('c'), str_b=orm.Str('d')
    )
    assert result.value == 'a b c d'


def test_function_args():
    """Simple process function that defines a single positional argument."""
    arg = 1

    with pytest.raises(ValueError):
        result = function_args()

    result = function_args(data_a=orm.Int(arg))
    assert isinstance(result, orm.Int)
    assert result == arg


def test_function_args_with_default():
    """Simple process function that defines a single argument with a default."""
    arg = 1

    result = function_args_with_default()
    assert isinstance(result, orm.Int)
    assert result == orm.Int(DEFAULT_INT)

    result = function_args_with_default(data_a=orm.Int(arg))
    assert isinstance(result, orm.Int)
    assert result == arg


def test_function_with_none_default():
    """Simple process function that defines a keyword with `None` as default value."""
    int_a = orm.Int(1)
    int_b = orm.Int(2)
    int_c = orm.Int(3)

    result = function_with_none_default(int_a, int_b)
    assert isinstance(result, orm.Int)
    assert result == orm.Int(3)

    result = function_with_none_default(int_a, int_b, int_c)
    assert isinstance(result, orm.Int)
    assert result == orm.Int(6)


def test_function_kwargs():
    """Simple process function that defines keyword arguments."""
    kwargs = {'data_a': orm.Int(DEFAULT_INT)}

    result, node = function_kwargs.run_get_node()
    assert isinstance(result, dict)
    assert len(node.base.links.get_incoming().all()) == 0
    assert result == {}

    result, node = function_kwargs.run_get_node(**kwargs)
    assert isinstance(result, dict)
    assert len(node.base.links.get_incoming().all()) == 1
    assert result == kwargs

    # Calling with any number of positional arguments should raise
    with pytest.raises(TypeError):
        function_kwargs.run_get_node(orm.Int(1))

    with pytest.raises(TypeError):
        function_kwargs.run_get_node(orm.Int(1), b=orm.Int(2))


def test_function_args_and_kwargs():
    """Simple process function that defines a positional argument and keyword arguments."""
    arg = 1
    args = (orm.Int(DEFAULT_INT),)
    kwargs = {'data_b': orm.Int(arg)}

    result = function_args_and_kwargs(*args)
    assert isinstance(result, dict)
    assert result == {'data_a': args[0]}

    result = function_args_and_kwargs(*args, **kwargs)
    assert isinstance(result, dict)
    assert result == {'data_a': args[0], 'data_b': kwargs['data_b']}

    # Calling with more positional arguments than defined in the signature should raise
    with pytest.raises(TypeError):
        function_kwargs.run_get_node(orm.Int(1), orm.Int(2))

    with pytest.raises(TypeError):
        function_kwargs.run_get_node(orm.Int(1), orm.Int(2), b=orm.Int(2))


def test_function_args_and_kwargs_default():
    """Simple process function that defines a positional argument and an argument with a default."""
    arg = 1
    args_input_default = (orm.Int(DEFAULT_INT),)
    args_input_explicit = (orm.Int(DEFAULT_INT), orm.Int(arg))

    result = function_args_and_default(*args_input_default)
    assert isinstance(result, dict)
    assert result == {'data_a': args_input_default[0], 'data_b': orm.Int(DEFAULT_INT)}

    result = function_args_and_default(*args_input_explicit)
    assert isinstance(result, dict)
    assert result == {'data_a': args_input_explicit[0], 'data_b': args_input_explicit[1]}


def test_function_varargs_and_kwargs():
    """Test function that accepts both positional and keyword arguments."""
    results = function_varargs_kwargs(*(orm.Str('a'), orm.Str('b')), kwarg_c=orm.Str('c'), kwarg_d=orm.Str('d'))
    assert sorted(results.keys()) == ['arg_0', 'arg_1', 'kwarg_c', 'kwarg_d']
    assert results['arg_0'] == orm.Str('a')
    assert results['arg_1'] == orm.Str('b')
    assert results['kwarg_c'] == orm.Str('c')
    assert results['kwarg_d'] == orm.Str('d')


def test_function_args_passing_kwargs():
    """Cannot pass kwargs if the function does not explicitly define it accepts kwargs."""
    with pytest.raises(ValueError):
        function_args(data_a=orm.Int(1), data_b=orm.Int(1))


def test_function_set_label_description():
    """Verify that the label and description can be set for all process function variants."""
    metadata = {'label': CUSTOM_LABEL, 'description': CUSTOM_DESCRIPTION}

    _, node = function_args.run_get_node(data_a=orm.Int(DEFAULT_INT), metadata=metadata)
    assert node.label == CUSTOM_LABEL
    assert node.description == CUSTOM_DESCRIPTION

    _, node = function_args_with_default.run_get_node(metadata=metadata)
    assert node.label == CUSTOM_LABEL
    assert node.description == CUSTOM_DESCRIPTION

    _, node = function_kwargs.run_get_node(metadata=metadata)
    assert node.label == CUSTOM_LABEL
    assert node.description == CUSTOM_DESCRIPTION

    _, node = function_args_and_kwargs.run_get_node(data_a=orm.Int(DEFAULT_INT), metadata=metadata)
    assert node.label == CUSTOM_LABEL
    assert node.description == CUSTOM_DESCRIPTION

    _, node = function_args_and_default.run_get_node(data_a=orm.Int(DEFAULT_INT), metadata=metadata)
    assert node.label == CUSTOM_LABEL
    assert node.description == CUSTOM_DESCRIPTION


def test_function_defaults():
    """Verify that a process function can define a default label and description but can be overriden."""
    metadata = {'label': CUSTOM_LABEL, 'description': CUSTOM_DESCRIPTION}

    _, node = function_defaults.run_get_node(data_a=orm.Int(DEFAULT_INT))
    assert node.label == DEFAULT_LABEL
    assert node.description == DEFAULT_DESCRIPTION

    _, node = function_defaults.run_get_node(metadata=metadata)
    assert node.label == CUSTOM_LABEL
    assert node.description == CUSTOM_DESCRIPTION


def test_function_default_label():
    """Verify unless specified label is taken from function name."""
    metadata = {'label': CUSTOM_LABEL, 'description': CUSTOM_DESCRIPTION}

    _, node = function_default_label.run_get_node()
    assert node.label == 'function_default_label'
    assert node.description == ''

    _, node = function_default_label.run_get_node(metadata=metadata)
    assert node.label == CUSTOM_LABEL
    assert node.description == CUSTOM_DESCRIPTION


def test_run_launchers():
    """Verify that the various non-daemon launchers are working."""
    result = run(function_return_true)
    assert result

    result, node = run_get_node(function_return_true)
    assert result
    assert result == get_true_node()
    assert isinstance(node, orm.CalcFunctionNode)


@pytest.mark.requires_rmq
def test_submit_launchers():
    """Verify that submit to daemon works."""
    # Process function can be submitted and will be run by a daemon worker as long as the function is importable
    # Note that the actual running is not tested here but is done so in `.github/system_tests/test_daemon.py`.
    node = submit(add_multiply, x=orm.Int(1), y=orm.Int(2), z=orm.Int(3))
    assert isinstance(node, orm.WorkFunctionNode)


def test_return_exit_code():
    """A process function that returns an ExitCode namedtuple should have its exit status and message set FINISHED"""
    exit_status = 418
    exit_message = 'I am a teapot'

    message = orm.Str(exit_message)
    _, node = function_exit_code.run_get_node(exit_status=orm.Int(exit_status), exit_message=message)

    assert node.is_finished
    assert not node.is_finished_ok
    assert node.exit_status == exit_status
    assert node.exit_message == exit_message


def test_normal_exception():
    """If a process, for example a FunctionProcess, excepts, the exception should be stored in the node."""
    exception = 'This process function excepted'

    with pytest.raises(RuntimeError):
        _, node = function_excepts.run_get_node(exception=orm.Str(exception))
        assert node.is_excepted
        assert node.exception == exception


def test_function_out_unstored():
    """A workfunction that returns an unstored node should raise as it indicates users tried to create data."""
    with pytest.raises(ValueError):
        function_out_unstored()


def test_function_return_nested():
    """Test that a process function can returned outputs in nested namespaces."""
    results, node = function_return_nested.run_get_node()
    assert results['nested']['output'] == DEFAULT_INT
    assert node.outputs.nested.output == DEFAULT_INT


def test_simple_workflow():
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

    assert result == (3 + 4) * 5
    assert isinstance(node, orm.WorkFunctionNode)


def test_hashes():
    """Test that the hashes generated for identical process functions with identical inputs are the same."""
    _, node1 = function_return_input.run_get_node(data=orm.Int(2))
    _, node2 = function_return_input.run_get_node(data=orm.Int(2))
    assert node1.base.caching.get_hash() == node1.base.extras.get('_aiida_hash')
    assert node2.base.caching.get_hash() == node2.base.extras.get('_aiida_hash')
    assert node1.base.caching.get_hash() == node2.base.caching.get_hash()


def test_hashes_different():
    """Test that the hashes generated for identical process functions with different inputs are the different."""
    _, node1 = function_return_input.run_get_node(data=orm.Int(2))
    _, node2 = function_return_input.run_get_node(data=orm.Int(3))
    assert node1.base.caching.get_hash() == node1.base.extras.get('_aiida_hash')
    assert node2.base.caching.get_hash() == node2.base.extras.get('_aiida_hash')
    assert node1.base.caching.get_hash() != node2.base.caching.get_hash()


def test_input_validation():
    """Test that process functions do not allow non-storable inputs, even when hidden in nested namespaces.

    Regression test for #5128.
    """
    with pytest.raises(ValueError):
        function_kwargs.run_get_node(**{'namespace': {'valid': orm.Int(1), 'invalid': 1}})


class DummyEnum(enum.Enum):
    """Dummy enumeration."""

    VALUE = 'value'


@pytest.mark.parametrize(
    'argument, node_cls',
    (
        (True, orm.Bool),
        ({'a': 1}, orm.Dict),
        (1.0, orm.Float),
        (1, orm.Int),
        ('string', orm.Str),
        ([1], orm.List),
        (DummyEnum.VALUE, orm.EnumData),
    ),
)
def test_input_serialization(argument, node_cls):
    """Test that Python base type inputs are automatically serialized to the AiiDA node counterpart."""
    result = function_args(argument)
    assert isinstance(result, node_cls)

    if isinstance(result, orm.EnumData):
        assert result.get_member() == argument
    elif isinstance(result, orm.List):
        assert result.get_list() == argument
    elif isinstance(result, orm.Dict):
        assert result.get_dict() == argument
    else:
        assert result.value == argument


@pytest.mark.parametrize(
    'default, node_cls',
    (
        (True, orm.Bool),
        ({'a': 1}, orm.Dict),
        (1.0, orm.Float),
        (1, orm.Int),
        ('string', orm.Str),
        ([1], orm.List),
        (DummyEnum.VALUE, orm.EnumData),
    ),
)
def test_default_serialization(default, node_cls):
    """Test that Python base type defaults are automatically serialized to the AiiDA node counterpart."""

    @workfunction
    def function_with_default(data_a=default):
        return data_a

    result = function_with_default()
    assert isinstance(result, node_cls)

    if isinstance(result, orm.EnumData):
        assert result.get_member() == default
    elif isinstance(result, orm.List):
        assert result.get_list() == default
    elif isinstance(result, orm.Dict):
        assert result.get_dict() == default
    else:
        assert result.value == default


def test_multiple_default_serialization():
    """Test that Python base type defaults are automatically serialized to the AiiDA node counterpart."""

    @workfunction  # type: ignore[misc]
    def function_with_multiple_defaults(integer: int = 10, string: str = 'default', boolean: bool = False):
        return {'integer': integer, 'string': string, 'boolean': boolean}

    results = function_with_multiple_defaults()
    assert results['integer'].value == 10
    assert results['string'].value == 'default'
    assert results['boolean'].value is False


def test_input_serialization_none_default():
    """Test that calling a function with explicit ``None`` for an argument that defines ``None`` as default works."""
    assert function_with_none_default(int_a=1, int_b=2, int_c=None).value == 3


def test_invalid_outputs():
    """Test that returning an invalid output will properly lead the node to go in the excepted state."""

    @calcfunction
    def excepting():
        node = orm.Int(2)
        return {'a': node, 'b': node}

    with pytest.raises(ValueError):
        excepting()

    # Since the calcfunction actually raises an exception, it cannot return the node, so we have to query for it
    node = orm.QueryBuilder().append(orm.ProcessNode, tag='node').order_by({'node': {'id': 'desc'}}).first(flat=True)
    assert node.is_excepted, node.process_state
    assert re.match(r'ValueError: node<.*> already has an incoming LinkType.CREATE link', node.exception)


def test_nested_namespace():
    """Test that dynamic nested namespaces are supported.

    As long as the function declares ``**kwargs`` and all leaf values are storable ``Data`` instances, it should work.
    """

    @workfunction
    def function(**kwargs):
        return kwargs

    inputs = {
        'nested': {
            'namespace': {
                'int': orm.Int(1),
            }
        }
    }
    results, node = function.run_get_node(**inputs)
    assert results == inputs
    assert node.base.links.get_incoming().nested() == inputs

    inputs = {
        'nested': {
            'namespace': {
                'int': 1,
            }
        }
    }
    with pytest.raises(ValueError):
        function.run_get_node(**inputs)


def test_type_hinting_spec_inference():
    """Test the parsing of type hinting to define the valid types of the dynamically generated input ports."""

    @calcfunction  # type: ignore[misc]
    def function(
        a,
        b: str,
        c: bool,
        d: orm.Str,
        e: t.Union[orm.Str, orm.Int],
        f: t.Union[str, int],
        g: t.Optional[t.Dict] = None,
    ):
        pass

    input_namespace = function.spec().inputs

    expected = (
        ('a', (orm.Data,)),
        ('b', (orm.Str,)),
        ('c', (orm.Bool,)),
        ('d', (orm.Str,)),
        ('e', (orm.Str, orm.Int)),
        ('f', (orm.Str, orm.Int)),
        ('g', (orm.Dict, type(None))),
    )

    for key, valid_types in expected:
        assert key in input_namespace
        assert input_namespace[key].valid_type == valid_types, key


def test_type_hinting_spec_inference_pep_604(caplog):
    """Test the parsing of type hinting that uses union typing of PEP 604 which is only available to Python 3.10 and up.

    Even though adding ``from __future__ import annotations`` should backport this functionality to Python 3.9 and older
    the ``get_annotations`` method (which was also added to the ``inspect`` package in Python 3.10) as provided by the
    ``get-annotations`` backport package fails for this new syntax when called with ``eval_str=True``. Therefore type
    inference using this syntax only works on Python 3.10 and up.

    See https://peps.python.org/pep-0604
    """

    @calcfunction  # type: ignore[misc]
    def function(
        a: str | int,
        b: orm.Str | orm.Int,
        c: dict | None = None,
    ):
        pass

    input_namespace = function.spec().inputs

    # Since the PEP 604 union syntax is only available starting from Python 3.10 the type inference will not be
    # available for older versions, and so the valid type will be the default ``(orm.Data,)``.
    if sys.version_info[:2] >= (3, 10):
        expected = (
            ('a', (orm.Str, orm.Int)),
            ('b', (orm.Str, orm.Int)),
            ('c', (orm.Dict, type(None))),
        )
    else:
        assert 'function `function` has invalid type hints: unsupported operand type' in caplog.records[0].message
        expected = (
            ('a', (orm.Data,)),
            ('b', (orm.Data,)),
            ('c', (orm.Data, type(None))),
        )

    for key, valid_types in expected:
        assert key in input_namespace
        assert input_namespace[key].valid_type == valid_types, key


def test_type_hinting_validation():
    """Test that type hints are converted to automatic type checking through the process specification."""

    @calcfunction  # type: ignore[misc]
    def function_type_hinting(a: t.Union[int, float]):
        return a + 1

    with pytest.raises(ValueError, match=r'.*value \'a\' is not of the right type.*'):
        function_type_hinting('string')

    assert function_type_hinting(1) == 2
    assert function_type_hinting(orm.Int(1)) == 2
    assert function_type_hinting(1.0) == 2.0
    assert function_type_hinting(orm.Float(1)) == 2.0


def test_help_text_spec_inference():
    """Test the parsing of docstrings to define the ``help`` message of the dynamically generated input ports."""

    @calcfunction
    def function(param_a, param_b, param_c):
        """Some documentation.

        :param param_a: Some description.
        :param param_b: Fantastic docstring.
        """

    input_namespace = function.spec().inputs

    assert input_namespace['param_a'].help == 'Some description.'
    assert input_namespace['param_b'].help == 'Fantastic docstring.'
    assert input_namespace['param_c'].help is None


def test_help_text_spec_inference_invalid_docstring(caplog, monkeypatch):
    """Test the parsing of docstrings does not except for invalid docstrings, but simply logs a warning."""
    import docstring_parser

    def raise_exception():
        raise RuntimeError()

    monkeypatch.setattr(docstring_parser, 'parse', lambda _: raise_exception())

    @calcfunction
    def function():
        """Docstring."""

    # Now call the spec to have it parse the docstring.
    function.spec()
    assert 'function `function` has a docstring that could not be parsed' in caplog.records[0].message


@pytest.mark.usefixtures('aiida_profile_clean')
def test_get_process_logger_calcfunction():
    """Test that ``get_process_logger`` returns a logger when called from within a calcfunction."""
    from aiida.common.log import get_process_logger

    message = 'Log message from calcfunction'

    @calcfunction
    def function_with_logging(data):
        logger = get_process_logger()
        assert logger is not None, 'get_process_logger should return a logger within a calcfunction'
        logger.report(message)
        return data + orm.Int(1)

    _, node = function_with_logging.run_get_node(data=orm.Int(1))

    # Verify that the log was stored in the database
    logs = orm.Log.collection.get_logs_for(node)
    assert len(logs) == 1
    assert logs[0].message == message
    assert logs[0].levelname == 'REPORT'
    assert logs[0].dbnode_id == node.pk


@pytest.mark.usefixtures('aiida_profile_clean')
def test_get_process_logger_workfunction():
    """Test that ``get_process_logger`` returns a logger when called from within a workfunction."""
    from aiida.common.log import get_process_logger

    message = 'Log message from workfunction'

    @workfunction
    def function_with_logging(data):
        logger = get_process_logger()
        assert logger is not None, 'get_process_logger should return a logger within a workfunction'
        logger.report(message)
        return data

    _, node = function_with_logging.run_get_node(data=orm.Int(1).store())

    # Verify that the log was stored in the database
    logs = orm.Log.collection.get_logs_for(node)
    assert len(logs) == 1
    assert logs[0].message == message
    assert logs[0].levelname == 'REPORT'
    assert logs[0].dbnode_id == node.pk


@pytest.mark.usefixtures('aiida_profile_clean')
def test_get_process_logger_multiple_levels():
    """Test that ``get_process_logger`` supports different log levels.

    Note: By default, only REPORT level and above (REPORT, WARNING, ERROR, CRITICAL) are stored
    to the database. DEBUG and INFO levels are below the default threshold.
    """
    from aiida.common.log import get_process_logger

    messages = {
        'warning': 'Warning message',
        'error': 'Error message',
        'report': 'Report message',
    }

    @calcfunction
    def function_with_multiple_logs(data):
        logger = get_process_logger()
        assert logger is not None
        logger.warning(messages['warning'])
        logger.error(messages['error'])
        logger.report(messages['report'])
        return data + orm.Int(1)

    _, node = function_with_multiple_logs.run_get_node(data=orm.Int(1))

    # Verify that all logs at or above REPORT level were stored in the database
    logs = orm.Log.collection.get_logs_for(node)
    assert len(logs) == 3

    # Check that each log level was recorded correctly
    log_messages = {log.levelname: log.message for log in logs}
    assert log_messages['WARNING'] == messages['warning']
    assert log_messages['ERROR'] == messages['error']
    assert log_messages['REPORT'] == messages['report']


def test_get_process_logger_outside_process():
    """Test that ``get_process_logger`` returns None when called outside a process context."""
    from aiida.common.log import get_process_logger

    logger = get_process_logger()
    assert logger is None, 'get_process_logger should return None when called outside a process context'


@pytest.mark.usefixtures('aiida_profile_clean')
def test_get_process_logger_nested_calls():
    """Test that ``get_process_logger`` works correctly in nested process function calls."""
    from aiida.common.log import get_process_logger

    outer_message = 'Message from outer workfunction'
    inner_message = 'Message from inner calcfunction'

    @calcfunction
    def inner_function(data):
        logger = get_process_logger()
        assert logger is not None
        logger.report(inner_message)
        return data + orm.Int(1)

    @workfunction
    def outer_function(data):
        logger = get_process_logger()
        assert logger is not None
        logger.report(outer_message)
        result = inner_function(data)
        return result

    _, outer_node = outer_function.run_get_node(data=orm.Int(1).store())

    # Verify that the outer workfunction's log was stored
    outer_logs = orm.Log.collection.get_logs_for(outer_node)
    assert len(outer_logs) == 1
    assert outer_logs[0].message == outer_message

    # Find the inner calcfunction node
    from aiida.orm import QueryBuilder

    builder = QueryBuilder()
    builder.append(orm.WorkFunctionNode, filters={'id': outer_node.pk}, tag='outer')
    builder.append(orm.CalcFunctionNode, with_incoming='outer')
    inner_nodes = builder.all(flat=True)
    assert len(inner_nodes) == 1
    inner_node = inner_nodes[0]

    # Verify that the inner calcfunction's log was stored
    inner_logs = orm.Log.collection.get_logs_for(inner_node)
    assert len(inner_logs) == 1
    assert inner_logs[0].message == inner_message
