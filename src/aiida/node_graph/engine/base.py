from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional

from aiida.node_graph import Graph
from aiida.node_graph.utils import clean_socket_reference, tag_socket_value

from .provenance import ProvenanceRecorder
from .utils import (
    _build_task_link_kwargs,
    _resolve_tagged_value,
    get_nested_dict,
    parse_outputs,
)


class BaseEngine(ABC):
    """Common helpers shared by engine implementations."""

    engine_kind = "engine"

    def __init__(
        self,
        name: str,
        recorder: Optional[ProvenanceRecorder] = None,
    ) -> None:
        self.name = name
        self.recorder = recorder or ProvenanceRecorder(name)

    @staticmethod
    def _is_graph_task(task) -> bool:
        return getattr(task.spec, "task_type", "").lower() == "graph"

    def _unwrap_callable(self, task) -> Optional[Callable]:
        if self._is_graph_task(task):
            return self._graph_callable(task)
        return self._extract_executor_callable(task)

    @staticmethod
    def _extract_executor_callable(task) -> Optional[Callable]:
        exec_obj = getattr(task.spec, "executor", None)
        if not exec_obj:
            return None
        fn = getattr(exec_obj, "callable", None)
        if hasattr(fn, "_callable"):
            fn = getattr(fn, "_callable")
        return fn

    def _graph_callable(self, task) -> Callable:
        graph_fn = self._extract_executor_callable(task)
        if graph_fn is None:
            return lambda **_kwargs: {}

        def _graph_runner(**kwargs):
            sub_ng = self._build_subgraph(task, graph_fn, kwargs)
            parent_pid = self._get_active_graph_pid()
            self._run_subgraph(task, sub_ng, parent_pid)
            return sub_ng.outputs._collect_values(unwrap=False)

        return _graph_runner

    @staticmethod
    def _snapshot_builtins(ng: Graph) -> Dict[str, Dict[str, Any]]:
        return {
            "graph_ctx": ng.ctx._collect_values(unwrap=False),
            "graph_inputs": ng.inputs._collect_values(unwrap=False),
            "graph_outputs": ng.outputs._collect_values(unwrap=False),
        }

    def _graph_flow_run_id(self, ng: Graph) -> str:
        return f"{self.engine_kind}:{self.name}"

    def _graph_task_run_id(self, ng: Graph) -> str:
        return f"{self.engine_kind}:{ng.name}"

    def _start_graph_run(
        self,
        ng: Graph,
        parent_pid: Optional[str],
    ) -> str:
        graph_pid = self.recorder.process_start(
            task_name=ng.name,
            callable_obj=None,
            flow_run_id=self._graph_flow_run_id(ng),
            task_run_id=self._graph_task_run_id(ng),
            kind="graph",
            parent_pid=parent_pid,
        )
        self.recorder.record_inputs_payload(
            graph_pid, ng.inputs._collect_values(unwrap=False)
        )
        return graph_pid

    def _finalize_graph_success(
        self,
        ng: Graph,
        graph_pid: str,
        graph_outputs: Dict[str, Any],
    ) -> Dict[str, Any]:
        cleaned = clean_socket_reference(graph_outputs)
        ng.outputs._set_socket_value(cleaned)
        self.recorder.record_outputs_payload(
            graph_pid,
            cleaned,
            label_kind="return",
        )
        self.recorder.process_end(graph_pid, state="FINISHED")
        return _resolve_tagged_value(cleaned)

    def _record_graph_failure(self, graph_pid: str, error: BaseException) -> None:
        self.recorder.process_end(graph_pid, state="FAILED", error=str(error))

    def _normalize_outputs(
        self,
        task,
        result: Any,
        *,
        strict: bool = True,
    ) -> Dict[str, Any]:
        if strict:
            parsed = parse_outputs(result, task.spec.outputs)
            task.outputs._set_socket_value(parsed)
        else:
            try:
                parsed = parse_outputs(result, task.spec.outputs)
                task.outputs._set_socket_value(parsed)
            except Exception as e:
                raise RuntimeError(
                    f"Failed to parse outputs for task '{task.name}': {e}"
                ) from e
        tag_socket_value(task.outputs, only_uuid=True)
        return task.outputs._collect_values(unwrap=False)

    def _link_socket_value(
        self, from_name: str, from_socket: str, source_map: Dict[str, Any]
    ) -> Any:
        return get_nested_dict(source_map[from_name], from_socket, default=None)

    def _link_whole_output(self, from_name: str, source_map: Dict[str, Any]) -> Any:
        return source_map[from_name]

    def _link_bundle(self, payload: Dict[str, Any]) -> Any:
        return payload

    def _build_link_kwargs(
        self,
        target_name: str,
        links,
        source_map: Dict[str, Any],
    ) -> Dict[str, Any]:
        return _build_task_link_kwargs(
            target_name,
            links,
            source_map,
            resolve_socket=self._link_socket_value,
            resolve_whole=self._link_whole_output,
            bundle_factory=self._link_bundle,
        )

    def _build_subgraph(
        self, task, graph_fn: Callable, kwargs: Dict[str, Any]
    ) -> Graph:
        from aiida.node_graph.utils.graph import materialize_graph

        sub_ng = materialize_graph(
            graph_fn,
            task.spec.inputs,
            task.spec.outputs,
            task.name,
            Graph,
            args=(),
            kwargs=kwargs,
            var_kwargs={},
        )
        sub_ng.name = f"{task.name}__subgraph"
        return sub_ng

    def _get_active_graph_pid(self) -> Optional[str]:
        return None

    @abstractmethod
    def _run_subgraph(self, task, sub_ng: Graph, parent_pid: Optional[str]) -> None:
        ...
