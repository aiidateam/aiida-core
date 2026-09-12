from __future__ import annotations

import sys
import traceback
from importlib.metadata import entry_points
from typing import Any

from aiida import common, orm

from aiida.pythonjob.data.jsonable_data import JsonableData

from .utils import import_from_path

builtin_serializers = {
    "builtins.int": "aiida.orm.nodes.data.int.Int",
    "builtins.float": "aiida.orm.nodes.data.float.Float",
    "builtins.str": "aiida.orm.nodes.data.str.Str",
    "builtins.bool": "aiida.orm.nodes.data.bool.Bool",
    "builtins.list": "aiida.orm.nodes.data.list.List",
    "builtins.dict": "aiida.orm.nodes.data.dict.Dict",
    "numpy.float32": "aiida.orm.nodes.data.float.Float",
    "numpy.float64": "aiida.orm.nodes.data.float.Float",
    "numpy.int64": "aiida.orm.nodes.data.int.Int",
    "numpy.bool_": "aiida.orm.nodes.data.bool.Bool",  # numpy<2.0
    "numpy.bool": "aiida.orm.nodes.data.bool.Bool",  # numpy>=2.0
    "numpy.ndarray": "aiida.orm.nodes.data.array.array.ArrayData",
}


def atoms_to_structure_data(structure):
    return orm.StructureData(ase=structure)


def get_serializers_from_entry_points() -> dict:
    """Retrieve the entry points for 'aiida.data' and store them in a dictionary."""
    eps_all = entry_points()
    if sys.version_info >= (3, 10):
        group = eps_all.select(group="aiida.data")
    else:
        group = eps_all.get("aiida.data", [])

    # By converting the group to a set, we remove accidental duplicates
    # where the same EntryPoint object is discovered twice. Legitimate
    # competing entry points from different packages will remain.
    unique_group = set(group)

    serializers = {}
    for ep in unique_group:
        # split the entry point name by first ".", and check the last part
        key = ep.name.split(".", 1)[-1]

        # skip key without "." because it is not a module name for a data type
        if "." not in key:
            continue

        serializers.setdefault(key, [])
        # get the path of the entry point value and replace ":" with "."
        serializers[key].append(ep.value.replace(":", "."))

    return serializers


def get_serializers() -> dict:
    """Retrieve the serializer from the entry points."""
    from aiida.pythonjob.config import config
    # import time

    # ts = time.time()
    all_serializers = builtin_serializers.copy()
    custom_serializers = config.get("serializers", {})
    eps = get_serializers_from_entry_points()
    # check if there are duplicates
    for key, value in eps.items():
        if len(value) > 1:
            if key not in custom_serializers:
                msg = f"Duplicate entry points for {key}: {value}. You can specify the one to use in the configuration file."  # noqa
                raise ValueError(msg)
        all_serializers[key] = value[0]
    all_serializers.update(custom_serializers)
    # print("Time to get serializer", time.time() - ts)
    return all_serializers


all_serializers = get_serializers()


def serialize_to_aiida_nodes(inputs: dict, serializers: dict | None = None) -> dict:
    """Serialize the inputs to a dictionary of AiiDA data nodes.

    Args:
        inputs (dict): The inputs to be serialized.

    Returns:
        dict: The serialized inputs.
    """
    new_inputs = {}
    # save all kwargs to inputs port
    for key, data in inputs.items():
        new_inputs[key] = general_serializer(data, serializers=serializers)
    return new_inputs


def general_serializer(
    data: Any,
    serializers: dict | None = None,
    store: bool = True,
    user: orm.User | None = None,
) -> orm.Node:
    """
    Attempt to serialize the data to an AiiDA data node based on the preference from `config`:
      1) AiiDA data only, 2) JSON-serializable, 3) fallback to PickledData (if allowed).
    """
    serializers = serializers or all_serializers

    # 1) If it is already an AiiDA node, just return it
    if isinstance(data, orm.Node):
        return data
    elif isinstance(data, common.extendeddicts.AttributeDict):
        # if the data is an AttributeDict, use it directly
        return data

    # 3) check entry point
    data_type = type(data)
    ep_key = f"{data_type.__module__}.{data_type.__name__}"
    if ep_key in serializers:
        try:
            serializer = import_from_path(serializers[ep_key])
            new_node = serializer(data, user=user)
            if store:
                new_node.store()
            return new_node
        except Exception:
            error_traceback = traceback.format_exc()
            raise ValueError(f"Error in serializing {ep_key}: {error_traceback}")

    try:
        node = JsonableData(data, user=user)
        if store:
            node.store()
        return node
    except (TypeError, ValueError):
        suggestions = [
            "How to fix:",
            "1) Register a type-specific AiiDA Data class as an `aiida.data` entry point "
            "(recommended for domain objects).",
            "   Example in `pyproject.toml`:",
            '   [project.entry-points."aiida.data"]',
            f'   myplugin.{ep_key} = "myplugin.data.mytype:MyTypeData"',
            "   where `MyTypeData` is a subclass of `aiida.orm.Data` that knows how to store your object.",
            "",
            "2) Or make the class JSON-serializable so `JsonableData` can handle it by implementing:",
            "   - `to_dict()` / `as_dict()` (any one) returning only JSON-friendly structures, and",
            "   - `from_dict(cls, dct)` / `fromdict(cls, dct)` to rebuild the object later.",
            "",
            "3) Or pass an ad-hoc serializer function via the `serializers` argument:",
            f"   general_serializer(obj, serializers={{'{ep_key}': 'my_pkg.mod:to_aiida_node'}})",
            "   where `to_aiida_node(obj)` returns an `aiida.orm.Data` instance.",
        ]
        raise ValueError(
            (
                "Cannot serialize the provided object.\n\n"
                f"Type: {ep_key}\n"
                f"Tried entry-point key: '{ep_key}' — not found in provided serializers.\n" + "\n".join(suggestions)
            )
        )
