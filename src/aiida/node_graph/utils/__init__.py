from __future__ import annotations
from typing import Dict, Any, Union, List


def gaph_to_short_json(
    ngdata: Dict[str, Union[str, List, Dict]]
) -> Dict[str, Union[str, Dict]]:
    """Export a nodegaph to a rete js editor data."""
    ngdata_short = {
        "name": ngdata["name"],
        "uuid": ngdata["uuid"],
        "state": ngdata["state"],
        "tasks": {},
        "links": ngdata["links"],
    }
    #
    for name, task in ngdata["tasks"].items():
        # Add required inputs to tasks
        inputs = []
        for input in task["input_sockets"]["sockets"].values():
            metadata = input.get("metadata", {}) or {}
            if metadata.get("required", False):
                inputs.append(
                    {"name": input["name"], "identifier": input["identifier"]}
                )

        ngdata_short["tasks"][name] = {
            "label": task["name"],
            "node_type": task["spec"]["task_type"].upper(),
            "inputs": inputs,
            "properties": {},
            "outputs": [],
            "position": task["position"],
            "children": task.get("children", []),
        }

    # Add links to tasks
    for link in ngdata_short["links"]:
        ngdata_short["tasks"][link["to_task"]]["inputs"].append(
            {
                "name": link["to_socket"],
            }
        )
        ngdata_short["tasks"][link["from_task"]]["outputs"].append(
            {
                "name": link["from_socket"],
            }
        )
    # remove the inputs socket of "graph_inputs"
    if "graph_inputs" in ngdata_short["tasks"]:
        ngdata_short["tasks"]["graph_inputs"]["inputs"] = []
    # remove the empty graph-level tasks
    for name in ["graph_inputs", "graph_outputs", "graph_ctx"]:
        if name in ngdata_short["tasks"]:
            task = ngdata_short["tasks"][name]
            if len(task["inputs"]) == 0 and len(task["outputs"]) == 0:
                del ngdata_short["tasks"][name]

    return ngdata_short


def yaml_to_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert yaml data into dict."""
    ntdata = data
    tasks = ntdata.pop("tasks")
    ntdata["tasks"] = {}
    for task in tasks:
        task.setdefault("metadata", {})
        task["metadata"]["identifier"] = task.pop("identifier", None)
        task["properties"] = task.get("properties", {})
        task["inputs"] = task.get("inputs", {})
        task["outputs"] = task.get("outputs", {})
        ntdata["tasks"][task["name"]] = task
    return ntdata


def deep_copy_only_dicts(
    original: Union[Dict[str, Any], Any]
) -> Union[Dict[str, Any], Any]:
    """Copy all nested dictionaries in a structure but keep
    the immutable values (such as integers, strings, or tuples)
    shared between the original and the copy"""
    from aiida.node_graph.socket import TaggedValue

    # TaggedValue should not be unpacked
    if isinstance(original, dict) and not isinstance(original, TaggedValue):
        return {k: deep_copy_only_dicts(v) for k, v in original.items()}
    else:
        # Return the original value if it's not a dictionary
        return original


def resolve_tagged_values(inputs: Any) -> Any:
    """Recursively resolve TaggedValue instances in nested dictionaries."""
    from aiida.node_graph.socket import TaggedValue

    if isinstance(inputs, TaggedValue):
        return inputs.__wrapped__
    if isinstance(inputs, dict):
        for key, value in inputs.items():
            if isinstance(value, TaggedValue):
                inputs[key] = value.__wrapped__
            else:
                resolve_tagged_values(value)
    return inputs


def get_arg_type(name: str, args_data: dict, arg_type: str = "kwargs") -> None:
    """Get the argument type from the input data."""
    if arg_type.upper() == "ARGS":
        args_data["args"].append(name)
    elif arg_type.upper() == "KWARGS":
        args_data["kwargs"].append(name)
    elif arg_type.upper() == "VAR_ARGS":
        if args_data["var_args"] is not None:
            raise ValueError("Only one VAR_ARGS is allowed")
        args_data["var_args"] = name
    elif arg_type.upper() == "VAR_KWARGS":
        if args_data["var_kwargs"] is not None:
            raise ValueError("Only one VAR_KWARGS is allowed")
        args_data["var_kwargs"] = name


def valid_name_string(s: str) -> bool:
    """
    Check whether the input string s contains only alphanumeric characters and underscores.
    If not, raise a ValueError with a clean message.

    Args:
        s: The string to validate.

    Returns:
        True if s is valid.

    Raises:
        ValueError: if s contains any character other than A-Z, a-z, 0-9 or underscore.
    """
    import re

    if not isinstance(s, str):
        raise ValueError(f"Invalid name: {s!r}: must be a string")

    if " " in s:
        raise ValueError(f"Invalid name: {s!r}: spaces are not allowed")

    if not re.fullmatch(r"[A-Za-z0-9_]+", s):
        raise ValueError(
            f"Invalid name: {s!r}. Only letters, digits and underscores are allowed"
        )


def tag_socket_value(socket: "TaskSocket", only_uuid: bool = False) -> "TaskSocket":
    """Use a tagged object for the socket's property value."""
    from aiida.node_graph.socket import TaskSocketNamespace, TaggedValue

    if isinstance(socket, TaskSocketNamespace):
        for sub_socket in socket._sockets.values():
            tag_socket_value(sub_socket, only_uuid=only_uuid)
    else:
        # replace the socket's property value directly with a TaggedValue
        # this avoids triggering the value setter
        if socket.property:
            if socket.property.value is not None:
                if not isinstance(socket.property.value, TaggedValue):
                    socket.property.value = TaggedValue(
                        socket.property.value, socket=socket
                    )
                if only_uuid:
                    # only keep the uuid reference, clear the socket reference.
                    # the uuid is kept for provenance tracking
                    socket.property.value._socket = None
                else:
                    socket.property.value._socket = socket


def clean_socket_reference(data: Any) -> Any:
    """Recursively clear the socket reference in TaggedValue objects."""
    from aiida.node_graph.socket import TaggedValue

    if isinstance(data, TaggedValue):
        data._socket = None
        return data
    elif isinstance(data, dict):
        return {k: clean_socket_reference(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_socket_reference(v) for v in data]
    elif isinstance(data, tuple):
        return tuple(clean_socket_reference(v) for v in data)
    else:
        return data
