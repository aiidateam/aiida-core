import importlib
from typing import Any


def import_from_path(path: str) -> Any:
    module_name, object_name = path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    try:
        return getattr(module, object_name)
    except AttributeError:
        raise AttributeError(f"{object_name} not found in module {module_name}.")
