import dataclasses
from typing import Optional, Callable, Dict, Any, Union
import inspect
import base64
import importlib
import cloudpickle
from enum import Enum


class ExecutorMode(str, Enum):
    """
    Defines the strategy for locating and executing code.
    """

    MODULE = "module"  # A callable that can be imported from a module path.
    GRAPH = "graph"  # A nested computational graph.
    PICKLED_CALLABLE = "pickled_callable"  # A callable serialized using cloudpickle.


def serialize_callable(
    func: Callable, register_pickle_by_value: bool = False, include_source: bool = True
) -> Dict[str, Any]:
    """
    Serialize a callable (function, class, etc.) to a dictionary with:
      - optional source code
      - pickled representation
      - callable name

    Args:
        func (Callable): The callable to inspect and serialize.
        register_pickle_by_value (bool, optional): Whether to register the
            callable's module with cloudpickle for pickling by value. Defaults
            to False.
        include_source (bool, optional): Whether to include the callable's
            source code in the output. Defaults to False.

    Returns:
        Dict[str, Any]: A dictionary containing the source code (if requested),
            the name of the callable, a base64-encoded pickled representation,
            and a mode key set to "pickled_callable".
    """

    if not callable(func):
        raise TypeError("Provided object is not a callable function or class.")
    source_code = ""
    callable_name = func.__name__
    if func.__module__ == "__main__" or "." in func.__qualname__.split(".", 1)[-1]:
        mode = ExecutorMode.PICKLED_CALLABLE
        pickled_data = cloudpickle.dumps(func)
        # Base64 encode the pickled callable
        pickled_callable = base64.b64encode(pickled_data).decode("utf-8")
        module_path = None
        # Attempt to retrieve source code if requested
        if include_source:
            try:
                source_code = inspect.getsource(func)
            except (OSError, TypeError):
                source_code = "Failed to retrieve source code."
    else:
        # Optionally register the module for pickling by value
        if register_pickle_by_value:
            module_path = func.__module__
            module = importlib.import_module(module_path)
            cloudpickle.register_pickle_by_value(module)
            pickled_data = cloudpickle.dumps(func)
            # Unregister after pickling
            cloudpickle.unregister_pickle_by_value(module)
            mode = ExecutorMode.PICKLED_CALLABLE
            pickled_callable = base64.b64encode(pickled_data).decode("utf-8")
        else:
            # Global callable (function/class), store its module and name for reference
            mode = ExecutorMode.MODULE
            module_path = func.__module__
            pickled_callable = None

    return {
        "mode": mode,
        "module_path": module_path,
        "pickled_callable": pickled_callable,
        "callable_name": callable_name,
        "source_code": source_code,
    }


@dataclasses.dataclass
class BaseExecutor:
    """
    A base class that encapsulates different ways of representing and executing
    a callable or computational graph.
    """

    mode: Optional[ExecutorMode] = None  # "module", "graph", "pickled_callable"
    module_path: Optional[str] = None
    callable_name: Optional[str] = None
    callable_kind: Optional[str] = None
    graph_data: Optional[dict] = None
    pickled_callable: Optional[str] = None
    source_code: Optional[str] = None
    metadata: Optional[dict] = None

    def __post_init__(self):
        """
        Post-initialization hook that inspects and normalizes
        module_path/callable_name if mode is 'module'.
        """
        self._normalize_module_mode()

    @classmethod
    def from_graph(cls, graph: Any) -> "BaseExecutor":
        """
        Factory method that creates a Executor from a graph-like object that
        can be converted to a dictionary.
        """
        graph_data = graph.to_dict(should_serialize=True)
        return cls(mode=ExecutorMode.GRAPH, graph_data=graph_data)

    def _normalize_module_mode(self) -> None:
        """
        Ensure the Executor is properly configured for "module" mode if
        `module_path` is set. Automatically splits the module_path to extract
        the callable name if `callable_name` is None.
        """
        if self.mode and isinstance(self.mode, str):
            try:
                self.mode = ExecutorMode(self.mode)
            except ValueError:
                # Provide a helpful error if the string is not a valid mode
                valid_modes = [e.value for e in ExecutorMode]
                raise ValueError(
                    f"'{self.mode}' is not a valid ExecutorMode. Use one of {valid_modes}."
                )

        if self.module_path is not None and self.mode is None:
            self.mode = ExecutorMode.MODULE

        if self.mode != ExecutorMode.MODULE:
            return

        if self.module_path is None:
            raise ValueError("module_path is required when mode is 'module'.")

        if self.callable_name is None:
            parts = self.module_path.split(".")
            if len(parts) < 2:
                raise ValueError(
                    "module_path must contain at least one dot to separate "
                    "the module from the callable (e.g. 'mymodule.myfunc')"
                )
            self.callable_name = parts[-1]
            self.module_path = ".".join(parts[:-1])

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert this Executor instance to a dictionary.
        """
        data = dataclasses.asdict(self)
        data["mode"] = self.mode.value if self.mode else None
        return data

    @property
    def callable(self) -> Union[Callable, None]:
        """
        Dynamically retrieve the actual callable based on the mode.
        """
        if self.mode == ExecutorMode.MODULE:
            try:
                module = importlib.import_module(self.module_path)
                return getattr(module, self.callable_name)
            except (ImportError, AttributeError) as e:
                raise ImportError(
                    f"Failed to import '{self.module_path}' or find "
                    f"callable '{self.callable_name}'. Error: {e}"
                ) from e

        # 'graph' mode does not have a direct callable.
        # Subclasses will handle other modes.
        return None


class SafeExecutor(BaseExecutor):
    """
    An executor that only supports safe modes ('module', 'graph'). It explicitly
    disallows 'pickled_callable' to prevent arbitrary code execution from
    untrusted sources. This should be used when deserializing from storage.
    """


class RuntimeExecutor(BaseExecutor):
    """
    An executor that supports all modes, including 'pickled_callable'.
    This is intended for runtime, in-memory graph construction where the
    callables are coming from a trusted source (i.e., the code itself).
    """

    @classmethod
    def from_callable(
        cls,
        func: Callable,
        register_pickle_by_value: bool = False,
        include_source: bool = True,
    ) -> "RuntimeExecutor":
        """
        Factory method that creates a RuntimeExecutor from a callable by serializing it.
        """
        executor_data = serialize_callable(
            func,
            register_pickle_by_value=register_pickle_by_value,
            include_source=include_source,
        )
        return cls(**executor_data)

    @property
    def callable(self) -> Union[Callable, None]:
        """
        Dynamically retrieve the actual callable, including support for unpickling.
        """
        # First, try the safe modes from the base class
        c = super().callable
        if c is not None:
            return c

        if self.mode == ExecutorMode.PICKLED_CALLABLE:
            if not self.pickled_callable:
                return None
            pickled_data = base64.b64decode(self.pickled_callable.encode("utf-8"))
            func = cloudpickle.loads(pickled_data)
            return func

        return None
