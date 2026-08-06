from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import replace
from typing import Annotated, Any

from aiida_shell import ShellJob
from aiida_shell.launch import prepare_shell_job_inputs
from node_graph.executor import RuntimeExecutor
from node_graph.socket_spec import SocketMeta, SocketSpec, merge_specs
from node_graph.task_spec import TaskSpec

from aiida import orm
from aiida.workgraph.enums import TaskAction, TaskState
from aiida.workgraph.socket_spec import from_aiida_process, namespace
from aiida.workgraph.task import Task, TaskHandle


def _serialize_value(self, store: bool = False) -> Any:
    from node_graph.utils import resolve_tagged_values

    value = resolve_tagged_values(self._value)
    if value is None:
        return None
    return RuntimeExecutor.from_callable(value).to_dict()


class ShellJobTask(Task):
    """Runtime for ShellJob nodes.

    This class is referenced by TaskSpec.base_class_path so the engine can import
    it and call `execute`.
    """

    identifier = 'workgraph.shelljob'
    name = 'shelljob'
    task_type = 'SHELLJOB'
    catalog = 'AIIDA'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # override the _serialize_value
        self.inputs['parser'].set_serializer(_serialize_value)

    def execute(self, engine_process, args=None, kwargs=None, var_kwargs=None):
        """Submit/launch the AiiDA ShellJob.

        - Translates friendly inputs (command, resolve_command, parser, ...)
          using `prepare_shell_job_inputs`.
        - Submits or runs under the engine's runner.
        """
        from aiida.workgraph.utils import create_and_pause_process

        kwargs = dict(kwargs or {})

        # Detect and translate aiida-shell convenience arguments
        signature = inspect.signature(prepare_shell_job_inputs)
        aiida_shell_keys = signature.parameters.keys()

        subset = {k: kwargs[k] for k in list(kwargs) if k in aiida_shell_keys}

        parser = subset.get('parser', None)
        if isinstance(parser, dict) and {'module_path', 'callable_name'} <= set(parser):
            # already a Executor dict -> build executor instance
            subset['parser'] = RuntimeExecutor(**parser).callable
        elif inspect.isfunction(parser):
            subset['parser'] = parser

        if subset:
            if 'command' in subset:
                subset['command'] = (
                    subset['command'].value if isinstance(subset['command'], orm.Str) else subset['command']
                )
            if 'resolve_command' in subset:
                subset['resolve_command'] = (
                    subset['resolve_command'].value
                    if isinstance(subset['resolve_command'], orm.Bool)
                    else subset['resolve_command']
                )
            if 'arguments' in subset:
                subset['arguments'] = (
                    subset['arguments'].get_list() if isinstance(subset['arguments'], orm.List) else subset['arguments']
                )
            prepared = prepare_shell_job_inputs(**subset)
            # drop original keys so they won't clash with launch kwargs
            for k in subset.keys():
                kwargs.pop(k, None)
            # merge translated inputs
            kwargs.update(prepared)

        # metadata
        md = kwargs.setdefault('metadata', {})
        md.setdefault('call_link_label', self.name)

        if getattr(self, 'action', None) == TaskAction.PAUSE:
            engine_process.report(f'Task {self.name} is created and paused.')
            process = create_and_pause_process(
                engine_process.runner,
                ShellJob,
                kwargs,
                state_msg='Paused through WorkGraph',
            )
            state = TaskState.CREATED
            process = process.node
        else:
            process = engine_process.submit(ShellJob, **kwargs)
            state = TaskState.RUNNING
        return process, state


def _build_shelljob_TaskSpec(
    *,
    identifier: str | None = None,
    outputs: SocketSpec | list[str] | None = None,
    parser_outputs: SocketSpec | list[str] | None = None,
) -> TaskSpec:
    """Create a `TaskSpec` for a ShellJob, augmenting inputs/outputs as needed.

    - Start from AiiDA Process spec inference
    - Add inputs: command, resolve_command
    - Ensure stdout/stderr outputs exist
    - Optionally add user-declared outputs and parser_outputs (as leaf-any)
    """
    from aiida_shell.parsers.shell import ShellParser

    from aiida.workgraph.socket_spec import validate_socket_data

    outputs = validate_socket_data(outputs)
    parser_outputs = validate_socket_data(parser_outputs)

    in_spec, out_spec = from_aiida_process(ShellJob)
    # the code socket is not required in the task
    # as we can build it from the command input
    code_spec = in_spec.fields['code']
    patched_code = replace(code_spec, meta=replace(code_spec.meta, required=False))
    in_spec = replace(in_spec, fields={**in_spec.fields, 'code': patched_code})

    # Add additional inputs
    additions_in = namespace(command=Any, resolve_command=Annotated[bool, SocketMeta(required=False)])
    in_spec = merge_specs(in_spec, additions_in)

    # Ensure stdout/stderr outputs
    additions_out = namespace(stdout=Any, stderr=Any)
    out_spec = merge_specs(out_spec, additions_out)

    # add extra outputs requested by user
    if outputs:
        # make sure the key are AiiDA compatible
        fields = {ShellParser.format_link_label(key): value for key, value in outputs.fields.items()}
        outputs = replace(outputs, fields=fields)
        out_spec = merge_specs(out_spec, outputs)

    if parser_outputs:
        out_spec = merge_specs(out_spec, parser_outputs)

    exec_payload = RuntimeExecutor.from_callable(ShellJob)

    return TaskSpec(
        identifier=identifier or 'ShellJob',
        catalog='AIIDA',
        task_type='SHELLJOB',
        inputs=in_spec,
        outputs=out_spec,
        executor=exec_payload,
        base_class=ShellJobTask,
        metadata={'task_type': 'SHELLJOB'},
    )


# Public factory used by users inside a WorkGraph


def shelljob(
    *,
    command: str,
    arguments: list[str] | None = None,
    nodes: dict[str, Any] | None = None,
    filenames: dict[str, str] | None = None,
    outputs: list[str | dict[str, Any]] | None = None,
    parser: Callable | None = None,
    parser_outputs: SocketSpec | list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    resolve_command: bool = True,
):
    """Create a ShellJob node in the active WorkGraph and return its outputs handle.

    Usage:
        with WorkGraph(name="test_shell_date_with_arguments") as wg:
            outs = shelljob(command="date", arguments=["--iso-8601"])  # returns handle
            wg.run()
    """
    spec = _build_shelljob_TaskSpec(outputs=outputs, parser_outputs=parser_outputs)

    handle = TaskHandle(spec)
    return handle(
        command=command,
        arguments=arguments,
        nodes=nodes,
        filenames=filenames,
        outputs=outputs,
        parser=parser,
        metadata=metadata,
        resolve_command=resolve_command,
    )
