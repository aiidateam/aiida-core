from __future__ import annotations

from collections.abc import Callable
from typing import Annotated, Any

from aiida_pythonjob import MonitorPyFunction, PyFunction, PythonJob, pyfunction
from node_graph.error_handler import ErrorHandlerSpec
from node_graph.executor import RuntimeExecutor
from node_graph.socket_spec import SocketMeta, SocketSpec, SocketSpecSelect
from node_graph.task_spec import BaseHandle, TaskSpec

from aiida import orm
from aiida.common.extendeddicts import AttributeDict
from aiida.engine import run_get_node
from aiida.workgraph.enums import TaskAction, TaskState
from aiida.workgraph.socket_spec import namespace
from aiida.workgraph.task import Task
from aiida.workgraph.utils import create_and_pause_process

from .function_task import build_callable_TaskSpec


class BaseSerializablePythonTask(Task):
    """
    A base Task that handles serialization and deserialization
    of Python data into AiiDA Data nodes, so that raw Python data
    can be stored/passed around by the WorkGraph engine.
    Subclasses must implement their own `execute` method.
    """

    @property
    def non_function_inputs(self):
        return self.spec.metadata.get('non_function_inputs', [])

    @property
    def non_function_outputs(self):
        return self.spec.metadata.get('non_function_outputs', [])

    @property
    def function_inputs_spec(self):
        inputs_spec = namespace(
            _=Annotated[
                Any,
                self.spec.inputs,
                SocketSpecSelect(exclude=self.non_function_inputs),
            ]
        ).fields['_']
        return inputs_spec

    @property
    def function_outputs_spec(self):
        outputs_spec = namespace(
            _=Annotated[
                Any,
                self.spec.outputs,
                SocketSpecSelect(exclude=self.non_function_outputs),
            ]
        ).fields['_']
        return outputs_spec

    def get_function_inputs(self, kwargs, var_kwargs):
        function_inputs = kwargs.pop('function_inputs', {}) or {}
        for key in list(kwargs.keys()):
            if key not in self.non_function_inputs:
                function_inputs[key] = kwargs.pop(key)
        # Handle var_kwargs
        if self.get_args_data()['var_kwargs'] is not None:
            var_key = self.get_args_data()['var_kwargs']
            function_inputs.pop(var_key, None)
            if var_kwargs:
                if isinstance(var_kwargs, (dict, AttributeDict)):
                    function_inputs.update(var_kwargs)
                elif isinstance(var_kwargs, orm.Data):
                    function_inputs.update(var_kwargs.value)
                else:
                    raise ValueError(f'Invalid var_kwargs type: {type(var_kwargs)}')
        return function_inputs

    def get_process_metadata(self, kwargs):
        metadata = kwargs.pop('metadata', {})
        metadata.update({'call_link_label': self.name})
        return metadata


class PythonJobTask(BaseSerializablePythonTask):
    """PythonJob Task."""

    identifier = 'workgraph.pythonjob'

    def execute(self, engine_process, args=None, kwargs=None, var_kwargs=None):
        """
        Here is the specialized 'execute' method for PythonJobTask,
        including the 'prepare_for_python_task' logic.
        """
        from aiida_pythonjob import prepare_pythonjob_inputs

        # Pull out code, computer, etc
        computer = kwargs.pop('computer', 'localhost')
        if isinstance(computer, orm.Str):
            computer = computer.value
        command_info = kwargs.pop('command_info', {})
        register_pickle_by_value = kwargs.pop('register_pickle_by_value', False)
        upload_files = kwargs.pop('upload_files', {})
        metadata = self.get_process_metadata(kwargs)
        function_inputs = self.get_function_inputs(kwargs, var_kwargs)
        func = RuntimeExecutor(**self.get_executor().to_dict()).callable
        # If it's a wrapped function, unwrap
        if isinstance(func, BaseHandle) and hasattr(func, '_callable'):
            func = func._callable

        if hasattr(func, 'is_process_function'):
            func = func.func

        # Prepare the final inputs for PythonJob
        inputs = prepare_pythonjob_inputs(
            function=func,
            function_inputs=function_inputs,
            inputs_spec=self.function_inputs_spec,
            outputs_spec=self.function_outputs_spec,
            code=kwargs.pop('code', None),
            command_info=command_info,
            computer=computer,
            metadata=metadata,
            upload_files=upload_files,
            process_label=f'PythonJob<{self.name}>',
            register_pickle_by_value=register_pickle_by_value,
            **kwargs,
        )

        # If we want to pause
        if self.action == TaskAction.PAUSE:
            engine_process.report(f'Task {self.name} is created and paused.')
            process = create_and_pause_process(
                engine_process.runner,
                PythonJob,
                inputs,
                state_msg='Paused through WorkGraph',
            )
            state = TaskState.CREATED
            process = process.node
        else:
            process = engine_process.submit(PythonJob, **inputs)
            state = TaskState.RUNNING

        return process, state


class PyFunctionTask(BaseSerializablePythonTask):
    """PyFunction Task."""

    identifier = 'workgraph.pyfunction'

    def execute(self, args=None, kwargs=None, var_kwargs=None, engine_process=None):
        from aiida_pythonjob import prepare_pyfunction_inputs

        kwargs = kwargs or {}
        metadata = self.get_process_metadata(kwargs)
        func = RuntimeExecutor(**self.get_executor().to_dict()).callable
        # If it's a wrapped function, unwrap
        if isinstance(func, BaseHandle) and hasattr(func, '_callable'):
            func = func._callable

        if self.spec.metadata.get('is_coroutine', False):
            function_inputs = self.get_function_inputs(kwargs, var_kwargs)
            inputs = prepare_pyfunction_inputs(
                function=func,
                function_inputs=function_inputs,
                inputs_spec=self.function_inputs_spec,
                outputs_spec=self.function_outputs_spec,
                metadata=metadata,
                process_label=kwargs.pop('process_label', None),
                deserializers=kwargs.pop('deserializers', None),
                serializers=kwargs.pop('serializers', None),
                register_pickle_by_value=kwargs.pop('register_pickle_by_value', False),
            )
            if self.action == TaskAction.PAUSE:
                engine_process.report(f'Task {self.name} is created and paused.')
                process = create_and_pause_process(
                    engine_process.runner,
                    PyFunction,
                    inputs,
                    state_msg='Paused through WorkGraph',
                )
                state = TaskState.CREATED
                process = process.node
            else:
                process = engine_process.submit(PyFunction, **inputs)
                state = TaskState.RUNNING

            return process, state
        else:
            # Make sure it's process_function-decorated
            if not hasattr(func, 'is_process_function'):
                func = pyfunction()(func)

            # If we have var_kwargs, pass them in
            if var_kwargs is None:
                _, process = run_get_node(
                    func,
                    inputs_spec=self.function_inputs_spec,
                    outputs_spec=self.function_outputs_spec,
                    metadata=metadata,
                    **kwargs,
                )
            else:
                _, process = run_get_node(func, **kwargs, **var_kwargs)

            return process, TaskState.FINISHED


class MonitorFunctionTask(BaseSerializablePythonTask):
    """Monitor Function Task."""

    identifier = 'workgraph.monitor_function'

    def execute(self, args=None, kwargs=None, var_kwargs=None, engine_process=None):
        from aiida_pythonjob import prepare_monitor_function_inputs

        kwargs = kwargs or {}
        metadata = self.get_process_metadata(kwargs)
        func = RuntimeExecutor(**self.get_executor().to_dict()).callable
        # If it's a wrapped function, unwrap
        if isinstance(func, BaseHandle) and hasattr(func, '_callable'):
            func = func._callable
        function_inputs = self.get_function_inputs(kwargs, var_kwargs)
        inputs = prepare_monitor_function_inputs(
            function=func,
            function_inputs=function_inputs,
            inputs_spec=self.function_inputs_spec,
            outputs_spec=self.function_outputs_spec,
            metadata=metadata,
            process_label=kwargs.pop('process_label', None),
            deserializers=kwargs.pop('deserializers', None),
            serializers=kwargs.pop('serializers', None),
            register_pickle_by_value=kwargs.pop('register_pickle_by_value', False),
            **kwargs,
        )
        if self.action == TaskAction.PAUSE:
            engine_process.report(f'Task {self.name} is created and paused.')
            process = create_and_pause_process(
                engine_process.runner,
                MonitorPyFunction,
                inputs,
                state_msg='Paused through WorkGraph',
            )
            state = TaskState.CREATED
            process = process.node
        else:
            process = engine_process.submit(MonitorPyFunction, **inputs)
            state = TaskState.RUNNING
        return process, state


def build_pythonjob_taskspec(
    obj: Callable,
    identifier: str | None = None,
    catalog: str = 'Others',
    in_spec: SocketSpec | None | list = None,
    out_spec: SocketSpec | None | list = None,
    error_handlers: dict[str, ErrorHandlerSpec] | None = None,
) -> TaskSpec:
    # allow list specs just for PythonJob (keep existing behavior)
    from aiida.workgraph.socket_spec import validate_socket_data

    in_spec = validate_socket_data(in_spec)
    out_spec = validate_socket_data(out_spec)

    # additions specific to PythonJob
    add_in = namespace(
        computer=Annotated[str, SocketMeta(required=False)],
        command_info=Annotated[dict, SocketMeta(required=False)],
        register_pickle_by_value=Annotated[bool, SocketMeta(required=False)],
    )

    return build_callable_TaskSpec(
        obj=obj,
        task_type='PYTHONJOB',
        catalog=catalog,
        base_class=PythonJobTask,
        identifier=identifier,
        process_cls=PythonJob,
        in_spec=in_spec,
        out_spec=out_spec,
        add_inputs=add_in,
        error_handlers=error_handlers,
    )


def build_pyfunction_taskspec(
    obj: Callable,
    identifier: str | None = None,
    catalog: str = 'Others',
    in_spec: SocketSpec | None = None,
    out_spec: SocketSpec | None = None,
    error_handlers: dict[str, ErrorHandlerSpec] | None = None,
) -> TaskSpec:
    import asyncio

    if asyncio.iscoroutinefunction(obj):
        metadata = {'is_coroutine': True}
    else:
        metadata = {}
    return build_callable_TaskSpec(
        obj=obj,
        task_type='PYFUNCTION',
        catalog=catalog,
        base_class=PyFunctionTask,
        identifier=identifier,
        process_cls=PyFunction,
        in_spec=in_spec,
        out_spec=out_spec,
        error_handlers=error_handlers,
        metadata=metadata,
    )


def build_monitor_function_taskspec(
    obj: Callable,
    identifier: str | None = None,
    catalog: str = 'Others',
    in_spec: SocketSpec | None = None,
    out_spec: SocketSpec | None = None,
    error_handlers: dict[str, ErrorHandlerSpec] | None = None,
) -> TaskSpec:
    add_in = namespace(
        interval=(int, 5),
        timeout=(int, 3600),
    )
    add_out = namespace(exit_code=Any)

    return build_callable_TaskSpec(
        obj=obj,
        task_type='MONITOR',
        catalog=catalog,
        base_class=MonitorFunctionTask,
        identifier=identifier,
        process_cls=MonitorPyFunction,
        in_spec=in_spec,
        out_spec=out_spec,
        add_inputs=add_in,
        add_outputs=add_out,
        error_handlers=error_handlers,
    )
