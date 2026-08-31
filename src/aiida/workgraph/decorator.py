from __future__ import annotations

import inspect
from collections.abc import Callable

from node_graph.error_handler import ErrorHandlerSpec, normalize_error_handlers
from node_graph.socket_spec import SocketSpec
from node_graph.task_spec import TaskSpec

from aiida.engine import CalcJob, WorkChain, calcfunction, workfunction
from aiida.workgraph.task import Task
from aiida.workgraph.tasks.aiida import AiiDAProcessTask, _build_aiida_function_taskspec

from .task import TaskHandle
from .workgraph import WorkGraph


def _spec_for(
    obj,
    *,
    identifier: str | None,
    inputs: SocketSpec | None = None,
    outputs: SocketSpec | None = None,
    catalog: str | None = None,
    error_handlers: dict[str, ErrorHandlerSpec] | None = None,
) -> TaskSpec:
    # AiiDA process classes
    if inspect.isclass(obj) and issubclass(obj, (CalcJob, WorkChain)):
        return AiiDAProcessTask.build(obj, attached_error_handlers=error_handlers)

    # AiiDA process functions (calcfunction/workfunction)
    if callable(obj) and getattr(obj, 'node_class', False):
        return _build_aiida_function_taskspec(
            obj,
            identifier=identifier,
            in_spec=inputs,
            out_spec=outputs,
            error_handlers=error_handlers,
            catalog=catalog or 'Others',
        )

    # Plain Python function -> PyFunction
    if callable(obj):
        # Lazy: keeps ``import aiida.workgraph`` free of the aiida-pythonjob dependency.
        from aiida.workgraph.tasks.pythonjob_tasks import build_pyfunction_taskspec

        spec = build_pyfunction_taskspec(
            obj,
            identifier=identifier,
            in_spec=inputs,
            out_spec=outputs,
            error_handlers=error_handlers,
            catalog=catalog or 'Others',
        )
        return spec

    raise ValueError(f'Unsupported object for @task: {obj!r}')


def build_task_from_callable(
    executor: Callable,
    inputs: SocketSpec | list | None = None,
    outputs: SocketSpec | list | None = None,
) -> Task:
    """Build task from a callable object.
    First, check if the executor is already a task.
    If not, check if it is a function or a class.
    If it is a function, build task from function.
    If it is a class, it only supports CalcJob and WorkChain.
    """
    from node_graph.task import Task

    # if it is already a task, return it
    if (
        hasattr(executor, '_TaskCls') and inspect.isclass(executor._TaskCls) and issubclass(executor._TaskCls, Task)
    ) or (inspect.isclass(executor) and issubclass(executor, Task)):
        return executor
    if inspect.isfunction(executor):
        # calcfunction and workfunction
        if getattr(executor, 'node_class', False):
            return task(inputs=inputs, outputs=outputs)(executor)
        else:
            return task(inputs=inputs, outputs=outputs)(executor)
    elif issubclass(executor, CalcJob) or issubclass(executor, WorkChain):
        if inputs is not None or outputs is not None:
            raise ValueError('Can not override inputs or outputs of an AiiDA process classes.')
        return task()(executor)
    raise ValueError(f'The executor {executor} is not supported.')


def nonfunctional_usage(callable: Callable):
    """
    This is a decorator for a decorator factory (a function that returns a decorator).
    It allows the usage of the decorator factory in a nonfunctional way. So a decorator
    factory that has been decorated by this decorator that could only be used befor like
    this

    .. code-block:: python

        @decorator_factory()
        def foo():
            pass

    can now be also used like this

    .. code-block:: python

        @decorator_factory
        def foo():
            pass

    """

    def decorator_task_wrapper(*args, **kwargs):
        if len(args) == 1 and isinstance(args[0], Callable) and len(kwargs) == 0:
            return callable()(args[0])
        else:
            return callable(*args, **kwargs)

    return decorator_task_wrapper


class TaskDecoratorCollection:
    """Collection of task decorators."""

    @staticmethod
    @nonfunctional_usage
    def decorator_task(
        identifier: str | None = None,
        inputs: SocketSpec | list | None = None,
        outputs: SocketSpec | list | None = None,
        error_handlers: dict[str, ErrorHandlerSpec] | None = None,
        catalog: str = 'Others',
    ) -> Callable:
        """Generate a decorator that register a function as a task.

        Attributes:
            indentifier (str): task identifier
            catalog (str): task catalog
            inputs (list): task inputs
            outputs (list): task outputs
        """

        def decorator(obj: WorkGraph | type | callable) -> TaskHandle:
            normalized_handlers = normalize_error_handlers(error_handlers)
            spec = _spec_for(
                obj,
                identifier=identifier,
                catalog=catalog,
                inputs=inputs,
                outputs=outputs,
                error_handlers=normalized_handlers,
            )

            handle = TaskHandle(spec)
            handle._callable = obj
            return handle

        return decorator

    @staticmethod
    @nonfunctional_usage
    def decorator_graph(
        identifier: str | None = None,
        catalog: str | None = None,
        inputs: SocketSpec | list | None = None,
        outputs: SocketSpec | list | None = None,
        max_depth: int = 100,
        max_number_jobs: int | None = None,
    ) -> Callable:
        """Generate a decorator that register a function as a graph task.
        Attributes:
            indentifier (str): task identifier
            catalog (str): task catalog
            inputs (list): task inputs
            outputs (list): task outputs
        """

        def decorator(func) -> TaskHandle:
            from aiida.workgraph.tasks.graph_task import _build_graph_task_taskspec

            handle = TaskHandle(
                _build_graph_task_taskspec(
                    func,
                    identifier=identifier,
                    catalog=catalog,
                    in_spec=inputs,
                    out_spec=outputs,
                    max_depth=max_depth,
                    max_number_jobs=max_number_jobs,
                )
            )
            handle._callable = func
            return handle

        return decorator

    @staticmethod
    @nonfunctional_usage
    def calcfunction(
        inputs: SocketSpec | list | None = None,
        outputs: SocketSpec | list | None = None,
        catalog: str | None = None,
        error_handlers: dict[str, ErrorHandlerSpec] | None = None,
    ) -> Callable:
        def decorator(func) -> TaskHandle:
            func_decorated = calcfunction(func)
            handle = TaskHandle(
                _build_aiida_function_taskspec(
                    func_decorated,
                    in_spec=inputs,
                    out_spec=outputs,
                    catalog=catalog,
                    error_handlers=error_handlers,
                )
            )
            handle._callable = func_decorated
            return handle

        return decorator

    @staticmethod
    @nonfunctional_usage
    def workfunction(
        inputs: SocketSpec | list | None = None,
        outputs: SocketSpec | list | None = None,
        catalog: str | None = None,
        error_handlers: dict[str, ErrorHandlerSpec] | None = None,
    ) -> Callable:
        def decorator(func) -> TaskHandle:
            func_decorated = workfunction(func)
            handle = TaskHandle(
                _build_aiida_function_taskspec(
                    func_decorated,
                    in_spec=inputs,
                    out_spec=outputs,
                    catalog=catalog,
                    error_handlers=error_handlers,
                )
            )
            handle._callable = func_decorated
            return handle

        return decorator

    @staticmethod
    @nonfunctional_usage
    def pythonjob(
        inputs: SocketSpec | list | None = None,
        outputs: SocketSpec | list | None = None,
        catalog: str | None = None,
        error_handlers: dict[str, ErrorHandlerSpec] | None = None,
    ) -> Callable:
        def decorator(func) -> TaskHandle:
            from aiida.workgraph.tasks.pythonjob_tasks import build_pythonjob_taskspec

            spec = build_pythonjob_taskspec(
                func,
                in_spec=inputs,
                out_spec=outputs,
                catalog=catalog,
                error_handlers=error_handlers,
            )
            handle = TaskHandle(spec)
            handle._callable = func
            return handle

        return decorator

    @staticmethod
    @nonfunctional_usage
    def monitor(
        inputs: SocketSpec | list | None = None,
        outputs: SocketSpec | list | None = None,
        catalog: str | None = None,
        error_handlers: dict[str, ErrorHandlerSpec] | None = None,
    ) -> Callable:
        def decorator(func) -> TaskHandle:
            from aiida.workgraph.tasks.pythonjob_tasks import build_monitor_function_taskspec

            handle = TaskHandle(
                build_monitor_function_taskspec(
                    func,
                    in_spec=inputs,
                    out_spec=outputs,
                    catalog=catalog,
                    error_handlers=error_handlers,
                )
            )
            handle._callable = func
            return handle

        return decorator

    # Making decorator_task accessible as 'task'
    task = decorator_task

    # Making decorator_graph accessible as 'graph'
    graph = decorator_graph

    def __call__(self, *args, **kwargs):
        # This allows using '@task' to directly apply the decorator_task functionality
        if len(args) == 1 and isinstance(args[0], Callable) and len(kwargs) == 0:
            return self.decorator_task()(args[0])
        else:
            return self.decorator_task(*args, **kwargs)


task = TaskDecoratorCollection()
