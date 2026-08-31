from collections.abc import Callable

from node_graph.executor import RuntimeExecutor
from node_graph.socket_spec import SocketSpec
from node_graph.task_spec import TaskSpec

from aiida.engine import Process
from aiida.workgraph.enums import TaskAction, TaskState
from aiida.workgraph.task import Task

from .function_task import build_callable_TaskSpec


class GraphTask(Task):
    """Graph builder task"""

    identifier = 'workgraph.graph_task'
    name = 'graph_task'
    task_type = 'graph_task'
    catalog = 'builtins'

    def execute(self, engine_process, args=None, kwargs=None, var_kwargs=None):
        from node_graph.utils.graph import materialize_graph

        from aiida.workgraph import WorkGraph
        from aiida.workgraph.engine.process import WorkGraphProcess
        from aiida.workgraph.task import TaskHandle
        from aiida.workgraph.utils import call_depth_from_node, create_and_pause_process

        executor = RuntimeExecutor(**self.get_executor().to_dict()).callable
        max_depth = self.spec.metadata.get('max_depth', 100)
        metadata = kwargs.pop('metadata', {}) if kwargs else {}
        metadata.setdefault('call_link_label', self.name)
        # Cloudpickle doesn't restore the function's own name in its globals after unpickling,
        # so any recursive calls would raise NameError. We re-insert a task handle into its
        # globals under its original name. We reuse the spec built at decoration time rather
        # than re-decorating the function: re-decoration would re-infer the signature, which
        # fails under PEP 563 once cloudpickle has dropped the names used only in stringized
        # annotations (issue #783).
        # Downside: this mutates the module globals at runtime, if another symbol with the same name exists,
        # we may introduce hard-to-trace bugs or collisions.
        if isinstance(executor, TaskHandle) and hasattr(executor, '_callable'):
            executor = executor._callable
        recursion_handle = TaskHandle(self.spec)
        recursion_handle._callable = executor
        executor.__globals__[executor.__name__] = recursion_handle
        depth = call_depth_from_node(engine_process.node)
        if depth >= max_depth:
            if depth >= max_depth:
                msg = (
                    f"Graph task '{self.name}' exceeded the recursion safeguard.\n"
                    f'- Current AiiDA process call depth (approx.): {depth}\n'
                    f'- Allowed maximum          :                  {max_depth}\n'
                    f'- Process UUID:                               {engine_process.node.uuid}\n\n'
                    f'Deeply nested process calls (>100) are generally discouraged. '
                    f'Prefer wrapping iterative logic inside a single task instead of '
                    f'recursively spawning new graph tasks.\n\n'
                    f'However, if you are confident that recursion is the right design, '
                    f'you can explicitly set a higher limit in your decorator, e.g.:\n'
                    f'    @task.graph(max_depth=200)\n'
                )
                engine_process.report(msg)
                raise RecursionError(msg)
        wg = materialize_graph(
            executor,
            self.spec.inputs,
            self.spec.outputs,
            self.name,
            WorkGraph,
            args=args,
            kwargs=kwargs,
            var_kwargs=var_kwargs,
        )
        # Set the maximum number of concurrent jobs
        max_number_jobs = self.spec.metadata.get('max_number_jobs')
        if max_number_jobs is not None:
            wg.max_number_jobs = max_number_jobs
        wg.parent_uuid = engine_process.node.uuid
        inputs = wg.to_engine_inputs(metadata=metadata)
        if self.action == TaskAction.PAUSE:
            engine_process.report(f'Task {self.name} is created and paused.')
            process = create_and_pause_process(
                engine_process.runner,
                WorkGraphProcess,
                inputs,
                state_msg='Paused through WorkGraph',
            )
            state = TaskState.CREATED
            process = process.node
        else:
            process = engine_process.submit(WorkGraphProcess, **inputs)
            state = TaskState.RUNNING

        return process, state


def _build_graph_task_taskspec(
    obj: Callable,
    identifier: str | None = None,
    in_spec: SocketSpec | None = None,
    out_spec: SocketSpec | None = None,
    max_depth: int = 100,
    max_number_jobs: int = 1000000,
    catalog: str = 'Others',
) -> TaskSpec:
    # defaults for max depth
    metadata = {'max_depth': max_depth, 'max_number_jobs': max_number_jobs}
    # We use Process as the process class here, so that the task inherits the metadata
    # inputs from the base Process class, such as 'call_link_label'.
    # While the actual process class will be the WorkGraphProcess,
    # which is set at runtime in the execute() method

    return build_callable_TaskSpec(
        obj=obj,
        task_type='GRAPH',
        base_class=GraphTask,
        identifier=identifier,
        catalog=catalog,
        process_cls=Process,
        in_spec=in_spec,
        out_spec=out_spec,
        metadata=metadata,
    )
