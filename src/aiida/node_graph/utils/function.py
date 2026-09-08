from __future__ import annotations

from typing import Any, Dict, Optional
import inspect
import importlib.metadata

__all__ = ["prepare_function_inputs", "is_function_like", "inspect_callable_metadata"]


def is_function_like(obj: Any) -> bool:
    return inspect.isfunction(obj) or inspect.ismethod(obj) or inspect.isbuiltin(obj)


def inspect_callable_metadata(func: Any) -> Dict[str, Optional[str]]:
    """Return a compact identity record for a Python callable."""

    module = getattr(func, "__module__", None)
    qualname = getattr(func, "__qualname__", None) or getattr(func, "__name__", None)
    callable_path = f"{module}.{qualname}" if module and qualname else qualname
    try:
        filename = inspect.getsourcefile(func) or inspect.getfile(func)  # type: ignore[arg-type]
    except Exception:
        filename = None
    package = module.split(".")[0] if module else None
    package_version: Optional[str]
    if package:
        try:
            package_version = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            package_version = None
    else:
        package_version = None

    return {
        "module": module,
        "qualname": qualname,
        "callable_path": callable_path,
        "file_path": filename,
        "package": package,
        "package_version": package_version,
    }


def prepare_function_inputs(func, *call_args, **call_kwargs):
    """Prepare inputs from a callable's signature and provided args/kwargs.

    - POSITIONAL_ONLY and POSITIONAL_OR_KEYWORD are consumed from *call_args
    - VAR_POSITIONAL (*args) not supported (raises)
    - Existing **call_kwargs win over args
    """
    inputs = dict(call_kwargs or {})
    if func is not None:
        arguments = list(call_args)
        orginal_func = func._callable if hasattr(func, "_callable") else func
        for name, parameter in inspect.signature(orginal_func).parameters.items():
            if parameter.kind in [
                parameter.POSITIONAL_ONLY,
                parameter.POSITIONAL_OR_KEYWORD,
            ]:
                try:
                    inputs[name] = arguments.pop(0)
                except IndexError:
                    pass
            elif parameter.kind is parameter.VAR_POSITIONAL:
                # not supported
                raise ValueError("VAR_POSITIONAL is not supported.")
    return inputs
