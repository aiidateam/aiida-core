###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Graph declarations use native value shapes; executor ports are adapted at the boundary."""

import inspect
import json
import typing as t

import pytest

from aiida import orm
from aiida.engine import Many, PortField, PortModel
from aiida.engine.processes.graphs import build_source
from aiida.engine.processes.graphs.inputs import port_for_shape, shape_from_port
from aiida.engine.processes.graphs.shapes import (
    LeafShape,
    ManyShape,
    NamespaceShape,
    dump_shape,
    load_shape,
    shape_for_annotation,
)

pytestmark = pytest.mark.presto


class Block(PortModel):
    parameters: t.Annotated[orm.Dict, PortField(help='Block parameters.')]
    file: orm.SinglefileData | None = None


class Collection(PortModel):
    blocks: Many[Block]


def test_native_contract_roundtrip():
    shape = shape_for_annotation(Collection)
    assert isinstance(shape, NamespaceShape)
    blocks = shape.select('blocks')
    assert isinstance(blocks, ManyShape)
    assert isinstance(blocks.entry, NamespaceShape)
    assert blocks.entry.select('parameters') == LeafShape(types=(orm.Dict,), help='Block parameters.')
    assert not blocks.entry.select('file').required
    assert blocks.entry.select('file').default is None
    payload = dump_shape(shape)
    assert payload['fields']['blocks']['kind'] == 'many'
    assert payload['fields']['blocks']['entry']['kind'] == 'namespace'
    assert load_shape(json.loads(json.dumps(payload))) == shape
    assert 'entry_port' not in json.dumps(payload)
    assert 'valid_type' not in json.dumps(payload)


@pytest.mark.parametrize('output', [False, True])
def test_executor_adapter(output):
    shape = shape_for_annotation(Collection)
    port = port_for_shape('boundary', shape, output=output)
    entry = port['blocks'].entry_port
    assert entry['parameters'].valid_type == (orm.Dict,)
    assert entry['parameters'].help == 'Block parameters.'
    assert not entry['file'].required
    assert shape_from_port(port, defaults=False) == load_shape(dump_shape(shape, defaults=False))


def test_python_leaves_are_translated_only_by_output_adapter():
    shape = shape_for_annotation(int)
    assert shape == LeafShape(types=(int,))
    assert port_for_shape('result', shape).valid_type == (int,)
    assert port_for_shape('result', shape, output=True).valid_type == (orm.Int,)


def test_source_lowering_has_no_engine_port_types():
    source = inspect.getsource(build_source)
    assert 'PortNamespace' not in source
    assert 'InputPort' not in source
    assert 'OutputPort' not in source
    assert t.get_type_hints(build_source._Reference)['shape'] == LeafShape | NamespaceShape | ManyShape


def test_default_snapshot_is_independent():
    default = {'values': [1]}
    shape = LeafShape(types=(dict,), required=False, default=default)
    payload = dump_shape(shape)
    payload['default']['values'].append(2)
    assert default == {'values': [1]}
    restored = load_shape(dump_shape(shape))
    assert restored == shape


@pytest.mark.parametrize('default', [object(), lambda: 5, float('nan')])
def test_non_json_defaults_are_rejected(default):
    with pytest.raises(TypeError, match='not a finite JSON value'):
        dump_shape(LeafShape(default=default))
