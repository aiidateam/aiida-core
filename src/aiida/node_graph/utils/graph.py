from ..graph import Graph
from typing import Any, Optional, Callable
from aiida.node_graph.socket_spec import SocketSpec
from aiida.node_graph.socket import (
    BaseSocket,
    TaskSocket,
    TaskSocketNamespace,
    TaggedValue,
)


def format_invalid_graph_payload_error(subpath: str, vtype: str) -> str:
    """
    Formats the 'Invalid graph return payload' error message with specific
    subpath and vtype values.
    """
    error_message = (
        "Invalid graph return payload.\n"
        f"- Location: {subpath}\n"
        f"- Got: {vtype}\n"
        "- Expected: BaseSocket (a task's socket) or TaggedValue\n\n"
        "Why this fails:\n"
        "You're returning a raw Python value computed inside the graph task. "
        "This bypasses Graph's provenance tracking and breaks data lineage.\n\n"
        "How to fix:\n"
        "1) Wrap the computation in a task and return its OUTPUT SOCKET:\n"
        "   @task()\n"
        "   def compute(x, y):\n"
        "       return x + y\n"
        "\n"
        "   # inside your graph\n"
        "   s = compute(x, y)\n"
        "   return {\n"
        "       'sum': s.outputs.result  # <-- BaseSocket, not a raw value\n"
        "   }\n\n"
    )
    return error_message


def _ensure_all_sockets_in_dict(d: dict, path: str = "outputs") -> None:
    for k, v in d.items():
        subpath = f"{path}.{k}"
        if isinstance(v, dict):
            _ensure_all_sockets_in_dict(v, path=subpath)
        elif not isinstance(v, (BaseSocket, TaggedValue)):
            vtype = type(v).__name__
            raise TypeError(format_invalid_graph_payload_error(subpath, vtype))


def _assign_graph_outputs(outputs: Any, graph: Graph) -> None:
    """
    Inspect the raw outputs from the function and attach them to the Graph.

    Rules:
      - None        -> no outputs
      - TaskSocket  -> map to first declared output
      - Namespace   -> iterate sockets; assign by name (respect non-dynamic outputs)
      - dict        -> every leaf value (including nested dicts) must be BaseSocket
      - tuple       -> every item must be BaseSocket; length must match declared outputs
    """

    if outputs is None:
        if len(graph.outputs) != 0:
            raise ValueError(
                "The function returned None, but the Graph task declares outputs. "
                "Either remove the declared outputs or ensure the function returns them."
            )
        return

    elif isinstance(outputs, (TaskSocket, TaggedValue)):
        # Single socket -> assign to first declared output slot
        graph.outputs[0] = outputs

    elif isinstance(outputs, TaskSocketNamespace):
        # if this is a dynamic namespace, we should link the top-level outputs
        if outputs._metadata.dynamic:
            graph.outputs = outputs

        for socket in outputs:
            if (
                socket._name not in graph.outputs
                and not graph.outputs._metadata.dynamic
            ):
                if socket._name.startswith("_"):
                    # Allow internal names to pass through even if not declared.
                    # This is useful for internal sockets that don't need
                    # to be exposed as a Graph output.
                    continue
                raise ValueError(
                    "Output socket name "
                    f"'{socket._name}' not declared in Graph task outputs.Available outputs: "
                    f"{list(graph.outputs._get_keys())}\n\n"
                    "How to fix:\n"
                    "1) Make graph outputs dynamic if you want to return arbitrary names:\n"
                    "   • `outputs = dynamic(Any)`\n"
                    "     (then returning arbitrary sockets is allowed)\n"
                    "2) Declare this output explicitly on the Graph:\n"
                    f"   • e.g. `outputs = namespace({socket._name}=Any, <some_other_name>=Any)`\n"
                    "3) Expose task outputs instead of inventing new names:\n"
                    f"   • e.g. `outputs = namespace({socket._name}=some_task.outputs, <some_other_name>=some_task.outputs)`\n"
                )
            graph.outputs[socket._name] = socket

    elif isinstance(outputs, dict):
        _ensure_all_sockets_in_dict(outputs)
        # If you also want to enforce declared names when not dynamic, do it here (optional).
        graph.outputs = outputs

    elif isinstance(outputs, tuple):
        if len(outputs) != len(graph.outputs):
            raise ValueError(
                f"The length of the outputs {len(outputs)} does not match the length of the "
                f"Graph task outputs {len(graph.outputs)}."
            )
        for i, output in enumerate(outputs):
            if not isinstance(output, (BaseSocket, TaggedValue)):
                raise TypeError(
                    format_invalid_graph_payload_error(
                        subpath=f"outputs[{i}]",
                        vtype=type(output).__name__,
                    )
                )
        outputs_dict = {
            graph.outputs[i]._name: output for i, output in enumerate(outputs)
        }
        graph.outputs = outputs_dict

    else:
        raise TypeError(
            format_invalid_graph_payload_error(
                subpath="outputs",
                vtype=type(outputs).__name__,
            )
        )


def materialize_graph(
    func: Callable,
    in_spec: SocketSpec,
    out_spec: SocketSpec,
    identifier: str = None,
    graph_class: type = None,
    *,
    args: tuple,
    kwargs: dict,
    var_kwargs: Optional[dict] = None,
) -> Graph:
    """
    Run func(*args, **kwargs, **(var_kwargs or {})) inside a Graph,
    assign its outputs and return the Graph.
    """
    from aiida.node_graph.utils import tag_socket_value, clean_socket_reference
    from aiida.node_graph.utils.struct_utils import coerce_inputs_from_spec
    from aiida.node_graph.utils.function import (
        prepare_function_inputs,
        inspect_callable_metadata,
    )

    if graph_class is None:
        from aiida.node_graph import Graph

        graph_class = Graph

    merged = {**kwargs, **(var_kwargs or {})}
    name = identifier.split(".")[-1] or func.__name__
    with graph_class(name=name, inputs=in_spec, outputs=out_spec) as graph:
        definition_meta = inspect_callable_metadata(func)
        definition_meta["task_identifier"] = identifier
        graph._metadata.setdefault("definition", definition_meta)
        inputs = prepare_function_inputs(func, *args, **merged)
        inputs = clean_socket_reference(inputs)
        graph.graph_inputs.set_inputs(inputs)
        tag_socket_value(graph.inputs)
        inputs = graph.inputs._collect_values(unwrap=False)
        inputs = coerce_inputs_from_spec(inputs, in_spec)
        raw = func(**inputs)
        _assign_graph_outputs(raw, graph)
        tag_socket_value(graph.inputs, only_uuid=True)
        return graph
