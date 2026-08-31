from collections.abc import Callable

from node_graph.error_handler import ErrorHandlerSpec, normalize_error_handlers
from node_graph.executor import RuntimeExecutor
from node_graph.socket_spec import SocketSpec
from node_graph.task_spec import SchemaSource, TaskSpec

from aiida.engine import Process
from aiida.workgraph.enums import TaskAction, TaskState
from aiida.workgraph.socket_spec import from_aiida_process
from aiida.workgraph.task import Task
from aiida.workgraph.utils import inspect_aiida_component_type

from .function_task import build_callable_TaskSpec


class AiiDAFunctionTask(Task):
    """Task with AiiDA calcfunction/workfunction as executor."""

    identifier = 'workgraph.aiida_functions'
    name = 'aiida_function'
    task_type = 'function'
    catalog = 'AIIDA'

    def execute(self, args=None, kwargs=None, var_kwargs=None):
        from node_graph.task_spec import BaseHandle

        from aiida.engine import run_get_node

        executor = RuntimeExecutor(**self.get_executor().to_dict()).callable
        # the imported executor could be a wrapped function
        if isinstance(executor, BaseHandle) and hasattr(executor, '_callable'):
            executor = getattr(executor, '_callable')
        kwargs.setdefault('metadata', {})
        kwargs['metadata'].update({'call_link_label': self.name})
        # since aiida 2.5.0, we need to use args_dict to pass the args to the run_get_node
        if var_kwargs is None:
            _, process = run_get_node(executor, **kwargs)
        else:
            _, process = run_get_node(executor, **kwargs, **var_kwargs)

        return process, TaskState.FINISHED


class AiiDAProcessTask(Task):
    """Task with AiiDA calcfunction/workfunction as executor."""

    identifier = 'workgraph.aiida_process'
    name = 'aiida_process'
    task_type = 'Process'
    catalog = 'AIIDA'

    @classmethod
    def build(
        cls,
        callable,
        attached_error_handlers: dict[str, ErrorHandlerSpec] | None = None,
    ):
        attached_error_handlers = normalize_error_handlers(attached_error_handlers)
        in_spec, out_spec = from_aiida_process(callable)
        return TaskSpec(
            identifier=callable.__name__,
            schema_source=SchemaSource.CALLABLE,
            catalog='AIIDA',
            inputs=in_spec,
            outputs=out_spec,
            executor=RuntimeExecutor.from_callable(callable),
            attached_error_handlers=attached_error_handlers,
            base_class=cls,
            task_type=inspect_aiida_component_type(callable),
        )

    def execute(self, engine_process, args=None, kwargs=None, var_kwargs=None):
        from aiida.workgraph.utils import create_and_pause_process

        executor = RuntimeExecutor(**self.get_executor().to_dict()).callable

        kwargs.setdefault('metadata', {})
        kwargs['metadata'].update({'call_link_label': self.name})
        if self.action == TaskAction.PAUSE:
            engine_process.report(f'Task {self.name} is created and paused.')
            process = create_and_pause_process(
                engine_process.runner,
                executor,
                kwargs,
                state_msg='Paused through WorkGraph',
            )
            state = TaskState.CREATED
            process = process.node
        else:
            process = engine_process.submit(executor, **kwargs)
            state = TaskState.RUNNING

        return process, state


class CalcJobTask(AiiDAProcessTask):
    identifier = 'workgraph.calcjob'
    name = 'calcjob'
    task_type = 'CalcJob'
    catalog = 'AIIDA'


class WorkChainTask(AiiDAProcessTask):
    identifier = 'workgraph.workchain'
    name = 'workchain'
    task_type = 'WorkChain'
    catalog = 'AIIDA'


def _build_aiida_function_taskspec(
    obj: Callable,
    identifier: str | None = None,
    catalog: str = 'AIIDA',
    in_spec: SocketSpec | None = None,
    out_spec: SocketSpec | None = None,
    error_handlers: dict[str, ErrorHandlerSpec] | None = None,
) -> TaskSpec:
    from dataclasses import replace

    from aiida.workgraph.utils import inspect_aiida_component_type

    spec = build_callable_TaskSpec(
        obj=obj,
        task_type=inspect_aiida_component_type(obj),
        catalog=catalog,
        base_class=AiiDAFunctionTask,
        identifier=identifier,
        process_cls=Process,
        in_spec=in_spec,
        out_spec=out_spec,
        error_handlers=error_handlers,
    )
    # the outputs of calcfunctions/workfunctions are always dynamic
    spec = replace(spec, outputs=replace(spec.outputs, meta=replace(spec.outputs.meta, dynamic=True)))
    if obj.spec().inputs.dynamic:
        spec = replace(spec, inputs=replace(spec.inputs, meta=replace(spec.inputs.meta, dynamic=True)))
    return spec
