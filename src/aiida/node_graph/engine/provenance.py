from __future__ import annotations
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from aiida.node_graph.socket import TaggedValue
from uuid import uuid4


def _flatten_dict(payload: Any, prefix: str = "") -> Dict[str, Any]:
    """
    Recursively flatten dict-like payloads into dotted keys.
    - If payload isn't a dict, returns {prefix or 'result': payload}.
    - For dicts, recurses depth-first; lists/tuples are recorded as whole values by default.
    """
    out: Dict[str, Any] = {}
    if isinstance(payload, TaggedValue):
        key = prefix or "result"
        out[key] = payload
        return out
    if not isinstance(payload, dict):
        key = prefix or "result"
        out[key] = payload
        return out
    for k, v in payload.items():
        dotted = f"{prefix}.{k}" if prefix else str(k)
        if isinstance(v, dict):
            out.update(_flatten_dict(v, dotted))
        else:
            out[dotted] = v
    return out


@dataclass
class DataNode:
    id: str
    kind: str
    preview: Optional[Any]
    label: Optional[str] = None
    size_hint: Optional[int] = None


@dataclass
class ProcessNode:
    id: str
    name: str
    callable_path: Optional[str]
    flow_run_id: Optional[str] = None
    task_run_id: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    state: Optional[str] = None
    error: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)
    kind: str = "task"


@dataclass
class Edge:
    src: str
    dst: str
    label: Optional[str] = None


class ProvenanceRecorder:
    """
    In-memory provenance store for one workflow run.
    Records *runtime* flattened inputs/outputs (dotted keys), which supports dynamic namespaces.
    """

    def __init__(self, workflow_name: str):
        self.workflow_name = workflow_name
        self.process_nodes: Dict[str, ProcessNode] = {}
        self.data_nodes: Dict[str, DataNode] = {}
        self.edges: List[Edge] = []
        self._latest_outputs_by_task: Dict[str, Dict[str, Any]] = {}

    def process_start(
        self,
        task_name: str,
        callable_obj: Optional[callable],
        flow_run_id: Optional[str],
        task_run_id: Optional[str],
        *,
        kind: str = "task",
        parent_pid: Optional[str] = None,
    ) -> str:
        pid = f"proc:{uuid4().hex}"
        callable_path = None
        if callable_obj is not None:
            mod = getattr(callable_obj, "__module__", None)
            name = getattr(
                callable_obj, "__qualname__", getattr(callable_obj, "__name__", None)
            )
            if mod and name:
                callable_path = f"{mod}.{name}"
        self.process_nodes[pid] = ProcessNode(
            id=pid,
            name=task_name,
            callable_path=callable_path,
            flow_run_id=flow_run_id,
            task_run_id=task_run_id,
            start_time=time.time(),
            kind=kind,
        )
        if parent_pid is not None and parent_pid in self.process_nodes:
            self.edges.append(Edge(src=parent_pid, dst=pid, label="call"))
        return pid

    def process_end(self, pid: str, state: str, error: Optional[str] = None):
        pn = self.process_nodes[pid]
        pn.end_time = time.time()
        pn.state = state
        pn.error = error

    def record_inputs_payload(
        self,
        pid: str,
        kwargs: Dict[str, Any],
    ):
        """
        Flatten kwargs to dotted keys at runtime (supports dynamic namespaces),
        then record one DataNode per leaf and an edge data->process per key.
        """
        flat = _flatten_dict(kwargs)
        self._record_inputs_flat(pid, flat)

    def _record_inputs_flat(self, pid: str, kwargs_flat: Dict[str, Any]):
        for k, v in kwargs_flat.items():
            uuid = v._uuid
            did = f"data:{uuid}"
            if did not in self.data_nodes:
                preview = v
                try:
                    if isinstance(v, (str, bytes)) and len(v) > 256:
                        preview = f"{v[:256]}... (+{len(v)-256} chars)"
                except Exception:
                    pass
                self.data_nodes[did] = DataNode(
                    id=did,
                    kind="input",
                    label=type(v.__wrapped__).__name__,
                    preview=preview,
                )
            self.edges.append(Edge(src=did, dst=pid, label=f"input:{k}"))

    def record_outputs_payload(
        self,
        pid: str,
        outputs: Dict[str, Any],
        label_kind: str = "output",
    ):
        flat = _flatten_dict(outputs)
        proc = self.process_nodes.get(pid)
        if proc is not None:
            self._latest_outputs_by_task[proc.name] = outputs
        self._record_outputs_flat(pid, flat, label_kind)

    def _record_outputs_flat(
        self, pid: str, outputs_flat: Dict[str, Any], label_kind: str = "output"
    ):
        for k, v in outputs_flat.items():
            uuid = v._uuid
            did = f"data:{uuid}"
            if did not in self.data_nodes:
                preview = v
                try:
                    if isinstance(v, (str, bytes)) and len(v) > 256:
                        preview = f"{v[:256]}... (+{len(v)-256} chars)"
                except Exception:
                    pass
                self.data_nodes[did] = DataNode(
                    id=did,
                    kind="output",
                    label=type(v.__wrapped__).__name__,
                    preview=preview,
                )
            self.edges.append(Edge(src=pid, dst=did, label=f"{label_kind}:{k}"))

    def to_json(self) -> dict:
        return {
            "workflow": self.workflow_name,
            "process_nodes": {k: vars(v) for k, v in self.process_nodes.items()},
            "data_nodes": {k: vars(v) for k, v in self.data_nodes.items()},
            "edges": [vars(e) for e in self.edges],
        }

    def save_json(self, path: str):
        with open(path, "w") as f:
            json.dump(self.to_json(), f, indent=2, sort_keys=True, default=str)
        return path

    def to_graphviz(self) -> str:
        lines = [
            "digraph provenance {",
            "  rankdir=TB;",
            '  graph [bgcolor="#ffffff"];',
            '  node [fontname="Helvetica"];',
            '  edge [fontname="Helvetica"];',
        ]
        for p in self.process_nodes.values():
            if p.kind == "graph":
                shape = "rectangle"
                fill = "#e38851ff"
                color = "#2e7d32"
            else:
                shape = "rectangle"
                fill = "#de707f77"
                color = "#2f5597"
            label = f"{p.name} ({self._short_id(p.id)})\\nstate={p.state}"
            lines.append(
                f'  "{p.id}" [shape={shape}, style="filled,rounded", fillcolor="{fill}", color="{color}", label="{label}"];'
            )
        for d in self.data_nodes.values():
            label_prefix = d.label or ""
            node_label = (
                f"{label_prefix} ({self._short_id(d.id)})"
                if label_prefix
                else self._short_id(d.id)
            )
            lines.append(
                f'  "{d.id}" [shape=ellipse, style="filled", fillcolor="#8cd499ff", color="#d46a0b", label="{node_label}"];'
            )
        for e in self.edges:
            label_text, style, color = self._edge_attributes(e.label)
            attrs = []
            if label_text:
                attrs.append(f'label="{label_text}"')
            if style:
                attrs.append(f'style="{style}"')
            if color:
                attrs.append(f'color="{color}"')
            attr_str = f" [{', '.join(attrs)}]" if attrs else ""
            lines.append(f'  "{e.src}" -> "{e.dst}"{attr_str};')
        lines.append("}")
        return "\n".join(lines)

    def save_graphviz(self, path: str):
        dot = self.to_graphviz()
        with open(path, "w") as f:
            f.write(dot)
        return path

    def generate_graph(self):
        """
        Return a ``graphviz.Source`` object representing the provenance graph.
        """
        try:
            from graphviz import Source
        except ImportError as exc:
            raise RuntimeError(
                "graphviz package is required to visualize provenance graphs."
            ) from exc
        return Source(self.to_graphviz())

    def to_graphviz_svg(self) -> str:
        graph = self.generate_graph()
        return graph.pipe(format="svg").decode("utf-8")

    def save_graphviz_svg(self, path: str):
        svg = self.to_graphviz_svg()
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        return path

    def _repr_svg_(self) -> Optional[str]:  # pragma: no cover - exercised in notebooks
        """SVG representation for rich notebook outputs."""
        try:
            return self.to_graphviz_svg()
        except RuntimeError:
            return None

    def _repr_html_(self) -> Optional[str]:  # pragma: no cover - exercised in notebooks
        """
        HTML fallback when SVG repr is unavailable or the graphviz dependency is
        missing.  Returning ``None`` defers to other representations.
        """
        svg = self._repr_svg_()
        if svg is None:
            return None
        return f'<div class="node-graph-provenance">{svg}</div>'

    def to_html(self, title: Optional[str] = None) -> str:
        """Return an HTML document that embeds the rendered provenance graph."""
        svg = self.to_graphviz_svg()
        page_title = title or f"{self.workflow_name} provenance"
        return """<!DOCTYPE html>\n""" + "\n".join(
            [
                '<html lang="en">',
                "  <head>",
                '    <meta charset="utf-8" />',
                f"    <title>{page_title}</title>",
                "    <style>",
                "      body {",
                "        font-family: Helvetica, Arial, sans-serif;",
                "        background-color: #f9f9fb;",
                "        margin: 0;",
                "        padding: 1.5rem;",
                "        color: #212121;",
                "      }",
                "      .container {",
                "        background-color: #ffffff;",
                "        padding: 1.5rem;",
                "        border-radius: 12px;",
                "        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.05);",
                "        overflow-x: auto;",
                "      }",
                "      h1 {",
                "        font-size: 1.5rem;",
                "        margin-top: 0;",
                "        margin-bottom: 1rem;",
                "      }",
                "      svg {",
                "        max-width: 100%;",
                "        height: auto;",
                "      }",
                "    </style>",
                "  </head>",
                "  <body>",
                '    <div class="container">',
                f"      <h1>{page_title}</h1>",
                f"{svg}",
                "    </div>",
                "  </body>",
                "</html>",
            ]
        )

    def save_html(self, path: str, title: Optional[str] = None):
        html = self.to_html(title=title)
        path_obj = Path(path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        path_obj.write_text(html, encoding="utf-8")
        return str(path_obj)

    @staticmethod
    def _edge_attributes(
        label: Optional[str],
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        if not label:
            return None, None, None

        style: Optional[str] = None
        color: Optional[str] = None
        text: Optional[str] = None

        if label == "call":
            style = "dashed"
            color = "#546e7a"
            text = "CALL"
            return text, style, color

        if label.startswith("return"):
            style = "dotted"
            color = "#7b1fa2"

        if ":" in label:
            kind, _, name = label.partition(":")
            kind_text = kind.upper()
            text = f"{kind_text}\\n{name}"
            return text, style, color

        text = label.upper()
        return text, style, color

    @staticmethod
    def _short_id(identifier: str, length: int = 7) -> str:
        tail = identifier.split(":")[-1]
        if len(tail) <= length:
            return tail
        return f"{tail[:length]}..."
