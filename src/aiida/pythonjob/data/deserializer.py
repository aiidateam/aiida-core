from __future__ import annotations

from typing import Any

from aiida import common, orm
from aiida.common.extendeddicts import AttributesFrozendict

from .utils import import_from_path

builtin_deserializers = {
    "aiida.orm.nodes.data.list.List": "aiida.pythonjob.data.deserializer.list_data_to_list",
    "aiida.orm.nodes.data.dict.Dict": "aiida.pythonjob.data.deserializer.dict_data_to_dict",
    "aiida.orm.nodes.data.array.array.ArrayData": "aiida.pythonjob.data.deserializer.array_data_to_array",
    "aiida.orm.nodes.data.structure.StructureData": "aiida.pythonjob.data.deserializer.structure_data_to_atoms",
}


def generate_aiida_node_deserializer(data: orm.Node) -> dict:
    if isinstance(data, orm.Data):
        return data.backend_entity.attributes
    elif isinstance(data, (common.extendeddicts.AttributeDict, dict)):
        # if the data is an AttributeDict, use it directly
        return {k: generate_aiida_node_deserializer(v) for k, v in data.items()}


def list_data_to_list(data):
    return data.get_list()


def dict_data_to_dict(data):
    return data.get_dict()


def array_data_to_array(data):
    return data.get_array()


def structure_data_to_atoms(structure):
    return structure.get_ase()


def structure_data_to_pymatgen(structure):
    return structure.get_pymatgen()


def get_deserializer() -> dict:
    """Retrieve the serializer from the entry points."""
    from aiida.pythonjob.config import config

    custom_deserializers = config.get("deserializers", {})
    deserializers = builtin_deserializers.copy()
    deserializers.update(custom_deserializers)
    return deserializers


all_deserializers = get_deserializer()


def deserialize_to_raw_python_data(
    data: orm.Node | dict, deserializers: dict | None = None, dry_run: bool = False
) -> Any:
    """Deserialize the AiiDA data node to an raw Python data."""

    deserializers = deserializers or all_deserializers

    if isinstance(data, orm.Data):
        if hasattr(data, "value"):
            return None if dry_run else getattr(data, "value")
        data_type = type(data)
        ep_key = f"{data_type.__module__}.{data_type.__name__}"
        if ep_key in deserializers:
            deserializer = import_from_path(deserializers[ep_key])
            return deserializer(data)
        else:
            raise ValueError(
                f"Cannot deserialize AiiDA data of type `{ep_key}`. "
                "This type does not define a `.value` attribute, and no matching "
                f"deserializer was provided in `deserializers` for key `{ep_key}`. "
                "To fix this, either:\n"
                "  1. Use a Data type with a `.value` property, or\n"
                "  2. Provide a custom deserializer in `deserializers`, e.g.:\n"
                "       deserializers = {\n"
                f"           '{ep_key}': 'my_package.my_module.my_deserializer'\n"
                "       }"
            )
    elif isinstance(data, (common.extendeddicts.AttributeDict, AttributesFrozendict, dict)):
        # if the data is an AttributeDict, use it directly
        return {k: deserialize_to_raw_python_data(v, deserializers=deserializers) for k, v in data.items()}
