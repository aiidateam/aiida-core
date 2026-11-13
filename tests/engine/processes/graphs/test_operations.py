###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Inline scalar operations: inference, evaluation, and serialized declarations."""

import json

import pytest

from aiida.common.exceptions import GraphRuntimeError, GraphTypeCheckError
from aiida.engine.processes.graphs.ir import Endpoint, GraphIR, InlineOperation, Route
from aiida.engine.processes.graphs.operations import evaluate_operation, infer_operation_shape
from aiida.engine.processes.graphs.shapes import LeafShape, NamespaceShape, dump_shape
from aiida.orm import Bool, Float, Int


def _operands(*types: type) -> tuple[LeafShape, ...]:
    """Return one leaf contract per operand type."""
    return tuple(LeafShape(types=(kind,)) for kind in types)


def _operation(operation: str, *types: type, result: type | None = None) -> InlineOperation:
    """Return an operation placement over operand contracts, inferring the result unless given."""
    shapes = _operands(*types)
    inferred = infer_operation_shape(operation, shapes)  # type: ignore[arg-type]
    return InlineOperation(
        name='op',
        operation=operation,  # type: ignore[arg-type]
        input_shape=NamespaceShape(
            fields=tuple((port, shape) for port, shape in zip(('left', 'right')[: len(shapes)], shapes, strict=True))
            if len(shapes) == 2
            else (('operand', shapes[0]),)
        ),
        result_shape=LeafShape(types=(result,)) if result is not None else inferred,
    )


def test_infer_arithmetic_promotes_float() -> None:
    """Integer pairs stay integers; any float promotes the result."""
    assert infer_operation_shape('add', _operands(Int, Int)).types == (Int,)
    assert infer_operation_shape('mul', _operands(Int, Float)).types == (Float,)
    assert infer_operation_shape('floordiv', _operands(Int, Int)).types == (Int,)
    assert infer_operation_shape('mod', _operands(Float, Int)).types == (Float,)
    assert infer_operation_shape(
        'neg',
        _operands(
            Float,
        ),
    ).types == (Float,)


def test_infer_comparisons_return_bool() -> None:
    """Ordered and equality comparisons over scalars produce booleans."""
    assert infer_operation_shape('lt', _operands(Int, Float)).types == (Bool,)
    assert infer_operation_shape('eq', _operands(Bool, Bool)).types == (Bool,)
    assert infer_operation_shape(
        'not',
        _operands(
            Bool,
        ),
    ).types == (Bool,)


def test_infer_rejects_unknown_operators() -> None:
    """Closed operators fail fast with the supported set."""
    with pytest.raises(GraphTypeCheckError, match='unknown operation'):
        infer_operation_shape('pow', _operands(Int, Int))  # type: ignore[arg-type]


def test_infer_rejects_illegal_arity() -> None:
    """Binary operators need two operands, unary operators need one."""
    with pytest.raises(GraphTypeCheckError, match='takes 2 operand'):
        infer_operation_shape(
            'add',
            _operands(
                Int,
            ),
        )
    with pytest.raises(GraphTypeCheckError, match='takes 1 operand'):
        infer_operation_shape('neg', _operands(Int, Int))


def test_infer_rejects_bool_arithmetic() -> None:
    """Numeric operators exclude booleans; `not` requires them."""
    with pytest.raises(GraphTypeCheckError, match='excluding `bool`'):
        infer_operation_shape('add', _operands(Int, Bool))
    with pytest.raises(GraphTypeCheckError, match='reads `bool`'):
        infer_operation_shape(
            'not',
            _operands(
                Int,
            ),
        )
    with pytest.raises(GraphTypeCheckError, match='excluding `bool`'):
        infer_operation_shape('le', _operands(Bool, Bool))


def test_infer_rejects_mixed_equality() -> None:
    """Equality keeps booleans apart from numbers, unlike Python's `True == 1`."""
    with pytest.raises(GraphTypeCheckError, match='numbers with numbers'):
        infer_operation_shape('eq', _operands(Bool, Int))


def test_infer_rejects_namespaces_and_unconstrained() -> None:
    """Operands are scalar leaves with declared types."""
    with pytest.raises(GraphTypeCheckError, match='scalar leaves, not namespaces'):
        infer_operation_shape('neg', (NamespaceShape(fields=(('x', LeafShape(types=(Int,))),)),))
    with pytest.raises(GraphTypeCheckError, match='declared scalar types'):
        infer_operation_shape('neg', (LeafShape(),))


def test_evaluate_binary_and_unary() -> None:
    """Operators follow Python semantics over plain values."""
    assert evaluate_operation('add', {'left': 2, 'right': 3}) == 5
    assert evaluate_operation('floordiv', {'left': 7, 'right': 2}) == 3
    assert evaluate_operation('mod', {'left': 7.5, 'right': 2}) == pytest.approx(1.5)
    assert evaluate_operation('lt', {'left': 2.0, 'right': 3}) is True
    assert evaluate_operation('ne', {'left': True, 'right': False}) is True
    assert evaluate_operation('neg', {'operand': 2}) == -2
    assert evaluate_operation('not', {'operand': False}) is True


@pytest.mark.usefixtures('aiida_profile_clean')
def test_evaluate_unwraps_nodes_without_creating_data() -> None:
    """Scalar nodes evaluate through `.value`; plain values come back, not nodes."""
    result = evaluate_operation('add', {'left': Int(2), 'right': Float(0.5)})
    assert result == 2.5
    assert type(result) is float
    assert evaluate_operation('not', {'operand': Bool(True)}) is False


def test_evaluate_rejects_zero_division() -> None:
    """Division by zero names the operator instead of leaking `ZeroDivisionError`."""
    with pytest.raises(GraphRuntimeError, match='divided by zero'):
        evaluate_operation('floordiv', {'left': 1, 'right': 0})
    with pytest.raises(GraphRuntimeError, match='divided by zero'):
        evaluate_operation('mod', {'left': 1.0, 'right': 0.0})


def test_infer_preserves_numeric_unions() -> None:
    """Union operands stay unions; an `int` runtime is never narrowed to `float`."""
    assert infer_operation_shape('add', (LeafShape(types=(Int, Float)), LeafShape(types=(Int,)))).types == (
        Int,
        Float,
    )
    assert infer_operation_shape('mul', (LeafShape(types=(Int, Float)), LeafShape(types=(Int, Float)))).types == (
        Int,
        Float,
    )
    assert infer_operation_shape(
        'neg',
        (LeafShape(types=(Int, Float)),),
    ).types == (Int, Float)
    # A pure float still forces `float`, reading its spelling from the float operands.
    assert infer_operation_shape('add', (LeafShape(types=(Float,)), LeafShape(types=(Int, Float)))).types == (Float,)
    # Integer pairs union their spellings instead of keeping only the first.
    assert infer_operation_shape('add', _operands(int, Int)).types == (int, Int)


def test_infer_mixed_plain_and_orm_spellings() -> None:
    """Plain and ORM spellings mix without narrowing."""
    assert infer_operation_shape('sub', _operands(int, float)).types == (float,)
    assert infer_operation_shape('add', _operands(Float, int)).types == (Float,)
    assert infer_operation_shape('add', (LeafShape(types=(int, float)), LeafShape(types=(int,)))).types == (
        int,
        float,
    )


def test_evaluate_rejects_nonfinite_results() -> None:
    """Overflows that Python rounds to infinity fail loudly."""
    with pytest.raises(GraphRuntimeError, match='non-finite'):
        evaluate_operation('mul', {'left': 1e308, 'right': 10.0})
    with pytest.raises(GraphRuntimeError, match='non-finite'):
        evaluate_operation('sub', {'left': float('inf'), 'right': float('inf')})


def test_evaluate_rejects_nonfinite_operands_everywhere() -> None:
    """Unary, comparison, and equality operands must be finite to keep checkpoints finite."""
    with pytest.raises(GraphRuntimeError, match='non-finite'):
        evaluate_operation('neg', {'operand': float('inf')})
    with pytest.raises(GraphRuntimeError, match='non-finite'):
        evaluate_operation('pos', {'operand': float('nan')})
    with pytest.raises(GraphRuntimeError, match='non-finite'):
        evaluate_operation('lt', {'left': 1.0, 'right': float('inf')})
    with pytest.raises(GraphRuntimeError, match='non-finite'):
        evaluate_operation('ge', {'left': float('nan'), 'right': 2})
    with pytest.raises(GraphRuntimeError, match='non-finite'):
        evaluate_operation('eq', {'left': float('inf'), 'right': float('inf')})
    with pytest.raises(GraphRuntimeError, match='non-finite'):
        evaluate_operation('ne', {'left': 1.0, 'right': float('nan')})


def test_evaluate_rejects_subclass_operands() -> None:
    """Subclasses with overloaded operators never run; only exact primitives compute."""

    class EvilInt(int):
        def __add__(self, other):  # type: ignore[no-untyped-def]
            return 999

    class EvilFloat(float):
        def __mul__(self, other):  # type: ignore[no-untyped-def]
            return 999.0

    with pytest.raises(GraphRuntimeError, match='not `EvilInt`'):
        evaluate_operation('add', {'left': EvilInt(1), 'right': 1})
    with pytest.raises(GraphRuntimeError, match='not `EvilFloat`'):
        evaluate_operation('mul', {'left': EvilFloat(2.0), 'right': 3.0})
    with pytest.raises(GraphRuntimeError, match='not `EvilInt`'):
        evaluate_operation('eq', {'left': EvilInt(1), 'right': 1})


def test_evaluate_rejects_illegal_types_and_arity() -> None:
    """Booleans stay out of arithmetic, strings stay out everywhere, ports must match."""
    with pytest.raises(GraphRuntimeError, match='excluding `bool`'):
        evaluate_operation('add', {'left': True, 'right': 1})
    with pytest.raises(GraphRuntimeError, match='not `str`'):
        evaluate_operation('eq', {'left': 'a', 'right': 'b'})
    with pytest.raises(GraphRuntimeError, match='compares `bool` with `bool`'):
        evaluate_operation('eq', {'left': True, 'right': 1})
    with pytest.raises(GraphRuntimeError, match='missing operand'):
        evaluate_operation('add', {'left': 1})
    with pytest.raises(GraphRuntimeError, match='takes no operand'):
        evaluate_operation('not', {'operand': True, 'extra': False})
    with pytest.raises(GraphRuntimeError, match='unknown operation'):
        evaluate_operation('pow', {'left': 2, 'right': 3})  # type: ignore[arg-type]


def test_operation_round_trips_through_json() -> None:
    """Serialized operations reload with identical contracts."""
    task = _operation('add', Int, Float)
    assert task.result_port == 'result'
    assert list(task.output_ports()) == ['result']
    rebuilt = InlineOperation.from_dict(json.loads(json.dumps(task.to_dict())))
    assert rebuilt == task
    assert rebuilt.to_dict() == task.to_dict()


def test_infer_strips_nullable_operands() -> None:
    """Nullability never leaks into the result; `None` runtimes still fail fast."""
    assert infer_operation_shape('add', (LeafShape(types=(Int, type(None))), LeafShape(types=(Int,)))).types == (Int,)
    assert infer_operation_shape(
        'neg',
        (LeafShape(types=(Int, Float, type(None))),),
    ).types == (Int, Float)
    with pytest.raises(GraphRuntimeError, match='not `NoneType`'):
        evaluate_operation('add', {'left': None, 'right': 1})


def test_operation_from_dict_rejects_malformed_ir() -> None:
    """Unknown operators, missing keys, and wrong ports fail as type errors."""
    task = _operation('add', Int, Int)
    with pytest.raises(GraphTypeCheckError, match='unknown operation'):
        InlineOperation.from_dict({**task.to_dict(), 'operation': 'pow'})
    with pytest.raises(GraphTypeCheckError, match='missing key'):
        InlineOperation.from_dict({key: value for key, value in task.to_dict().items() if key != 'operation'})
    with pytest.raises(GraphTypeCheckError, match='reads operand'):
        InlineOperation.from_dict(
            {
                **task.to_dict(),
                'input_shape': dump_shape(NamespaceShape(fields=(('operand', LeafShape(types=(Int,))),))),
            }
        )
    with pytest.raises(GraphTypeCheckError, match='scalar leaf'):
        InlineOperation.from_dict(
            {
                **task.to_dict(),
                'result_shape': dump_shape(NamespaceShape(fields=(('result', LeafShape(types=(Int,))),))),
            }
        )


def test_graph_rejects_narrowed_union_results() -> None:
    """Declaring a narrowed `Float` result for union operands fails validation."""
    union_operation = InlineOperation(
        name='op',
        operation='add',
        input_shape=NamespaceShape(
            fields=(
                ('left', LeafShape(types=(Int, Float))),
                ('right', LeafShape(types=(Int,))),
            )
        ),
        result_shape=LeafShape(types=(Float,)),
    )
    with pytest.raises(GraphTypeCheckError, match='declares result'):
        GraphIR(
            tasks=(union_operation,),
            input_shape=NamespaceShape(
                fields=(
                    ('left', LeafShape(types=(Int, Float))),
                    ('right', LeafShape(types=(Int,))),
                )
            ),
            dependencies=(),
            inputs={
                'left': (Route('op', 'left'),),
                'right': (Route('op', 'right'),),
            },
            outputs={},
        )
    with pytest.raises(GraphTypeCheckError, match='declares result'):
        GraphIR(
            tasks=(_operation('add', Int, Int, result=Bool),),
            input_shape=NamespaceShape(),
            outputs={},
        )


def test_graph_versions_operation_bearing_ir() -> None:
    """Operation-free graphs stay at 0.1; operations bump the template to 0.2."""
    plain = GraphIR(
        tasks=(),
        input_shape=NamespaceShape(),
        outputs={},
    )
    assert plain.to_dict()['version'] == '0.1'
    assert GraphIR.from_dict(plain.to_dict()) == plain

    operation = _operation('mul', Int, Int)
    graph = GraphIR(
        tasks=(operation,),
        input_shape=NamespaceShape(
            fields=(
                ('left', LeafShape(types=(Int,))),
                ('right', LeafShape(types=(Int,))),
            )
        ),
        dependencies=(),
        inputs={'left': (Route('op', 'left'),), 'right': (Route('op', 'right'),)},
        outputs={'result': Endpoint(port='result', task='op')},
    )
    assert graph.to_dict()['version'] == '0.2'
    assert GraphIR.from_dict(json.loads(json.dumps(graph.to_dict()))) == graph


def test_graph_rejects_unknown_versions() -> None:
    """Templates from the future fail loudly instead of mis-scheduling."""
    graph = GraphIR(tasks=(), input_shape=NamespaceShape(), outputs={})
    with pytest.raises(GraphTypeCheckError, match=r'version `0.9`'):
        GraphIR.from_dict({**graph.to_dict(), 'version': '0.9'})


def test_graph_rejects_mistyped_operation_results() -> None:
    """Declared result types must match the inferred operator contract."""
    with pytest.raises(GraphTypeCheckError, match='declares result'):
        GraphIR(
            tasks=(_operation('add', Int, Int, result=Bool),),
            input_shape=NamespaceShape(),
            outputs={},
        )


def test_operation_validates_regardless_of_field_order() -> None:
    """Operand lookup follows port names, so a reversed declaration order still validates."""
    left, right = LeafShape(types=(Int,)), LeafShape(types=(Float,))
    task = InlineOperation(
        name='op',
        operation='add',
        input_shape=NamespaceShape(fields=(('right', right), ('left', left))),
        result_shape=infer_operation_shape('add', (left, right)),
    )
    graph = GraphIR(
        tasks=(task,),
        input_shape=NamespaceShape(fields=(('first', LeafShape(types=(Int,))), ('second', LeafShape(types=(Float,))))),
        inputs={'first': (Route('op', 'left'),), 'second': (Route('op', 'right'),)},
        outputs={'total': Endpoint(port='result', task='op')},
    )
    assert graph.build_output_namespace()['total'].valid_type == (Float,)


def test_operation_wires_through_ports() -> None:
    """Routed inputs and valued dependencies type-check against operand ports."""
    operation = _operation('le', Int, Float)
    graph = GraphIR(
        tasks=(operation,),
        input_shape=NamespaceShape(
            fields=(
                ('limit', LeafShape(types=(Int,))),
                ('value', LeafShape(types=(Float,))),
            )
        ),
        inputs={'limit': (Route('op', 'left'),), 'value': (Route('op', 'right'),)},
        outputs={'ok': Endpoint(port='result', task='op')},
    )
    assert graph.build_output_namespace()['ok'].valid_type == (Bool,)
    with pytest.raises(GraphTypeCheckError, match='unknown input'):
        GraphIR(
            tasks=(operation,),
            input_shape=NamespaceShape(fields=(('limit', LeafShape(types=(Int,))),)),
            inputs={'limit': (Route('op', 'middle'),)},
            outputs={},
        )
    with pytest.raises(GraphTypeCheckError, match='incompatible types'):
        GraphIR(
            tasks=(_operation('add', Int, Int),),
            input_shape=NamespaceShape(fields=(('flag', LeafShape(types=(Bool,))),)),
            inputs={'flag': (Route('op', 'left'),)},
            outputs={},
        )
