from __future__ import annotations
from typing import Any, Optional, Callable, List, Dict
import inspect
from .error_handler import ErrorHandlerSpec
from .task import Task
from .task_spec import TaskHandle, BaseHandle
from .socket_spec import SocketSpec
from .utils.function import inspect_callable_metadata


def build_task_from_callable(
    executor: Callable,
    inputs: Optional[SocketSpec | List[str]] = None,
    outputs: Optional[SocketSpec | List[str]] = None,
) -> Task:
    """Build task from a callable object.
    First, check if the executor is already a task.
    If not, check if it is a function or a class.
    If it is a function, build task from function.
    """

    # if it already has Task class, return it
    if (
        isinstance(executor, BaseHandle)
        or inspect.isclass(executor)
        and issubclass(executor, Task)
    ):
        return executor
    if callable(executor):
        return task(inputs=inputs, outputs=outputs)(executor)

    raise ValueError(f"The executor {executor} is not supported.")


def decorator_task(
    identifier: Optional[str] = None,
    inputs: Optional[SocketSpec | List[str]] = None,
    outputs: Optional[SocketSpec | List[str]] = None,
    error_handlers: Optional[Dict[str, ErrorHandlerSpec]] = None,
    catalog: str = "Others",
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Generate a decorator that register a function as a Graph task.
    After decoration, calling that function `func(x, y, ...)`
    dynamically creates a task in the current Graph context
    instead of executing Python code directly.

    Attributes:
        indentifier (str): task identifier
        catalog (str): task catalog
        inputs (dict): task inputs
        outputs (dict): task outputs
    """

    def wrap(func) -> TaskHandle:
        from aiida.node_graph.tasks.function_task import FunctionTask

        callable_meta = inspect_callable_metadata(func)
        metadata = {"callable": callable_meta}
        version = callable_meta.get("package_version")
        resolved_identifier = identifier
        if resolved_identifier is None:
            package = callable_meta.get("package")
            func_name = getattr(func, "__name__", None) or callable_meta.get("qualname")
            if package and func_name:
                resolved_identifier = f"{package}.{func_name}"
            else:
                resolved_identifier = func_name or "task"
        return FunctionTask.build(
            obj=func,
            identifier=resolved_identifier,
            catalog=catalog,
            input_spec=inputs,
            output_spec=outputs,
            error_handlers=error_handlers,
            metadata=metadata,
            version=version,
        )

    return wrap


def decorator_graph(
    identifier: Optional[str] = None,
    inputs: Optional[SocketSpec | list] = None,
    outputs: Optional[SocketSpec | list] = None,
    catalog: str = "Others",
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Generate a decorator that register a function as a graph task.

    Attributes:
        indentifier (str): task identifier
        catalog (str): task catalog
        inputs (dict): task inputs
        outputs (dict): task outputs
    """

    def wrap(func) -> TaskHandle:
        from aiida.node_graph.tasks.function_task import FunctionTask

        callable_meta = inspect_callable_metadata(func)
        metadata = {"callable": callable_meta}
        version = callable_meta.get("package_version")
        resolved_identifier = identifier
        if resolved_identifier is None:
            package = callable_meta.get("package")
            func_name = getattr(func, "__name__", None) or callable_meta.get("qualname")
            if package and func_name:
                resolved_identifier = f"{package}.{func_name}"
            else:
                resolved_identifier = func_name or "graph"
        return FunctionTask.build(
            obj=func,
            identifier=resolved_identifier,
            task_type="graph",
            catalog=catalog,
            input_spec=inputs,
            output_spec=outputs,
            metadata=metadata,
            version=version,
        )

    return wrap


class TaskDecoratorCollection:
    """Collection of task decorators."""

    task: Callable[..., Any] = staticmethod(decorator_task)
    graph: Callable[..., Any] = staticmethod(decorator_graph)

    # Alias '@task' to '@task.task'.
    def __call__(self, *args, **kwargs):
        return self.task(*args, **kwargs)


task: TaskDecoratorCollection = TaskDecoratorCollection()
