###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Pure inline collection expressions for graph orchestration state.

Compiles a restricted Python expression to a closed JSON tree, infers its static
contract from declared shapes, and evaluates it synchronously inside one inline
placement. Results are plain Python scalars, lists, and dicts (selected items may
be the referenced nodes themselves); nothing here dispatches tasks or stores data.

Supported source: free names (resolved by the caller to input ports), finite scalar
constants, the scalar operators of :mod:`aiida.engine.processes.graphs.operations`,
integer indexing of lists (negatives allowed), string keys of dicts, public
attribute reads (``NamespaceShape`` fields, annotated properties, scalar ``.value``),
list/dict literals, and filtered/nested list/dict comprehensions. Dictionaries
iterate keys; ``for key, value in mapping.items()`` tuple targets iterate pairs.
Slices, method calls, private names, and boolean ``and``/``or`` stay task concerns.

:func:`compile_expression` raises :class:`GraphTypeCheckError` with the offending
source excerpt; :func:`infer_expression_shape` raises it for ill-typed trees;
:func:`evaluate_expression` raises :class:`GraphRuntimeError` for bad runtime
values. Malformed trees fail closed in both.
"""

from __future__ import annotations

import ast
import inspect
import math
import typing as t
from collections.abc import Callable, Mapping

from aiida.common.exceptions import GraphRuntimeError, GraphTypeCheckError
from aiida.engine.processes.graphs.operations import (
    BINARY_OPERATIONS,
    OPERAND_PORT,
    OperationKind,
    const_result_shape,
    evaluate_operation,
    infer_operation_shape,
)
from aiida.engine.processes.graphs.shapes import LeafShape, NamespaceShape, Shape, shape_for_annotation
from aiida.orm import Bool, DataDict, DataList, DataNode, Float, Int, Str
from aiida.orm.nodes.data.dict import Dict as OrmDict
from aiida.orm.nodes.data.list import List as OrmList

__all__ = ('compile_expression', 'evaluate_expression', 'infer_expression_shape')

#: A serialized expression tree; plain JSON mappings, lists, strings, and scalars only.
Expression: t.TypeAlias = Mapping[str, t.Any]

#: Resolve one free :class:`ast.Name` node to its expression input port and declared shape.
Resolver: t.TypeAlias = Callable[[ast.expr], tuple[str, Shape]]

_BINARY_AST: t.Final[dict[type[ast.operator], OperationKind]] = {
    ast.Add: 'add',
    ast.Sub: 'sub',
    ast.Mult: 'mul',
    ast.FloorDiv: 'floordiv',
    ast.Mod: 'mod',
}

_COMPARISON_AST: t.Final[dict[type[ast.cmpop], OperationKind]] = {
    ast.Lt: 'lt',
    ast.LtE: 'le',
    ast.Gt: 'gt',
    ast.GtE: 'ge',
    ast.Eq: 'eq',
    ast.NotEq: 'ne',
}

_UNARY_AST: t.Final[dict[type[ast.unaryop], OperationKind]] = {
    ast.USub: 'neg',
    ast.UAdd: 'pos',
    ast.Not: 'not',
}

_UNARY_OPERATIONS: t.Final = frozenset({'neg', 'pos', 'not'})

_PRIMITIVE_OF: t.Final[dict[type, type]] = {Int: int, Float: float, Bool: bool, Str: str}

_LIST_TYPES: t.Final = (list, DataList, OrmList)
_DICT_TYPES: t.Final = (dict, DataDict, OrmDict)


def _collection_result_shape(element: LeafShape, *, kind: t.Literal['list', 'dict']) -> LeafShape:
    """Return the static contract of a collection built from one element contract.

    Collections stay plain Python at runtime, but a direct owned member (one concrete
    :class:`DataNode` element, the same rule as ``_owned_container_type``) declares an
    owned ``DataList``/``DataDict`` contract so downstream ``list[Node]``/``dict[str, Node]``
    task inputs validate. Primitives and nested collections keep plain ``list``/``dict``.
    """
    kinds = list(element.types) if element.types is not None else []
    if len(kinds) == 1 and issubclass(kinds[0], DataNode) and element.element is None:
        owned = DataList if kind == 'list' else DataDict
        return LeafShape(types=(owned,), element=element)
    plain = list if kind == 'list' else dict
    return LeafShape(types=(plain,), element=element)


def compile_expression(node: ast.expr, resolve: Resolver) -> tuple[dict[str, t.Any], dict[str, Shape]]:
    """Compile one expression to its closed JSON tree and referenced input ports.

    Free names resolve through ``resolve``, which receives each :class:`ast.Name`
    node outside comprehension bindings and returns its expression input port and
    declared shape. Comprehension targets bind as locals instead and never reach
    ``resolve``.

    :param node: the expression to compile; statements and task calls are rejected.
    :param resolve: maps each free name node to its ``(port, shape)`` pair.
    :return: the serialized expression and its ``port`` to ``Shape`` inputs.
    :raises GraphTypeCheckError: for unsupported syntax, with the offending source.
    """
    refs: dict[str, Shape] = {}
    compiled = _compile(node, frozenset(), resolve, refs)
    return compiled, refs


def infer_expression_shape(expression: Expression, inputs: Mapping[str, Shape]) -> Shape:
    """Infer the static result contract of a compiled expression.

    :param expression: the closed tree from :func:`compile_expression`.
    :param inputs: the declared shape of each referenced input port.
    :return: the result shape; collections carry their ``element`` contract.
    :raises GraphTypeCheckError: for malformed trees, unknown ports, or ill-typed uses.
    """
    return _infer(_checked_tree(expression, runtime=False), inputs, {})


def evaluate_expression(expression: Expression, inputs: Mapping[str, object]) -> object:
    """Evaluate a compiled expression over runtime values without mutating them.

    ``orm.List``/``orm.Dict`` unwrap to plain JSON; ``DataList``/``DataDict`` iterate
    and index through their member nodes. Scalar arithmetic unwraps through
    :func:`evaluate_operation`. Comprehensions run eagerly in this call.

    :param expression: the closed tree from :func:`compile_expression`.
    :param inputs: the runtime value of each referenced input port.
    :return: a plain scalar, list, or dict; selected items may be referenced nodes.
    :raises GraphRuntimeError: for malformed trees and failing runtime values.
    """
    result = _evaluate(_checked_tree(expression, runtime=True), inputs, {})
    _check_finite_result(result)
    return result


def _check_finite_result(value: object) -> None:
    """Keep newly unwrapped values finite without traversing referenced data nodes."""
    if type(value) is float and not math.isfinite(value):
        msg = 'inline expression produced a non-finite result.'
        raise GraphRuntimeError(msg)
    if type(value) is list:
        for item in value:
            _check_finite_result(item)
    elif type(value) is dict:
        for item in value.values():
            _check_finite_result(item)


def _checked_tree(tree: object, *, runtime: bool) -> dict[str, t.Any]:
    """Return one validated tree mapping, rejecting anything else closed."""
    if not isinstance(tree, Mapping):
        msg = f'malformed expression; expected a mapping, got `{type(tree).__name__}`.'
        if runtime:
            raise GraphRuntimeError(msg)
        raise GraphTypeCheckError(msg)
    return dict(tree)


def _source_snippet(node: ast.AST) -> str:
    """Return the source excerpt of one rejected node, when it unparses."""
    try:
        return ast.unparse(node)
    except (ValueError, TypeError, SyntaxError, MemoryError, RecursionError):
        return type(node).__name__


def _fail_compile(node: ast.AST, reason: str) -> t.NoReturn:
    """Raise a type error naming the offending source excerpt."""
    msg = f'{reason}; got `{_source_snippet(node)}`.'
    raise GraphTypeCheckError(msg)


def _fail_runtime(message: str) -> t.NoReturn:
    """Raise a runtime error for a failing expression value."""
    raise GraphRuntimeError(message)


def _checked_resolve(node: ast.Name, resolve: Resolver, refs: dict[str, Shape]) -> dict[str, t.Any]:
    """Resolve one free name to its port reference, recording its declared shape."""
    resolved = resolve(node)
    port_raw: object = resolved[0]
    shape_raw: object = resolved[1]
    if not isinstance(port_raw, str) or not port_raw or not isinstance(shape_raw, (LeafShape, NamespaceShape)):
        msg = f'resolving `{node.id}` must return a `(port, Shape)` pair.'
        raise GraphTypeCheckError(msg)
    if port_raw in refs and refs[port_raw] != shape_raw:
        msg = f'resolving `{node.id}` disagrees about port `{port_raw}`.'
        raise GraphTypeCheckError(msg)
    refs[port_raw] = shape_raw
    return {'tag': 'ref', 'port': port_raw}


def _compile(node: ast.expr, bound: frozenset[str], resolve: Resolver, refs: dict[str, Shape]) -> dict[str, t.Any]:
    """Compile one source node with comprehension locals in ``bound``."""
    if isinstance(node, ast.Name):
        if node.id in bound:
            return {'tag': 'local', 'name': node.id}
        return _checked_resolve(node, resolve, refs)
    if isinstance(node, ast.Constant):
        return _compile_constant(node)
    if isinstance(node, ast.BinOp):
        operation = _BINARY_AST.get(type(node.op))
        if operation is None:
            _fail_compile(node, 'only `+`, `-`, `*`, `//`, and `%` compute inline; put this operator in a task instead')
        assert operation is not None
        return {
            'tag': 'binary',
            'op': operation,
            'left': _compile(node.left, bound, resolve, refs),
            'right': _compile(node.right, bound, resolve, refs),
        }
    if isinstance(node, ast.Compare):
        return _compile_compare(node, bound, resolve, refs)
    if isinstance(node, ast.UnaryOp):
        operation = _UNARY_AST.get(type(node.op))
        if operation is None:
            _fail_compile(node, 'only unary `-`, `+`, and `not` compute inline; put this operator in a task instead')
        assert operation is not None
        return {'tag': 'unary', 'op': operation, 'operand': _compile(node.operand, bound, resolve, refs)}
    if isinstance(node, ast.Subscript):
        if isinstance(node.slice, ast.Slice):
            _fail_compile(node, 'slices have no fixed shape; index one element instead')
        return {
            'tag': 'index',
            'target': _compile(node.value, bound, resolve, refs),
            'index': _compile(node.slice, bound, resolve, refs),
        }
    if isinstance(node, ast.Attribute):
        if not node.attr or node.attr.startswith('_'):
            _fail_compile(node, 'attribute reads expose public fields only, not underscore names')
        return {'tag': 'attribute', 'target': _compile(node.value, bound, resolve, refs), 'attr': node.attr}
    if isinstance(node, (ast.List, ast.Tuple)):
        return {'tag': 'list', 'items': [_compile(item, bound, resolve, refs) for item in node.elts]}
    if isinstance(node, ast.Dict):
        return _compile_dict(node, bound, resolve, refs)
    if isinstance(node, ast.ListComp):
        return _compile_listcomp(node, bound, resolve, refs)
    if isinstance(node, ast.DictComp):
        return _compile_dictcomp(node, bound, resolve, refs)
    if isinstance(node, ast.Call):
        _fail_compile(node, 'calls never run inline; compute call results in a task instead')
    if isinstance(node, ast.BoolOp):
        _fail_compile(node, 'boolean `and`/`or` combine control flow; branch on comparisons instead')
    if isinstance(node, ast.IfExp):
        _fail_compile(node, 'conditional values branch control flow; use a branch instead')
    if isinstance(node, (ast.SetComp, ast.GeneratorExp, ast.Set)):
        _fail_compile(node, 'only list and dict comprehensions collect inline; use those instead')
    _fail_compile(node, 'put this calculation in a task instead')


def _compile_constant(node: ast.Constant) -> dict[str, t.Any]:
    """Compile one literal, rejecting non-finite and non-scalar values."""
    value = node.value
    if value is None or type(value) is bool or type(value) is int or type(value) is str:
        return {'tag': 'const', 'value': value}
    if type(value) is float:
        try:
            const_result_shape(value)
        except GraphTypeCheckError:
            _fail_compile(node, 'inline numbers must be finite; compute non-finite values in tasks instead')
        return {'tag': 'const', 'value': value}
    _fail_compile(node, 'inline literals bind finite numbers, strings, booleans, and `None`')


def _compile_compare(
    node: ast.Compare, bound: frozenset[str], resolve: Resolver, refs: dict[str, Shape]
) -> dict[str, t.Any]:
    """Compile one two-sided comparison, rejecting chains and identity tests."""
    if len(node.ops) != 1 or len(node.comparators) != 1:
        _fail_compile(node, 'comparisons compare two values at a time; compare two values per expression instead')
    operation = _COMPARISON_AST.get(type(node.ops[0]))
    if operation is None:
        _fail_compile(node, 'only `<`, `<=`, `>`, `>=`, `==`, and `!=` compare inline; put this test in a task instead')
    assert operation is not None
    return {
        'tag': 'binary',
        'op': operation,
        'left': _compile(node.left, bound, resolve, refs),
        'right': _compile(node.comparators[0], bound, resolve, refs),
    }


def _compile_dict(node: ast.Dict, bound: frozenset[str], resolve: Resolver, refs: dict[str, Shape]) -> dict[str, t.Any]:
    """Compile one dict literal with string keys."""
    entries = []
    for key, value in zip(node.keys, node.values, strict=True):
        if key is None:
            _fail_compile(node, 'dict unpacking hides its keys; write each key out instead')
        assert isinstance(key, ast.expr)
        if not (isinstance(key, ast.Constant) and type(key.value) is str):
            _fail_compile(node, 'dict literal keys must be quoted names; compute dynamic keys in tasks')
        entries.append({'key': _compile(key, bound, resolve, refs), 'value': _compile(value, bound, resolve, refs)})
    return {'tag': 'dict', 'entries': entries}


def _is_items_call(node: ast.expr) -> t.TypeGuard[ast.Call]:
    """Return whether an iterator spells ``mapping.items()`` with no arguments."""
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == 'items'
        and not node.args
        and not node.keywords
    )


def _compile_target(target: ast.expr, *, pairs: bool, node: ast.AST) -> str | list[str]:
    """Compile one comprehension target to bound name(s)."""
    if isinstance(target, ast.Name):
        if pairs:
            _fail_compile(node, 'pair iteration binds two names; write `for key, value in mapping.items()` instead')
        if not target.id.isidentifier() or target.id.startswith('_'):
            _fail_compile(node, 'comprehension targets bind plain public names')
        return target.id
    if isinstance(target, (ast.Tuple, ast.List)) and pairs and len(target.elts) == 2:
        names = []
        for element in target.elts:
            if not isinstance(element, ast.Name):
                _fail_compile(node, 'pair iteration binds two plain names')
            assert isinstance(element, ast.Name)
            names.append(element.id)
        if names[0] == names[1]:
            _fail_compile(node, 'pair iteration binds two distinct names')
        if any(not name.isidentifier() or name.startswith('_') for name in names):
            _fail_compile(node, 'comprehension targets bind plain public names')
        return names
    _fail_compile(target, 'comprehensions bind one plain name, or two names over `mapping.items()`')


def _compile_generators(
    generators: list[ast.comprehension], bound: frozenset[str], resolve: Resolver, refs: dict[str, Shape]
) -> tuple[list[dict[str, t.Any]], frozenset[str]]:
    """Compile comprehension generators, threading bound locals through nesting."""
    compiled_generators: list[dict[str, t.Any]] = []
    current = bound
    for generator in generators:
        if generator.is_async:
            _fail_compile(generator, 'async iteration never runs inline; iterate plain collections instead')
        if _is_items_call(generator.iter):
            func = generator.iter.func
            assert isinstance(func, ast.Attribute)
            source = func.value
            pairs = True
        else:
            source = generator.iter
            pairs = False
        target = _compile_target(generator.target, pairs=pairs, node=generator)
        names = [target] if isinstance(target, str) else list(target)
        if len(set(names)) != len(names):
            _fail_compile(generator, 'comprehension targets bind distinct names')
        compiled_iter = _compile(source, current, resolve, refs)
        extended = current | frozenset(names)
        compiled_ifs = [_compile(condition, extended, resolve, refs) for condition in generator.ifs]
        compiled_generators.append({'target': target, 'iter': compiled_iter, 'ifs': compiled_ifs, 'pairs': pairs})
        current = extended
    return compiled_generators, current


def _compile_listcomp(
    node: ast.ListComp, bound: frozenset[str], resolve: Resolver, refs: dict[str, Shape]
) -> dict[str, t.Any]:
    """Compile one list comprehension with filtered, nested generators."""
    if not node.generators:
        _fail_compile(node, 'a comprehension iterates at least once')
    generators, extended = _compile_generators(node.generators, bound, resolve, refs)
    return {'tag': 'listcomp', 'elt': _compile(node.elt, extended, resolve, refs), 'generators': generators}


def _compile_dictcomp(
    node: ast.DictComp, bound: frozenset[str], resolve: Resolver, refs: dict[str, Shape]
) -> dict[str, t.Any]:
    """Compile one dict comprehension with string keys."""
    if not node.generators:
        _fail_compile(node, 'a comprehension iterates at least once')
    generators, extended = _compile_generators(node.generators, bound, resolve, refs)
    return {
        'tag': 'dictcomp',
        'key': _compile(node.key, extended, resolve, refs),
        'value': _compile(node.value, extended, resolve, refs),
        'generators': generators,
    }


def _require_keys(node: dict[str, t.Any], expected: frozenset[str], *, runtime: bool) -> None:
    """Reject malformed trees missing keys, carrying extras, or naming no tag."""
    error = GraphRuntimeError if runtime else GraphTypeCheckError
    if set(node) != expected | {'tag'}:
        msg = f'malformed expression `{node.get("tag")}`; expected keys {sorted(expected | {"tag"})}.'
        raise error(msg)


def _infer_ref(node: dict[str, t.Any], inputs: Mapping[str, Shape]) -> Shape:
    """Return the declared shape of one referenced input port."""
    _require_keys(node, frozenset({'port'}), runtime=False)
    port = node['port']
    if not isinstance(port, str):
        msg = f'malformed expression `ref`; port names are strings, got `{type(port).__name__}`.'
        raise GraphTypeCheckError(msg)
    try:
        return inputs[port]
    except KeyError as exception:
        msg = f'expression reads unknown input `{port}`.'
        raise GraphTypeCheckError(msg) from exception


def _infer_local(node: dict[str, t.Any], scope: Mapping[str, Shape]) -> Shape:
    """Return the element shape one comprehension variable carries."""
    _require_keys(node, frozenset({'name'}), runtime=False)
    name = node['name']
    if not isinstance(name, str):
        msg = 'malformed expression `local`; variable names are strings.'
        raise GraphTypeCheckError(msg)
    try:
        return scope[name]
    except KeyError as exception:
        msg = f'expression variable `{name}` is not bound here.'
        raise GraphTypeCheckError(msg) from exception


def _infer_const(node: dict[str, t.Any]) -> LeafShape:
    """Return the contract of one bound scalar literal."""
    _require_keys(node, frozenset({'value'}), runtime=False)
    try:
        return const_result_shape(node['value'])
    except GraphTypeCheckError as exception:
        msg = f'malformed expression `const` ({exception}).'
        raise GraphTypeCheckError(msg) from exception


def _collection_kind(shape: Shape, *, what: str) -> t.Literal['list', 'dict']:
    """Return whether a collection contract iterates members or keys."""
    if isinstance(shape, NamespaceShape):
        msg = f'{what} works on collections, not namespaces; index a collection input instead.'
        raise GraphTypeCheckError(msg)
    assert isinstance(shape, LeafShape)
    if shape.element is None:
        msg = f'{what} needs a declared element type; annotate the collection as `list[T]` or `dict[str, T]` instead.'
        raise GraphTypeCheckError(msg)
    kinds = {kind for kind in shape.types or () if kind is not type(None)}
    if not kinds:
        msg = (
            f'{what} needs a declared collection type; annotate the collection as `list[T]` or `dict[str, T]` instead.'
        )
        raise GraphTypeCheckError(msg)
    list_like = {kind for kind in kinds if issubclass(kind, _LIST_TYPES)}
    dict_like = {kind for kind in kinds if issubclass(kind, _DICT_TYPES)}
    if kinds != list_like | dict_like:
        names = ', '.join(f'`{kind.__name__}`' for kind in kinds)
        msg = f'{what} reads `list`/`DataList` and `dict`/`DataDict` collections, not {names}.'
        raise GraphTypeCheckError(msg)
    if bool(list_like) == bool(dict_like):
        msg = f'{what} needs one collection kind; intersecting list and dict contracts stays a task concern.'
        raise GraphTypeCheckError(msg)
    return 'list' if list_like else 'dict'


def _require_index_kind(index: Shape, kind: t.Literal['list', 'dict']) -> None:
    """Reject indices of the wrong static kind for one collection."""
    if not isinstance(index, LeafShape):
        msg = f'indexing a {kind} needs an `int` index or a `str` key, not a namespace.'
        raise GraphTypeCheckError(msg)
    kinds = {kind for kind in index.types or () if kind is not type(None)}
    expected = (int, Int) if kind == 'list' else (str, Str)
    names = '`int` index' if kind == 'list' else '`str` key'
    if not kinds or any(not issubclass(kind, expected) for kind in kinds):
        msg = f'indexing a {kind} needs an {names}.'
        raise GraphTypeCheckError(msg)


def _infer_index(node: dict[str, t.Any], inputs: Mapping[str, Shape], scope: Mapping[str, Shape]) -> Shape:
    """Return the element contract of one indexed collection."""
    _require_keys(node, frozenset({'target', 'index'}), runtime=False)
    target = _infer(node['target'], inputs, scope)
    kind = _collection_kind(target, what='indexing')
    _require_index_kind(_infer(node['index'], inputs, scope), kind)
    assert isinstance(target, LeafShape) and target.element is not None
    return target.element


def _infer_attribute(node: dict[str, t.Any], inputs: Mapping[str, Shape], scope: Mapping[str, Shape]) -> Shape:
    """Return the contract of one public field, property, or scalar `.value`."""
    _require_keys(node, frozenset({'target', 'attr'}), runtime=False)
    attr = node['attr']
    if not isinstance(attr, str) or not attr or attr.startswith('_'):
        msg = 'attribute reads expose public fields only, not underscore names.'
        raise GraphTypeCheckError(msg)
    target = _infer(node['target'], inputs, scope)
    if isinstance(target, NamespaceShape):
        try:
            return target.select(attr)
        except KeyError as exception:
            msg = f'`{attr}` is not a declared field here; check the spelling instead.'
            raise GraphTypeCheckError(msg) from exception
    assert isinstance(target, LeafShape)
    if attr == 'value':
        return _infer_scalar_value(target)
    return _infer_property(target, attr)


def _infer_scalar_value(shape: LeafShape) -> LeafShape:
    """Return the primitive contract of one scalar node `.value`."""
    kinds = [kind for kind in shape.types or () if kind is not type(None)]
    if kinds and all(kind in _PRIMITIVE_OF for kind in kinds):
        primitives: list[type] = []
        for kind in kinds:
            primitive = _PRIMITIVE_OF[kind]
            if primitive not in primitives:
                primitives.append(primitive)
        return LeafShape(types=tuple(primitives))
    names = ' or '.join(f'`{kind.__name__}`' for kind in kinds) if kinds else 'an unknown type'
    msg = f'`.value` reads scalar nodes, not {names}; check the spelling instead.'
    raise GraphTypeCheckError(msg)


def _infer_property(shape: LeafShape, attr: str) -> Shape:
    """Return the contract of one annotated property shared by every declared type."""
    kinds = [kind for kind in shape.types or () if kind is not type(None)]
    if not kinds:
        msg = f'`{attr}` needs a declared node type; annotate the value instead of guessing.'
        raise GraphTypeCheckError(msg)
    resolved: Shape | None = None
    for kind in kinds:
        try:
            found = inspect.getattr_static(kind, attr)
        except AttributeError as exception:
            msg = f'`{getattr(kind, "__name__", kind)}` declares no property `{attr}`; check the spelling instead.'
            raise GraphTypeCheckError(msg) from exception
        if not isinstance(found, property) or found.fget is None:
            msg = f'`{attr}` is not a declared property; methods and general calls stay task concerns.'
            raise GraphTypeCheckError(msg)
        try:
            hints = t.get_type_hints(found.fget, include_extras=True)
        except (NameError, AttributeError, TypeError, SyntaxError) as exception:
            msg = f'property `{attr}` needs a resolvable return annotation ({exception}).'
            raise GraphTypeCheckError(msg) from exception
        if 'return' not in hints:
            msg = f'property `{attr}` needs an annotated return type; annotate it instead of guessing.'
            raise GraphTypeCheckError(msg)
        contract = shape_for_annotation(hints['return'])
        if resolved is None:
            resolved = contract
        elif resolved != contract:
            msg = f'property `{attr}` disagrees across declared types; narrow the annotation instead.'
            raise GraphTypeCheckError(msg)
    assert resolved is not None
    return resolved


def _infer_unified(items: list[dict[str, t.Any]], inputs: Mapping[str, Shape], scope: Mapping[str, Shape]) -> Shape:
    """Return the shared contract of literal items, rejecting heterogeneous mixes."""
    if not items:
        msg = 'empty literals declare no element type; build empty collections in a task instead.'
        raise GraphTypeCheckError(msg)
    first = _infer(items[0], inputs, scope)
    for item in items[1:]:
        if _infer(item, inputs, scope) != first:
            msg = 'heterogeneous literals have no single element type; build mixed collections in a task instead.'
            raise GraphTypeCheckError(msg)
    return first


def _check_generator(
    generator: t.Any, *, runtime: bool
) -> tuple[str | list[str], dict[str, t.Any], list[dict[str, t.Any]], bool]:
    """Validate one comprehension generator mapping, returning its parts."""
    error = GraphRuntimeError if runtime else GraphTypeCheckError
    if not isinstance(generator, Mapping) or set(generator) != {'target', 'iter', 'ifs', 'pairs'}:
        msg = 'malformed comprehension; generators bind `target`, `iter`, `ifs`, and `pairs`.'
        raise error(msg)
    target, iterable, filters, pairs = generator['target'], generator['iter'], generator['ifs'], generator['pairs']
    if isinstance(target, str):
        names = [target]
    elif isinstance(target, list) and len(target) == 2 and all(isinstance(name, str) for name in target):
        names = list(target)
    else:
        msg = 'malformed comprehension; targets bind one name or two names over `.items()`.'
        raise error(msg)
    if not isinstance(iterable, Mapping) or not isinstance(filters, list) or not isinstance(pairs, bool):
        msg = 'malformed comprehension generator.'
        raise error(msg)
    if (len(names) == 2) != pairs:
        msg = 'pair iteration binds two names over `.items()`; plain iteration binds one.'
        raise error(msg)
    return target, dict(iterable), [dict(condition) for condition in filters], pairs


def _bind_generator(
    target: str | list[str], kind: t.Literal['list', 'dict'], element: Shape, *, pairs: bool
) -> dict[str, Shape]:
    """Return the locals one generator binds: members, keys, or key/value pairs."""
    if pairs:
        assert isinstance(target, list)
        assert isinstance(element, LeafShape)
        return {target[0]: LeafShape(types=(str,)), target[1]: element}
    assert isinstance(target, str)
    if kind == 'list':
        assert isinstance(element, LeafShape)
        return {target: element}
    return {target: LeafShape(types=(str,))}


def _infer_generators(
    generators: t.Any, inputs: Mapping[str, Shape], scope: Mapping[str, Shape]
) -> tuple[list[tuple[str | list[str], Shape, list[Shape], bool]], dict[str, Shape]]:
    """Infer each generator's bound locals, threading them through nesting and filters."""
    if not isinstance(generators, list) or not generators:
        msg = 'a comprehension iterates at least once.'
        raise GraphTypeCheckError(msg)
    current = dict(scope)
    rewritten: list[tuple[str | list[str], Shape, list[Shape], bool]] = []
    for generator in generators:
        target, iterable, filters, pairs = _check_generator(generator, runtime=False)
        collection = _infer(iterable, inputs, current)
        kind = _collection_kind(collection, what='iteration')
        assert isinstance(collection, LeafShape) and collection.element is not None
        if kind == 'list' and pairs:
            msg = 'pair iteration reads mappings; iterate a mapping with `.items()` instead.'
            raise GraphTypeCheckError(msg)
        bound = _bind_generator(target, kind, collection.element, pairs=pairs)
        current.update(bound)
        for condition in filters:
            narrowed = _infer(condition, inputs, current)
            if not isinstance(narrowed, LeafShape):
                msg = 'comprehension filters keep true/false values; compare values or read a boolean instead.'
                raise GraphTypeCheckError(msg)
            kinds = [kind for kind in narrowed.types or () if kind is not type(None)]
            if not kinds or not all(kind in (bool, Bool) for kind in kinds):
                msg = 'comprehension filters keep true/false values; compare values or read a boolean instead.'
                raise GraphTypeCheckError(msg)
        rewritten.append((target, collection, [], pairs))
    return rewritten, current


def _infer(node: object, inputs: Mapping[str, Shape], scope: Mapping[str, Shape]) -> Shape:
    """Infer the contract of one validated tree node."""
    tree = _checked_tree(node, runtime=False)
    tag = tree.get('tag')
    if tag == 'ref':
        return _infer_ref(tree, inputs)
    if tag == 'local':
        return _infer_local(tree, scope)
    if tag == 'const':
        return _infer_const(tree)
    if tag == 'binary':
        _require_keys(tree, frozenset({'op', 'left', 'right'}), runtime=False)
        if tree['op'] not in BINARY_OPERATIONS:
            msg = f'malformed expression; unknown operator `{tree["op"]}`.'
            raise GraphTypeCheckError(msg)
        left, right = _infer(tree['left'], inputs, scope), _infer(tree['right'], inputs, scope)
        try:
            return infer_operation_shape(tree['op'], (left, right))
        except GraphTypeCheckError as exception:
            msg = f'cannot compute `{tree["op"]}` here ({exception}).'
            raise GraphTypeCheckError(msg) from exception
    if tag == 'unary':
        _require_keys(tree, frozenset({'op', 'operand'}), runtime=False)
        if tree['op'] not in _UNARY_OPERATIONS:
            msg = f'malformed expression; unknown operator `{tree["op"]}`.'
            raise GraphTypeCheckError(msg)
        try:
            return infer_operation_shape(tree['op'], (_infer(tree['operand'], inputs, scope),))
        except GraphTypeCheckError as exception:
            msg = f'cannot compute `{tree["op"]}` here ({exception}).'
            raise GraphTypeCheckError(msg) from exception
    if tag == 'index':
        return _infer_index(tree, inputs, scope)
    if tag == 'attribute':
        return _infer_attribute(tree, inputs, scope)
    if tag == 'list':
        _require_keys(tree, frozenset({'items'}), runtime=False)
        if not isinstance(tree['items'], list):
            msg = 'malformed expression `list`; items form a list.'
            raise GraphTypeCheckError(msg)
        element = _infer_unified([dict(item) for item in tree['items']], inputs, scope) if tree['items'] else None
        if element is None:
            return LeafShape(types=(list,), element=None)
        assert isinstance(element, LeafShape)
        return _collection_result_shape(element, kind='list')
    if tag == 'dict':
        _require_keys(tree, frozenset({'entries'}), runtime=False)
        return _infer_dict_shape(tree, inputs, scope)
    if tag == 'listcomp':
        _require_keys(tree, frozenset({'elt', 'generators'}), runtime=False)
        _, extended = _infer_generators(tree['generators'], inputs, scope)
        element = _infer(tree['elt'], inputs, extended)
        if not isinstance(element, LeafShape):
            msg = 'comprehensions collect scalar leaves; regroup namespaces in outputs instead.'
            raise GraphTypeCheckError(msg)
        return _collection_result_shape(element, kind='list')
    if tag == 'dictcomp':
        _require_keys(tree, frozenset({'key', 'value', 'generators'}), runtime=False)
        _, extended = _infer_generators(tree['generators'], inputs, scope)
        key_shape = _infer(tree['key'], inputs, extended)
        if not (
            isinstance(key_shape, LeafShape)
            and key_shape.types
            and all(kind in (str, Str) for kind in key_shape.types if kind is not type(None))
        ):
            msg = 'dict comprehensions key on strings; key on a string instead.'
            raise GraphTypeCheckError(msg)
        value_shape = _infer(tree['value'], inputs, extended)
        if not isinstance(value_shape, LeafShape):
            msg = 'comprehensions collect scalar leaves; regroup namespaces in outputs instead.'
            raise GraphTypeCheckError(msg)
        return _collection_result_shape(value_shape, kind='dict')
    msg = f'malformed expression; unknown tag `{tag}`.'
    raise GraphTypeCheckError(msg)


def _infer_dict_shape(tree: dict[str, t.Any], inputs: Mapping[str, Shape], scope: Mapping[str, Shape]) -> LeafShape:
    """Return the contract of one dict literal with string keys."""
    entries = tree['entries']
    if not isinstance(entries, list):
        msg = 'malformed expression `dict`; entries form a list.'
        raise GraphTypeCheckError(msg)
    values = []
    for entry in entries:
        if not isinstance(entry, Mapping) or set(entry) != {'key', 'value'}:
            msg = 'malformed expression `dict`; entries pair `key` and `value`.'
            raise GraphTypeCheckError(msg)
        key_shape = _infer(entry['key'], inputs, scope)
        if not (
            isinstance(key_shape, LeafShape)
            and key_shape.types
            and all(kind in (str, Str) for kind in key_shape.types if kind is not type(None))
        ):
            msg = 'dict literals key on strings; key on a string instead.'
            raise GraphTypeCheckError(msg)
        values.append(entry['value'])
    element = _infer_unified([dict(value) for value in values], inputs, scope) if values else None
    if element is None:
        return LeafShape(types=(dict,), element=None)
    assert isinstance(element, LeafShape)
    return _collection_result_shape(element, kind='dict')


def _eval_ref(node: dict[str, t.Any], inputs: Mapping[str, object]) -> object:
    """Return one input value, rejecting unknown ports."""
    _require_keys(node, frozenset({'port'}), runtime=True)
    port = node['port']
    if not isinstance(port, str):
        _fail_runtime(f'malformed expression `ref`; port names are strings, got `{type(port).__name__}`.')
    try:
        return inputs[port]
    except KeyError:
        _fail_runtime(f'expression is missing input `{port}`.')


def _eval_local(node: dict[str, t.Any], scope: Mapping[str, object]) -> object:
    """Return one bound comprehension variable."""
    _require_keys(node, frozenset({'name'}), runtime=True)
    name = node['name']
    if not isinstance(name, str):
        _fail_runtime('malformed expression `local`; variable names are strings.')
    try:
        return scope[name]
    except KeyError:
        _fail_runtime(f'expression variable `{name}` is not bound here.')


def _eval_const(node: dict[str, t.Any]) -> object:
    """Return one validated scalar literal."""
    _require_keys(node, frozenset({'value'}), runtime=True)
    value = node['value']
    if value is None or type(value) is bool or type(value) is int or type(value) is str:
        return value
    if type(value) is float:
        try:
            const_result_shape(value)
        except GraphTypeCheckError as exception:
            _fail_runtime(f'malformed expression `const` ({exception}).')
        return value
    _fail_runtime(f'malformed expression `const`; cannot bind `{type(value).__name__}`.')


def _sequence_items(value: object, *, what: str) -> list[t.Any]:
    """Materialize the members of one list-like runtime value without mutating it."""
    if isinstance(value, DataList):
        return list(value)
    if isinstance(value, OrmList):
        return list(value.get_list())
    if type(value) is list:
        return list(value)
    _fail_runtime(f'{what} iterates `list` collections, not `{type(value).__name__}`.')


def _mapping_items(value: object, *, what: str) -> dict[str, t.Any]:
    """Materialize one dict-like runtime value without mutating it."""
    if isinstance(value, DataDict):
        return {key: value[key] for key in value}
    if isinstance(value, OrmDict):
        return dict(value.get_dict())
    if type(value) is dict:
        return dict(value)
    _fail_runtime(f'{what} reads `dict` collections, not `{type(value).__name__}`.')


def _unwrap_index_scalar(value: object) -> object:
    """Unwrap a stored scalar index to the plain value indexing computes over.

    Only the known ``Int``/``Str`` index spellings unwrap; ``Bool`` and anything else
    pass through to the exact-type checks below, which reject them loudly.
    """
    if isinstance(value, Int):
        return value.value
    if isinstance(value, Str):
        return value.value
    return value


def _eval_index(node: dict[str, t.Any], inputs: Mapping[str, object], scope: Mapping[str, object]) -> object:
    """Index one list by integer (negatives allowed) or one dict by string key."""
    _require_keys(node, frozenset({'target', 'index'}), runtime=True)
    target = _evaluate(dict(node['target']), inputs, scope)
    position = _unwrap_index_scalar(_evaluate(dict(node['index']), inputs, scope))
    if isinstance(target, DataDict) or isinstance(target, OrmDict) or type(target) is dict:
        if type(position) is not str:
            _fail_runtime(f'indexing a dict needs a `str` key, not `{type(position).__name__}`.')
        mapping = _mapping_items(target, what='indexing')
        try:
            return mapping[position]
        except KeyError:
            _fail_runtime(f'indexing is missing key `{position}`.')
    if isinstance(target, (DataList, OrmList)) or type(target) is list:
        if type(position) is bool or type(position) is not int:
            _fail_runtime(f'indexing a list needs an `int` index, not `{type(position).__name__}`.')
        members = _sequence_items(target, what='indexing')
        try:
            return members[position]
        except IndexError:
            _fail_runtime(f'indexing is out of range for index `{position}`.')
    _fail_runtime(f'indexing reads `list` and `dict` collections, not `{type(target).__name__}`.')


def _eval_attribute(node: dict[str, t.Any], inputs: Mapping[str, object], scope: Mapping[str, object]) -> object:
    """Read one public field, property, scalar `.value`, or namespace entry."""
    _require_keys(node, frozenset({'target', 'attr'}), runtime=True)
    attr = node['attr']
    if not isinstance(attr, str) or not attr or attr.startswith('_'):
        _fail_runtime('attribute reads expose public fields only, not underscore names.')
    target = _evaluate(dict(node['target']), inputs, scope)
    if isinstance(target, DataDict):
        try:
            return target[attr]
        except KeyError:
            _fail_runtime(f'`{attr}` is not a declared entry here.')
    if isinstance(target, OrmDict):
        mapping = _mapping_items(target, what='attribute reads')
        try:
            return mapping[attr]
        except KeyError:
            _fail_runtime(f'`{attr}` is not a declared entry here.')
    if type(target) is dict:
        try:
            return target[attr]
        except KeyError:
            _fail_runtime(f'`{attr}` is not a declared field here.')
    if isinstance(target, (DataList, OrmList)) or type(target) is list:
        _fail_runtime(f'`{attr}` is not a declared field of a list.')
    try:
        found = inspect.getattr_static(target, attr)
    except AttributeError:
        _fail_runtime(f'`{attr}` is not a declared field here.')
    if isinstance(found, property) and found.fget is not None:
        value = found.fget(target)
    else:
        value = getattr(target, attr)
    if callable(value):
        _fail_runtime(f'`{attr}` is not a declared property; methods never run inline.')
    return value


def _eval_sequence(
    source: dict[str, t.Any], inputs: Mapping[str, object], scope: Mapping[str, object], *, pairs: bool
) -> list[t.Any]:
    """Materialize one generator source as members, keys, or key/value pairs."""
    value = _evaluate(source, inputs, scope)
    if isinstance(value, DataDict) or isinstance(value, OrmDict) or type(value) is dict:
        mapping = _mapping_items(value, what='iteration')
        return list(mapping.items()) if pairs else list(mapping)
    if isinstance(value, (DataList, OrmList)) or type(value) is list:
        return _sequence_items(value, what='iteration')
    _fail_runtime(f'iteration reads `list` and `dict` collections, not `{type(value).__name__}`.')


def _eval_generators(
    generators: list[dict[str, t.Any]],
    inputs: Mapping[str, object],
    scope: Mapping[str, object],
    emit: Callable[[Mapping[str, object]], None],
) -> None:
    """Execute comprehension generators depth-first inside this placement."""

    def visit(depth: int, current: dict[str, object]) -> None:
        """Bind one generator level, then recurse or emit the element."""
        if depth == len(generators):
            emit(current)
            return
        target, iterable, filters, pairs = _check_generator(generators[depth], runtime=True)
        entries = _eval_sequence(dict(iterable), inputs, current, pairs=pairs)
        names = [target] if isinstance(target, str) else list(target)
        for entry in entries:
            if pairs:
                key, member = entry
                if type(key) is not str:
                    _fail_runtime('pair iteration keys on strings.')
                if not isinstance(target, list):
                    _fail_runtime('malformed comprehension; pair targets bind two names.')
                following = dict(current)
                following[target[0]], following[target[1]] = key, member
            else:
                if isinstance(target, list):
                    _fail_runtime('malformed comprehension; plain iteration binds one name.')
                assert isinstance(target, str)
                if isinstance(entry, tuple):
                    _fail_runtime('iterate pairs with `for key, value in mapping.items()`.')
                following = dict(current)
                following[target] = entry
            kept = True
            for condition in filters:
                verdict = _evaluate(dict(condition), inputs, following)
                if isinstance(verdict, Bool):
                    verdict = verdict.value
                if type(verdict) is not bool:
                    _fail_runtime('comprehension filters keep true/false values.')
                if not verdict:
                    kept = False
                    break
            if kept:
                visit(depth + 1, following)
        _ = names

    visit(0, dict(scope))


def _evaluate(node: object, inputs: Mapping[str, object], scope: Mapping[str, object]) -> object:
    """Evaluate one validated tree node with comprehension locals in ``scope``."""
    tree = _checked_tree(node, runtime=True)
    tag = tree.get('tag')
    if tag == 'ref':
        return _eval_ref(tree, inputs)
    if tag == 'local':
        return _eval_local(tree, scope)
    if tag == 'const':
        return _eval_const(tree)
    if tag == 'binary':
        _require_keys(tree, frozenset({'op', 'left', 'right'}), runtime=True)
        if tree['op'] not in BINARY_OPERATIONS:
            _fail_runtime(f'malformed expression; unknown operator `{tree["op"]}`.')
        left = _evaluate(dict(tree['left']), inputs, scope)
        right = _evaluate(dict(tree['right']), inputs, scope)
        return evaluate_operation(tree['op'], {'left': left, 'right': right})
    if tag == 'unary':
        _require_keys(tree, frozenset({'op', 'operand'}), runtime=True)
        if tree['op'] not in _UNARY_OPERATIONS:
            _fail_runtime(f'malformed expression; unknown operator `{tree["op"]}`.')
        return evaluate_operation(tree['op'], {OPERAND_PORT: _evaluate(dict(tree['operand']), inputs, scope)})
    if tag == 'index':
        return _eval_index(tree, inputs, scope)
    if tag == 'attribute':
        return _eval_attribute(tree, inputs, scope)
    if tag == 'list':
        _require_keys(tree, frozenset({'items'}), runtime=True)
        if not isinstance(tree['items'], list):
            _fail_runtime('malformed expression `list`; items form a list.')
        return [_evaluate(dict(item), inputs, scope) for item in tree['items']]
    if tag == 'dict':
        _require_keys(tree, frozenset({'entries'}), runtime=True)
        return _eval_dict(tree, inputs, scope)
    if tag == 'listcomp':
        _require_keys(tree, frozenset({'elt', 'generators'}), runtime=True)
        collected: list[t.Any] = []
        _eval_generators(
            [dict(generator) for generator in tree['generators']],
            inputs,
            scope,
            lambda bound: collected.append(_evaluate(dict(tree['elt']), inputs, bound)),
        )
        return collected
    if tag == 'dictcomp':
        _require_keys(tree, frozenset({'key', 'value', 'generators'}), runtime=True)
        collected_dict: dict[str, t.Any] = {}

        def _emit(bound: Mapping[str, object]) -> None:
            key = _unwrap_index_scalar(_evaluate(dict(tree['key']), inputs, bound))
            if type(key) is not str:
                _fail_runtime('dict comprehensions key on strings.')
            collected_dict[key] = _evaluate(dict(tree['value']), inputs, bound)

        _eval_generators([dict(generator) for generator in tree['generators']], inputs, scope, _emit)
        return collected_dict
    _fail_runtime(f'malformed expression; unknown tag `{tag}`.')


def _eval_dict(tree: dict[str, t.Any], inputs: Mapping[str, object], scope: Mapping[str, object]) -> dict[str, t.Any]:
    """Evaluate one dict literal, requiring string keys without mutating inputs."""
    entries = tree['entries']
    if not isinstance(entries, list):
        _fail_runtime('malformed expression `dict`; entries form a list.')
    collected: dict[str, t.Any] = {}
    for entry in entries:
        if not isinstance(entry, Mapping) or set(entry) != {'key', 'value'}:
            _fail_runtime('malformed expression `dict`; entries pair `key` and `value`.')
        key = _unwrap_index_scalar(_evaluate(entry['key'], inputs, scope))
        if type(key) is not str:
            _fail_runtime('dict literals key on strings.')
        collected[key] = _evaluate(entry['value'], inputs, scope)
    return collected
