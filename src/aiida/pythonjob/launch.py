from __future__ import annotations

import inspect
import os
import types
from typing import Any, Callable, Dict, Optional, Tuple, Union

from aiida import orm
from aiida.node_graph.socket_spec import infer_specs_from_callable
from aiida.node_graph.task_spec import BaseHandle

from aiida.pythonjob.data.deserializer import all_deserializers
from aiida.pythonjob.data.serializer import all_serializers

from .utils import build_function_data, get_or_create_code, serialize_ports


def _unwrap_callable(func: Any) -> Callable[..., Any] | None:
    """
    Return a plain Python function from several supported wrappers.
    Returns None if func is None. Raises for unsupported types.
    """
    if func is None:
        return None
    if isinstance(func, BaseHandle) and hasattr(func, "_callable"):
        return func._callable
    if getattr(func, "is_process_function", False):
        # aiida process_function wrapper (e.g., calcfunction/workfunction)
        return func.func
    if inspect.isfunction(func):
        return func
    if isinstance(func, types.BuiltinFunctionType):
        raise NotImplementedError("Built-in functions are not supported yet.")
    raise ValueError(f"Invalid function type: {type(func)!r}")


def _validate_inputs_against_signature(func: Callable[..., Any], inputs: dict) -> None:
    """Raise ValueError if inputs do not bind to func's signature."""
    sig = inspect.signature(func)
    try:
        sig.bind(**inputs)
    except TypeError as e:
        raise ValueError(f"Invalid function inputs: {e}") from e


def _merge_registry(overrides: dict | None, base: dict) -> dict:
    """Shallow-merge (user overrides win)."""
    return {**base, **(overrides or {})}


def _normalize_upload_files(
    upload_files: Dict[str, Union[str, orm.SinglefileData, orm.FolderData]] | None,
) -> Dict[str, Union[orm.SinglefileData, orm.FolderData]]:
    """
    Convert string paths to AiiDA SinglefileData/FolderData and sanitize keys.
    """
    result: Dict[str, Union[orm.SinglefileData, orm.FolderData]] = {}
    if not upload_files:
        return result

    for key, source in upload_files.items():
        # Only alphanumeric + underscore in keys; also make dots explicit
        new_key = key.replace(".", "_dot_")

        if isinstance(source, str):
            if os.path.isfile(source):
                result[new_key] = orm.SinglefileData(file=source)
            elif os.path.isdir(source):
                result[new_key] = orm.FolderData(tree=source)
            else:
                raise ValueError(f"Invalid upload file path: {source!r}")
        elif isinstance(source, (orm.SinglefileData, orm.FolderData)):
            result[new_key] = source
        else:
            raise ValueError(f"Invalid upload file type: {type(source)}, value={source!r}")

    return result


def _maybe_build_function_data(func: Callable[..., Any] | None, *, register_pickle_by_value: bool) -> dict | None:
    """Build function_data if we have a Python function; else return None."""
    if func is None:
        return None
    return build_function_data(func, register_pickle_by_value=register_pickle_by_value)


def _prepare_common(
    *,
    function: Optional[Callable[..., Any]],
    function_data: Optional[dict],
    function_inputs: Optional[Dict[str, Any]],
    inputs_spec: Optional[type],
    outputs_spec: Optional[type],
    serializers: Optional[dict],
    deserializers: Optional[dict],
    register_pickle_by_value: bool,
    validate_signature: bool,
) -> Tuple[dict, dict, dict, dict]:
    """
    Shared logic used by both PyFunction and PythonJob preparations.

    Returns:
        (prepared_inputs, outputs_spec_dict, merged_serializers, merged_deserializers)
        where prepared_inputs = {"function_data": ..., "function_inputs": ..., "metadata": {...}}
    """
    # Unwrap and normalize the function
    fn = _unwrap_callable(function)

    # Guard: either function or function_data must be present, but not both
    if fn is None and function_data is None:
        raise ValueError("Either `function` or `function_data` must be provided.")
    if fn is not None and function_data is not None:
        raise ValueError("Only one of `function` or `function_data` should be provided.")

    # If we have a Python function, build function_data from source/pickle
    if fn is not None:
        function_data = _maybe_build_function_data(fn, register_pickle_by_value=register_pickle_by_value)

    # Infer I/O specs
    in_spec, out_spec = infer_specs_from_callable(fn, inputs=inputs_spec, outputs=outputs_spec)

    # Merge serializer/deserializer registries (user wins)
    merged_serializers = _merge_registry(serializers, all_serializers)
    merged_deserializers = _merge_registry(deserializers, all_deserializers)

    # Serialize inputs according to (possibly nested) input schema
    py_inputs = function_inputs or {}
    serialized_inputs = serialize_ports(
        python_data=py_inputs,
        port_schema=in_spec,
        serializers=merged_serializers,
    )

    # Optional: validate against fn signature (bind) using the PROVIDED keys.
    # Binding cares about names/arity, not the exact serialized types.
    if validate_signature and fn is not None:
        _validate_inputs_against_signature(fn, serialized_inputs)

    metadata = {
        "inputs_spec": in_spec.to_dict(),
        "outputs_spec": out_spec.to_dict(),
        "serializers": merged_serializers,
        "deserializers": merged_deserializers,
    }

    prepared = {
        "function_data": function_data,
        "function_inputs": serialized_inputs,
        "metadata": metadata,
    }
    return prepared, metadata["outputs_spec"], merged_serializers, merged_deserializers


def create_inputs(func: Callable[..., Any], *args: Any, **kwargs: Any) -> dict[str, Any]:
    """
    Create the input dictionary for calling a Python function by name-binding.
    Positional args are mapped to positional parameters; **kwargs are merged on top.
    Variable positional parameters (*args) are not supported.
    """
    inputs = dict(kwargs or {})
    arguments = list(args)
    for name, param in inspect.signature(func).parameters.items():
        if param.kind in (param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD):
            try:
                inputs[name] = arguments.pop(0)
            except IndexError:
                pass
        elif param.kind is param.VAR_POSITIONAL:
            raise NotImplementedError("Variable positional arguments (*args) are not supported.")
    return inputs


def prepare_pythonjob_inputs(
    function: Optional[Callable[..., Any]] = None,
    function_inputs: Optional[Dict[str, Any]] = None,
    inputs_spec: Optional[type] = None,
    outputs_spec: Optional[type] = None,
    code: Optional[orm.AbstractCode] = None,
    command_info: Optional[Dict[str, str]] = None,
    computer: Union[str, orm.Computer] = "localhost",
    metadata: Optional[Dict[str, Any]] = None,
    upload_files: Optional[Dict[str, Union[str, orm.SinglefileData, orm.FolderData]]] = None,
    process_label: Optional[str] = None,
    function_data: dict | None = None,
    deserializers: dict | None = None,
    serializers: dict | None = None,
    register_pickle_by_value: bool = False,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Prepare the inputs for a PythonJob (runner that needs a Code and optional upload_files).
    """
    prepared, _, _, _ = _prepare_common(
        function=function,
        function_data=function_data,
        function_inputs=function_inputs,
        inputs_spec=inputs_spec,
        outputs_spec=outputs_spec,
        serializers=serializers,
        deserializers=deserializers,
        register_pickle_by_value=register_pickle_by_value,
        validate_signature=(function is not None),  # only when we actually got a function
    )

    # Files & Code specifics
    new_upload_files = _normalize_upload_files(upload_files)
    if code is None:
        code = get_or_create_code(computer=computer, **(command_info or {}))

    # Merge external metadata if provided
    md = {**prepared["metadata"], **(metadata or {})}
    prepared["metadata"] = md

    inputs: Dict[str, Any] = {
        **prepared,
        "code": code,
        "upload_files": new_upload_files,
        **kwargs,
    }
    if process_label:
        inputs["process_label"] = process_label
    return inputs


def prepare_pyfunction_inputs(
    function: Optional[Callable[..., Any]] = None,
    function_inputs: Optional[Dict[str, Any]] = None,
    inputs_spec: Optional[type] = None,
    outputs_spec: Optional[type] = None,
    metadata: Optional[Dict[str, Any]] = None,
    process_label: Optional[str] = None,
    function_data: dict | None = None,
    deserializers: dict | None = None,
    serializers: dict | None = None,
    register_pickle_by_value: bool = False,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Prepare the inputs for a local PyFunction (no Code/upload_files).
    """
    prepared, _, _, _ = _prepare_common(
        function=function,
        function_data=function_data,
        function_inputs=function_inputs,
        inputs_spec=inputs_spec,
        outputs_spec=outputs_spec,
        serializers=serializers,
        deserializers=deserializers,
        register_pickle_by_value=register_pickle_by_value,
        validate_signature=False,  # leave binding checks to the engine if desired
    )

    # Merge external metadata if provided
    md = {**prepared["metadata"], **(metadata or {})}
    prepared["metadata"] = md

    inputs: Dict[str, Any] = {
        **prepared,
        **kwargs,
    }
    if process_label:
        inputs["process_label"] = process_label
    return inputs


def prepare_monitor_function_inputs(
    function: Optional[Callable[..., Any]] = None,
    function_inputs: Optional[Dict[str, Any]] = None,
    inputs_spec: Optional[type] = None,
    outputs_spec: Optional[type] = None,
    metadata: Optional[Dict[str, Any]] = None,
    process_label: Optional[str] = None,
    function_data: dict | None = None,
    deserializers: dict | None = None,
    serializers: dict | None = None,
    register_pickle_by_value: bool = False,
    interval: Optional[Union[int, float, orm.Float, orm.Int]] = None,
    timeout: Optional[Union[int, float, orm.Float, orm.Int]] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Prepare the inputs for a monitor function (no Code/upload_files).
    """
    inputs = prepare_pyfunction_inputs(
        function=function,
        function_inputs=function_inputs,
        inputs_spec=inputs_spec,
        outputs_spec=outputs_spec,
        metadata=metadata,
        process_label=process_label,
        function_data=function_data,
        deserializers=deserializers,
        serializers=serializers,
        register_pickle_by_value=register_pickle_by_value,
        **kwargs,
    )
    inputs["interval"] = orm.Float(interval) if interval is not None else orm.Float(10.0)
    inputs["timeout"] = orm.Float(timeout) if timeout is not None else orm.Float(3600.0)
    return inputs
