from __future__ import annotations

import importlib
import inspect
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
    _SpecialForm,
    get_type_hints,
)

from aiida.common.exceptions import NotExistent
from aiida.orm import Computer, InstalledCode, User, load_code, load_computer
from aiida.node_graph.socket_meta import SocketMeta
from aiida.node_graph.socket_spec import SocketSpec
from aiida.node_graph.utils.struct_utils import is_structured_instance, structured_to_dict

from aiida.pythonjob.data.serializer import general_serializer


def get_required_imports(func: Callable) -> Dict[str, set]:
    """Retrieve type hints and the corresponding modules."""
    type_hints = get_type_hints(func)
    imports = {}

    def add_imports(type_hint):
        if isinstance(type_hint, _SpecialForm):  # Handle special forms like Any, Union, Optional
            module_name = "typing"
            type_name = type_hint._name or str(type_hint)
        elif hasattr(type_hint, "__origin__"):  # This checks for higher-order types like List, Dict
            module_name = type_hint.__module__
            type_name = getattr(type_hint, "_name", None) or getattr(type_hint.__origin__, "__name__", None)
            for arg in getattr(type_hint, "__args__", []):
                if arg is type(None):
                    continue
                add_imports(arg)  # Recursively add imports for each argument
        elif hasattr(type_hint, "__module__"):
            module_name = type_hint.__module__
            type_name = type_hint.__name__
        else:
            return  # If no module or origin, we can't import it, e.g., for literals
        if type_name is not None:
            if module_name not in imports:
                imports[module_name] = set()
            imports[module_name].add(type_name)

    for _, type_hint in type_hints.items():
        add_imports(type_hint)
    return imports


def inspect_function(
    func: Callable, inspect_source: bool = False, register_pickle_by_value: bool = False
) -> Dict[str, Any]:
    """Serialize a function for storage or transmission."""
    # we need save the source code explicitly, because in the case of jupyter notebook,
    # the source code is not saved in the pickle file
    import cloudpickle

    if inspect_source:
        try:
            source_code = inspect.getsource(func)
            # Split the source into lines for processing
            source_code_lines = source_code.split("\n")
            source_code = "\n".join(source_code_lines)
        except OSError:
            source_code = "Failed to retrieve source code."
    else:
        source_code = ""

    if register_pickle_by_value:
        module = importlib.import_module(func.__module__)
        cloudpickle.register_pickle_by_value(module)
        pickled_function = cloudpickle.dumps(func)
        cloudpickle.unregister_pickle_by_value(module)
    else:
        pickled_function = cloudpickle.dumps(func)

    return {"source_code": source_code, "mode": "use_pickled_function", "pickled_function": pickled_function}


def build_function_data(func: Callable, register_pickle_by_value: bool = False) -> Dict[str, Any]:
    """Inspect the function and return a dictionary with the function data."""
    import types

    if isinstance(func, (types.FunctionType, types.BuiltinFunctionType, type)):
        # Check if callable is nested (contains dots in __qualname__ after the first segment)
        function_data = {"name": func.__name__}
        if func.__module__ == "__main__" or "." in func.__qualname__.split(".", 1)[-1]:
            # Local or nested callable, so pickle the callable
            function_data.update(inspect_function(func, inspect_source=True))
        else:
            # Global callable (function/class), store its module and name for reference
            function_data.update(inspect_function(func, register_pickle_by_value=register_pickle_by_value))
    else:
        raise TypeError("Provided object is not a callable function or class.")
    return function_data


def get_or_create_code(
    label: str = "python3",
    computer: Optional[Union[str, "Computer"]] = "localhost",
    filepath_executable: Optional[str] = None,
    prepend_text: str = "",
) -> InstalledCode:
    """Try to load code, create if not exit."""

    computer_label = computer.label if isinstance(computer, Computer) else computer

    try:
        return load_code(f"{label}@{computer_label}")
    except NotExistent:
        description = f"Code on computer: {computer_label}"
        computer = load_computer(computer_label)
        filepath_executable = filepath_executable or label
        code = InstalledCode(
            computer=computer,
            label=label,
            description=description,
            filepath_executable=filepath_executable,
            default_calc_job_plugin="pythonjob.pythonjob",
            prepend_text=prepend_text,
        )

        code.store()
        return code


def generate_bash_to_create_python_env(
    name: str,
    pip: Optional[List[str]] = None,
    conda: Optional[Dict[str, list]] = None,
    modules: Optional[List[str]] = None,
    python_version: Optional[str] = None,
    variables: Optional[Dict[str, str]] = None,
    shell: str = "posix",
):
    """
    Generates a bash script for creating or updating a Python environment on a remote computer.
    If python_version is None, it uses the Python version from the local environment.
    Conda is a dictionary that can include 'channels' and 'dependencies'.
    """
    import sys

    pip = pip or []
    conda_channels = conda.get("channels", []) if conda else []
    conda_dependencies = conda.get("dependencies", []) if conda else []
    # Determine the Python version from the local environment if not provided
    local_python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    desired_python_version = python_version if python_version is not None else local_python_version

    # Start of the script
    script = "#!/bin/bash\n\n"

    # Load modules if provided
    if modules:
        script += "# Load specified system modules\n"
        for module in modules:
            script += f"module load {module}\n"

    # Conda shell hook initialization for proper conda activation
    script += "# Initialize Conda for this shell\n"
    script += f'eval "$(conda shell.{shell} hook)"\n'

    script += "# Setup the Python environment\n"
    script += "if ! conda info --envs | grep -q ^{name}$; then\n"
    script += "    # Environment does not exist, create it\n"
    if conda_dependencies:
        dependencies_string = " ".join(conda_dependencies)
        script += f"    conda create -y -n {name} python={desired_python_version} {dependencies_string}\n"
    else:
        script += f"    conda create -y -n {name} python={desired_python_version}\n"
    script += "fi\n"
    if conda_channels:
        script += "EXISTING_CHANNELS=$(conda config --show channels)\n"
        script += "for CHANNEL in " + " ".join(conda_channels) + ";\n"
        script += "do\n"
        script += '    if ! echo "$EXISTING_CHANNELS" | grep -q $CHANNEL; then\n'
        script += "        conda config --prepend channels $CHANNEL\n"
        script += "    fi\n"
        script += "done\n"
    script += f"conda activate {name}\n"

    # Install pip packages
    if pip:
        script += f"pip install {' '.join(pip)}\n"

    # Set environment variables
    if variables:
        for var, value in variables.items():
            script += f"export {var}='{value}'\n"

    # End of the script
    script += "echo 'Environment setup is complete.'\n"

    return script


def create_conda_env(
    computer: Union[str, Computer],
    name: str,
    pip: Optional[List[str]] = None,
    conda: Optional[List[str]] = None,
    modules: Optional[List[str]] = None,
    python_version: Optional[str] = None,
    variables: Optional[Dict[str, str]] = None,
    shell: str = "posix",
) -> Tuple[bool, str]:
    """Test that there is no unexpected output from the connection."""
    # Execute a command that should not return any error, except ``NotImplementedError``
    # since not all transport plugins implement remote command execution.
    from aiida.common.exceptions import NotExistent

    user = User.collection.get_default()
    if isinstance(computer, str):
        computer = load_computer(computer)
    try:
        authinfo = computer.get_authinfo(user)
    except NotExistent:
        raise f"Computer<{computer.label}> is not yet configured for user<{user.email}>"

    scheduler = authinfo.computer.get_scheduler()
    transport = authinfo.get_transport()

    script = generate_bash_to_create_python_env(name, pip, conda, modules, python_version, variables, shell)
    with transport:
        scheduler.set_transport(transport)
        try:
            retval, stdout, stderr = transport.exec_command_wait(script)
        except NotImplementedError:
            return (
                True,
                f"Skipped, remote command execution is not implemented for the "
                f"`{computer.transport_type}` transport plugin",
            )

        if retval != 0:
            return (
                False,
                f"The command returned a non-zero return code ({retval})",
            )

        template = """
We detected an error while creating the environemnt on the remote computer, as shown between the bars
=============================================================================================
{}
=============================================================================================
Please check!
    """
        if stderr:
            return False, template.format(stderr)

        if stdout:
            # the last line is the echo 'Environment setup is complete.'
            if not stdout.strip().endswith("Environment setup is complete."):
                return False, template.format(stdout)
            else:
                return True, "Environment setup is complete."

    return True, None


def _ensure_spec(schema: SocketSpec | Dict[str, Any]) -> SocketSpec:
    if isinstance(schema, SocketSpec):
        return schema
    if isinstance(schema, dict):
        return SocketSpec.from_dict(schema)
    raise TypeError(f"Unsupported schema type: {type(schema)}")


def _has_var_kwargs(spec: SocketSpec) -> bool:
    for field in spec.fields.values():
        role = getattr(field.meta, "call_role", None)
        if role == "var_kwargs":
            return True
    return False


def serialize_ports(
    python_data: Any,
    port_schema: SocketSpec | Dict[str, Any],
    serializers: Optional[Dict[str, str]] = None,
    user: Optional[User] = None,
) -> Any:
    """Serialize raw Python data to AiiDA Data following a SocketSpec schema.

    Handles special namespace roles like ``var_kwargs`` by accepting arbitrary
    keys at that namespace level (using ``item`` if provided, otherwise ANY).
    """
    spec = _ensure_spec(port_schema)

    # Namespace
    if spec.is_namespace():
        name = getattr(spec.meta, "help", None) or "<namespace>"
        if is_structured_instance(python_data):
            python_data = structured_to_dict(python_data)
        if not isinstance(python_data, dict):
            raise ValueError(f"Expected dict for namespace '{name}', got {type(python_data)}")

        out: Dict[str, Any] = {}
        fields = spec.fields or {}

        for key, value in python_data.items():
            if key in fields:
                child_spec = fields[key]
                # Metadata is not serialized
                if child_spec.meta.is_metadata:
                    out[key] = value
                elif child_spec.is_namespace():
                    out[key] = serialize_ports(value, child_spec, serializers=serializers)
                else:
                    out[key] = general_serializer(value, serializers=serializers, store=False, user=user)
            elif spec.meta.dynamic:
                if spec.item is None:
                    if isinstance(value, dict):
                        item = SocketSpec(identifier="node_graph.namespace", meta=SocketMeta(dynamic=True))
                        out[key] = serialize_ports(value, item, serializers=serializers)
                    else:
                        out[key] = general_serializer(value, serializers=serializers, store=False, user=user)
                elif spec.item.is_namespace():
                    out[key] = serialize_ports(value, spec.item, serializers=serializers)
                else:
                    out[key] = general_serializer(value, serializers=serializers, store=False, user=user)
            else:
                raise ValueError(f"Unexpected key '{key}' for namespace '{name}' (not dynamic).")
        return out

    # Leaf
    return general_serializer(python_data, serializers=serializers, store=False, user=user)
