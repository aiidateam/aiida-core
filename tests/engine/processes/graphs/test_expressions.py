###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Pure inline collection expressions: compilation, shape inference, and evaluation."""

import ast
import json

import pytest

from aiida.common.exceptions import GraphRuntimeError, GraphTypeCheckError
from aiida.engine.processes.graphs.expressions import (
    compile_expression,
    evaluate_expression,
    infer_expression_shape,
)
from aiida.engine.processes.graphs.shapes import LeafShape, NamespaceShape
from aiida.orm import Bool, DataDict, DataList, Int, Str


def _resolve(mapping: dict[str, tuple[str, object]]) -> object:
    """Return a resolver reading free names from ``mapping``."""

    def resolve(node: ast.expr) -> tuple[str, object]:
        assert isinstance(node, ast.Name)
        return mapping[node.id]

    return resolve


def _compile(source: str, mapping: dict[str, tuple[str, object]]) -> tuple[dict, dict]:
    """Compile one source expression with the given name contracts."""
    return compile_expression(ast.parse(source, mode='eval').body, _resolve(mapping))


INTS = LeafShape(types=(list,), element=LeafShape(types=(int,)))
STR_INT_MAP = LeafShape(types=(dict,), element=LeafShape(types=(int,)))


@pytest.mark.parametrize('source', ['values[0]', '[item for item in values]'])
@pytest.mark.parametrize('value', [float('nan'), float('inf')])
def test_nonfinite_collection_values_fail(source: str, value: float) -> None:
    """Selecting or collecting a non-finite primitive cannot poison checkpoint state."""
    expression, _ = _compile(
        source, {'values': ('values', LeafShape(types=(list,), element=LeafShape(types=(float,))))}
    )
    with pytest.raises(GraphRuntimeError, match='non-finite'):
        evaluate_expression(expression, {'values': [value]})


def test_compile_arithmetic_binds_refs() -> None:
    """Free names compile to port references; operators keep their spelling."""
    expression, refs = _compile('x + 1', {'x': ('x', LeafShape(types=(int,)))})
    assert expression['tag'] == 'binary' and expression['op'] == 'add'
    assert expression['left'] == {'tag': 'ref', 'port': 'x'}
    assert expression['right'] == {'tag': 'const', 'value': 1}
    assert refs == {'x': LeafShape(types=(int,))}


def test_infer_arithmetic_delegates_to_operations() -> None:
    """Scalar operators infer through the shared operation contracts."""
    expression, _ = _compile('x * y', {'x': ('x', LeafShape(types=(int,))), 'y': ('y', LeafShape(types=(int,)))})
    assert infer_expression_shape(expression, {'x': LeafShape(types=(int,)), 'y': LeafShape(types=(int,))}).types == (
        int,
    )


def test_evaluate_arithmetic_and_comparison() -> None:
    """Compiled arithmetic evaluates to plain values without mutating inputs."""
    expression, _ = _compile('x * 2 + y', {'x': ('x', LeafShape(types=(int,))), 'y': ('y', LeafShape(types=(int,)))})
    given: dict[str, object] = {'x': 3, 'y': 1}
    assert evaluate_expression(expression, given) == 7
    assert given == {'x': 3, 'y': 1}


@pytest.mark.usefixtures('aiida_profile_clean')
def test_evaluate_unwraps_scalar_nodes() -> None:
    """Scalar node operands compute through `.value`, returning plain values."""
    expression, _ = _compile('x + 1', {'x': ('x', LeafShape(types=(Int,)))})
    assert evaluate_expression(expression, {'x': Int(2)}) == 3


def test_index_lists_with_negatives_and_dicts_by_key() -> None:
    """Integer indices read lists (negatives allowed); string keys read dicts."""
    expression, _ = _compile('xs[0] + xs[-1]', {'xs': ('xs', INTS)})
    assert evaluate_expression(expression, {'xs': [1, 2, 3]}) == 4
    keyed, _ = _compile('d["b"]', {'d': ('d', STR_INT_MAP)})
    assert evaluate_expression(keyed, {'d': {'a': 1, 'b': 2}}) == 2
    assert infer_expression_shape(expression, {'xs': INTS}).types == (int,)


def test_index_rejects_bad_position_and_missing_key() -> None:
    """Out-of-range indices, wrong index types, and missing keys fail loudly."""
    expression, _ = _compile('xs[i]', {'xs': ('xs', INTS), 'i': ('i', LeafShape(types=(int,)))})
    with pytest.raises(GraphRuntimeError, match='out of range'):
        evaluate_expression(expression, {'xs': [1], 'i': 5})
    with pytest.raises(GraphRuntimeError, match='`int` index'):
        evaluate_expression(expression, {'xs': [1], 'i': 'a'})
    keyed, _ = _compile('d[k]', {'d': ('d', STR_INT_MAP), 'k': ('k', LeafShape(types=(str,)))})
    with pytest.raises(GraphRuntimeError, match='missing key'):
        evaluate_expression(keyed, {'d': {'a': 1}, 'k': 'b'})


def test_compile_rejects_slices_calls_and_private_names() -> None:
    """Slices, calls, and underscore attributes stay task concerns."""
    mapping = {'xs': ('xs', INTS)}
    with pytest.raises(GraphTypeCheckError, match=r'Slices|slice'):
        _compile('xs[1:2]', mapping)
    with pytest.raises(GraphTypeCheckError, match='calls never run'):
        _compile('f(x)', {'f': ('f', LeafShape(types=(int,))), 'x': ('x', LeafShape(types=(int,)))})
    with pytest.raises(GraphTypeCheckError, match='underscore'):
        _compile('x._hidden', {'x': ('x', LeafShape(types=(int,)))})


def test_attribute_reads_namespace_fields_and_scalar_value() -> None:
    """Dotted reads select declared namespace fields and scalar `.value`."""
    shape = NamespaceShape(fields=(('name', LeafShape(types=(str,))),))
    expression, _ = _compile('bundle.name', {'bundle': ('bundle', shape)})
    assert infer_expression_shape(expression, {'bundle': shape}).types == (str,)
    assert evaluate_expression(expression, {'bundle': {'name': 'ok'}}) == 'ok'
    valued, _ = _compile('x.value', {'x': ('x', LeafShape(types=(Int,)))})
    assert infer_expression_shape(valued, {'x': LeafShape(types=(Int,))}).types == (int,)


def test_listcomp_filters_and_nests() -> None:
    """Filtered and nested comprehensions collect eagerly in one placement."""
    expression, _ = _compile('[y * 2 for y in xs if y > 1]', {'xs': ('xs', INTS)})
    assert evaluate_expression(expression, {'xs': [1, 2, 3]}) == [4, 6]
    assert infer_expression_shape(expression, {'xs': INTS}).element == LeafShape(types=(int,))
    nested, _ = _compile('[a + b for a in xs for b in ys]', {'xs': ('xs', INTS), 'ys': ('ys', INTS)})
    assert evaluate_expression(nested, {'xs': [1, 2], 'ys': [10, 20]}) == [11, 21, 12, 22]


def test_dicts_iterate_keys_and_items_pairs() -> None:
    """Mappings iterate keys; `.items()` with a tuple target iterates pairs."""
    keys, _ = _compile('[k for k in d]', {'d': ('d', STR_INT_MAP)})
    assert evaluate_expression(keys, {'d': {'a': 1, 'b': 2}}) == ['a', 'b']
    pairs, _ = _compile('[v for k, v in d.items() if v > 1]', {'d': ('d', STR_INT_MAP)})
    assert evaluate_expression(pairs, {'d': {'a': 1, 'b': 2}}) == [2]
    built, _ = _compile('{k: v * 2 for k, v in d.items()}', {'d': ('d', STR_INT_MAP)})
    assert evaluate_expression(built, {'d': {'a': 1}}) == {'a': 2}


def test_unknown_element_annotations_reject_clearly() -> None:
    """Collections without a declared element type never guess."""
    bare = LeafShape(types=(list,))
    expression, _ = _compile('xs[0]', {'xs': ('xs', bare)})
    with pytest.raises(GraphTypeCheckError, match='element type'):
        infer_expression_shape(expression, {'xs': bare})


def test_inputs_are_not_mutated() -> None:
    """Comprehensions and literals build new collections, leaving inputs alone."""
    expression, _ = _compile('[y + 1 for y in xs]', {'xs': ('xs', INTS)})
    given: dict[str, object] = {'xs': [1, 2]}
    assert evaluate_expression(expression, given) == [2, 3]
    assert given == {'xs': [1, 2]}


@pytest.mark.usefixtures('aiida_profile_clean')
def test_owned_containers_iterate_members() -> None:
    """`DataList` iterates member nodes; `DataDict` indexes them by key."""
    listed, _ = _compile('[v.value for v in xs]', {'xs': ('xs', LeafShape(types=(DataList,)))})
    assert evaluate_expression(listed, {'xs': DataList([Int(1), Int(2)])}) == [1, 2]
    keyed, _ = _compile('d["a"].value', {'d': ('d', LeafShape(types=(DataDict,)))})
    assert evaluate_expression(keyed, {'d': DataDict({'a': Int(3)})}) == 3


def test_index_unwraps_stored_scalar_nodes() -> None:
    """Stored ``Int``/``Str`` indices read through their values; ``Bool`` never indexes."""
    listed, _ = _compile('xs[i]', {'xs': ('xs', INTS), 'i': ('i', LeafShape(types=(Int,)))})
    assert evaluate_expression(listed, {'xs': [1, 2, 3], 'i': Int(1)}) == 2
    keyed, _ = _compile('d[k]', {'d': ('d', STR_INT_MAP), 'k': ('k', LeafShape(types=(Str,)))})
    assert evaluate_expression(keyed, {'d': {'a': 1, 'b': 2}, 'k': Str('b')}) == 2
    keyed_plain, _ = _compile('d[k]', {'d': ('d', STR_INT_MAP), 'k': ('k', LeafShape(types=(str,)))})
    assert evaluate_expression(keyed_plain, {'d': {'a': 1}, 'k': Str('a')}) == 1
    with pytest.raises(GraphRuntimeError, match='`int` index'):
        evaluate_expression(listed, {'xs': [1], 'i': Bool(True)})
    with pytest.raises(GraphRuntimeError, match='`str` key'):
        evaluate_expression(keyed, {'d': {'a': 1}, 'k': Bool(True)})


def test_malformed_trees_fail_closed() -> None:
    """Unknown tags and missing keys fail instead of miscomputing."""
    with pytest.raises(GraphTypeCheckError, match='unknown tag'):
        infer_expression_shape({'tag': 'frobnicate'}, {})
    with pytest.raises(GraphTypeCheckError, match='malformed'):
        infer_expression_shape({'tag': 'binary', 'op': 'add', 'left': {'tag': 'const', 'value': 1}}, {})
    with pytest.raises(GraphRuntimeError, match=r'unknown tag|malformed'):
        evaluate_expression({'tag': 'frobnicate'}, {})
    with pytest.raises(GraphTypeCheckError, match='unknown input'):
        infer_expression_shape({'tag': 'ref', 'port': 'missing'}, {})


def test_expression_round_trips_through_json() -> None:
    """Compiled trees are plain JSON, so templates can persist them."""
    expression, refs = _compile('{k: v + 1 for k, v in d.items()}', {'d': ('d', STR_INT_MAP)})
    assert json.loads(json.dumps(expression)) == expression
    assert infer_expression_shape(expression, {'d': STR_INT_MAP}).types == (dict,)
    assert evaluate_expression(json.loads(json.dumps(expression)), {'d': {'a': 1}}) == {'a': 2}
    assert refs == {'d': STR_INT_MAP}
    assert infer_expression_shape(expression, {'d': STR_INT_MAP}).element == LeafShape(types=(int,))


def test_infer_rejects_non_boolean_filters() -> None:
    """Comprehension filters must read as booleans."""
    expression, _ = _compile('[y for y in xs if y]', {'xs': ('xs', INTS)})
    with pytest.raises(GraphTypeCheckError, match='true/false'):
        infer_expression_shape(expression, {'xs': INTS})
    assert evaluate_expression(
        _compile('[y for y in xs if flag]', {'xs': ('xs', INTS), 'flag': ('flag', LeafShape(types=(Bool,)))})[0],
        {'xs': [1], 'flag': True},
    ) == [1]
