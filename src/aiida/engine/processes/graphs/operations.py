###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Static contracts and evaluation for inline scalar operations.

Inline operations compute orchestration state (counters, flags, scaled values) without recording
scientific provenance: their outputs are plain Python values held by the engine, never `Data` nodes,
so lowering must not fabricate `DataNode` outputs or `CREATE` links for them. The runtime evaluates
each placement from its wired inputs and keeps the result as control state; returning such a value
as a root graph output fails when the graph exposes its outputs, not here, so nested scopes may
freely thread operation results as loop and branch state.

:func:`infer_operation_shape` captures the static result contract of one operation for lowering and
validation. :func:`evaluate_operation` applies the operator to runtime values for the engine.
"""

from __future__ import annotations

import math
import operator
import typing as t
from collections.abc import Mapping

from aiida.common.exceptions import GraphRuntimeError, GraphTypeCheckError
from aiida.engine.processes.graphs.shapes import LeafShape, NamespaceShape, Shape
from aiida.orm import Bool, Float, Int

__all__ = (
    'BINARY_OPERATIONS',
    'LEFT_PORT',
    'OPERAND_PORT',
    'OPERATIONS',
    'RESULT_PORT',
    'RIGHT_PORT',
    'OperationKind',
    'evaluate_operation',
    'infer_operation_shape',
)

#: The inline operations, matching the source operators `+`, `-`, `*`, `//`, `%`,
#: `<`, `<=`, `>`, `>=`, `==`, `!=`, unary `-`, unary `+`, and `not`, in order.
OperationKind: t.TypeAlias = t.Literal[
    'add', 'sub', 'mul', 'floordiv', 'mod', 'lt', 'le', 'gt', 'ge', 'eq', 'ne', 'neg', 'pos', 'not'
]

#: Every supported inline operation.
OPERATIONS: t.Final = frozenset(
    {'add', 'sub', 'mul', 'floordiv', 'mod', 'lt', 'le', 'gt', 'ge', 'eq', 'ne', 'neg', 'pos', 'not'}
)

#: Operations reading two operands from the `left` and `right` ports.
BINARY_OPERATIONS: t.Final = frozenset({'add', 'sub', 'mul', 'floordiv', 'mod', 'lt', 'le', 'gt', 'ge', 'eq', 'ne'})

#: Input port of the left operand of a binary operation, in source order.
LEFT_PORT: t.Final = 'left'

#: Input port of the right operand of a binary operation, in source order.
RIGHT_PORT: t.Final = 'right'

#: Input port of the single operand of a unary operation.
OPERAND_PORT: t.Final = 'operand'

#: Output port of every inline operation.
RESULT_PORT: t.Final = 'result'


def _operand_kind(shape: Shape) -> t.Literal['int', 'float', 'bool', 'promoted', 'other', 'collection', 'unknown']:
    """Return the scalar kind an operand shape admits: `int`, `float`, `bool`, or `other`.

    `None` nullability is ignored, matching boundary validation, which strips it before comparing
    stored types. Python and ORM spellings of one kind map together: `int` with `Int`,
    `float` with `Float`, and `bool` with `Bool`.
    """
    if isinstance(shape, NamespaceShape):
        return 'collection'
    kinds: set[str] = set()
    for kind in shape.types or ():
        if kind is type(None):
            continue
        if kind is bool or kind is Bool:
            kinds.add('bool')
        elif kind is int or kind is Int:
            kinds.add('int')
        elif kind is float or kind is Float:
            kinds.add('float')
        else:
            kinds.add('other')
    if not kinds:
        return 'unknown'
    if kinds == {'int'}:
        return 'int'
    if kinds == {'float'}:
        return 'float'
    if kinds == {'bool'}:
        return 'bool'
    if kinds <= {'int', 'float'}:
        return 'promoted'
    return 'other'


def _describe(shape: Shape) -> str:
    """Name the declared types of an operand for a diagnostic."""
    if isinstance(shape, NamespaceShape):
        return 'a group of values'
    types = [kind for kind in shape.types or () if kind is not type(None)]
    if not types:
        return 'an unknown type'
    return ' or '.join(f'`{kind.__name__}`' for kind in types)


def _check_scalar(operation: str, shape: Shape) -> t.Literal['int', 'float', 'bool', 'promoted', 'other']:
    """Return the scalar kind of one operand, rejecting collections and unknown types."""
    kind = _operand_kind(shape)
    if kind == 'collection':
        msg = f'inline operation `{operation}` works on scalar leaves, not namespaces.'
        raise GraphTypeCheckError(msg)
    if kind == 'unknown':
        msg = f'inline operation `{operation}` needs declared scalar types, got {_describe(shape)}.'
        raise GraphTypeCheckError(msg)
    return kind


def infer_operation_shape(operation: OperationKind, operands: tuple[Shape, ...]) -> LeafShape:
    """Infer the result contract of one inline operation from its operand contracts.

    Integer pairs stay integers, unioning `int`/`Int` spellings across both operands. Any
    pure `float` promotes the result to `float`, unioning `float`/`Float` spellings; `int |
    float` unions without a pure float stay unions so an `int` runtime is never narrowed to
    `float`. Comparisons and `not` always produce `Bool`. Equality keeps booleans apart
    from numbers, unlike Python's `True == 1`.

    :param operation: the fixed operation to apply.
    :param operands: the operand contracts, two for binary operations and one for unary ones.
    :return: the result leaf with its scalar type.
    :raises GraphTypeCheckError: for unknown operations, wrong arity, collections, unknown or
        non-scalar types, boolean operands where numbers are required, and mixed equality.
    """
    if operation not in OPERATIONS:
        msg = f'unknown operation `{operation}`; expected one of {sorted(OPERATIONS)}.'
        raise GraphTypeCheckError(msg)
    if operation in BINARY_OPERATIONS:
        if len(operands) != 2:
            msg = f'inline operation `{operation}` takes 2 operands, got {len(operands)}.'
            raise GraphTypeCheckError(msg)
    elif len(operands) != 1:
        msg = f'inline operation `{operation}` takes 1 operand, got {len(operands)}.'
        raise GraphTypeCheckError(msg)
    kinds = [_check_scalar(operation, shape) for shape in operands]
    if operation == 'not':
        if kinds[0] != 'bool':
            msg = f'inline operation `not` reads `bool`, got {_describe(operands[0])}.'
            raise GraphTypeCheckError(msg)
        return LeafShape(types=(Bool,))
    shown = ' and '.join(_describe(shape) for shape in operands)
    if operation in {'eq', 'ne'}:
        left, right = kinds[0], kinds[1]
        if left == 'bool' or right == 'bool':
            if left == 'bool' and right == 'bool':
                return LeafShape(types=(Bool,))
            msg = f'inline operation `{operation}` compares numbers with numbers or `bool` with `bool`, got {shown}.'
            raise GraphTypeCheckError(msg)
        if 'other' in (left, right):
            msg = f'inline operation `{operation}` works on numbers, got {shown}.'
            raise GraphTypeCheckError(msg)
        return LeafShape(types=(Bool,))
    if any(kind == 'bool' for kind in kinds):
        noun = 'operand' if len(operands) == 1 else 'operands'
        msg = f'inline operation `{operation}` works on numbers excluding `bool`, got {noun} {shown}.'
        raise GraphTypeCheckError(msg)
    if any(kind == 'other' for kind in kinds):
        noun = 'operand' if len(operands) == 1 else 'operands'
        msg = f'inline operation `{operation}` works on numbers, got {noun} {shown}.'
        raise GraphTypeCheckError(msg)
    if operation in {'lt', 'le', 'gt', 'ge'}:
        return LeafShape(types=(Bool,))
    if operation in {'neg', 'pos'}:
        assert len(operands) == 1
        return LeafShape(types=_result_type(operands[0], kinds[0]))
    assert operation in {'add', 'sub', 'mul', 'floordiv', 'mod'}
    assert len(operands) == 2
    if kinds[0] == 'int' and kinds[1] == 'int':
        unioned = _union_spellings(operands, numeric='int')
        if unioned:
            return LeafShape(types=unioned)
    elif 'float' in kinds:
        unioned = _union_spellings(
            tuple(shape for shape, kind in zip(operands, kinds) if kind in {'float', 'promoted'}),
            numeric='float',
        )
        if unioned:
            return LeafShape(types=unioned)
    elif 'promoted' in kinds:
        unioned = _union_spellings(operands, numeric='both')
        if unioned:
            return LeafShape(types=unioned)
    msg = f'inline operation `{operation}` works on numbers, got {_describe(operands[0])}.'
    raise GraphTypeCheckError(msg)


def _spellings(shape: Shape, *, numeric: t.Literal['int', 'float']) -> tuple[type, ...]:
    """Return the `int` or `float` declarations of one operand, skipping nullability."""
    assert isinstance(shape, LeafShape)
    collected: list[type] = []
    for declared in shape.types or ():
        if declared is type(None):
            continue
        if numeric == 'int' and (declared is int or declared is Int):
            collected.append(declared)
        elif numeric == 'float' and (declared is float or declared is Float):
            collected.append(declared)
    deduped: list[type] = []
    for declared in collected:
        if declared not in deduped:
            deduped.append(declared)
    return tuple(deduped)


def _result_type(shape: Shape, kind: str) -> tuple[type, ...]:
    """Return the result type for one numeric kind, preserving the operand spelling.

    Promoted operands (`int | float` unions) keep their union: narrowing to `Float` alone
    would lie about `int` runtimes, which stay `int`. Single-kind operands keep their spelling:
    `Int` operands produce `Int`, plain `int` operands produce `int`.
    """
    assert isinstance(shape, LeafShape)
    if kind == 'promoted':
        union: list[type] = []
        for declared in shape.types or ():
            if declared is type(None):
                continue
            if declared in (int, Int, float, Float) and declared not in union:
                union.append(declared)
        if union:
            return tuple(union)
    elif kind == 'int':
        spellings = _spellings(shape, numeric='int')
        if spellings:
            return spellings
    elif kind == 'float':
        spellings = _spellings(shape, numeric='float')
        if spellings:
            return spellings
    msg = f'inline operation needs declared scalar types, got {_describe(shape)}.'
    raise GraphTypeCheckError(msg)


def _union_spellings(shapes: tuple[Shape, ...], *, numeric: t.Literal['int', 'float', 'both']) -> tuple[type, ...]:
    """Return the deduplicated `int`/`float` spellings across operands, `int` spellings first."""
    union: list[type] = []
    if numeric in {'int', 'both'}:
        for shape in shapes:
            for declared in _spellings(shape, numeric='int'):
                if declared not in union:
                    union.append(declared)
    if numeric in {'float', 'both'}:
        for shape in shapes:
            for declared in _spellings(shape, numeric='float'):
                if declared not in union:
                    union.append(declared)
    return tuple(union)


_BINARY_EVALUATORS: t.Final[dict[str, t.Callable[..., t.Any]]] = {
    'add': operator.add,
    'sub': operator.sub,
    'mul': operator.mul,
    'floordiv': operator.floordiv,
    'mod': operator.mod,
    'lt': operator.lt,
    'le': operator.le,
    'gt': operator.gt,
    'ge': operator.ge,
    'eq': operator.eq,
    'ne': operator.ne,
}

_UNARY_EVALUATORS: t.Final[dict[str, t.Callable[..., t.Any]]] = {
    'neg': operator.neg,
    'pos': operator.pos,
    'not': operator.not_,
}


def _primitive(value: object) -> object:
    """Unwrap a scalar node to the plain value inline operations compute over.

    Only the known ORM scalar classes unwrap; anything else passes through to the exact-type
    checks below, which reject it loudly.
    """
    if isinstance(value, (Int, Float, Bool)):
        return value.value
    return value


def evaluate_operation(operation: OperationKind, inputs: Mapping[str, object]) -> int | float | bool:
    """Evaluate one inline operation over plain runtime values.

    Scalar nodes evaluate through their `.value`; the result is always a plain Python value,
    never a node. Only exact `int`, `float`, and `bool` primitives compute, so subclasses
    with overloaded operators never run. Non-finite operands and results fail loudly instead
    of leaking `ZeroDivisionError`, `inf`, or `nan` into finite checkpoint state.

    :param operation: the fixed operation to apply.
    :param inputs: the `left`/`right` operands of a binary operation, or the `operand` of a unary one.
    :return: the plain Python result.
    :raises GraphRuntimeError: for unknown operations, missing or extra operands, illegal types,
        division by zero, and non-finite operands or results.
    """
    if operation not in OPERATIONS:
        msg = f'unknown operation `{operation}`; expected one of {sorted(OPERATIONS)}.'
        raise GraphRuntimeError(msg)
    expected = (LEFT_PORT, RIGHT_PORT) if operation in BINARY_OPERATIONS else (OPERAND_PORT,)
    for name in expected:
        if name not in inputs:
            msg = f'inline operation `{operation}` is missing operand `{name}`.'
            raise GraphRuntimeError(msg)
    for name in inputs:
        if name not in expected:
            msg = f'inline operation `{operation}` takes no operand `{name}`.'
            raise GraphRuntimeError(msg)
    if operation in BINARY_OPERATIONS:
        return _evaluate_binary(operation, _primitive(inputs[LEFT_PORT]), _primitive(inputs[RIGHT_PORT]))
    return _evaluate_unary(operation, _primitive(inputs[OPERAND_PORT]))


def _require_finite(operation: str, value: int | float) -> int | float:
    """Return a numeric operand, rejecting non-finite floats to keep checkpoints finite."""
    if isinstance(value, float) and not math.isfinite(value):
        msg = f'inline operation `{operation}` got a non-finite operand.'
        raise GraphRuntimeError(msg)
    return value


def _require_number(operation: str, value: object) -> int | float:
    """Return a runtime operand for arithmetic, rejecting booleans and other types.

    Only exact `int` and `float` compute: subclasses may overload operators, which would
    contradict the fixed safe operator set.
    """
    if type(value) is bool:
        msg = f'inline operation `{operation}` works on numbers excluding `bool`, got `bool`.'
        raise GraphRuntimeError(msg)
    if type(value) is int:
        return value
    if type(value) is float:
        return _require_finite(operation, value)
    msg = f'inline operation `{operation}` works on numbers, not `{type(value).__name__}`.'
    raise GraphRuntimeError(msg)


def _evaluate_binary(operation: str, left: object, right: object) -> int | float | bool:
    """Evaluate one binary operation over unwrapped runtime values."""
    if operation in {'eq', 'ne'}:
        return _evaluate_equality(operation, left, right)
    if operation in {'lt', 'le', 'gt', 'ge'}:
        left_number = _require_number(operation, left)
        right_number = _require_number(operation, right)
        result: object = _BINARY_EVALUATORS[operation](left_number, right_number)
        assert isinstance(result, bool)
        return result
    left_number = _require_number(operation, left)
    right_number = _require_number(operation, right)
    try:
        produced: object = _BINARY_EVALUATORS[operation](left_number, right_number)
    except ZeroDivisionError as exception:
        msg = f'inline operation `{operation}` divided by zero.'
        raise GraphRuntimeError(msg) from exception
    if type(produced) is float and not math.isfinite(produced):
        msg = f'inline operation `{operation}` produced a non-finite result.'
        raise GraphRuntimeError(msg)
    assert type(produced) is int or type(produced) is float
    return produced


def _evaluate_equality(operation: str, left: object, right: object) -> bool:
    """Evaluate `eq`/`ne`, keeping booleans apart from numbers and rejecting other types.

    Only exact primitives compute; non-finite numeric operands fail like everywhere else.
    """
    for value in (left, right):
        if type(value) is bool or type(value) is int or type(value) is float:
            continue
        msg = f'inline operation `{operation}` works on numbers, not `{type(value).__name__}`.'
        raise GraphRuntimeError(msg)
    if (type(left) is bool) != (type(right) is bool):
        msg = f'inline operation `{operation}` compares `bool` with `bool`, not with numbers.'
        raise GraphRuntimeError(msg)
    for value in (left, right):
        if type(value) is float and not math.isfinite(value):
            msg = f'inline operation `{operation}` got a non-finite operand.'
            raise GraphRuntimeError(msg)
    result = _BINARY_EVALUATORS[operation](left, right)
    assert isinstance(result, bool)
    return result


def _evaluate_unary(operation: str, operand: object) -> int | float | bool:
    """Evaluate one unary operation over an unwrapped runtime value."""
    if operation == 'not':
        if type(operand) is not bool:
            msg = f'inline operation `not` reads `bool`, got `{type(operand).__name__}`.'
            raise GraphRuntimeError(msg)
        return not operand
    number = _require_number(operation, operand)
    produced: object = _UNARY_EVALUATORS[operation](number)
    if type(produced) is float and not math.isfinite(produced):
        msg = f'inline operation `{operation}` produced a non-finite result.'
        raise GraphRuntimeError(msg)
    assert type(produced) is int or type(produced) is float
    return produced
