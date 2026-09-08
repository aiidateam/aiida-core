from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from aiida import orm
from aiida.engine import ExitCode
from aiida.node_graph.socket_spec import SocketSpec
from aiida.node_graph.utils.struct_utils import is_structured_instance, structured_to_dict

from ..utils import _ensure_spec, serialize_ports


def _ordered_field_names(spec: SocketSpec) -> list[str]:
    return list(spec.fields.keys())


def already_serialized(results: Any) -> bool:
    """Check if *results* (possibly nested mapping) are already AiiDA Data.
    #TODO we should only support that all results are AiiDA Data
    """
    import collections

    if isinstance(results, orm.Data):
        return True
    if isinstance(results, collections.abc.Mapping):
        for value in results.values():
            if not already_serialized(value):
                return False
        return True
    return False


def parse_outputs(
    results: Any,
    output_spec: SocketSpec | Dict[str, Any],
    exit_codes,
    logger,
    serializers: Optional[Dict[str, str]] = None,
    user: Optional[orm.User] = None,
) -> Tuple[Optional[Dict[str, Any]], Optional[ExitCode]]:
    """Validate & convert *results* according to *output_spec*.

    Returns (outputs_dict, exit_code). If *exit_code* is not None, the caller should
    return it and ignore *outputs_dict*.
    """
    spec = _ensure_spec(output_spec)

    fields = spec.fields or {}
    is_dyn = spec.meta.dynamic
    if is_structured_instance(results) and (fields or is_dyn):
        results = structured_to_dict(results)

    if already_serialized(results):
        return {"result": results}, None

    # tuple -> map by order of fixed field names
    if isinstance(results, tuple):
        names = _ordered_field_names(spec)
        if len(names) != len(results):
            return None, exit_codes.ERROR_RESULT_OUTPUT_MISMATCH
        outs: Dict[str, Any] = {}
        for i, name in enumerate(names):
            child_spec = fields[name]
            val = results[i]
            outs[name] = serialize_ports(val, child_spec, serializers=serializers, user=user)
        return outs, None

    # dict
    if isinstance(results, dict):
        remaining = dict(results)
        # optional inline exit code
        exit_code_val = remaining.pop("exit_code", None)
        if exit_code_val is not None:
            if isinstance(exit_code_val, ExitCode):
                ec = exit_code_val
            elif isinstance(exit_code_val, dict):
                ec = ExitCode(exit_code_val.get("status", 1), exit_code_val.get("message", ""))
            elif isinstance(exit_code_val, int):
                ec = ExitCode(exit_code_val)
            else:
                ec = ExitCode(1, f"Invalid inline exit_code payload: {type(exit_code_val)}")
            if ec.status != 0:
                return None, ec

        outs: Dict[str, Any] = {}
        if len(fields) == 1 and not is_dyn:
            ((only_name, only_spec),) = fields.items()
            # if user used the same key as port name, use that value;
            if only_name in results:
                outs[only_name] = serialize_ports(results.pop(only_name), only_spec, serializers=serializers, user=user)
                if results:
                    logger.warning(f"Found extra results that are not included in the output: {list(results.keys())}")
            else:
                # else treat the entire dict as the value for that single port.
                outs[only_name] = serialize_ports(results, only_spec, serializers=serializers, user=user)
            return outs, None

        # fixed fields
        for name, child_spec in fields.items():
            if name in remaining:
                value = remaining.pop(name)
                outs[name] = serialize_ports(value, child_spec, serializers=serializers, user=user)
            else:
                # If the field is explicitly required -> invalid output
                required = getattr(child_spec.meta, "required", None)
                if required is True:
                    logger.warning(f"Missing required output: {name}")
                    return None, exit_codes.ERROR_MISSING_OUTPUT
        # dynamic items
        if is_dyn:
            outs.update(
                serialize_ports(
                    remaining,
                    spec or SocketSpec(identifier="node_graph.any"),
                    serializers=serializers,
                    user=user,
                )
            )
            return outs, None
        # not dynamic -> leftovers are unexpected (warn but continue)
        if remaining:
            logger.warning(f"Found extra results that are not included in the output: {list(remaining.keys())}")
        return outs, None

    # single fixed output + non-dict/tuple scalar
    if len(fields) == 1 and not is_dyn:
        ((only_name, only_spec),) = fields.items()
        return {only_name: serialize_ports(results, only_spec, serializers=serializers, user=user)}, None

    # empty output spec + None result
    if len(fields) == 0 and results is None:
        return {}, None

    return None, exit_codes.ERROR_RESULT_OUTPUT_MISMATCH
