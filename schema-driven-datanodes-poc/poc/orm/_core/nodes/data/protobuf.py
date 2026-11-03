###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Protobuf encoding and decoding for data-node schema declarations and values."""

from __future__ import annotations

import typing as t

from google.protobuf import descriptor_pb2, descriptor_pool, message_factory

from poc.orm._core.nodes.data.schema import FieldSpec, SchemaSpec

TYPE_NAMES: dict[int, str] = {
    0: 'string',
    1: 'int',
    2: 'float',
    3: 'bool',
    4: 'list[string]',
}


def build_protobuf_classes() -> tuple[type[t.Any], type[t.Any], type[t.Any], type[t.Any], type[t.Any]]:
    """Define protobuf messages programmatically so the PoC stays self-contained."""
    file_proto = descriptor_pb2.FileDescriptorProto()
    file_proto.name = 'schema_spec.proto'
    file_proto.package = 'schema'
    file_proto.syntax = 'proto3'

    enum = file_proto.enum_type.add()
    enum.name = 'ScalarType'
    for number, name in (
        (0, 'SCALAR_TYPE_STRING'),
        (1, 'SCALAR_TYPE_INT'),
        (2, 'SCALAR_TYPE_FLOAT'),
        (3, 'SCALAR_TYPE_BOOL'),
        (4, 'SCALAR_TYPE_LIST_STRING'),
    ):
        value = enum.value.add()
        value.name = name
        value.number = number

    field_spec = file_proto.message_type.add()
    field_spec.name = 'FieldSpec'
    for number, name, field_type, type_name in (
        (1, 'name', descriptor_pb2.FieldDescriptorProto.TYPE_STRING, ''),
        (2, 'scalar_type', descriptor_pb2.FieldDescriptorProto.TYPE_ENUM, '.schema.ScalarType'),
        (3, 'required', descriptor_pb2.FieldDescriptorProto.TYPE_BOOL, ''),
        (4, 'default_str', descriptor_pb2.FieldDescriptorProto.TYPE_STRING, ''),
        (5, 'has_default_str', descriptor_pb2.FieldDescriptorProto.TYPE_BOOL, ''),
        (6, 'default_int', descriptor_pb2.FieldDescriptorProto.TYPE_INT64, ''),
        (7, 'has_default_int', descriptor_pb2.FieldDescriptorProto.TYPE_BOOL, ''),
        (8, 'validator_name', descriptor_pb2.FieldDescriptorProto.TYPE_STRING, ''),
        (9, 'description', descriptor_pb2.FieldDescriptorProto.TYPE_STRING, ''),
    ):
        field = field_spec.field.add()
        field.name = name
        field.number = number
        field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
        field.type = field_type
        if type_name:
            field.type_name = type_name

    schema_spec = file_proto.message_type.add()
    schema_spec.name = 'SchemaSpec'
    field = schema_spec.field.add()
    field.name = 'name'
    field.number = 1
    field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING
    field = schema_spec.field.add()
    field.name = 'fields'
    field.number = 2
    field.label = descriptor_pb2.FieldDescriptorProto.LABEL_REPEATED
    field.type = descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE
    field.type_name = '.schema.FieldSpec'

    envelope = file_proto.message_type.add()
    envelope.name = 'SchemaEnvelope'
    for number, name, field_type, type_name in (
        (1, 'format_version', descriptor_pb2.FieldDescriptorProto.TYPE_UINT32, ''),
        (2, 'schema', descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE, '.schema.SchemaSpec'),
    ):
        field = envelope.field.add()
        field.name = name
        field.number = number
        field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
        field.type = field_type
        if type_name:
            field.type_name = type_name

    value_field = file_proto.message_type.add()
    value_field.name = 'ValueField'
    field = value_field.field.add()
    field.name = 'name'
    field.number = 1
    field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING
    oneof = value_field.oneof_decl.add()
    oneof.name = 'value'
    for number, name, field_type in (
        (2, 'string_value', descriptor_pb2.FieldDescriptorProto.TYPE_STRING),
        (3, 'int_value', descriptor_pb2.FieldDescriptorProto.TYPE_INT64),
        (4, 'float_value', descriptor_pb2.FieldDescriptorProto.TYPE_DOUBLE),
        (5, 'bool_value', descriptor_pb2.FieldDescriptorProto.TYPE_BOOL),
    ):
        field = value_field.field.add()
        field.name = name
        field.number = number
        field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
        field.type = field_type
        field.oneof_index = 0
    field = value_field.field.add()
    field.name = 'list_string_value'
    field.number = 6
    field.label = descriptor_pb2.FieldDescriptorProto.LABEL_REPEATED
    field.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING

    payload = file_proto.message_type.add()
    payload.name = 'NodePayload'
    field = payload.field.add()
    field.name = 'fields'
    field.number = 1
    field.label = descriptor_pb2.FieldDescriptorProto.LABEL_REPEATED
    field.type = descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE
    field.type_name = '.schema.ValueField'

    pool = descriptor_pool.DescriptorPool()
    pool.Add(file_proto)
    return (
        message_factory.GetMessageClass(pool.FindMessageTypeByName('schema.FieldSpec')),
        message_factory.GetMessageClass(pool.FindMessageTypeByName('schema.SchemaSpec')),
        message_factory.GetMessageClass(pool.FindMessageTypeByName('schema.SchemaEnvelope')),
        message_factory.GetMessageClass(pool.FindMessageTypeByName('schema.ValueField')),
        message_factory.GetMessageClass(pool.FindMessageTypeByName('schema.NodePayload')),
    )


FieldSpecMessage, SchemaSpecMessage, SchemaEnvelopeMessage, ValueFieldMessage, NodePayloadMessage = build_protobuf_classes()


def encode_schema(schema: SchemaSpec, *, format_version: int = 1) -> bytes:
    """Encode a data-node schema object to a versioned protobuf blob."""
    envelope = SchemaEnvelopeMessage()
    envelope.format_version = format_version
    envelope.schema.name = schema.name
    for field in schema.fields:
        item = envelope.schema.fields.add()
        item.name = field.name
        item.scalar_type = field.scalar_type
        item.required = field.required
        if field.default_str is not None:
            item.default_str = field.default_str
            item.has_default_str = True
        if field.default_int is not None:
            item.default_int = field.default_int
            item.has_default_int = True
        if field.validator_name is not None:
            item.validator_name = field.validator_name
        item.description = field.description
    return envelope.SerializeToString()


def decode_schema(blob: bytes) -> tuple[int, SchemaSpec]:
    """Decode a protobuf blob from the database into Python schema objects."""
    envelope = SchemaEnvelopeMessage()
    envelope.ParseFromString(blob)
    schema = SchemaSpec(
        name=envelope.schema.name,
        fields=tuple(
            FieldSpec(
                name=field.name,
                scalar_type=field.scalar_type,
                required=field.required,
                default_str=field.default_str if field.has_default_str else None,
                default_int=field.default_int if field.has_default_int else None,
                validator_name=field.validator_name or None,
                description=field.description,
            )
            for field in envelope.schema.fields
        ),
    )
    return envelope.format_version, schema


def encode_values(schema: SchemaSpec, values: dict[str, t.Any]) -> bytes:
    """Encode validated data-node values to a protobuf blob."""
    payload = NodePayloadMessage()
    by_name = {field.name: field for field in schema.fields}

    for name, value in values.items():
        if value is None:
            continue
        declaration = by_name.get(name)
        if declaration is None:
            continue
        item = payload.fields.add()
        item.name = name
        if declaration.scalar_type == 0:
            item.string_value = value
        elif declaration.scalar_type == 1:
            item.int_value = value
        elif declaration.scalar_type == 2:
            item.float_value = value
        elif declaration.scalar_type == 3:
            item.bool_value = value
        elif declaration.scalar_type == 4:
            item.list_string_value.extend(value)

    return payload.SerializeToString()


def decode_values(schema: SchemaSpec, blob: bytes) -> dict[str, t.Any]:
    """Decode a protobuf value blob to plain Python values."""
    payload = NodePayloadMessage()
    payload.ParseFromString(blob)
    by_name = {field.name: field for field in schema.fields}
    values: dict[str, t.Any] = {}

    for item in payload.fields:
        declaration = by_name[item.name]
        if declaration.scalar_type == 0:
            values[item.name] = item.string_value
        elif declaration.scalar_type == 1:
            values[item.name] = item.int_value
        elif declaration.scalar_type == 2:
            values[item.name] = item.float_value
        elif declaration.scalar_type == 3:
            values[item.name] = item.bool_value
        elif declaration.scalar_type == 4:
            values[item.name] = list(item.list_string_value)

    return values
