from __future__ import annotations
from typing import Any, Dict, Optional

from aiida.node_graph import Graph
from aiida.node_graph.graph import BUILTIN_TASKS
from .provenance import ProvenanceRecorder
from .base import BaseEngine

from .utils import (
    _scan_links_topology,
    _collect_literals,
    update_nested_dict_with_special_keys,
    _resolve_tagged_value,
)
from aiida.node_graph.utils.struct_utils import coerce_inputs_from_spec


class LocalEngine(BaseEngine):
    """
    Sync, dependency-free runner with provenance:

    - @task: calls the underlying python function, normalizes to {result: ...}
    - @task.graph: builds & runs a sub-Graph, resolves returned socket-handles to values
    - Provenance: records runtime *flattened* inputs & outputs around each task run
    - Link semantics from utils: _wait, _outputs, and multi-fan-in bundling
    """

    engine_kind = "local"

    def __init__(
        self, name: str = "local-flow", recorder: Optional[ProvenanceRecorder] = None
    ):
        super().__init__(name, recorder)
        self._graph_pid: Optional[str] = None

    def run(
        self,
        ng: Graph,
        parent_pid: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute ``ng`` and return the graph outputs as plain values."""
        order, incoming, _required = _scan_links_topology(ng)

        # Built-ins: treat as already "available" values
        values: Dict[str, Dict[str, Any]] = self._snapshot_builtins(ng)

        graph_pid = self._start_graph_run(ng, parent_pid)
        previous_pid = self._graph_pid
        self._graph_pid = graph_pid

        try:
            for name in order:
                if name in BUILTIN_TASKS:
                    continue

                task = ng.tasks[name]

                kw = dict(_collect_literals(task))
                link_kwargs = self._build_link_kwargs(
                    target_name=name,
                    links=incoming.get(name, []),
                    source_map=values,
                )
                kw.update(link_kwargs)
                kw = update_nested_dict_with_special_keys(kw)

                label_kind = "return" if self._is_graph_task(task) else "create"
                executor = self._build_task_executor(task, label_kind=label_kind)
                tagged_out = executor(graph_pid, **kw)
                values[name] = tagged_out

            graph_outputs = self._build_link_kwargs(
                target_name="graph_outputs",
                links=incoming.get("graph_outputs", []),
                source_map=values,
            )
            # graph_outputs = update_nested_dict_with_special_keys(graph_outputs)
            return self._finalize_graph_success(ng, graph_pid, graph_outputs)
        except Exception as e:
            self._record_graph_failure(graph_pid, e)
            raise
        finally:
            self._graph_pid = previous_pid

    def _build_task_executor(self, task, label_kind: str):
        fn = self._unwrap_callable(task)
        is_graph = self._is_graph_task(task)

        def _executor(parent_pid: Optional[str], **kwargs: Any) -> Dict[str, Any]:
            pid: Optional[str] = None
            run_kwargs = dict(kwargs)
            if not is_graph:
                pid = self.recorder.process_start(
                    task_name=task.name,
                    callable_obj=fn,
                    flow_run_id=f"{self.engine_kind}:{self.name}",
                    task_run_id=f"{self.engine_kind}:{task.name}",
                    parent_pid=parent_pid,
                )
                self.recorder.record_inputs_payload(pid, run_kwargs)

            try:
                raw_kwargs = _resolve_tagged_value(run_kwargs)
                raw_kwargs = coerce_inputs_from_spec(raw_kwargs, task.spec.inputs)
                if is_graph and fn is not None:
                    res = fn(**run_kwargs)
                elif fn is None:
                    res = dict(raw_kwargs)
                else:
                    res = fn(**raw_kwargs)

                tagged_out = self._normalize_outputs(task, res, strict=False)

                if pid is not None:
                    self.recorder.record_outputs_payload(
                        pid, tagged_out, label_kind=label_kind
                    )
                    self.recorder.process_end(pid, state="FINISHED")

                return tagged_out
            except Exception as exc:
                if pid is not None:
                    self.recorder.process_end(pid, state="FAILED", error=str(exc))
                raise

        return _executor

    def _run_subgraph(self, task, sub_ng: Graph, parent_pid: Optional[str]) -> None:
        LocalEngine(name=f"{self.name}::{task.name}", recorder=self.recorder).run(
            sub_ng, parent_pid=parent_pid
        )

    def _get_active_graph_pid(self) -> Optional[str]:
        return self._graph_pid
